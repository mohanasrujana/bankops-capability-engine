from enum import StrEnum

from pydantic import Field

from bankops.artifacts.models import RiskLevel, StrictModel

type ReplayValue = str | int | float | bool


class ReplayStatus(StrEnum):
    SUCCESS = "success"
    BUSINESS_OUTCOME = "business_outcome"
    INTERVENTION_REQUIRED = "intervention_required"
    FAILURE = "failure"


class ReplayError(StrictModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    step_id: str | None = None
    expected: str | None = None
    observed: str | None = None


class InterventionRequest(StrictModel):
    reason: str = Field(min_length=1)
    step_id: str = Field(min_length=1)
    action_kind: str = Field(min_length=1)
    risk: RiskLevel


class ReplayResult(StrictModel):
    status: ReplayStatus
    capability_id: str = Field(min_length=1)
    capability_version: int = Field(ge=1)
    outputs: dict[str, ReplayValue] = Field(default_factory=dict)
    outcome_code: str | None = None
    completed_step_ids: tuple[str, ...] = ()
    error: ReplayError | None = None
    intervention: InterventionRequest | None = None
