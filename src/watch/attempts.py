from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field

from watch.models import (
    ObservationSet,
    OccurrenceStatus,
    RunStatus,
    ScheduleOccurrence,
    Target,
    WorkflowRun,
)
from watch.occurrences import (
    OccurrenceExecutionBlockedError,
    OccurrenceNotFoundError,
    OccurrenceScheduleNotFoundError,
    OccurrenceTargetNotFoundError,
)
from watch.storage import JsonStore
from watch.workflow import execute_supplied_observations

MAX_ATTEMPTS = 3


class AttemptStatus(StrEnum):
    EXECUTING = "executing"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class ExecutionAttempt(BaseModel):
    attempt_id: str = Field(pattern=r"^att-[a-f0-9]{24}$")
    execution_key: str = Field(pattern=r"^occ-[a-f0-9]{24}$")
    attempt_number: int = Field(ge=1, le=MAX_ATTEMPTS)
    reason: str = Field(min_length=1, max_length=1000)
    status: AttemptStatus
    started_at: datetime
    finished_at: datetime | None = None
    run_id: str | None = None
    error: str | None = Field(default=None, max_length=2000)


class Collector(Protocol):
    def collect(self, target: Target) -> ObservationSet: ...


class AttemptLimitReachedError(RuntimeError):
    pass


class AttemptNotFoundError(LookupError):
    pass


def attempt_id(execution_key: str, attempt_number: int) -> str:
    material = f"{execution_key}|{attempt_number}".encode()
    return f"att-{sha256(material).hexdigest()[:24]}"


class AttemptStore:
    def __init__(self, workspace: Path) -> None:
        self.attempts_dir = workspace / "attempts"
        self.locks_dir = workspace / "attempt-locks"
        self.attempts_dir.mkdir(parents=True, exist_ok=True)
        self.locks_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, attempt: ExecutionAttempt) -> Path:
        return self.attempts_dir / f"{attempt.attempt_id}.json"

    def create(self, attempt: ExecutionAttempt) -> Path:
        path = self._path(attempt)
        with path.open("x", encoding="utf-8") as file:
            file.write(attempt.model_dump_json(indent=2))
        return path

    def update(self, attempt: ExecutionAttempt) -> Path:
        path = self._path(attempt)
        if not path.is_file():
            raise AttemptNotFoundError(attempt.attempt_id)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(attempt.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(path)
        return path

    def lock(self, attempt: ExecutionAttempt) -> Path:
        path = self.locks_dir / f"{attempt.attempt_id}.lock"
        with path.open("x", encoding="utf-8") as file:
            file.write(attempt.attempt_id)
        return path

    def list(self, execution_key: str | None = None) -> list[ExecutionAttempt]:
        attempts = [
            ExecutionAttempt.model_validate_json(path.read_text(encoding="utf-8"))
            for path in self.attempts_dir.glob("*.json")
        ]
        if execution_key is not None:
            attempts = [
                item for item in attempts if item.execution_key == execution_key
            ]
        return sorted(
            attempts,
            key=lambda item: (item.execution_key, item.attempt_number),
        )

    def get(self, attempt_id_value: str) -> ExecutionAttempt | None:
        path = self.attempts_dir / f"{attempt_id_value}.json"
        if not path.is_file():
            return None
        content = path.read_text(encoding="utf-8")
        return ExecutionAttempt.model_validate_json(content)


class BoundedRetryService:
    def __init__(
        self,
        store: JsonStore,
        workspace: Path,
        collector: Collector,
    ) -> None:
        self._store = store
        self._workspace = workspace
        self._collector = collector
        self._attempts = AttemptStore(workspace)

    def list_attempts(
        self,
        execution_key: str | None = None,
    ) -> list[ExecutionAttempt]:
        return self._attempts.list(execution_key)

    def retry(
        self,
        execution_key_value: str,
        reason: str,
    ) -> tuple[ScheduleOccurrence, ExecutionAttempt, WorkflowRun | None, str]:
        occurrence = self._store.get_occurrence(execution_key_value)
        if occurrence is None:
            raise OccurrenceNotFoundError(execution_key_value)
        if occurrence.status != OccurrenceStatus.FAILED:
            raise OccurrenceExecutionBlockedError(
                "only failed occurrences are eligible for retry"
            )

        schedule = self._store.get_schedule(occurrence.schedule_id)
        if schedule is None:
            raise OccurrenceScheduleNotFoundError(occurrence.schedule_id)
        if not schedule.enabled:
            raise OccurrenceExecutionBlockedError("schedule is disabled")
        target = self._store.get_target(occurrence.target_id)
        if target is None:
            raise OccurrenceTargetNotFoundError(occurrence.target_id)
        if not target.enabled:
            raise OccurrenceExecutionBlockedError("target is disabled")

        existing = self._attempts.list(occurrence.execution_key)
        next_number = len(existing) + 1
        if next_number > MAX_ATTEMPTS:
            raise AttemptLimitReachedError(
                f"attempt limit reached: maximum {MAX_ATTEMPTS}"
            )

        attempt = ExecutionAttempt(
            attempt_id=attempt_id(occurrence.execution_key, next_number),
            execution_key=occurrence.execution_key,
            attempt_number=next_number,
            reason=reason.strip(),
            status=AttemptStatus.EXECUTING,
            started_at=datetime.now(UTC),
        )
        try:
            self._attempts.create(attempt)
            self._attempts.lock(attempt)
        except FileExistsError:
            current = self._attempts.get(attempt.attempt_id)
            if current is None:
                raise
            run = self._store.get_run(current.run_id) if current.run_id else None
            result = (
                "already-executing"
                if current.status == AttemptStatus.EXECUTING
                else "already-finished"
            )
            return occurrence, current, run, result

        try:
            observations = self._collector.collect(target)
            run, _, _ = execute_supplied_observations(
                target=target,
                observations=observations,
                workspace=self._workspace,
            )
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"[:2000]
            failed_attempt = attempt.model_copy(
                update={
                    "status": AttemptStatus.FAILED,
                    "finished_at": datetime.now(UTC),
                    "error": error,
                }
            )
            self._attempts.update(failed_attempt)
            return occurrence, failed_attempt, None, "failed"

        final_status = (
            AttemptStatus.PARTIAL
            if run.status == RunStatus.PARTIAL
            else AttemptStatus.COMPLETED
        )
        finished_attempt = attempt.model_copy(
            update={
                "status": final_status,
                "finished_at": datetime.now(UTC),
                "run_id": run.run_id,
            }
        )
        self._attempts.update(finished_attempt)
        return occurrence, finished_attempt, run, final_status.value
