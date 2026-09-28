"""Temporally coherent failure-mode effects on sensor baselines."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from industrial_ai.simulator.models import FailureMode


class DriftSensor(StrEnum):
    """Sensors that can be affected by SENSOR_DRIFT."""

    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    VIBRATION = "vibration"
    MOTOR_CURRENT = "motor_current"
    RPM = "rpm"
    FLOW_RATE = "flow_rate"


@dataclass(frozen=True, slots=True)
class SensorBaseline:
    """Nominal operating point for a single machine."""

    temperature: float
    pressure: float
    vibration: float
    motor_current: float
    rpm: float
    flow_rate: float


@dataclass(frozen=True, slots=True)
class SensorSample:
    """Instantaneous sensor values before validation."""

    temperature: float
    pressure: float
    vibration: float
    motor_current: float
    rpm: float
    flow_rate: float


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def apply_failure(
    baseline: SensorBaseline,
    mode: FailureMode,
    progress: float,
    *,
    drift_sensor: DriftSensor | None = None,
) -> SensorSample:
    """Apply failure effects for ``progress`` in ``[0, 1]`` to a baseline.

    Effects are temporally coherent: secondary symptoms appear only after
    ``progress`` crosses mode-specific thresholds.
    """
    p = _clamp(progress, 0.0, 1.0)
    temperature = baseline.temperature
    pressure = baseline.pressure
    vibration = baseline.vibration
    motor_current = baseline.motor_current
    rpm = baseline.rpm
    flow_rate = baseline.flow_rate

    if mode is FailureMode.NORMAL or p == 0.0:
        return SensorSample(
            temperature=temperature,
            pressure=pressure,
            vibration=vibration,
            motor_current=motor_current,
            rpm=rpm,
            flow_rate=flow_rate,
        )

    if mode is FailureMode.BEARING_FAILURE:
        # Vibration rises first; frictional heat and current follow later.
        vibration += 0.8 + 10.0 * (p**1.4)
        late = max(0.0, (p - 0.35) / 0.65)
        temperature += 18.0 * (late**1.2)
        motor_current += 2.5 * max(0.0, (p - 0.45) / 0.55)
        rpm -= 40.0 * late

    elif mode is FailureMode.OVERHEATING:
        temperature += 28.0 * p
        motor_current += 1.8 * p
        rpm -= 60.0 * max(0.0, (p - 0.25) / 0.75)
        flow_rate -= 5.0 * max(0.0, (p - 0.5) / 0.5)

    elif mode is FailureMode.PRESSURE_LEAK:
        pressure -= 2.8 * p
        flow_rate -= 25.0 * p
        # Pump may spin up slightly trying to compensate once leak is severe.
        rpm += 30.0 * max(0.0, (p - 0.4) / 0.6)
        motor_current += 0.8 * max(0.0, (p - 0.4) / 0.6)

    elif mode is FailureMode.MOTOR_OVERLOAD:
        motor_current += 6.0 * p
        rpm -= 120.0 * p
        temperature += 12.0 * max(0.0, (p - 0.2) / 0.8)
        vibration += 1.5 * max(0.0, (p - 0.5) / 0.5)

    elif mode is FailureMode.SENSOR_DRIFT:
        if drift_sensor is None:
            drift_sensor = DriftSensor.TEMPERATURE
        drift_amount = {
            DriftSensor.TEMPERATURE: 20.0,
            DriftSensor.PRESSURE: 1.5,
            DriftSensor.VIBRATION: 4.0,
            DriftSensor.MOTOR_CURRENT: 3.0,
            DriftSensor.RPM: 150.0,
            DriftSensor.FLOW_RATE: 30.0,
        }[drift_sensor]
        bias = drift_amount * p
        if drift_sensor is DriftSensor.TEMPERATURE:
            temperature += bias
        elif drift_sensor is DriftSensor.PRESSURE:
            pressure += bias
        elif drift_sensor is DriftSensor.VIBRATION:
            vibration += bias
        elif drift_sensor is DriftSensor.MOTOR_CURRENT:
            motor_current += bias
        elif drift_sensor is DriftSensor.RPM:
            rpm += bias
        else:
            flow_rate += bias

    return SensorSample(
        temperature=_clamp(temperature, -40.0, 250.0),
        pressure=_clamp(pressure, 0.0, 50.0),
        vibration=_clamp(vibration, 0.0, 100.0),
        motor_current=_clamp(motor_current, 0.0, 200.0),
        rpm=_clamp(rpm, 0.0, 10000.0),
        flow_rate=_clamp(flow_rate, 0.0, 1000.0),
    )


ACTIVE_FAILURE_MODES: tuple[FailureMode, ...] = (
    FailureMode.BEARING_FAILURE,
    FailureMode.OVERHEATING,
    FailureMode.PRESSURE_LEAK,
    FailureMode.MOTOR_OVERLOAD,
    FailureMode.SENSOR_DRIFT,
)
