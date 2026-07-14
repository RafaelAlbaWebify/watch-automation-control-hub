from __future__ import annotations

from collections import defaultdict
from html import escape
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from watch.models import OperationalAction, WorkflowRun
from watch.storage import JsonStore
from watch.web_layout import badge, page, table


def _action_count_by_run(actions: list[OperationalAction]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for action in actions:
        counts[action.source_run_id] += 1
    return dict(counts)


def _timeline_rows(runs: list[WorkflowRun], actions: list[OperationalAction]) -> str:
    action_counts = _action_count_by_run(actions)
    rows: list[str] = []
    for run in reversed(runs):
        changes = ", ".join(run.changed_fields)
        event = changes if changes else "baseline evidence"
        previous = (
            f"<code>{escape(run.previous_run_id)}</code>"
            if run.previous_run_id
            else "none"
        )
        rows.append(
            "<tr>"
            f"<td>{escape(run.started_at.isoformat())}</td>"
            f'<td><a href="/targets/{escape(run.target_id)}">'
            f"{escape(run.target_id)}</a></td>"
            f"<td><code>{escape(run.run_id)}</code></td>"
            f"<td>{previous}</td>"
            f"<td>{badge(run.status.value)}</td>"
            f"<td>{escape(event)}</td>"
            f"<td>{len(run.findings)}</td>"
            f"<td>{action_counts.get(run.run_id, 0)}</td>"
            f'<td><a href="/reports/{escape(run.run_id)}">Open report</a></td>'
            "</tr>"
        )
    return "".join(rows)


def mount_change_timeline_routes(app: FastAPI, workspace: Path) -> None:
    store = JsonStore(workspace)

    @app.get("/changes", response_class=HTMLResponse, include_in_schema=False)
    def change_timeline() -> HTMLResponse:
        runs = store.list_runs()
        actions = store.list_actions()
        content = (
            "<thead><tr><th>Observed at</th><th>Target</th><th>Run</th>"
            "<th>Previous run</th><th>Status</th><th>Change event</th>"
            "<th>Findings</th><th>Actions</th><th>Evidence</th>"
            "</tr></thead><tbody>"
            + _timeline_rows(runs, actions)
            + "</tbody>"
        )
        body = (
            '<p class="note">Read-only chronology built from immutable runs, '
            "previous-run links, findings, actions, and reports.</p>"
            + table(content, "Chronological target change evidence")
            if runs
            else '<p class="empty">No run evidence exists for the change timeline.</p>'
        )
        return page("Change timeline", body)
