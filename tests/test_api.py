from pathlib import Path

from fastapi.testclient import TestClient

from watch.api import create_app
from watch.models import ObservationSet, Target
from watch.workflow import execute_supplied_observations


def _target() -> Target:
    return Target(
        target_id="api-demo",
        name="API Demo",
        url="https://example.com",
    )


def test_empty_workspace_returns_empty_collections(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    assert client.get("/api/health").json() == {
        "status": "ok",
        "mode": "read-only",
    }
    assert client.get("/api/runs").json() == []
    assert client.get("/api/actions").json() == []


def test_api_exposes_persisted_run_action_and_report(tmp_path: Path) -> None:
    run, actions, _ = execute_supplied_observations(
        _target(),
        ObservationSet(http_status=503, response_ms=2500),
        tmp_path,
    )
    client = TestClient(create_app(tmp_path))

    runs_response = client.get("/api/runs")
    assert runs_response.status_code == 200
    assert runs_response.json()[0]["run_id"] == run.run_id

    run_response = client.get(f"/api/runs/{run.run_id}")
    assert run_response.status_code == 200
    assert run_response.json()["target_id"] == "api-demo"

    actions_response = client.get("/api/actions")
    assert actions_response.status_code == 200
    assert actions_response.json()[0]["action_id"] == actions[0].action_id

    report_response = client.get(f"/api/reports/{run.run_id}.md")
    assert report_response.status_code == 200
    assert report_response.headers["content-type"].startswith("text/markdown")
    assert "# WATCH Operational Report" in report_response.text


def test_missing_run_and_report_return_404(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    run_response = client.get("/api/runs/run-missing")
    report_response = client.get("/api/reports/run-missing.md")

    assert run_response.status_code == 404
    assert run_response.json() == {"detail": "run not found"}
    assert report_response.status_code == 404
    assert report_response.json() == {"detail": "report not found"}


def test_openapi_contains_only_intended_read_endpoints(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    schema = client.get("/openapi.json").json()

    assert set(schema["paths"]) == {
        "/api/health",
        "/api/runs",
        "/api/runs/{run_id}",
        "/api/actions",
        "/api/reports/{run_id}.md",
    }
    for methods in schema["paths"].values():
        assert set(methods) == {"get"}
