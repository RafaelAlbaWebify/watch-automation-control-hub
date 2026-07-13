from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from watch.analysis import analyze
from watch.models import Finding, ObservationSet, OperationalAction, RunStatus, Severity, Target, WorkflowRun
from watch.reports import render_markdown
from watch.storage import JsonStore


def _changed_fields(previous: ObservationSet | None, current: ObservationSet) -> list[str]:
    if previous is None:
        return []
    previous_data = previous.model_dump()
    current_data = current.model_dump()
    return sorted(key for key, value in current_data.items() if previous_data.get(key) != value)


def _action_fingerprint(target_id: str, finding: Finding) -> str:
    return sha256(f"{target_id}:{finding.code}".encode("utf-8")).hexdigest()[:20]


def execute_supplied_observations(target: Target, observations: ObservationSet, workspace: Path) -> tuple[WorkflowRun, list[OperationalAction], list[Path]]:
    store = JsonStore(workspace)
    previous = store.latest_run(target.target_id)
    started_at = datetime.now(UTC)
    findings = analyze(target, observations)
    status = RunStatus.PARTIAL if observations.errors else RunStatus.COMPLETED
    run = WorkflowRun(
        run_id=f"run-{uuid4().hex[:12]}",
        target_id=target.target_id,
        started_at=started_at,
        finished_at=datetime.now(UTC),
        status=status,
        observations=observations,
        findings=findings,
        previous_run_id=previous.run_id if previous else None,
        changed_fields=_changed_fields(previous.observations if previous else None, observations),
    )
    store.save_run(run)

    actions: list[OperationalAction] = []
    for finding in findings:
        if finding.severity == Severity.INFO:
            continue
        fingerprint = _action_fingerprint(target.target_id, finding)
        existing = store.find_open_action(fingerprint)
        if existing is not None:
            actions.append(existing)
            continue
        now = datetime.now(UTC)
        action = OperationalAction(
            action_id=f"act-{uuid4().hex[:12]}",
            fingerprint=fingerprint,
            target_id=target.target_id,
            finding_code=finding.code,
            severity=finding.severity,
            summary=finding.summary,
            source_run_id=run.run_id,
            created_at=now,
            updated_at=now,
        )
        store.save_action(action)
        actions.append(action)

    markdown_path = store.reports_dir / f"{run.run_id}.md"
    markdown_path.write_text(render_markdown(run, actions), encoding="utf-8")
    json_path = store.save_json_report(run)
    return run, actions, [markdown_path, json_path]
