from datetime import UTC, datetime
from pathlib import Path

from watch.models import IntervalSchedule, ScheduleOccurrence, Target
from watch.occurrences import execution_key
from watch.runner import DuePlanStatus, DueWorkPlanner
from watch.storage import JsonStore


def _snapshot(workspace: Path) -> list[tuple[str, bytes]]:
    return sorted(
        (path.relative_to(workspace).as_posix(), path.read_bytes())
        for path in workspace.rglob("*")
        if path.is_file()
    )


def test_due_work_planner_classifies_schedules_without_writes(tmp_path: Path) -> None:
    store = JsonStore(tmp_path)
    store.create_target(
        Target(
            target_id="ready-target",
            name="Ready",
            url="https://example.com",
        )
    )
    store.create_target(
        Target(
            target_id="disabled-target",
            name="Disabled",
            url="https://example.org",
            enabled=False,
        )
    )
    schedules = [
        IntervalSchedule(
            schedule_id="a-ready",
            target_id="ready-target",
            start_at=datetime(2026, 7, 14, 7, 0, tzinfo=UTC),
            interval_minutes=60,
        ),
        IntervalSchedule(
            schedule_id="b-claimed",
            target_id="ready-target",
            start_at=datetime(2026, 7, 14, 7, 0, tzinfo=UTC),
            interval_minutes=60,
        ),
        IntervalSchedule(
            schedule_id="c-disabled-schedule",
            target_id="ready-target",
            enabled=False,
            start_at=datetime(2026, 7, 14, 7, 0, tzinfo=UTC),
            interval_minutes=60,
        ),
        IntervalSchedule(
            schedule_id="d-missing-target",
            target_id="missing-target",
            start_at=datetime(2026, 7, 14, 7, 0, tzinfo=UTC),
            interval_minutes=60,
        ),
        IntervalSchedule(
            schedule_id="e-disabled-target",
            target_id="disabled-target",
            start_at=datetime(2026, 7, 14, 7, 0, tzinfo=UTC),
            interval_minutes=60,
        ),
        IntervalSchedule(
            schedule_id="f-before-start",
            target_id="ready-target",
            start_at=datetime(2026, 7, 15, 7, 0, tzinfo=UTC),
            interval_minutes=60,
        ),
    ]
    for schedule in schedules:
        store.create_schedule(schedule)

    latest_boundary = datetime(2026, 7, 14, 11, 0, tzinfo=UTC)
    claimed_key = execution_key("b-claimed", latest_boundary)
    store.claim_occurrence(
        ScheduleOccurrence(
            execution_key=claimed_key,
            schedule_id="b-claimed",
            target_id="ready-target",
            occurrence_at=latest_boundary,
            claimed_at=datetime(2026, 7, 14, 11, 1, tzinfo=UTC),
        )
    )
    before = _snapshot(tmp_path)

    plan = DueWorkPlanner(store).plan(datetime(2026, 7, 14, 11, 20, 0, tzinfo=UTC))

    assert [item.schedule_id for item in plan] == [
        "a-ready",
        "b-claimed",
        "c-disabled-schedule",
        "d-missing-target",
        "e-disabled-target",
        "f-before-start",
    ]
    assert [item.status for item in plan] == [
        DuePlanStatus.READY_TO_CLAIM,
        DuePlanStatus.ALREADY_CLAIMED,
        DuePlanStatus.SCHEDULE_DISABLED,
        DuePlanStatus.TARGET_MISSING,
        DuePlanStatus.TARGET_DISABLED,
        DuePlanStatus.BEFORE_START,
    ]
    assert plan[0].occurrence_at == latest_boundary
    assert plan[0].execution_key == execution_key("a-ready", latest_boundary)
    assert plan[1].existing_occurrence_status is not None
    assert _snapshot(tmp_path) == before


def test_due_work_planner_detects_latest_claim_and_normalizes_timezone(
    tmp_path: Path,
) -> None:
    store = JsonStore(tmp_path)
    target = Target(
        target_id="planned-target",
        name="Planned",
        url="https://example.com",
    )
    schedule = IntervalSchedule(
        schedule_id="planned-hourly",
        target_id=target.target_id,
        start_at=datetime(2026, 7, 14, 7, 0, tzinfo=UTC),
        interval_minutes=60,
    )
    store.create_target(target)
    store.create_schedule(schedule)
    occurrence_at = datetime(2026, 7, 14, 10, 0, tzinfo=UTC)
    store.claim_occurrence(
        ScheduleOccurrence(
            execution_key=execution_key(schedule.schedule_id, occurrence_at),
            schedule_id=schedule.schedule_id,
            target_id=target.target_id,
            occurrence_at=occurrence_at,
            claimed_at=datetime(2026, 7, 14, 10, 1, tzinfo=UTC),
        )
    )

    plan = DueWorkPlanner(store).plan(
        datetime.fromisoformat("2026-07-14T12:20:00+02:00")
    )

    assert len(plan) == 1
    assert plan[0].status == DuePlanStatus.ALREADY_CLAIMED
    assert plan[0].evaluated_at == datetime(2026, 7, 14, 10, 20, tzinfo=UTC)
    assert plan[0].occurrence_at == occurrence_at
    assert plan[0].existing_occurrence_status is not None
