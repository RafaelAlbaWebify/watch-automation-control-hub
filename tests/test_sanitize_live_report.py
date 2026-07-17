from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_sanitizer() -> object:
    script = Path(__file__).parents[1] / "scripts" / "sanitize-live-report.py"
    spec = importlib.util.spec_from_file_location("sanitize_live_report", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sanitizer_removes_dynamic_identifiers_timestamps_and_addresses(
    tmp_path: Path,
) -> None:
    source = tmp_path / "report.md"
    source.write_text(
        "# WATCH Operational Report\n\n"
        "- Run ID: `run-secret`\n"
        "- Started: 2026-07-17T16:00:00+00:00\n"
        "- Finished: 2026-07-17T16:00:01+00:00\n"
        "- Previous run: `run-old`\n\n"
        "| resolved_ips | ['93.184.216.34'] |\n"
        "- `action-secret` — **open** — example\n",
        encoding="utf-8",
    )
    module = _load_sanitizer()
    sanitized = module.sanitize_report(source)  # type: ignore[attr-defined]

    assert "run-secret" not in sanitized
    assert "run-old" not in sanitized
    assert "93.184.216.34" not in sanitized
    assert "action-secret" not in sanitized
    assert "run-sanitized-live-example" in sanitized
    assert "sanitized-public-address" in sanitized
    assert "explicitly approved" in sanitized
