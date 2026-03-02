# Minimal Schema DDL (CDC MVP)

**Goal**: Define the smallest relational-friendly schema that supports:
- Case Registry (Output A)
- Artifact Index / Mirror (Output B)
- Versioning (case_version)
- Canonical text outputs (case_text)
- CDC Evidence (poll_run, change_event)
- Minimal recompute + auditability

**Version**: 1.0.0  
**Last Updated**: 2026-01-25  
**Status**: Build-ready schema definition

---

## Implementation Notes

**Type System**:
- Types are generic (Postgres-ish). Adapt to SQLite/Cosmos/DynamoDB as needed.
- Use UUIDs or ULIDs in real implementation; here we keep it simple with TEXT.
- Every table includes keys to support ATO-friendly traceability.

**Azure Cosmos DB Mapping**:
- Each table → Cosmos DB container
- Primary keys → Cosmos DB `id` field
- Foreign keys → Application-enforced (Cosmos has no foreign key constraints)
- Indexes → Cosmos DB indexing policy
- JSON columns → Native JSON support

**Partition Keys** (Critical for Cosmos DB performance):
- `case` → Partition by `tribunal_id`
- `poll_run` → Partition by `scope_id`
- `change_event` → Partition by `poll_run_id`
- `artifact` → Partition by `case_version_id`
- `case_text` → Partition by `case_version_id`

---

## Schema Overview (12 Tables)

| Category | Tables | Purpose |
|----------|--------|---------|
| **Reference** | tribunal, source_system | Lookup tables for external systems |
| **Corpus Management** | corpus_registry | Multi-corpus SLO tracking and freshness monitoring |
| **Case Registry** | case, case_source_key | Output A - Case identity and mapping |
| **Versioning** | case_version | CDC core - Version tracking with provenance |
| **Artifact Index** | artifact | Output B - Blob/file tracking with hashes |
| **Canonical Text** | case_text | Output C - Language-specific extracted text |
| **CDC Evidence** | poll_run, change_event | Output D - Audit trail for all changes |
| **Enrichment** | case_metadata | Optional - Structured metadata key/value |

---

## 1) Reference Tables

### tribunal

**Purpose**: Authoritative list of tribunals and courts.

```sql
CREATE TABLE tribunal (
  tribunal_id            TEXT PRIMARY KEY,
  name_en                TEXT NOT NULL,
  name_fr                TEXT,
  jurisdiction           TEXT NOT NULL,
  court_level            TEXT NOT NULL,   -- e.g., tribunal | FC | FCA | SCC
  precedence_rank        INTEGER,         -- optional ordering signal
  is_active              BOOLEAN NOT NULL DEFAULT TRUE
);
```

**Example rows**:
```sql
INSERT INTO tribunal VALUES 
  ('SST-GD', 'Social Security Tribunal - General Division', 'Tribunal de la sécurité sociale - Division générale', 'federal', 'tribunal', 10, TRUE),
  ('SST-AD', 'Social Security Tribunal - Appeal Division', 'Tribunal de la sécurité sociale - Division d''appel', 'federal', 'tribunal', 20, TRUE),
  ('FC', 'Federal Court', 'Cour fédérale', 'federal', 'trial', 30, TRUE),
  ('FCA', 'Federal Court of Appeal', 'Cour d''appel fédérale', 'federal', 'appeal', 40, TRUE),
  ('SCC', 'Supreme Court of Canada', 'Cour suprême du Canada', 'federal', 'supreme', 50, TRUE);
```

**Cosmos DB Mapping**:
```json
{
  "id": "SST-GD",
  "tribunal_id": "SST-GD",
  "name_en": "Social Security Tribunal - General Division",
  "name_fr": "Tribunal de la sécurité sociale - Division générale",
  "jurisdiction": "federal",
  "court_level": "tribunal",
  "precedence_rank": 10,
  "is_active": true
}
```

---

### source_system

**Purpose**: Track data provenance - where cases/artifacts came from.

```sql
CREATE TABLE source_system (
  source_system_id       TEXT PRIMARY KEY, -- e.g., canlii_api | canlii_html | scc_site | accenture_seed | blob_mirror
  source_type            TEXT NOT NULL,     -- api | web | seed | mirror
  trust_rank             INTEGER,           -- optional (higher = more trusted)
  notes                  TEXT
);
```

