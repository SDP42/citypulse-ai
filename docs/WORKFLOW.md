# Workflow — how work gets done here

## Roles
- **You (product owner/developer):** approve stack & phase gates; run Git (commit/push); decide the pilot area; approve downloads/accounts.
- **Claude Code:** proposes, implements approved batches, tests, reports. Never commits/pushes. Never starts the next batch unprompted.

## Unit of work = one sub-phase (`N.M` in [PHASES.md](PHASES.md))
Each sub-phase is one small batch (1–3 related tasks) with its own *done-when* test. Several sub-phases may be approved together, but each is tested and logged separately so a failure points at one small change.

## The loop (per sub-phase)
1. **Restate** intended files + tests before editing.
2. **Implement** small vertical slice (domain logic isolated from UI & network).
3. **Test** — unit + contract (+ integration/adversarial where relevant). Offline only by default.
4. **Report** using the template below. Append an entry to [WORKDONE.md](WORKDONE.md).
5. **STOP.** You review, run Git, approve the next batch.

## Report template (end of every batch)
1. Why this was needed · 2. How it works · 3. Files added/changed · 4. Commands run + real results · 5. Manual checks · 6. Failure cases handled · 7. Risks / licences / dependencies · 8. How to undo · 9. Suggested next batch.

## Phase gate (end of every phase)
Score each acceptance criterion **PASS / FAIL / NOT TESTED**, each PASS linked to evidence (test output, fixture, screenshot, source record). State data mode used (synthetic / real / mocked). Skipped tests are never PASS. Outcome: PASS · PASS WITH EXPLICIT RISKS · BLOCKED.

## Rules that never bend
- Zero paid runtime APIs; core path works offline.
- New DB / framework / vector store / agent library ⇒ new ADR in `docs/decisions/` + approval.
- **Downloads & accounts need explicit approval** (state file, source, size). No bulk scraping; respect rate limits/terms.
- Unverified source ⇒ stays `candidate`; never presented as an active integration.
- Branching suggestion (for you): `main` ← `phase-N/batch-M`. Conventional commits (`feat:`, `fix:`, `docs:`, `test:`).

## Local commands
```bash
make setup      # venv + npm install
make fixtures   # regenerate synthetic data
make dev        # API :8000 + web :5173
make test       # pytest + vitest
```

## Decision flow
Question → check [PRODUCT.md](PRODUCT.md) & blueprint → if it changes architecture: write ADR (status PROPOSED) → you approve → ACCEPTED → implement.

## Status vocabulary
Facts are labelled **verified**, **candidate**, **assumption**, **unresolved**. Generated text never changes source facts.
