from __future__ import annotations

import json
import sqlite3
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
                status TEXT NOT NULL,
                record_json TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def save(self, record: EpisodeRecord) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO episodes(episode_id, status, record_json) VALUES (?, ?, ?)",
            (record.episode_id, record.status, record.model_dump_json()),
        )
        self.connection.commit()

    def records(self) -> list[EpisodeRecord]:
        rows = self.connection.execute(
            "SELECT record_json FROM episodes ORDER BY episode_id"
        ).fetchall()
        return [EpisodeRecord.model_validate(json.loads(row[0])) for row in rows]

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args) -> None:
        self.close()
