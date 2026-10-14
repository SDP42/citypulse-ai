# CityPulse — Phases and sub-phases

Dependency order, not a calendar. **Every phase is split into sub-phases (`N.M`).** A sub-phase is the unit of work: one small, approvable batch (1–3 tasks) with its own *done-when* test, evidence, and a **STOP for approval** (see [WORKFLOW.md](WORKFLOW.md)). A phase closes only when all of its sub-phases are PASS or explicitly deferred with a reason. Progress log: [WORKDONE.md](WORKDONE.md). Study notes: [LEARNING.md](LEARNING.md).

Legend: ☐ todo · ◐ in progress / partly done · ☑ done · 🔒 gated (needs your approval, a licence, or an account first) · ⏸ deferred

**Why sub-phases:** smaller steps mean each claim is tested against hand-calculated expectations before the next layer builds on it, failures are found where they're cheap to fix, and you approve small diffs.

---

## Track A — Foundation MVP (blueprint p.7)

### Phase 0 — Repo audit  ☑
| ID | Sub-phase | Done when | |
|---|---|---|---|
| 0.1 | Read-only audit | Empty repo + toolchain recorded | ☑ |

### Phase 1 — Architecture & scaffold  ◐
| ID | Sub-phase | Done when | |
|---|---|---|---|
| 1.1 | Blueprint digest & product charter | PRODUCT.md states wedge, non-goals, persona hypotheses | ☑ |
| 1.2 | Stack decision | ADR-0001 ACCEPTED | ☑ |
| 1.3 | Backend skeleton | FastAPI app, settings, error shape, migrations runner, tests | ☑ |
| 1.4 | Web skeleton | Vite/React/TS shell, data-mode badge, tests | ☑ |
| 1.5 | One-command dev run | `make dev` verified on a clean checkout | ☐ (NOT TESTED) |
| 1.6 | CI | GitHub Actions: backend tests, web typecheck/tests/build, offline smoke | ☐ |
| 1.7 | Repo hygiene | LICENSE, NOTICE, README, .gitignore audit | ☑ |

### Phase 2 — Sources & fixtures  ◐
| ID | Sub-phase | Done when | |
|---|---|---|---|
| 2.1 | Source matrix | Every candidate has status + evidence + limits | ☑ |
| 2.2 | Synthetic fixtures | Seeded generator with injected defects, labelled SYNTHETIC | ☑ |
| 2.3 | Open-licence data collection | Files hashed in MANIFEST with licence per file | ☑ |
| 2.4 | Derived layers | OSM → roads/waterways/places; wards ⨝ census | ☑ |
| 2.5 | Tests for data scripts | `extract_osm_mumbai`, `build_wards`, `build_manifest` covered on tiny fixtures | ☐ |
| 2.6 | Licence resolution for open candidates | IMD data policy read; MCGM excerpt or licence confirmed; data.gov.in searched manually (you) | ☐ 🔒 |
| 2.7 | Real-mode fixture DB | Real wards + population loaded in real mode; UI shows "no data", never zeros | ☐ |

### Phase 3 — Schema & ingestion  ◐
| ID | Sub-phase | Done when | |
|---|---|---|---|
| 3.1 | Core schema & migrations | Blank-DB and upgrade tests pass | ☑ |
| 3.2 | CSV importer | Preview, mapping, quarantine, idempotency, PII redaction | ☑ |
| 3.3 | GeoJSON point import | Same rules as CSV; cross-format dedupe | ☑ |
| 3.4 | Boundary registry | QA report, whole-file rejection, versioned activation | ☑ |
| 3.5 | Safe export | Formula-injection tests + mutation check | ☑ |
| 3.6 | Quarantine repair & reprocess | Corrected mapping reprocesses a batch with lineage to the original; stable IDs | ☐ |
| 3.7 | Privacy & retention controls | Name/address redaction, configurable retention of raw uploads and quarantine | ☐ |
| 3.8 | Excel (.xlsx) import | Formulas never executed; row/size limits; tests | ☐ (optional) |

