from __future__ import annotations

import argparse
import json
from pathlib import Path

from watch.readiness import build_readiness_report, render_readiness_markdown


def main() -> int:
    parser = argparse.ArgumentParser(description="Build WATCH V1 readiness evidence.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--markdown-out", type=Path, required=True)
    args = parser.parse_args()

    report = build_readiness_report(args.root)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report.to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_readiness_markdown(report),
        encoding="utf-8",
    )
    print(json.dumps(report.to_dict(), indent=2))
    return 0 if report.automated_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
