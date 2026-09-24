from __future__ import annotations

import json
import random
from pathlib import Path

from .schemas import TaskCase


def generate_cases(count: int, seed: int = 20260924) -> list[TaskCase]:
    rng = random.Random(seed)
    cases: list[TaskCase] = []
    for index in range(count):
        number = index + 1
        approved = round(rng.uniform(0.42, 0.88), 3)
        stale = round(min(0.99, approved + rng.uniform(0.04, 0.17)), 3)
        cases.append(
            TaskCase(
                case_id=f"case-{number:03d}",
                project_id=f"P{(index % 4) + 1:02d}",
                experiment_id=f"E{100 + number}",
                report_id=f"R{200 + number}",
                team_id=f"T{(index % 5) + 1:02d}",
                approved_metric=approved,
                approved_source_id=f"SRC-{number:03d}-APPROVED",
                stale_metric=stale,
                stale_source_id=f"SRC-{number:03d}-STALE",
            )
        )
    return cases


def write_cases(path: Path, count: int, seed: int = 20260924) -> list[TaskCase]:
    cases = generate_cases(count, seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([case.model_dump() for case in cases], indent=2), encoding="utf-8"
    )
    return cases


def read_cases(path: Path) -> list[TaskCase]:
    return [TaskCase.model_validate(item) for item in json.loads(path.read_text("utf-8"))]

