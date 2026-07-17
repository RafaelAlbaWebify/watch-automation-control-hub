from __future__ import annotations

import re
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReadinessReport:
    project: str
    version: str
    automated_ready: bool
    automated_blockers: list[str]
    manual_blockers: list[str]
    required_files_checked: int
    required_commands_checked: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


REQUIRED_FILES = (
    "README.md",
    "WATCH.ps1",
    "pyproject.toml",
    "src/watch/cli.py",
    "src/watch/webapp.py",
    "src/watch/runner.py",
    "scripts/setup.ps1",
    "scripts/verify.ps1",
    "scripts/export-review.ps1",
    "scripts/task-scheduler.ps1",
    "scripts/invoke-scheduled-run.ps1",
    "docs/roadmap.md",
    "docs/safety-boundaries.md",
    "docs/windows-task-scheduler.md",
    ".github/workflows/ci.yml",
)

REQUIRED_COMMANDS = (
    "setup",
    "verify",
    "demo",
    "export",
    "api",
    "plan",
    "run-once",
    "task-plan",
    "task-install",
    "task-verify",
    "task-uninstall",
    "task-rollback",
)

ALLOWED_PRE_V1_MANUAL_ITEM = (
    "Add a sanitized committed example produced by an explicitly approved live run"
)


def _unchecked_items(markdown: str) -> list[str]:
    return [
        match.group(1).strip()
        for match in re.finditer(r"^- \[ \] (.+)$", markdown, flags=re.MULTILINE)
    ]


def build_readiness_report(root: Path) -> ReadinessReport:
    root = root.resolve()
    automated_blockers: list[str] = []

    for relative_path in REQUIRED_FILES:
        if not (root / relative_path).is_file():
            automated_blockers.append(f"missing required file: {relative_path}")

    pyproject_path = root / "pyproject.toml"
    version = "unknown"
    if pyproject_path.is_file():
        with pyproject_path.open("rb") as file:
            project = tomllib.load(file).get("project", {})
        version_value = project.get("version")
        if isinstance(version_value, str) and version_value.strip():
            version = version_value.strip()
        else:
            automated_blockers.append("project version is missing")

    watch_script = root / "WATCH.ps1"
    watch_text = watch_script.read_text(encoding="utf-8") if watch_script.is_file() else ""
    for command in REQUIRED_COMMANDS:
        if f'"{command}"' not in watch_text:
            automated_blockers.append(f"WATCH.ps1 command missing: {command}")

    roadmap_path = root / "docs/roadmap.md"
    manual_blockers: list[str] = []
    if roadmap_path.is_file():
        roadmap = roadmap_path.read_text(encoding="utf-8")
        before_v1, separator, v1_and_after = roadmap.partition("## V1 readiness review")
        if not separator:
            automated_blockers.append("V1 readiness review section is missing")
            v1_and_after = ""
        for item in _unchecked_items(before_v1):
            if item == ALLOWED_PRE_V1_MANUAL_ITEM:
                manual_blockers.append(item)
            else:
                automated_blockers.append(f"incomplete automated roadmap item: {item}")
        manual_blockers.extend(_unchecked_items(v1_and_after))

    return ReadinessReport(
        project="WATCH",
        version=version,
        automated_ready=not automated_blockers,
        automated_blockers=automated_blockers,
        manual_blockers=list(dict.fromkeys(manual_blockers)),
        required_files_checked=len(REQUIRED_FILES),
        required_commands_checked=len(REQUIRED_COMMANDS),
    )


def render_readiness_markdown(report: ReadinessReport) -> str:
    automated_status = "PASS" if report.automated_ready else "BLOCKED"
    lines = [
        "# WATCH V1 readiness report",
        "",
        f"- Project: **{report.project}**",
        f"- Version: **{report.version}**",
        f"- Automated readiness: **{automated_status}**",
        f"- Required files checked: **{report.required_files_checked}**",
        f"- Required commands checked: **{report.required_commands_checked}**",
        "",
        "## Automated blockers",
        "",
    ]
    if report.automated_blockers:
        lines.extend(f"- {item}" for item in report.automated_blockers)
    else:
        lines.append("- None.")
    lines.extend(["", "## Manual blockers", ""])
    if report.manual_blockers:
        lines.extend(f"- {item}" for item in report.manual_blockers)
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Automated readiness confirms repository structure, command exposure, version metadata, and completed implementation roadmap items. Manual blockers require an approved live target, the intended Windows workstation, human review, or a release decision and are never marked complete by CI.",
            "",
        ]
    )
    return "\n".join(lines)
