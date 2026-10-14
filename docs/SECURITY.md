# Security & safety (blueprint 083–088, App. D)

## Trust zones
A source intake · B canonical data · C derived analysis · D AI interface — see [ARCHITECTURE.md](ARCHITECTURE.md).

## Release blockers
| Risk | Required control |
|---|---|
| Prompt injection via reports/docs | Retrieved text is data; tools authorised independently; adversarial tests |
| Arbitrary SQL / data exposure | Allowlisted metric tools; read-only DB connection; row/time limits |
| SSRF / arbitrary URLs | Hosts allowlisted in config only; no model-generated URLs; private ranges denied; `NETWORK=off` default |
| Malicious uploads | Size/row limits, temp files, parser tests, transaction rollback, no macro/formula execution |
| PII in logs/embeddings | Redaction, retention plan, no raw prompt logs |
| Unclear licence | Source marked `candidate`/blocked; attribution tracked |
| False street-level hazard claims | Resolution caveats; no predictive flood claims; no emergency warnings |
| Stale source shown as current | Visible staleness; no-data ≠ no-incident |
| Unreviewed recommendations | Draft-only + review event; no external action channel |

## Local-first assumptions
Single-user local app; no auth in MVP. Any shared deployment ⇒ new threat model + auth before exposure.

## Reporting
Not a legal certification or pen test. Re-review before any real civic deployment.
