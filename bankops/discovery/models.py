from typing import Annotated, Literal

from pydantic import Field, HttpUrl, StringConstraints

from bankops.artifacts.models import ActionStep, Checkpoint, LocatorPlan, StrictModel


class DiscoveryRequest(StrictModel):
    """Validated discovery input; the execution loop must enforce policy and limits."""

    goal: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    target_url: HttpUrl
    inputs: dict[str, str] = Field(default_factory=dict)
    max_steps: int = Field(default=15, ge=1, le=50, strict=True)
    timeout_seconds: int = Field(default=120, ge=1, le=300, strict=True)


class ControlObservation(StrictModel):
    """Native control metadata; name_hint is not a computed accessible name."""

    tag: Literal["input", "textarea", "select", "button", "a"]
    input_type: str | None = Field(default=None, max_length=100)
    name_hint: str = Field(max_length=500)
    target: LocatorPlan
    disabled: bool = Field(strict=True)
    readonly: bool = Field(strict=True)


class DiscoveryObservation(StrictModel):
    """Bounded visible page state for model input, not a redacted log record."""

    url: HttpUrl
    title: str = Field(max_length=500)
    visible_text: str = Field(max_length=20_000)
    truncated: bool = Field(strict=True)
    controls: tuple[ControlObservation, ...] = Field(default=(), max_length=100)


class ActionDecision(StrictModel):
    """Propose one action; validation does not grant permission to execute it."""

    kind: Literal["act"] = "act"
    action: ActionStep


class SuccessDecision(StrictModel):
    """Propose completion; the engine must verify the checkpoint and outputs."""

    kind: Literal["success"] = "success"
    checkpoint: Checkpoint


class StopDecision(StrictModel):
    """Request a non-success stop, with a short explanation for the operator."""

    kind: Literal["stop"] = "stop"
    reason: Literal["dead_end", "intervention_required", "business_outcome"]
    message: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1_000)
    ]


type DiscoveryDecision = Annotated[
    ActionDecision | SuccessDecision | StopDecision,
    Field(discriminator="kind"),
]
