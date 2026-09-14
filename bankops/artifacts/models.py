import re
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RoleLocator(StrictModel):
    kind: Literal["role"] = "role"
    role: str = Field(min_length=1)
    name: str = Field(min_length=1)
    exact: bool = True


class LabelLocator(StrictModel):
    kind: Literal["label"] = "label"
    label: str = Field(min_length=1)
    exact: bool = True


class TextLocator(StrictModel):
    kind: Literal["text"] = "text"
    text: str = Field(min_length=1)
    exact: bool = True


class CssLocator(StrictModel):
    kind: Literal["css"] = "css"
    selector: str = Field(min_length=1)


class CoordinateLocator(StrictModel):
    kind: Literal["coordinate"] = "coordinate"
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    viewport_width: int = Field(gt=0)
    viewport_height: int = Field(gt=0)


type Locator = Annotated[
    RoleLocator | LabelLocator | TextLocator | CssLocator | CoordinateLocator,
    Field(discriminator="kind"),
]


class LocatorPlan(StrictModel):
    candidates: tuple[Locator, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def require_coordinate_fallback_to_be_last(self) -> Self:
        coordinate_indexes = [
            index
            for index, candidate in enumerate(self.candidates)
            if candidate.kind == "coordinate"
        ]

        if coordinate_indexes and coordinate_indexes[-1] != len(self.candidates) - 1:
            raise ValueError("A coordinate locator must be the final fallback")

        if len(coordinate_indexes) > 1:
            raise ValueError("A locator plan may contain at most one coordinate fallback")

        return self


class RiskLevel(StrEnum):
    SAFE = "safe"
    REVERSIBLE = "reversible"
    RISKY = "risky"
    IRREVERSIBLE = "irreversible"


type StepId = Annotated[
    str,
    Field(min_length=1, pattern=r"^[a-z][a-z0-9-]*$"),
]


class ClickStep(StrictModel):
    kind: Literal["click"] = "click"
    id: StepId
    description: str = Field(min_length=1)
    target: LocatorPlan
    risk: RiskLevel = RiskLevel.REVERSIBLE
    timeout_ms: int = Field(default=5_000, ge=100, le=30_000)


class FillStep(StrictModel):
    kind: Literal["fill"] = "fill"
    id: StepId
    description: str = Field(min_length=1)
    target: LocatorPlan
    value_template: str = Field(min_length=1)
    risk: RiskLevel = RiskLevel.REVERSIBLE
    timeout_ms: int = Field(default=5_000, ge=100, le=30_000)


class ExtractStep(StrictModel):
    kind: Literal["extract"] = "extract"
    id: StepId
    description: str = Field(min_length=1)
    target: LocatorPlan
    output_name: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    source: Literal["text", "value"] = "text"
    risk: RiskLevel = RiskLevel.SAFE
    timeout_ms: int = Field(default=5_000, ge=100, le=30_000)


class WaitForStep(StrictModel):
    kind: Literal["wait_for"] = "wait_for"
    id: StepId
    description: str = Field(min_length=1)
    target: LocatorPlan
    state: Literal["visible", "hidden", "enabled"] = "visible"
    risk: RiskLevel = RiskLevel.SAFE
    timeout_ms: int = Field(default=5_000, ge=100, le=30_000)


type ActionStep = Annotated[
    ClickStep | FillStep | ExtractStep | WaitForStep,
    Field(discriminator="kind"),
]


class ElementCheckpoint(StrictModel):
    kind: Literal["element"] = "element"
    target: LocatorPlan
    state: Literal["visible", "hidden"] = "visible"
    timeout_ms: int = Field(default=5_000, ge=100, le=30_000)


class UrlCheckpoint(StrictModel):
    kind: Literal["url"] = "url"
    pattern: str = Field(min_length=1)
    timeout_ms: int = Field(default=5_000, ge=100, le=30_000)


type Checkpoint = Annotated[
    ElementCheckpoint | UrlCheckpoint,
    Field(discriminator="kind"),
]


class ValueType(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"


class InputParameter(StrictModel):
    name: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    value_type: ValueType
    description: str = Field(min_length=1)
    required: bool = True
    sensitive: bool = False


class OutputParameter(StrictModel):
    name: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    value_type: ValueType
    description: str = Field(min_length=1)
    sensitive: bool = False


class ApplicationCompatibility(StrictModel):
    application: str = Field(min_length=1)
    family: str = Field(min_length=1)
    entrypoint: str = Field(min_length=1)


class OutcomeDefinition(StrictModel):
    code: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    description: str = Field(min_length=1)
    checkpoint: Checkpoint


class ExecutionPolicy(StrictModel):
    allowed_action_kinds: frozenset[Literal["click", "fill", "extract", "wait_for"]]
    allowed_url_prefixes: tuple[str, ...] = Field(min_length=1)
    require_approval_for: frozenset[RiskLevel] = frozenset({RiskLevel.RISKY})


_INPUT_REFERENCE = re.compile(r"{{\s*inputs\.([a-z][a-z0-9_]*)\s*}}")


class CapabilityArtifact(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    capability_id: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9-]*$")
    capability_version: int = Field(ge=1)
    description: str = Field(min_length=1)
    compatibility: ApplicationCompatibility
    inputs: tuple[InputParameter, ...]
    outputs: tuple[OutputParameter, ...]
    steps: tuple[ActionStep, ...] = Field(min_length=1)
    outcomes: tuple[OutcomeDefinition, ...] = Field(min_length=1)
    success_checkpoint: Checkpoint
    policy: ExecutionPolicy

    @model_validator(mode="after")
    def validate_contract_relationships(self) -> Self:
        input_names = [parameter.name for parameter in self.inputs]
        output_names = [parameter.name for parameter in self.outputs]
        step_ids = [step.id for step in self.steps]
        outcome_codes = [outcome.code for outcome in self.outcomes]

        self._require_unique("input names", input_names)
        self._require_unique("output names", output_names)
        self._require_unique("step IDs", step_ids)
        self._require_unique("outcome codes", outcome_codes)

        declared_inputs = set(input_names)
        extracted_outputs: list[str] = []
        for step in self.steps:
            if step.kind not in self.policy.allowed_action_kinds:
                raise ValueError(f"Action kind '{step.kind}' is not allowed by policy")
            if step.risk is RiskLevel.IRREVERSIBLE:
                raise ValueError("Reusable artifacts cannot contain irreversible actions")
            if (
                step.risk is RiskLevel.RISKY
                and RiskLevel.RISKY not in self.policy.require_approval_for
            ):
                raise ValueError("Risky actions must require approval")
            if isinstance(step, FillStep):
                references = set(_INPUT_REFERENCE.findall(step.value_template))
                unknown = references - declared_inputs
                if unknown:
                    raise ValueError(
                        f"Fill step '{step.id}' references undeclared inputs: "
                        f"{', '.join(sorted(unknown))}"
                    )
            if isinstance(step, ExtractStep):
                extracted_outputs.append(step.output_name)

        undeclared_outputs = set(extracted_outputs) - set(output_names)
        if undeclared_outputs:
            raise ValueError(
                "Extraction steps produce undeclared outputs: "
                f"{', '.join(sorted(undeclared_outputs))}"
            )
        missing_outputs = set(output_names) - set(extracted_outputs)
        if missing_outputs:
            raise ValueError(
                f"Declared outputs have no extraction step: {', '.join(sorted(missing_outputs))}"
            )
        self._require_unique("extracted output names", extracted_outputs)
        return self

    @staticmethod
    def _require_unique(label: str, values: list[str]) -> None:
        if len(values) != len(set(values)):
            raise ValueError(f"Artifact contains duplicate {label}")
