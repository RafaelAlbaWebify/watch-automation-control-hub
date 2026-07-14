from __future__ import annotations

from watch.models import IntervalSchedule, IntervalScheduleUpdate
from watch.storage import JsonStore


class ScheduleNotFoundError(LookupError):
    pass


class ScheduleAlreadyExistsError(ValueError):
    pass


class ScheduleTargetNotFoundError(LookupError):
    pass


class ScheduleService:
    def __init__(self, store: JsonStore) -> None:
        self._store = store

    def create(self, schedule: IntervalSchedule) -> IntervalSchedule:
        if self._store.get_target(schedule.target_id) is None:
            raise ScheduleTargetNotFoundError(schedule.target_id)
        try:
            self._store.create_schedule(schedule)
        except FileExistsError as exc:
            raise ScheduleAlreadyExistsError(schedule.schedule_id) from exc
        return schedule

    def get(self, schedule_id: str) -> IntervalSchedule:
        schedule = self._store.get_schedule(schedule_id)
        if schedule is None:
            raise ScheduleNotFoundError(schedule_id)
        return schedule

    def list(self) -> list[IntervalSchedule]:
        return self._store.list_schedules()

    def update(
        self,
        schedule_id: str,
        request: IntervalScheduleUpdate,
    ) -> IntervalSchedule:
        existing = self.get(schedule_id)
        if self._store.get_target(existing.target_id) is None:
            raise ScheduleTargetNotFoundError(existing.target_id)
        schedule = request.apply_to(schedule_id, existing.target_id)
        try:
            self._store.update_schedule(schedule)
        except FileNotFoundError as exc:
            raise ScheduleNotFoundError(schedule_id) from exc
        return schedule
