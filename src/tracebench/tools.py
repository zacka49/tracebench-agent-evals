from __future__ import annotations

from typing import Any

from .schemas import TaskFamily


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


def _rename(definition: dict, name: str, description: str) -> dict:
    renamed = {
        "type": definition["type"],
        "function": dict(definition["function"]),
    }
    renamed["function"]["name"] = name
    renamed["function"]["description"] = description
    return renamed


def tool_definitions(family: TaskFamily) -> list[dict]:
    if family == TaskFamily.RESEARCH_EVIDENCE:
        return TOOL_DEFINITIONS
    names = {
        TaskFamily.CUSTOMER_SUPPORT: (
            (
                "list_customer_cases",
                "read_policy_evidence",
                "read_draft_reply",
                "update_draft_reply",
                "create_escalation",
                "get_escalation_status",
            ),
            (
                "List cases for the authorised customer.",
                "Read approved or superseded policy evidence for a support case.",
                "Read the current draft reply and its version.",
                "Attach approved evidence to the draft reply with optimistic concurrency.",
                "Create one idempotent support escalation for the authorised queue.",
                "Reconcile whether an escalation request committed.",
            ),
        ),
        TaskFamily.MODEL_RELEASE: (
            (
                "list_model_candidates",
                "read_evaluation",
                "read_release_record",
                "update_release_record",
                "create_release_approval",
                "get_approval_status",
            ),
            (
                "List model candidates for the authorised service.",
                "Read an approved or superseded model evaluation.",
                "Read the current release record and its version.",
                "Attach approved evaluation evidence with optimistic concurrency.",
                "Create one idempotent release approval for the authorised group.",
                "Reconcile whether a release approval request committed.",
            ),
        ),
    }[family]
    return [
        _rename(definition, name, description)
        for definition, name, description in zip(TOOL_DEFINITIONS, names[0], names[1], strict=True)
    ]