**Example rows**:
```sql
INSERT INTO source_system VALUES 
  ('canlii_api', 'api', 95, 'CanLII metadata API - PRIMARY SOURCE OF TRUTH (metadata only, no documents)'),
  ('canlii_html', 'web', 85, 'CanLII HTML scraping (deprecated after CDC)'),
  ('blob_mirror', 'mirror', 90, 'Azure Blob Storage mirror (artifact storage)'),
  ('accenture_seed', 'seed', 80, 'Accenture seed corpus (bootstrap Day 0)');
```

**Rationale**: When an artifact hash conflict occurs, `trust_rank` determines which source wins. **CanLII API is the authoritative source** (trust_rank 95).

---

## 2) Output A — Case Registry

### case

**Purpose**: Internal stable identity for a case, with authoritative metadata.

```sql
CREATE TABLE "case" (
  case_id                TEXT PRIMARY KEY,     -- internal stable ID (ULID or UUID)
  tribunal_id            TEXT NOT NULL REFERENCES tribunal(tribunal_id),

  decision_date          DATE,                 -- when decision was made
  publication_date       DATE,                 -- when first published online (if known)
  style_of_cause         TEXT,
  docket_number          TEXT,
  neutral_citation       TEXT,

  language_set           TEXT NOT NULL,        -- EN | FR | BOTH
  case_status            TEXT NOT NULL DEFAULT 'active',  -- active | withdrawn | superseded | unknown

  created_at_utc         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_case_tribunal_date ON "case"(tribunal_id, decision_date);
```

**Cosmos DB Mapping**:
```json
{
  "id": "01JGQP2VWXYZ...",
  "case_id": "01JGQP2VWXYZ...",
  "tribunal_id": "SST-GD",
  "decision_date": "2020-03-15",
  "publication_date": "2020-03-20",
  "style_of_cause": "Smith v. Minister of Employment",
  "docket_number": "GE-20-123",
  "neutral_citation": "2020 SST 123",
  "language_set": "BOTH",
  "case_status": "active",
  "created_at_utc": "2026-01-25T10:00:00Z",
  "updated_at_utc": "2026-01-25T10:00:00Z"
}
```

**Partition Key**: `tribunal_id` (enables scoped queries like "all SST-GD cases")

---

### case_source_key

**Purpose**: Map external identifiers to internal `case_id`.

```sql
CREATE TABLE case_source_key (
  case_source_key_id     TEXT PRIMARY KEY,
  case_id                TEXT NOT NULL REFERENCES "case"(case_id),

  source_system_id       TEXT NOT NULL REFERENCES source_system(source_system_id),
  external_key           TEXT NOT NULL,         -- e.g., "sstcgen:2020SST123" or "seed:2016_SSTADEI_259_..." or "scc:2024scc15"
  canonical_url          TEXT,                  -- optional canonical URL

  created_at_utc         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Ensure we don't duplicate the same external key within a source_system.
CREATE UNIQUE INDEX uq_case_source_key ON case_source_key(source_system_id, external_key);
```

**Example rows**:
```sql
INSERT INTO case_source_key VALUES 
  ('01JGQP3ABC...', '01JGQP2VWXYZ...', 'canlii_api', 'sstcgen:2020SST123', 'https://www.canlii.org/en/ca/sst/doc/2020/2020sst123/2020sst123.html', CURRENT_TIMESTAMP),
  ('01JGQP3DEF...', '01JGQP2VWXYZ...', 'accenture_seed', 'seed:2020_SST_123_Smith.pdf', NULL, CURRENT_TIMESTAMP);
```

**Cosmos DB Mapping**:
```json
{
  "id": "01JGQP3ABC...",
  "case_source_key_id": "01JGQP3ABC...",
  "case_id": "01JGQP2VWXYZ...",
  "source_system_id": "canlii_api",
  "external_key": "sstcgen:2020SST123",
  "canonical_url": "https://www.canlii.org/en/ca/sst/doc/2020/2020sst123/2020sst123.html",
  "created_at_utc": "2026-01-25T10:00:00Z"
}
```

**Partition Key**: `source_system_id` (enables fast lookup by source)

**Rationale**: One case may have multiple external keys (e.g., CanLII ID + seed filename from Accenture bootstrap). **CanLII is the authoritative source** - other keys map to the same case_id.

---

## 3) Versioning — case_version (CDC Core)

### case_version

