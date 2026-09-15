from datetime import UTC, datetime
from pathlib import Path

import pytest

from bankops.artifacts.models import CapabilityArtifact
from bankops.replay.cli import parse_inputs
from bankops.replay.evidence import create_replay_evidence
from bankops.replay.models import ReplayResult, ReplayStatus

_ARTIFACT_PATH = (
    Path(__file__).parents[2]
    / "evidence"
    / "artifacts"
    / "ledgerdesk-member-savings-balance.v1.json"
)


def load_artifact() -> CapabilityArtifact:
    return CapabilityArtifact.model_validate_json(_ARTIFACT_PATH.read_text())


def test_cli_parses_declared_string_input() -> None:
    assert parse_inputs(load_artifact(), ["member_id=M-10001"]) == {"member_id": "M-10001"}


def test_cli_rejects_unknown_and_duplicate_inputs() -> None:
    artifact = load_artifact()

    with pytest.raises(ValueError, match="Unknown input"):
        parse_inputs(artifact, ["customer_id=M-10001"])
    with pytest.raises(ValueError, match="more than once"):
        parse_inputs(artifact, ["member_id=M-10001", "member_id=M-10002"])


def test_evidence_redacts_sensitive_input_and_output() -> None:
    artifact = load_artifact()
    result = ReplayResult(
        status=ReplayStatus.SUCCESS,
        capability_id=artifact.capability_id,
        capability_version=artifact.capability_version,
        outputs={"savings_balance": "$4,250.75"},
        completed_step_ids=("extract-savings-balance",),
    )

    evidence = create_replay_evidence(
        artifact,
        {"member_id": "M-10001"},
        result,
        recorded_at=datetime(2026, 9, 15, tzinfo=UTC),
    )

    assert evidence.inputs == {"member_id": "[REDACTED]"}
    assert evidence.outputs == {"savings_balance": "[REDACTED]"}
    assert "M-10001" not in evidence.model_dump_json()
    assert "$4,250.75" not in evidence.model_dump_json()
