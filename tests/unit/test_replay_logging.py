import json
from datetime import UTC, datetime
from pathlib import Path

from bankops.logging.replay import (
    JsonlEventSink,
    ReplayEvent,
    ReplayEventRecorder,
    ReplayEventType,
)


class MemorySink:
    def __init__(self) -> None:
        self.events: list[ReplayEvent] = []

    def emit(self, event: ReplayEvent) -> None:
        self.events.append(event)


def test_recorder_sequences_metadata_without_values() -> None:
    sink = MemorySink()
    recorder = ReplayEventRecorder(
        sink,
        run_id="run-1",
        clock=lambda: datetime(2026, 9, 18, tzinfo=UTC),
    )

    recorder.record(
        ReplayEventType.RUN_STARTED,
        capability_id="lookup-member-savings-balance",
        capability_version=1,
        input_names=("member_id",),
    )
    recorder.record(
        ReplayEventType.STEP_COMPLETED,
        capability_id="lookup-member-savings-balance",
        capability_version=1,
        step_id="extract-savings-balance",
        action_kind="extract",
        output_names=("savings_balance",),
    )

    assert [event.sequence for event in sink.events] == [1, 2]
    serialized = "\n".join(event.model_dump_json() for event in sink.events)
    assert "member_id" in serialized
    assert "savings_balance" in serialized
    assert "M-10001" not in serialized
    assert "$4,250.75" not in serialized


def test_jsonl_sink_writes_one_parseable_event_per_line(tmp_path: Path) -> None:
    path = tmp_path / "replay.jsonl"
    recorder = ReplayEventRecorder(
        JsonlEventSink(path),
        run_id="run-1",
        clock=lambda: datetime(2026, 9, 18, tzinfo=UTC),
    )

    recorder.record(
        ReplayEventType.RUN_COMPLETED,
        capability_id="lookup-member-savings-balance",
        capability_version=1,
        output_names=("savings_balance",),
    )

    lines = path.read_text().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["event_type"] == "run_completed"
