import asyncio
import re
from enum import StrEnum
from typing import Protocol, Self
from urllib.parse import unquote, urlsplit

from pydantic import Field, model_validator

from bankops.artifacts.models import (
    ActionStep,
    Checkpoint,
    ClickStep,
    ExecutionPolicy,
    ExtractStep,
    FillStep,
    OutcomeDefinition,
    RiskLevel,
    StrictModel,
    WaitForStep,
)
from bankops.discovery.models import DiscoveryObservation, DiscoveryRequest
from bankops.discovery.provider import DecisionContext, DecisionProvider, DecisionProviderError
from bankops.surfaces.base import SurfaceAdapter, SurfaceError


class DiscoveryContract(StrictModel):
    """Trusted caller criteria, never supplied or edited by the model."""

    policy: ExecutionPolicy
    success_checkpoint: Checkpoint
    output_names: tuple[str, ...] = Field(min_length=1, max_length=50)
    outcomes: tuple[OutcomeDefinition, ...] = ()

    @model_validator(mode="after")
    def require_unique_names(self) -> Self:
        if len(set(self.output_names)) != len(self.output_names) or any(
            re.fullmatch(r"[a-z][a-z0-9_]*", name) is None for name in self.output_names
        ):
            raise ValueError("Output names must be unique identifiers")
        if len({outcome.code for outcome in self.outcomes}) != len(self.outcomes):
            raise ValueError("Outcome codes must be unique")
        return self


class DiscoveryStatus(StrEnum):
    SUCCESS = "success"
    BUSINESS_OUTCOME = "business_outcome"
    DEAD_END = "dead_end"
    INTERVENTION_REQUIRED = "intervention_required"
    MAX_STEPS = "max_steps"
    TIMEOUT = "timeout"
    FAILURE = "failure"


class DiscoveryResult(StrictModel):
    """Runtime result, not redacted evidence or an emitted capability artifact."""

    status: DiscoveryStatus
    completed_steps: tuple[ActionStep, ...] = ()
    outputs: dict[str, str] = Field(default_factory=dict)
    decision_count: int = Field(default=0, ge=0)
    code: str | None = None
    step_id: str | None = None


class ObservationCollector(Protocol):
    async def observe(self) -> DiscoveryObservation: ...


class ActionAuthorizer(Protocol):
    """Trusted policy/approval boundary; must assess actions independently of model risk."""

    async def authorize(self, step: ActionStep, observation: DiscoveryObservation) -> bool: ...


def _url_allowed(url: str, policy: ExecutionPolicy) -> bool:
    target = urlsplit(url)
    if target.scheme not in {"http", "https"} or target.username or target.password:
        return False
    path = unquote(target.path)
    if any(segment in {".", ".."} for segment in path.split("/")):
        return False
    for prefix in policy.allowed_url_prefixes:
        allowed = urlsplit(prefix)
        if allowed.username or allowed.password or allowed.query or allowed.fragment:
            continue
        if (target.scheme, target.netloc) != (allowed.scheme, allowed.netloc):
            continue
        boundary = unquote(allowed.path).rstrip("/")
        if path == boundary or path.startswith(boundary + "/"):
            return True
    return False


