import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { describe, formatWhen } from "@/lib/format";

const PAGE = 25;
const CATS = ["", "waterlogging", "pothole", "drain_blockage", "garbage", "streetlight"];

export function IncidentsPanel() {
  const [offset, setOffset] = useState(0);
  const [category, setCategory] = useState("");
  const { data, error, isFetching } = useQuery({
    queryKey: ["observations", offset, category], queryFn: () => api.observations(PAGE, offset, category || undefined), placeholderData: keepPreviousData,
  });
  if (error) return <p className="text-warn">Could not load reports: {String(error)}</p>;
  if (!data) return <p className="text-muted">Loading…</p>;
  if (data.total === 0 && !category)
    return <p className="text-muted">No reports stored for {data.scope.data_mode} mode. This is “no data yet”, not “no problems” — import a CSV on the Import tab.</p>;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm text-muted"><b className="text-slate-200">{data.total.toLocaleString()}</b> reports (not confirmed incidents) · {data.quality.with_point_coordinates.toLocaleString()} with a point · {data.quality.without_point_coordinates.toLocaleString()} without (never given a fake point)</div>
        <select aria-label="Category" className="rounded border border-line bg-panel px-2 py-1 text-sm" value={category} onChange={(e) => { setCategory(e.target.value); setOffset(0); }}>
          {CATS.map((c) => <option key={c} value={c}>{c || "all categories"}</option>)}
        </select>
      </div>
      <div className={`overflow-x-auto rounded-lg border border-line ${isFetching ? "opacity-70" : ""}`}>
        <table className="w-full text-left text-sm">
          <thead className="bg-panel text-xs text-muted"><tr><th className="p-2">When</th><th>Category</th><th>Area</th><th>Location</th><th>Text</th><th>Caveats</th></tr></thead>
          <tbody>{data.items.map((o) => (
            <tr key={o.observation_id} className="border-t border-line align-top">
              <td className="whitespace-nowrap p-2">{formatWhen(o.reported_at, o.event_time_precision)}</td>
              <td>{o.category}</td><td>{o.area_name ?? <span className="text-muted">unresolved</span>}</td>
              <td className="font-mono text-xs">{o.latitude != null ? `${o.latitude.toFixed(4)}, ${o.longitude?.toFixed(4)}` : <span className="text-muted">{o.location_method}</span>}</td>
              <td className="max-w-xs truncate">{o.text}</td>
              <td className="text-xs text-muted">{o.quality_flags.map(describe).join(" · ")}</td>
            </tr>))}</tbody>
        </table>
      </div>
      <div className="flex items-center gap-3 text-sm">
        <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))} className="rounded bg-line px-3 py-1 disabled:opacity-40">Previous</button>
        <span className="text-muted">{offset + 1}–{Math.min(offset + PAGE, data.total)} of {data.total.toLocaleString()}</span>
        <button disabled={offset + PAGE >= data.total} onClick={() => setOffset(offset + PAGE)} className="rounded bg-line px-3 py-1 disabled:opacity-40">Next</button>
      </div>
    </div>
  );
}
