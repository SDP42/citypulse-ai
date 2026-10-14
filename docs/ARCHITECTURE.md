# Architecture (proposed — ADR-0001)

Modular monolith. Flow (blueprint p.5/135):

```
Sources / CSV / GeoJSON / synthetic fixtures
   -> source registry (licence status)
   -> immutable raw snapshot (hash)
   -> parse -> normalise -> quality gate -> quarantine
   -> canonical SQLite store (+ H3 / geometry)
   -> SQL metric layer | ML/NLP baselines | document KB (FTS5 [+embeddings])
   -> evidence bundle -> bounded agent / report draft -> human review -> export + audit
```

## Trust zones → code
| Zone | Dir | Rule |
|---|---|---|
| A Source intake | `api/citypulse/sources`, `ingest` | size-limited, no macros/paths/unbounded fetch |
| B Canonical data | `db`, `geo` | parameterised SQL only; no LLM writes |
| C Derived analysis | `analytics`, `ml`, `nlp` | versioned; inference labelled |
| D AI interface | `rag`, `agent`, `reports`, `providers` | retrieved text is untrusted; typed read-only tools; abstain/escalate |

## Traceability contract (every result)
`source → batch → observation → analysis_run → (model_run) → draft → review_event`. No public-facing result without scope, observation window, lineage, quality flags, evidence-vs-inference label. Enforced in `core/provenance.py`.

## Core tables (blueprint 126 / App. B)
`source_registry, ingestion_batch, raw_object_ref, observation, area, boundary_version, document, document_chunk, analysis_run, metric_result, duplicate_candidate, model_run, recommendation_draft, review_event, audit_event`.

## API catalogue (blueprint 129)
`GET /health · /sources · /sources/{id}/status · POST /imports/preview · POST /imports · GET /observations · /analytics/{summary,trends,hotspots} · /areas · /documents/search · POST /analysis-runs · GET /analysis-runs/{id} · POST /reports/drafts · POST /reports/{id}/review`
Plus (ours): `GET /lineage/{kind}/{id}` (powers Provenance X-ray) and `GET /agent/runs/{id}/stream` (SSE trace).
Consistent error shape `{code, message, correlation_id, fields?}`; bounded pagination; long jobs are stateful, not sync.

## Modes
`DATA_MODE=synthetic|real` (never mixed in one aggregate) · `NETWORK=off|allowlist` (default off) · `LLM_PROVIDER=none|ollama` (default none; remote not implemented).

## Performance (M1 Air)
Stream/chunk imports; cache aggregates; heavy work off request thread with progress + cancel; budgets recorded in Phase 11.
