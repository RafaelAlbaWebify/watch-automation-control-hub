from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class RunStatus(StrEnum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class ActionStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class OccurrenceStatus(StrEnum):
    CLAIMED = "claimed"
    EXECUTING = "executing"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    MISSED = "missed"


class Target(BaseModel):
    target_id: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9-]*$")
    name: str = Field(min_length=1)
    url: HttpUrl
    enabled: bool = True
    tags: list[str] = Field(default_factory=list)
    expected_status_codes: list[int] = Field(default_factory=lambda: [200])
    timeout_seconds: int = Field(default=10, ge=1, le=60)

    @field_validator("expected_status_codes")
    @classmethod
    def validate_status_codes(cls, values: list[int]) -> list[int]:
        if not values:
            raise ValueError("at least one expected status code is required")
        if any(value < 100 or value > 599 for value in values):
            raise ValueError("status codes must be between 100 and 599")
        return sorted(set(values))


class TargetUpdate(BaseModel):
    name: str = Field(min_length=1)
    url: HttpUrl
    enabled: bool = True
    tags: list[str] = Field(default_factory=list)
    expected_status_codes: list[int] = Field(default_factory=lambda: [200])
    timeout_seconds: int = Field(default=10, ge=1, le=60)

    @field_validator("expected_status_codes")
    @classmethod
    def validate_status_codes(cls, values: list[int]) -> list[int]:
        return Target.validate_status_codes(values)

    def apply_to(self, target_id: str) -> Target:
        return Target(target_id=target_id, **self.model_dump())


class IntervalSchedule(BaseModel):
    schedule_id: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9-]*$")
    target_id: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9-]*$")
    enabled: bool = True
    start_at: datetime
    interval_minutes: int = Field(ge=5, le=10080)

    @field_validator("start_at")
    @classmethod
    def normalize_start_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("start_at must include a timezone")
        return value.astimezone(UTC)


class IntervalScheduleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    start_at: datetime
    interval_minutes: int = Field(ge=5, le=10080)

    @field_validator("start_at")
    @classmethod
    def normalize_start_at(cls, value: datetime) -> datetime:
        return IntervalSchedule.normalize_start_at(value)

    def apply_to(self, schedule_id: str, target_id: str) -> IntervalSchedule:
        return IntervalSchedule(
            schedule_id=schedule_id,
            target_id=target_id,
            **self.model_dump(),
        )


class ScheduleOccurrence(BaseModel):
    execution_key: str = Field(pattern=r"^occ-[a-f0-9]{24}$")
    schedule_id: str
    target_id: str
    occurrence_at: datetime
    claimed_at: datetime
    status: OccurrenceStatus = OccurrenceStatus.CLAIMED
    execution_started_at: datetime | None = None
    finished_at: datetime | None = None
    run_id: str | None = None
    error: str | None = Field(default=None, max_length=2000)

    @field_validator(
        "occurrence_at",
        "claimed_at",
        "execution_started_at",
        "finished_at",
    )
    @classmethod
    def normalize_timestamp(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurrence timestamps must include a timezone")
        return value.astimezone(UTC)


class ObservationSet(BaseModel):
    http_status: int | None = Field(default=None, ge=100, le=599)
    final_url: str | None = None
    redirect_count: int | None = Field(default=None, ge=0)
    redirect_chain: list[str] = Field(default_factory=list)
    response_ms: int | None = Field(default=None, ge=0)
    tls_days_remaining: int | None = None
    page_title: str | None = None
    resolved_ips: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class Finding(BaseModel):
    code: str
    severity: Severity
    summary: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    recommended_action: str
    limitations: list[str] = Field(default_factory=list)


class WorkflowRun(BaseModel):
    run_id: str
    target_id: str
    started_at: datetime
    finished_at: datetime
    status: RunStatus
    observations: ObservationSet
    findings: list[Finding]
    previous_run_id: str | None = None
    changed_fields: list[str] = Field(default_factory=list)

    @classmethod
    def now(cls) -> datetime:
        return datetime.now(UTC)


class OperationalAction(BaseModel):
    action_id: str
    fingerprint: str
    target_id: str
    finding_code: str
    severity: Severity
    summary: str
    source_run_id: str
    status: ActionStatus = ActionStatus.OPEN
    created_at: datetime
    updated_at: datetime
    resolution_note: str | None = None
