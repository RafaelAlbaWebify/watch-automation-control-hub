from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from html import escape
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from watch.attempt_web import _attempt_rows
from watch.attempts import AttemptStore
from watch.change_timeline import _timeline_rows
from watch.models import ActionStatus
from watch.occurrences import OccurrenceAttentionService
from watch.storage import JsonStore
from watch.target_detail import _action_rows as _target_action_rows
from watch.target_detail import _run_rows as _target_run_rows
from watch.web import (
    _action_rows,
    _attention_rows,
    _occurrence_rows,
    _run_table,
    _schedule_rows,
    _target_rows,
)
from watch.web_layout import badge, page, table


def _summary_card(label: str, value: str, detail: str) -> str:
    return (
        '<article class="card">'
        f"<h3>{escape(label)}</h3>"
        f'<p class="metric">{value}</p>'
        f"<p>{detail}</p>"
        "</article>"
    )


def _panel(title: str, subtitle: str, content: str) -> str:
    return (
        '<section class="panel">'
        '<div class="panel-heading">'
        f"<h3>{escape(title)}</h3><p>{escape(subtitle)}</p>"
        "</div>"
        f"{content}"
        "</section>"
    )


def mount_refined_web_routes(app: FastAPI, workspace: Path) -> None:
    store = JsonStore(workspace)
    attempts = AttemptStore(workspace)

    @app.get("/targets", response_class=HTMLResponse, include_in_schema=False)
    def targets_page() -> HTMLResponse:
        targets = store.list_targets()
        runs = store.list_runs()
        enabled = sum(target.enabled for target in targets)
        never_run = sum(not any(run.target_id == target.target_id for run in runs) for target in targets)
        summary = (
            '<section class="grid" aria-label="Target inventory summary">'
            + _summary_card("Registered", str(len(targets)), "public endpoints")
            + _summary_card("Enabled", str(enabled), "included in operations")
            + _summary_card("Disabled", str(len(targets) - enabled), "retained but inactive")
            + _summary_card("Never run", str(never_run), "awaiting first evidence")
            + "</section>"
        )
        content = (
            "<thead><tr><th>Name</th><th>ID</th><th>URL</th>"
            "<th>State</th><th>Latest run</th></tr></thead><tbody>"
            + _target_rows(targets, runs)
            + "</tbody>"
        )
        evidence = (
            table(content, "Registered operational targets")
            if targets
            else '<p class="empty">No targets are registered.</p>'
        )
        return page("Targets", summary + _panel("Target inventory", "Read-only configuration and latest state", evidence))

    @app.get("/schedules", response_class=HTMLResponse, include_in_schema=False)
    def schedules_page() -> HTMLResponse:
        schedules = store.list_schedules()
        enabled = sum(schedule.enabled for schedule in schedules)
        intervals = {schedule.interval_minutes for schedule in schedules}
        summary = (
            '<section class="grid" aria-label="Schedule inventory summary">'
            + _summary_card("Configured", str(len(schedules)), "recurring schedules")
            + _summary_card("Enabled", str(enabled), "eligible for execution")
            + _summary_card("Disabled", str(len(schedules) - enabled), "retained but inactive")
            + _summary_card("Intervals", str(len(intervals)), "distinct cadences")
            + "</section>"
        )
        content = (
            "<thead><tr><th>Schedule</th><th>Target</th><th>State</th>"
            "<th>Starts</th><th>Interval</th></tr></thead><tbody>"
            + _schedule_rows(schedules)
            + "</tbody>"
        )
        evidence = (
            table(content, "Configured recurring schedules")
            if schedules
            else '<p class="empty">No schedules are configured.</p>'
        )
        return page("Schedules", summary + _panel("Schedule inventory", "Persisted local execution policy", evidence))

    @app.get("/occurrences", response_class=HTMLResponse, include_in_schema=False)
    def occurrences_page() -> HTMLResponse:
        occurrences = store.list_occurrences()
        statuses: dict[str, int] = defaultdict(int)
        for occurrence in occurrences:
            statuses[occurrence.status.value] += 1
        summary = (
            '<section class="grid" aria-label="Occurrence summary">'
            + _summary_card("Persisted", str(len(occurrences)), "execution boundaries")
            + _summary_card("Claimed", str(statuses.get("claimed", 0)), "reserved for execution")
            + _summary_card("Executing", str(statuses.get("executing", 0)), "currently in progress")
            + _summary_card("Completed", str(statuses.get("completed", 0)), "linked evidence records")
            + "</section>"
        )
        content = (
            "<thead><tr><th>Execution key</th><th>Schedule</th><th>Target</th>"
            "<th>Due at</th><th>Status</th><th>Run</th><th>Error</th></tr></thead><tbody>"
            + _occurrence_rows(occurrences)
            + "</tbody>"
        )
        evidence = (
            table(content, "Persisted schedule occurrences")
            if occurrences
            else '<p class="empty">No schedule occurrences are recorded.</p>'
        )
        return page("Occurrences", summary + _panel("Occurrence ledger", "Immutable due-time and claim evidence", evidence))

    @app.get("/attention", response_class=HTMLResponse, include_in_schema=False)
    def attention_page() -> HTMLResponse:
        evaluated_at = datetime.now(UTC)
        attention = OccurrenceAttentionService(store).inspect(
            evaluated_at=evaluated_at,
            grace_minutes=15,
            lookback_occurrences=10,
        )
        kinds: dict[str, int] = defaultdict(int)
        for item in attention:
            kinds[item.kind.value] += 1
        summary = (
            '<section class="grid" aria-label="Attention summary">'
            + _summary_card("Attention items", str(len(attention)), "requiring operator review")
            + _summary_card("Missed", str(kinds.get("missed-unclaimed", 0)), "unclaimed due boundaries")
            + _summary_card("Stale", str(kinds.get("executing-stale", 0)), "long-running executions")
            + _summary_card("Grace", "15 min", "read-only threshold")
            + "</section>"
        )
        content = (
            "<thead><tr><th>Kind</th><th>Schedule</th><th>Target</th>"
            "<th>Due at</th><th>Age</th><th>Details</th></tr></thead><tbody>"
            + _attention_rows(attention)
            + "</tbody>"
        )
        evidence = (
            table(content, "Missed and stale occurrence attention")
            if attention
            else '<p class="empty">No missed or stale occurrences need attention.</p>'
        )
        note = (
            '<p class="note">Read-only inspection using a 15-minute grace period and '
            f"10-boundary lookback. Evaluated at {escape(evaluated_at.isoformat())}.</p>"
        )
        return page("Schedule attention", summary + note + _panel("Attention queue", "No automatic remediation", evidence))

    @app.get("/attempts", response_class=HTMLResponse, include_in_schema=False)
    def attempts_page() -> HTMLResponse:
        history = attempts.list()
        completed = sum(attempt.status.value == "completed" for attempt in history)
        failed = sum(attempt.status.value == "failed" for attempt in history)
        linked = sum(attempt.run_id is not None for attempt in history)
        summary = (
            '<section class="grid" aria-label="Retry attempt summary">'
            + _summary_card("Attempts", str(len(history)), "operator-controlled retries")
            + _summary_card("Completed", str(completed), "successful retry executions")
            + _summary_card("Failed", str(failed), "retained error evidence")
            + _summary_card("Linked runs", str(linked), "report evidence available")
            + "</section>"
        )
        content = (
            "<thead><tr><th>Attempt</th><th>Occurrence</th><th>Number</th>"
            "<th>Operator reason</th><th>Status</th><th>Started</th>"
            "<th>Finished</th><th>Run</th><th>Error</th></tr></thead><tbody>"
            + _attempt_rows(history)
            + "</tbody>"
        )
        evidence = (
            table(content, "Operator-controlled retry attempt history")
            if history
            else '<p class="empty">No retry attempts have been recorded.</p>'
        )
        return page("Retry attempts", summary + _panel("Retry evidence", "Explicit operator intent and immutable outcomes", evidence))

    @app.get("/runs", response_class=HTMLResponse, include_in_schema=False)
    def runs_page() -> HTMLResponse:
        runs = store.list_runs()
        completed = sum(run.status.value == "completed" for run in runs)
        findings = sum(len(run.findings) for run in runs)
        changed = sum(bool(run.changed_fields) for run in runs)
        summary = (
            '<section class="grid" aria-label="Run history summary">'
            + _summary_card("Runs", str(len(runs)), "immutable executions")
            + _summary_card("Completed", str(completed), "successful collections")
            + _summary_card("With changes", str(changed), "delta evidence recorded")
            + _summary_card("Findings", str(findings), "total observations raised")
            + "</section>"
        )
        evidence = (
            _run_table(runs, "Immutable workflow run history")
            if runs
            else '<p class="empty">No runs have been recorded.</p>'
        )
        return page("Runs", summary + _panel("Execution history", "Reports remain linked to their source run", evidence))

    @app.get("/changes", response_class=HTMLResponse, include_in_schema=False)
    def changes_page() -> HTMLResponse:
        runs = store.list_runs()
        if not runs:
            return page("Change timeline", '<p class="empty">No run evidence exists for the change timeline.</p>')
        actions = store.list_actions()
        changed = sum(bool(run.changed_fields) for run in runs)
        baselines = len(runs) - changed
        summary = (
            '<section class="grid" aria-label="Change evidence summary">'
            + _summary_card("Evidence events", str(len(runs)), "chronological run records")
            + _summary_card("Changes", str(changed), "delta-bearing runs")
            + _summary_card("Baselines", str(baselines), "initial evidence records")
            + _summary_card("Actions", str(len(actions)), "linked operational follow-up")
            + "</section>"
        )
        content = (
            "<thead><tr><th>Observed at</th><th>Target</th><th>Run</th>"
            "<th>Previous run</th><th>Status</th><th>Change event</th>"
            "<th>Findings</th><th>Actions</th><th>Evidence</th></tr></thead><tbody>"
            + _timeline_rows(runs, actions)
            + "</tbody>"
        )
        note = '<p class="note">Read-only chronology built from immutable runs, previous-run links, findings, actions, and reports.</p>'
        return page("Change timeline", summary + note + _panel("Change chronology", "Oldest evidence remains traceable through previous-run links", table(content, "Chronological target change evidence")))

    @app.get("/actions", response_class=HTMLResponse, include_in_schema=False)
    def actions_page() -> HTMLResponse:
        actions = store.list_actions()
        open_count = sum(action.status == ActionStatus.OPEN for action in actions)
        acknowledged = sum(action.status == ActionStatus.ACKNOWLEDGED for action in actions)
        resolved = len(actions) - open_count - acknowledged
        summary = (
            '<section class="grid" aria-label="Operational action summary">'
            + _summary_card("Actions", str(len(actions)), "finding-derived records")
            + _summary_card("Open", str(open_count), "awaiting operator response")
            + _summary_card("Acknowledged", str(acknowledged), "accepted for follow-up")
            + _summary_card("Resolved", str(resolved), "closed evidence")
            + "</section>"
        )
        content = (
            "<thead><tr><th>Severity</th><th>Status</th><th>Target</th>"
            "<th>Code</th><th>Summary</th><th>Source run</th></tr></thead><tbody>"
            + _action_rows(actions)
            + "</tbody>"
        )
        evidence = (
            table(content, "Operational action history")
            if actions
            else '<p class="empty">No operational actions are pending.</p>'
        )
        return page("Actions", summary + _panel("Action register", "Read-only operational follow-up derived from findings", evidence))

    @app.get("/reports/{run_id}", response_class=HTMLResponse, include_in_schema=False)
    def report_page(run_id: str) -> HTMLResponse:
        report = store.read_markdown_report(run_id)
        if report is None:
            raise HTTPException(status_code=404, detail="report not found")
        runs = [run for run in store.list_runs() if run.run_id == run_id]
        run = runs[0] if runs else None
        summary = (
            '<section class="grid" aria-label="Report summary">'
            + _summary_card("Run", f"<code>{escape(run_id)}</code>", "immutable report identifier")
            + _summary_card("Status", badge(run.status.value) if run else badge("unknown"), "collection outcome")
            + _summary_card("Findings", str(len(run.findings)) if run else "0", "recorded observations")
            + _summary_card("Changes", str(len(run.changed_fields)) if run else "0", "fields changed from previous run")
            + "</section>"
        )
        evidence = f'<div class="panel"><pre>{escape(report)}</pre></div>'
        return page(f"Report {run_id}", summary + _panel("Operational report", "Preserved markdown evidence", evidence), current_path="/runs")

    @app.get("/targets/{target_id}", response_class=HTMLResponse, include_in_schema=False)
    def target_detail(target_id: str) -> HTMLResponse:
        target = store.get_target(target_id)
        if target is None:
            raise HTTPException(status_code=404, detail="target not found")
        schedules = [schedule for schedule in store.list_schedules() if schedule.target_id == target_id]
        runs = store.list_runs(target_id)
        actions = [action for action in store.list_actions() if action.target_id == target_id]
        action_counts: dict[str, int] = defaultdict(int)
        for action in actions:
            action_counts[action.source_run_id] += 1
        state = "enabled" if target.enabled else "disabled"
        latest = runs[-1].status.value if runs else "never run"
        summary = (
            '<section class="grid" aria-label="Target summary">'
            + _summary_card("State", badge(state), "Target summary")
            + _summary_card("Schedules", str(len(schedules)), "linked execution policies")
            + _summary_card("Runs", str(len(runs)), f"Latest: {badge(latest)}")
            + _summary_card("Actions", str(len(actions)), "operational follow-up")
            + "</section>"
        )
        tags = ", ".join(target.tags) or "none"
        expected = ", ".join(str(code) for code in target.expected_status_codes)
        config = (
            "<tbody>"
            f"<tr><th>ID</th><td><code>{escape(target.target_id)}</code></td></tr>"
            f"<tr><th>URL</th><td>{escape(str(target.url))}</td></tr>"
            f"<tr><th>Tags</th><td>{escape(tags)}</td></tr>"
            f"<tr><th>Expected status</th><td>{escape(expected)}</td></tr>"
            f"<tr><th>Timeout</th><td>{target.timeout_seconds} seconds</td></tr>"
            f"<tr><th>Latest run</th><td>{badge(latest)}</td></tr>"
            "</tbody>"
        )
        configuration = _panel("Configuration", "Target configuration", table(config, "Target configuration", compact=True))
        schedule_content = (
            "<thead><tr><th>Schedule</th><th>State</th><th>Starts</th><th>Interval</th></tr></thead><tbody>"
            + "".join(
                "<tr>"
                f"<td><code>{escape(schedule.schedule_id)}</code></td>"
                f"<td>{badge('enabled' if schedule.enabled else 'disabled')}</td>"
                f"<td>{escape(schedule.start_at.isoformat())}</td>"
                f"<td>{schedule.interval_minutes} minutes</td>"
                "</tr>"
                for schedule in schedules
            )
            + "</tbody>"
        )
        schedule_evidence = table(schedule_content, "Schedules linked to this target") if schedules else '<p class="empty">No schedules.</p>'
        run_content = (
            "<thead><tr><th>Observed at</th><th>Run</th><th>Status</th><th>Changes</th>"
            "<th>Findings</th><th>Actions</th><th>Evidence</th></tr></thead><tbody>"
            + _target_run_rows(runs, action_counts)
            + "</tbody>"
        )
        run_evidence = table(run_content, "Run and change history for this target") if runs else '<p class="empty">No runs.</p>'
        action_content = (
            "<thead><tr><th>Severity</th><th>Status</th><th>Code</th><th>Summary</th><th>Source run</th></tr></thead><tbody>"
            + _target_action_rows(actions)
            + "</tbody>"
        )
        action_evidence = table(action_content, "Operational actions for this target") if actions else '<p class="empty">No actions.</p>'
        body = (
            summary
            + configuration
            + _panel("Schedules", "Schedules linked to this target", schedule_evidence)
            + _panel("Run and change history", "Run and change history for this target", run_evidence)
            + _panel("Operational actions", "Operational actions for this target", action_evidence)
        )
        return page(target.name, body, current_path=f"/targets/{target_id}")
