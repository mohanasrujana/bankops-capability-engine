import json
from pathlib import Path

import pytest

from bankops.artifacts.models import CapabilityArtifact, Checkpoint, LocatorPlan
from bankops.logging.replay import ReplayEvent, ReplayEventRecorder, ReplayEventType
from bankops.replay.engine import ReplayEngine
from bankops.replay.models import ReplayStatus
from bankops.safety.approval import ApprovalRequest
from bankops.surfaces.base import SurfaceError

_ARTIFACT_PATH = (
    Path(__file__).parents[2]
    / "evidence"
    / "artifacts"
    / "ledgerdesk-member-savings-balance.v1.json"
)


class FakeSurface:
    def __init__(
        self,
        *,
        outcome: str | None = None,
        fail_on: str | None = None,
        final_checkpoint: bool = True,
        fail_wait_attempts: int = 0,
    ) -> None:
        self.outcome = outcome
        self.fail_on = fail_on
        self.final_checkpoint = final_checkpoint
        self.fail_wait_attempts = fail_wait_attempts
        self.wait_calls = 0
        self.operations: list[tuple[str, str]] = []

    async def navigate(self, url: str) -> None:
        self.operations.append(("navigate", url))

    async def fill(self, target: LocatorPlan, value: str, timeout_ms: int) -> None:
        self.operations.append(("fill", value))

    async def click(self, target: LocatorPlan, timeout_ms: int) -> None:
        self.operations.append(("click", ""))
        if self.fail_on == "click":
            raise SurfaceError("button was not actionable")

    async def wait_for(self, target: LocatorPlan, state: str, timeout_ms: int) -> None:
        self.wait_calls += 1
        self.operations.append(("wait_for", state))
        if self.wait_calls <= self.fail_wait_attempts:
            raise SurfaceError("target was temporarily unavailable")

    async def extract(self, target: LocatorPlan, source: str, timeout_ms: int) -> str:
        self.operations.append(("extract", source))
        return "$4,250.75"

    async def checkpoint_is_met(self, checkpoint: Checkpoint) -> bool:
        if self.outcome is None:
            return False
        candidate = checkpoint.target.candidates[0]
        return getattr(candidate, "name", None) == self.outcome

    async def wait_for_checkpoint(self, checkpoint: Checkpoint) -> bool:
        return self.final_checkpoint


class MemorySink:
    def __init__(self) -> None:
        self.events: list[ReplayEvent] = []

    def emit(self, event: ReplayEvent) -> None:
        self.events.append(event)


class AllowApprovalProvider:
    def __init__(self, approved: bool) -> None:
        self.approved = approved
        self.requests: list[ApprovalRequest] = []

    async def approve(self, request: ApprovalRequest) -> bool:
        self.requests.append(request)
        return self.approved


def load_artifact() -> CapabilityArtifact:
    return CapabilityArtifact.model_validate_json(_ARTIFACT_PATH.read_text())


@pytest.mark.anyio
async def test_replay_executes_steps_in_order_without_model_decisions() -> None:
    surface = FakeSurface()
    result = await ReplayEngine(surface).replay(load_artifact(), {"member_id": "M-10001"})

    assert result.status is ReplayStatus.SUCCESS
    assert result.outputs == {"savings_balance": "$4,250.75"}
    assert result.completed_step_ids == (
        "enter-member-id",
        "submit-member-search",
        "wait-for-open-member",
        "open-member",
        "wait-for-savings-balance",
        "extract-savings-balance",
    )
    assert surface.operations == [
        ("navigate", "http://127.0.0.1:8000/"),
        ("fill", "M-10001"),
        ("click", ""),
        ("wait_for", "visible"),
        ("click", ""),
        ("wait_for", "visible"),
        ("extract", "text"),
    ]


@pytest.mark.anyio
async def test_replay_returns_business_outcome_before_later_steps() -> None:
    surface = FakeSurface(outcome="Member Not Found")
    result = await ReplayEngine(surface).replay(load_artifact(), {"member_id": "M-99999"})

    assert result.status is ReplayStatus.BUSINESS_OUTCOME
    assert result.outcome_code == "member_not_found"
    assert result.outputs == {}


@pytest.mark.anyio
async def test_replay_rejects_missing_required_input_before_navigation() -> None:
    surface = FakeSurface()
    result = await ReplayEngine(surface).replay(load_artifact(), {})

    assert result.status is ReplayStatus.FAILURE
    assert result.error is not None
    assert result.error.code == "invalid_invocation"
    assert surface.operations == []


