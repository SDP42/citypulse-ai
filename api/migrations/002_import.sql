-- Importer support: area mode/population, batch accounting, hash-level idempotency.
ALTER TABLE area ADD COLUMN is_synthetic INTEGER NOT NULL DEFAULT 0;
ALTER TABLE area ADD COLUMN population INTEGER;
ALTER TABLE area ADD COLUMN population_vintage TEXT;

ALTER TABLE ingestion_batch ADD COLUMN rows_duplicate INTEGER;
ALTER TABLE ingestion_batch ADD COLUMN data_mode TEXT;
ALTER TABLE ingestion_batch ADD COLUMN licence_declared TEXT;
ALTER TABLE ingestion_batch ADD COLUMN mapping_json TEXT;
ALTER TABLE ingestion_batch ADD COLUMN raw_path TEXT;
ALTER TABLE ingestion_batch ADD COLUMN summary_json TEXT;

CREATE UNIQUE INDEX ux_obs_hash ON observation(source_id, record_hash);
CREATE INDEX ix_quarantine_batch ON quarantine_row(batch_id);
