from __future__ import annotations

import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from watch.actions import ActionNotFoundError, ActionService, InvalidActionTransitionError
from watch.models import OperationalAction, WorkflowRun
from watch.storage import JsonStore


class ResolutionRequest(BaseModel):
    resolution_note: str = Field(min_length=1, max_length=2000)


def create_app(workspace: Path) -> FastAPI:
    store = JsonStore(workspace)
    actions = ActionService(store)
    app = FastAPI(
        title="WATCH Operator API",
        version="0.4.0",
        description="Local operator access to WATCH evidence and action state.",
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": "local-operator"}

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
