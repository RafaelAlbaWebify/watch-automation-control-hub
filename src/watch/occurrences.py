from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256

from watch.models import IntervalSchedule, ScheduleOccurrence
from watch.storage import JsonStore


class OccurrenceNotFoundError(LookupError):
    pass


class OccurrenceScheduleNotFoundError(LookupError):
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
