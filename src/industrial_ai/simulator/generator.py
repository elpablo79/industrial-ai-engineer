"""Deterministic multi-machine industrial telemetry generator."""

from __future__ import annotations

import math
import random
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TextIO

from industrial_ai.simulator.configuration import SimulatorConfig
from industrial_ai.simulator.failure_modes import (
    ACTIVE_FAILURE_MODES,
    DriftSensor,
    SensorBaseline,
    apply_failure,
)
from industrial_ai.simulator.models import FailureMode, TelemetryEvent

# Noise scale relative to each sensor's typical operating magnitude.
_NOISE_SIGMA = {
    "temperature": 0.35,
    "pressure": 0.05,
    "vibration": 0.08,
    "motor_current": 0.12,
    "rpm": 4.0,
    "flow_rate": 0.8,
}

_DRIFT_SENSORS: tuple[DriftSensor, ...] = tuple(DriftSensor)


def machine_id_for_index(index: int) -> str:
    """Return a zero-padded machine identifier (``M001``, ``M002``, ...)."""
    if index < 1:
        msg = f"machine index must be >= 1, got {index}"
        raise ValueError(msg)
    return f"M{index:03d}"


def generate_machine_ids(n_machines: int) -> list[str]:
    """Generate ``n_machines`` sequential machine IDs starting at ``M001``."""
    if n_machines < 1:
        msg = f"n_machines must be >= 1, got {n_machines}"
        raise ValueError(msg)
    return [machine_id_for_index(i) for i in range(1, n_machines + 1)]


def _baseline_for_machine(machine_index: int, rng: random.Random) -> SensorBaseline:
    """Create a stable per-machine operating point with small inter-machine spread."""
    spread = ((machine_index * 17) % 10) / 10.0
    return SensorBaseline(
        temperature=68.0 + 4.0 * spread + rng.uniform(-1.0, 1.0),
        pressure=4.5 + 0.4 * spread + rng.uniform(-0.1, 0.1),
        vibration=2.0 + 0.3 * spread + rng.uniform(-0.1, 0.1),
        motor_current=7.5 + 0.8 * spread + rng.uniform(-0.2, 0.2),
        rpm=1450.0 + 20.0 * spread + rng.uniform(-5.0, 5.0),
        flow_rate=100.0 + 8.0 * spread + rng.uniform(-2.0, 2.0),
    )


@dataclass
class MachineState:
    """Mutable operating state for one simulated machine."""

    machine_id: str
    baseline: SensorBaseline
    mode: FailureMode = FailureMode.NORMAL
    progress: float = 0.0
    drift_sensor: DriftSensor | None = None
    _forced_mode: FailureMode | None = field(default=None, repr=False)


