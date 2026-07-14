from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from watch.api import create_app
from watch.models import (
    IntervalSchedule,
    OccurrenceStatus,
    ScheduleOccurrence,
    Target,
)
from watch.occurrences import execution_key
from watch.storage import JsonStore


def _seed_schedule(tmp_path: Path, *, enabled: bool = True) -> JsonStore:
    store = JsonStore(tmp_path)
    store.create_target(
        Target(
            target_id="scheduled-target",
            name="Scheduled Target",
            url="https://example.com",
        )
    )
    store.create_schedule(
        IntervalSchedule(
            schedule_id="hourly-check",
            target_id="scheduled-target",
            enabled=enabled,
            start_at=datetime(2026, 7, 14, 7, 0, tzinfo=UTC),
            interval_minutes=60,
        )
    )
    return store


def _attention(client: TestClient, **overrides: object) -> list[dict[str, object]]:
    payload: dict[str, object] = {
        "evaluated_at": "2026-07-14T10:20:00Z",
        "grace_minutes": 15,
        "lookback_occurrences": 3,
    }
    payload.update(overrides)
    response = client.post("/api/occurrences/attention", json=payload)
    assert response.status_code == 200
    return response.json()


def test_reports_bounded_recent_unclaimed_boundaries(tmp_path: Path) -> None:
    _seed_schedule(tmp_path)
    client = TestClient(create_app(tmp_path))

    items = _attention(client)

    assert [item["kind"] for item in items] == [
        "missed-unclaimed",
        "missed-unclaimed",
        "missed-unclaimed",
    ]
    assert [item["occurrence_at"] for item in items] == [
        "2026-07-14T08:00:00Z",
        "2026-07-14T09:00:00Z",
        "2026-07-14T10:00:00Z",
    ]
    assert all(item["schedule_id"] == "hourly-check" for item in items)


def test_grace_window_and_existing_occurrence_exclude_boundaries(tmp_path: Path) -> None:
    store = _seed_schedule(tmp_path)
    existing_at = datetime(2026, 7, 14, 9, 0, tzinfo=UTC)
    store.claim_occurrence(
        ScheduleOccurrence(
            execution_key=execution_key("hourly-check", existing_at),
            schedule_id="hourly-check",
            target_id="scheduled-target",
            occurrence_at=existing_at,
            claimed_at=datetime(2026, 7, 14, 9, 1, tzinfo=UTC),
        )
    )
    client = TestClient(create_app(tmp_path))

    items = _attention(
        client,
        evaluated_at="2026-07-14T10:05:00Z",
        grace_minutes=15,
        lookback_occurrences=3,
    )

    assert [item["occurrence_at"] for item in items] == [
        "2026-07-14T07:00:00Z",
        "2026-07-14T08:00:00Z",
    ]


def test_reports_stale_executing_occurrence(tmp_path: Path) -> None:
    store = _seed_schedule(tmp_path)
    occurrence_at = datetime(2026, 7, 14, 9, 0, tzinfo=UTC)
    occurrence = ScheduleOccurrence(
        execution_key=execution_key("hourly-check", occurrence_at),
        schedule_id="hourly-check",
        target_id="scheduled-target",
        occurrence_at=occurrence_at,
        claimed_at=datetime(2026, 7, 14, 9, 1, tzinfo=UTC),
        status=OccurrenceStatus.EXECUTING,
        execution_started_at=datetime(2026, 7, 14, 9, 2, tzinfo=UTC),
    )
    store.claim_occurrence(occurrence)

    items = _attention(
        TestClient(create_app(tmp_path)),
        evaluated_at="2026-07-14T10:00:00+00:00",
        grace_minutes=30,
        lookback_occurrences=1,
    )

    stale = [item for item in items if item["kind"] == "executing-stale"]
    assert len(stale) == 1
    assert stale[0]["execution_key"] == occurrence.execution_key
    assert stale[0]["age_minutes"] == 58


def test_disabled_schedule_is_ignored_and_attention_is_read_only(tmp_path: Path) -> None:
    _seed_schedule(tmp_path, enabled=False)
    before = sorted(
        (path.relative_to(tmp_path).as_posix(), path.read_bytes())
        for path in tmp_path.rglob("*")
        if path.is_file()
    )

    items = _attention(TestClient(create_app(tmp_path)))

    after = sorted(
        (path.relative_to(tmp_path).as_posix(), path.read_bytes())
        for path in tmp_path.rglob("*")
        if path.is_file()
    )
    assert items == []
    assert after == before


def test_attention_request_validation(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    assert client.post(
        "/api/occurrences/attention",
        json={
            "evaluated_at": "2026-07-14T10:00:00",
            "grace_minutes": 15,
            "lookback_occurrences": 3,
        },
    ).status_code == 422
    assert client.post(
        "/api/occurrences/attention",
        json={
            "evaluated_at": "2026-07-14T10:00:00Z",
            "grace_minutes": 0,
            "lookback_occurrences": 101,
        },
    ).status_code == 422
