"""Pydantic models for industrial telemetry events."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FailureMode(StrEnum):
    """Supported machine operating / failure modes."""

    NORMAL = "NORMAL"
    BEARING_FAILURE = "BEARING_FAILURE"
    OVERHEATING = "OVERHEATING"
    PRESSURE_LEAK = "PRESSURE_LEAK"
    MOTOR_OVERLOAD = "MOTOR_OVERLOAD"
    SENSOR_DRIFT = "SENSOR_DRIFT"


class TelemetryEvent(BaseModel):
    """Validated telemetry sample emitted by one machine."""

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    machine_id: str = Field(..., pattern=r"^M\d{3,}$")
    temperature: float = Field(..., description="Temperature in °C")
    pressure: float = Field(..., description="Pressure in bar")
    vibration: float = Field(..., description="Vibration in mm/s RMS")
    motor_current: float = Field(..., description="Motor current in A")
    rpm: float = Field(..., description="Rotational speed in rpm")
    flow_rate: float = Field(..., description="Process flow rate in L/min")

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, value: float) -> float:
        if not -40.0 <= value <= 250.0:
            msg = f"temperature out of physical range: {value}"
            raise ValueError(msg)
        return value

    @field_validator("pressure")
    @classmethod
    def validate_pressure(cls, value: float) -> float:
        if not 0.0 <= value <= 50.0:
            msg = f"pressure out of physical range: {value}"
            raise ValueError(msg)
        return value

    @field_validator("vibration")
    @classmethod
    def validate_vibration(cls, value: float) -> float:
        if not 0.0 <= value <= 100.0:
            msg = f"vibration out of physical range: {value}"
            raise ValueError(msg)
        return value

    @field_validator("motor_current")
    @classmethod
    def validate_motor_current(cls, value: float) -> float:
        if not 0.0 <= value <= 200.0:
            msg = f"motor_current out of physical range: {value}"
            raise ValueError(msg)
        return value

    @field_validator("rpm")
    @classmethod
    def validate_rpm(cls, value: float) -> float:
        if not 0.0 <= value <= 10000.0:
            msg = f"rpm out of physical range: {value}"
            raise ValueError(msg)
        return value

    @field_validator("flow_rate")
    @classmethod
    def validate_flow_rate(cls, value: float) -> float:
        if not 0.0 <= value <= 1000.0:
            msg = f"flow_rate out of physical range: {value}"
            raise ValueError(msg)
        return value

    def to_jsonl(self) -> str:
        """Serialize as a single JSON Lines record."""
        return self.model_dump_json()
