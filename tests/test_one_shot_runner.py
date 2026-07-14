from datetime import UTC, datetime
from pathlib import Path

import pytest

from watch.models import IntervalSchedule, ObservationSet, Target
from watch.one_shot_runner import OneShotDueRunner
from watch.storage import JsonStore


class SequenceCollector:
    def __init__(self, observations: list[ObservationSet]) -> None:
        self._observations = observations
        self.calls: list[str] = []

    def collect(self, target: Target) -> ObservationSet:
        self.calls.append(target.target_id)
        return self._observations[len(self.calls) - 1]


class FailingCollector:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def collect(self, target: Target) -> ObservationSet:
        self.calls.append(target.target_id)
        raise RuntimeError("collector unavailable")


def _seed(workspace: Path, count: int = 3) -> JsonStore:
    store = JsonStore(workspace)
    for index in range(count):
        target = Target(
            target_id=f"target-{index}",
            name=f"Target {index}",
            url="https://example.com",
        )
        store.create_target(target)
        store.create_schedule(
            IntervalSchedule(
                schedule_id=f"schedule-{index}",
                target_id=target.target_id,
                start_at=datetime(2026, 7, 14, 7, 0, tzinfo=UTC),
                interval_minutes=60,
            )
        )
    return store


def test_one_shot_runner_respects_deterministic_max_work(tmp_path: Path) -> None:
    store = _seed(tmp_path)
    collector = SequenceCollector(
        [
            ObservationSet(http_status=200, response_ms=50),
            ObservationSet(http_status=200, response_ms=60),
        ]
    )

    summary = OneShotDueRunner(store, tmp_path, collector).run(
        datetime(2026, 7, 14, 10, 20, tzinfo=UTC),
        max_work=2,
    )

    assert summary.planned == 3
    assert summary.ready == 3
    assert summary.selected == 2
    assert summary.completed == 2
    assert summary.partial == 0
    assert summary.failed == 0
    assert summary.skipped == 1
    assert [item.schedule_id for item in summary.results] == [
        "schedule-0",
        "schedule-1",
    ]
    assert collector.calls == ["target-0", "target-1"]
    assert all(item.claim_result == "claimed" for item in summary.results)
    assert all(item.execution_result == "completed" for item in summary.results)
    assert all(item.run_id is not None for item in summary.results)


def test_one_shot_runner_maps_partial_and_failed_results(tmp_path: Path) -> None:
    partial_workspace = tmp_path / "partial"
    partial_store = _seed(partial_workspace, count=1)
    partial_collector = SequenceCollector(
        [ObservationSet(errors=["HTTP_TIMEOUT: request exceeded configured timeout"])]
    )
    partial = OneShotDueRunner(
        partial_store,
        partial_workspace,
        partial_collector,
    ).run(datetime(2026, 7, 14, 10, 20, tzinfo=UTC), 1)
    assert partial.partial == 1
    assert partial.results[0].occurrence_status.value == "partial"
    assert partial.results[0].run_id is not None

    failed_workspace = tmp_path / "failed"
    failed_store = _seed(failed_workspace, count=1)
    failed_collector = FailingCollector()
    failed = OneShotDueRunner(
        failed_store,
        failed_workspace,
        failed_collector,
    ).run(datetime(2026, 7, 14, 10, 20, tzinfo=UTC), 1)
    assert failed.failed == 1
    assert failed.results[0].occurrence_status.value == "failed"
    assert failed.results[0].run_id is None
    assert failed.results[0].error == "RuntimeError: collector unavailable"


def test_repeated_invocation_does_not_recollect_finished_work(tmp_path: Path) -> None:
    store = _seed(tmp_path, count=1)
    collector = SequenceCollector([ObservationSet(http_status=200)])
    runner = OneShotDueRunner(store, tmp_path, collector)
    evaluated_at = datetime(2026, 7, 14, 10, 20, tzinfo=UTC)

    first = runner.run(evaluated_at, 1)
    second = runner.run(evaluated_at, 1)

    assert first.completed == 1
    assert second.ready == 0
    assert second.selected == 0
    assert second.results == []
    assert collector.calls == ["target-0"]


def test_one_shot_runner_skips_non_ready_plan_items(tmp_path: Path) -> None:
    store = _seed(tmp_path, count=1)
    target = store.get_target("target-0")
    assert target is not None
    store.update_target(target.model_copy(update={"enabled": False}))
    collector = SequenceCollector([])

    summary = OneShotDueRunner(store, tmp_path, collector).run(
        datetime(2026, 7, 14, 10, 20, tzinfo=UTC),
        1,
    )

    assert summary.planned == 1
    assert summary.ready == 0
    assert summary.selected == 0
    assert summary.skipped == 1
    assert summary.results == []
    assert collector.calls == []


@pytest.mark.parametrize("max_work", [0, 11])
def test_one_shot_runner_rejects_invalid_limits(tmp_path: Path, max_work: int) -> None:
    store = _seed(tmp_path, count=1)
    with pytest.raises(ValueError, match="between 1 and 10"):
        OneShotDueRunner(store, tmp_path, SequenceCollector([])).run(
            datetime(2026, 7, 14, 10, 20, tzinfo=UTC),
            max_work,
        )
