# Industrial AI Engineer

Production-oriented end-to-end AI engineering platform for industrial anomaly detection, incident investigation, and AI-assisted maintenance diagnosis.

## Current milestone

**Milestone 1 — Industrial Data Simulator**

The repository now includes a deterministic, configurable industrial telemetry simulator that emits validated JSONL events for multiple machines.

Still deferred: Kafka, databases, ML models, LLMs, RAG, agents, FastAPI, dashboards, and cloud deployment.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- GNU Make
- Docker / Docker Compose (optional at this stage)

## Development setup

```bash
# Clone the repository, then from the project root:
uv sync
make install   # sync deps + install pre-commit hooks
```

Copy environment defaults if needed:

```bash
cp .env.example .env
```

Verify the package imports:

```bash
uv run python -c "import industrial_ai; print(industrial_ai.__version__)"
```

## Industrial telemetry simulator

Generate synthetic multi-machine sensor streams (temperature, pressure, vibration, motor current, rpm, flow rate) with temporally coherent failure injection:

- `NORMAL`
- `BEARING_FAILURE`
- `OVERHEATING`
- `PRESSURE_LEAK`
- `MOTOR_OVERLOAD`
- `SENSOR_DRIFT`

```bash
# 10 machines, 300 seconds, deterministic seed → stdout JSONL
uv run python -m industrial_ai.simulator --machines 10 --duration 300 --seed 42

# Write to a file
uv run python -m industrial_ai.simulator \
  --machines 5 \
  --duration 60 \
  --interval 1 \
  --seed 42 \
  --failure-probability 0.002 \
  --output data/telemetry.jsonl
```

| Flag | Meaning |
|------|---------|
| `--machines` | Number of machines (`M001` …) |
| `--duration` | Simulation length in seconds |
| `--interval` | Sampling period in seconds |
| `--seed` | RNG seed for reproducible output |
| `--failure-probability` | Per-second chance a healthy machine starts a failure |
| `--failure-duration` | Seconds for a failure to reach full severity |
| `--output` / `-o` | JSONL destination (default: stdout) |

Example event:

```json
{
  "timestamp": "2026-01-01T00:00:00Z",
  "machine_id": "M001",
  "temperature": 71.4,
  "pressure": 4.8,
  "vibration": 2.3,
  "motor_current": 8.2,
  "rpm": 1450.0,
  "flow_rate": 102.4
}
```

## Commands

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies and pre-commit hooks |
| `make test` | Run the unit test suite |
| `make lint` | Run Ruff lint checks |
| `make format` | Format code with Ruff |
| `make typecheck` | Run mypy in strict mode |
| `make check` | Run lint, typecheck, and tests |

Equivalent `uv` invocations:

```bash
uv sync
uv run pytest
uv run ruff check src tests
uv run mypy
```

## Project layout

```text
industrial-ai-engineer/
├── src/industrial_ai/
│   ├── config.py              # App settings from environment
│   └── simulator/             # Milestone 1 telemetry simulator
├── tests/unit/
├── docs/
├── scripts/
├── pyproject.toml
├── Makefile
└── docker-compose.yml
```

## License

MIT — see [LICENSE](LICENSE).
