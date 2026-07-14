import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from watch.cli import app as cli_app
from watch.models import IntervalSchedule, ObservationSet, Target
from watch.storage import JsonStore
from watch.webapp import create_app


class ForbiddenCollector:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def collect(self, target: Target) -> ObservationSet:
        self.calls.append(target.target_id)
        raise AssertionError("due planning must not invoke the collector")


def _snapshot(workspace: Path) -> list[tuple[str, bytes]]:
    return sorted(
        (path.relative_to(workspace).as_posix(), path.read_bytes())
        for path in workspace.rglob("*")
        if path.is_file()
    )


def _seed(workspace: Path) -> None:
    store = JsonStore(workspace)
    target = Target(
        target_id="interface-target",
        name="Interface target",
        url="https://example.com",
    )
    store.create_target(target)
    store.create_schedule(
        IntervalSchedule(
            schedule_id="interface-hourly",
            target_id=target.target_id,
            start_at=datetime(2026, 7, 14, 7, 0, tzinfo=UTC),
            interval_minutes=60,
        )
    )


def test_workbench_due_plan_api_is_read_only_and_skips_collector(tmp_path: Path) -> None:
    _seed(tmp_path)
    before = _snapshot(tmp_path)
    collector = ForbiddenCollector()
    client = TestClient(create_app(tmp_path, collector))

    response = client.post(
        "/api/runner/plan",
        json={"evaluated_at": "2026-07-14T12:20:00+02:00"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["status"] == "ready-to-claim"
    assert payload[0]["evaluated_at"] == "2026-07-14T10:20:00Z"
    assert payload[0]["occurrence_at"] == "2026-07-14T10:00:00Z"
    assert collector.calls == []
    assert _snapshot(tmp_path) == before

    schema = client.get("/openapi.json").json()
    assert set(schema["paths"]["/api/runner/plan"]) == {"post"}


def test_workbench_due_plan_api_rejects_naive_time(tmp_path: Path) -> None:
    _seed(tmp_path)
    response = TestClient(create_app(tmp_path, ForbiddenCollector())).post(
        "/api/runner/plan",
        json={"evaluated_at": "2026-07-14T10:20:00"},
    )
    assert response.status_code == 422


def test_plan_due_cli_emits_json_without_writes(tmp_path: Path) -> None:
    _seed(tmp_path)
    before = _snapshot(tmp_path)

    result = CliRunner().invoke(
        cli_app,
        [
            "plan-due",
            "--evaluated-at",
            "2026-07-14T12:20:00+02:00",
            "--workspace",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload[0]["schedule_id"] == "interface-hourly"
    assert payload[0]["status"] == "ready-to-claim"
    assert payload[0]["execution_key"].startswith("occ-")
    assert _snapshot(tmp_path) == before


def test_plan_due_cli_rejects_naive_time(tmp_path: Path) -> None:
    _seed(tmp_path)
    result = CliRunner().invoke(
        cli_app,
        [
            "plan-due",
            "--evaluated-at",
            "2026-07-14T10:20:00",
            "--workspace",
            str(tmp_path),
        ],
    )
    assert result.exit_code != 0
    assert "must include a timezone" in result.output