### Phase 4 — Deterministic analytics  ◐
| ID | Sub-phase | Done when | |
|---|---|---|---|
| 4.1 | Metric layer + summary | Hand-calculated values match | ☑ |
| 4.2 | Trends | IST day/week buckets, gap handling, small-sample caveat | ☑ |
| 4.3 | Lineage API + Provenance X-ray v0 | Number ↔ rows verified; change detection | ☑ |
| 4.4 | Recurrence (repeat locations) | Distance+time rule, distinct from duplicates; edge cases (empty, single, ties, grid size) | ☐ |
| 4.5 | Related-record explorer | From a hotspot/run to related reports, with filters | ☐ |
| 4.6 | Denominator registry | Population/road-length sources with vintage; "not calculated" when missing | ☐ |
| 4.7 | Freshness & staleness | Per-source expected vs observed refresh; stale banner changes report caveats | ☐ |
| 4.8 | Metric dictionary | Every metric: formula, denominator, exclusions, limits (doc + tested against code) | ☐ |

### Phase 5 — Geospatial  ☐
| ID | Sub-phase | Done when | |
|---|---|---|---|
| 5.1 | CRS utilities | Local projected CRS (UTM 43N) distances; round-trip tests on control points | ☐ |
| 5.2 | H3 grid aggregation | Counts per hex equal hand-computed; resolution is a parameter | ☐ |
| 5.3 | Gazetteer from OSM places | Name/alias lookup with ambiguity preserved | ☐ |
| 5.4 | Reviewed geocoding | Candidate list, confidence, reviewer decision, revert; precision on a labelled sample | ☐ |
| 5.5 | Map ↔ table parity | Test: same filters give identical counts in map data and table | ☐ |
| 5.6 | Basic map view | MapLibre with boundaries + points, no tile dependency | ☐ |
| 5.7 | Location-precision indicator | Point vs area-level vs unresolved visibly distinct | ☐ |

### Phase 6 — ML baseline  ☐
| ID | Sub-phase | Done when | |
|---|---|---|---|
| 6.1 | Task selection | One task chosen with a written value hypothesis | ☐ |
| 6.2 | Chronological split harness | No random splits; cutoff stored | ☐ |
| 6.3 | Naive & seasonal-naive baselines | MAE/RMSE reported | ☐ |
| 6.4 | Feature pipeline with leakage tests | Test fails if a future value enters a feature | ☐ |
| 6.5 | Candidate model + calibration | Beats baseline on holdout, or stays disabled | ☐ |
| 6.6 | Model card & feature flag | Labelled experimental in UI | ☐ |

### Phase 7 — NLP  ☐
| ID | Sub-phase | Done when | |
|---|---|---|---|
| 7.1 | Text normalisation | Hindi/Marathi/code-mixed/transliterated samples handled | ☐ |
| 7.2 | Category classifier | Rules → TF-IDF baseline; macro-F1 + confusion matrix | ☐ |
| 7.3 | Place/entity extraction | Candidates only, never auto-assigned | ☐ |
| 7.4 | Duplicate candidates | Non-destructive, explains matched fields, review required | ☐ |
| 7.5 | PII redaction v2 | Names/addresses recall measured on a labelled sample | ☐ |
| 7.6 | Evaluation sample & labelling flow | Reviewed set versioned in repo (synthetic or cleared) | ☐ |

### Phase 8 — RAG  ☐
| ID | Sub-phase | Done when | |
|---|---|---|---|
| 8.1 | Document registry | Only licensed documents; hash, version, licence | ☐ 🔒 |
| 8.2 | Chunking with page refs | Citations resolve to page/section | ☐ |
| 8.3 | FTS5 retrieval | Recall@K on a small question set | ☐ |
| 8.4 | Cited answers + abstention | No-answer questions abstain | ☐ |
| 8.5 | Conflict & freshness handling | Conflicting/old sources are shown, not blended | ☐ |
| 8.6 | Prompt-injection tests | Injected instructions in documents change nothing | ☐ |
| 8.7 | Optional local embeddings | Behind provider interface; off by default | ☐ 🔒 |

