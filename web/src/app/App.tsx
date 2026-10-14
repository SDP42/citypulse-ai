import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { DataModeBadge } from "@/components/DataModeBadge";
import { ImportPanel } from "@/features/import/ImportPanel";
import { IncidentsPanel } from "@/features/incidents/IncidentsPanel";
import { SourcesPanel } from "@/features/sources/SourcesPanel";
import { api } from "@/lib/api";

const TABS = ["Overview", "Map", "Timeline", "Incidents", "Sources", "Evidence", "Brief", "Import"] as const;
type Tab = (typeof TABS)[number];

export default function App() {
  const [tab, setTab] = useState<Tab>("Import");
  const { data: health } = useQuery({ queryKey: ["health"], queryFn: api.health, retry: false });
  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between border-b border-line px-6 py-3">
        <h1 className="text-lg font-semibold tracking-tight">City<span className="text-pulse">Pulse</span> AI</h1>
        <nav className="flex gap-1 text-sm">
          {TABS.map((t) => (
            <button key={t} onClick={() => setTab(t)}
              className={`rounded px-3 py-1.5 ${tab === t ? "bg-line text-white" : "text-muted hover:text-white"}`}>{t}</button>
          ))}
        </nav>
        <DataModeBadge health={health} />
      </header>
      <main className="p-6">
        {tab === "Sources" ? <SourcesPanel /> : tab === "Import" ? <ImportPanel /> : tab === "Incidents" ? <IncidentsPanel /> : <p className="text-muted">{tab} — planned in a later phase (see docs/PHASES.md).</p>}
      </main>
    </div>
  );
}
