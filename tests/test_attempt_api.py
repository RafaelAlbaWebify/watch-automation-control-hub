from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from watch.models import (
    IntervalSchedule,
    ObservationSet,
    OccurrenceStatus,
    ScheduleOccurrence,
    Target,
)
from watch.occurrences import execution_key
from watch.storage import JsonStore
from watch.webapp import create_app


class SuccessfulCollector:
    def collect(self, target: Target) -> ObservationSet:
        return ObservationSet(
            http_status=200,
            final_url=str(target.url),
            redirect_count=0,
            response_ms=40,
            tls_days_remaining=90,
            page_title="Recovered",
            resolved_ips=["93.184.216.34"],
        )


class FailedCollector:
    def collect(self, target: Target) -> ObservationSet:
        raise RuntimeError("still unavailable")


def _failed_occurrence(workspace: Path) -> ScheduleOccurrence:
    store = JsonStore(workspace)
    target = Target(
        target_id="retry-api-target",
        name="Retry API Target",
        url="https://example.com",
    )
    schedule = IntervalSchedule(
        schedule_id="retry-api-hourly",
        target_id=target.target_id,
        start_at=datetime(2026, 7, 14, 7, 0, tzinfo=UTC),
        interval_minutes=60,
    )
    occurrence_at = datetime(2026, 7, 14, 8, 0, tzinfo=UTC)
    occurrence = ScheduleOccurrence(
        execution_key=execution_key(schedule.schedule_id, occurrence_at),
        schedule_id=schedule.schedule_id,
        target_id=target.target_id,
        occurrence_at=occurrence_at,
        claimed_at=datetime(2026, 7, 14, 8, 1, tzinfo=UTC),
        status=OccurrenceStatus.FAILED,
        execution_started_at=datetime(2026, 7, 14, 8, 2, tzinfo=UTC),
        finished_at=datetime(2026, 7, 14, 8, 3, tzinfo=UTC),
        error="RuntimeError: original failure",
    )
    store.create_target(target)
    store.create_schedule(schedule)
    store.claim_occurrence(occurrence)
    return occurrence


def test_attempt_history_and_successful_retry_api(tmp_path: Path) -> None:
    occurrence = _failed_occurrence(tmp_path)
    occurrence_path = tmp_path / "occurrences" / f"{occurrence.execution_key}.json"
    original_bytes = occurrence_path.read_bytes()
    client = TestClient(create_app(tmp_path, SuccessfulCollector()))

    assert client.get("/api/attempts").json() == []
    assert client.get(
        f"/api/occurrences/{occurrence.execution_key}/attempts"
    ).json() == []

    response = client.post(
        f"/api/occurrences/{occurrence.execution_key}/retry",
        json={"reason": "Operator validated a transient service failure."},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] == "completed"
    assert payload["occurrence"]["status"] == "failed"
    assert payload["occurrence"]["error"] == "RuntimeError: original failure"
    assert payload["attempt"]["attempt_number"] == 1
    assert payload["attempt"]["reason"] == (
        "Operator validated a transient service failure."
    )
    assert payload["attempt"]["status"] == "completed"
    assert payload["run"]["run_id"] == payload["attempt"]["run_id"]
    assert occurrence_path.read_bytes() == original_bytes

    attempts = client.get("/api/attempts").json()
    assert [attempt["attempt_number"] for attempt in attempts] == [1]
    assert attempts[0]["status"] == "completed"

    scoped = client.get(
        f"/api/occurrences/{occurrence.execution_key}/attempts"
    ).json()
    assert scoped == attempts


def test_retry_api_maps_missing_validation_and_attempt_limit_errors(
    tmp_path: Path,
) -> None:
    client = TestClient(create_app(tmp_path, FailedCollector()))
    assert client.get("/api/occurrences/missing/attempts").status_code == 404
    assert client.post(
        "/api/occurrences/missing/retry",
        json={"reason": "Missing occurrence."},
    ).status_code == 404
    assert client.post(
        "/api/occurrences/missing/retry",
        json={"reason": "   "},
    ).status_code == 422

    occurrence = _failed_occurrence(tmp_path)
    retry_url = f"/api/occurrences/{occurrence.execution_key}/retry"
    assert client.post(
        retry_url,
        json={"reason": "Operator retry one."},
    ).json()["attempt"]["attempt_number"] == 1
    assert client.post(
        retry_url,
        json={"reason": "Operator retry two."},
    ).json()["attempt"]["attempt_number"] == 2
    assert client.post(
        retry_url,
        json={"reason": "Operator retry three."},
    ).json()["attempt"]["attempt_number"] == 3
    limit = client.post(
        retry_url,
        json={"reason": "Fourth retry must be blocked."},
    )
    assert limit.status_code == 409
    assert limit.json()["detail"] == "attempt limit reached: maximum 3"


def test_retry_routes_are_in_workbench_openapi(tmp_path: Path) -> None:
    schema = TestClient(create_app(tmp_path, SuccessfulCollector())).get(
        "/openapi.json"
    ).json()
    paths = schema["paths"]

    assert "/api/attempts" in paths
    assert "/api/occurrences/{execution_key}/attempts" in paths
    assert "/api/occurrences/{execution_key}/retry" in paths
    request_schema = paths[
        "/api/occurrences/{execution_key}/retry"
    ]["post"]["requestBody"]
    assert request_schema["required"] is True