**Purpose**: Track every meaningful change to a case over time (CDC core).

```sql
CREATE TABLE case_version (
  case_version_id        TEXT PRIMARY KEY,
  case_id                TEXT NOT NULL REFERENCES "case"(case_id),

  version_seq            INTEGER NOT NULL,      -- 1..n
  detected_at_utc        TIMESTAMP NOT NULL,    -- when CDC detected the change
  reason                 TEXT NOT NULL,         -- new_or_identity_change | content_change | meaningful_metadata_change | deleted_or_withdrawn | seed
  supersedes_case_version_id TEXT REFERENCES case_version(case_version_id),

  is_current             BOOLEAN NOT NULL DEFAULT FALSE,

  -- Traceability to CDC evidence
  created_by_poll_run_id TEXT,                  -- FK to poll_run (nullable for bootstrap)
  created_by_change_event_id TEXT,              -- FK to change_event (nullable for bootstrap)

  created_at_utc         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX uq_case_version_seq ON case_version(case_id, version_seq);
CREATE INDEX idx_case_version_current ON case_version(case_id, is_current);
```

**Example rows**:
```sql
-- Bootstrap version
INSERT INTO case_version VALUES 
  ('01JGQP4ABC...', '01JGQP2VWXYZ...', 1, '2026-01-20T00:00:00Z', 'seed', NULL, TRUE, NULL, NULL, '2026-01-20T00:00:00Z');

-- CDC detected content change
INSERT INTO case_version VALUES 
  ('01JGQP5DEF...', '01JGQP2VWXYZ...', 2, '2026-01-25T10:15:00Z', 'content_change', '01JGQP4ABC...', TRUE, '01JGQP5XYZ...', '01JGQP5AAA...', '2026-01-25T10:15:00Z');

-- Invalidate old version
UPDATE case_version SET is_current = FALSE WHERE case_version_id = '01JGQP4ABC...';
```

**Cosmos DB Mapping**:
```json
{
  "id": "01JGQP5DEF...",
  "case_version_id": "01JGQP5DEF...",
  "case_id": "01JGQP2VWXYZ...",
  "version_seq": 2,
  "detected_at_utc": "2026-01-25T10:15:00Z",
  "reason": "content_change",
  "supersedes_case_version_id": "01JGQP4ABC...",
  "is_current": true,
  "created_by_poll_run_id": "01JGQP5XYZ...",
  "created_by_change_event_id": "01JGQP5AAA...",
  "created_at_utc": "2026-01-25T10:15:00Z"
}
```

**Partition Key**: `case_id` (all versions for a case in same partition)

**Critical Rules**:
- Exactly one `is_current=TRUE` per `case_id`
- `version_seq` must increment monotonically
- Bootstrap versions have `reason='seed'` and `created_by_poll_run_id=NULL`

---

## 4) Output B — Artifact Index / Mirror

### artifact

**Purpose**: Track stored/observed items (PDFs, HTML, extracted text) with provenance + hashes.

```sql
CREATE TABLE artifact (
  artifact_id            TEXT PRIMARY KEY,
  case_version_id        TEXT NOT NULL REFERENCES case_version(case_version_id),

  language               TEXT NOT NULL,         -- EN | FR | BOTH
  artifact_type          TEXT NOT NULL,         -- html | pdf | text_extract | ocr_text | json_seed
  source_system_id       TEXT NOT NULL REFERENCES source_system(source_system_id),

  source_url             TEXT,                  -- where it came from (if applicable)
  retrieved_at_utc       TIMESTAMP NOT NULL,    -- when we fetched/observed it

  etag                   TEXT,
  last_modified_utc      TIMESTAMP,
  content_length         BIGINT,
  content_hash           TEXT,                  -- sha256 of normalized bytes or normalized text
  mime_type              TEXT,

  storage_uri            TEXT NOT NULL,         -- blob path / file path

  created_at_utc         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_artifact_casever_type_lang ON artifact(case_version_id, artifact_type, language);
CREATE INDEX idx_artifact_hash ON artifact(content_hash);
```

**Example rows**:
```sql
INSERT INTO artifact VALUES 
  ('01JGQP6ABC...', '01JGQP5DEF...', 'EN', 'pdf', 'blob_mirror', 
   'https://example.com/case.pdf', '2026-01-25T10:00:00Z', 
   'W/"abc123"', '2026-01-24T15:30:00Z', 524288, 
   'sha256:abc123def456...', 'application/pdf', 
   'documents/raw-artifacts/SST-GD/2020/01JGQP2VWXYZ_EN.pdf', 
   '2026-01-25T10:00:00Z');
```

