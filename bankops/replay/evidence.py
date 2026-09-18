from datetime import UTC, datetime

from bankops.artifacts.models import CapabilityArtifact, StrictModel
from bankops.replay.models import (
    InterventionRequest,
    ReplayError,
    ReplayResult,
    ReplayStatus,
    ReplayValue,
)

_REDACTED = "[REDACTED]"


class ReplayEvidence(StrictModel):
    recorded_at: datetime
    schema_version: str
    capability_id: str
    capability_version: int
    status: ReplayStatus
    inputs: dict[str, ReplayValue]
    outputs: dict[str, ReplayValue]
    outcome_code: str | None
    completed_step_ids: tuple[str, ...]
    error: ReplayError | None
    intervention: InterventionRequest | None = None


def create_replay_evidence(
    artifact: CapabilityArtifact,
    inputs: dict[str, ReplayValue],
    result: ReplayResult,
    *,
    recorded_at: datetime | None = None,
) -> ReplayEvidence:
    sensitive_inputs = {parameter.name for parameter in artifact.inputs if parameter.sensitive}
    sensitive_outputs = {parameter.name for parameter in artifact.outputs if parameter.sensitive}
    return ReplayEvidence(
        recorded_at=recorded_at or datetime.now(UTC),
        schema_version=artifact.schema_version,
        capability_id=artifact.capability_id,
        capability_version=artifact.capability_version,
        status=result.status,
        inputs={
            name: _REDACTED if name in sensitive_inputs else value for name, value in inputs.items()
        },
        outputs={
            name: _REDACTED if name in sensitive_outputs else value
            for name, value in result.outputs.items()
        },
        outcome_code=result.outcome_code,
        completed_step_ids=result.completed_step_ids,
        error=result.error,
        intervention=result.intervention,
    )
