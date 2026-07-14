from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer

from watch.collectors import WebsiteCollector
from watch.models import ObservationSet, Target
from watch.runner import DueWorkPlanner
from watch.storage import JsonStore
from watch.workflow import execute_supplied_observations

app = typer.Typer(no_args_is_help=True, help="WATCH automation-control workbench.")


@app.command()
def demo(
    workspace: Annotated[
        Path,
        typer.Option(help="Directory for generated run, action, and report evidence."),
    ] = Path(".watch-data"),
) -> None:
    sample_path = Path("samples/demo-input.json")
    if not sample_path.exists():
        raise typer.BadParameter(f"sample file not found: {sample_path}")
    payload = json.loads(sample_path.read_text(encoding="utf-8"))
    target = Target.model_validate(payload["target"])
    observations = ObservationSet.model_validate(payload["observations"])
    run, actions, reports = execute_supplied_observations(
        target=target,
        observations=observations,
        workspace=workspace,
    )
    typer.echo("WATCH DEMO PASS")
    typer.echo(f"Run: {run.run_id}")
    typer.echo(f"Status: {run.status.value}")
    typer.echo(f"Findings: {len(run.findings)}")
    typer.echo(f"Actions returned: {len(actions)}")
    for report in reports:
        typer.echo(f"Report: {report}")


@app.command("plan-due")
def plan_due(
    evaluated_at: Annotated[
        str,
        typer.Option(help="Explicit timezone-aware ISO 8601 evaluation timestamp."),
    ],
    workspace: Annotated[
        Path,
        typer.Option(help="Existing WATCH workspace to inspect without modification."),
    ] = Path(".watch-data"),
) -> None:
    try:
        parsed = datetime.fromisoformat(evaluated_at.replace("Z", "+00:00"))
        plan = DueWorkPlanner(JsonStore(workspace)).plan(parsed)
    except ValueError as exc:
        raise typer.BadParameter(str(exc), param_hint="--evaluated-at") from exc

    typer.echo(
        json.dumps(
            [item.model_dump(mode="json") for item in plan],
            indent=2,
            sort_keys=True,
        )
    )


@app.command()
def collect(
    url: Annotated[str, typer.Argument(help="Explicit public HTTP or HTTPS target.")],
    workspace: Annotated[
        Path,
        typer.Option(help="Directory for generated run, action, and report evidence."),
    ] = Path(".watch-data"),
    timeout_seconds: Annotated[
        int,
        typer.Option(min=1, max=60, help="Per-target timeout in seconds."),
    ] = 10,
) -> None:
    target = Target.model_validate(
        {
            "target_id": "cli-target",
            "name": "CLI target",
            "url": url,
            "timeout_seconds": timeout_seconds,
        }
    )
    observations = WebsiteCollector().collect(target)
    run, actions, reports = execute_supplied_observations(
        target=target,
        observations=observations,
        workspace=workspace,
    )
    typer.echo("WATCH COLLECTION COMPLETE")
    typer.echo(f"Run: {run.run_id}")
    typer.echo(f"Status: {run.status.value}")
    typer.echo(f"HTTP status: {observations.http_status}")
    typer.echo(f"Errors: {len(observations.errors)}")
    typer.echo(f"Actions returned: {len(actions)}")
    for report in reports:
        typer.echo(f"Report: {report}")


if __name__ == "__main__":
    app()
