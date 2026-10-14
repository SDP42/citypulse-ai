import { useQuery } from "@tanstack/react-query";
import { motion, useReducedMotion } from "framer-motion";
import { api } from "@/lib/api";

// Provenance X-ray v0: metric -> run -> inputs -> batches -> sources -> rows. Every step is data from the API.
export function LineageDrawer({ runId, onClose }: { runId: string; onClose: () => void }) {
  const reduce = useReducedMotion();
  const { data: l, error } = useQuery({ queryKey: ["lineage", runId], queryFn: () => api.lineage(runId) });
  const { data: rec } = useQuery({ queryKey: ["records", runId], queryFn: () => api.runRecords(runId, 10) });
  const step = (i: number) => (reduce ? {} : { initial: { opacity: 0, x: 14 }, animate: { opacity: 1, x: 0 }, transition: { delay: i * 0.08 } });
  return (
    <aside role="dialog" aria-label="How this number was computed" className="fixed inset-y-0 right-0 z-20 w-full max-w-md overflow-y-auto border-l border-line bg-panel p-5 shadow-2xl">
      <div className="flex items-start justify-between">
        <h2 className="text-lg font-semibold">How was this computed?</h2>
        <button onClick={onClose} aria-label="Close" className="rounded px-2 py-1 text-muted hover:text-white">✕</button>
      </div>
      {error && <p className="mt-4 text-warn">{String(error)}</p>}
      {!l && !error && <p className="mt-4 text-muted">Loading…</p>}
      {l && (
        <ol className="mt-4 space-y-4 text-sm">
          <motion.li {...step(0)} className="rounded border border-line p-3">
            <div className="text-xs uppercase tracking-wide text-muted">1 · Metric</div>
            <b>{l.metric.title}</b> <span className="font-mono text-xs text-muted">{l.metric.version}</span>
            <p className="mt-1 text-muted">{l.metric.definition}</p>
            <p className="mt-1 text-xs text-pulse">{l.evidence_vs_inference}</p>
          </motion.li>
          <motion.li {...step(1)} className="rounded border border-line p-3">
            <div className="text-xs uppercase tracking-wide text-muted">2 · Run &amp; scope</div>
            <span className="font-mono text-xs">{l.run_id}</span>
            <pre className="mt-1 overflow-x-auto text-xs text-muted">{JSON.stringify(l.scope)}</pre>
          </motion.li>
          <motion.li {...step(2)} className={`rounded border p-3 ${l.verification.status === "verified" ? "border-pulse/40" : "border-warn/60"}`}>
            <div className="text-xs uppercase tracking-wide text-muted">3 · Input rows</div>
            <b className="tabular-nums">{l.input.count.toLocaleString()}</b> rows · digest <span className="font-mono text-xs">{l.input.digest.slice(0, 12)}…</span>
            <p className={`mt-1 ${l.verification.status === "verified" ? "text-pulse" : "text-warn"}`}>
              {l.verification.status === "verified" ? "✓ " : "⚠ "}{l.verification.message}
            </p>
          </motion.li>
          <motion.li {...step(3)} className="rounded border border-line p-3">
            <div className="text-xs uppercase tracking-wide text-muted">4 · Import batches</div>
            {l.batches.map((b) => (
              <div key={b.batch_id} className="mt-1">
                <span className="font-mono text-xs">{b.file_name}</span> · {b.rows_accepted.toLocaleString()} stored, {b.rows_quarantined.toLocaleString()} quarantined, {b.rows_duplicate.toLocaleString()} duplicates
                <div className="font-mono text-xs text-muted">sha256 {b.file_sha256.slice(0, 16)}… · {b.batch_id}</div>
                {b.licence_declared && <div className="text-xs text-muted">licence declared: {b.licence_declared}</div>}
              </div>
            ))}
          </motion.li>
          <motion.li {...step(4)} className="rounded border border-line p-3">
            <div className="text-xs uppercase tracking-wide text-muted">5 · Sources &amp; licences</div>
            {l.sources.map((s) => (
              <div key={s.source_id} className="mt-1">
                <b>{s.source_name}</b> <span className={s.is_synthetic ? "text-synth" : "text-pulse"}>{s.is_synthetic ? "SYNTHETIC" : s.source_status}</span>
                <div className="text-xs text-muted">{s.licence_name ?? "licence unknown"}{s.attribution_text ? ` · ${s.attribution_text}` : ""}</div>
                {s.known_limitations && <div className="text-xs text-muted">{s.known_limitations}</div>}
              </div>
            ))}
          </motion.li>
          <motion.li {...step(5)} className="rounded border border-line p-3">
            <div className="text-xs uppercase tracking-wide text-muted">6 · The rows themselves (first 10 of {rec?.total.toLocaleString() ?? "…"})</div>
            <table className="mt-1 w-full text-left text-xs"><tbody>
              {rec?.items.map((r) => (
                <tr key={r.observation_id} className="border-t border-line"><td className="py-1 font-mono">{r.external_id ?? r.observation_id}</td><td>{r.category}</td><td className="text-muted">{r.reported_at ?? "undated"}</td></tr>
              ))}
            </tbody></table>
          </motion.li>
        </ol>
      )}
    </aside>
  );
}
