-- Core canonical schema (blueprint 126/127, App. B). Raw is immutable; normalised sits beside it.
CREATE TABLE source_registry (
  source_id TEXT PRIMARY KEY,
  source_name TEXT NOT NULL,
  owner TEXT,
  canonical_url TEXT,
  access_method TEXT NOT NULL,
  licence_name TEXT,
  licence_url TEXT,
  attribution_text TEXT,
  terms_checked_at TEXT,
  source_status TEXT NOT NULL CHECK (source_status IN ('candidate','verified','research-only','blocked','disabled')),
  is_synthetic INTEGER NOT NULL DEFAULT 0,
  geographic_coverage TEXT,
  temporal_coverage TEXT,
  known_limitations TEXT
);

CREATE TABLE ingestion_batch (
  batch_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES source_registry(source_id),
  file_name TEXT,
  file_sha256 TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL CHECK (status IN ('running','accepted','quarantined','failed')),
  parser_version TEXT NOT NULL,
  rows_total INTEGER, rows_accepted INTEGER, rows_quarantined INTEGER,
  UNIQUE (source_id, file_sha256, parser_version)  -- idempotent re-import
);

CREATE TABLE area (
  area_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  level TEXT,
  boundary_source TEXT,          -- 'user-supplied' | 'synthetic' | verified source_id
  boundary_version TEXT,
  geometry_geojson TEXT
);

CREATE TABLE observation (
  observation_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES source_registry(source_id),
  batch_id TEXT NOT NULL REFERENCES ingestion_batch(batch_id),
  external_id TEXT,
  category TEXT NOT NULL,
  text_raw TEXT,
  text_normalized TEXT,
  reported_at TEXT,
  observed_at TEXT,
  event_time_precision TEXT,     -- 'minute'|'hour'|'day'|'unknown'
  status_source TEXT,
  latitude REAL, longitude REAL,
  area_id TEXT REFERENCES area(area_id),
  location_method TEXT,          -- 'point'|'ward-name'|'unresolved'
  location_confidence REAL,
  quality_flags TEXT NOT NULL DEFAULT '[]',
  record_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  schema_version TEXT NOT NULL
);
CREATE INDEX ix_obs_source ON observation(source_id);
CREATE INDEX ix_obs_time ON observation(reported_at);
CREATE INDEX ix_obs_cat ON observation(category);
CREATE INDEX ix_obs_area ON observation(area_id);
CREATE UNIQUE INDEX ux_obs_ext ON observation(source_id, external_id) WHERE external_id IS NOT NULL;

CREATE TABLE quarantine_row (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  batch_id TEXT NOT NULL REFERENCES ingestion_batch(batch_id),
  row_number INTEGER NOT NULL,
  error_codes TEXT NOT NULL,
  redacted_excerpt TEXT
);

CREATE TABLE audit_event (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT NOT NULL, actor TEXT NOT NULL, action TEXT NOT NULL, ref TEXT, detail TEXT
);
