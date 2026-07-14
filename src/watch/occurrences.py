from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Protocol

from watch.models import (
    IntervalSchedule,
    ObservationSet,
    OccurrenceAttention,
    OccurrenceAttentionKind,
    OccurrenceStatus,
    RunStatus,
    ScheduleOccurrence,
    Target,
    WorkflowRun,
)
from watch.storage import JsonStore
from watch.workflow import execute_supplied_observations


class Collector(Protocol):
    def collect(self, target: Target) -> ObservationSet: ...


class OccurrenceNotFoundError(LookupError):
    pass


class OccurrenceScheduleNotFoundError(LookupError):
    pass


class OccurrenceTargetNotFoundError(LookupError):
    pass


class OccurrenceExecutionBlockedError(RuntimeError):
    pass


class EvaluationTimeError(ValueError):
    pass


def normalize_evaluation_time(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise EvaluationTimeError("evaluated_at must include a timezone")
    return value.astimezone(UTC)


def latest_due_occurrence(
    schedule: IntervalSchedule,
    evaluated_at: datetime,
) -> datetime | None:
    evaluated_utc = normalize_evaluation_time(evaluated_at)
    if evaluated_utc < schedule.start_at:
        return None
    interval = timedelta(minutes=schedule.interval_minutes)
    elapsed = evaluated_utc - schedule.start_at
    occurrence_number = elapsed // interval
    return schedule.start_at + (occurrence_number * interval)


def execution_key(schedule_id: str, occurrence_at: datetime) -> str:
    normalized = normalize_evaluation_time(occurrence_at)
    material = f"{schedule_id}|{normalized.isoformat()}".encode()
    return f"occ-{sha256(material).hexdigest()[:24]}"


class OccurrenceService:
    def __init__(self, store: JsonStore) -> None:
        self._store = store

    def list(self) -> list[ScheduleOccurrence]:
        return self._store.list_occurrences()

    def get(self, execution_key_value: str) -> ScheduleOccurrence:
        occurrence = self._store.get_occurrence(execution_key_value)
        if occurrence is None:
            raise OccurrenceNotFoundError(execution_key_value)
        return occurrence

    def evaluate(
        self,
        schedule_id: str,
        evaluated_at: datetime,
    ) -> tuple[ScheduleOccurrence | None, str]:
        schedule = self._store.get_schedule(schedule_id)
        if schedule is None:
            raise OccurrenceScheduleNotFoundError(schedule_id)
        if not schedule.enabled:
            return None, "schedule-disabled"
        target = self._store.get_target(schedule.target_id)
        if target is None:
            return None, "target-missing"
        if not target.enabled:
            return None, "target-disabled"

        evaluated_utc = normalize_evaluation_time(evaluated_at)
        occurrence_at = latest_due_occurrence(schedule, evaluated_utc)
        if occurrence_at is None:
            return None, "before-start"

        key = execution_key(schedule.schedule_id, occurrence_at)
        existing = self._store.get_occurrence(key)
        if existing is not None:
            return existing, "already-claimed"

        occurrence = ScheduleOccurrence(
            execution_key=key,
            schedule_id=schedule.schedule_id,
            target_id=schedule.target_id,
            occurrence_at=occurrence_at,
            claimed_at=evaluated_utc,
        )
        try:
            self._store.claim_occurrence(occurrence)
        except FileExistsError:
            existing = self._store.get_occurrence(key)
            if existing is None:
                raise
            return existing, "already-claimed"
        return occurrence, "claimed"


class OccurrenceAttentionService:
    def __init__(self, store: JsonStore) -> None:
        self._store = store

    def inspect(
        self,
        evaluated_at: datetime,
        grace_minutes: int,
        lookback_occurrences: int,
    ) -> list[OccurrenceAttention]:
        evaluated_utc = normalize_evaluation_time(evaluated_at)
        cutoff = evaluated_utc - timedelta(minutes=grace_minutes)
        attention: list[OccurrenceAttention] = []

        for schedule in self._store.list_schedules():
            if not schedule.enabled:
                continue
            latest = latest_due_occurrence(schedule, cutoff)
            if latest is None:
                continue
            interval = timedelta(minutes=schedule.interval_minutes)
            for index in range(lookback_occurrences):
                occurrence_at = latest - (index * interval)
                if occurrence_at < schedule.start_at:
                    break
                key = execution_key(schedule.schedule_id, occurrence_at)
                if self._store.get_occurrence(key) is not None:
                    continue
                age_minutes = int(
                    (evaluated_utc - occurrence_at).total_seconds() // 60
                )
                attention.append(
                    OccurrenceAttention(
                        execution_key=key,
                        schedule_id=schedule.schedule_id,
                        target_id=schedule.target_id,
                        occurrence_at=occurrence_at,
                        kind=OccurrenceAttentionKind.MISSED_UNCLAIMED,
                        detected_at=evaluated_utc,
                        age_minutes=age_minutes,
                        details=(
                            "No occurrence record exists for this due schedule boundary."
                        ),
                    )
                )

        for occurrence in self._store.list_occurrences():
            started_at = occurrence.execution_started_at
            if (
                occurrence.status != OccurrenceStatus.EXECUTING
                or started_at is None
                or started_at > cutoff
            ):
                continue
            age_minutes = int((evaluated_utc - started_at).total_seconds() // 60)
            attention.append(
                OccurrenceAttention(
                    execution_key=occurrence.execution_key,
                    schedule_id=occurrence.schedule_id,
                    target_id=occurrence.target_id,
                    occurrence_at=occurrence.occurrence_at,
                    kind=OccurrenceAttentionKind.EXECUTING_STALE,
                    detected_at=evaluated_utc,
                    age_minutes=age_minutes,
                    details=(
                        "Occurrence remains executing beyond the configured grace period."
                    ),
                )
            )

        return sorted(
            attention,
            key=lambda item: (item.occurrence_at, item.kind.value, item.execution_key),
        )


class OccurrenceExecutionService:
    _TERMINAL = {
        OccurrenceStatus.COMPLETED,
        OccurrenceStatus.PARTIAL,
        OccurrenceStatus.FAILED,
        OccurrenceStatus.MISSED,
    }

    def __init__(
        self,
        store: JsonStore,
        workspace: Path,
        collector: Collector,
    ) -> None:
        self._store = store
        self._workspace = workspace
        self._collector = collector

    def execute(
        self,
        execution_key_value: str,
    ) -> tuple[ScheduleOccurrence, WorkflowRun | None, str]:
        occurrence = self._store.get_occurrence(execution_key_value)
        if occurrence is None:
            raise OccurrenceNotFoundError(execution_key_value)
        if occurrence.status in self._TERMINAL:
            run = self._store.get_run(occurrence.run_id) if occurrence.run_id else None
            return occurrence, run, "already-finished"
        if occurrence.status == OccurrenceStatus.EXECUTING:
            return occurrence, None, "already-executing"

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

        try:
            self._store.begin_occurrence_execution(execution_key_value)
        except FileExistsError:
            current = self._store.get_occurrence(execution_key_value)
            if current is None:
                raise OccurrenceNotFoundError(execution_key_value) from None
            run = self._store.get_run(current.run_id) if current.run_id else None
            result = (
                "already-finished"
                if current.status in self._TERMINAL
                else "already-executing"
            )
            return current, run, result

        started = occurrence.model_copy(
            update={
                "status": OccurrenceStatus.EXECUTING,
                "execution_started_at": datetime.now(UTC),
                "error": None,
            }
        )
        self._store.update_occurrence(started)

        try:
            observations = self._collector.collect(target)
            run, _, _ = execute_supplied_observations(
                target=target,
                observations=observations,
                workspace=self._workspace,
            )
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"[:2000]
            failed = started.model_copy(
                update={
                    "status": OccurrenceStatus.FAILED,
                    "finished_at": datetime.now(UTC),
                    "error": error,
                }
            )
            self._store.update_occurrence(failed)
            return failed, None, "failed"

        status = (
            OccurrenceStatus.PARTIAL
            if run.status == RunStatus.PARTIAL
            else OccurrenceStatus.COMPLETED
        )
        finished = started.model_copy(
            update={
                "status": status,
                "finished_at": datetime.now(UTC),
                "run_id": run.run_id,
            }
        )
        self._store.update_occurrence(finished)
        return finished, run, status.value
