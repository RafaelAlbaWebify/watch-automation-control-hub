from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from watch.api import create_app
from watch.models import IntervalSchedule, ObservationSet, Target
from watch.occurrences import execution_key, latest_due_occurrence


class FailingCollector:
    def collect(self, target: Target) -> ObservationSet:
        raise AssertionError("occurrence evaluation must not invoke the collector")


def _target_payload(enabled: bool = True) -> dict[str, object]:
    return {
        "target_id": "scheduled-target",
        "name": "Scheduled Target",
        "url": "https://example.com",
        "enabled": enabled,
        "tags": [],
        "expected_status_codes": [200],
        "timeout_seconds": 10,
    }


def _schedule_payload(enabled: bool = True) -> dict[str, object]:
    return {
        "schedule_id": "hourly-check",
        "target_id": "scheduled-target",
        "enabled": enabled,
        "start_at": "2026-07-14T07:00:00Z",
        "interval_minutes": 60,
    }


def _client_with_schedule(
    tmp_path: Path,
    *,
    target_enabled: bool = True,
    schedule_enabled: bool = True,
) -> TestClient:
    client = TestClient(create_app(tmp_path, collector=FailingCollector()))
    assert client.post(
        "/api/targets", json=_target_payload(target_enabled)
    ).status_code == 201
    assert client.post(
        "/api/schedules", json=_schedule_payload(schedule_enabled)
    ).status_code == 201
    return client


def test_latest_due_occurrence_is_deterministic() -> None:
    schedule = IntervalSchedule.model_validate(_schedule_payload())

    assert latest_due_occurrence(
        schedule, datetime(2026, 7, 14, 6, 59, tzinfo=UTC)
    ) is None
    assert latest_due_occurrence(
        schedule, datetime(2026, 7, 14, 7, 0, tzinfo=UTC)
    ) == datetime(2026, 7, 14, 7, 0, tzinfo=UTC)
    assert latest_due_occurrence(
        schedule, datetime(2026, 7, 14, 8, 59, 59, tzinfo=UTC)
    ) == datetime(2026, 7, 14, 8, 0, tzinfo=UTC)
    assert latest_due_occurrence(
        schedule, datetime(2026, 7, 14, 9, 0, tzinfo=UTC)
    ) == datetime(2026, 7, 14, 9, 0, tzinfo=UTC)


def test_execution_key_is_stable_and_occurrence_specific() -> None:
    first = execution_key("hourly-check", datetime(2026, 7, 14, 7, 0, tzinfo=UTC))
    repeated = execution_key(
        "hourly-check", datetime.fromisoformat("2026-07-14T09:00:00+02:00")
    )
    later = execution_key("hourly-check", datetime(2026, 7, 14, 8, 0, tzinfo=UTC))

    assert first == repeated
    assert first.startswith("occ-")
    assert len(first) == 28
    assert later != first


def test_api_claims_once_and_persists_across_new_app_instances(tmp_path: Path) -> None:
    client = _client_with_schedule(tmp_path)
    request = {"evaluated_at": "2026-07-14T09:42:00+02:00"}

    first = client.post(
        "/api/schedules/hourly-check/occurrences/evaluate", json=request
    )
    assert first.status_code == 200
    assert first.json()["result"] == "claimed"
    occurrence = first.json()["occurrence"]
    assert occurrence["occurrence_at"] == "2026-07-14T07:00:00Z"
    assert occurrence["claimed_at"] == "2026-07-14T07:42:00Z"
    assert occurrence["status"] == "claimed"

    restarted = TestClient(create_app(tmp_path, collector=FailingCollector()))
    repeated = restarted.post(
        "/api/schedules/hourly-check/occurrences/evaluate", json=request
    )
    assert repeated.status_code == 200
    assert repeated.json()["result"] == "already-claimed"
    assert repeated.json()["occurrence"]["execution_key"] == occurrence["execution_key"]

    assert restarted.get("/api/occurrences").json() == [repeated.json()["occurrence"]]
    assert restarted.get(
        f"/api/occurrences/{occurrence['execution_key']}"
    ).status_code == 200
    assert restarted.get("/api/runs").json() == []


def test_later_due_boundary_creates_a_new_occurrence(tmp_path: Path) -> None:
    client = _client_with_schedule(tmp_path)

    first = client.post(
        "/api/schedules/hourly-check/occurrences/evaluate",
        json={"evaluated_at": "2026-07-14T07:59:59Z"},
    ).json()["occurrence"]
    second = client.post(
        "/api/schedules/hourly-check/occurrences/evaluate",
        json={"evaluated_at": "2026-07-14T08:00:00Z"},
    ).json()["occurrence"]

    assert first["occurrence_at"] == "2026-07-14T07:00:00Z"
    assert second["occurrence_at"] == "2026-07-14T08:00:00Z"
    assert first["execution_key"] != second["execution_key"]
    assert len(client.get("/api/occurrences").json()) == 2


def test_evaluation_returns_explicit_no_claim_reasons(tmp_path: Path) -> None:
    before = _client_with_schedule(tmp_path / "before")
    response = before.post(
        "/api/schedules/hourly-check/occurrences/evaluate",
        json={"evaluated_at": "2026-07-14T06:59:59Z"},
    )
    assert response.json() == {"occurrence": None, "result": "before-start"}

    disabled_schedule = _client_with_schedule(
        tmp_path / "schedule-disabled", schedule_enabled=False
    )
    response = disabled_schedule.post(
        "/api/schedules/hourly-check/occurrences/evaluate",
        json={"evaluated_at": "2026-07-14T08:00:00Z"},
    )
    assert response.json() == {"occurrence": None, "result": "schedule-disabled"}

    disabled_target = _client_with_schedule(
        tmp_path / "target-disabled", target_enabled=False
    )
    response = disabled_target.post(
        "/api/schedules/hourly-check/occurrences/evaluate",
        json={"evaluated_at": "2026-07-14T08:00:00Z"},
    )
    assert response.json() == {"occurrence": None, "result": "target-disabled"}


def test_evaluation_rejects_missing_schedule_and_naive_time(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path, collector=FailingCollector()))
    assert client.post(
        "/api/schedules/missing/occurrences/evaluate",
        json={"evaluated_at": "2026-07-14T08:00:00Z"},
    ).status_code == 404

    client = _client_with_schedule(tmp_path / "naive")
    assert client.post(
        "/api/schedules/hourly-check/occurrences/evaluate",
        json={"evaluated_at": "2026-07-14T08:00:00"},
    ).status_code == 422
    assert client.get("/api/occurrences/missing").status_code == 404
