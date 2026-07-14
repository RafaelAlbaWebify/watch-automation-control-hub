from __future__ import annotations

from datetime import UTC, datetime
from html import escape
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from watch.models import (
    ActionStatus,
    IntervalSchedule,
    OccurrenceAttention,
    OperationalAction,
    ScheduleOccurrence,
    Target,
    WorkflowRun,
)
from watch.occurrences import OccurrenceAttentionService
from watch.storage import JsonStore
from watch.web_layout import page

_RUN_HEADER = (
    "<table><thead><tr><th>Run</th><th>Target</th><th>Status</th>"
    "<th>Findings</th><th>Changes</th><th>Report</th></tr></thead><tbody>"
)


def _target_rows(targets: list[Target], runs: list[WorkflowRun]) -> str:
    latest_by_target: dict[str, WorkflowRun] = {}
    for run in runs:
        latest_by_target[run.target_id] = run
    rows: list[str] = []
    for target in targets:
        latest = latest_by_target.get(target.target_id)
        latest_status = latest.status.value if latest else "never run"
        state = "enabled" if target.enabled else "disabled"
        target_path = f"/targets/{escape(target.target_id)}"
        rows.append(
            "<tr>"
            f'<td><a href="{target_path}">{escape(target.name)}</a></td>'
            f"<td><code>{escape(target.target_id)}</code></td>"
            f"<td>{escape(str(target.url))}</td>"
            f'<td><span class="badge">{state}</span></td>'
            f"<td>{escape(latest_status)}</td>"
            "</tr>"
        )
    return "".join(rows)


def _schedule_rows(schedules: list[IntervalSchedule]) -> str:
    rows: list[str] = []
    for schedule in schedules:
        state = "enabled" if schedule.enabled else "disabled"
        rows.append(
            "<tr>"
            f"<td><code>{escape(schedule.schedule_id)}</code></td>"
            f'<td><a href="/targets/{escape(schedule.target_id)}">'
            f"{escape(schedule.target_id)}</a></td>"
            f'<td><span class="badge">{state}</span></td>'
            f"<td>{escape(schedule.start_at.isoformat())}</td>"
            f"<td>{schedule.interval_minutes} minutes</td>"
            "</tr>"
        )
    return "".join(rows)


def _occurrence_rows(occurrences: list[ScheduleOccurrence]) -> str:
    rows: list[str] = []
    for occurrence in reversed(occurrences):
        run = (
            f"<code>{escape(occurrence.run_id)}</code>"
            if occurrence.run_id
            else "not linked"
        )
        error = escape(occurrence.error) if occurrence.error else "none"
        rows.append(
            "<tr>"
            f"<td><code>{escape(occurrence.execution_key)}</code></td>"
            f"<td>{escape(occurrence.schedule_id)}</td>"
            f'<td><a href="/targets/{escape(occurrence.target_id)}">'
            f"{escape(occurrence.target_id)}</a></td>"
            f"<td>{escape(occurrence.occurrence_at.isoformat())}</td>"
            f'<td><span class="badge">{escape(occurrence.status.value)}</span></td>'
            f"<td>{run}</td>"
            f"<td>{error}</td>"
            "</tr>"
        )
    return "".join(rows)


def _attention_rows(attention: list[OccurrenceAttention]) -> str:
    rows: list[str] = []
    for item in reversed(attention):
        rows.append(
            "<tr>"
            f"<td>{escape(item.kind.value)}</td>"
            f"<td>{escape(item.schedule_id)}</td>"
            f'<td><a href="/targets/{escape(item.target_id)}">'
            f"{escape(item.target_id)}</a></td>"
            f"<td>{escape(item.occurrence_at.isoformat())}</td>"
            f"<td>{item.age_minutes} minutes</td>"
            f"<td>{escape(item.details)}</td>"
            "</tr>"
        )
    return "".join(rows)


def _run_rows(runs: list[WorkflowRun]) -> str:
    rows: list[str] = []
    for run in reversed(runs):
        changes = ", ".join(run.changed_fields) or "none"
        rows.append(
            "<tr>"
            f"<td><code>{escape(run.run_id)}</code></td>"
            f'<td><a href="/targets/{escape(run.target_id)}">'
            f"{escape(run.target_id)}</a></td>"
            f'<td><span class="badge">{escape(run.status.value)}</span></td>'
            f"<td>{len(run.findings)}</td>"
            f"<td>{escape(changes)}</td>"
            f'<td><a href="/reports/{escape(run.run_id)}">Open report</a></td>'
            "</tr>"
        )
    return "".join(rows)


