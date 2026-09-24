from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException

from .analysis import build_report
from .runner import run_config
from .schemas import RunConfig
from .storage import EpisodeStore


def create_app(data_root: Path | str = "service-data") -> FastAPI:
    root = Path(data_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    app = FastAPI(title="TraceBench", version="0.2.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/runs")
    def list_runs() -> list[dict]:
        manifests = []
        for database in root.glob("*/episodes.db"):
            with EpisodeStore(database) as store:
                manifests.extend(store.runs())
        return manifests

    @app.get("/runs/{run_id}")
    def get_run(run_id: str) -> dict:
        for database in root.glob("*/episodes.db"):
            with EpisodeStore(database) as store:
                records = store.records(run_id)
            if records:
                return {
                    "run_id": run_id,
                    "episode_count": len(records),
                    "succeeded": sum(item.status == "succeeded" for item in records),
                    "records": [item.model_dump(mode="json") for item in records],
                }
        raise HTTPException(status_code=404, detail="run not found")

    @app.post("/runs")
    def execute_run(config: RunConfig) -> dict:
        config_key = config.model_dump_json()
        output = root / __import__("hashlib").sha256(config_key.encode()).hexdigest()[:16]
        records = run_config(config, output, resume=True)
        markdown, _ = build_report(records, output)
        return {
            "run_id": records[0].run_id if records else None,
            "episode_count": len(records),
            "report": str(markdown),
        }

    return app


app = create_app()
