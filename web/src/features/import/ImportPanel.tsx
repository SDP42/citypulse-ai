import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api, ApiFailure, importForm, type ImportSummary, type QuarantinePage } from "@/lib/api";
import { describe, sniffHeaders } from "@/lib/format";

const FIELDS = ["category", "reported_at", "latitude", "longitude", "area_name", "text", "external_id", "status"] as const;

function Stat({ label, value, tone }: { label: string; value: number; tone?: string }) {
  return (
    <div className="rounded-lg border border-line bg-panel px-4 py-3">
      <div className={`text-2xl font-semibold tabular-nums ${tone ?? ""}`}>{value.toLocaleString()}</div>
      <div className="text-xs text-muted">{label}</div>
    </div>
  );
}

function Codes({ title, counts }: { title: string; counts: Record<string, number> }) {
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  if (!entries.length) return null;
  return (
    <div>
      <h4 className="mb-2 text-sm font-medium">{title}</h4>
      <ul className="space-y-1 text-sm">
        {entries.map(([k, n]) => (
          <li key={k} className="flex gap-3"><span className="w-10 text-right font-mono text-muted">{n}</span><span>{describe(k)} <span className="font-mono text-xs text-muted">({k})</span></span></li>
        ))}
      </ul>
    </div>
  );
}

