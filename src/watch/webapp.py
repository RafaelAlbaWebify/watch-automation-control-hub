from __future__ import annotations

from pathlib import Path

import uvicorn
from fastapi import FastAPI

from watch.api import Collector, configured_workspace
from watch.api import create_app as create_api_app
from watch.change_timeline import mount_change_timeline_routes
from watch.target_detail import mount_target_detail_routes
from watch.web import mount_web_routes


def create_app(workspace: Path, collector: Collector | None = None) -> FastAPI:
    app = create_api_app(workspace, collector)
    mount_web_routes(app, workspace)
    mount_change_timeline_routes(app, workspace)
    mount_target_detail_routes(app, workspace)
    return app


app = create_app(configured_workspace())


def main() -> None:
    uvicorn.run("watch.webapp:app", host="127.0.0.1", port=8000, reload=False)
