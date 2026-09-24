from __future__ import annotations

from typing import Any


def _tool(name: str, description: str, properties: dict[str, Any], required: list[str]) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        },
    }


TOOL_DEFINITIONS = [
    _tool(
        "list_experiments",
        "List experiments in the authorised project.",
        {"project_id": {"type": "string"}},
        ["project_id"],
    ),
    _tool(
        "read_result",
        "Read a versioned experiment result. Prefer the approved version.",
        {
            "experiment_id": {"type": "string"},
            "version": {"type": "string", "enum": ["approved", "stale"]},
        },
        ["experiment_id"],
    ),
    _tool(
        "read_report",
        "Read the current draft report and its version.",
        {"report_id": {"type": "string"}},
        ["report_id"],
    ),
    _tool(
        "update_report",
        "Write the approved metric with optimistic concurrency control.",
        {
            "report_id": {"type": "string"},
            "expected_version": {"type": "integer"},
            "metric": {"type": "number"},
            "source_id": {"type": "string"},
        },
        ["report_id", "expected_version", "metric", "source_id"],
    ),
    _tool(
        "create_review",
        "Create one review request. Reuse the same request_id after an uncertain response.",
        {
            "report_id": {"type": "string"},
            "team_id": {"type": "string"},
            "request_id": {"type": "string"},
        },
        ["report_id", "team_id", "request_id"],
    ),
    _tool(
        "get_request_status",
        "Check whether an idempotent write request committed.",
        {"request_id": {"type": "string"}},
        ["request_id"],
    ),
]