def _action_rows(actions: list[OperationalAction]) -> str:
    rows: list[str] = []
    for action in reversed(actions):
        rows.append(
            "<tr>"
            f"<td>{escape(action.severity.value)}</td>"
            f'<td><span class="badge">{escape(action.status.value)}</span></td>'
            f'<td><a href="/targets/{escape(action.target_id)}">'
            f"{escape(action.target_id)}</a></td>"
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
        schedules = store.list_schedules()
        occurrences = store.list_occurrences()
        runs = store.list_runs()
        actions = store.list_actions()
        enabled = sum(target.enabled for target in targets)
        enabled_schedules = sum(schedule.enabled for schedule in schedules)
        open_actions = sum(action.status == ActionStatus.OPEN for action in actions)
        acknowledged = sum(
            action.status == ActionStatus.ACKNOWLEDGED for action in actions
        )
        latest = runs[-1].status.value if runs else "no runs"
        latest_runs = (
            _RUN_HEADER + _run_rows(runs[-5:]) + "</tbody></table>"
            if runs
            else '<p class="empty">No runs have been recorded.</p>'
        )
        target_links = (
            "<ul>"
            + "".join(
                f'<li><a href="/targets/{escape(target.target_id)}">'
                f"{escape(target.name)}</a></li>"
                for target in targets
            )
            + "</ul>"
            if targets
            else '<p class="empty">No targets are registered.</p>'
        )
        body = f"""
<section class="grid" aria-label="Operational summary">
  <article class="card">
    <h3>Targets</h3><p class="metric">{len(targets)}</p><p>{enabled} enabled</p>
  </article>
  <article class="card">
    <h3>Schedules</h3><p class="metric">{len(schedules)}</p>
    <p>{enabled_schedules} enabled</p>
  </article>
  <article class="card">
    <h3>Occurrences</h3><p class="metric">{len(occurrences)}</p>
    <p>persisted execution records</p>
  </article>
  <article class="card">
    <h3>Runs</h3><p class="metric">{len(runs)}</p><p>Latest: {escape(latest)}</p>
  </article>
  <article class="card">
    <h3>Open actions</h3><p class="metric">{open_actions}</p>
    <p>{acknowledged} acknowledged</p>
  </article>
</section>
<section><h3>Target drill-down</h3>{target_links}</section>
<section><h3>Latest runs</h3>{latest_runs}</section>
"""
        return page("Operator dashboard", body)

    @app.get("/targets", response_class=HTMLResponse, include_in_schema=False)
    def targets_page() -> HTMLResponse:
        targets = store.list_targets()
        runs = store.list_runs()
        header = (
            "<table><thead><tr><th>Name</th><th>ID</th><th>URL</th>"
            "<th>State</th><th>Latest run</th></tr></thead><tbody>"
        )
        body = (
            header + _target_rows(targets, runs) + "</tbody></table>"
            if targets
            else '<p class="empty">No targets are registered.</p>'
        )
        return page("Targets", body)

    @app.get("/schedules", response_class=HTMLResponse, include_in_schema=False)
    def schedules_page() -> HTMLResponse:
        schedules = store.list_schedules()
        header = (
            "<table><thead><tr><th>Schedule</th><th>Target</th><th>State</th>"
            "<th>Starts</th><th>Interval</th></tr></thead><tbody>"
        )
        body = (
            header + _schedule_rows(schedules) + "</tbody></table>"
            if schedules
            else '<p class="empty">No schedules are configured.</p>'
        )
        return page("Schedules", body)

    @app.get("/occurrences", response_class=HTMLResponse, include_in_schema=False)
    def occurrences_page() -> HTMLResponse:
        occurrences = store.list_occurrences()
        header = (
            "<table><thead><tr><th>Execution key</th><th>Schedule</th>"
            "<th>Target</th><th>Due at</th><th>Status</th><th>Run</th>"
            "<th>Error</th></tr></thead><tbody>"
        )
        body = (
            header + _occurrence_rows(occurrences) + "</tbody></table>"
            if occurrences
            else '<p class="empty">No schedule occurrences are recorded.</p>'
        )
        return page("Occurrences", body)

    @app.get("/attention", response_class=HTMLResponse, include_in_schema=False)
    def attention_page() -> HTMLResponse:
        evaluated_at = datetime.now(UTC)
        attention = OccurrenceAttentionService(store).inspect(
            evaluated_at=evaluated_at,
            grace_minutes=15,
            lookback_occurrences=10,
        )
        header = (
            "<table><thead><tr><th>Kind</th><th>Schedule</th><th>Target</th>"
            "<th>Due at</th><th>Age</th><th>Details</th></tr></thead><tbody>"
        )
        content = (
            header + _attention_rows(attention) + "</tbody></table>"
            if attention
            else '<p class="empty">No missed or stale occurrences need attention.</p>'
        )
        body = (
            '<p class="note">Read-only inspection using a 15-minute grace period and '
            f"10-boundary lookback. Evaluated at {escape(evaluated_at.isoformat())}.</p>"
            + content
        )
        return page("Schedule attention", body)

    @app.get("/runs", response_class=HTMLResponse, include_in_schema=False)
    def runs_page() -> HTMLResponse:
        runs = store.list_runs()
        body = (
            _RUN_HEADER + _run_rows(runs) + "</tbody></table>"
            if runs
            else '<p class="empty">No runs have been recorded.</p>'
        )
        return page("Runs", body)

    @app.get("/actions", response_class=HTMLResponse, include_in_schema=False)
    def actions_page() -> HTMLResponse:
        actions = store.list_actions()
        header = (
            "<table><thead><tr><th>Severity</th><th>Status</th><th>Target</th>"
            "<th>Code</th><th>Summary</th><th>Source run</th></tr></thead><tbody>"
        )
        body = (
            header + _action_rows(actions) + "</tbody></table>"
            if actions
            else '<p class="empty">No operational actions are pending.</p>'
        )
        return page("Actions", body)

    @app.get("/reports/{run_id}", response_class=HTMLResponse, include_in_schema=False)
    def report_page(run_id: str) -> HTMLResponse:
        report = store.read_markdown_report(run_id)
        if report is None:
            raise HTTPException(status_code=404, detail="report not found")
        return page(f"Report {run_id}", f"<pre>{escape(report)}</pre>")