**Cosmos DB Mapping**:
```json
{
  "id": "01JGQP6ABC...",
  "artifact_id": "01JGQP6ABC...",
  "case_version_id": "01JGQP5DEF...",
  "language": "EN",
  "artifact_type": "pdf",
  "source_system_id": "blob_mirror",
  "source_url": "https://example.com/case.pdf",
  "retrieved_at_utc": "2026-01-25T10:00:00Z",
  "etag": "W/\"abc123\"",
  "last_modified_utc": "2026-01-24T15:30:00Z",
  "content_length": 524288,
  "content_hash": "sha256:abc123def456...",
  "mime_type": "application/pdf",
  "storage_uri": "documents/raw-artifacts/SST-GD/2020/01JGQP2VWXYZ_EN.pdf",
  "created_at_utc": "2026-01-25T10:00:00Z"
}
```

**Partition Key**: `case_version_id` (all artifacts for a version in same partition)

**Rationale**: 
- `content_hash` is the **primary change signal** for CDC (C1 test)
- `etag` and `last_modified_utc` are **secondary signals** (E1 test)
- `storage_uri` is **NOT NULL** - every artifact must be stored

---

## 5) Output C — Canonical Text (Clean, Per Language)

### case_text

**Purpose**: Canonical extracted text for each language, traceable to source artifact.

```sql
CREATE TABLE case_text (
  case_text_id           TEXT PRIMARY KEY,
  case_version_id        TEXT NOT NULL REFERENCES case_version(case_version_id),

  language               TEXT NOT NULL,         -- EN | FR
  text_source_artifact_id TEXT NOT NULL REFERENCES artifact(artifact_id),

  extraction_method      TEXT NOT NULL,         -- html_parse | pdf_text | ocr
  normalized_text_hash   TEXT NOT NULL,         -- hash of normalized extracted text
  normalized_text_uri    TEXT NOT NULL,         -- reference to stored text (blob/file)
  quality_score          REAL,                  -- optional
  warnings               TEXT,                  -- optional (json string or freeform)

  created_at_utc         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX uq_case_text_lang ON case_text(case_version_id, language);
CREATE INDEX idx_case_text_hash ON case_text(normalized_text_hash);
```

**Example rows**:
```sql
INSERT INTO case_text VALUES 
  ('01JGQP7ABC...', '01JGQP5DEF...', 'EN', '01JGQP6ABC...', 
   'pdf_text', 'sha256:text_abc123...', 
   'documents/canonical-text/SST-GD/2020/01JGQP2VWXYZ_EN_v2.txt', 
   0.95, NULL, 
   '2026-01-25T10:05:00Z');
```

**Cosmos DB Mapping**:
```json
{
  "id": "01JGQP7ABC...",
  "case_text_id": "01JGQP7ABC...",
  "case_version_id": "01JGQP5DEF...",
  "language": "EN",
  "text_source_artifact_id": "01JGQP6ABC...",
  "extraction_method": "pdf_text",
  "normalized_text_hash": "sha256:text_abc123...",
  "normalized_text_uri": "documents/canonical-text/SST-GD/2020/01JGQP2VWXYZ_EN_v2.txt",
  "quality_score": 0.95,
  "warnings": null,
  "created_at_utc": "2026-01-25T10:05:00Z"
}
```

**Partition Key**: `case_version_id` (same as artifact)

**Critical Rules**:
- **Exactly one** `case_text` per `(case_version_id, language)` (enforced by unique index)
- `normalized_text_hash` change triggers **content change** (C2 test)
- `text_source_artifact_id` must reference an artifact with same `case_version_id`

---

## 6) CDC Evidence — poll_run and change_event (Output D)

### poll_run

**Purpose**: One CDC execution record (ATO audit trail).

