from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from watch.models import (
    IntervalSchedule,
    ObservationSet,
    OccurrenceStatus,
    Target,
)
from watch.occurrences import OccurrenceService
from watch.schedules import ScheduleService
from watch.storage import JsonStore
from watch.targets import TargetService
from watch.webapp import create_app
from watch.workflow import execute_supplied_observations


def _seed_workspace(workspace: Path) -> tuple[str, str]:
    store = JsonStore(workspace)
    target = Target(
        target_id="portfolio-demo",
        name="Portfolio Demo",
        url="https://example.com",
        tags=["portfolio"],
    )
    TargetService(store).create(target)
    baseline, _, _ = execute_supplied_observations(
        target,
        ObservationSet(
            http_status=503,
            final_url="https://example.com",
            response_ms=420,
            page_title="Example Domain",
        ),
        workspace,
    )
    changed, _, _ = execute_supplied_observations(
        target,
        ObservationSet(
            http_status=200,
            final_url="https://example.com",
            response_ms=180,
            page_title="Recovered Example Domain",
        ),
        workspace,
    )
    ScheduleService(store).create(
        IntervalSchedule(
            schedule_id="portfolio-hourly",
            target_id=target.target_id,
            start_at=datetime(2024, 1, 1, tzinfo=UTC),
            interval_minutes=60,
        )
    )
    occurrence, result = OccurrenceService(store).evaluate(
        "portfolio-hourly",
        datetime(2024, 1, 1, 1, 5, tzinfo=UTC),
    )
    assert occurrence is not None
    assert result == "claimed"
    store.update_occurrence(
        occurrence.model_copy(
            update={
                "status": OccurrenceStatus.EXECUTING,
                "execution_started_at": datetime(2024, 1, 1, 1, 6, tzinfo=UTC),
            }
        )
    )
    return baseline.run_id, changed.run_id


def test_empty_dashboard_explains_empty_state(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    response = client.get("/")
    assert response.status_code == 200
    assert "Operator dashboard" in response.text
    assert "No runs have been recorded." in response.text
    assert "No targets are registered." in client.get("/targets").text
    assert "No schedules are configured." in client.get("/schedules").text
    assert "No schedule occurrences are recorded." in client.get("/occurrences").text
    assert "No missed or stale occurrences need attention." in client.get("/attention").text
    assert "No run evidence exists for the change timeline." in client.get("/changes").text
    assert "No operational actions are pending." in client.get("/actions").text


def test_dashboard_exposes_operational_scheduling_and_change_evidence(
    tmp_path: Path,
) -> None:
    baseline_run_id, changed_run_id = _seed_workspace(tmp_path)
    client = TestClient(create_app(tmp_path))

    dashboard = client.get("/")
    targets = client.get("/targets")
    schedules = client.get("/schedules")
    occurrences = client.get("/occurrences")
    attention = client.get("/attention")
    runs = client.get("/runs")
    changes = client.get("/changes")
    actions = client.get("/actions")
    target_detail = client.get("/targets/portfolio-demo")
    report = client.get(f"/reports/{changed_run_id}")

    assert dashboard.status_code == 200
    assert "Latest: completed" in dashboard.text
    assert "Target drill-down" in dashboard.text
    assert 'href="/targets/portfolio-demo"' in dashboard.text
    assert "Portfolio Demo" in targets.text
    assert 'href="/targets/portfolio-demo"' in targets.text
    assert "portfolio-hourly" in schedules.text
    assert "60 minutes" in schedules.text
    assert "portfolio-hourly" in occurrences.text
    assert "executing" in occurrences.text
    assert "missed-unclaimed" in attention.text
    assert "executing-stale" in attention.text
    assert changed_run_id in runs.text
    assert "Open report" in runs.text
    assert changes.status_code == 200
    assert baseline_run_id in changes.text
    assert changed_run_id in changes.text
    assert "baseline evidence" in changes.text
    assert "http_status" in changes.text
    assert "Previous run" in changes.text
    assert "UNEXPECTED_HTTP_STATUS" in actions.text
    assert target_detail.status_code == 200
    assert "Target summary" in target_detail.text
    assert "portfolio-hourly" in target_detail.text
    assert "Run and change history" in target_detail.text
    assert "http_status" in target_detail.text
    assert "UNEXPECTED_HTTP_STATUS" in target_detail.text
    assert report.status_code == 200
    assert "WATCH Operational Report" in report.text


def test_all_operator_pages_share_complete_navigation(tmp_path: Path) -> None:
    _seed_workspace(tmp_path)
    client = TestClient(create_app(tmp_path))

    for path in (
        "/",
        "/targets",
        "/targets/portfolio-demo",
        "/schedules",
        "/occurrences",
        "/attention",
        "/runs",
        "/changes",
        "/actions",
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert 'href="/changes">Changes</a>' in response.text
        assert 'href="/targets">Targets</a>' in response.text
        assert 'href="/docs">API</a>' in response.text


def test_dashboard_keeps_json_api_and_openapi_contract_available(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    assert client.get("/api/health").json() == {
        "status": "ok",
        "mode": "local-operator",
    }
    paths = client.get("/openapi.json").json()["paths"]
    assert "/" not in paths
    assert "/changes" not in paths
    assert "/targets/{target_id}" not in paths


def test_unknown_operator_resources_return_not_found(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    report = client.get("/reports/unknown")
    target = client.get("/targets/unknown")
    assert report.status_code == 404
    assert report.json() == {"detail": "report not found"}
    assert target.status_code == 404
    assert target.json() == {"detail": "target not found"}
