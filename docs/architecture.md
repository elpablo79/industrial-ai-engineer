# Architecture

## Purpose

Industrial AI Engineer is a production-oriented platform for:

- industrial anomaly detection
- incident investigation
- AI-assisted maintenance diagnosis

## Current status

| Layer | Status |
|-------|--------|
| Package layout (`src/industrial_ai`) | Present |
| Typed environment configuration | Present |
| Quality tooling (pytest, Ruff, mypy, pre-commit) | Present |
| Docker Compose skeleton | Present (no services) |
| Industrial telemetry simulator | Present (Milestone 1) |
| Streaming, storage, ML, LLM, API, UI | Deferred |

## Milestone 1 — Industrial data simulator

```text
SimulatorConfig
       │
       ▼
TelemetrySimulator ──► MachineState[] (baseline + failure progress)
       │
       ├─ failure_modes.apply_failure(progress)
       │
       ▼
TelemetryEvent (Pydantic) ──► JSONL (stdout / file)
```

Design notes:

- Events are schema-validated with Pydantic before emission.
- Failures progress over time (`failure_duration_seconds`); secondary symptoms appear after mode-specific thresholds.
- A fixed `seed` yields bit-stable JSONL streams for tests and demos.
- Kafka and other consumers are intentionally out of scope until later milestones.

## Planned high-level shape (future milestones)

```text
Sensors / OT data  (← simulator stands in for this today)
       │
       ▼
  Ingestion / streaming
       │
       ▼
  Feature store / persistence
       │
       ├──────────────┐
       ▼              ▼
 Anomaly models   Investigation / RAG
       │              │
       └──────┬───────┘
              ▼
     Diagnosis / agents
              ▼
     Ops API / dashboards
```
