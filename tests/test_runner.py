import json
import sqlite3
from pathlib import Path

from tracebench.runner import run_config
from tracebench.schemas import Condition, RunConfig, Variant
from tracebench.storage import EpisodeStore


def test_runner_persists_deduplicated_episode_records(tmp_path: Path):
    config = RunConfig(
        suite="test",
        provider="scripted",
        model="control",
        case_count=2,
        variants=[Variant.BASELINE, Variant.CONTROLS_AND_RECOVERY],
        conditions=[Condition.CLEAN, Condition.FAULT],
        repeats=1,
    )
    records = run_config(config, tmp_path)
    assert len(records) == 8
    with EpisodeStore(tmp_path / "episodes.db") as store:
        assert len(store.records()) == 8
    assert (tmp_path / "run-manifest.json").exists()


def test_runner_resumes_without_duplicate_attempts(tmp_path: Path):
    config = RunConfig(
        suite="resume-test",
        provider="scripted",
        model="control",
        case_count=1,
        variants=[Variant.BASELINE],
        conditions=[Condition.CLEAN],
    )
    first = run_config(config, tmp_path)
    second = run_config(config, tmp_path)
    assert [item.attempt_id for item in first] == [item.attempt_id for item in second]
    with EpisodeStore(tmp_path / "episodes.db") as store:
        assert len(store.records(first[0].run_id)) == 1


def test_forced_rerun_preserves_attempt_history(tmp_path: Path):
    config = RunConfig(
        suite="attempt-test",
        provider="scripted",
        model="control",
        case_count=1,
        variants=[Variant.BASELINE],
        conditions=[Condition.CLEAN],
    )
    first = run_config(config, tmp_path)
    second = run_config(config, tmp_path, resume=False)
    assert first[0].attempt_id.endswith("a001")
    assert second[0].attempt_id.endswith("a002")


def test_legacy_episode_records_remain_readable(tmp_path: Path):
    config = RunConfig(
        suite="legacy-test",
        provider="scripted",
        model="control",
        case_count=1,
        variants=[Variant.BASELINE],
        conditions=[Condition.CLEAN],
    )
    record = run_config(config, tmp_path)[0].model_dump(mode="json")
    record.pop("run_id")
    record.pop("attempt_id")
    record.pop("messages")
    record["score"].pop("claimed_status")
    database = tmp_path / "legacy.db"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE episodes (episode_id TEXT PRIMARY KEY, status TEXT, record_json TEXT)"
    )
    connection.execute(
        "INSERT INTO episodes VALUES (?, ?, ?)",
        (record["episode_id"], record["status"], json.dumps(record)),
    )
    connection.commit()
    connection.close()
    with EpisodeStore(database) as store:
        restored = store.records()[0]
    assert restored.run_id == "legacy"
    assert restored.attempt_id.endswith("-legacy")
