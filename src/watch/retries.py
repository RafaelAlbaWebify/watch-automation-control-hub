from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Protocol

from watch.models import (
    ObservationSet,
    OccurrenceStatus,
    RetryAttempt,
    RetryAttemptStatus,
    RunStatus,
    Target,
    WorkflowRun,
)
from watch.storage import JsonStore
from watch.workflow import execute_supplied_observations


class Collector(Protocol):
    def collect(self, target: Target) -> ObservationSet: ...


class RetryAttemptNotFoundError(LookupError):
    pass


class RetryOccurrenceNotFoundError(LookupError):
    pass


class RetryScheduleNotFoundError(LookupError):
    pass


class RetryTargetNotFoundError(LookupError):
    pass


class RetryNotAllowedError(RuntimeError):
    pass


class RetryLimitReachedError(RuntimeError):
    pass


def retry_attempt_id(execution_key: str, attempt_number: int) -> str:
    material = f"{execution_key}|{attempt_number}".encode()
    return f"retry-{sha256(material).hexdigest()[:24]}"


class RetryAttemptService:
    MAX_ATTEMPTS = 3

    def __init__(
        self,
        store: JsonStore,
        workspace: Path,
        collector: Collector,
    ) -> None:
        self._store = store
        self._workspace = workspace
        self._collector = collector

    def list(self) -> list[RetryAttempt]:
        return self._store.list_retry_attempts()

    def get(self, attempt_id: str) -> RetryAttempt:
        attempt = self._store.get_retry_attempt(attempt_id)
        if attempt is None:
            raise RetryAttemptNotFoundError(attempt_id)
        return attempt

    def retry(
        self,
        execution_key: str,
        reason: str,
    ) -> tuple[RetryAttempt, WorkflowRun | None, str]:
        occurrence = self._store.get_occurrence(execution_key)
        if occurrence is None:
            raise RetryOccurrenceNotFoundError(execution_key)
        if occurrence.status != OccurrenceStatus.FAILED:
            raise RetryNotAllowedError("only failed occurrences can be retried")

        schedule = self._store.get_schedule(occurrence.schedule_id)
        if schedule is None:
            raise RetryScheduleNotFoundError(occurrence.schedule_id)
        if not schedule.enabled:
            raise RetryNotAllowedError("schedule is disabled")
        target = self._store.get_target(occurrence.target_id)
        if target is None:
            raise RetryTargetNotFoundError(occurrence.target_id)
        if not target.enabled:
            raise RetryNotAllowedError("target is disabled")

        existing_attempts = self._store.list_retry_attempts(execution_key)
        if len(existing_attempts) >= self.MAX_ATTEMPTS:
            raise RetryLimitReachedError("retry attempt limit reached")
        attempt_number = len(existing_attempts) + 1
        attempt_id = retry_attempt_id(execution_key, attempt_number)
        attempt = RetryAttempt(
            attempt_id=attempt_id,
            execution_key=execution_key,
            attempt_number=attempt_number,
            reason=reason.strip(),
            requested_at=datetime.now(UTC),
        )
        try:
            self._store.create_retry_attempt(attempt)
        except FileExistsError:
            existing = self._store.get_retry_attempt(attempt_id)
            if existing is None:
                raise
            run = self._store.get_run(existing.run_id) if existing.run_id else None
            result = (
                "already-finished"
                if existing.status != RetryAttemptStatus.EXECUTING
                else "already-executing"
            )
            return existing, run, result

        try:
            observations = self._collector.collect(target)
            run, _, _ = execute_supplied_observations(
                target=target,
                observations=observations,
                workspace=self._workspace,
            )
        except Exception as exc:
            failed = attempt.model_copy(
                update={
                    "status": RetryAttemptStatus.FAILED,
                    "finished_at": datetime.now(UTC),
                    "error": f"{type(exc).__name__}: {exc}"[:2000],
                }
            )
            self._store.update_retry_attempt(failed)
            return failed, None, "failed"

        status = (
            RetryAttemptStatus.PARTIAL
            if run.status == RunStatus.PARTIAL
            else RetryAttemptStatus.COMPLETED
        )
        finished = attempt.model_copy(
            update={
                "status": status,
                "finished_at": datetime.now(UTC),
                "run_id": run.run_id,
            }
        )
        self._store.update_retry_attempt(finished)
        return finished, run, status.value