export function ImportPanel() {
  const { data: health } = useQuery({ queryKey: ["health"], queryFn: api.health });
  const { data: sources } = useQuery({ queryKey: ["sources"], queryFn: api.sources });
  const synthetic = health?.data_mode === "synthetic";
  const options = (sources?.items ?? []).filter(
    (s) => s.source_status === "verified" && ["local-generated", "user-provided-file"].includes(s.access_method ?? "") && Boolean(s.is_synthetic) === synthetic);

  const [file, setFile] = useState<File | null>(null);
  const [sourceId, setSourceId] = useState("");
  const [licence, setLicence] = useState("");
  const [headers, setHeaders] = useState<string[]>([]);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [summary, setSummary] = useState<ImportSummary | null>(null);
  const [quarantine, setQuarantine] = useState<QuarantinePage | null>(null);
  const [error, setError] = useState<ApiFailure | null>(null);
  const [busy, setBusy] = useState(false);
  const source = sourceId || options[0]?.source_id || "";
  const needsLicence = options.find((o) => o.source_id === source)?.is_synthetic === 0;

  async function onFile(f: File | null) {
    setFile(f); setSummary(null); setQuarantine(null); setError(null); setMapping({});
    setHeaders(f ? sniffHeaders(await f.slice(0, 4096).text()) : []);
  }

  async function run(kind: "preview" | "commit") {
    if (!file) return;
    setBusy(true); setError(null);
    try {
      const form = importForm(file, source, { mapping, licence });
      const s = await (kind === "preview" ? api.preview(form) : api.commit(form));
      setSummary(s); setQuarantine(null);
      if (kind === "commit" && s.batch_id && s.rows_quarantined) setQuarantine(await api.quarantine(s.batch_id));
    } catch (e) {
      setError(e instanceof ApiFailure ? e : new ApiFailure({ code: "network", message: String(e), correlation_id: "" }));
      setSummary(null);
    } finally { setBusy(false); }
  }

  const done = summary && summary.status !== "preview";
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <section className="rounded-lg border border-line bg-panel p-5">
        <h2 className="text-lg font-semibold">Import a CSV</h2>
        <p className="mt-1 text-sm text-muted">Preview first — nothing is stored until you commit. Rows are reports, not confirmed incidents. {synthetic ? "App is in synthetic mode: only synthetic sources are accepted." : "App is in real mode: synthetic sources are refused."}</p>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <label className="text-sm">Source
            <select className="mt-1 w-full rounded border border-line bg-ink px-2 py-2" value={source} onChange={(e) => setSourceId(e.target.value)}>
              {options.map((o) => <option key={o.source_id} value={o.source_id}>{o.source_name}</option>)}
            </select>
          </label>
          <label className="text-sm">CSV file
            <input type="file" accept=".csv,text/csv" className="mt-1 w-full text-sm" onChange={(e) => onFile(e.target.files?.[0] ?? null)} />
          </label>
          {needsLicence && (
            <label className="text-sm md:col-span-2">Licence / permission you hold for this data (required to commit)
              <input className="mt-1 w-full rounded border border-line bg-ink px-2 py-2" value={licence} onChange={(e) => setLicence(e.target.value)} placeholder="e.g. Partner NGO export, shared with written consent" />
            </label>
          )}
        </div>
        {error?.code === "missing_required_mapping" || error?.code === "bad_mapping" ? (
          <div className="mt-4 rounded border border-warn/40 p-3">
            <p className="text-sm text-warn">{error.message} Choose which column holds each field:</p>
            <div className="mt-2 grid gap-2 md:grid-cols-4">
              {FIELDS.map((f) => (
                <label key={f} className="text-xs text-muted">{f}
                  <select className="mt-1 w-full rounded border border-line bg-ink px-1 py-1 text-sm text-slate-200" value={mapping[f] ?? ""} onChange={(e) => setMapping({ ...mapping, [f]: e.target.value })}>
                    <option value="">— none —</option>{headers.map((h) => <option key={h}>{h}</option>)}
                  </select>
                </label>
              ))}
            </div>
          </div>
        ) : error && <p role="alert" className="mt-4 text-sm text-warn">{error.message} <span className="font-mono text-xs text-muted">[{error.code}{error.correlation_id ? ` · ${error.correlation_id}` : ""}]</span></p>}
        <div className="mt-4 flex gap-3">
          <button disabled={!file || busy || !source} onClick={() => run("preview")} className="rounded bg-line px-4 py-2 text-sm disabled:opacity-40">Preview</button>
          <button disabled={!summary || summary.status !== "preview" || summary.rows_accepted === 0 || busy || (needsLicence && !licence.trim())}
            onClick={() => run("commit")} className="rounded bg-pulse px-4 py-2 text-sm font-medium text-ink disabled:opacity-40">Commit {summary?.rows_accepted ?? ""} rows</button>
        </div>
      </section>

      {summary && (
        <section className="space-y-5 rounded-lg border border-line bg-panel p-5" aria-live="polite">
          <div className="flex items-baseline justify-between">
            <h3 className="font-semibold">{done ? (summary.status === "already_imported" ? "Already imported — nothing added" : summary.status === "failed" ? "Import failed — no rows stored" : "Import complete") : "Preview (nothing stored)"}</h3>
            <span className="font-mono text-xs text-muted">{summary.file_name} · {summary.encoding} · delimiter “{summary.delimiter === "\t" ? "tab" : summary.delimiter}” · sha256 {summary.file_sha256.slice(0, 10)}…</span>
          </div>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Stat label="rows in file" value={summary.rows_total} />
            <Stat label={done ? "stored" : "will be stored"} value={summary.rows_accepted} tone="text-pulse" />
            <Stat label="quarantined" value={summary.rows_quarantined} tone={summary.rows_quarantined ? "text-warn" : ""} />
            <Stat label="duplicates skipped" value={summary.rows_duplicate} />
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <Codes title="Why rows were quarantined" counts={summary.error_counts} />
            <Codes title="Kept, with a caveat" counts={summary.flag_counts} />
          </div>
          <details className="text-sm"><summary className="cursor-pointer text-muted">Column mapping and first rows</summary>
            <pre className="mt-2 overflow-x-auto rounded bg-ink p-3 font-mono text-xs">{JSON.stringify({ mapping: summary.mapping, sample: summary.sample }, null, 1)}</pre>
          </details>
          <ul className="list-disc pl-5 text-xs text-muted">{summary.caveats.map((c) => <li key={c}>{c}</li>)}</ul>
          {quarantine && (
            <div>
              <h4 className="mb-2 text-sm font-medium">Quarantined rows ({quarantine.total})</h4>
              <table className="w-full text-left text-xs"><thead className="text-muted"><tr><th className="py-1">Row</th><th>Reason</th><th>Redacted excerpt</th></tr></thead>
                <tbody>{quarantine.items.map((q) => (
                  <tr key={q.row_number} className="border-t border-line align-top"><td className="py-1 font-mono">{q.row_number}</td><td>{q.error_codes.map(describe).join("; ")}</td><td className="max-w-md truncate font-mono text-muted">{q.excerpt}</td></tr>
                ))}</tbody></table>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
