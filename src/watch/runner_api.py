from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel, field_validator

from watch.occurrences import normalize_evaluation_time
from watch.runner import DuePlanItem, DueWorkPlanner
from watch.storage import JsonStore


class DuePlanRequest(BaseModel):
    evaluated_at: datetime

    @field_validator("evaluated_at")
    @classmethod
    def validate_evaluated_at(cls, value: datetime) -> datetime:
        return normalize_evaluation_time(value)


def mount_runner_routes(app: FastAPI, store: JsonStore) -> None:
    planner = DueWorkPlanner(store)

    @app.post("/api/runner/plan", response_model=list[DuePlanItem])
    def plan_due_work(request: DuePlanRequest) -> list[DuePlanItem]:
        return planner.plan(request.evaluated_at)