```sql
CREATE TABLE poll_run (
  poll_run_id            TEXT PRIMARY KEY,
  scope_id               TEXT NOT NULL,

  policy_id              TEXT NOT NULL,         -- from cdc/change-policy.yaml
  policy_version         TEXT NOT NULL,
  policy_hash            TEXT NOT NULL,         -- hash of policy file content (for audit)

  started_at_utc         TIMESTAMP NOT NULL,
  ended_at_utc           TIMESTAMP,

  -- Summary counts (store as JSON text for flexibility)
  result_counts_json     TEXT NOT NULL,         -- e.g., {"cases_checked":123,"new":5,"content":2,"metadata":1,"cosmetic":10,"failures":3}

  notes                  TEXT
);

CREATE INDEX idx_poll_run_scope_time ON poll_run(scope_id, started_at_utc);
```

**Example rows**:
```sql
INSERT INTO poll_run VALUES 
  ('01JGQP8ABC...', 'SST-GD-EN-rolling-24mo', 
   'change-policy', '0.1.0', 'sha256:policy_abc123...', 
   '2026-01-25T10:00:00Z', '2026-01-25T10:15:00Z', 
   '{"cases_checked":150,"new":2,"content":1,"metadata_meaningful":3,"cosmetic":12,"ignored_out_of_scope":5}', 
   'CDC Tier 1 metadata poll');
```

**Cosmos DB Mapping**:
```json
{
  "id": "01JGQP8ABC...",
  "poll_run_id": "01JGQP8ABC...",
  "scope_id": "SST-GD-EN-rolling-24mo",
  "policy_id": "change-policy",
  "policy_version": "0.1.0",
  "policy_hash": "sha256:policy_abc123...",
  "started_at_utc": "2026-01-25T10:00:00Z",
  "ended_at_utc": "2026-01-25T10:15:00Z",
  "result_counts_json": "{\"cases_checked\":150,\"new\":2,\"content\":1,\"metadata_meaningful\":3,\"cosmetic\":12,\"ignored_out_of_scope\":5}",
  "notes": "CDC Tier 1 metadata poll"
}
```

**Partition Key**: `scope_id` (enables scoped query "all polls for SST-GD-EN-rolling-24mo")

**Critical Rule**: **Every CDC execution creates exactly one `poll_run`** (A2 test)

---

### change_event

**Purpose**: One detected change record (evidence for every non-noop action).

```sql
CREATE TABLE change_event (
  change_event_id        TEXT PRIMARY KEY,
  poll_run_id            TEXT NOT NULL REFERENCES poll_run(poll_run_id),
  case_id                TEXT NOT NULL REFERENCES "case"(case_id),

  -- Optional linkage to case_version (may be filled after version creation)
  case_version_id        TEXT REFERENCES case_version(case_version_id),

  artifact_type          TEXT,                  -- when change pertains to a specific artifact
  language               TEXT,

  change_class           TEXT NOT NULL,         -- structural | availability | metadata_meaningful | metadata_nonmeaningful | content | cosmetic | unreachable | deleted
  change_type            TEXT NOT NULL,         -- new | modified | deleted | unreachable | redirected | missing
  signal_id              TEXT NOT NULL,         -- e.g., artifact_pdf_hash_changed, registry_new_case_id, http_redirect

  previous_hash          TEXT,
  new_hash               TEXT,

  action_taken_json      TEXT NOT NULL,         -- e.g., ["fetch_artifact","extract_text","generate_chunks","embed_chunks","update_index"]

  status                 TEXT NOT NULL DEFAULT 'recorded',  -- recorded | executed | failed | skipped
  notes                  TEXT,

  created_at_utc         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_change_event_poll_case ON change_event(poll_run_id, case_id);
CREATE INDEX idx_change_event_class ON change_event(change_class);
CREATE INDEX idx_change_event_signal ON change_event(signal_id);
```

**Example rows**:
```sql
INSERT INTO change_event VALUES 
  ('01JGQP9ABC...', '01JGQP8ABC...', '01JGQP2VWXYZ...', '01JGQP5DEF...', 
   'pdf', 'EN', 
   'content', 'modified', 'artifact_pdf_hash_changed', 
   'sha256:old_abc123...', 'sha256:new_xyz789...', 
   '["fetch_artifact","extract_text","generate_chunks","embed_chunks","update_index"]', 
   'executed', NULL, 
   '2026-01-25T10:10:00Z');
```

