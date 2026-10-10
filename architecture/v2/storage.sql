-- SQLite reference schema for v2, not a migration of the legacy registry.
-- The application owns permissions, complete-bundle validation and transactions.
PRAGMA foreign_keys = ON;

CREATE TABLE source_blob (
  sha256 TEXT PRIMARY KEY CHECK(length(sha256)=64), storage_key TEXT NOT NULL,
  byte_size INTEGER NOT NULL CHECK(byte_size>=0)
);
CREATE TABLE document_version (
  id TEXT PRIMARY KEY, blob_sha256 TEXT NOT NULL REFERENCES source_blob(sha256),
  family_id TEXT, metadata_json TEXT NOT NULL, provenance_event_id TEXT NOT NULL
);
CREATE TABLE source_segment (
  id TEXT PRIMARY KEY, document_version_id TEXT NOT NULL REFERENCES document_version(id),
  parser_fingerprint TEXT NOT NULL, physical_page INTEGER NOT NULL CHECK(physical_page>=1),
  original_text TEXT NOT NULL, metadata_json TEXT NOT NULL
);
CREATE TABLE translation (
  id TEXT PRIMARY KEY, segment_id TEXT NOT NULL REFERENCES source_segment(id),
  input_fingerprint TEXT NOT NULL, english_text TEXT NOT NULL,
  alignment_and_provenance_json TEXT NOT NULL,
  UNIQUE(segment_id,input_fingerprint)
);
CREATE TABLE corpus_snapshot (
  id TEXT PRIMARY KEY, country_code TEXT, generation INTEGER NOT NULL,
  manifest_sha256 TEXT NOT NULL CHECK(length(manifest_sha256)=64), manifest_json TEXT NOT NULL
);
CREATE TABLE analysis_run (
  sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL CHECK(kind IN ('prime','ad_hoc','comparison')),
  feature TEXT NOT NULL, country_code TEXT, corpus_snapshot_id TEXT NOT NULL REFERENCES corpus_snapshot(id),
  owner_scope TEXT NOT NULL, idempotency_key TEXT NOT NULL, model_settings_json TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('queued','running','validating','complete','failed','cancelled','needs_input')),
  UNIQUE(owner_scope,idempotency_key), CHECK(kind!='prime' OR country_code IS NOT NULL)
);
CREATE TABLE task_artifact (
  id TEXT PRIMARY KEY, input_fingerprint TEXT NOT NULL, owner_scope TEXT NOT NULL,
  stage TEXT NOT NULL, sha256 TEXT NOT NULL CHECK(length(sha256)=64), storage_key TEXT NOT NULL,
  provenance_json TEXT NOT NULL, UNIQUE(owner_scope,stage,input_fingerprint)
);
CREATE TABLE run_artifact (
  run_id TEXT NOT NULL REFERENCES analysis_run(id), artifact_id TEXT NOT NULL REFERENCES task_artifact(id),
  reused INTEGER NOT NULL CHECK(reused IN (0,1)), PRIMARY KEY(run_id,artifact_id)
);
CREATE TABLE evidence_record (
  id TEXT PRIMARY KEY, artifact_id TEXT NOT NULL REFERENCES task_artifact(id), record_json TEXT NOT NULL
);
CREATE TABLE commitment_identity (
  id TEXT PRIMARY KEY, country_code TEXT NOT NULL, created_event_id TEXT NOT NULL
);
CREATE TABLE commitment_revision (
  id TEXT PRIMARY KEY, commitment_id TEXT NOT NULL REFERENCES commitment_identity(id),
  artifact_id TEXT NOT NULL REFERENCES task_artifact(id), canonical_json TEXT NOT NULL
);
CREATE TABLE validation_receipt (
  id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES analysis_run(id),
  bundle_sha256 TEXT NOT NULL CHECK(length(bundle_sha256)=64),
  state TEXT NOT NULL CHECK(state IN ('passed','passed_with_limitations')),
  validator_version TEXT NOT NULL, checks_json TEXT NOT NULL,
  UNIQUE(id,run_id,bundle_sha256)
);
CREATE TABLE report_bundle (
  id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES analysis_run(id),
  kind TEXT NOT NULL CHECK(kind IN ('prime','ad_hoc','comparison')), country_code TEXT,
  bundle_sha256 TEXT NOT NULL CHECK(length(bundle_sha256)=64), receipt_id TEXT NOT NULL,
  manifest_json TEXT NOT NULL, created_at TEXT NOT NULL,
  CHECK(kind!='prime' OR country_code IS NOT NULL),
  FOREIGN KEY(receipt_id,run_id,bundle_sha256) REFERENCES validation_receipt(id,run_id,bundle_sha256)
);
CREATE TABLE prime_selection (
  country_code TEXT PRIMARY KEY, mode TEXT NOT NULL CHECK(mode IN ('latest_successful','pinned')),
  report_id TEXT REFERENCES report_bundle(id), revision INTEGER NOT NULL CHECK(revision>=0),
  actor_id TEXT NOT NULL, changed_at TEXT NOT NULL
);
CREATE TABLE ad_hoc_history (
  report_id TEXT PRIMARY KEY REFERENCES report_bundle(id), owner_scope TEXT NOT NULL,
  previous_report_id TEXT REFERENCES report_bundle(id), brief_json TEXT NOT NULL
);
CREATE TABLE audit_event (
  id TEXT PRIMARY KEY, entity_id TEXT NOT NULL, actor_id TEXT NOT NULL,
  event_kind TEXT NOT NULL, event_json TEXT NOT NULL, created_at TEXT NOT NULL
);

