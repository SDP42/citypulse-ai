# ADR-0001 — Technology stack

- **Status:** ACCEPTED 2026-10-14 (approved by product owner at the Phase 1 gate; greenfield repo, no audit constraints).
- **Amendment 2026-10-14:** added `python-multipart` (uploads) and `osmium` (pyosmium; OSM clipping, dev/script use only). `pip install -e .` hung in this environment, so deps are installed directly (see Makefile).
- **Date:** 2026-10-14
- **Drivers:** zero paid runtime APIs · runs from a clean checkout on a MacBook Air M1 (arm64, Python 3.12, Node 22 verified) · offline/fixture mode for the whole core path · traceable data lineage · a frontend memorable enough to demo.

## Decision

| Layer | Choice | Why | Rejected alternative |
|---|---|---|---|
| API | **Python 3.12 + FastAPI + Pydantic v2** | Typed contracts = the blueprint's "typed tool schemas"; best geo/ML/NLP ecosystem; async + SSE for agent traces | Node/NestJS (weaker geo/ML) |
| Store | **SQLite (WAL) + FTS5**, single file in `data/db/` | Zero-ops, transactional imports, built-in full-text search for RAG baseline, trivially read-only for the agent | PostGIS (server to run; justify only after measuring), DuckDB (revisit for heavy analytics) |
| Spatial | **shapely + pyproj + H3** (Python), GeoJSON on the wire | No spatial DB needed; H3 gives stable hex grid for recurrence; explicit CRS handling | GeoPandas as default (heavy install; allowed for offline notebooks only) |
| Migrations | Plain numbered `.sql` files + tiny runner | Blueprint requires blank-DB → upgrade tests; avoids ORM lock-in | Alembic/SQLAlchemy (add only if needed) |
| Local ML/NLP | **scikit-learn** baselines; **optional** sentence-transformers (multilingual MiniLM) | CPU-friendly; licences to be verified at use | Hosted embeddings (violates policy) |
| Local LLM | **Optional** Ollama adapter behind `providers/`; deterministic provider is the default | Core must work with no model | Any remote API (disabled by default, never silent fallback) |
| Web | **Vite + React 18 + TypeScript** | Fast on M1, no SSR needed for a local-first app | Next.js (server features unused) |
| Map | **MapLibre GL JS + deck.gl** | GPU hex extrusion, time-animated layers, arcs; open licences | Leaflet (can't do the signature visuals) |
| Basemap | **PMTiles** single file cut from a Geofabrik OSM extract; blank style + boundary GeoJSON fallback | Offline, no tile-server abuse (OSM tile policy), ODbL attribution shown | Public OSM tile URL as default |
| UI state/data | Zustand + TanStack Query; d3-scale/d3-shape for timelines | Small, boring, testable | Redux |
| Motion/styling | Tailwind CSS + Framer Motion | Speed of iteration for a design-led UI | — |
| Tests | pytest (+hypothesis for parsers/geometry), Vitest, Playwright (one E2E journey) | Matches blueprint's pyramid | — |
| Packaging | `uv` or venv + `pnpm`/`npm`; **no Docker required** | Blueprint 097 | Docker-first |

## Consequences
- Two processes in dev (`uvicorn`, `vite`), one `make dev` wrapper.
- No framework mandates leak into domain code: `analytics/`, `geo/`, `ingest/` are pure Python, testable against fixtures.
- Any later addition of a DB server, vector store, or agent library needs a new ADR + user approval (blueprint note 132).

## Review triggers
Data volume > ~5M observations · need for multi-user writes · measured hotspot query latency > budget · a verified pilot dataset that requires PostGIS features.