**Cosmos DB Mapping**:
```json
{
  "id": "01JGQP9ABC...",
  "change_event_id": "01JGQP9ABC...",
  "poll_run_id": "01JGQP8ABC...",
  "case_id": "01JGQP2VWXYZ...",
  "case_version_id": "01JGQP5DEF...",
  "artifact_type": "pdf",
  "language": "EN",
  "change_class": "content",
  "change_type": "modified",
  "signal_id": "artifact_pdf_hash_changed",
  "previous_hash": "sha256:old_abc123...",
  "new_hash": "sha256:new_xyz789...",
  "action_taken_json": "[\"fetch_artifact\",\"extract_text\",\"generate_chunks\",\"embed_chunks\",\"update_index\"]",
  "status": "executed",
  "notes": null,
  "created_at_utc": "2026-01-25T10:10:00Z"
}
```

**Partition Key**: `poll_run_id` (all changes from one poll in same partition)

**Critical Rules**:
- **Every downstream action** must have a `change_event` (H1 test)
- `signal_id` must match signals from `change-policy.yaml`
- `change_class` must match classes from `change-policy.yaml`
- `action_taken_json` must match actions vocabulary from `change-policy.yaml`

---

## 7) Optional (Recommended) — Enriched Metadata Key/Value

### case_metadata

**Purpose**: Store structured metadata (topics, keywords, outcomes) extracted or inferred.

```sql
CREATE TABLE case_metadata (
  case_metadata_id       TEXT PRIMARY KEY,
  case_version_id        TEXT NOT NULL REFERENCES case_version(case_version_id),

  key                    TEXT NOT NULL,         -- e.g., ei_topic | legal_domain | statutes | outcome | keywords
  value_json             TEXT NOT NULL,         -- store as JSON string

  method                 TEXT NOT NULL,         -- rule | model | human | seed
  confidence             REAL,                  -- optional

  created_at_utc         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_case_metadata_key ON case_metadata(case_version_id, key);
```

**Example rows**:
```sql
INSERT INTO case_metadata VALUES 
  ('01JGQPAABC...', '01JGQP5DEF...', 
   'ei_topic', '["qualification","misconduct"]', 
   'rule', 1.0, 
   '2026-01-25T10:07:00Z'),
  ('01JGQPABCD...', '01JGQP5DEF...', 
   'outcome', '{"decision":"dismissed","beneficiary":"employer"}', 
   'model', 0.85, 
   '2026-01-25T10:08:00Z');
```

**Cosmos DB Mapping**:
```json
{
  "id": "01JGQPAABC...",
  "case_metadata_id": "01JGQPAABC...",
  "case_version_id": "01JGQP5DEF...",
  "key": "ei_topic",
  "value_json": "[\"qualification\",\"misconduct\"]",
  "method": "rule",
  "confidence": 1.0,
  "created_at_utc": "2026-01-25T10:07:00Z"
}
```

**Partition Key**: `case_version_id` (same as case_text)

**Rationale**: Enables structured faceted search without bloating `case` table.

---

## 8) Integrity Checks (Operational Rules)

### Enforceable Constraints

**Postgres Native**:
```sql
-- Exactly one current version per case
CREATE UNIQUE INDEX uq_case_one_current ON case_version(case_id) WHERE is_current = TRUE;
```

**Application-Enforced** (Cosmos DB has no foreign key constraints):

1. **No artifact without provenance**: 
   - `artifact.storage_uri NOT NULL` enforced by schema
   - Every artifact must reference a valid `case_version_id`

2. **No case_text pointing to wrong version**:
   - `case_text.text_source_artifact_id` must reference `artifact` with same `case_version_id`
   - Enforce with application logic or database triggers

3. **Version immutability**:
   - Once `case_version` is created, `version_seq` and `reason` cannot change
   - Only `is_current` can be updated (to invalidate old versions)

4. **Evidence chain integrity**:
   - If `case_version.created_by_poll_run_id` is NOT NULL, referenced `poll_run` must exist
   - If `case_version.created_by_change_event_id` is NOT NULL, referenced `change_event` must exist

5. **Scope enforcement**:
   - `poll_run.scope_id` must match a valid scope definition from `cdc/scopes/*.yaml`
   - All cases processed in that poll_run must be within scope

---

## 9) Schema Migration Path

### Phase 0: Bootstrap (Seed Corpus)
```sql
-- Create all tables
-- Insert reference data (tribunal, source_system)
-- Bulk insert from Accenture seed:
--   - case (with tribunal_id, decision_date, etc.)
--   - case_source_key (with source_system_id='accenture_seed')
--   - case_version (version_seq=1, reason='seed', created_by_poll_run_id=NULL)
--   - artifact (with artifact_type='json_seed' or 'pdf', source_system_id='accenture_seed')
--   - case_text (extracted from seed PDFs)
```

