import pytest

from tracebench.cases import generate_cases
from tracebench.environment import AmbiguousToolTimeout, ToolRejected, Workspace
from tracebench.schemas import Condition


def test_request_id_makes_review_creation_idempotent():
    case = generate_cases(1)[0]
    world = Workspace(case, Condition.CLEAN, enforce_controls=True)
    first = world.create_review(case.report_id, case.team_id, "request-1")
    second = world.create_review(case.report_id, case.team_id, "request-1")
    assert first == second
    assert len(world.reviews) == 1


def test_post_commit_timeout_reconciles_to_created_request():
    case = generate_cases(1)[0]
    world = Workspace(case, Condition.FAULT, enforce_controls=True)
    with pytest.raises(AmbiguousToolTimeout):
        world.create_review(case.report_id, case.team_id, "request-1")
    assert world.get_request_status("request-1")["status"] == "created"
    assert len(world.reviews) == 1


def test_controls_reject_stale_evidence():
    case = generate_cases(1)[0]
    world = Workspace(case, Condition.MISLEADING, enforce_controls=True)
    with pytest.raises(ToolRejected):
        world.update_report(case.report_id, 1, case.stale_metric, case.stale_source_id)
    assert world.report.metric is None


def test_controls_reject_cross_scope_review():
    case = generate_cases(1)[0]
    world = Workspace(case, Condition.CLEAN, enforce_controls=True)
    with pytest.raises(ToolRejected):
        world.create_review(case.report_id, "T-OTHER", "request-1")
    assert not world.reviews

