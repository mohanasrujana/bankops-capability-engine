from pathlib import Path

from bankops.replay.evidence import ReplayEvidence
from bankops.replay.models import ReplayStatus

_REPLAY_DIRECTORY = Path(__file__).parents[2] / "evidence" / "replay"


def load_evidence(filename: str) -> ReplayEvidence:
    return ReplayEvidence.model_validate_json((_REPLAY_DIRECTORY / filename).read_text())


def test_saved_success_evidence_is_complete_and_redacted() -> None:
    evidence = load_evidence("success.json")

    assert evidence.status is ReplayStatus.SUCCESS
    assert evidence.inputs == {"member_id": "[REDACTED]"}
    assert evidence.outputs == {"savings_balance": "[REDACTED]"}
    assert len(evidence.completed_step_ids) == 6
    assert evidence.error is None


def test_saved_business_outcome_stops_before_member_navigation() -> None:
    evidence = load_evidence("member-not-found.json")

    assert evidence.status is ReplayStatus.BUSINESS_OUTCOME
    assert evidence.outcome_code == "member_not_found"
    assert evidence.completed_step_ids == (
        "enter-member-id",
        "submit-member-search",
    )
    assert evidence.outputs == {}
