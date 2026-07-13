from __future__ import annotations

from watch.models import Finding, ObservationSet, Severity, Target


def analyze(target: Target, observations: ObservationSet) -> list[Finding]:
    findings: list[Finding] = []

    if observations.errors:
        findings.append(
            Finding(
                code="CHECK_EXECUTION_ERROR",
                severity=Severity.CRITICAL,
                summary="One or more checks could not complete.",
                evidence={"errors": observations.errors},
                recommended_action=(
                    "Review the check errors and rerun after validating connectivity."
                ),
                limitations=[
                    "No root cause is inferred from an execution error."
                ],
            )
        )

    if (
        observations.http_status is not None
        and observations.http_status not in target.expected_status_codes
    ):
        findings.append(
            Finding(
                code="UNEXPECTED_HTTP_STATUS",
                severity=Severity.CRITICAL,
                summary=f"HTTP status {observations.http_status} was not expected.",
                evidence={
                    "observed": observations.http_status,
                    "expected": target.expected_status_codes,
                },
                recommended_action=(
                    "Validate availability and review recent application or "
                    "hosting changes."
                ),
                limitations=[
                    "A single public check does not prove the internal root cause."
                ],
            )
        )

    if observations.response_ms is not None and observations.response_ms >= 2000:
        findings.append(
            Finding(
                code="SLOW_RESPONSE",
                severity=Severity.WARNING,
                summary=f"Response time was {observations.response_ms} ms.",
                evidence={
                    "response_ms": observations.response_ms,
                    "threshold_ms": 2000,
                },
                recommended_action=(
                    "Repeat the check and compare hosting, application, and "
                    "network evidence."
                ),
            )
        )

    if (
        observations.tls_days_remaining is not None
        and observations.tls_days_remaining <= 30
    ):
        severity = (
            Severity.CRITICAL
            if observations.tls_days_remaining <= 7
            else Severity.WARNING
        )
        findings.append(
            Finding(
                code="TLS_EXPIRY_APPROACHING",
                severity=severity,
                summary=(
                    "TLS certificate has "
                    f"{observations.tls_days_remaining} days remaining."
                ),
                evidence={
                    "days_remaining": observations.tls_days_remaining,
                    "warning_threshold": 30,
                    "critical_threshold": 7,
                },
                recommended_action=(
                    "Confirm certificate ownership and renewal responsibility."
                ),
            )
        )

    if not findings:
        findings.append(
            Finding(
                code="NO_ACTIONABLE_FINDINGS",
                severity=Severity.INFO,
                summary="No configured threshold was breached.",
                evidence={},
                recommended_action="Continue scheduled observation.",
            )
        )

    return findings
