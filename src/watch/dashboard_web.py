from __future__ import annotations

from datetime import UTC, datetime
from html import escape
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from watch.attempts import AttemptStore
from watch.models import ActionStatus, OccurrenceStatus, WorkflowRun
from watch.occurrences import OccurrenceAttentionService
from watch.storage import JsonStore
from watch.web_layout import badge, page, table


def _recent_run_rows(runs: list[WorkflowRun]) -> str:
    rows: list[str] = []
    for run in reversed(runs[-5:]):
        changes = ", ".join(run.changed_fields) or "none"
        rows.append(
            "<tr>"
            f"<td><code>{escape(run.run_id)}</code></td>"
            f'<td><a href="/targets/{escape(run.target_id)}">'
            f"{escape(run.target_id)}</a></td>"
            f"<td>{badge(run.status.value)}</td>"
            f"<td>{len(run.findings)}</td>"
            f"<td>{escape(changes)}</td>"
            f'<td><a href="/reports/{escape(run.run_id)}">Open report</a></td>'
            "</tr>"
        )
    return "".join(rows)


def _recent_runs_table(runs: list[WorkflowRun]) -> str:
    if not runs:
        return '<p class="empty">No runs have been recorded.</p>'
    content = (
        "<thead><tr><th>Run</th><th>Target</th><th>Status</th>"
        "<th>Findings</th><th>Changes</th><th>Report</th></tr></thead><tbody>"
        + _recent_run_rows(runs)
        + "</tbody>"
    )
    return table(content, "Five most recent workflow runs")


def mount_dashboard_route(app: FastAPI, workspace: Path) -> None:
    store = JsonStore(workspace)
    attempt_store = AttemptStore(workspace)

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def dashboard() -> HTMLResponse:
        targets = store.list_targets()
        schedules = store.list_schedules()
        occurrences = store.list_occurrences()
        attempts = attempt_store.list()
        runs = store.list_runs()
        actions = store.list_actions()

        enabled_targets = sum(target.enabled for target in targets)
        enabled_schedules = sum(schedule.enabled for schedule in schedules)
        open_actions = sum(action.status == ActionStatus.OPEN for action in actions)
        acknowledged = sum(
            action.status == ActionStatus.ACKNOWLEDGED for action in actions
        )
        completed_runs = sum(run.status.value == "completed" for run in runs)
        non_success_runs = sum(run.status.value != "completed" for run in runs)
        active_occurrences = sum(
            occurrence.status in {OccurrenceStatus.CLAIMED, OccurrenceStatus.EXECUTING}
            for occurrence in occurrences
        )
        latest = runs[-1].status.value if runs else "no runs"

        attention = OccurrenceAttentionService(store).inspect(
            evaluated_at=datetime.now(UTC),
            grace_minutes=15,
            lookback_occurrences=10,
        )

        target_links = (
            '<ul class="target-list">'
            + "".join(
                f'<li><a href="/targets/{escape(target.target_id)}">'
                f"{escape(target.name)}<br>"
                f"<small>{badge('enabled' if target.enabled else 'disabled')}</small>"
                "</a></li>"
                for target in targets
            )
            + "</ul>"
            if targets
            else '<p class="empty">No targets are registered.</p>'
        )

        body = f"""
<section class="grid" aria-label="Operational summary">
  <article class="card">
    <h3>Registered targets</h3>
    <p class="metric">{len(targets)}</p>
    <p>{enabled_targets} enabled</p>
  </article>
  <article class="card">
    <h3>Enabled schedules</h3>
    <p class="metric">{enabled_schedules}</p>
    <p>{len(schedules)} configured</p>
  </article>
  <article class="card">
    <h3>Active occurrences</h3>
    <p class="metric">{active_occurrences}</p>
    <p>{len(occurrences)} persisted records</p>
  </article>
  <article class="card">
    <h3>Successful runs</h3>
    <p class="metric">{completed_runs}</p>
    <p>Latest: {badge(latest)}</p>
  </article>
  <article class="card">
    <h3>Retry attempts</h3>
    <p class="metric">{len(attempts)}</p>
    <p>{non_success_runs} partial or failed runs</p>
  </article>
  <article class="card">
    <h3>Open actions</h3>
    <p class="metric">{open_actions}</p>
    <p>{acknowledged} acknowledged</p>
  </article>
</section>
<section class="dashboard-columns" aria-label="Dashboard detail">
  <div class="panel">
    <div class="panel-heading">
      <h3>Target drill-down</h3>
      <p>Registered public endpoints</p>
    </div>
    {target_links}
  </div>
  <aside class="panel" aria-label="Current control status">
    <div class="panel-heading">
      <h3>Current status</h3>
      <p>Read-only summary</p>
    </div>
    <table class="compact">
      <tbody>
        <tr><th scope="row">Attention items</th><td>{len(attention)}</td></tr>
        <tr><th scope="row">Retry evidence</th><td>{len(attempts)}</td></tr>
        <tr><th scope="row">Operational actions</th><td>{len(actions)}</td></tr>
        <tr><th scope="row">Execution mode</th><td>Local operator</td></tr>
        <tr><th scope="row">Remediation</th><td>{badge('disabled')}</td></tr>
      </tbody>
    </table>
  </aside>
</section>
<section>
  <h3>Latest runs</h3>
  {_recent_runs_table(runs)}
</section>
"""
        return page("Operator dashboard", body)