CREATE INDEX records_by_artifact ON evidence_record(artifact_id);
CREATE INDEX runs_by_country_sequence ON analysis_run(country_code,sequence DESC);
CREATE INDEX reports_by_run ON report_bundle(run_id);
CREATE INDEX segments_by_document ON source_segment(document_version_id,physical_page);

CREATE TRIGGER source_version_no_update BEFORE UPDATE ON document_version
BEGIN SELECT RAISE(ABORT,'document versions are immutable'); END;
CREATE TRIGGER source_version_no_delete BEFORE DELETE ON document_version
BEGIN SELECT RAISE(ABORT,'use explicit withdrawal/tombstone, not source deletion'); END;
CREATE TRIGGER source_segment_no_update BEFORE UPDATE ON source_segment
BEGIN SELECT RAISE(ABORT,'segments are immutable; new parsing creates new IDs'); END;
CREATE TRIGGER translation_no_update BEFORE UPDATE ON translation
BEGIN SELECT RAISE(ABORT,'translation corrections create new versions'); END;
CREATE TRIGGER bundle_no_update BEFORE UPDATE ON report_bundle
BEGIN SELECT RAISE(ABORT,'reports are immutable; create a corrected bundle'); END;
CREATE TRIGGER bundle_run_scope BEFORE INSERT ON report_bundle
WHEN NOT EXISTS (SELECT 1 FROM analysis_run r WHERE r.id=NEW.run_id
                 AND r.kind=NEW.kind AND r.country_code IS NEW.country_code AND r.state='complete')
BEGIN SELECT RAISE(ABORT,'bundle must match a completed run'); END;
CREATE TRIGGER prime_insert_scope BEFORE INSERT ON prime_selection
WHEN NEW.report_id IS NOT NULL AND NOT EXISTS
 (SELECT 1 FROM report_bundle b WHERE b.id=NEW.report_id AND b.kind='prime' AND b.country_code=NEW.country_code)
BEGIN SELECT RAISE(ABORT,'Prime requires a Prime bundle for the same country'); END;
CREATE TRIGGER prime_update_scope BEFORE UPDATE ON prime_selection
WHEN NEW.report_id IS NOT NULL AND NOT EXISTS
 (SELECT 1 FROM report_bundle b WHERE b.id=NEW.report_id AND b.kind='prime' AND b.country_code=NEW.country_code)
BEGIN SELECT RAISE(ABORT,'Prime requires a Prime bundle for the same country'); END;
CREATE TRIGGER ad_hoc_scope BEFORE INSERT ON ad_hoc_history
WHEN NOT EXISTS (SELECT 1 FROM report_bundle b WHERE b.id=NEW.report_id AND b.kind IN ('ad_hoc','comparison'))
BEGIN SELECT RAISE(ABORT,'ad hoc history cannot contain Prime'); END;
