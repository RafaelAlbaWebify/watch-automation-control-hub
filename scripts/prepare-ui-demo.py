from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from watch.models import ObservationSet, Target
from watch.storage import JsonStore
from watch.targets import TargetService
from watch.workflow import execute_supplied_observations


def prepare(workspace: Path) -> None:
    if workspace.exists():
        shutil.rmtree(workspace)

    store = JsonStore(workspace)
    targets = TargetService(store)

    healthy = Target(
        target_id="healthy-demo",
        name="Healthy public demo",
        url="https://example.com",
        tags=["portfolio", "healthy"],
    )
    degraded = Target(
        target_id="degraded-demo",
        name="Degraded public demo",
        url="https://example.org",
        tags=["portfolio", "degraded"],
    )
    disabled = Target(
        target_id="disabled-demo",
        name="Disabled public demo",
        url="https://example.net",
        enabled=False,
        tags=["portfolio", "disabled"],
    )

    for target in (healthy, degraded, disabled):
        targets.create(target)

    execute_supplied_observations(
        healthy,
        ObservationSet(
            http_status=200,
            final_url="https://example.com/",
            response_ms=180,
            tls_days_remaining=120,
            page_title="Example Domain",
            resolved_ips=["93.184.216.34"],
        ),
        workspace,
    )
    execute_supplied_observations(
        degraded,
        ObservationSet(
            http_status=503,
            final_url="https://example.org/",
            response_ms=2450,
            tls_days_remaining=12,
            page_title="Service unavailable",
            resolved_ips=["93.184.216.34"],
        ),
        workspace,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare deterministic WATCH UI evidence.")
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.workspace.resolve())


if __name__ == "__main__":
    main()
