"""Configuration for the industrial telemetry simulator."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SimulatorConfig(BaseModel):
    """Runtime parameters for synthetic telemetry generation."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    n_machines: int = Field(default=5, ge=1, le=10_000, alias="machines")
    duration_seconds: float = Field(default=60.0, gt=0, alias="duration")
    sampling_interval_seconds: float = Field(default=1.0, gt=0, alias="interval")
    seed: int | None = None
    failure_probability: float = Field(
        default=0.002,
        ge=0.0,
        le=1.0,
        description="Per-second probability that a healthy machine starts a failure.",
    )
    failure_duration_seconds: float = Field(
        default=120.0,
        gt=0,
        description="Seconds for an injected failure to reach full severity.",
    )
    start_time: datetime = Field(
        default_factory=lambda: datetime(2026, 1, 1, tzinfo=UTC)
    )
    output_path: Path | None = None

    @field_validator("start_time")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @property
    def n_steps(self) -> int:
        """Number of sampling steps implied by duration and interval."""
        return max(1, int(self.duration_seconds / self.sampling_interval_seconds))
