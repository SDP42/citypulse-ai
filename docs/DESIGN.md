# Frontend design system

**Mood:** a dark "city control room" that is *honest* — visually loud about uncertainty, quiet about everything else.

## Principles
1. **Uncertainty is a first-class visual**: opacity = data quality, hatch = low-confidence location, dashed = inferred, solid = observed.
2. **Never red/green only**; always a second channel (shape/pattern/label). Tabular fallback for every chart/map.
3. **Every number is clickable** → Provenance X-ray.
4. **Data-mode badge always visible** (SYNTHETIC pink, REAL teal, STALE amber).
5. **Unknown ≠ zero**: empty states say "no data received" vs "verified none".
6. Motion explains (time scrub, lineage unspooling), never decorates; respect `prefers-reduced-motion`.

## Tokens (tailwind.config.js)
`ink #07090f` bg · `panel #0d121c` · `line #1c2638` · `pulse #5eead4` accent · `warn #fbbf24` · `synth #f472b6` · `muted #8a97ad`. Fonts: Inter + JetBrains Mono for IDs/hashes.

## Layout
Header (logo · tabs · data-mode badge) → global filter bar (area · category · window · mode) → page. Pages: Overview · Map & hotspots · Time trends · Incident explorer · Sources/health · Evidence library · Analysis brief · Import/Settings (blueprint note 050).

## Signature components (Track B)
`TimeMachineMap`, `LineageXRay`, `PulseStrip`, `AgentTimeline`, `AbstentionCard`, `BriefReceipt`, `QualityBadge`, `ResolutionNotice`.

## Accessibility
Keyboard-navigable, focus rings, ≥4.5:1 contrast, ARIA for charts with table alternative, reduced-motion path, colour-blind-safe palette checked.

## Map rules
Provider configurable; OSM attribution visible; no bulk tile fetching; offline PMTiles/GeoJSON fallback; location-precision indicator on points.
