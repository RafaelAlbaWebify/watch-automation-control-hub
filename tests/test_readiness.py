from pathlib import Path

from watch.readiness import build_readiness_report, render_readiness_markdown


def test_current_repository_is_automatically_ready() -> None:
    root = Path(__file__).resolve().parents[1]
    report = build_readiness_report(root)

    assert report.automated_ready is True
    assert report.automated_blockers == []
    assert report.version == "0.3.0"
    assert (
        "Execute and verify Task Scheduler installation on the intended Windows workstation"
        in report.manual_blockers
    )
    assert (
        "Add a sanitized committed example produced by an explicitly approved live run"
        in report.manual_blockers
    )

    markdown = render_readiness_markdown(report)
    assert "Automated readiness: **PASS**" in markdown
    assert "## Manual blockers" in markdown


def test_missing_required_file_blocks_readiness(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/roadmap.md").write_text(
        "## V1 readiness review\n\n- [ ] Manual validation\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "watch"\nversion = "1.0.0"\n',
        encoding="utf-8",
    )

    report = build_readiness_report(tmp_path)

    assert report.automated_ready is False
    assert any(item.startswith("missing required file:") for item in report.automated_blockers)
    assert report.manual_blockers == ["Manual validation"]
