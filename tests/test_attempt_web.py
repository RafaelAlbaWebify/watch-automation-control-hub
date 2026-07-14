from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from watch.attempts import AttemptStatus, AttemptStore, ExecutionAttempt, attempt_id
from watch.webapp import create_app


class NoopCollector:
    def collect(self, target):  # type: ignore[no-untyped-def]
        raise AssertionError("collector must not run for attempt visibility")


def test_attempt_page_has_explicit_empty_state(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path, NoopCollector()))

    response = client.get("/attempts")

    assert response.status_code == 200
    assert "No retry attempt evidence has been recorded." in response.text
    assert 'href="/attempts" aria-current="page"' in response.text
    assert "/attempts" not in client.get("/openapi.json").json()["paths"]


def test_attempt_page_renders_immutable_failure_and_recovery(tmp_path: Path) -> None:
    key = "occ-0123456789abcdef01234567"
    store = AttemptStore(tmp_path)
    store.create(
        ExecutionAttempt(
            attempt_id=attempt_id(key, 1),
            execution_key=key,
            attempt_number=1,
            status=AttemptStatus.FAILED,
            started_at=datetime(2026, 7, 14, 8, 0, tzinfo=UTC),
            finished_at=datetime(2026, 7, 14, 8, 1, tzinfo=UTC),
            error="RuntimeError: first failure",
        )
    )
    store.create(
        ExecutionAttempt(
            attempt_id=attempt_id(key, 2),
            execution_key=key,
            attempt_number=2,
            status=AttemptStatus.COMPLETED,
            started_at=datetime(2026, 7, 14, 8, 5, tzinfo=UTC),
            finished_at=datetime(2026, 7, 14, 8, 6, tzinfo=UTC),
            run_id="run-recovered",
        )
    )
    response = TestClient(create_app(tmp_path, NoopCollector())).get("/attempts")

    assert response.status_code == 200
    assert "Immutable occurrence execution attempts" in response.text
    assert "RuntimeError: first failure" in response.text
    assert "run-recovered" in response.text
    assert "badge-danger">failed" in response.text
    assert "badge-success">completed" in response.text
