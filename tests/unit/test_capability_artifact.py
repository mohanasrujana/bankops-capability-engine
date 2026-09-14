import pytest
from pydantic import ValidationError

from bankops.artifacts.models import CapabilityArtifact


def valid_artifact_data() -> dict[str, object]:
    return {
        "capability_id": "lookup-member-savings-balance",
        "capability_version": 1,
        "description": "Look up a member and read the savings balance",
        "compatibility": {
            "application": "LedgerDesk",
            "family": "ledgerdesk-local",
            "entrypoint": "http://127.0.0.1:8000/",
        },
        "inputs": [
            {
                "name": "member_id",
                "value_type": "string",
                "description": "Synthetic member identifier",
            }
        ],
        "outputs": [
            {
                "name": "savings_balance",
                "value_type": "string",
                "description": "Displayed savings balance",
                "sensitive": True,
            }
        ],
        "steps": [
            {
                "kind": "fill",
                "id": "enter-member-id",
                "description": "Enter the member ID",
                "target": {"candidates": [{"kind": "label", "label": "Member ID"}]},
                "value_template": "{{ inputs.member_id }}",
            },
            {
                "kind": "click",
                "id": "submit-search",
                "description": "Submit the search",
                "target": {"candidates": [{"kind": "role", "role": "button", "name": "Search"}]},
            },
            {
                "kind": "extract",
                "id": "read-savings-balance",
                "description": "Read the displayed savings balance",
                "target": {"candidates": [{"kind": "label", "label": "Savings Balance"}]},
                "output_name": "savings_balance",
            },
        ],
        "outcomes": [
            {
                "code": "member_not_found",
                "description": "The member does not exist",
                "checkpoint": {
                    "kind": "element",
                    "target": {"candidates": [{"kind": "text", "text": "Member Not Found"}]},
                },
            }
        ],
        "success_checkpoint": {
            "kind": "element",
            "target": {"candidates": [{"kind": "label", "label": "Savings Balance"}]},
        },
        "policy": {
            "allowed_action_kinds": ["fill", "click", "extract"],
            "allowed_url_prefixes": ["http://127.0.0.1:8000/"],
        },
    }


def test_complete_artifact_parses_and_serializes() -> None:
    artifact = CapabilityArtifact.model_validate(valid_artifact_data())

    assert artifact.schema_version == "1.0"
    assert artifact.steps[0].kind == "fill"
    assert artifact.model_dump(mode="json")["inputs"][0]["name"] == "member_id"


def test_artifact_rejects_undeclared_input_reference() -> None:
    data = valid_artifact_data()
    steps = data["steps"]
    assert isinstance(steps, list)
    steps[0]["value_template"] = "{{ inputs.customer_id }}"

    with pytest.raises(ValidationError, match="references undeclared inputs"):
        CapabilityArtifact.model_validate(data)


def test_artifact_rejects_output_without_extraction() -> None:
    data = valid_artifact_data()
    steps = data["steps"]
    assert isinstance(steps, list)
    steps.pop()

    with pytest.raises(ValidationError, match="no extraction step"):
        CapabilityArtifact.model_validate(data)


def test_artifact_rejects_action_missing_from_allowlist() -> None:
    data = valid_artifact_data()
    policy = data["policy"]
    assert isinstance(policy, dict)
    policy["allowed_action_kinds"] = ["fill", "extract"]

    with pytest.raises(ValidationError, match="not allowed by policy"):
        CapabilityArtifact.model_validate(data)


def test_artifact_rejects_irreversible_action() -> None:
    data = valid_artifact_data()
    steps = data["steps"]
    assert isinstance(steps, list)
    steps[1]["risk"] = "irreversible"

    with pytest.raises(ValidationError, match="cannot contain irreversible"):
        CapabilityArtifact.model_validate(data)


def test_artifact_rejects_duplicate_step_ids() -> None:
    data = valid_artifact_data()
    steps = data["steps"]
    assert isinstance(steps, list)
    steps[1]["id"] = "enter-member-id"

    with pytest.raises(ValidationError, match="duplicate step IDs"):
        CapabilityArtifact.model_validate(data)
