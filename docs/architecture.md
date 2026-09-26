# Architecture

## Purpose

Industrial AI Engineer is a production-oriented platform for:

- industrial anomaly detection
- incident investigation
- AI-assisted maintenance diagnosis

## Milestone 0 scope

Milestone 0 establishes the engineering foundation only:

| Layer | Status |
|-------|--------|
| Package layout (`src/industrial_ai`) | Present |
| Typed environment configuration | Present |
| Quality tooling (pytest, Ruff, mypy, pre-commit) | Present |
| Docker Compose skeleton | Present (no services) |
| Streaming, storage, ML, LLM, API, UI | Deferred |

## Planned high-level shape (future milestones)

```text
Sensors / OT data
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

This document will be expanded as each milestone lands concrete components. No runtime topology is active yet.
