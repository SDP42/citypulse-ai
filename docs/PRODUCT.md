# CityPulse AI — Product

> Source of truth for scope: `docs/blueprint/CityPulse_AI_Deep_Research_Engineering_Blueprint_v1.pdf` (research cut-off 2026-10-14). This file is the working interpretation; if they conflict, the blueprint's safety rules win.

## One line
An evidence workbench that turns scattered civic reports into **traceable** patterns, so a human can decide what to investigate next — and can prove why.

## Wedge
Source provenance + recurrence/spatial analytics + weather/document context + cited, human-reviewed briefs. FixMyStreet/Open311 solve *reporting*; CityPulse solves *defensible synthesis*.
(We do **not** claim nobody has built civic analytics — we claim a focused, reproducible, evidence-first implementation of an underserved workflow.)

## Who it's for (hypotheses until interviewed)
Civic researchers · ward-level NGO coordinators · residents'-association volunteers · journalists.

## What makes it memorable (the "crazy" part, inside the guardrails)
The blueprint forbids fake certainty, so our spectacle is **honesty made visual**:

1. **Evidence Time Machine** — a 3D H3-hex map (deck.gl) you scrub through time. Hex height = report count, *opacity = data quality*, hatched = low-confidence location. Rainfall (IMERG grid) pulses underneath at its true ~10 km resolution — and visibly looks coarse, on purpose.
2. **Provenance X-ray** — click *any* number, bar, or sentence → an animated lineage graph unspools: metric → analysis run → filters → observations → batch → raw snapshot → source licence. The trace contract (blueprint p.6) as a signature interaction.
3. **City Pulse rhythm** — a per-area recurrence "heartbeat" strip showing repeat-location cadence, distinct from duplicate reports.
4. **Glass-box Analyst** — a local agent whose every tool call streams live into a replayable timeline; it cites rows/pages, **abstains** with a visible "insufficient evidence" state, and can only draft.
5. **Brief with receipts** — exported evidence brief where each claim carries a lineage ID/QR back to its rows.
6. **Honest-mode chrome** — a permanent data-mode badge (SYNTHETIC DEMO / REAL / STALE source) and "unknown ≠ zero" empty states.

## MVP demo must show (blueprint p.3)
Import with schema preview + quality report · trace any number · repeat locations ≠ incidents · optional weather context with resolution caveats · cited doc Q&A with abstention · constrained agent drafting a reviewed report · all core analytics offline, no paid API.

## Non-goals
Emergency warnings · dispatch · auto-filing complaints · publishing accusations · flood *prediction* claims · login/multi-tenant/mobile for MVP · "most neglected area" rankings.

## Pilot
One Mumbai ward/area **configurable**; chosen only after source verification. Until then: clearly labelled synthetic fixtures + manual CSV/GeoJSON import.
