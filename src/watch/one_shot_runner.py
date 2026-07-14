from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field

from watch.models import ObservationSet, OccurrenceStatus, Target
from watch.occurrences import OccurrenceExecutionService, OccurrenceService
from watch.runner import DuePlanStatus, DueWorkPlanner
from watch.storage import JsonStore


class Collector(Protocol):
    def collect(self, target: Target) -> ObservationSet: ...


class DueRunItemResult(BaseModel):
    schedule_id: str
    execution_key: str
    claim_result: str
    execution_result: str
    occurrence_status: OccurrenceStatus
    run_id: str | None = None
    error: str | None = None


class DueRunSummary(BaseModel):
    evaluated_at: datetime
    max_work: int = Field(ge=1, le=10)
    planned: int = Field(ge=0)
    ready: int = Field(ge=0)
    selected: int = Field(ge=0)
    completed: int = Field(ge=0)
    partial: int = Field(ge=0)
    failed: int = Field(ge=0)
    skipped: int = Field(ge=0)
    results: list[DueRunItemResult]


class OneShotDueRunner:
    def __init__(
        self,
        store: JsonStore,
        workspace: Path,
        collector: Collector,
    ) -> None:
        self._planner = DueWorkPlanner(store)
        self._occurrences = OccurrenceService(store)
        self._execution = OccurrenceExecutionService(store, workspace, collector)

    def run(self, evaluated_at: datetime, max_work: int) -> DueRunSummary:
        if max_work < 1 or max_work > 10:
            raise ValueError("max_work must be between 1 and 10")

        plan = self._planner.plan(evaluated_at)
        ready = [item for item in plan if item.status == DuePlanStatus.READY_TO_CLAIM]
        selected = ready[:max_work]
        results: list[DueRunItemResult] = []

        for item in selected:
            occurrence, claim_result = self._occurrences.evaluate(
                item.schedule_id,
                item.evaluated_at,
            )
            if occurrence is None:
                continue
            executed, run, execution_result = self._execution.execute(
                occurrence.execution_key
            )
            results.append(
                DueRunItemResult(
                    schedule_id=item.schedule_id,
                    execution_key=occurrence.execution_key,
                    claim_result=claim_result,
                    execution_result=execution_result,
                    occurrence_status=executed.status,
                    run_id=run.run_id if run else executed.run_id,
                    error=executed.error,
                )
            )

        completed = sum(
            result.occurrence_status == OccurrenceStatus.COMPLETED for result in results
        )
        partial = sum(
            result.occurrence_status == OccurrenceStatus.PARTIAL for result in results
        )
        failed = sum(
            result.occurrence_status == OccurrenceStatus.FAILED for result in results
        )
        return DueRunSummary(
            evaluated_at=plan[0].evaluated_at if plan else evaluated_at,
            max_work=max_work,
            planned=len(plan),
            ready=len(ready),
            selected=len(selected),
            completed=completed,
            partial=partial,
            failed=failed,
            skipped=len(plan) - len(selected),
            results=results,
        )
