import { scaleBand, scaleLinear } from "d3-scale";
import type { Trend } from "@/lib/api";

// Bars = reports per bucket. Hatched stub = "no reports recorded" (not "verified none"). Table fallback below for a11y.
export function TrendChart({ trend, onTrace }: { trend: Trend; onTrace: () => void }) {
  const s = trend.series;
  if (!s.length) return <p className="text-sm text-muted">No dated reports yet — nothing to chart. This is “no data”, not “no problems”.</p>;
  const W = 720, H = 180, m = { t: 8, r: 8, b: 22, l: 30 };
  const x = scaleBand<string>().domain(s.map((d) => d.start)).range([m.l, W - m.r]).padding(0.15);
  const max = Math.max(1, ...s.map((d) => d.count));
  const y = scaleLinear().domain([0, max]).nice().range([H - m.b, m.t]);
  const step = Math.ceil(s.length / 8);
  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Reports per ${trend.granularity}, ${s.length} buckets`} className="w-full" onClick={onTrace}>
        <defs><pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="5" stroke="#8a97ad" strokeWidth="1.5" /></pattern></defs>
        {y.ticks(4).map((t) => (<g key={t}><line x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} stroke="#1c2638" /><text x={m.l - 6} y={y(t) + 3} textAnchor="end" fontSize="9" fill="#8a97ad">{t}</text></g>))}
        {s.map((d, i) => (
          <g key={d.start}>
            <title>{d.start}: {d.no_reports ? "no reports recorded" : `${d.count} report${d.count === 1 ? "" : "s"}`}</title>
            {d.no_reports
              ? <rect x={x(d.start)} y={H - m.b - 6} width={x.bandwidth()} height={6} fill="url(#hatch)" />
              : <rect x={x(d.start)} y={y(d.count)} width={x.bandwidth()} height={H - m.b - y(d.count)} fill="#5eead4" rx="1.5" />}
            {i % step === 0 && <text x={(x(d.start) ?? 0) + x.bandwidth() / 2} y={H - 6} textAnchor="middle" fontSize="9" fill="#8a97ad">{d.start.slice(5)}</text>}
          </g>
        ))}
      </svg>
      <details className="mt-2 text-xs text-muted"><summary className="cursor-pointer">Data table</summary>
        <table className="mt-1"><tbody>{s.map((d) => <tr key={d.start}><td className="pr-4 font-mono">{d.start}</td><td>{d.no_reports ? "no reports recorded" : d.count}</td></tr>)}</tbody></table>
      </details>
    </div>
  );
}
