import re
from collections.abc import Mapping
from urllib.parse import urlsplit

from bankops.artifacts.models import (
    CapabilityArtifact,
    ClickStep,
    ExtractStep,
    FillStep,
    ValueType,
    WaitForStep,
)
from bankops.logging.replay import ReplayEventRecorder, ReplayEventType
from bankops.replay.models import ReplayError, ReplayResult, ReplayStatus, ReplayValue
from bankops.surfaces.base import SurfaceAdapter, SurfaceError

_INPUT_REFERENCE = re.compile(r"{{\s*inputs\.([a-z][a-z0-9_]*)\s*}}")


class InvocationError(ValueError):
    """Invocation inputs do not satisfy the artifact contract."""


class ReplayEngine:
    def __init__(
        self,
        surface: SurfaceAdapter,
        recorder: ReplayEventRecorder | None = None,
    ) -> None:
        self._surface = surface
        self._recorder = recorder

    async def replay(
        self,
        artifact: CapabilityArtifact,
        inputs: Mapping[str, ReplayValue],
    ) -> ReplayResult:
        self._record(
            ReplayEventType.RUN_STARTED,
            artifact,
            input_names=tuple(sorted(inputs)),
        )
        try:
            validated_inputs = _validate_inputs(artifact, inputs)
            _require_allowlisted_entrypoint(artifact)
        except InvocationError as error:
            result = self._failure(artifact, "invalid_invocation", str(error))
            self._record(
                ReplayEventType.RUN_FAILED,
                artifact,
                error_code="invalid_invocation",
            )
            return result

        outputs: dict[str, ReplayValue] = {}
        completed_steps: list[str] = []
        current_step_id: str | None = None

        try:
            await self._surface.navigate(artifact.compatibility.entrypoint)
            for step in artifact.steps:
                current_step_id = step.id
                self._record(
                    ReplayEventType.STEP_STARTED,
                    artifact,
                    step_id=step.id,
                    action_kind=step.kind,
                )
                if isinstance(step, FillStep):
                    value = _render_template(step.value_template, validated_inputs)
                    await self._surface.fill(step.target, value, step.timeout_ms)
                elif isinstance(step, ClickStep):
                    await self._surface.click(step.target, step.timeout_ms)
                elif isinstance(step, WaitForStep):
                    await self._surface.wait_for(step.target, step.state, step.timeout_ms)
                elif isinstance(step, ExtractStep):
                    outputs[step.output_name] = await self._surface.extract(
                        step.target, step.source, step.timeout_ms
                    )

                completed_steps.append(step.id)
                self._record(
                    ReplayEventType.STEP_COMPLETED,
                    artifact,
                    step_id=step.id,
                    action_kind=step.kind,
                    output_names=(step.output_name,) if isinstance(step, ExtractStep) else (),
                )
                outcome_code = await self._matching_outcome(artifact)
                if outcome_code is not None:
                    result = ReplayResult(
                        status=ReplayStatus.BUSINESS_OUTCOME,
                        capability_id=artifact.capability_id,
                        capability_version=artifact.capability_version,
                        outcome_code=outcome_code,
                        completed_step_ids=tuple(completed_steps),
                    )
                    self._record(
                        ReplayEventType.BUSINESS_OUTCOME,
                        artifact,
                        outcome_code=outcome_code,
                    )
                    return result

            if not await self._surface.wait_for_checkpoint(artifact.success_checkpoint):
                result = self._failure(
                    artifact,
                    "checkpoint_not_met",
                    "The final success checkpoint was not observed",
                    completed_steps=completed_steps,
                    expected="success checkpoint",
                    observed="checkpoint absent",
                )
                self._record(
                    ReplayEventType.RUN_FAILED,
                    artifact,
                    error_code="checkpoint_not_met",
                )
                return result

            result = ReplayResult(
                status=ReplayStatus.SUCCESS,
                capability_id=artifact.capability_id,
                capability_version=artifact.capability_version,
                outputs=outputs,
                completed_step_ids=tuple(completed_steps),
            )
            self._record(
                ReplayEventType.RUN_COMPLETED,
                artifact,
                output_names=tuple(sorted(outputs)),
            )
            return result
        except SurfaceError as error:
            result = self._failure(
                artifact,
                "surface_error",
                str(error),
                completed_steps=completed_steps,
                step_id=current_step_id,
            )
            self._record(
                ReplayEventType.RUN_FAILED,
                artifact,
                step_id=current_step_id,
                error_code="surface_error",
            )
            return result

    async def _matching_outcome(self, artifact: CapabilityArtifact) -> str | None:
        for outcome in artifact.outcomes:
            if await self._surface.checkpoint_is_met(outcome.checkpoint):
                return outcome.code
        return None

    def _record(
        self,
        event_type: ReplayEventType,
        artifact: CapabilityArtifact,
        *,
        step_id: str | None = None,
        action_kind: str | None = None,
        input_names: tuple[str, ...] = (),
        output_names: tuple[str, ...] = (),
        outcome_code: str | None = None,
        error_code: str | None = None,
    ) -> None:
        if self._recorder is not None:
            self._recorder.record(
                event_type,
                capability_id=artifact.capability_id,
                capability_version=artifact.capability_version,
                step_id=step_id,
                action_kind=action_kind,
                input_names=input_names,
                output_names=output_names,
                outcome_code=outcome_code,
                error_code=error_code,
            )

    @staticmethod
    def _failure(
        artifact: CapabilityArtifact,
        code: str,
        message: str,
        *,
        completed_steps: list[str] | None = None,
        step_id: str | None = None,
        expected: str | None = None,
        observed: str | None = None,
    ) -> ReplayResult:
        return ReplayResult(
            status=ReplayStatus.FAILURE,
            capability_id=artifact.capability_id,
            capability_version=artifact.capability_version,
            completed_step_ids=tuple(completed_steps or ()),
            error=ReplayError(
                code=code,
                message=message,
                step_id=step_id,
                expected=expected,
                observed=observed,
            ),
        )


