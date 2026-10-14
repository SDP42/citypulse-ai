# Testing strategy (blueprint 098)

| Layer | Tool | Scope |
|---|---|---|
| Unit | pytest (+hypothesis) | parsers, geometry, metrics, timestamp rules, null semantics |
| Contract | pytest + FastAPI TestClient | every route: fields, error shape, pagination, limits |
| Integration | pytest, temp SQLite | migrations from blank, import → canonical → metric, idempotency |
| Adversarial | pytest (`tests/adversarial`) | prompt injection in docs, SQL/URL/path abuse, zip bombs, CSV formula injection |
| Frontend | Vitest | components, lineage rendering, badge states |
| E2E | Playwright | one core journey: import → hotspot → trace → brief |
| Offline smoke | script | network disabled: import, analytics, retrieval fixture, export |

## Rules
- Fixtures synthetic or permission-cleared; **no test calls real APIs or paid services**.
- Tests assert behaviour (hand-calculated expected values), not model wording.
- Time-series evaluation uses chronological splits only.
- Network tests are marked `@pytest.mark.network` and opt-in.
- A skipped test is NOT TESTED, never PASS.

## Definition of done
PASS/FAIL/NOT TESTED per criterion with linked evidence; data mode stated. See [WORKFLOW.md](WORKFLOW.md).
