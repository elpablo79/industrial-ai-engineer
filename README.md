# Industrial AI Engineer

Production-oriented end-to-end AI engineering platform for industrial anomaly detection, incident investigation, and AI-assisted maintenance diagnosis.

## Current milestone

**Milestone 0 — Project Foundation**

This repository currently provides only the development foundation:

- Python package layout (`src/industrial_ai`)
- Dependency management with `uv`
- Test, lint, format, and type-check tooling
- Pre-commit hooks
- Minimal Docker Compose skeleton
- Environment-based typed configuration

Application services (Kafka, databases, ML, LLMs, RAG, agents, FastAPI, dashboards, cloud) are intentionally out of scope for this milestone.

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
├── src/industrial_ai/   # Application package
├── tests/unit/          # Unit tests
├── docs/                # Architecture and design notes
├── scripts/             # Utility scripts (empty in M0)
├── pyproject.toml       # Project metadata and tool config
├── Makefile             # Developer shortcuts
└── docker-compose.yml   # Compose skeleton (no app services yet)
```

## License

MIT — see [LICENSE](LICENSE).
