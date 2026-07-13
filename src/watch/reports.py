from __future__ import annotations

from watch.models import OperationalAction, WorkflowRun


def render_markdown(run: WorkflowRun, actions: list[OperationalAction]) -> str:
    lines = [
        "# WATCH Operational Report",
        "",
        f"- Run ID: `{run.run_id}`",
        f"- Target: `{run.target_id}`",
        f"- Status: **{run.status.value}**",
        f"- Started: {run.started_at.isoformat()}",
        f"- Finished: {run.finished_at.isoformat()}",
        f"- Previous run: `{run.previous_run_id or 'none'}`",
        "",
        "## Observations",
        "",
        "| Field | Value |",
        "|---|---|",
    ]
    for key, value in run.observations.model_dump().items():
        lines.append(f"| {key} | {value} |")
    lines.extend(["", "## Changes", ""])
    if run.changed_fields:
        lines.extend(f"- `{field}` changed" for field in run.changed_fields)
    else:
        lines.append("- No previous-run change detected.")
    lines.extend(["", "## Findings", ""])
    for finding in run.findings:
        lines.extend([f"### {finding.code}", "", f"- Severity: **{finding.severity.value}**", f"- Summary: {finding.summary}", f"- Recommended action: {finding.recommended_action}", ""])
    lines.extend(["## Operational actions", ""])
    if actions:
        for action in actions:
            lines.append(f"- `{action.action_id}` — **{action.status.value}** — {action.summary}")
    else:
        lines.append("- No open operational action was required.")
    lines.extend(["", "## Limitations", "", "- Findings are deterministic threshold results, not confirmed root causes.", "- External systems were not modified.", ""])
    return "\n".join(lines)
