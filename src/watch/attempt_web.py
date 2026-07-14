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
        run = (
            f'<a href="/reports/{escape(attempt.run_id)}">'
            f"<code>{escape(attempt.run_id)}</code></a>"
            if attempt.run_id
            else "none"
        )
        finished = attempt.finished_at.isoformat() if attempt.finished_at else "pending"
        rows.append(
            "<tr>"
            f"<td>{attempt.attempt_number}</td>"
            f"<td>{badge(attempt.status.value)}</td>"
            f"<td><code>{escape(attempt.attempt_id)}</code></td>"
            f"<td><code>{escape(attempt.execution_key)}</code></td>"
            f"<td>{escape(attempt.started_at.isoformat())}</td>"
            f"<td>{escape(finished)}</td>"
            f"<td>{run}</td>"
            f"<td>{escape(attempt.error or 'none')}</td>"
            "</tr>"
        )
    return "".join(rows)


def mount_attempt_web_routes(app: FastAPI, workspace: Path) -> None:
    store = AttemptStore(workspace)

    @app.get("/attempts", response_class=HTMLResponse, include_in_schema=False)
    def attempts_page() -> HTMLResponse:
        attempts = store.list()
        if not attempts:
            return page(
                "Attempts",
                '<p class="empty">No retry attempt evidence has been recorded.</p>',
            )
        content = (
            "<thead><tr><th>Number</th><th>Status</th><th>Attempt</th>"
            "<th>Occurrence</th><th>Started</th><th>Finished</th>"
            "<th>Run</th><th>Error</th></tr></thead><tbody>"
            + _attempt_rows(attempts)
            + "</tbody>"
        )
        body = (
            '<p class="note">Read-only retry evidence. Retry execution remains an '
            "explicit API operation with a hard three-attempt limit.</p>"
            + table(content, "Immutable occurrence execution attempts")
        )
        return page("Attempts", body)
