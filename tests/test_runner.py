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

