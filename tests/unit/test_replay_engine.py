import json
from pathlib import Path

import pytest

from bankops.artifacts.models import CapabilityArtifact, Checkpoint, LocatorPlan
from bankops.logging.replay import ReplayEvent, ReplayEventRecorder, ReplayEventType
from bankops.replay.engine import ReplayEngine
from bankops.replay.models import ReplayStatus
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
    ) -> None:
        self.outcome = outcome
        self.fail_on = fail_on
        self.final_checkpoint = final_checkpoint
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
        self.operations.append(("wait_for", state))

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
