from __future__ import annotations

import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Response

from watch.models import OperationalAction, WorkflowRun
from watch.storage import JsonStore


def create_app(workspace: Path) -> FastAPI:
    store = JsonStore(workspace)
    app = FastAPI(
        title="WATCH Operator API",
        version="0.3.0",
        description="Read-only access to WATCH operational evidence.",
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": "read-only"}

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
