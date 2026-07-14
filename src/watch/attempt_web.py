from __future__ import annotations

from html import escape
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from watch.attempts import AttemptStore, ExecutionAttempt
from watch.web_layout import badge, page, table


def _attempt_rows(attempts: list[ExecutionAttempt]) -> str:
    rows: list[str] = []
    for attempt in reversed(attempts):
        finished = (
            escape(attempt.finished_at.isoformat())
            if attempt.finished_at is not None
            else "not finished"
        )
        run = (
            f'<a href="/reports/{escape(attempt.run_id)}"><code>'
            f"{escape(attempt.run_id)}</code></a>"
            if attempt.run_id
            else "not linked"
        )
        error = escape(attempt.error) if attempt.error else "none"
        rows.append(
            "<tr>"
            f"<td><code>{escape(attempt.attempt_id)}</code></td>"
            f'<td><a href="/occurrences"><code>'
            f"{escape(attempt.execution_key)}</code></a></td>"
            f"<td>{attempt.attempt_number}</td>"
            f"<td>{escape(attempt.reason)}</td>"
            f"<td>{badge(attempt.status.value)}</td>"
            f"<td>{escape(attempt.started_at.isoformat())}</td>"
            f"<td>{finished}</td>"
            f"<td>{run}</td>"
            f"<td>{error}</td>"
            "</tr>"
        )
    return "".join(rows)


def mount_attempt_web_routes(app: FastAPI, workspace: Path) -> None:
    attempts = AttemptStore(workspace)

    @app.get("/attempts", response_class=HTMLResponse, include_in_schema=False)
    def attempts_page() -> HTMLResponse:
        history = attempts.list()
        content = (
            "<thead><tr><th>Attempt</th><th>Occurrence</th><th>Number</th>"
            "<th>Operator reason</th><th>Status</th><th>Started</th>"
            "<th>Finished</th><th>Run</th><th>Error</th></tr></thead><tbody>"
            + _attempt_rows(history)
            + "</tbody>"
        )
        body = (
            table(content, "Operator-controlled retry attempt history")
            if history
            else '<p class="empty">No retry attempts have been recorded.</p>'
        )
        return page("Retry attempts", body)
