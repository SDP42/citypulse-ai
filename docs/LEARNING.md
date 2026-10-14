# Learning track — what to study alongside each phase

Pick 1–2 items per phase; the goal is understanding what the code does, not collecting tutorials.

| Phase | Concepts | Suggested starting points |
|---|---|---|
| 1–2 | FastAPI & Pydantic v2; ADRs; open licences (ODbL, GODL-India); provenance | FastAPI docs; Michael Nygard ADR post; OSM copyright page |
| 3 | SQLite WAL, transactions, idempotency keys; data-quality dimensions; CSV pitfalls | SQLite docs; blueprint notes 033–038 |
| 4 | SQL aggregates/window functions; metric definitions, denominators | "Use the Index, Luke"; blueprint 042–049 |
| 5 | CRS/EPSG, lon/lat order, H3 hex grid, shapely | PostGIS/GeoPandas docs; H3 docs |
| 6 | Time-series validation, leakage, calibration, baselines | scikit-learn time-series CV |
| 7 | Tokenisation, Hindi/Marathi/code-mixed text, string similarity | Sentence-Transformers docs |
| 8 | BM25 vs embeddings; chunking; citation & abstention evals | FTS5 docs; RAG eval literature |
| 9 | Tool-use design; prompt injection; OWASP API Top 10 | OWASP API Security 2023; NIST AI RMF |
| 10 | Visual perception; a11y; colour-blind-safe palettes | Tufte; WCAG 2.2 quick ref |
| 14 | WebGL/deck.gl layers, animation | deck.gl docs |
| 15 | Graph layout, d3 force/dag | d3-dag; Observable examples |
| 17 | Raster data, NetCDF/xarray, spurious correlation | GPM IMERG docs |
| 18 | Vector tiles, PMTiles, planetiler | Protomaps docs |
| 19–20 | Streaming (SSE), local LLM inference on M1, quantisation | Ollama docs |
| 21 | i18n, local speech-to-text | Whisper-class models |
| 22 | Limits of causal claims; simulation labelling | Pearl "Book of Why" ch.1 |
| 26 | Service workers, IndexedDB, privacy by design | MDN PWA guide |
| 28–29 | k-anonymity, data cards, FAIR | Datasheets for Datasets |

Keep notes in `docs/notes/` (create per topic) and link them from the relevant ADR.
