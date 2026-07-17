from __future__ import annotations

import argparse
import re
from pathlib import Path


def sanitize_report(source: Path) -> str:
    text = source.read_text(encoding="utf-8")
    replacements = [
        (r"(?m)^- Run ID: `[^`]+`$", "- Run ID: `run-sanitized-live-example`"),
        (r"(?m)^- Started: .+$", "- Started: 2026-07-17T00:00:00+00:00"),
        (r"(?m)^- Finished: .+$", "- Finished: 2026-07-17T00:00:01+00:00"),
        (r"(?m)^- Previous run: `[^`]+`$", "- Previous run: `none`"),
        (r"(?m)^\| resolved_ips \| .*\|$", "| resolved_ips | [sanitized-public-address] |"),
        (r"`action-[^`]+`", "`action-sanitized`"),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    header = (
        "<!-- Generated from one explicitly approved, bounded, read-only live check "
        "against https://example.com. Dynamic identifiers, timestamps, and resolved "
        "addresses were sanitized before publication. -->\n\n"
    )
    return header + text.rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Sanitize a WATCH live Markdown report.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sanitized = sanitize_report(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(sanitized, encoding="utf-8")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
