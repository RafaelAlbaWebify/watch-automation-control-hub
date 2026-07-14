from __future__ import annotations

import argparse
import shutil
from datetime import UTC, datetime
from pathlib import Path

from watch.attempts import AttemptStatus, AttemptStore, ExecutionAttempt, attempt_id
from watch.models import IntervalSchedule, ObservationSet, OccurrenceStatus, Target
from watch.occurrences import OccurrenceService
from watch.schedules import ScheduleService
from watch.storage import JsonStore
from watch.targets import TargetService
from watch.workflow import execute_supplied_observations


def prepare(workspace: Path) -> None:
    if workspace.exists():
        shutil.rmtree(workspace)

    store = JsonStore(workspace)
    targets = TargetService(store)

    healthy = Target(
        target_id="healthy-demo",
        name="Healthy public demo",
        url="https://example.com",
        tags=["portfolio", "healthy"],
    )
    degraded = Target(
        target_id="degraded-demo",
        name="Degraded public demo",
        url="https://example.org",
        tags=["portfolio", "degraded"],
    )
    disabled = Target(
        target_id="disabled-demo",
        name="Disabled public demo",
        url="https://example.net",
        enabled=False,
        tags=["portfolio", "disabled"],
    )

    for target in (healthy, degraded, disabled):
        targets.create(target)

    execute_supplied_observations(
        healthy,
        ObservationSet(
            http_status=200,
            final_url="https://example.com/",
            response_ms=180,
            tls_days_remaining=120,
            page_title="Example Domain",
            resolved_ips=["93.184.216.34"],
        ),
        workspace,
    )
    execute_supplied_observations(
        degraded,
        ObservationSet(
            http_status=503,
            final_url="https://example.org/",
            response_ms=2450,
            tls_days_remaining=12,
            page_title="Service unavailable",
            resolved_ips=["93.184.216.34"],
        ),
        workspace,
    )
    changed_run, _, _ = execute_supplied_observations(
        degraded,
        ObservationSet(
            http_status=200,
            final_url="https://example.org/",
            response_ms=310,
            tls_days_remaining=45,
            page_title="Recovered service",
            resolved_ips=["93.184.216.34"],
        ),
        workspace,
    )
    if not changed_run.previous_run_id or not changed_run.changed_fields:
        raise RuntimeError("expected deterministic previous-run change evidence")

    schedules = ScheduleService(store)
    schedules.create(
        IntervalSchedule(
            schedule_id="healthy-hourly",
            target_id=healthy.target_id,
            start_at=datetime(2026, 1, 1, tzinfo=UTC),
            interval_minutes=60,
        )
    )
    schedules.create(
        IntervalSchedule(
            schedule_id="degraded-hourly",
            target_id=degraded.target_id,
            start_at=datetime(2026, 1, 1, tzinfo=UTC),
            interval_minutes=60,
        )
    )

    occurrence, result = OccurrenceService(store).evaluate(
        "degraded-hourly",
        datetime(2026, 1, 1, 1, 5, tzinfo=UTC),
    )
    if occurrence is None or result != "claimed":
        raise RuntimeError(f"expected a claimed occurrence, got {result}")
    stale = occurrence.model_copy(
        update={
            "status": OccurrenceStatus.EXECUTING,
            "execution_started_at": datetime(2026, 1, 1, 1, 6, tzinfo=UTC),
        }
    )
    store.update_occurrence(stale)

    attempts = AttemptStore(workspace)
    completed_attempt = ExecutionAttempt(
        attempt_id=attempt_id(occurrence.execution_key, 1),
        execution_key=occurrence.execution_key,
        attempt_number=1,
        reason="Operator confirmed the upstream dependency had recovered.",
        status=AttemptStatus.COMPLETED,
        started_at=datetime(2026, 1, 1, 2, 0, tzinfo=UTC),
        finished_at=datetime(2026, 1, 1, 2, 1, tzinfo=UTC),
        run_id=changed_run.run_id,
    )
    failed_attempt = ExecutionAttempt(
        attempt_id=attempt_id(occurrence.execution_key, 2),
        execution_key=occurrence.execution_key,
        attempt_number=2,
        reason="Operator requested a second controlled validation.",
        status=AttemptStatus.FAILED,
        started_at=datetime(2026, 1, 1, 3, 0, tzinfo=UTC),
        finished_at=datetime(2026, 1, 1, 3, 1, tzinfo=UTC),
        error="RuntimeError: deterministic retry evidence",
    )
    attempts.create(completed_attempt)
    attempts.create(failed_attempt)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare deterministic WATCH UI evidence.")
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.workspace.resolve())


if __name__ == "__main__":
    main()
