import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api, ApiFailure, type BoundaryResult } from "@/lib/api";
import { BOUNDARY_TEXT } from "@/lib/format";

export function BoundaryPanel() {
  const { data: health } = useQuery({ queryKey: ["health"], queryFn: api.health });
  const { data: sources } = useQuery({ queryKey: ["sources"], queryFn: api.sources });
  const synthetic = health?.data_mode === "synthetic";
  const options = (sources?.items ?? []).filter((s) => s.source_status === "verified" && ["local-generated", "user-provided-file"].includes(s.access_method ?? "") && Boolean(s.is_synthetic) === synthetic);
  const [file, setFile] = useState<File | null>(null);
  const [label, setLabel] = useState(""); const [vintage, setVintage] = useState(""); const [nameProp, setNameProp] = useState(""); const [licence, setLicence] = useState("");
  const [res, setRes] = useState<BoundaryResult | null>(null);
  const [err, setErr] = useState<ApiFailure | null>(null);
  const source = options[0]?.source_id ?? "";
  const needsLicence = !synthetic;

  const form = () => {
    const f = new FormData();
    f.set("file", file!); f.set("source_id", source); f.set("label", label); f.set("level", "ward");
    if (vintage) f.set("vintage", vintage); if (nameProp) f.set("name_property", nameProp); if (licence) f.set("licence_declared", licence);
    return f;
  };
  const run = async (commit: boolean) => {
    setErr(null);
    try { setRes(await (commit ? api.boundaryCommit(form()) : api.boundaryPreview(form()))); }
    catch (e) { setRes(null); setErr(e instanceof ApiFailure ? e : new ApiFailure({ code: "network", message: String(e), correlation_id: "" })); }
  };
  const q = res?.qa;
  const input = "mt-1 w-full rounded border border-line bg-ink px-2 py-2";
  return (
    <section className="mx-auto max-w-4xl rounded-lg border border-line bg-panel p-5">
      <h2 className="text-lg font-semibold">Import boundaries (GeoJSON polygons)</h2>
      <p className="mt-1 text-sm text-muted">Wards/zones are never guessed: bring your own file. Invalid polygons reject the whole file so no partial ward set is used. New boundaries apply to future imports only; existing reports keep their area.</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <label className="text-sm">GeoJSON file<input type="file" accept=".geojson,.json,application/geo+json" className="mt-1 w-full text-sm" onChange={(e) => { setFile(e.target.files?.[0] ?? null); setRes(null); setErr(null); }} /></label>
        <label className="text-sm">Version label (required)<input className={input} value={label} onChange={(e) => setLabel(e.target.value)} placeholder="e.g. BMC wards 2022" /></label>
        <label className="text-sm">Vintage / year<input className={input} value={vintage} onChange={(e) => setVintage(e.target.value)} placeholder="e.g. 2022" /></label>
        <label className="text-sm">Name property (optional)<input className={input} value={nameProp} onChange={(e) => setNameProp(e.target.value)} placeholder="auto: name, ward, zone_name…" /></label>
        {needsLicence && <label className="text-sm md:col-span-2">Licence / permission you hold<input className={input} value={licence} onChange={(e) => setLicence(e.target.value)} /></label>}
      </div>
      {err && <p role="alert" className="mt-3 text-sm text-warn">{err.message} <span className="font-mono text-xs text-muted">[{err.code}]</span></p>}
      <div className="mt-4 flex gap-3">
        <button disabled={!file || !source} onClick={() => run(false)} className="rounded bg-line px-4 py-2 text-sm disabled:opacity-40">Check file</button>
        <button disabled={!file || !label.trim() || res?.status !== "preview" || !q?.ok || (needsLicence && !licence.trim())} onClick={() => run(true)} className="rounded bg-pulse px-4 py-2 text-sm font-medium text-ink disabled:opacity-40">Activate as new boundary version</button>
      </div>
      {res && q && (
        <div className="mt-5 space-y-3 text-sm" aria-live="polite">
          <h3 className="font-medium">{res.status === "preview" ? "QA report (nothing stored)" : res.status === "active" ? "Boundary version activated" : res.status === "already_imported" ? "Already imported" : "Rejected — nothing activated"}</h3>
          <p className="font-mono text-xs text-muted">{q.usable_features}/{q.feature_count} usable features · name “{q.name_property ?? "none"}” · {res.crs} ({res.crs_basis}) · bbox {q.bbox?.map((n) => n.toFixed(3)).join(", ") ?? "—"} · gaps {q.gaps}</p>
          {Object.entries(q.blocking_issue_counts).map(([k, n]) => <p key={k} className="text-warn">✕ {n} × {BOUNDARY_TEXT[k] ?? k}</p>)}
          {q.warnings.map((w) => <p key={w} className="text-warn">⚠ {w}</p>)}
          {q.ok && !q.warnings.length && <p className="text-pulse">✓ All features valid, uniquely named, no significant overlaps.</p>}
          <ul className="list-disc pl-5 text-xs text-muted">{res.caveats.map((c) => <li key={c}>{c}</li>)}</ul>
        </div>
      )}
    </section>
  );
}
