from datetime import UTC, datetime
from pathlib import Path

import pytest

from watch.attempts import (
    MAX_ATTEMPTS,
    AttemptLimitReachedError,
    AttemptStatus,
    BoundedRetryService,
    attempt_id,
)
from watch.models import (
    IntervalSchedule,
    ObservationSet,
    OccurrenceStatus,
    ScheduleOccurrence,
    Target,
)
from watch.occurrences import OccurrenceExecutionBlockedError, execution_key
from watch.storage import JsonStore


class SuccessfulCollector:
    def collect(self, target: Target) -> ObservationSet:
        return ObservationSet(
            http_status=200,
            final_url=str(target.url),
            redirect_count=0,
            response_ms=50,
            tls_days_remaining=90,
            page_title="Recovered",
            resolved_ips=["93.184.216.34"],
        )


class FailedCollector:
    def collect(self, target: Target) -> ObservationSet:
        raise RuntimeError("upstream unavailable")


def _failed_workspace(tmp_path: Path) -> tuple[JsonStore, ScheduleOccurrence]:
    store = JsonStore(tmp_path)
    target = Target(
        target_id="retry-target",
        name="Retry Target",
        url="https://example.com",
    )
    schedule = IntervalSchedule(
        schedule_id="retry-hourly",
        target_id=target.target_id,
        start_at=datetime(2026, 7, 14, 7, 0, tzinfo=UTC),
        interval_minutes=60,
    )
    occurrence_at = datetime(2026, 7, 14, 8, 0, tzinfo=UTC)
    occurrence = ScheduleOccurrence(
        execution_key=execution_key(schedule.schedule_id, occurrence_at),
        schedule_id=schedule.schedule_id,
        target_id=target.target_id,
        occurrence_at=occurrence_at,
        claimed_at=datetime(2026, 7, 14, 8, 1, tzinfo=UTC),
        status=OccurrenceStatus.FAILED,
        execution_started_at=datetime(2026, 7, 14, 8, 2, tzinfo=UTC),
        finished_at=datetime(2026, 7, 14, 8, 3, tzinfo=UTC),
        error="RuntimeError: first failure",
    )
    store.create_target(target)
    store.create_schedule(schedule)
    store.claim_occurrence(occurrence)
    return store, occurrence


def test_attempt_id_is_stable_and_attempt_specific() -> None:
    key = "occ-0123456789abcdef01234567"

    assert attempt_id(key, 1) == attempt_id(key, 1)
    assert attempt_id(key, 1) != attempt_id(key, 2)
    assert attempt_id(key, 1).startswith("att-")
    assert len(attempt_id(key, 1)) == 28


def test_successful_retry_preserves_original_occurrence(tmp_path: Path) -> None:
    store, occurrence = _failed_workspace(tmp_path)
    occurrence_path = store.occurrences_dir / f"{occurrence.execution_key}.json"
    original_bytes = occurrence_path.read_bytes()
    service = BoundedRetryService(store, tmp_path, SuccessfulCollector())

    returned, retry_attempt, run, result = service.retry(
        occurrence.execution_key,
        "Operator confirmed a transient upstream failure.",
    )

    attempts = service.list_attempts(occurrence.execution_key)
    assert [item.attempt_number for item in attempts] == [1]
    assert retry_attempt.reason == "Operator confirmed a transient upstream failure."
    assert retry_attempt.status == AttemptStatus.COMPLETED
    assert run is not None
    assert retry_attempt.run_id == run.run_id
    assert result == "completed"
    assert returned == occurrence
    assert occurrence_path.read_bytes() == original_bytes


def test_failed_retry_preserves_original_failure_evidence(tmp_path: Path) -> None:
    store, occurrence = _failed_workspace(tmp_path)
    occurrence_path = store.occurrences_dir / f"{occurrence.execution_key}.json"
    original_bytes = occurrence_path.read_bytes()
    service = BoundedRetryService(store, tmp_path, FailedCollector())

    returned, retry_attempt, run, result = service.retry(
        occurrence.execution_key,
        "Operator approved one controlled retry.",
    )

    attempts = service.list_attempts(occurrence.execution_key)
    assert len(attempts) == 1
    assert retry_attempt.status == AttemptStatus.FAILED
    assert retry_attempt.error == "RuntimeError: upstream unavailable"
    assert run is None
    assert result == "failed"
    assert returned == occurrence
    assert occurrence_path.read_bytes() == original_bytes


def test_retry_is_allowed_only_for_failed_occurrences(tmp_path: Path) -> None:
    store, occurrence = _failed_workspace(tmp_path)
    completed = occurrence.model_copy(update={"status": OccurrenceStatus.COMPLETED})
    store.update_occurrence(completed)
    service = BoundedRetryService(store, tmp_path, SuccessfulCollector())

    with pytest.raises(
        OccurrenceExecutionBlockedError,
        match="only failed occurrences are eligible for retry",
    ):
        service.retry(occurrence.execution_key, "Must not execute.")


def test_retry_stops_at_three_operator_attempts(tmp_path: Path) -> None:
    store, occurrence = _failed_workspace(tmp_path)
    service = BoundedRetryService(store, tmp_path, FailedCollector())

    for expected_attempt in range(1, MAX_ATTEMPTS + 1):
        _, attempt, _, result = service.retry(
            occurrence.execution_key,
            f"Operator-approved retry {expected_attempt}.",
        )
        assert attempt.attempt_number == expected_attempt
        assert result == "failed"

    with pytest.raises(AttemptLimitReachedError, match="attempt limit reached"):
        service.retry(occurrence.execution_key, "Fourth retry must be blocked.")

    attempts = service.list_attempts(occurrence.execution_key)
    assert len(attempts) == MAX_ATTEMPTS
    assert [item.attempt_number for item in attempts] == [1, 2, 3]
