# CityPulse AI

Local-first urban evidence workbench: source-grounded, traceable, human-reviewed. No paid runtime APIs.

> Status: **Phase 1–2 — scaffold + fixtures.** Backend tests pass (3); web builds. See [docs/WORKDONE.md](docs/WORKDONE.md).

```
api/        FastAPI backend (Python 3.12) — modular monolith, see docs/ARCHITECTURE.md
web/        Vite + React + TS + MapLibre/deck.gl frontend
data/       fixtures (committed) · raw/staging/db/models/tiles (gitignored)
docs/       PRODUCT · ARCHITECTURE · PHASES · ADRs · source register · blueprint PDF
scripts/    fixture generator, dev helpers
```

Start with [docs/PRODUCT.md](docs/PRODUCT.md) → [docs/PHASES.md](docs/PHASES.md) → [docs/decisions/ADR-0001-stack.md](docs/decisions/ADR-0001-stack.md).

Data is synthetic unless a verified source says otherwise. This is an analytical tool — not an emergency system and not official civic guidance.

## Docs index
[PHASES](docs/PHASES.md) · [WORKFLOW](docs/WORKFLOW.md) · [WORKDONE](docs/WORKDONE.md) · [ARCHITECTURE](docs/ARCHITECTURE.md) · [DESIGN](docs/DESIGN.md) · [TESTING](docs/TESTING.md) · [SECURITY](docs/SECURITY.md) · [DATA_POLICY](docs/DATA_POLICY.md) · [LEARNING](docs/LEARNING.md) · [source register](docs/data-source-register.md)

```bash
make setup && make fixtures && make dev   # API :8000, web :5173
```
