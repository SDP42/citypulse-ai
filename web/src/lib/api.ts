export type Health = { status: string; version: string; data_mode: "synthetic" | "real"; network: string; llm_provider: string };
export type Source = {
  source_id: string; source_name: string; source_status: string; is_synthetic: number; access_method?: string;
  known_limitations?: string; checked_at?: string; evidence?: string; licence_name?: string;
};
export type ApiError = { code: string; message: string; correlation_id: string; fields?: Record<string, string> | null };
export type ImportSummary = {
  status: "preview" | "accepted" | "quarantined" | "failed" | "already_imported";
  batch_id?: string; source_id: string; data_mode: string; file_name: string; file_sha256: string; encoding: string;
  delimiter: string; headers: string[]; mapping: Record<string, string | null>; rows_total: number; rows_accepted: number;
  rows_quarantined: number; rows_duplicate: number; error_counts: Record<string, number>; flag_counts: Record<string, number>;
  already_imported: boolean; sample: Record<string, string>[]; caveats: string[];
};
export type Observation = {
  observation_id: string; source_id: string; batch_id: string; external_id: string | null; category: string; text: string | null;
  reported_at: string | null; event_time_precision: string; latitude: number | null; longitude: number | null;
  area_id: string | null; area_name: string | null; location_method: string; quality_flags: string[];
};
export type ObservationPage = {
  items: Observation[]; total: number; limit: number; offset: number;
  scope: { data_mode: string }; quality: { with_point_coordinates: number; without_point_coordinates: number }; caveats: string[];
};
export type QuarantinePage = { items: { row_number: number; error_codes: string[]; excerpt: string }[]; total: number };

export class ApiFailure extends Error {
  constructor(public body: ApiError) { super(body.message); }
  get code() { return this.body.code; }
  get correlation_id() { return this.body.correlation_id; }
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`/api${path}`, init);
  const body = await r.json().catch(() => ({ code: "network", message: r.statusText, correlation_id: "" }));
  if (!r.ok) throw new ApiFailure(body as ApiError);
  return body as T;
}

export function importForm(file: File, source_id: string, opts: { mapping?: Record<string, string>; licence?: string }) {
  const f = new FormData();
  f.set("file", file); f.set("source_id", source_id);
  if (opts.mapping && Object.keys(opts.mapping).length) f.set("mapping", JSON.stringify(opts.mapping));
  if (opts.licence) f.set("licence_declared", opts.licence);
  return f;
}

export const api = {
  health: () => call<Health>("/health"),
  sources: () => call<{ items: Source[] }>("/sources"),
  preview: (f: FormData) => call<ImportSummary>("/imports/preview", { method: "POST", body: f }),
  commit: (f: FormData) => call<ImportSummary>("/imports", { method: "POST", body: f }),
  quarantine: (batch: string) => call<QuarantinePage>(`/imports/${batch}/quarantine?limit=50`),
  observations: (limit: number, offset: number, category?: string) =>
    call<ObservationPage>(`/observations?limit=${limit}&offset=${offset}${category ? `&category=${encodeURIComponent(category)}` : ""}`),
};
