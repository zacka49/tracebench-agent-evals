from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

import httpx

from .agents import AgentOutcome, EpisodeTimeout, OllamaAgent, ScriptedAgent
from .cases import generate_cases
from .environment import Workspace
from .schemas import EpisodeRecord, FinalStatus, RunConfig
from .scoring import score_episode
from .storage import EpisodeStore


def _git_revision() -> str:
    try:
        git = ["git", "-c", f"safe.directory={Path.cwd().as_posix()}"]
        revision = subprocess.run(
            [*git, "rev-parse", "HEAD"],
            capture_output=True,
            check=True,
            text=True,
            timeout=2,
        ).stdout.strip()
        diff = subprocess.run(
            [*git, "diff", "--binary", "HEAD"],
            capture_output=True,
            check=True,
            timeout=2,
        ).stdout
        untracked = subprocess.run(
            [*git, "ls-files", "--others", "--exclude-standard", "-z"],
            capture_output=True,
            check=True,
            timeout=2,
        ).stdout.split(b"\0")
        dirty = hashlib.sha256(diff)
        for encoded_path in sorted(item for item in untracked if item):
            dirty.update(encoded_path)
            path = Path(encoded_path.decode("utf-8"))
            if path.is_file():
                dirty.update(path.read_bytes())
        return revision if not diff and not untracked[0] else f"{revision}-dirty-{dirty.hexdigest()[:12]}"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _run_identity(config: RunConfig, cases: list) -> tuple[str, dict]:
    cases_json = json.dumps([case.model_dump(mode="json") for case in cases], sort_keys=True)
    provenance = {
        "config": config.model_dump(mode="json"),
        "cases_sha256": hashlib.sha256(cases_json.encode()).hexdigest(),
        "git_revision": _git_revision(),
    }
    encoded = json.dumps(provenance, sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()[:20], provenance


def _episode_id(run_id: str, case_id: str, variant: str, condition: str, repeat: int) -> str:
    raw = "|".join([run_id, case_id, variant, condition, str(repeat)])
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


def run_config(config: RunConfig, output_dir: Path, resume: bool = True) -> list[EpisodeRecord]:
    output_dir.mkdir(parents=True, exist_ok=True)
    cases = generate_cases(config.case_count, config.seed)
    run_id, provenance = _run_identity(config, cases)
    database_path = output_dir / "episodes.db"
    records: list[EpisodeRecord] = []
    with EpisodeStore(database_path) as store:
        manifest = {"run_id": run_id, **provenance, "database": database_path.name}
        store.save_run(run_id, manifest)
        existing = {record.episode_id: record for record in store.records(run_id)} if resume else {}
        for case in cases:
            for condition in config.conditions:
                for variant in config.variants:
                    for repetition in range(config.repeats):
                        episode_id = _episode_id(
                            run_id, case.case_id, variant.value, condition.value, repetition
                        )
                        if episode_id in existing:
                            records.append(existing[episode_id])
                            continue
                        attempt_number = store.next_attempt_number(episode_id)
                        attempt_id = f"{episode_id}-a{attempt_number:03d}"
                        world = Workspace(case, condition, enforce_controls=variant.has_controls)
                        started = time.perf_counter()
                        status = "succeeded"
                        error = None
                        try:
                            agent = (
                                ScriptedAgent()
                                if config.provider == "scripted"
                                else OllamaAgent(config.model)
                            )
                            outcome = agent.run(
                                world,
                                case,
                                variant,
                                config.limits.tool_calls,
                                config.limits.wall_seconds,
                            )
                        except EpisodeTimeout as exc:
                            status = "timed_out"
                            error = f"EpisodeTimeout: {exc}"
                            outcome = AgentOutcome(
                                "Episode exceeded its wall-clock deadline.",
                                exc.tool_calls,
                                FinalStatus.UNKNOWN,
                                exc.messages,
                            )
                        except (
                            httpx.HTTPError,
                            KeyError,
                            RuntimeError,
                            TypeError,
                            ValueError,
                        ) as exc:  # preserve failed episodes in the result set
                            status = "failed"
                            error = f"{type(exc).__name__}: {exc}"
                            outcome = AgentOutcome(
                                "Episode failed before completion.",
                                0,
                                FinalStatus.FAILED,
                                [],
                            )
                        latency_ms = (time.perf_counter() - started) * 1000
                        score = score_episode(
                            world,
                            case,
                            outcome.final_message,
                            outcome.status,
                            outcome.tool_calls,
                            latency_ms,
                        )
                        record = EpisodeRecord(
                            run_id=run_id,
                            episode_id=episode_id,
                            attempt_id=attempt_id,
                            case_id=case.case_id,
                            condition=condition,
                            variant=variant,
                            provider=config.provider,
                            model=config.model,
                            repetition=repetition,
                            status=status,
                            final_message=outcome.final_message,
                            messages=outcome.messages,
                            score=score,
                            events=world.events,
                            final_state=world.snapshot(),
                            error=error,
                        )
                        store.save(record)
                        records.append(record)
        manifest["episode_count"] = len(records)
        store.save_run(run_id, manifest)
    (output_dir / "run-manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    (output_dir / "episodes.jsonl").write_text(
        "".join(record.model_dump_json() + "\n" for record in records), encoding="utf-8"
    )
    return records
