from __future__ import annotations

from collections import defaultdict
from html import escape
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from watch.models import OperationalAction, WorkflowRun
from watch.storage import JsonStore

_STYLE = """
:root { color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }
body { margin: 0; background: #101418; color: #edf2f7; }
header { padding: 1.25rem 2rem; border-bottom: 1px solid #2d3748; }
nav a { color: #90cdf4; margin-right: 1rem; text-decoration: none; }
main { padding: 2rem; max-width: 1200px; margin: 0 auto; }
table { width: 100%; border-collapse: collapse; background: #1a202c; }
th, td { padding: .75rem; border-bottom: 1px solid #2d3748; text-align: left; }
th { color: #a0aec0; }
.badge { display: inline-block; padding: .15rem .5rem; border-radius: 999px; background: #2d3748; }
.empty, .note { color: #a0aec0; }
a { color: #90cdf4; }
"""


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
            f"<td>{escape(run.target_id)}</td>"
            f"<td><code>{escape(run.run_id)}</code></td>"
            f"<td>{previous}</td>"
            f"<td><span class=\"badge\">{escape(run.status.value)}</span></td>"
            f"<td>{escape(event)}</td>"
            f"<td>{len(run.findings)}</td>"
            f"<td>{action_counts.get(run.run_id, 0)}</td>"
            f"<td><a href=\"/reports/{escape(run.run_id)}\">Open report</a></td>"
            "</tr>"
        )
    return "".join(rows)


def mount_change_timeline_routes(app: FastAPI, workspace: Path) -> None:
    store = JsonStore(workspace)

    @app.get("/changes", response_class=HTMLResponse, include_in_schema=False)
    def change_timeline() -> HTMLResponse:
        runs = store.list_runs()
        actions = store.list_actions()
        body = (
            "<table><thead><tr><th>Observed at</th><th>Target</th><th>Run</th>"
            "<th>Previous run</th><th>Status</th><th>Change event</th>"
            "<th>Findings</th><th>Actions</th><th>Evidence</th>"
            "</tr></thead><tbody>"
            + _timeline_rows(runs, actions)
            + "</tbody></table>"
            if runs
            else '<p class="empty">No run evidence exists for the change timeline.</p>'
        )
        document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Change timeline · WATCH</title>
  <style>{_STYLE}</style>
</head>
<body>
<header>
  <h1>WATCH</h1>
  <p>Workflow Automation &amp; Technical Control Hub</p>
  <nav>
    <a href="/">Dashboard</a>
    <a href="/targets">Targets</a>
    <a href="/schedules">Schedules</a>
    <a href="/occurrences">Occurrences</a>
    <a href="/attention">Attention</a>
    <a href="/runs">Runs</a>
    <a href="/changes">Changes</a>
    <a href="/actions">Actions</a>
    <a href="/docs">API</a>
  </nav>
</header>
<main>
  <h2>Change timeline</h2>
  <p class="note">
    Read-only chronology built from immutable runs, previous-run links,
    findings, actions, and reports.
  </p>
  {body}
</main>
</body>
</html>"""
        return HTMLResponse(document)