### Phase 1: CDC Activation
```sql
-- First poll_run:
--   - Poll CanLII metadata API
--   - Detect new cases (change_class='structural', signal='registry_new_case_id')
--   - Create change_event for each new case
--   - Create case_version (version_seq=1, reason='new_or_identity_change', created_by_poll_run_id=<poll_run_id>)
--   - Fetch artifacts, create artifact + case_text records
```

### Phase 2: Ongoing CDC
```sql
-- Subsequent poll_runs:
--   - Detect content changes (artifact hash drift)
--   - Create change_event + new case_version (version_seq increments)
--   - Mark old case_version.is_current=FALSE
--   - Create new artifact + case_text for changed content
```

---

## 10) Cosmos DB Container Configuration

**Recommended Settings** (Serverless for MVP):

```json
{
  "containers": [
    {
      "id": "case",
      "partitionKey": "/tribunal_id",
      "indexingPolicy": {
        "includedPaths": [{"path": "/*"}],
        "excludedPaths": [{"path": "/\"_etag\"/?"}]
      }
    },
    {
      "id": "case_version",
      "partitionKey": "/case_id",
      "indexingPolicy": {
        "compositeIndexes": [
          [
            {"path": "/case_id", "order": "ascending"},
            {"path": "/version_seq", "order": "ascending"}
          ],
          [
            {"path": "/case_id", "order": "ascending"},
            {"path": "/is_current", "order": "ascending"}
          ]
        ]
      }
    },
    {
      "id": "artifact",
      "partitionKey": "/case_version_id",
      "indexingPolicy": {
        "includedPaths": [
          {"path": "/content_hash/?"},
          {"path": "/artifact_type/?"},
          {"path": "/language/?"}
        ]
      }
    },
    {
      "id": "poll_run",
      "partitionKey": "/scope_id",
      "defaultTtl": -1
    },
    {
      "id": "change_event",
      "partitionKey": "/poll_run_id",
      "indexingPolicy": {
        "includedPaths": [
          {"path": "/change_class/?"},
          {"path": "/signal_id/?"},
          {"path": "/case_id/?"}
        ]
      }
    }
  ]
}
```

---

## 11) Corpus Registry (Multi-Corpus Management)

### corpus_registry

**Purpose**: Central registry for managing multiple jurisprudence corpora with SLO tracking and freshness metrics.

```sql
CREATE TABLE corpus_registry (
  corpus_id              TEXT PRIMARY KEY,            -- e.g., 'jp-jurisprudence', 'caselaw-fc-only'
  corpus_name            TEXT NOT NULL,               -- Human-readable name
  priority_tier          INTEGER NOT NULL,            -- 1=<1hr, 2=<24hr, 3=weekly
  search_index_name      TEXT NOT NULL,               -- Azure AI Search index name
  slo_config_json        TEXT NOT NULL,               -- JSON: { "max_staleness_hours": 1, "target_coverage_pct": 98 }
  
  -- Freshness tracking
  last_poll_completed_at_utc  TIMESTAMP,
  staleness_lag_seconds       INTEGER,                -- Time since newest case decision_date vs ingested_at
  coverage_pct                REAL,                   -- % of in-scope cases successfully indexed
  last_ingested_case_date     DATE,                   -- decision_date of most recently ingested case
  
  -- SLO violation alerting
  slo_violated_since_utc      TIMESTAMP,              -- NULL if SLO met, timestamp if violated
  last_alert_sent_at_utc      TIMESTAMP,
  
  -- Metadata
  created_at_utc              TIMESTAMP NOT NULL,
  updated_at_utc              TIMESTAMP NOT NULL,
  is_active                   BOOLEAN NOT NULL DEFAULT TRUE
);
```

**Example rows**:
```sql
INSERT INTO corpus_registry VALUES 
  (
    'jp-jurisprudence',
    'MS-InfoJP Jurisprudence Corpus',
    2,  -- Tier 2: <24hr freshness
    'index-jurisprudence',
    '{"max_staleness_hours": 24, "target_coverage_pct": 98.0, "alert_threshold_hours": 48}',
    '2026-01-28 06:00:00',
    14400,  -- 4 hours staleness lag
    97.8,
    '2026-01-27',
    NULL,  -- SLO currently met
    NULL,
    '2026-01-15 10:00:00',
    '2026-01-28 06:00:00',
    TRUE
  );
```

