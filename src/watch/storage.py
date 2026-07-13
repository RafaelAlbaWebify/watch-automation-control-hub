from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from watch.models import OperationalAction, WorkflowRun

ModelT = TypeVar("ModelT", bound=BaseModel)


class JsonStore:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.runs_dir = workspace / "runs"
        self.actions_dir = workspace / "actions"
        self.reports_dir = workspace / "reports"
        for directory in (self.runs_dir, self.actions_dir, self.reports_dir):
            directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _write(path: Path, model: BaseModel) -> None:
        path.write_text(model.model_dump_json(indent=2), encoding="utf-8")

    @staticmethod
    def _read(path: Path, model_type: type[ModelT]) -> ModelT:
        return model_type.model_validate_json(path.read_text(encoding="utf-8"))

    def save_run(self, run: WorkflowRun) -> Path:
        path = self.runs_dir / f"{run.run_id}.json"
        if path.exists():
            raise FileExistsError(f"immutable run already exists: {run.run_id}")
        self._write(path, run)
        return path

    def list_runs(self, target_id: str | None = None) -> list[WorkflowRun]:
        runs = [self._read(path, WorkflowRun) for path in self.runs_dir.glob("*.json")]
        if target_id is not None:
            runs = [run for run in runs if run.target_id == target_id]
        return sorted(runs, key=lambda run: run.started_at)

    def get_run(self, run_id: str) -> WorkflowRun | None:
        path = self.runs_dir / f"{run_id}.json"
        return self._read(path, WorkflowRun) if path.is_file() else None

    def latest_run(self, target_id: str) -> WorkflowRun | None:
        runs = self.list_runs(target_id)
        return runs[-1] if runs else None

    def save_action(self, action: OperationalAction) -> Path:
        path = self.actions_dir / f"{action.action_id}.json"
        self._write(path, action)
        return path

    def list_actions(self) -> list[OperationalAction]:
        actions = [
            self._read(path, OperationalAction)
            for path in self.actions_dir.glob("*.json")
        ]
        return sorted(actions, key=lambda action: action.created_at)

    def find_open_action(self, fingerprint: str) -> OperationalAction | None:
        for action in self.list_actions():
            if action.fingerprint == fingerprint and action.status.value != "resolved":
                return action
        return None

    def read_markdown_report(self, run_id: str) -> str | None:
        path = self.reports_dir / f"{run_id}.md"
        return path.read_text(encoding="utf-8") if path.is_file() else None

    def save_json_report(self, run: WorkflowRun) -> Path:
        path = self.reports_dir / f"{run.run_id}.json"
        payload = json.dumps(run.model_dump(mode="json"), indent=2)
        path.write_text(payload, encoding="utf-8")
        return path
