-- Boundary versions (blueprint 030/035) and analysis runs (blueprint 049, p.6 traceability contract).
CREATE TABLE boundary_version (
  boundary_version_id TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  source_id TEXT NOT NULL REFERENCES source_registry(source_id),
  file_name TEXT,
  file_sha256 TEXT NOT NULL,
  crs TEXT NOT NULL,
  crs_basis TEXT NOT NULL CHECK (crs_basis IN ('assumed-wgs84','declared-wgs84')),
  name_property TEXT,
  level TEXT,
  vintage TEXT,
  licence_declared TEXT,
  feature_count INTEGER,
  bbox_json TEXT,
  qa_json TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active','superseded','failed')),
  is_synthetic INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (source_id, file_sha256)
);

ALTER TABLE area ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1;
ALTER TABLE area ADD COLUMN boundary_version_id TEXT REFERENCES boundary_version(boundary_version_id);
CREATE INDEX ix_area_active ON area(is_synthetic, is_active);

-- run_id is deterministic: hash(metric, version, params, data mode, input digest) -> repeat runs are identical.
CREATE TABLE analysis_run (
  run_id TEXT PRIMARY KEY,
  metric TEXT NOT NULL,
  metric_version TEXT NOT NULL,
  params_json TEXT NOT NULL,
  data_mode TEXT NOT NULL,
  input_count INTEGER NOT NULL,
  input_digest TEXT NOT NULL,
  window_start TEXT,
  window_end TEXT,
  source_ids_json TEXT NOT NULL,
  batch_ids_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  result_json TEXT NOT NULL
);
