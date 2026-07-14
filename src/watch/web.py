from __future__ import annotations

from html import escape
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from watch.models import ActionStatus, OperationalAction, Target, WorkflowRun
from watch.storage import JsonStore

_STYLE = """
:root { color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }
body { margin: 0; background: #101418; color: #edf2f7; }
header { padding: 1.25rem 2rem; border-bottom: 1px solid #2d3748; }
nav a { color: #90cdf4; margin-right: 1rem; text-decoration: none; }
main { padding: 2rem; max-width: 1200px; margin: 0 auto; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; }
.card { background: #1a202c; border: 1px solid #2d3748; border-radius: 10px; padding: 1rem; }
.metric { font-size: 2rem; font-weight: 700; margin: .25rem 0; }
table { width: 100%; border-collapse: collapse; background: #1a202c; }
th, td { padding: .75rem; border-bottom: 1px solid #2d3748; text-align: left; vertical-align: top; }
th { color: #a0aec0; }
.badge { display: inline-block; padding: .15rem .5rem; border-radius: 999px; background: #2d3748; }
.empty { color: #a0aec0; font-style: italic; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #1a202c; padding: 1rem; border-radius: 10px; }
a { color: #90cdf4; }
"""


def _page(title: str, body: str) -> HTMLResponse:
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} · WATCH</title>
  <style>{_STYLE}</style>
</head>
<body>
<header>
  <h1>WATCH</h1>
  <p>Workflow Automation &amp; Technical Control Hub</p>
  <nav>
    <a href="/">Dashboard</a>
    <a href="/targets">Targets</a>
    <a href="/runs">Runs</a>
    <a href="/actions">Actions</a>
    <a href="/docs">API</a>
  </nav>
</header>
<main>
  <h2>{escape(title)}</h2>
  {body}
</main>
</body>
</html>"""
    return HTMLResponse(document)


def _target_rows(targets: list[Target], runs: list[WorkflowRun]) -> str:
    latest_by_target: dict[str, WorkflowRun] = {}
    for run in runs:
        latest_by_target[run.target_id] = run
    rows = []
    for target in targets:
        latest = latest_by_target.get(target.target_id)
        latest_status = latest.status.value if latest else "never run"
        rows.append(
            "<tr>"
            f"<td>{escape(target.name)}</td>"
            f"<td><code>{escape(target.target_id)}</code></td>"
            f"<td>{escape(str(target.url))}</td>"
            f"<td><span class=\"badge\">{'enabled' if target.enabled else 'disabled'}</span></td>"
            f"<td>{escape(latest_status)}</td>"
            "</tr>"
        )
    return "".join(rows)


def _run_rows(runs: list[WorkflowRun]) -> str:
    rows = []
    for run in reversed(runs):
        rows.append(
            "<tr>"
            f"<td><code>{escape(run.run_id)}</code></td>"
            f"<td>{escape(run.target_id)}</td>"
            f"<td><span class=\"badge\">{escape(run.status.value)}</span></td>"
            f"<td>{len(run.findings)}</td>"
            f"<td>{escape(', '.join(run.changed_fields) or 'none')}</td>"
            f"<td><a href=\"/reports/{escape(run.run_id)}\">Open report</a></td>"
            "</tr>"
        )
    return "".join(rows)


def _action_rows(actions: list[OperationalAction]) -> str:
    rows = []
    for action in reversed(actions):
        rows.append(
            "<tr>"
            f"<td>{escape(action.severity.value)}</td>"
            f"<td><span class=\"badge\">{escape(action.status.value)}</span></td>"
            f"<td>{escape(action.target_id)}</td>"
            f"<td><code>{escape(action.finding_code)}</code></td>"
            f"<td>{escape(action.summary)}</td>"
            f"<td><code>{escape(action.source_run_id)}</code></td>"
            "</tr>"
        )
    return "".join(rows)


def mount_web_routes(app: FastAPI, workspace: Path) -> None:
    store = JsonStore(workspace)

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def dashboard() -> HTMLResponse:
        targets = store.list_targets()
        runs = store.list_runs()
        actions = store.list_actions()
        enabled = sum(target.enabled for target in targets)
        open_actions = sum(action.status == ActionStatus.OPEN for action in actions)
        acknowledged = sum(action.status == ActionStatus.ACKNOWLEDGED for action in actions)
        latest = runs[-1].status.value if runs else "no runs"
        body = f"""
<section class="grid" aria-label="Operational summary">
  <article class="card"><h3>Targets</h3><p class="metric">{len(targets)}</p><p>{enabled} enabled</p></article>
  <article class="card"><h3>Runs</h3><p class="metric">{len(runs)}</p><p>Latest: {escape(latest)}</p></article>
  <article class="card"><h3>Open actions</h3><p class="metric">{open_actions}</p><p>{acknowledged} acknowledged</p></article>
</section>
<section>
  <h3>Latest runs</h3>
  {('<table><thead><tr><th>Run</th><th>Target</th><th>Status</th><th>Findings</th><th>Changes</th><th>Report</th></tr></thead><tbody>' + _run_rows(runs[-5:]) + '</tbody></table>') if runs else '<p class="empty">No runs have been recorded.</p>'}
</section>
"""
        return _page("Operator dashboard", body)

    @app.get("/targets", response_class=HTMLResponse, include_in_schema=False)
    def targets_page() -> HTMLResponse:
        targets = store.list_targets()
        runs = store.list_runs()
        body = (
            '<table><thead><tr><th>Name</th><th>ID</th><th>URL</th><th>State</th><th>Latest run</th></tr></thead><tbody>'
            + _target_rows(targets, runs)
            + "</tbody></table>"
            if targets
            else '<p class="empty">No targets are registered.</p>'
        )
        return _page("Targets", body)

    @app.get("/runs", response_class=HTMLResponse, include_in_schema=False)
    def runs_page() -> HTMLResponse:
        runs = store.list_runs()
        body = (
            '<table><thead><tr><th>Run</th><th>Target</th><th>Status</th><th>Findings</th><th>Changes</th><th>Report</th></tr></thead><tbody>'
            + _run_rows(runs)
            + "</tbody></table>"
            if runs
            else '<p class="empty">No runs have been recorded.</p>'
        )
        return _page("Runs", body)

    @app.get("/actions", response_class=HTMLResponse, include_in_schema=False)
    def actions_page() -> HTMLResponse:
        actions = store.list_actions()
        body = (
            '<table><thead><tr><th>Severity</th><th>Status</th><th>Target</th><th>Code</th><th>Summary</th><th>Source run</th></tr></thead><tbody>'
            + _action_rows(actions)
            + "</tbody></table>"
            if actions
            else '<p class="empty">No operational actions are pending.</p>'
        )
        return _page("Actions", body)

    @app.get("/reports/{run_id}", response_class=HTMLResponse, include_in_schema=False)
    def report_page(run_id: str) -> HTMLResponse:
        report = store.read_markdown_report(run_id)
        if report is None:
            raise HTTPException(status_code=404, detail="report not found")
        return _page(f"Report {run_id}", f"<pre>{escape(report)}</pre>")
