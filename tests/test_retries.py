from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from watch.api import create_app
from watch.models import (
    IntervalSchedule,
    ObservationSet,
    OccurrenceStatus,
    ScheduleOccurrence,
    Target,
)
from watch.occurrences import execution_key
from watch.storage import JsonStore


class RetryCollector:
    def __init__(self, observations: ObservationSet | None = None) -> None:
        self.observations = observations or ObservationSet(http_status=200)
        self.calls: list[str] = []
        self.error: Exception | None = None

    def collect(self, target: Target) -> ObservationSet:
        self.calls.append(target.target_id)
        if self.error is not None:
            raise self.error
        return self.observations


def _seed_failed_occurrence(
    tmp_path: Path,
    *,
    status: OccurrenceStatus = OccurrenceStatus.FAILED,
    target_enabled: bool = True,
    schedule_enabled: bool = True,
) -> tuple[JsonStore, str]:
    store = JsonStore(tmp_path)
    store.create_target(
        Target(
            target_id="retry-target",
            name="Retry Target",
            url="https://example.com",
            enabled=target_enabled,
        )
    )
    store.create_schedule(
        IntervalSchedule(
            schedule_id="retry-schedule",
            target_id="retry-target",
            enabled=schedule_enabled,
            start_at=datetime(2026, 7, 14, 7, 0, tzinfo=UTC),
            interval_minutes=60,
        )
    )
    occurrence_at = datetime(2026, 7, 14, 8, 0, tzinfo=UTC)
    key = execution_key("retry-schedule", occurrence_at)
    store.claim_occurrence(
        ScheduleOccurrence(
            execution_key=key,
            schedule_id="retry-schedule",
            target_id="retry-target",
            occurrence_at=occurrence_at,
            claimed_at=datetime(2026, 7, 14, 8, 1, tzinfo=UTC),
            status=status,
            execution_started_at=datetime(2026, 7, 14, 8, 2, tzinfo=UTC),
            finished_at=(
                datetime(2026, 7, 14, 8, 3, tzinfo=UTC)
                if status == OccurrenceStatus.FAILED
                else None
            ),
            error="RuntimeError: original failure" if status == OccurrenceStatus.FAILED else None,
        )
    )
    return store, key


def test_successful_retry_persists_separate_attempt_and_run(tmp_path: Path) -> None:
    store, key = _seed_failed_occurrence(tmp_path)
    occurrence_path = store.occurrences_dir / f"{key}.json"
    original_bytes = occurrence_path.read_bytes()
    collector = RetryCollector(ObservationSet(http_status=200, response_ms=100))
    client = TestClient(create_app(tmp_path, collector=collector))

    response = client.post(
        f"/api/occurrences/{key}/retries",
        json={"reason": "Operator validated transient failure."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] == "completed"
    assert payload["attempt"]["attempt_number"] == 1
    assert payload["attempt"]["status"] == "completed"
    assert payload["attempt"]["run_id"] == payload["run"]["run_id"]
    assert collector.calls == ["retry-target"]
    assert occurrence_path.read_bytes() == original_bytes

    restarted = TestClient(create_app(tmp_path, collector=collector))
    attempt_id = payload["attempt"]["attempt_id"]
    assert restarted.get(f"/api/retry-attempts/{attempt_id}").status_code == 200
    assert restarted.get("/api/retry-attempts").json()[0]["attempt_id"] == attempt_id
    assert len(restarted.get("/api/runs").json()) == 1


def test_partial_and_failed_retry_results_are_preserved(tmp_path: Path) -> None:
    _, partial_key = _seed_failed_occurrence(tmp_path / "partial")
    partial_collector = RetryCollector(
        ObservationSet(errors=["HTTP_TIMEOUT: request exceeded configured timeout"])
    )
    partial = TestClient(
        create_app(tmp_path / "partial", collector=partial_collector)
    ).post(
        f"/api/occurrences/{partial_key}/retries",
        json={"reason": "Retry after timeout review."},
    )
    assert partial.json()["result"] == "partial"
    assert partial.json()["attempt"]["status"] == "partial"
    assert partial.json()["run"]["status"] == "partial"

    _, failed_key = _seed_failed_occurrence(tmp_path / "failed")
    failed_collector = RetryCollector()
    failed_collector.error = RuntimeError("retry collection failed")
    failed = TestClient(
        create_app(tmp_path / "failed", collector=failed_collector)
    ).post(
        f"/api/occurrences/{failed_key}/retries",
        json={"reason": "Retry after operator approval."},
    )
    assert failed.json()["result"] == "failed"
    assert failed.json()["attempt"]["status"] == "failed"
    assert failed.json()["attempt"]["run_id"] is None
    assert failed.json()["attempt"]["error"] == (
        "RuntimeError: retry collection failed"
    )


def test_retry_limit_is_three_attempts(tmp_path: Path) -> None:
    _, key = _seed_failed_occurrence(tmp_path)
    collector = RetryCollector()
    collector.error = RuntimeError("still failing")
    client = TestClient(create_app(tmp_path, collector=collector))

    for number in range(1, 4):
        response = client.post(
            f"/api/occurrences/{key}/retries",
            json={"reason": f"Approved retry {number}."},
        )
        assert response.status_code == 200
        assert response.json()["attempt"]["attempt_number"] == number

    fourth = client.post(
        f"/api/occurrences/{key}/retries",
        json={"reason": "Fourth retry must be blocked."},
    )
    assert fourth.status_code == 409
    assert len(client.get("/api/retry-attempts").json()) == 3
    assert collector.calls == ["retry-target", "retry-target", "retry-target"]


def test_only_failed_occurrences_can_be_retried(tmp_path: Path) -> None:
    _, key = _seed_failed_occurrence(tmp_path, status=OccurrenceStatus.COMPLETED)
    collector = RetryCollector()
    response = TestClient(create_app(tmp_path, collector=collector)).post(
        f"/api/occurrences/{key}/retries",
        json={"reason": "This must not execute."},
    )
    assert response.status_code == 409
    assert collector.calls == []


def test_disabled_schedule_and_target_block_retry(tmp_path: Path) -> None:
    collector = RetryCollector()
    _, schedule_key = _seed_failed_occurrence(
        tmp_path / "schedule", schedule_enabled=False
    )
    schedule_response = TestClient(
        create_app(tmp_path / "schedule", collector=collector)
    ).post(
        f"/api/occurrences/{schedule_key}/retries",
        json={"reason": "Blocked schedule."},
    )
    assert schedule_response.status_code == 409

    _, target_key = _seed_failed_occurrence(tmp_path / "target", target_enabled=False)
    target_response = TestClient(
        create_app(tmp_path / "target", collector=collector)
    ).post(
        f"/api/occurrences/{target_key}/retries",
        json={"reason": "Blocked target."},
    )
    assert target_response.status_code == 409
    assert collector.calls == []


def test_retry_request_and_missing_resources_are_validated(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path, collector=RetryCollector()))
    assert client.post(
        "/api/occurrences/occ-000000000000000000000000/retries",
        json={"reason": "Missing occurrence."},
    ).status_code == 404
    assert client.post(
        "/api/occurrences/occ-000000000000000000000000/retries",
        json={"reason": "   "},
    ).status_code == 422
    assert client.get("/api/retry-attempts/retry-missing").status_code == 404
