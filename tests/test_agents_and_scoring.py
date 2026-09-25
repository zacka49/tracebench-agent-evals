import pytest

from tracebench.agents import (
    EpisodeTimeout,
    OllamaAgent,
    ScriptedAgent,
    TransformersAgent,
    _extract_json_object,
)
from tracebench.cases import generate_cases
from tracebench.environment import Workspace
from tracebench.schemas import Condition, FinalStatus, TaskFamily, Variant
from tracebench.scoring import score_episode


def run(condition: Condition, variant: Variant):
    case = generate_cases(1)[0]
    world = Workspace(case, condition, enforce_controls=variant.has_controls)
    outcome = ScriptedAgent().run(world, case, variant, 12)
    return score_episode(
        world, case, outcome.final_message, outcome.status, outcome.tool_calls, 1.0
    )


def test_baseline_duplicates_after_ambiguous_timeout():
    score = run(Condition.FAULT, Variant.BASELINE)
    assert not score.verified_completion
    assert score.duplicate_effects == 1
    assert score.false_completion


def test_recovery_variant_reconciles_ambiguous_timeout():
    score = run(Condition.FAULT, Variant.CONTROLS_AND_RECOVERY)
    assert score.verified_completion
    assert score.fault_recovered
    assert score.duplicate_effects == 0


def test_misleading_content_changes_baseline_not_controlled_agent():
    baseline = run(Condition.MISLEADING, Variant.BASELINE)
    controlled = run(Condition.MISLEADING, Variant.CONTROLS_AND_RECOVERY)
    assert not baseline.report_correct
    assert baseline.false_completion
    assert controlled.verified_completion


def test_negated_completion_is_not_a_false_completion_claim():
    case = generate_cases(1)[0]
    world = Workspace(case, Condition.CLEAN, enforce_controls=True)
    score = score_episode(
        world,
        case,
        "The task was not completed.",
        FinalStatus.BLOCKED,
        0,
        1.0,
    )
    assert not score.false_completion


def test_expired_deadline_prevents_first_tool_call():
    case = generate_cases(1)[0]
    world = Workspace(case, Condition.CLEAN, enforce_controls=True)
    with pytest.raises(EpisodeTimeout) as error:
        ScriptedAgent().run(
            world, case, Variant.CONTROLS_AND_RECOVERY, limit=12, wall_seconds=0
        )
    assert error.value.tool_calls == 0
    assert world.events == []


def test_action_controls_isolated_from_prompt_guidance():
    score = run(Condition.MISLEADING, Variant.ACTION_CONTROLS)
    assert not score.verified_completion
    assert score.attempted_violations == 1
    assert not score.prohibited_action_executed


def test_model_prompt_requires_observed_tool_state():
    prompt = OllamaAgent.system_prompt(Variant.BASELINE)
    assert "MUST call" in prompt
    assert "zero tool calls is invalid" in prompt


def test_transformers_protocol_extracts_first_json_object():
    text = 'prefix {"tool":{"name":"read_report","arguments":{}}} suffix'
    assert _extract_json_object(text) == {
        "tool": {"name": "read_report", "arguments": {}}
    }
    assert _extract_json_object("no object") is None


def test_transformers_prompt_requires_json_and_recovery():
    prompt = TransformersAgent.system_prompt(Variant.CONTROLS_AND_RECOVERY, [])
    assert "exactly one JSON object" in prompt
    assert "same request ID" in prompt


@pytest.mark.parametrize("family_index", [0, 1, 2])
def test_each_task_family_completes_with_recovery_controls(family_index: int):
    case = generate_cases(3)[family_index]
    world = Workspace(case, Condition.FAULT, enforce_controls=True)
    outcome = ScriptedAgent().run(world, case, Variant.CONTROLS_AND_RECOVERY, 12)
    score = score_episode(
        world, case, outcome.final_message, outcome.status, outcome.tool_calls, 1.0
    )
    assert case.family == list(TaskFamily)[family_index]
    assert score.verified_completion
    assert {event.tool for event in world.events} <= set(case.tool_names.values())
