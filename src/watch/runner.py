from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

from watch.models import OccurrenceStatus
from watch.occurrences import (
    execution_key,
    latest_due_occurrence,
    normalize_evaluation_time,
)
from watch.storage import JsonStore


class DuePlanStatus(StrEnum):
    READY_TO_CLAIM = "ready-to-claim"
    ALREADY_CLAIMED = "already-claimed"
    SCHEDULE_DISABLED = "schedule-disabled"
    TARGET_MISSING = "target-missing"
    TARGET_DISABLED = "target-disabled"
    BEFORE_START = "before-start"


class DuePlanItem(BaseModel):
    schedule_id: str
    target_id: str
    status: DuePlanStatus
    evaluated_at: datetime
    occurrence_at: datetime | None = None
    execution_key: str | None = None
    existing_occurrence_status: OccurrenceStatus | None = None
    reason: str


class DueWorkPlanner:
    def __init__(self, store: JsonStore) -> None:
        self._store = store

    def plan(self, evaluated_at: datetime) -> list[DuePlanItem]:
        evaluated_utc = normalize_evaluation_time(evaluated_at)
        items: list[DuePlanItem] = []

        for schedule in self._store.list_schedules():
            if not schedule.enabled:
                items.append(
                    DuePlanItem(
                        schedule_id=schedule.schedule_id,
                        target_id=schedule.target_id,
                        status=DuePlanStatus.SCHEDULE_DISABLED,
                        evaluated_at=evaluated_utc,
                        reason="Schedule is disabled.",
                    )
                )
                continue

            target = self._store.get_target(schedule.target_id)
            if target is None:
                items.append(
                    DuePlanItem(
                        schedule_id=schedule.schedule_id,
                        target_id=schedule.target_id,
                        status=DuePlanStatus.TARGET_MISSING,
                        evaluated_at=evaluated_utc,
                        reason="Linked target does not exist.",
                    )
                )
                continue
            if not target.enabled:
                items.append(
                    DuePlanItem(
                        schedule_id=schedule.schedule_id,
                        target_id=schedule.target_id,
                        status=DuePlanStatus.TARGET_DISABLED,
                        evaluated_at=evaluated_utc,
                        reason="Linked target is disabled.",
                    )
                )
                continue

            occurrence_at = latest_due_occurrence(schedule, evaluated_utc)
            if occurrence_at is None:
                items.append(
                    DuePlanItem(
                        schedule_id=schedule.schedule_id,
                        target_id=schedule.target_id,
                        status=DuePlanStatus.BEFORE_START,
                        evaluated_at=evaluated_utc,
                        reason="Evaluation time is before the schedule start.",
                    )
                )
                continue

            key = execution_key(schedule.schedule_id, occurrence_at)
            existing = self._store.get_occurrence(key)
            if existing is not None:
                items.append(
                    DuePlanItem(
                        schedule_id=schedule.schedule_id,
                        target_id=schedule.target_id,
                        status=DuePlanStatus.ALREADY_CLAIMED,
                        evaluated_at=evaluated_utc,
                        occurrence_at=occurrence_at,
                        execution_key=key,
                        existing_occurrence_status=existing.status,
                        reason="The latest due boundary already has an occurrence record.",
                    )
                )
                continue

            items.append(
                DuePlanItem(
                    schedule_id=schedule.schedule_id,
                    target_id=schedule.target_id,
                    status=DuePlanStatus.READY_TO_CLAIM,
                    evaluated_at=evaluated_utc,
                    occurrence_at=occurrence_at,
                    execution_key=key,
                    reason="The latest due boundary is eligible for an explicit claim.",
                )
            )

        return items
