import pytest
from pydantic import TypeAdapter, ValidationError

from bankops.discovery.models import DiscoveryDecision, DiscoveryObservation

DECISIONS = TypeAdapter(DiscoveryDecision)


@pytest.mark.parametrize(
    "payload",
    [
        {
            "kind": "act",
            "action": {
                "kind": "fill",
                "id": "enter-member",
                "description": "Enter member ID",
                "target": {"candidates": [{"kind": "label", "label": "Member ID"}]},
                "value_template": "{{ inputs.member_id }}",
            },
        },
        {"kind": "success", "checkpoint": {"kind": "url", "pattern": "/members/"}},
        {"kind": "stop", "reason": "dead_end", "message": "No available controls"},
        {"kind": "stop", "reason": "intervention_required", "message": "Login needed"},
        {"kind": "stop", "reason": "business_outcome", "message": "Member not found"},
    ],
)
def test_decision_round_trip(payload: dict[str, object]) -> None:
    decision = DECISIONS.validate_python(payload)
    assert DECISIONS.validate_json(DECISIONS.dump_json(decision)) == decision


@pytest.mark.parametrize(
    "payload",
    [
        {"kind": "execute_python", "code": "print('unsafe')"},
        {"kind": "act", "action": {"kind": "shell", "command": "ls"}},
        {"kind": "success"},
        {"kind": "success", "checkpoint": {"kind": "url", "pattern": ""}},
        {"kind": "stop", "reason": "timeout", "message": "Model owns no timer"},
        {"kind": "stop", "reason": "dead_end", "message": "  "},
        {"kind": "stop", "reason": "dead_end", "message": "x" * 1_001},
        {"kind": "stop", "reason": "dead_end", "message": "Blocked", "action": {}},
    ],
)
def test_decision_rejects_unsupported_or_ambiguous_payload(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        DECISIONS.validate_python(payload)


def test_observation_accepts_empty_page_and_explicit_truncation() -> None:
    observation = DiscoveryObservation.model_validate(
        {"url": "http://127.0.0.1:8000", "title": "", "visible_text": "", "truncated": False}
    )
    assert observation.visible_text == ""
    assert not observation.truncated


@pytest.mark.parametrize(
    ("field", "value"),
    [("title", "x" * 501), ("visible_text", "x" * 20_001), ("truncated", "false")],
)
def test_observation_rejects_oversized_or_coerced_state(field: str, value: object) -> None:
    payload: dict[str, object] = {
        "url": "http://127.0.0.1:8000",
        "title": "LedgerDesk",
        "visible_text": "Member ID",
        "truncated": False,
    }
    payload[field] = value
    with pytest.raises(ValidationError):
        DiscoveryObservation.model_validate(payload)
