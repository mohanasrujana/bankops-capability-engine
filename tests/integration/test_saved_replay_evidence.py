from pathlib import Path

from bankops.logging.replay import ReplayEvent, ReplayEventType
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


def test_saved_structured_log_is_ordered_and_value_free() -> None:
    path = _REPLAY_DIRECTORY / "success.jsonl"
    events = [ReplayEvent.model_validate_json(line) for line in path.read_text().splitlines()]

    assert len(events) == 14
    assert [event.sequence for event in events] == list(range(1, 15))
    assert events[0].event_type is ReplayEventType.RUN_STARTED
    assert events[-1].event_type is ReplayEventType.RUN_COMPLETED
    assert len({event.run_id for event in events}) == 1
    serialized = path.read_text()
    assert "M-10001" not in serialized
    assert "$4,250.75" not in serialized
