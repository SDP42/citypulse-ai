import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { LineageDrawer } from "@/features/provenance/LineageDrawer";
import { api } from "@/lib/api";
import { pct } from "@/lib/format";
import { TrendChart } from "./TrendChart";

function Kpi({ label, value, sub, onTrace }: { label: string; value: number; sub?: string; onTrace: () => void }) {
  return (
    <button onClick={onTrace} className="rounded-lg border border-line bg-panel p-4 text-left transition hover:border-pulse/60" title="Click to see how this was computed">
      <div className="text-3xl font-semibold tabular-nums">{value.toLocaleString()}</div>
      <div className="text-sm text-muted">{label}</div>
      {sub && <div className="mt-1 font-mono text-xs text-muted">{sub}</div>}
    </button>
  );
}

export function OverviewPanel() {
  const [trace, setTrace] = useState<string | null>(null);
  const [gran, setGran] = useState<"day" | "week">("day");
  const sum = useQuery({ queryKey: ["summary"], queryFn: api.summary });
  const tr = useQuery({ queryKey: ["trend", gran], queryFn: () => api.trends(gran) });
  if (sum.error) return <p className="text-warn">Could not load summary: {String(sum.error)}</p>;
  if (!sum.data) return <p className="text-muted">Loading…</p>;
  const s = sum.data, r = s.result;
  if (r.total === 0) return <p className="text-muted">No reports stored for {s.scope.data_mode} mode. This is “no data yet”, not “no problems”. Import a CSV or GeoJSON on the Import tab.</p>;
  const maxCat = Math.max(...r.by_category.map((c) => c.count));
  const win = r.observed_window_ist;
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="rounded border border-line bg-panel px-4 py-2 text-xs text-muted">
        {s.caveats.map((c) => <p key={c}>• {c}</p>)}
        <p className="mt-1 font-mono">scope: {s.scope.data_mode} · window {win.first_day ?? "?"} → {win.last_day ?? "?"} (Asia/Kolkata) · metric {s.metric_version} · run {s.run_id}</p>
      </div>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Kpi label="reports (not confirmed incidents)" value={r.total} onTrace={() => setTrace(s.run_id)} />
        <Kpi label="with a point location" value={r.with_point} sub={pct(r.with_point, r.total)} onTrace={() => setTrace(s.run_id)} />
        <Kpi label="area-level or unresolved only" value={r.without_point} sub={`${r.area_unresolved} with no area`} onTrace={() => setTrace(s.run_id)} />
        <Kpi label="no date recorded" value={r.undated} sub={r.date_only ? `${r.date_only} date-only` : undefined} onTrace={() => setTrace(s.run_id)} />
      </div>
      <section className="rounded-lg border border-line bg-panel p-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="font-medium">Reports over time</h3>
          <div className="flex gap-1 text-xs">{(["day", "week"] as const).map((g) => <button key={g} onClick={() => setGran(g)} className={`rounded px-2 py-1 ${gran === g ? "bg-line" : "text-muted"}`}>{g}</button>)}</div>
        </div>
        {tr.data ? <TrendChart trend={tr.data.result} onTrace={() => setTrace(tr.data!.run_id)} /> : <p className="text-sm text-muted">Loading…</p>}
        {tr.data?.caveats.slice(-2).map((c) => <p key={c} className="mt-1 text-xs text-muted">{c}</p>)}
      </section>
      <div className="grid gap-6 md:grid-cols-2">
        <section className="rounded-lg border border-line bg-panel p-4">
          <h3 className="mb-3 font-medium">By category</h3>
          <ul className="space-y-2 text-sm">{r.by_category.map((c) => (
            <li key={c.category}><div className="flex justify-between"><span>{c.category}</span><span className="tabular-nums text-muted">{c.count}</span></div>
              <div className="mt-1 h-1.5 rounded bg-line"><div className="h-1.5 rounded bg-pulse" style={{ width: `${(c.count / maxCat) * 100}%` }} /></div></li>))}</ul>
        </section>
        <section className="rounded-lg border border-line bg-panel p-4">
          <h3 className="mb-3 font-medium">By area</h3>
          <table className="w-full text-left text-sm"><thead className="text-xs text-muted"><tr><th>Area</th><th className="text-right">Reports</th><th className="text-right">per 10k people</th></tr></thead>
            <tbody>{r.by_area.map((a) => (
              <tr key={a.area_id} className="border-t border-line"><td className="py-1">{a.area}</td><td className="text-right tabular-nums">{a.count}</td>
                <td className="text-right text-xs">{a.per_10k != null ? <span title={`${a.population_vintage} population`}>{a.per_10k}</span> : <span className="text-muted" title={a.per_10k_status}>not calculated</span>}</td></tr>))}</tbody></table>
          <p className="mt-2 text-xs text-muted">High counts reflect reporting as well as problems; this is not a ranking of “worst” areas.</p>
        </section>
      </div>
      {trace && <LineageDrawer runId={trace} onClose={() => setTrace(null)} />}
    </div>
  );
}
