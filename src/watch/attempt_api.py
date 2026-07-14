from __future__ import annotations

from pathlib import Path
from typing import Protocol

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from watch.attempts import (
    AttemptLimitReachedError,
    BoundedRetryService,
    ExecutionAttempt,
)
from watch.models import ObservationSet, ScheduleOccurrence, Target, WorkflowRun
from watch.occurrences import (
    OccurrenceExecutionBlockedError,
    OccurrenceNotFoundError,
    OccurrenceScheduleNotFoundError,
    OccurrenceTargetNotFoundError,
)
from watch.storage import JsonStore


class Collector(Protocol):
    def collect(self, target: Target) -> ObservationSet: ...


class RetryResponse(BaseModel):
    occurrence: ScheduleOccurrence
    attempt: ExecutionAttempt
    run: WorkflowRun | None
    result: str


def mount_attempt_routes(
    app: FastAPI,
    workspace: Path,
    collector: Collector,
) -> None:
    service = BoundedRetryService(JsonStore(workspace), workspace, collector)

    @app.get("/api/attempts", response_model=list[ExecutionAttempt])
    def list_attempts() -> list[ExecutionAttempt]:
        return service.list_attempts()

    @app.get(
        "/api/occurrences/{execution_key}/attempts",
        response_model=list[ExecutionAttempt],
    )
    def list_occurrence_attempts(execution_key: str) -> list[ExecutionAttempt]:
        occurrence = JsonStore(workspace).get_occurrence(execution_key)
        if occurrence is None:
            raise HTTPException(status_code=404, detail="occurrence not found")
        return service.list_attempts(execution_key)

    @app.post(
        "/api/occurrences/{execution_key}/retry",
        response_model=RetryResponse,
    )
    def retry_occurrence(execution_key: str) -> RetryResponse:
        try:
            occurrence, attempt, run, result = service.retry(execution_key)
        except OccurrenceNotFoundError as exc:
            raise HTTPException(status_code=404, detail="occurrence not found") from exc
        except OccurrenceScheduleNotFoundError as exc:
            raise HTTPException(status_code=404, detail="schedule not found") from exc
        except OccurrenceTargetNotFoundError as exc:
            raise HTTPException(status_code=404, detail="target not found") from exc
        except (OccurrenceExecutionBlockedError, AttemptLimitReachedError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return RetryResponse(
            occurrence=occurrence,
            attempt=attempt,
            run=run,
            result=result,
        )
