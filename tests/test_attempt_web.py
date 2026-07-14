from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from watch.attempts import AttemptStatus, AttemptStore, ExecutionAttempt, attempt_id
from watch.webapp import create_app


def test_attempt_page_empty_state_and_openapi_exclusion(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    response = client.get("/attempts")

    assert response.status_code == 200
    assert "No retry attempts have been recorded." in response.text
    assert 'href="/attempts" aria-current="page"' in response.text
    assert "/attempts" not in client.get("/openapi.json").json()["paths"]


def test_attempt_page_renders_escaped_evidence_and_report_link(tmp_path: Path) -> None:
    execution_key = "occ-0123456789abcdef01234567"
    attempt = ExecutionAttempt(
        attempt_id=attempt_id(execution_key, 1),
        execution_key=execution_key,
        attempt_number=1,
        reason="Operator <approved> & reviewed.",
        status=AttemptStatus.FAILED,
        started_at=datetime(2026, 7, 14, 10, 0, tzinfo=UTC),
        finished_at=datetime(2026, 7, 14, 10, 1, tzinfo=UTC),
        run_id="run-example",
        error="RuntimeError: <unsafe> & unavailable",
    )
    AttemptStore(tmp_path).create(attempt)

    response = TestClient(create_app(tmp_path)).get("/attempts")

    assert response.status_code == 200
    assert "Operator-controlled retry attempt history" in response.text
    assert "Operator &lt;approved&gt; &amp; reviewed." in response.text
    assert "RuntimeError: &lt;unsafe&gt; &amp; unavailable" in response.text
    assert '<a href="/reports/run-example"><code>run-example</code></a>' in response.text
    assert 'href="/occurrences"' in response.text
    assert "badge-danger" in response.text


def test_dashboard_shows_attempt_metric(tmp_path: Path) -> None:
    execution_key = "occ-0123456789abcdef01234567"
    AttemptStore(tmp_path).create(
        ExecutionAttempt(
            attempt_id=attempt_id(execution_key, 1),
            execution_key=execution_key,
            attempt_number=1,
            reason="Operator-approved retry.",
            status=AttemptStatus.COMPLETED,
            started_at=datetime(2026, 7, 14, 10, 0, tzinfo=UTC),
            finished_at=datetime(2026, 7, 14, 10, 1, tzinfo=UTC),
        )
    )

    response = TestClient(create_app(tmp_path)).get("/")

    assert response.status_code == 200
    assert "Retry attempts" in response.text
    assert 'href="/attempts"' in response.text
