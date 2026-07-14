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


def _target_payload() -> dict[str, object]:
    return {
        "target_id": "inventory-demo",
        "name": "Inventory Demo",
        "url": "https://example.com",
        "enabled": True,
        "tags": ["portfolio"],
        "expected_status_codes": [200],
        "timeout_seconds": 10,
    }


def _action_id(tmp_path: Path) -> str:
    _, actions, _ = execute_supplied_observations(
        _target(), ObservationSet(http_status=503), tmp_path
    )
    return actions[0].action_id


def test_empty_workspace_returns_empty_collections(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    assert client.get("/api/health").json() == {
        "status": "ok",
        "mode": "local-operator",
    }
    assert client.get("/api/targets").json() == []
    assert client.get("/api/runs").json() == []
    assert client.get("/api/actions").json() == []


def test_target_inventory_create_list_get_and_update(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    payload = _target_payload()

    created = client.post("/api/targets", json=payload)
    assert created.status_code == 201
    assert created.json()["target_id"] == "inventory-demo"

    assert client.get("/api/targets").json()[0]["name"] == "Inventory Demo"
    assert client.get("/api/targets/inventory-demo").status_code == 200

    update_payload = {
        key: value for key, value in payload.items() if key != "target_id"
    }
    update_payload["name"] = "Updated Inventory Demo"
    update_payload["enabled"] = False
    update_payload["expected_status_codes"] = [204, 200, 200]

    updated = client.put("/api/targets/inventory-demo", json=update_payload)
    assert updated.status_code == 200
    assert updated.json()["target_id"] == "inventory-demo"
    assert updated.json()["name"] == "Updated Inventory Demo"
    assert updated.json()["enabled"] is False
    assert updated.json()["expected_status_codes"] == [200, 204]

    persisted = TestClient(create_app(tmp_path)).get(
        "/api/targets/inventory-demo"
    )
    assert persisted.json()["name"] == "Updated Inventory Demo"


def test_target_inventory_rejects_conflicts_missing_and_invalid_data(
    tmp_path: Path,
) -> None:
    client = TestClient(create_app(tmp_path))
    payload = _target_payload()

    assert client.post("/api/targets", json=payload).status_code == 201
    assert client.post("/api/targets", json=payload).status_code == 409
    assert client.get("/api/targets/missing").status_code == 404

    update_payload = {
        key: value for key, value in payload.items() if key != "target_id"
    }
    assert client.put("/api/targets/missing", json=update_payload).status_code == 404

    invalid_payload = dict(payload)
    invalid_payload["url"] = "file:///etc/passwd"
    assert client.post("/api/targets", json=invalid_payload).status_code == 422

    invalid_update = dict(update_payload)
    invalid_update["timeout_seconds"] = 0
    assert client.put(
        "/api/targets/inventory-demo", json=invalid_update
    ).status_code == 422


def test_api_exposes_persisted_run_action_and_report(tmp_path: Path) -> None:
    run, actions, _ = execute_supplied_observations(
        _target(), ObservationSet(http_status=503, response_ms=2500), tmp_path
    )
    client = TestClient(create_app(tmp_path))
    assert client.get("/api/runs").json()[0]["run_id"] == run.run_id
    assert client.get(f"/api/runs/{run.run_id}").json()["target_id"] == "api-demo"
    assert client.get("/api/actions").json()[0]["action_id"] == actions[0].action_id
    report = client.get(f"/api/reports/{run.run_id}.md")
    assert report.status_code == 200
    assert report.headers["content-type"].startswith("text/markdown")


def test_action_can_be_acknowledged_and_resolved(tmp_path: Path) -> None:
    action_id = _action_id(tmp_path)
    client = TestClient(create_app(tmp_path))

    acknowledged = client.post(f"/api/actions/{action_id}/acknowledge")
    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "acknowledged"

    repeated = client.post(f"/api/actions/{action_id}/acknowledge")
    assert repeated.status_code == 200
    assert repeated.json()["status"] == "acknowledged"

    resolved = client.post(
        f"/api/actions/{action_id}/resolve",
        json={"resolution_note": "Validated and remediated manually."},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["resolution_note"] == "Validated and remediated manually."

    persisted = TestClient(create_app(tmp_path)).get("/api/actions").json()[0]
    assert persisted["status"] == "resolved"


def test_invalid_action_transitions_are_rejected(tmp_path: Path) -> None:
    action_id = _action_id(tmp_path)
    client = TestClient(create_app(tmp_path))

    assert client.post("/api/actions/missing/acknowledge").status_code == 404
    assert client.post(
        f"/api/actions/{action_id}/resolve", json={"resolution_note": "   "}
    ).status_code == 422
    assert client.post(
        f"/api/actions/{action_id}/resolve", json={"resolution_note": "Done"}
    ).status_code == 200
    assert client.post(f"/api/actions/{action_id}/acknowledge").status_code == 409
    assert client.post(
        f"/api/actions/{action_id}/resolve", json={"resolution_note": "Again"}
    ).status_code == 409


def test_missing_run_and_report_return_404(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    assert client.get("/api/runs/run-missing").status_code == 404
    assert client.get("/api/reports/run-missing.md").status_code == 404


def test_openapi_contains_intended_operator_endpoints(tmp_path: Path) -> None:
    schema = TestClient(create_app(tmp_path)).get("/openapi.json").json()
    assert set(schema["paths"]) == {
        "/api/health",
        "/api/targets",
        "/api/targets/{target_id}",
        "/api/runs",
        "/api/runs/{run_id}",
        "/api/actions",
        "/api/actions/{action_id}/acknowledge",
        "/api/actions/{action_id}/resolve",
        "/api/reports/{run_id}.md",
    }
    assert set(schema["paths"]["/api/targets"]) == {"get", "post"}
    assert set(schema["paths"]["/api/targets/{target_id}"]) == {"get", "put"}
    assert set(schema["paths"]["/api/actions/{action_id}/acknowledge"]) == {"post"}
    assert set(schema["paths"]["/api/actions/{action_id}/resolve"]) == {"post"}
