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

export type Run<R> = {
  run_id: string; metric: string; metric_version: string; created_at: string; kind: string;
  scope: Record<string, string>; input: { count: number; digest: string; source_ids: string[]; batch_ids: string[] };
  result: R; caveats: string[]; quality: { denominator: string; exclusions: string };
};
export type Summary = {
  total: number; with_point: number; without_point: number; undated: number; date_only: number; area_unresolved: number;
  observed_window_ist: { first_day: string | null; last_day: string | null };
  by_category: { category: string; count: number }[];
  by_area: { area_id: string; area: string; count: number; population: number | null; population_vintage: string | null; per_10k: number | null; per_10k_status: string }[];
};
export type Trend = { granularity: string; timezone: string; dated_total: number; undated: number; series: { start: string; count: number; no_reports: boolean }[] };
export type Lineage = {
  run_id: string; created_at: string; evidence_vs_inference: string; records_url: string;
  metric: { name: string; version: string; title: string; definition: string };
  scope: Record<string, string | null>; input: { count: number; digest: string };
  verification: { status: "verified" | "data_changed_since_run"; current_count: number; message: string };
  sources: { source_id: string; source_name: string; source_status: string; is_synthetic: number; licence_name: string | null; attribution_text: string | null; known_limitations: string | null }[];
  batches: { batch_id: string; file_name: string; file_sha256: string; started_at: string; status: string; rows_total: number; rows_accepted: number; rows_quarantined: number; rows_duplicate: number; licence_declared: string | null }[];
};
export type RunRecords = { items: { observation_id: string; external_id: string | null; category: string; reported_at: string | null; area_id: string | null }[]; total: number };
export type BoundaryQA = {
  feature_count: number; usable_features: number; name_property: string | null; bbox: number[] | null; ok: boolean; gaps: string;
  blocking_issue_counts: Record<string, number>; blocking_issues: Record<string, unknown[]>;
  overlap_count: number; overlap_warnings: { a: string; b: string; overlap_ratio_of_smaller: number }[]; warnings: string[];
};
export type BoundaryResult = {
  status: "preview" | "active" | "failed" | "already_imported"; boundary_version_id?: string; label: string; crs: string; crs_basis: string;
  qa: BoundaryQA; caveats: string[]; file_name: string; file_sha256: string;
};

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

const qs = (o: Record<string, string | undefined>) => {
  const p = new URLSearchParams(Object.entries(o).filter(([, v]) => v) as [string, string][]).toString();
  return p ? `?${p}` : "";
};
export const exportUrl = (category?: string) => `/api/observations/export.csv${qs({ category })}`;

export const api = {
  health: () => call<Health>("/health"),
  sources: () => call<{ items: Source[] }>("/sources"),
  preview: (f: FormData) => call<ImportSummary>("/imports/preview", { method: "POST", body: f }),
  commit: (f: FormData) => call<ImportSummary>("/imports", { method: "POST", body: f }),
  summary: () => call<Run<Summary>>("/analytics/summary"),
  trends: (granularity: "day" | "week") => call<Run<Trend>>(`/analytics/trends?granularity=${granularity}`),
  lineage: (run: string) => call<Lineage>(`/lineage/analysis-runs/${run}`),
  runRecords: (run: string, limit = 20) => call<RunRecords>(`/analysis-runs/${run}/records?limit=${limit}`),
  boundaryPreview: (f: FormData) => call<BoundaryResult>("/boundaries/preview", { method: "POST", body: f }),
  boundaryCommit: (f: FormData) => call<BoundaryResult>("/boundaries", { method: "POST", body: f }),
  quarantine: (batch: string) => call<QuarantinePage>(`/imports/${batch}/quarantine?limit=50`),
  observations: (limit: number, offset: number, category?: string) =>
    call<ObservationPage>(`/observations?limit=${limit}&offset=${offset}${category ? `&category=${encodeURIComponent(category)}` : ""}`),
};