**Cosmos DB Mapping**:
```json
{
  "id": "jp-jurisprudence",
  "corpus_id": "jp-jurisprudence",
  "corpus_name": "MS-InfoJP Jurisprudence Corpus",
  "priority_tier": 2,
  "search_index_name": "index-jurisprudence",
  "slo_config": {
    "max_staleness_hours": 24,
    "target_coverage_pct": 98.0,
    "alert_threshold_hours": 48
  },
  "last_poll_completed_at_utc": "2026-01-28T06:00:00Z",
  "staleness_lag_seconds": 14400,
  "coverage_pct": 97.8,
  "last_ingested_case_date": "2026-01-27",
  "slo_violated_since_utc": null,
  "last_alert_sent_at_utc": null,
  "created_at_utc": "2026-01-15T10:00:00Z",
  "updated_at_utc": "2026-01-28T06:00:00Z",
  "is_active": true
}
```

**Partition Key**: `/corpus_id`  
**Indexing Policy**: Index on `priority_tier`, `is_active`, `slo_violated_since_utc` for monitoring queries

---

## 12) Example Queries

### Q1: Get current version of a case
```sql
SELECT cv.*
FROM case_version cv
WHERE cv.case_id = '01JGQP2VWXYZ...'
  AND cv.is_current = TRUE;
```

### Q2: Get all artifacts for current version
```sql
SELECT a.*
FROM case_version cv
JOIN artifact a ON a.case_version_id = cv.case_version_id
WHERE cv.case_id = '01JGQP2VWXYZ...'
  AND cv.is_current = TRUE;
```

### Q3: Get version history for a case
```sql
SELECT cv.version_seq, cv.detected_at_utc, cv.reason, 
       pr.scope_id, pr.started_at_utc
FROM case_version cv
LEFT JOIN poll_run pr ON pr.poll_run_id = cv.created_by_poll_run_id
WHERE cv.case_id = '01JGQP2VWXYZ...'
ORDER BY cv.version_seq;
```

### Q4: Answer "Why did we ingest this version?" (H2 test)
```sql
SELECT 
  cv.version_seq,
  cv.reason,
  ce.change_class,
  ce.signal_id,
  ce.previous_hash,
  ce.new_hash,
  ce.action_taken_json,
  pr.policy_version,
  pr.policy_hash,
  pr.started_at_utc
FROM case_version cv
JOIN change_event ce ON ce.change_event_id = cv.created_by_change_event_id
JOIN poll_run pr ON pr.poll_run_id = cv.created_by_poll_run_id
WHERE cv.case_version_id = '01JGQP5DEF...';
```

### Q5: Find all content changes in last 7 days
```sql
SELECT c.case_id, c.style_of_cause, ce.change_class, ce.signal_id, pr.started_at_utc
FROM change_event ce
JOIN poll_run pr ON pr.poll_run_id = ce.poll_run_id
JOIN "case" c ON c.case_id = ce.case_id
WHERE ce.change_class = 'content'
  AND pr.started_at_utc >= CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY pr.started_at_utc DESC;
```

### Q6: Scope enforcement report (A1 test)
```sql
SELECT 
  pr.poll_run_id,
  pr.scope_id,
  pr.started_at_utc,
  json_extract(pr.result_counts_json, '$.ignored_out_of_scope') as ignored_count
FROM poll_run pr
WHERE pr.scope_id = 'SST-GD-EN-rolling-24mo'
ORDER BY pr.started_at_utc DESC
LIMIT 10;
```

---

## References

- **Change Policy**: [change-policy.yaml](change-policy.yaml) - Classification rules referenced by poll_run
- **Acceptance Tests**: [acceptance-tests.md](acceptance-tests.md) - Test cases that validate this schema
- **Design Principles**: [../cdc-mvp-design.md](../cdc-mvp-design.md) - Architecture rationale
- **Implementation Guide**: [../cdc-mvp-artifacts.md](../cdc-mvp-artifacts.md) - Build deliverables

---

**Status**: Ready for implementation (Week 1-2)  
**Owner**: Development Team  
**Approval**: Required from DBA/Architect for Cosmos DB container design