@pytest.mark.anyio
async def test_replay_rejects_entrypoint_outside_allowlist() -> None:
    data = json.loads(_ARTIFACT_PATH.read_text())
    data["compatibility"]["entrypoint"] = "http://127.0.0.1:8000.evil.test/"
    artifact = CapabilityArtifact.model_validate(data)
    surface = FakeSurface()

    result = await ReplayEngine(surface).replay(artifact, {"member_id": "M-10001"})

    assert result.status is ReplayStatus.FAILURE
    assert result.error is not None
    assert result.error.code == "invalid_invocation"
    assert surface.operations == []


@pytest.mark.anyio
async def test_replay_reports_failed_step_and_observation() -> None:
    result = await ReplayEngine(FakeSurface(fail_on="click")).replay(
        load_artifact(), {"member_id": "M-10001"}
    )

    assert result.status is ReplayStatus.FAILURE
    assert result.error is not None
    assert result.error.code == "surface_error"
    assert result.error.step_id == "submit-member-search"
    assert result.error.message == "button was not actionable"
    assert result.completed_step_ids == ("enter-member-id",)


@pytest.mark.anyio
async def test_replay_requires_final_success_checkpoint() -> None:
    result = await ReplayEngine(FakeSurface(final_checkpoint=False)).replay(
        load_artifact(), {"member_id": "M-10001"}
    )

    assert result.status is ReplayStatus.FAILURE
    assert result.error is not None
    assert result.error.code == "checkpoint_not_met"
    assert result.error.expected == "success checkpoint"
    assert result.error.observed == "checkpoint absent"


@pytest.mark.anyio
async def test_replay_emits_ordered_value_free_events() -> None:
    sink = MemorySink()
    recorder = ReplayEventRecorder(sink, run_id="run-1")

    result = await ReplayEngine(FakeSurface(), recorder=recorder).replay(
        load_artifact(), {"member_id": "M-10001"}
    )

    assert result.status is ReplayStatus.SUCCESS
    assert sink.events[0].event_type is ReplayEventType.RUN_STARTED
    assert sink.events[-1].event_type is ReplayEventType.RUN_COMPLETED
    assert [event.sequence for event in sink.events] == list(range(1, len(sink.events) + 1))
    serialized = "\n".join(event.model_dump_json() for event in sink.events)
    assert "M-10001" not in serialized
    assert "$4,250.75" not in serialized


@pytest.mark.anyio
async def test_replay_retries_only_when_artifact_records_bounded_recovery() -> None:
    data = json.loads(_ARTIFACT_PATH.read_text())
    data["steps"][2]["retry"] = {"max_attempts": 2, "delay_ms": 0}
    artifact = CapabilityArtifact.model_validate(data)
    surface = FakeSurface(fail_wait_attempts=1)
    sink = MemorySink()

    result = await ReplayEngine(surface, recorder=ReplayEventRecorder(sink, run_id="run-1")).replay(
        artifact, {"member_id": "M-10001"}
    )

    assert result.status is ReplayStatus.SUCCESS
    assert surface.wait_calls == 3
    retry_events = [
        event for event in sink.events if event.event_type is ReplayEventType.STEP_RETRY
    ]
    assert len(retry_events) == 1
    assert retry_events[0].step_id == "wait-for-open-member"
    assert retry_events[0].attempt == 2


@pytest.mark.anyio
async def test_risky_step_stops_before_execution_without_approval() -> None:
    data = json.loads(_ARTIFACT_PATH.read_text())
    data["steps"][0]["risk"] = "risky"
    artifact = CapabilityArtifact.model_validate(data)
    surface = FakeSurface()

    result = await ReplayEngine(surface).replay(artifact, {"member_id": "M-10001"})

    assert result.status is ReplayStatus.INTERVENTION_REQUIRED
    assert result.intervention is not None
    assert result.intervention.step_id == "enter-member-id"
    assert surface.operations == [("navigate", "http://127.0.0.1:8000/")]


@pytest.mark.anyio
async def test_risky_step_executes_after_explicit_approval() -> None:
    data = json.loads(_ARTIFACT_PATH.read_text())
    data["steps"][0]["risk"] = "risky"
    artifact = CapabilityArtifact.model_validate(data)
    approval = AllowApprovalProvider(approved=True)

    result = await ReplayEngine(FakeSurface(), approval_provider=approval).replay(
        artifact, {"member_id": "M-10001"}
    )

    assert result.status is ReplayStatus.SUCCESS
    assert len(approval.requests) == 1
    assert approval.requests[0].step_id == "enter-member-id"
