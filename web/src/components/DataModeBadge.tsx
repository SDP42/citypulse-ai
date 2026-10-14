import type { Health } from "@/lib/api";

// Permanent chrome: synthetic and real data must never be mistaken for each other.
export function DataModeBadge({ health }: { health?: Health }) {
  if (!health) return <span className="rounded px-2 py-1 text-xs bg-line text-muted">API offline — unknown</span>;
  const synth = health.data_mode === "synthetic";
  return (
    <span className={`rounded px-2 py-1 text-xs font-mono tracking-wide ${synth ? "bg-synth/15 text-synth" : "bg-pulse/15 text-pulse"}`}>
      {synth ? "SYNTHETIC DEMO DATA" : "REAL DATA"}
    </span>
  );
}
