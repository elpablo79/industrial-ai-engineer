"""Unit tests for machine ID helpers and simulator configuration."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from industrial_ai.simulator.configuration import SimulatorConfig
from industrial_ai.simulator.generator import generate_machine_ids, machine_id_for_index


def test_machine_id_generation() -> None:
    assert machine_id_for_index(1) == "M001"
    assert machine_id_for_index(10) == "M010"
    assert machine_id_for_index(100) == "M100"
    assert generate_machine_ids(3) == ["M001", "M002", "M003"]


def test_machine_id_rejects_non_positive_index() -> None:
    with pytest.raises(ValueError, match="machine index"):
        machine_id_for_index(0)


def test_generate_machine_ids_rejects_empty() -> None:
    with pytest.raises(ValueError, match="n_machines"):
        generate_machine_ids(0)


def test_simulator_config_defaults() -> None:
    config = SimulatorConfig()
    assert config.n_machines == 5
    assert config.duration_seconds == 60.0
    assert config.sampling_interval_seconds == 1.0
    assert config.seed is None
    assert 0.0 <= config.failure_probability <= 1.0


def test_simulator_config_aliases() -> None:
    config = SimulatorConfig.model_validate(
        {"machines": 10, "duration": 300, "interval": 2.0, "seed": 42}
    )
    assert config.n_machines == 10
    assert config.duration_seconds == 300.0
    assert config.sampling_interval_seconds == 2.0
    assert config.n_steps == 150


def test_simulator_config_rejects_invalid() -> None:
    with pytest.raises(ValidationError):
        SimulatorConfig(n_machines=0)
    with pytest.raises(ValidationError):
        SimulatorConfig(failure_probability=1.5)
    with pytest.raises(ValidationError):
        SimulatorConfig(duration_seconds=-1)
