# CityPulse — Phases

Dependency order, not a calendar. Each phase = several 3–4 task **batches**; each batch ends with tests + evidence + **STOP for approval** (see [WORKFLOW.md](WORKFLOW.md)). Progress log lives in [WORKDONE.md](WORKDONE.md). What to study per phase: [LEARNING.md](LEARNING.md).

Legend: ☐ todo · ◐ in progress · ☑ done · 🔒 gated (needs explicit approval/verification before starting)

## Track A — Foundation MVP (from the blueprint, p.7)

| # | Phase | Build | Learn | Exit gate | Status |
|---|---|---|---|---|---|
| 0 | Repo audit | Greenfield confirmed | — | Recorded in WORKDONE | ☑ |
| 1 | Architecture & scaffold | ADR-0001, backend + web skeleton, source register, docs | FastAPI, Vite/React basics, ADRs | Stack approved by user | ☑ |
| 2 | Sources & fixtures | Source verification, deterministic synthetic fixtures with injected defects, data-mode badge | Open-data licences (GODL, ODbL), provenance | Offline repeatable fixture; every source status-labelled | ☑ |
| 3 | Schema & ingestion | Migrations, CSV/GeoJSON import preview, validation, quarantine, idempotency, formula-injection-safe export | SQLite/WAL, data quality dimensions, idempotency | Blank-DB + import tests pass; re-import adds 0 rows | ◐ (batch 1 done: CSV importer) |
| 4 | Deterministic analytics | Counts, trends, recurrence, related records, SQL metric layer, `/lineage` | SQL window fns, metric definitions, denominators | KPIs equal hand-computed fixture values | ☐ |
| 5 | Geospatial | CRS checks, boundary versions, place matching, H3 grid, map ↔ table parity | CRS/EPSG, H3, shapely, lon/lat order | Known coords & filters agree; map never disagrees with table | ☐ |
| 6 | ML baseline | One task, naive baseline, chronological holdout, model card | Time-series CV, leakage, calibration | Beats baseline or stays disabled/experimental | ☐ |
| 7 | NLP | Normalisation, Hindi/Marathi/code-mixed text, place candidates, duplicate candidates, PII redaction | Tokenisation, transliteration, similarity | Reviewed eval sample; privacy tests | ☐ |
| 8 | RAG | Small approved corpus (DMP/guidelines), chunking, FTS5 (+opt. embeddings), citations, abstention | Retrieval, BM25, embeddings, RAG eval | Citation + no-answer tests pass | ☐ |
| 9 | Bounded agent | Typed read-only tools, step limits, SSE trace, review queue | Tool-use design, prompt injection, OWASP API | Adversarial suite blocks unsafe SQL/URL/tool use | ☐ |
| 10 | UX & export | Overview, map, timeline, explorer, brief export | Data-viz perception, a11y | First-time user completes the core task unaided | ☐ |
| 11 | Hardening | Security review, licence/attribution, a11y, perf budgets (M1) | Threat modelling, profiling | Appendix-D release blockers closed | ☐ |
| 12 | Human pilot | One geography / problem / user; measured feedback | User research, usability testing | Go/no-go memo with honest results | ☐ 🔒 |
| 13 | Release gate | Runbook, known limits, reproducible setup, cost register | Release engineering | No unsupported claims | ☐ |

## Track B — The "crazy" layer (builds on Track A; each phase is optional and gated)

Rule: none of these may weaken a blueprint safety rule. If a feature can't be made honest, it doesn't ship.

