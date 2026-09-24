from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Self

from .schemas import EpisodeRecord


class EpisodeStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS episodes (
                episode_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL,
                record_json TEXT NOT NULL
            )
            """
        )
        columns = {
            row[1] for row in self.connection.execute("PRAGMA table_info(episodes)").fetchall()
        }
        if "run_id" not in columns:
            self.connection.execute("ALTER TABLE episodes ADD COLUMN run_id TEXT NOT NULL DEFAULT ''")
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                manifest_json TEXT NOT NULL
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS attempts (
                attempt_id TEXT PRIMARY KEY,
                episode_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                status TEXT NOT NULL,
                record_json TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def save_run(self, run_id: str, manifest: dict) -> None:
        self.connection.execute(
            """
            INSERT INTO runs(run_id, created_at, manifest_json) VALUES (?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET manifest_json = excluded.manifest_json
            """,
            (run_id, datetime.now(UTC).isoformat(), json.dumps(manifest, sort_keys=True)),
        )
        self.connection.commit()

    def save(self, record: EpisodeRecord) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO episodes(episode_id, run_id, status, record_json) VALUES (?, ?, ?, ?)",
            (record.episode_id, record.run_id, record.status, record.model_dump_json()),
        )
        self.connection.execute(
            "INSERT OR REPLACE INTO attempts(attempt_id, episode_id, run_id, status, record_json) VALUES (?, ?, ?, ?, ?)",
            (
                record.attempt_id,
                record.episode_id,
                record.run_id,
                record.status,
                record.model_dump_json(),
            ),
        )
        self.connection.commit()

    def records(self, run_id: str | None = None) -> list[EpisodeRecord]:
        if run_id is None:
            rows = self.connection.execute(
                "SELECT record_json FROM episodes ORDER BY episode_id"
            ).fetchall()
        else:
            rows = self.connection.execute(
                "SELECT record_json FROM episodes WHERE run_id = ? ORDER BY episode_id",
                (run_id,),
            ).fetchall()
        records = []
        for row in rows:
            payload = json.loads(row[0])
            payload.setdefault("run_id", "legacy")
            payload.setdefault("attempt_id", f"{payload['episode_id']}-legacy")
            payload.setdefault("messages", [])
            payload["score"].setdefault("claimed_status", "unknown")
            records.append(EpisodeRecord.model_validate(payload))
        return records

    def runs(self) -> list[dict]:
        rows = self.connection.execute(
            "SELECT manifest_json FROM runs ORDER BY created_at DESC"
        ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def next_attempt_number(self, episode_id: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) FROM attempts WHERE episode_id = ?", (episode_id,)
        ).fetchone()
        return int(row[0]) + 1

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args) -> None:
        self.close()
