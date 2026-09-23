import pytest
from pydantic import ValidationError

from bankops.discovery.models import DiscoveryRequest


def test_request_round_trips_with_named_inputs() -> None:
    request = DiscoveryRequest.model_validate(
        {
            "goal": "  Find the member's savings balance  ",
            "target_url": "http://127.0.0.1:8000",
            "inputs": {"member_id": "M-10001"},
        }
    )

    assert request.goal == "Find the member's savings balance"
    assert request.inputs == {"member_id": "M-10001"}
    assert request.max_steps == 15
    assert request.timeout_seconds == 120
    assert DiscoveryRequest.model_validate_json(request.model_dump_json()) == request


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("goal", ""),
        ("goal", " \n\t"),
        ("target_url", "not-a-url"),
        ("target_url", "file:///etc/passwd"),
        ("max_steps", 0),
        ("max_steps", 51),
        ("max_steps", True),
        ("max_steps", "15"),
        ("timeout_seconds", 0),
        ("timeout_seconds", 301),
        ("timeout_seconds", 1.5),
        ("inputs", {"member_id": 10001}),
        ("unknown_option", True),
    ],
)
def test_request_rejects_invalid_input(field: str, value: object) -> None:
    payload: dict[str, object] = {
        "goal": "Find the savings balance",
        "target_url": "http://127.0.0.1:8000",
    }
    payload[field] = value

    with pytest.raises(ValidationError):
        DiscoveryRequest.model_validate(payload)


@pytest.mark.parametrize(("steps", "seconds"), [(1, 1), (50, 300)])
def test_request_accepts_limit_boundaries(steps: int, seconds: int) -> None:
    request = DiscoveryRequest.model_validate(
        {
            "goal": "Find the savings balance",
            "target_url": "https://example.com",
            "max_steps": steps,
            "timeout_seconds": seconds,
        }
    )
    assert request.max_steps == steps
    assert request.timeout_seconds == seconds


def test_request_defaults_are_independent_and_attributes_are_frozen() -> None:
    payload = {"goal": "Find the balance", "target_url": "http://127.0.0.1:8000"}
    first = DiscoveryRequest.model_validate(payload)
    second = DiscoveryRequest.model_validate(payload)
    first.inputs["member_id"] = "M-10001"
    assert second.inputs == {}

    with pytest.raises(ValidationError, match="frozen"):
        first.max_steps = 20
