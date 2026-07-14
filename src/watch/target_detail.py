from __future__ import annotations

from collections import defaultdict
from html import escape
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from watch.models import OperationalAction, WorkflowRun
from watch.storage import JsonStore
from watch.web_layout import badge, page, table


def _run_rows(runs: list[WorkflowRun], action_counts: dict[str, int]) -> str:
    rows: list[str] = []
    for run in reversed(runs):
        changes = ", ".join(run.changed_fields) or "baseline evidence"
        rows.append(
            "<tr>"
            f"<td>{escape(run.started_at.isoformat())}</td>"
            f"<td><code>{escape(run.run_id)}</code></td>"
            f"<td>{badge(run.status.value)}</td>"
            f"<td>{escape(changes)}</td>"
            f"<td>{len(run.findings)}</td>"
            f"<td>{action_counts.get(run.run_id, 0)}</td>"
            f'<td><a href="/reports/{escape(run.run_id)}">Open report</a></td>'
            "</tr>"
        )
    return "".join(rows)


def _action_rows(actions: list[OperationalAction]) -> str:
    rows: list[str] = []
    for action in reversed(actions):
        rows.append(
            "<tr>"
            f"<td>{badge(action.severity.value)}</td>"
            f"<td>{badge(action.status.value)}</td>"
            f"<td><code>{escape(action.finding_code)}</code></td>"
            f"<td>{escape(action.summary)}</td>"
            f"<td><code>{escape(action.source_run_id)}</code></td>"
            "</tr>"
        )
    return "".join(rows)


def mount_target_detail_routes(app: FastAPI, workspace: Path) -> None:
    store = JsonStore(workspace)

    @app.get(
        "/targets/{target_id}",
        response_class=HTMLResponse,
        include_in_schema=False,
    )
    def target_detail(target_id: str) -> HTMLResponse:
        target = store.get_target(target_id)
        if target is None:
            raise HTTPException(status_code=404, detail="target not found")

        schedules = [
            schedule
            for schedule in store.list_schedules()
            if schedule.target_id == target_id
        ]
        runs = store.list_runs(target_id)
        actions = [
            action for action in store.list_actions() if action.target_id == target_id
        ]
        action_counts: dict[str, int] = defaultdict(int)
        for action in actions:
            action_counts[action.source_run_id] += 1

        state = "enabled" if target.enabled else "disabled"
        tags = ", ".join(target.tags) or "none"
        expected = ", ".join(str(code) for code in target.expected_status_codes)
        latest = runs[-1].status.value if runs else "never run"
        configuration = (
            "<tbody>"
            f"<tr><th>ID</th><td><code>{escape(target.target_id)}</code></td></tr>"
            f"<tr><th>URL</th><td>{escape(str(target.url))}</td></tr>"
            f"<tr><th>Tags</th><td>{escape(tags)}</td></tr>"
            f"<tr><th>Expected status</th><td>{escape(expected)}</td></tr>"
            f"<tr><th>Timeout</th><td>{target.timeout_seconds} seconds</td></tr>"
            f"<tr><th>Latest run</th><td>{badge(latest)}</td></tr>"
            "</tbody>"
        )
        summary = f"""
<section class="grid" aria-label="Target summary">
  <article class="card"><h3>State</h3><p class="metric">{badge(state)}</p></article>
  <article class="card"><h3>Schedules</h3><p class="metric">{len(schedules)}</p></article>
  <article class="card"><h3>Runs</h3><p class="metric">{len(runs)}</p></article>
  <article class="card"><h3>Actions</h3><p class="metric">{len(actions)}</p></article>
</section>
<section><h3>Configuration</h3>{table(configuration, "Target configuration", compact=True)}</section>
"""
        schedule_content = (
            "<thead><tr><th>Schedule</th><th>State</th><th>Starts</th>"
            "<th>Interval</th></tr></thead><tbody>"
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
        schedule_section = (
            "<section><h3>Schedules</h3>"
            + table(schedule_content, "Schedules linked to this target")
            + "</section>"
            if schedules
            else '<section><h3>Schedules</h3><p class="empty">No schedules.</p></section>'
        )
        run_content = (
            "<thead><tr><th>Observed at</th><th>Run</th><th>Status</th>"
            "<th>Changes</th><th>Findings</th><th>Actions</th><th>Evidence</th>"
            "</tr></thead><tbody>"
            + _run_rows(runs, action_counts)
            + "</tbody>"
        )
        run_section = (
            "<section><h3>Run and change history</h3>"
            + table(run_content, "Run and change history for this target")
            + "</section>"
            if runs
            else '<section><h3>Run and change history</h3><p class="empty">No runs.</p></section>'
        )
        action_content = (
            "<thead><tr><th>Severity</th><th>Status</th><th>Code</th>"
            "<th>Summary</th><th>Source run</th></tr></thead><tbody>"
            + _action_rows(actions)
            + "</tbody>"
        )
        action_section = (
            "<section><h3>Operational actions</h3>"
            + table(action_content, "Operational actions for this target")
            + "</section>"
            if actions
            else '<section><h3>Operational actions</h3><p class="empty">No actions.</p></section>'
        )
        return page(
            target.name,
            summary + schedule_section + run_section + action_section,
            current_path=f"/targets/{target_id}",
        )
