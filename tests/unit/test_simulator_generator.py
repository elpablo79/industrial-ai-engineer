"""Unit tests for deterministic generation and failure-mode behaviour."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

import pytest

from industrial_ai.simulator.configuration import SimulatorConfig
from industrial_ai.simulator.failure_modes import (
    DriftSensor,
    SensorBaseline,
    apply_failure,
)
from industrial_ai.simulator.generator import TelemetrySimulator
from industrial_ai.simulator.models import FailureMode, TelemetryEvent


def _config(**overrides: object) -> SimulatorConfig:
    payload: dict[str, object] = {
        "n_machines": 3,
        "duration_seconds": 20.0,
        "sampling_interval_seconds": 1.0,
        "seed": 42,
        "failure_probability": 0.0,
        "failure_duration_seconds": 10.0,
    }
    payload.update(overrides)
    return SimulatorConfig.model_validate(payload)


def test_deterministic_generation_with_seed() -> None:
    events_a = TelemetrySimulator(_config(seed=42)).collect()
    events_b = TelemetrySimulator(_config(seed=42)).collect()
    assert events_a == events_b
    assert len(events_a) == 3 * 20


def test_seed_reproducibility_across_runs() -> None:
    first = [e.model_dump(mode="json") for e in TelemetrySimulator(_config()).collect()]
    second = [
        e.model_dump(mode="json") for e in TelemetrySimulator(_config()).collect()
    ]
    assert first == second


def test_different_seeds_diverge() -> None:
    a = TelemetrySimulator(_config(seed=1)).collect()
    b = TelemetrySimulator(_config(seed=2)).collect()
    assert a != b


def test_normal_operation_stays_near_baseline() -> None:
    sim = TelemetrySimulator(_config(failure_probability=0.0, n_machines=1))
    events = sim.collect()
    assert all(isinstance(e, TelemetryEvent) for e in events)
    temps = [e.temperature for e in events]
    pressures = [e.pressure for e in events]
    assert 60.0 < mean(temps) < 80.0
    assert 3.5 < mean(pressures) < 6.0
    assert max(temps) - min(temps) < 5.0
    assert all(e.machine_id == "M001" for e in events)


def test_machine_ids_match_count() -> None:
    sim = TelemetrySimulator(_config(n_machines=10))
    assert sim.machine_ids == [f"M{i:03d}" for i in range(1, 11)]
    events = sim.collect()
    assert {e.machine_id for e in events} == set(sim.machine_ids)


def _forced_series(mode: FailureMode) -> list[TelemetryEvent]:
    config = _config(
        n_machines=1,
        duration_seconds=30.0,
        failure_duration_seconds=20.0,
        failure_probability=0.0,
    )
    return TelemetrySimulator(config, forced_modes={"M001": mode}).collect()


def test_bearing_failure_raises_vibration_then_temperature() -> None:
    events = _forced_series(FailureMode.BEARING_FAILURE)
    early = events[:5]
    late = events[-5:]
    assert mean(e.vibration for e in late) > mean(e.vibration for e in early) + 1.0
    assert mean(e.temperature for e in late) > mean(e.temperature for e in early)


def test_overheating_raises_temperature() -> None:
    events = _forced_series(FailureMode.OVERHEATING)
    early = events[:5]
    late = events[-5:]
    assert mean(e.temperature for e in late) > mean(e.temperature for e in early) + 5.0
    assert mean(e.motor_current for e in late) > mean(e.motor_current for e in early)


def test_pressure_leak_reduces_pressure_and_flow() -> None:
    events = _forced_series(FailureMode.PRESSURE_LEAK)
    early = events[:5]
    late = events[-5:]
    assert mean(e.pressure for e in late) < mean(e.pressure for e in early) - 0.5
    assert mean(e.flow_rate for e in late) < mean(e.flow_rate for e in early) - 5.0


def test_motor_overload_raises_current_and_drops_rpm() -> None:
    events = _forced_series(FailureMode.MOTOR_OVERLOAD)
    early = events[:5]
    late = events[-5:]
    assert (
        mean(e.motor_current for e in late) > mean(e.motor_current for e in early) + 1.0
    )
    assert mean(e.rpm for e in late) < mean(e.rpm for e in early) - 20.0


def test_sensor_drift_moves_at_least_one_channel() -> None:
    events = _forced_series(FailureMode.SENSOR_DRIFT)
    early = events[:3]
    late = events[-3:]
    deltas = {
        "temperature": abs(
            mean(e.temperature for e in late) - mean(e.temperature for e in early)
        ),
        "pressure": abs(
            mean(e.pressure for e in late) - mean(e.pressure for e in early)
        ),
        "vibration": abs(
            mean(e.vibration for e in late) - mean(e.vibration for e in early)
        ),
        "motor_current": abs(
            mean(e.motor_current for e in late) - mean(e.motor_current for e in early)
        ),
        "rpm": abs(mean(e.rpm for e in late) - mean(e.rpm for e in early)),
        "flow_rate": abs(
            mean(e.flow_rate for e in late) - mean(e.flow_rate for e in early)
        ),
    }
    assert max(deltas.values()) > 1.0


@pytest.mark.parametrize("mode", list(FailureMode))
def test_apply_failure_at_zero_progress_matches_baseline(mode: FailureMode) -> None:
    baseline = SensorBaseline(
        temperature=70.0,
        pressure=5.0,
        vibration=2.0,
        motor_current=8.0,
        rpm=1500.0,
        flow_rate=100.0,
    )
    sample = apply_failure(baseline, mode, 0.0, drift_sensor=DriftSensor.TEMPERATURE)
    assert sample.temperature == baseline.temperature
    assert sample.pressure == baseline.pressure
    assert sample.vibration == baseline.vibration
    assert sample.motor_current == baseline.motor_current
    assert sample.rpm == baseline.rpm
    assert sample.flow_rate == baseline.flow_rate


def test_jsonl_output_is_valid(tmp_path: Path) -> None:
    out = tmp_path / "telemetry.jsonl"
    sim = TelemetrySimulator(_config(n_machines=2, duration_seconds=5.0))
    count = sim.write_jsonl(out)
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert count == len(lines) == 10
    for line in lines:
        event = TelemetryEvent.model_validate(json.loads(line))
        assert event.machine_id in {"M001", "M002"}
