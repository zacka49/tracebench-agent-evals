from tracebench.agents import ScriptedAgent
from tracebench.cases import generate_cases
from tracebench.environment import Workspace
from tracebench.schemas import Condition, Variant
from tracebench.scoring import score_episode


def run(condition: Condition, variant: Variant):
    case = generate_cases(1)[0]
    world = Workspace(case, condition, enforce_controls=variant.has_controls)
    outcome = ScriptedAgent().run(world, case, variant, 12)
    return score_episode(world, case, outcome.final_message, outcome.tool_calls, 1.0)


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

