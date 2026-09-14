import pytest
from pydantic import TypeAdapter, ValidationError

from bankops.artifacts.models import ActionStep, RiskLevel

_ACTION_ADAPTER = TypeAdapter(ActionStep)


def test_fill_step_parses_as_reversible_action() -> None:
    action = _ACTION_ADAPTER.validate_python(
        {
            "kind": "fill",
            "id": "enter-member-id",
            "description": "Enter the invocation member ID",
            "target": {
                "candidates": [
                    {
                        "kind": "label",
                        "label": "Member ID",
                    }
                ]
            },
            "value_template": "{{ inputs.member_id }}",
        }
    )

    assert action.kind == "fill"
    assert action.risk is RiskLevel.REVERSIBLE
    assert action.timeout_ms == 5_000


def test_extract_step_defaults_to_safe_text_extraction() -> None:
    action = _ACTION_ADAPTER.validate_python(
        {
            "kind": "extract",
            "id": "read-savings-balance",
            "description": "Read the displayed savings balance",
            "target": {
                "candidates": [
                    {
                        "kind": "label",
                        "label": "Savings Balance",
                    }
                ]
            },
            "output_name": "savings_balance",
        }
    )

    assert action.kind == "extract"
    assert action.risk is RiskLevel.SAFE
    assert action.source == "text"


def test_action_discriminator_rejects_unknown_action_kind() -> None:
    with pytest.raises(ValidationError, match="Input tag 'drag' found"):
        _ACTION_ADAPTER.validate_python(
            {
                "kind": "drag",
                "id": "move-control",
                "description": "Unsupported action",
                "target": {
                    "candidates": [
                        {
                            "kind": "text",
                            "text": "Control",
                        }
                    ]
                },
            }
        )


def test_action_rejects_non_slug_step_id() -> None:
    with pytest.raises(ValidationError, match="String should match pattern"):
        _ACTION_ADAPTER.validate_python(
            {
                "kind": "click",
                "id": "Click Search",
                "description": "Click Search",
                "target": {
                    "candidates": [
                        {
                            "kind": "role",
                            "role": "button",
                            "name": "Search",
                        }
                    ]
                },
            }
        )


def test_action_timeout_is_bounded() -> None:
    with pytest.raises(ValidationError, match="less than or equal to 30000"):
        _ACTION_ADAPTER.validate_python(
            {
                "kind": "wait_for",
                "id": "wait-forever",
                "description": "An invalid unbounded wait",
                "target": {
                    "candidates": [
                        {
                            "kind": "text",
                            "text": "Eventually",
                        }
                    ]
                },
                "timeout_ms": 60_000,
            }
        )
