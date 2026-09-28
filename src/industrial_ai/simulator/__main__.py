"""CLI entry point: ``python -m industrial_ai.simulator``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from industrial_ai.simulator.configuration import SimulatorConfig
from industrial_ai.simulator.generator import TelemetrySimulator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m industrial_ai.simulator",
        description="Generate synthetic industrial telemetry as JSON Lines.",
    )
    parser.add_argument(
        "--machines",
        type=int,
        default=5,
        help="Number of machines to simulate (default: 5).",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=60.0,
        help="Simulation duration in seconds (default: 60).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Sampling interval in seconds (default: 1).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for deterministic output.",
    )
    parser.add_argument(
        "--failure-probability",
        type=float,
        default=0.002,
        dest="failure_probability",
        help="Per-second probability a healthy machine starts a failure.",
    )
    parser.add_argument(
        "--failure-duration",
        type=float,
        default=120.0,
        dest="failure_duration_seconds",
        help="Seconds for a failure to reach full severity (default: 120).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output JSONL path (default: stdout).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = SimulatorConfig.model_validate(
        {
            "machines": args.machines,
            "duration": args.duration,
            "interval": args.interval,
            "seed": args.seed,
            "failure_probability": args.failure_probability,
            "failure_duration_seconds": args.failure_duration_seconds,
            "output_path": args.output,
        }
    )
    simulator = TelemetrySimulator(config)
    count = simulator.write_jsonl()
    if args.output is not None:
        print(f"Wrote {count} events to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