def _validate_inputs(
    artifact: CapabilityArtifact,
    inputs: Mapping[str, ReplayValue],
) -> dict[str, ReplayValue]:
    declarations = {parameter.name: parameter for parameter in artifact.inputs}
    unknown = set(inputs) - set(declarations)
    if unknown:
        raise InvocationError(f"Unknown inputs: {', '.join(sorted(unknown))}")

    missing = {
        name
        for name, declaration in declarations.items()
        if declaration.required and name not in inputs
    }
    if missing:
        raise InvocationError(f"Missing required inputs: {', '.join(sorted(missing))}")

    for name, value in inputs.items():
        expected = declarations[name].value_type
        if not _matches_type(value, expected):
            raise InvocationError(f"Input '{name}' must have type '{expected.value}'")
    return dict(inputs)


def _matches_type(value: ReplayValue, expected: ValueType) -> bool:
    if expected is ValueType.STRING:
        return isinstance(value, str)
    if expected is ValueType.BOOLEAN:
        return isinstance(value, bool)
    if expected is ValueType.INTEGER:
        return isinstance(value, int) and not isinstance(value, bool)
    if expected is ValueType.NUMBER:
        return isinstance(value, int | float) and not isinstance(value, bool)
    return False


def _render_template(template: str, inputs: Mapping[str, ReplayValue]) -> str:
    return _INPUT_REFERENCE.sub(lambda match: str(inputs[match.group(1)]), template)


def _require_allowlisted_entrypoint(artifact: CapabilityArtifact) -> None:
    entrypoint = urlsplit(artifact.compatibility.entrypoint)
    for allowed_prefix in artifact.policy.allowed_url_prefixes:
        allowed = urlsplit(allowed_prefix)
        same_origin = entrypoint.scheme == allowed.scheme and entrypoint.netloc == allowed.netloc
        path_allowed = entrypoint.path.startswith(allowed.path)
        if same_origin and path_allowed:
            return
    raise InvocationError("Artifact entrypoint is outside its URL allowlist")