| # | Phase | Build | Learn | Gate | Status |
|---|---|---|---|---|---|
| 14 | **Evidence Time Machine** | deck.gl 3D H3 hex map, time scrubber + playback, opacity = data quality, hatch = low-confidence location | deck.gl layers, WebGL perf, animation easing | 60 fps on M1 with fixture-scale data; table fallback identical | ☐ |
| 15 | **Provenance X-ray** | Click any number/sentence → animated lineage graph to raw rows & licence | Graph layout, d3, lineage modelling | Every KPI/brief claim opens a valid lineage; test enumerates all | ☐ |
| 16 | **City Pulse rhythm** | Per-area recurrence "heartbeat" strips; repeat-location cadence ≠ duplicates | Time-series viz, small multiples, seasonality | Metric def + min-sample threshold shown in UI | ☐ |
| 17 | **Rain layer (IMERG/IMD)** 🔒 | Gridded rainfall pulse at true ~10 km resolution, lag explorer with control analysis | Raster/NetCDF, xarray, spatial aggregation, spurious correlation | Resolution caveat enforced by test; control analysis present | ☐ |
| 18 | **Offline vector basemap** 🔒 | PMTiles from Geofabrik Mumbai clip, ODbL attribution | Vector tiles, tippecanoe/planetiler, PMTiles | Map works with network off; attribution visible | ☐ |
| 19 | **Glass-box Analyst v2** | Replayable agent timeline, step-by-step tool cards, "why I abstained" panel, diff of draft vs evidence | SSE/streaming, agent eval, deterministic replay | Replay reproduces trace; unsafe-tool rate 0 | ☐ |
| 20 | **Local LLM + embeddings** 🔒 | Ollama adapter, multilingual embeddings, model cards, licence check | Quantisation, M1 inference, embedding eval | Core path still works with provider off; no silent remote fallback | ☐ |
| 21 | **Multilingual + voice intake** | Hindi/Marathi UI strings, local speech-to-text for field notes (opt-in) | i18n, Whisper-class local STT, code-mixing | Eval on labelled sample; PII redaction before storage | ☐ 🔒 |
| 22 | **Counterfactual "what-if" lab** | Scenario sliders (e.g. drain-clearance timing) clearly labelled *simulation*, never a forecast claim | Causal inference limits, simulation hygiene | Every output carries SIMULATION label + assumptions list | ☐ |
| 23 | **Review workspace** | Local multi-reviewer queue, comments, accept/edit/reject with audit trail, brief versioning | Event sourcing-lite, diffing, RBAC | Audit trail reconstructs any brief | ☐ |
| 24 | **Brief with receipts** | PDF/HTML export where each claim has lineage ID + QR to rows | PDF generation, QR, reproducible builds | Rebuilding from IDs reproduces numbers | ☐ |
| 25 | **Eval Lab dashboard** | In-app benchmarks: geocoding precision, classifier F1, RAG recall/abstention, agent safety | MLOps-lite, metrics, calibration plots | Every ML/RAG feature has a visible score & model card | ☐ |
| 26 | **Offline PWA / field capture** | Installable PWA, offline queue, consented photo/location capture | Service workers, IndexedDB, privacy by design | Works in airplane mode; consent logged | ☐ 🔒 |
| 27 | **Connector SDK** | Adapter template + contract test kit so others add sources (Open311, CKAN, CSV feeds) | Plugin design, contract testing, SSRF defence | Fake connector passes same suite as real one | ☐ |
| 28 | **Public transparency page** | Read-only, aggregate-only embeddable widgets with data cards | Data cards, privacy thresholds (k-anonymity) | No row-level/PII leakage test passes | ☐ 🔒 |
| 29 | **Open data publishing** | Export derived datasets + data card + licence, DOI-ready | Data licensing, FAIR principles | Licence compatibility check automated | ☐ |
| 30 | **Federated multi-city** | Multiple pilots/areas with isolated sources & boundary versions | Multi-tenancy, schema versioning | Cross-city leakage test passes | ☐ 🔒 |
| 31 | **Official-channel bridge** 🔒 | Only with verified authorised Open311 access: *human-approved* draft hand-off | Open311, consent, abuse prevention | Explicit written authorisation; still draft-only by default | ☐ |

## Cross-cutting tracks (run alongside)
- **Design system** — see [DESIGN.md](DESIGN.md).
- **Testing & CI** — see [TESTING.md](TESTING.md).
- **Security & privacy** — see [SECURITY.md](SECURITY.md).
- **Data governance** — see [DATA_POLICY.md](DATA_POLICY.md).
- **Product/learning** — [PRODUCT.md](PRODUCT.md), [LEARNING.md](LEARNING.md).

## Next batch proposal (Phase 3, batch 2 → Phase 4 start)
1. GeoJSON import (points/boundaries) with CRS assumption shown, transactional accept-or-quarantine-whole-batch.
2. Boundary registry: load/validate user-supplied boundaries, boundary QA report (feature count, invalid geometries, gaps/overlaps, bbox).
3. Formula-safe CSV export of quarantine + observations (uses `neutralise_formula`).
4. Start Phase 4: `/analytics/summary` + `/analytics/trends` with SQL metric layer and `/lineage` for one KPI.