### Phase 9 — Bounded agent  ☐
| ID | Sub-phase | Done when | |
|---|---|---|---|
| 9.1 | Typed tool contracts | Read-only allowlist; schemas validated | ☐ |
| 9.2 | Read-only data access | Parameterised metrics only; row/time limits; no arbitrary SQL | ☐ |
| 9.3 | State machine & step limits | Max steps, timeouts, cancellation | ☐ |
| 9.4 | Trace storage + SSE | Every step persisted and streamable | ☐ |
| 9.5 | Draft + review queue | Output is a draft; accept/edit/reject recorded | ☐ |
| 9.6 | Adversarial suite | Unsafe SQL/URL/path/tool calls blocked, logged | ☐ |
| 9.7 | Deterministic replay | A trace replays to the same draft with a fake model | ☐ |

### Phase 10 — UX & export  ☐
| ID | Sub-phase | Done when | |
|---|---|---|---|
| 10.1 | Global filters & navigation | One filter state drives every page | ☐ |
| 10.2 | Map & hotspots page | Parity with table | ☐ |
| 10.3 | Incident explorer | Raw rows, quality flags, lineage links | ☐ |
| 10.4 | Source & data-health page | Last attempt, record count, licence date, status | ☐ |
| 10.5 | Evidence library | Cited documents browsable | ☐ |
| 10.6 | Brief builder & export | Typed report object → HTML/PDF with caveats | ☐ |
| 10.7 | Accessibility pass | Keyboard, contrast, table alternatives, reduced motion | ☐ |
| 10.8 | Usability session | First-time user completes the core task unaided | ☐ 🔒 |

### Phase 11 — Hardening  ☐
| ID | Sub-phase | Done when | |
|---|---|---|---|
| 11.1 | Threat model | Trust-boundary diagram + threat register | ☐ |
| 11.2 | Security test suite | Upload, SQL, SSRF, path, header tests | ☐ |
| 11.3 | Licence & attribution audit | Attribution visible wherever data is shown | ☐ |
| 11.4 | Performance budgets | p95 latency/memory recorded on M1 | ☐ |
| 11.5 | Accessibility audit | WCAG checklist results | ☐ |
| 11.6 | Dependency & licence register | Every dependency + licence listed | ☐ |
| 11.7 | Backup / restore | Restore from backup reproduces results | ☐ |

### Phase 12 — Human pilot  ☐ 🔒
| ID | Sub-phase | Done when | |
|---|---|---|---|
| 12.1 | Partner & data agreement | Written permission, scope, retention | ☐ 🔒 |
| 12.2 | Pilot data intake | Real export imported, quality reported | ☐ 🔒 |
| 12.3 | Task-based sessions | ≥5 interviews/sessions logged | ☐ 🔒 |
| 12.4 | Measured comparison | Time-to-brief vs baseline workflow | ☐ |
| 12.5 | Go / no-go memo | Honest results, including failures | ☐ |

### Phase 13 — Release gate  ☐
| ID | Sub-phase | Done when | |
|---|---|---|---|
| 13.1 | Runbook | Local demo / private pilot / public each documented | ☐ |
| 13.2 | Clean-checkout reproduction | Fresh clone → working demo, offline smoke passes | ☐ |
| 13.3 | Claim audit | Every README/UI claim backed by evidence (Appendix K) | ☐ |
| 13.4 | Cost & dependency register | Zero paid runtime APIs verified by test | ☐ |
| 13.5 | Release | Tag, known-limits page | ☐ |

---

## Track B — The "crazy" layer (optional, gated; never weakens a blueprint safety rule)

Each phase has 3–4 sub-phases; the first is always the smallest honest version.

