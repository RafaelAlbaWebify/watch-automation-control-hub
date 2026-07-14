from pathlib import Path

from fastapi.testclient import TestClient

from watch.models import ObservationSet, Target
from watch.storage import JsonStore
from watch.targets import TargetService
from watch.webapp import create_app
from watch.workflow import execute_supplied_observations


def _seed_workspace(workspace: Path) -> str:
    target = Target(
        target_id="portfolio-demo",
        name="Portfolio Demo",
        url="https://example.com",
        tags=["portfolio"],
    )
    TargetService(JsonStore(workspace)).create(target)
    run, _, _ = execute_supplied_observations(
        target,
        ObservationSet(
            http_status=503,
            final_url="https://example.com",
            response_ms=420,
            page_title="Example Domain",
        ),
        workspace,
    )
    return run.run_id


def test_empty_dashboard_explains_empty_state(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    response = client.get("/")

    assert response.status_code == 200
    assert "Operator dashboard" in response.text
    assert "No runs have been recorded." in response.text
    assert client.get("/targets").status_code == 200
    assert "No targets are registered." in client.get("/targets").text
    assert "No operational actions are pending." in client.get("/actions").text


def test_dashboard_exposes_existing_targets_runs_actions_and_report(tmp_path: Path) -> None:
    run_id = _seed_workspace(tmp_path)
    client = TestClient(create_app(tmp_path))

    dashboard = client.get("/")
    targets = client.get("/targets")
    runs = client.get("/runs")
    actions = client.get("/actions")
    report = client.get(f"/reports/{run_id}")

    assert dashboard.status_code == 200
    assert "Portfolio Demo" not in dashboard.text
    assert "Latest: completed" in dashboard.text
    assert "Open actions" in dashboard.text
    assert targets.status_code == 200
    assert "Portfolio Demo" in targets.text
    assert "portfolio-demo" in targets.text
    assert runs.status_code == 200
    assert run_id in runs.text
    assert "Open report" in runs.text
    assert actions.status_code == 200
    assert "UNEXPECTED_HTTP_STATUS" in actions.text
    assert report.status_code == 200
    assert "WATCH Operational Report" in report.text


def test_dashboard_keeps_json_api_and_openapi_contract_available(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    assert client.get("/api/health").json() == {
        "status": "ok",
        "mode": "local-operator",
    }
    assert client.get("/openapi.json").status_code == 200
    assert "/" not in client.get("/openapi.json").json()["paths"]


def test_report_page_returns_not_found_for_unknown_run(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    response = client.get("/reports/unknown")

    assert response.status_code == 404
    assert response.json() == {"detail": "report not found"}