class DiscoveryEngine:
    def __init__(
        self,
        surface: SurfaceAdapter,
        collector: ObservationCollector,
        provider: DecisionProvider,
        *,
        authorizer: ActionAuthorizer | None = None,
    ) -> None:
        self._surface = surface
        self._collector = collector
        self._provider = provider
        self._authorizer = authorizer

    async def discover(
        self, request: DiscoveryRequest, contract: DiscoveryContract
    ) -> DiscoveryResult:
        # Frozen model fields can contain mutable input dictionaries.
        request = request.model_copy(deep=True)
        completed: list[ActionStep] = []
        outputs: dict[str, str] = {}
        count = 0
        current_id: str | None = None

        def result(status: DiscoveryStatus, code: str | None = None) -> DiscoveryResult:
            return DiscoveryResult(
                status=status,
                code=code,
                completed_steps=tuple(completed),
                outputs=dict(outputs),
                decision_count=count,
                step_id=current_id,
            )

        if not _url_allowed(str(request.target_url), contract.policy):
            return result(DiscoveryStatus.FAILURE, "target_not_allowed")
        try:
            async with asyncio.timeout(request.timeout_seconds):
                await self._surface.navigate(str(request.target_url))
                observation = await self._collector.observe()
                for _ in range(request.max_steps):
                    current_id = None
                    if not _url_allowed(str(observation.url), contract.policy):
                        return result(DiscoveryStatus.FAILURE, "target_not_allowed")
                    for outcome in contract.outcomes:
                        if await self._surface.checkpoint_is_met(outcome.checkpoint):
                            return result(DiscoveryStatus.BUSINESS_OUTCOME, outcome.code)
                    count += 1
                    decision = await self._provider.decide(
                        DecisionContext(
                            request=request.model_copy(deep=True),
                            observation=observation,
                            completed_steps=tuple(completed),
                            output_names=tuple(outputs),
                            expected_output_names=contract.output_names,
                            success_checkpoint=contract.success_checkpoint,
                        )
                    )
                    # A model request may take seconds; refresh state before acting.
                    observation = await self._collector.observe()
                    if not _url_allowed(str(observation.url), contract.policy):
                        return result(DiscoveryStatus.FAILURE, "target_not_allowed")
                    if decision.kind == "stop":
                        if decision.reason == "business_outcome":
                            for outcome in contract.outcomes:
                                if await self._surface.checkpoint_is_met(outcome.checkpoint):
                                    return result(DiscoveryStatus.BUSINESS_OUTCOME, outcome.code)
                            return result(DiscoveryStatus.FAILURE, "unverified_business_outcome")
                        return result(DiscoveryStatus(decision.reason), "model_requested_stop")
                    if decision.kind == "success":
                        if set(outputs) != set(contract.output_names):
                            return result(DiscoveryStatus.FAILURE, "missing_outputs")
                        if not await self._surface.wait_for_checkpoint(contract.success_checkpoint):
                            return result(DiscoveryStatus.FAILURE, "trusted_checkpoint_not_met")
                        if not await self._surface.wait_for_checkpoint(decision.checkpoint):
                            return result(DiscoveryStatus.FAILURE, "proposed_checkpoint_not_met")
                        observation = await self._collector.observe()
                        if not _url_allowed(str(observation.url), contract.policy):
                            return result(DiscoveryStatus.FAILURE, "target_not_allowed")
                        return result(DiscoveryStatus.SUCCESS)

                    step = decision.action
                    current_id = step.id
                    if step.id in {previous.id for previous in completed}:
                        return result(DiscoveryStatus.FAILURE, "duplicate_step_id")
                    if step.kind not in contract.policy.allowed_action_kinds:
                        return result(DiscoveryStatus.FAILURE, "action_not_allowed")
                    if step.risk is RiskLevel.IRREVERSIBLE:
                        return result(DiscoveryStatus.FAILURE, "irreversible_action")
                    if isinstance(step, ExtractStep | WaitForStep) and step.retry is not None:
                        return result(DiscoveryStatus.FAILURE, "discovery_retry_not_supported")
                    value: str | None = None
                    if isinstance(step, FillStep):
                        match = re.fullmatch(
                            r"{{\s*inputs\.([a-z][a-z0-9_]*)\s*}}", step.value_template
                        )
                        if match is None or match.group(1) not in request.inputs:
                            return result(DiscoveryStatus.FAILURE, "invalid_input_reference")
                        value = request.inputs[match.group(1)]
                    if isinstance(step, ExtractStep) and (
                        step.output_name not in contract.output_names or step.output_name in outputs
                    ):
                        return result(DiscoveryStatus.FAILURE, "invalid_output_name")
                    if isinstance(step, ClickStep | FillStep):
                        control = next(
                            (c for c in observation.controls if c.target == step.target), None
                        )
                        if (
                            control is None
                            or control.disabled
                            or (
                                isinstance(step, FillStep)
                                and (control.readonly or control.input_type == "password")
                            )
                        ):
                            return result(
                                DiscoveryStatus.INTERVENTION_REQUIRED, "control_not_actionable"
                            )
                    if (
                        self._authorizer is None
                        or (await self._authorizer.authorize(step, observation)) is not True
                    ):
                        return result(
                            DiscoveryStatus.INTERVENTION_REQUIRED, "action_not_authorized"
                        )
                    fresh = await self._collector.observe()
                    if fresh != observation:
                        return result(
                            DiscoveryStatus.INTERVENTION_REQUIRED,
                            "state_changed_during_authorization",
                        )
                    if isinstance(step, FillStep):
                        assert value is not None
                        await self._surface.fill(step.target, value, step.timeout_ms)
                    elif isinstance(step, ClickStep):
                        await self._surface.click(step.target, step.timeout_ms)
                    elif isinstance(step, WaitForStep):
                        await self._surface.wait_for(step.target, step.state, step.timeout_ms)
                    elif isinstance(step, ExtractStep):
                        outputs[step.output_name] = await self._surface.extract(
                            step.target,
                            step.source,
                            step.timeout_ms,
                        )
                    completed.append(step)
                    observation = await self._collector.observe()
                if not _url_allowed(str(observation.url), contract.policy):
                    return result(DiscoveryStatus.FAILURE, "target_not_allowed")
                for outcome in contract.outcomes:
                    if await self._surface.checkpoint_is_met(outcome.checkpoint):
                        return result(DiscoveryStatus.BUSINESS_OUTCOME, outcome.code)
                return result(DiscoveryStatus.MAX_STEPS, "decision_limit_reached")
        except TimeoutError:
            return result(DiscoveryStatus.TIMEOUT, "deadline_exceeded")
        except DecisionProviderError:
            return result(DiscoveryStatus.FAILURE, "provider_error")
        except SurfaceError:
            return result(DiscoveryStatus.FAILURE, "surface_error")