class TelemetrySimulator:
    """Generate temporally coherent multi-machine telemetry streams."""

    def __init__(
        self,
        config: SimulatorConfig,
        *,
        forced_modes: dict[str, FailureMode] | None = None,
    ) -> None:
        self.config = config
        self._rng = random.Random(config.seed)
        self._machines = self._init_machines(forced_modes or {})

    @property
    def machine_ids(self) -> list[str]:
        return [machine.machine_id for machine in self._machines]

    @property
    def machines(self) -> Sequence[MachineState]:
        return self._machines

    def _init_machines(
        self, forced_modes: dict[str, FailureMode]
    ) -> list[MachineState]:
        ids = generate_machine_ids(self.config.n_machines)
        machines: list[MachineState] = []
        for index, mid in enumerate(ids, start=1):
            baseline = _baseline_for_machine(index, self._rng)
            forced = forced_modes.get(mid)
            state = MachineState(
                machine_id=mid,
                baseline=baseline,
                mode=forced if forced is not None else FailureMode.NORMAL,
                progress=0.0 if forced is None else 0.0,
                drift_sensor=(
                    self._pick_drift_sensor()
                    if forced is FailureMode.SENSOR_DRIFT
                    else None
                ),
                _forced_mode=forced,
            )
            machines.append(state)
        return machines

    def generate(self) -> Iterator[TelemetryEvent]:
        """Yield telemetry events for the configured duration."""
        step_delta = timedelta(seconds=self.config.sampling_interval_seconds)
        current_time = self.config.start_time
        interval = self.config.sampling_interval_seconds

        for _ in range(self.config.n_steps):
            for machine in self._machines:
                self._advance_failure_state(machine, interval)
                yield self._sample(machine, current_time)
            current_time = current_time + step_delta

    def collect(self) -> list[TelemetryEvent]:
        """Materialize the full event stream."""
        return list(self.generate())

    def write_jsonl(self, destination: Path | TextIO | None = None) -> int:
        """Write events as JSON Lines. Returns the number of records written."""
        path = destination if destination is not None else self.config.output_path
        count = 0
        if path is None:
            import sys

            for event in self.generate():
                sys.stdout.write(event.to_jsonl() + "\n")
                count += 1
            return count

        if isinstance(path, Path):
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as handle:
                for event in self.generate():
                    handle.write(event.to_jsonl() + "\n")
                    count += 1
            return count

        for event in self.generate():
            path.write(event.to_jsonl() + "\n")
            count += 1
        return count

    def _advance_failure_state(self, machine: MachineState, interval: float) -> None:
        if machine._forced_mode is not None:
            # Forced modes progress monotonically for testability / demos.
            machine.mode = machine._forced_mode
            machine.progress = min(
                1.0,
                machine.progress + interval / self.config.failure_duration_seconds,
            )
            if (
                machine.mode is FailureMode.SENSOR_DRIFT
                and machine.drift_sensor is None
            ):
                machine.drift_sensor = self._pick_drift_sensor()
            return

        if machine.mode is FailureMode.NORMAL:
            # Convert per-second probability to per-interval Bernoulli trial.
            p_start = 1.0 - (1.0 - self.config.failure_probability) ** interval
            if self._rng.random() < p_start:
                machine.mode = self._rng.choice(ACTIVE_FAILURE_MODES)
                machine.progress = 0.0
                machine.drift_sensor = (
                    self._pick_drift_sensor()
                    if machine.mode is FailureMode.SENSOR_DRIFT
                    else None
                )
            return

        machine.progress = min(
            1.0,
            machine.progress + interval / self.config.failure_duration_seconds,
        )

    def _pick_drift_sensor(self) -> DriftSensor:
        return self._rng.choice(_DRIFT_SENSORS)

    def _sample(self, machine: MachineState, timestamp: datetime) -> TelemetryEvent:
        affected = apply_failure(
            machine.baseline,
            machine.mode,
            machine.progress,
            drift_sensor=machine.drift_sensor,
        )
        return TelemetryEvent(
            timestamp=timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=UTC),
            machine_id=machine.machine_id,
            temperature=self._noise(affected.temperature, "temperature"),
            pressure=self._noise(affected.pressure, "pressure"),
            vibration=self._noise(affected.vibration, "vibration"),
            motor_current=self._noise(affected.motor_current, "motor_current"),
            rpm=self._noise(affected.rpm, "rpm"),
            flow_rate=self._noise(affected.flow_rate, "flow_rate"),
        )

    def _noise(self, value: float, sensor: str) -> float:
        sigma = _NOISE_SIGMA[sensor]
        noisy = value + self._rng.gauss(0.0, sigma)
        # Keep values inside TelemetryEvent physical bounds after noise.
        bounds = {
            "temperature": (-40.0, 250.0),
            "pressure": (0.0, 50.0),
            "vibration": (0.0, 100.0),
            "motor_current": (0.0, 200.0),
            "rpm": (0.0, 10000.0),
            "flow_rate": (0.0, 1000.0),
        }
        low, high = bounds[sensor]
        if math.isnan(noisy) or math.isinf(noisy):
            return value
        return max(low, min(high, noisy))