| Phase | Sub-phases | Gate |
|---|---|---|
| **14 Evidence Time Machine** ☐ | 14.1 deck.gl H3 hex layer on fixtures · 14.2 time scrubber + playback · 14.3 quality encoding (opacity = quality, hatch = low-confidence location) · 14.4 table parity + fps budget | 60 fps on M1; table identical |
| **15 Provenance X-ray** ◐ | 15.1 ☑ v0 drawer (done) · 15.2 animated lineage graph · 15.3 claim-level lineage in briefs · 15.4 test enumerating every KPI/claim | every claim opens a valid lineage |
| **16 City Pulse rhythm** ☐ | 16.1 recurrence visual spec · 16.2 `PulseStrip` component · 16.3 thresholds + definition in UI | min-sample shown |
| **17 Rain layer** 🔒 ☐ | 17.1 rainfall → area context from Open-Meteo (have data) · 17.2 IMERG ingest (needs your Earthdata account) · 17.3 lag + control analysis · 17.4 resolution-notice tests | resolution caveat enforced by test |
| **18 Offline vector basemap** 🔒 ☐ | 18.1 Mumbai PMTiles build (needs tippecanoe/planetiler) · 18.2 offline style · 18.3 attribution · 18.4 fallback tests | works with network off |
| **19 Glass-box Analyst v2** ☐ | 19.1 timeline UI · 19.2 abstention card · 19.3 draft-vs-evidence diff · 19.4 replay UI | unsafe-tool rate 0 |
| **20 Local LLM + embeddings** 🔒 ☐ | 20.1 provider interface + fake · 20.2 Ollama adapter · 20.3 embedding eval · 20.4 model cards + licence check | no silent remote fallback |
| **21 Multilingual + voice** 🔒 ☐ | 21.1 i18n framework · 21.2 Hindi/Marathi strings · 21.3 local speech-to-text (opt-in) · 21.4 redaction before storage | eval on labelled sample |
| **22 What-if lab** ☐ | 22.1 scenario schema + SIMULATION label · 22.2 simple simulation engine · 22.3 assumptions panel · 22.4 anti-misuse tests | every output labelled |
| **23 Review workspace** ☐ | 23.1 local reviewer identities · 23.2 queue + comments · 23.3 accept/edit/reject + audit · 23.4 brief versioning | audit reconstructs any brief |
| **24 Brief with receipts** ☐ | 24.1 report schema · 24.2 HTML renderer · 24.3 PDF + QR · 24.4 rebuild-from-IDs test | numbers reproduce |
| **25 Eval Lab** ☐ | 25.1 harness · 25.2 dashboard · 25.3 model-card links | every ML/RAG feature scored |
| **26 Offline PWA / field capture** 🔒 ☐ | 26.1 PWA shell · 26.2 offline queue · 26.3 consented capture · 26.4 sync conflicts | works in airplane mode |
| **27 Connector SDK** ☐ | 27.1 interface · 27.2 contract-test kit · 27.3 CKAN/Open311 reference adapter · 27.4 SSRF guard | fake passes same suite as real |
| **28 Public transparency page** 🔒 ☐ | 28.1 aggregate-only API · 28.2 k-anonymity thresholds · 28.3 embeddable widgets · 28.4 leakage tests | no row-level/PII leak |
| **29 Open data publishing** ☐ | 29.1 dataset export · 29.2 data card · 29.3 licence-compatibility check | check automated |
| **30 Federated multi-city** 🔒 ☐ | 30.1 area/tenant isolation · 30.2 per-city config · 30.3 cross-leak tests | no cross-city leakage |
| **31 Official-channel bridge** 🔒 ☐ | 31.1 authorisation evidence · 31.2 draft hand-off format · 31.3 abuse controls | written authorisation; draft-only |

When a Track B phase is started, its sub-phases are expanded into full `ID | done when | status` tables here first.

---

## Next sub-phases (proposal — pick one)
Fastest route to a visible, honest product: **4.4 → 4.5 → 5.1 → 5.2 → 5.5 → 5.6**.
Quick housekeeping worth doing first: **1.5 + 1.6** (verify `make dev`, add CI) and **2.5** (tests for the data scripts).
