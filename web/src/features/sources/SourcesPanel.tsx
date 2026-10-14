import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function SourcesPanel() {
  const { data, error } = useQuery({ queryKey: ["sources"], queryFn: api.sources });
  if (error) return <p className="text-warn">Could not load sources: {String(error)}</p>;
  return (
    <ul className="grid gap-3 md:grid-cols-2">
      {data?.items.map((s) => (
        <li key={s.source_id} className="rounded-lg border border-line bg-panel p-4">
          <div className="flex items-center justify-between">
            <span className="font-medium">{s.source_name}</span>
            <span className="font-mono text-xs text-muted">{s.source_status}</span>
          </div>
          <p className="mt-2 text-sm text-muted">{s.known_limitations ?? "—"}</p>
          <p className="mt-2 font-mono text-xs text-muted">checked {s.checked_at ?? "never"}</p>
        </li>
      ))}
    </ul>
  );
}
