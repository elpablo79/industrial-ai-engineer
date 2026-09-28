"""Unit tests for telemetry event schema validation."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from industrial_ai.simulator.models import TelemetryEvent


def _valid_event(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "timestamp": datetime(2026, 1, 1, tzinfo=UTC),
        "machine_id": "M001",
        "temperature": 71.4,
        "pressure": 4.8,
        "vibration": 2.3,
        "motor_current": 8.2,
        "rpm": 1450.0,
        "flow_rate": 102.4,
    }
    payload.update(overrides)
    return payload


def test_telemetry_schema_accepts_valid_event() -> None:
    event = TelemetryEvent.model_validate(_valid_event())
    assert event.machine_id == "M001"
    assert event.temperature == pytest.approx(71.4)


def test_invalid_machine_id_rejected() -> None:
    with pytest.raises(ValidationError):
        TelemetryEvent.model_validate(_valid_event(machine_id="machine-1"))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("temperature", -100.0),
        ("temperature", 300.0),
        ("pressure", -1.0),
        ("pressure", 99.0),
        ("vibration", -0.1),
        ("vibration", 150.0),
        ("motor_current", -5.0),
        ("motor_current", 500.0),
        ("rpm", -10.0),
        ("rpm", 20000.0),
        ("flow_rate", -1.0),
        ("flow_rate", 5000.0),
    ],
)
def test_invalid_sensor_values_rejected(field: str, value: float) -> None:
    with pytest.raises(ValidationError):
        TelemetryEvent.model_validate(_valid_event(**{field: value}))


def test_json_serialization_roundtrip() -> None:
    event = TelemetryEvent.model_validate(_valid_event())
    line = event.to_jsonl()
    restored = TelemetryEvent.model_validate_json(line)
    assert restored == event
    assert '"machine_id":"M001"' in line
    assert "timestamp" in line
