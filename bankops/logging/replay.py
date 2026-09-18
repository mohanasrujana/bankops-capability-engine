import json
from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from pydantic import Field

from bankops.artifacts.models import StrictModel


class ReplayEventType(StrEnum):
    RUN_STARTED = "run_started"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_RETRY = "step_retry"
    INTERVENTION_REQUIRED = "intervention_required"
    BUSINESS_OUTCOME = "business_outcome"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"


class ReplayEvent(StrictModel):
    recorded_at: datetime
    run_id: str = Field(min_length=1)
    sequence: int = Field(ge=1)
    event_type: ReplayEventType
    capability_id: str = Field(min_length=1)
    capability_version: int = Field(ge=1)
    step_id: str | None = None
    action_kind: str | None = None
    input_names: tuple[str, ...] = ()
    output_names: tuple[str, ...] = ()
    outcome_code: str | None = None
    error_code: str | None = None
    attempt: int | None = Field(default=None, ge=1)


class EventSink(Protocol):
    def emit(self, event: ReplayEvent) -> None: ...


class JsonlEventSink:
    def __init__(self, path: Path) -> None:
        self._path = path

    def emit(self, event: ReplayEvent) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event.model_dump(mode="json"), sort_keys=True) + "\n")


class ReplayEventRecorder:
    def __init__(
        self,
        sink: EventSink,
        *,
        run_id: str | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._sink = sink
        self._run_id = run_id or str(uuid4())
        self._clock = clock or (lambda: datetime.now(UTC))
        self._sequence = 0

    def record(
        self,
        event_type: ReplayEventType,
        *,
        capability_id: str,
        capability_version: int,
        step_id: str | None = None,
        action_kind: str | None = None,
        input_names: tuple[str, ...] = (),
        output_names: tuple[str, ...] = (),
        outcome_code: str | None = None,
        error_code: str | None = None,
        attempt: int | None = None,
    ) -> None:
        self._sequence += 1
        self._sink.emit(
            ReplayEvent(
                recorded_at=self._clock(),
                run_id=self._run_id,
                sequence=self._sequence,
                event_type=event_type,
                capability_id=capability_id,
                capability_version=capability_version,
                step_id=step_id,
                action_kind=action_kind,
                input_names=input_names,
                output_names=output_names,
                outcome_code=outcome_code,
                error_code=error_code,
                attempt=attempt,
            )
        )
