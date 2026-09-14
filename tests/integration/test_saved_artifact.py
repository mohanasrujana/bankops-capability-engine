from pathlib import Path

from bankops.artifacts.models import CapabilityArtifact

_ARTIFACT_PATH = (
    Path(__file__).parents[2]
    / "evidence"
    / "artifacts"
    / "ledgerdesk-member-savings-balance.v1.json"
)


def test_saved_ledgerdesk_artifact_matches_contract() -> None:
    artifact = CapabilityArtifact.model_validate_json(_ARTIFACT_PATH.read_text())

    assert artifact.capability_id == "lookup-member-savings-balance"
    assert artifact.capability_version == 1
    assert [step.id for step in artifact.steps] == [
        "enter-member-id",
        "submit-member-search",
        "wait-for-open-member",
        "open-member",
        "wait-for-savings-balance",
        "extract-savings-balance",
    ]
    assert {outcome.code for outcome in artifact.outcomes} == {
        "invalid_member_id",
        "member_not_found",
    }
    assert artifact.outputs[0].sensitive is True
