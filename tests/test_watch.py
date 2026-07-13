from pathlib import Path

import pytest
from pydantic import ValidationError

from watch.analysis import analyze
from watch.models import ObservationSet, Severity, Target
from watch.storage import JsonStore
from watch.workflow import execute_supplied_observations


def target() -> Target:
    return Target(
        target_id="demo-site",
        name="Demo",
        url="https://example.com",
    )


def test_target_validation() -> None:
    validated = Target(
        target_id="demo-site",
        name="Demo",
        url="https://example.com",
        expected_status_codes=[204, 200, 200],
    )
    assert validated.expected_status_codes == [200, 204]

    with pytest.raises(ValidationError):
        Target(
            target_id="Invalid ID",
            name="Demo",
            url="https://example.com",
        )


def test_analysis_creates_expected_findings() -> None:
    observations = ObservationSet(
        http_status=503,
        response_ms=2500,
        tls_days_remaining=5,
    )
    findings = analyze(target(), observations)

    assert {finding.code for finding in findings} == {
        "UNEXPECTED_HTTP_STATUS",
        "SLOW_RESPONSE",
        "TLS_EXPIRY_APPROACHING",
    }
    tls_finding = next(
        finding
        for finding in findings
        if finding.code == "TLS_EXPIRY_APPROACHING"
    )
    assert tls_finding.severity == Severity.CRITICAL


def test_workflow_persists_and_prevents_duplicate_actions(
    tmp_path: Path,
) -> None:
    observation = ObservationSet(http_status=503)
    first_run, first_actions, first_reports = execute_supplied_observations(
        target(),
        observation,
        tmp_path,
    )
    second_run, second_actions, _ = execute_supplied_observations(
        target(),
        observation,
        tmp_path,
    )
    store = JsonStore(tmp_path)

    assert all(path.exists() for path in first_reports)
    assert second_run.previous_run_id == first_run.run_id
    assert second_run.changed_fields == []
    assert len(store.list_actions()) == 1
    assert first_actions[0].action_id == second_actions[0].action_id


def test_workflow_detects_change(tmp_path: Path) -> None:
    execute_supplied_observations(
        target(),
        ObservationSet(http_status=200),
        tmp_path,
    )
    second_run, _, _ = execute_supplied_observations(
        target(),
        ObservationSet(http_status=503),
        tmp_path,
    )
    assert second_run.changed_fields == ["http_status"]
