from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

import uvicorn
from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field

from watch.actions import ActionNotFoundError, ActionService, InvalidActionTransitionError
from watch.collectors import WebsiteCollector
from watch.models import (
    IntervalSchedule,
    IntervalScheduleUpdate,
    ObservationSet,
    OperationalAction,
    Target,
    TargetUpdate,
    WorkflowRun,
)
from watch.schedules import (
    ScheduleAlreadyExistsError,
    ScheduleNotFoundError,
    ScheduleService,
    ScheduleTargetNotFoundError,
)
from watch.storage import JsonStore
from watch.targets import TargetAlreadyExistsError, TargetNotFoundError, TargetService
from watch.workflow import execute_supplied_observations


class Collector(Protocol):
    def collect(self, target: Target) -> ObservationSet: ...


class ResolutionRequest(BaseModel):
    resolution_note: str = Field(min_length=1, max_length=2000)


class ExecutionResponse(BaseModel):
    run: WorkflowRun
    actions: list[OperationalAction]


def create_app(workspace: Path, collector: Collector | None = None) -> FastAPI:
    store = JsonStore(workspace)
    actions = ActionService(store)
    targets = TargetService(store)
    schedules = ScheduleService(store)
    website_collector: Collector = collector or WebsiteCollector()
    app = FastAPI(
        title="WATCH Operator API",
        version="0.7.0",
        description=(
            "Local operator access to WATCH targets, schedule configuration, "
            "execution, evidence, and actions."
        ),
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": "local-operator"}

    @app.get("/api/targets", response_model=list[Target])
    def list_targets() -> list[Target]:
        return targets.list()

    @app.get("/api/targets/{target_id}", response_model=Target)
    def get_target(target_id: str) -> Target:
        try:
            return targets.get(target_id)
        except TargetNotFoundError as exc:
            raise HTTPException(status_code=404, detail="target not found") from exc

    @app.post(
        "/api/targets",
        response_model=Target,
        status_code=status.HTTP_201_CREATED,
    )
    def create_target(target: Target) -> Target:
        try:
            return targets.create(target)
        except TargetAlreadyExistsError as exc:
            raise HTTPException(status_code=409, detail="target already exists") from exc

    @app.put("/api/targets/{target_id}", response_model=Target)
    def update_target(target_id: str, request: TargetUpdate) -> Target:
        try:
            return targets.update(target_id, request)
        except TargetNotFoundError as exc:
            raise HTTPException(status_code=404, detail="target not found") from exc

    @app.post(
        "/api/targets/{target_id}/runs",
        response_model=ExecutionResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def execute_target(target_id: str) -> ExecutionResponse:
        try:
            target = targets.get(target_id)
        except TargetNotFoundError as exc:
            raise HTTPException(status_code=404, detail="target not found") from exc
        if not target.enabled:
            raise HTTPException(status_code=409, detail="target is disabled")
        observations = website_collector.collect(target)
        run, run_actions, _ = execute_supplied_observations(
            target=target,
            observations=observations,
            workspace=workspace,
        )
        return ExecutionResponse(run=run, actions=run_actions)

    @app.get("/api/schedules", response_model=list[IntervalSchedule])
    def list_schedules() -> list[IntervalSchedule]:
        return schedules.list()

    @app.get("/api/schedules/{schedule_id}", response_model=IntervalSchedule)
    def get_schedule(schedule_id: str) -> IntervalSchedule:
        try:
            return schedules.get(schedule_id)
        except ScheduleNotFoundError as exc:
            raise HTTPException(status_code=404, detail="schedule not found") from exc

    @app.post(
        "/api/schedules",
        response_model=IntervalSchedule,
        status_code=status.HTTP_201_CREATED,
    )
    def create_schedule(schedule: IntervalSchedule) -> IntervalSchedule:
        try:
            return schedules.create(schedule)
        except ScheduleTargetNotFoundError as exc:
            raise HTTPException(status_code=404, detail="target not found") from exc
        except ScheduleAlreadyExistsError as exc:
            raise HTTPException(status_code=409, detail="schedule already exists") from exc

    @app.put("/api/schedules/{schedule_id}", response_model=IntervalSchedule)
    def update_schedule(
        schedule_id: str,
        request: IntervalScheduleUpdate,
    ) -> IntervalSchedule:
        try:
            return schedules.update(schedule_id, request)
        except ScheduleNotFoundError as exc:
            raise HTTPException(status_code=404, detail="schedule not found") from exc
        except ScheduleTargetNotFoundError as exc:
            raise HTTPException(status_code=404, detail="target not found") from exc

    @app.get("/api/runs", response_model=list[WorkflowRun])
    def list_runs() -> list[WorkflowRun]:
        return store.list_runs()

    @app.get("/api/runs/{run_id}", response_model=WorkflowRun)
    def get_run(run_id: str) -> WorkflowRun:
        run = store.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="run not found")
        return run

    @app.get("/api/actions", response_model=list[OperationalAction])
    def list_actions() -> list[OperationalAction]:
        return store.list_actions()

    @app.post("/api/actions/{action_id}/acknowledge", response_model=OperationalAction)
    def acknowledge_action(action_id: str) -> OperationalAction:
        try:
            return actions.acknowledge(action_id)
        except ActionNotFoundError as exc:
            raise HTTPException(status_code=404, detail="action not found") from exc
        except InvalidActionTransitionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/actions/{action_id}/resolve", response_model=OperationalAction)
    def resolve_action(action_id: str, request: ResolutionRequest) -> OperationalAction:
        try:
            return actions.resolve(action_id, request.resolution_note)
        except ActionNotFoundError as exc:
            raise HTTPException(status_code=404, detail="action not found") from exc
        except InvalidActionTransitionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/api/reports/{run_id}.md")
    def get_markdown_report(run_id: str) -> Response:
        report = store.read_markdown_report(run_id)
        if report is None:
            raise HTTPException(status_code=404, detail="report not found")
        return Response(content=report, media_type="text/markdown")

    return app


def configured_workspace() -> Path:
    return Path(os.environ.get("WATCH_WORKSPACE", ".watch-data")).resolve()


app = create_app(configured_workspace())


def main() -> None:
    uvicorn.run("watch.api:app", host="127.0.0.1", port=8000, reload=False)
