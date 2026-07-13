from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from watch.models import ObservationSet, Target
from watch.workflow import execute_supplied_observations

app = typer.Typer(no_args_is_help=True, help="WATCH automation-control workbench.")


@app.command()
def demo(
    workspace: Annotated[Path, typer.Option(help="Directory for generated run, action, and report evidence.")] = Path(".watch-data"),
) -> None:
    sample_path = Path("samples/demo-input.json")
    if not sample_path.exists():
        raise typer.BadParameter(f"sample file not found: {sample_path}")
    payload = json.loads(sample_path.read_text(encoding="utf-8"))
    target = Target.model_validate(payload["target"])
    observations = ObservationSet.model_validate(payload["observations"])
    run, actions, reports = execute_supplied_observations(target=target, observations=observations, workspace=workspace)
    typer.echo("WATCH DEMO PASS")
    typer.echo(f"Run: {run.run_id}")
    typer.echo(f"Status: {run.status.value}")
    typer.echo(f"Findings: {len(run.findings)}")
    typer.echo(f"Actions returned: {len(actions)}")
    for report in reports:
        typer.echo(f"Report: {report}")


if __name__ == "__main__":
    app()
