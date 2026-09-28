"""CLI tests for ``python -m industrial_ai.simulator``."""

from __future__ import annotations

import json
from pathlib import Path

from industrial_ai.simulator.__main__ import main
from industrial_ai.simulator.models import TelemetryEvent


def test_cli_writes_jsonl(tmp_path: Path) -> None:
    out = tmp_path / "out.jsonl"
    exit_code = main(
        [
            "--machines",
            "2",
            "--duration",
            "3",
            "--interval",
            "1",
            "--seed",
            "7",
            "--output",
            str(out),
        ]
    )
    assert exit_code == 0
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 6
    for line in lines:
        TelemetryEvent.model_validate(json.loads(line))
