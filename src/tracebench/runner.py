from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import httpx

from .agents import OllamaAgent, ScriptedAgent
from .cases import generate_cases
from .environment import Workspace
from .schemas import EpisodeRecord, RunConfig
from .scoring import score_episode
from .storage import EpisodeStore


def _episode_id(config: RunConfig, case_id: str, variant: str, condition: str, repeat: int) -> str:
    raw = "|".join([config.suite, config.provider, config.model, case_id, variant, condition, str(repeat)])
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


def run_config(config: RunConfig, output_dir: Path) -> list[EpisodeRecord]:
    output_dir.mkdir(parents=True, exist_ok=True)
    cases = generate_cases(config.case_count)
    database_path = output_dir / "episodes.db"
    records: list[EpisodeRecord] = []
    with EpisodeStore(database_path) as store:
        for case in cases:
            for condition in config.conditions:
                for variant in config.variants:
                    for repetition in range(config.repeats):
                        episode_id = _episode_id(
                            config, case.case_id, variant.value, condition.value, repetition
                        )
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
                            outcome = agent.run(world, case, variant, config.limits.tool_calls)
                        except (
                            httpx.HTTPError,
                            KeyError,
                            RuntimeError,
                            TypeError,
                            ValueError,
                        ) as exc:  # preserve failed episodes in the result set
                            status = "failed"
                            error = f"{type(exc).__name__}: {exc}"
                            from .agents import AgentOutcome

                            outcome = AgentOutcome("Episode failed before completion.", 0)
                        latency_ms = (time.perf_counter() - started) * 1000
                        score = score_episode(
                            world, case, outcome.final_message, outcome.tool_calls, latency_ms
                        )
                        record = EpisodeRecord(
                            episode_id=episode_id,
                            case_id=case.case_id,
                            condition=condition,
                            variant=variant,
                            provider=config.provider,
                            model=config.model,
                            repetition=repetition,
                            status=status,
                            final_message=outcome.final_message,
                            score=score,
                            events=world.events,
                            final_state=world.snapshot(),
                            error=error,
                        )
                        store.save(record)
                        records.append(record)
    (output_dir / "run-manifest.json").write_text(
        json.dumps(
            {
                "config": config.model_dump(mode="json"),
                "episode_count": len(records),
                "database": str(database_path.name),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (output_dir / "episodes.jsonl").write_text(
        "".join(record.model_dump_json() + "\n" for record in records), encoding="utf-8"
    )
    return records
