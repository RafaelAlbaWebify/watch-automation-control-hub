from pathlib import Path

from fastapi.testclient import TestClient

from watch.api import create_app
from watch.models import ObservationSet, Target


class CountingCollector:
    def __init__(self, observations: ObservationSet | None = None) -> None:
        self.observations = observations or ObservationSet(http_status=200)
        self.calls: list[str] = []
        self.error: Exception | None = None

    def collect(self, target: Target) -> ObservationSet:
        self.calls.append(target.target_id)
        if self.error is not None:
            raise self.error
        return self.observations


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


def _claimed_occurrence(
    tmp_path: Path,
    collector: CountingCollector,
    *,
    target_enabled: bool = True,
    schedule_enabled: bool = True,
) -> tuple[TestClient, str]:
    client = TestClient(create_app(tmp_path, collector=collector))
    assert client.post(
        "/api/targets", json=_target_payload(target_enabled)
    ).status_code == 201
    assert client.post(
        "/api/schedules", json=_schedule_payload(schedule_enabled)
    ).status_code == 201
    evaluated = client.post(
        "/api/schedules/hourly-check/occurrences/evaluate",
        json={"evaluated_at": "2026-07-14T08:00:00Z"},
    )
    assert evaluated.status_code == 200
    return client, evaluated.json()["occurrence"]["execution_key"]


def test_claimed_occurrence_executes_once_and_links_completed_run(
    tmp_path: Path,
) -> None:
    collector = CountingCollector(ObservationSet(http_status=200, response_ms=100))
    client, key = _claimed_occurrence(tmp_path, collector)

    first = client.post(f"/api/occurrences/{key}/execute")
    assert first.status_code == 200
    payload = first.json()
    assert payload["result"] == "completed"
    assert payload["occurrence"]["status"] == "completed"
    assert payload["occurrence"]["execution_started_at"] is not None
    assert payload["occurrence"]["finished_at"] is not None
    assert payload["occurrence"]["run_id"] == payload["run"]["run_id"]
    assert collector.calls == ["scheduled-target"]

    restarted = TestClient(create_app(tmp_path, collector=collector))
    repeated = restarted.post(f"/api/occurrences/{key}/execute")
    assert repeated.status_code == 200
    assert repeated.json()["result"] == "already-finished"
    assert repeated.json()["run"]["run_id"] == payload["run"]["run_id"]
    assert collector.calls == ["scheduled-target"]

    persisted = restarted.get(f"/api/occurrences/{key}").json()
    assert persisted["run_id"] == payload["run"]["run_id"]
    assert len(restarted.get("/api/runs").json()) == 1


def test_partial_workflow_maps_to_partial_occurrence(tmp_path: Path) -> None:
    collector = CountingCollector(
        ObservationSet(errors=["HTTP_TIMEOUT: request exceeded configured timeout"])
    )
    client, key = _claimed_occurrence(tmp_path, collector)

    response = client.post(f"/api/occurrences/{key}/execute")
    assert response.status_code == 200
    assert response.json()["result"] == "partial"
    assert response.json()["occurrence"]["status"] == "partial"
    assert response.json()["run"]["status"] == "partial"
    assert collector.calls == ["scheduled-target"]


def test_collector_exception_is_persisted_and_never_retried(tmp_path: Path) -> None:
    collector = CountingCollector()
    collector.error = RuntimeError("simulated collector failure")
    client, key = _claimed_occurrence(tmp_path, collector)

    failed = client.post(f"/api/occurrences/{key}/execute")
    assert failed.status_code == 200
    payload = failed.json()
    assert payload["result"] == "failed"
    assert payload["occurrence"]["status"] == "failed"
    assert payload["occurrence"]["run_id"] is None
    assert payload["run"] is None
    assert payload["occurrence"]["error"] == (
        "RuntimeError: simulated collector failure"
    )
    assert collector.calls == ["scheduled-target"]

    repeated = TestClient(create_app(tmp_path, collector=collector)).post(
        f"/api/occurrences/{key}/execute"
    )
    assert repeated.json()["result"] == "already-finished"
    assert collector.calls == ["scheduled-target"]
    assert TestClient(create_app(tmp_path)).get("/api/runs").json() == []


def test_disabled_schedule_and_target_block_before_collection(tmp_path: Path) -> None:
    collector = CountingCollector()
    client, key = _claimed_occurrence(tmp_path / "schedule", collector)
    schedule = _schedule_payload(enabled=False)
    schedule.pop("schedule_id")
    schedule.pop("target_id")
    assert client.put("/api/schedules/hourly-check", json=schedule).status_code == 200
    assert client.post(f"/api/occurrences/{key}/execute").status_code == 409

    client, key = _claimed_occurrence(tmp_path / "target", collector)
    target = _target_payload(enabled=False)
    target.pop("target_id")
    assert client.put("/api/targets/scheduled-target", json=target).status_code == 200
    assert client.post(f"/api/occurrences/{key}/execute").status_code == 409
    assert collector.calls == []


def test_missing_occurrence_returns_404(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path, collector=CountingCollector()))
    assert client.post("/api/occurrences/occ-missing/execute").status_code == 404
