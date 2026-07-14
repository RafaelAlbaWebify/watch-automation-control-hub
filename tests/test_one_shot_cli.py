import json
from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from watch.cli import app as cli_app
from watch.models import IntervalSchedule, ObservationSet, Target
from watch.storage import JsonStore


class SuccessfulCollector:
    calls: list[str] = []

    def collect(self, target: Target) -> ObservationSet:
        self.calls.append(target.target_id)
        return ObservationSet(http_status=200, response_ms=50)


def _seed(workspace: Path) -> None:
    store = JsonStore(workspace)
    target = Target(
        target_id="cli-runner-target",
        name="CLI runner target",
        url="https://example.com",
    )
    store.create_target(target)
    store.create_schedule(
        IntervalSchedule(
            schedule_id="cli-runner-hourly",
            target_id=target.target_id,
            start_at=datetime(2026, 7, 14, 7, 0, tzinfo=UTC),
            interval_minutes=60,
        )
    )


def test_run_due_once_cli_emits_machine_readable_summary(
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    _seed(tmp_path)
    collector = SuccessfulCollector()
    monkeypatch.setattr("watch.cli.WebsiteCollector", lambda: collector)  # type: ignore[attr-defined]

    result = CliRunner().invoke(
        cli_app,
        [
            "run-due-once",
            "--evaluated-at",
            "2026-07-14T12:20:00+02:00",
            "--max-work",
            "1",
            "--workspace",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["max_work"] == 1
    assert payload["selected"] == 1
    assert payload["completed"] == 1
    assert payload["results"][0]["schedule_id"] == "cli-runner-hourly"
    assert collector.calls == ["cli-runner-target"]


def test_run_due_once_cli_validates_time_and_limit(tmp_path: Path) -> None:
    _seed(tmp_path)
    runner = CliRunner()

    naive = runner.invoke(
        cli_app,
        [
            "run-due-once",
            "--evaluated-at",
            "2026-07-14T10:20:00",
            "--max-work",
            "1",
            "--workspace",
            str(tmp_path),
        ],
    )
    assert naive.exit_code != 0
    assert "must include a timezone" in naive.output

    invalid_limit = runner.invoke(
        cli_app,
        [
            "run-due-once",
            "--evaluated-at",
            "2026-07-14T10:20:00Z",
            "--max-work",
            "11",
            "--workspace",
            str(tmp_path),
        ],
    )
    assert invalid_limit.exit_code != 0
