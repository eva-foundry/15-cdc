# CDC MVP Design Principles

**Purpose**: Architecture principles and design decisions for MS-InfoJP Change Data Capture system.  
**Version**: 1.0.0  
**Last Updated**: 2026-01-28  
**Status**: Architecture foundation document

---

## Executive Summary

The MS-InfoJP CDC system maintains freshness in the jurisprudence RAG corpus by detecting changes in CanLII case metadata and artifacts, tracking versions with full provenance, and minimizing recompute through delta-only processing.

**Core Design Principles**:
1. **Two-Plane Architecture** - Separate data work from control/monitoring
2. **Policy-Driven Classification** - Rules in YAML, not code
3. **Minimal Recompute** - Only changed artifacts/chunks/vectors reprocessed
4. **Idempotent Replay** - Same inputs → same outputs (deterministic)
5. **Evidence-Based Audit** - Every action has change_event provenance

---

## Architecture Overview

### Two-Plane Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CONTROL PLANE                               │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │ Corpus Registry│  │ Policy Mgmt  │  │ CDC Ops Dashboard      │  │
│  │ - SLO tiers    │  │ - change-    │  │ - Run status           │  │
│  │ - Freshness    │  │   policy.yaml│  │ - Freshness lag        │  │
│  │   tracking     │  │ - scope.yaml │  │ - SLO violations       │  │
│  └────────────────┘  └──────────────┘  └────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           DATA PLANE                                 │
│                                                                       │
│  ┌──────────────┐     ┌────────────────┐     ┌──────────────────┐  │
│  │   DETECT     │ ──▶ │  CDC EVIDENCE  │ ──▶ │   DOWNSTREAM     │  │
│  │              │     │                │     │   PROCESSING     │  │
│  │ Tier 1 CDC:  │     │ • Case Registry│     │                  │  │
│  │ - Schedule   │     │ • Artifact     │     │ • Fetch artifact │  │
│  │   polling    │     │   Index        │     │ • Extract text   │  │
│  │ - CanLII API │     │ • poll_run     │     │ • Generate chunks│  │
│  │ - Metadata   │     │ • change_event │     │ • Embed chunks   │  │
│  │   hashing    │     │                │     │ • Update index   │  │
│  │              │     │ (Cosmos DB)    │     │                  │  │
│  └──────────────┘     └────────────────┘     └──────────────────┘  │
│                                                        │             │
│                                                        ▼             │
│                           ┌────────────────────────────────────┐    │
│                           │  FRESHNESS-AWARE RETRIEVAL         │    │
│                           │  • Azure AI Search                 │    │
│                           │  • Recency boost (365-day window)  │    │
│                           │  • source_last_modified scoring    │    │
│                           └────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

**Data Plane** (does the work):
- **Change Detection** → Scheduled polling of CanLII metadata, event-driven triggers (Phase 2)
- **CDC Evidence** → Case registry, artifact index, change events stored in Cosmos DB
- **Downstream Processing** → Extract, chunk, embed, index (delta only)
- **Freshness-Aware Retrieval** → Recency-boosted search queries

**Control Plane** (keeps it running):
- **Corpus Registry** → Multi-corpus management with SLO tiers
- **Policy Management** → Change classification rules, scope definitions
- **CDC Operations Dashboard** → Run status, freshness lag monitoring
- **Client Reporting** → What changed, why, freshness guarantees

---

## Design Principles

### 1. Policy-Driven Classification

**Principle**: All change classification rules live in YAML, not Python code.

**Rationale**:
- Non-developers (legal ops, compliance) can update rules
- Version-controlled policy changes with audit trail
- Every poll_run records `policy_version` and `policy_hash` for reproducibility
- No code redeployment needed for rule changes

**Implementation**:
- [change-policy.yaml](change-policy.yaml) defines 8 change classes
- [scope.yaml](scope.yaml) defines corpus boundaries
- [immutability.yaml](immutability.yaml) defines polling frequencies
- [language-policy.yaml](language-policy.yaml) defines EN/FR/BI handling

**Example**:
```yaml
# change-policy.yaml excerpt
change_classes:
  metadata_meaningful:
    description: Metadata changed that affects search/filtering
    signals:
      - tribunal_id
      - decision_date
      - neutral_citation
    downstream_actions:
      - update_index_metadata_only  # No re-embedding needed
```

---

### 2. Minimal Recompute

**Principle**: Only changed artifacts, chunks, and vectors are reprocessed.

**Rationale**:
- RAG corpus may have 100K+ cases (millions of chunks)
- Full recompute on every change is prohibitively expensive
- Embeddings API cost: $0.00002/1K tokens (text-embedding-3-small)
- Delta processing reduces cost by 95%+

**Techniques**:
1. **Content Hashing** - SHA-256 hash of PDF bytes, extracted text
2. **Chunk-Level Delta** - Only re-chunk/re-embed changed sections
3. **Metadata-Only Updates** - Index upsert without re-embedding
4. **Artifact Tracking** - `artifact` table prevents redundant downloads

**Implementation**:
```python
# Pseudocode from artifact_index.py
def track_artifact(case_version_id, artifact_type, content_bytes):
    content_hash = hashlib.sha256(content_bytes).hexdigest()
    
    existing = db.query(
        "SELECT artifact_id FROM artifact WHERE content_hash = ?",
        (content_hash,)
    )
    
    if existing:
        log.info(f"Content hash match - reusing artifact {existing.artifact_id}")
        return existing.artifact_id  # No re-processing needed
    
    # New content - trigger downstream pipeline
    artifact_id = upload_to_blob(content_bytes)
    create_change_event(change_class='content', action='extract_text')
    return artifact_id
```

**Cost Savings**:
- **Scenario**: 1000 cases, 10 change per day
- **Full recompute**: 1000 × 5000 tokens × $0.00002 = $1.00/day
- **Delta recompute**: 10 × 5000 tokens × $0.00002 = $0.001/day
- **Savings**: 99.9% reduction

---

### 3. Idempotent Replay

**Principle**: Replaying the same poll_run produces identical outputs.

**Rationale**:
- Debugging: "What happened on 2026-01-15 at 06:00 UTC?"
- Compliance: ATO requires reproducible audit trails
- Testing: Integration tests must be deterministic
- Recovery: Replay after partial failure

**Requirements**:
1. **Deterministic case_id** - Generated from (tribunal_id, decision_date, metadata)
2. **Deterministic scope_id** - Reproducible from (tribunal, language, time_window)
3. **Frozen policy** - poll_run records policy_hash and policy_version
4. **Timestamped snapshots** - CanLII metadata frozen at poll_run_start

**Implementation**:
```python
# Pseudocode from case_registry.py
def generate_case_id(tribunal_id, decision_date, metadata):
    # Deterministic UUID from stable inputs
    namespace = UUID('01JGQP0000000000000000000')  # Fixed namespace
    canonical = f"{tribunal_id}|{decision_date}|{metadata['neutral_citation']}"
    case_id = uuid5(namespace, canonical)
    return case_id
```

**Anti-Patterns** (Avoid):
- ❌ Random UUIDs (uuid4) - not reproducible
- ❌ Auto-increment IDs - order-dependent
- ❌ Timestamp-based IDs - not deterministic on replay

---

### 4. Evidence-Based Audit

**Principle**: Every downstream action has a change_event with provenance.

**Rationale**:
- ATO compliance requires "why did we ingest this?" answers
- Security teams need full audit trail
- Debugging: trace back from chunk → change_event → poll_run → policy
- No "silent work" - everything logged

**Schema Design**:
```sql
-- Every change_event includes full provenance
CREATE TABLE change_event (
  change_event_id        TEXT PRIMARY KEY,
  poll_run_id            TEXT NOT NULL,       -- Which CDC run?
  case_id                TEXT NOT NULL,       -- Which case?
  change_class           TEXT NOT NULL,       -- Why classified this way?
  signal_id              TEXT NOT NULL,       -- What triggered change?
  previous_hash          TEXT,                -- Before state
  new_hash               TEXT,                -- After state
  action_taken_json      TEXT,                -- What did we do?
  created_at_utc         TIMESTAMP NOT NULL
);

-- Poll_run records policy used
CREATE TABLE poll_run (
  poll_run_id            TEXT PRIMARY KEY,
  scope_id               TEXT NOT NULL,
  policy_version         TEXT NOT NULL,       -- e.g., "0.1.0"
  policy_hash            TEXT NOT NULL,       -- SHA-256 of change-policy.yaml
  started_at_utc         TIMESTAMP NOT NULL,
  completed_at_utc       TIMESTAMP,
  result_counts_json     TEXT
);
```

**Query Example** (Acceptance Test H2):
```sql
-- "Why did we ingest version 3 of case X?"
SELECT 
  cv.version_seq,
  ce.change_class,
  ce.signal_id,
  ce.action_taken_json,
  pr.policy_version,
  pr.started_at_utc
FROM case_version cv
JOIN change_event ce ON ce.change_event_id = cv.created_by_change_event_id
JOIN poll_run pr ON pr.poll_run_id = ce.poll_run_id
WHERE cv.case_version_id = '01JGQP5DEF...';

-- Result:
-- version_seq: 3
-- change_class: content
-- signal_id: pdf_content_hash
-- action_taken_json: ["extract_text", "generate_chunks", "embed_chunks", "update_index"]
-- policy_version: 0.1.0
-- started_at_utc: 2026-01-20 06:00:00
```

---

### 5. Tier 1 vs Tier 2 CDC Patterns

**Tier 1 CDC** (Phase 1 MVP):
- **Scheduled polling** - Daily at 2 AM UTC for mutable scopes, weekly for immutable
- **Batch processing** - All in-scope cases checked per run
- **Metadata-only** - CanLII API returns metadata (no content downloads)
- **Change detection** - Hash comparison: old metadata vs new metadata

**Tier 2 CDC** (Phase 2+):
- **Event-driven triggers** - CanLII webhook → Azure Event Grid → immediate processing
- **Single-case processing** - Only changed case processed
- **Real-time freshness** - <1 hour staleness for Tier 1 SLO corpora
- **Cost optimization** - No polling overhead for unchanged cases

**MVP Scope**:
- ✅ Tier 1 CDC for all scopes (Phase 1 Week 2)
- ⏳ Tier 2 CDC for selected high-priority corpora (Phase 2)

**Design Decision**: Start with Tier 1 for simplicity, validate architecture, then add Tier 2.

---

## Component Design

### Data Source: CanLII as Authoritative Source

**Decision**: CanLII API is the PRIMARY and AUTHORITATIVE source for jurisprudence metadata.

**Trust Hierarchy** (from source_system table):
1. **CanLII API** (trust_rank 95) - Authoritative metadata source
2. **Azure Blob Storage** (trust_rank 90) - Artifact storage
3. **Accenture Seed** (trust_rank 80) - Bootstrap corpus only

**Rationale**:
- CanLII maintains the canonical registry of Canadian legal decisions
- All tribunal/court decisions are published through CanLII
- CanLII API provides structured metadata (tribunal, decision_date, neutral_citation)
- Other sources (if added) are supplementary only

**Integration Point**:
- **API Endpoint**: `https://api.canlii.org/v1/caseBrowse`
- **Authentication**: API key in `CANLII_API_KEY` environment variable
- **API Key Source**: AICOE key (configured in backend.env and functions/local.settings.json)

**Note**: Previous references to "A2AJ" (Access to Justice) have been removed. A2AJ is NOT a source system for MS-InfoJP. CanLII is the sole authoritative source for jurisprudence data.

---

### Case Registry

**Purpose**: Maintain stable case identities across external key changes.

**Problem**: CanLII case URLs can change (e.g., `/2024sst100` → `/2024sst-100` formatting), but it's the same case.

**Solution**: Assign immutable `case_id` based on (tribunal_id, decision_date, neutral_citation).

**Key Methods**:
```python
class CaseRegistry:
    def register_case(self, tribunal_id, decision_date, external_keys, metadata):
        """
        Find existing case by external_keys, or create new case.
        Returns case_id (immutable).
        """
        
    def _find_by_external_key(self, external_keys):
        """Search case_source_key table for known URLs/IDs."""
        
    def _generate_case_id(self, tribunal_id, decision_date, metadata):
        """Deterministic UUID from canonical inputs."""
```

**Test Coverage**: B1, B2, B3 from [acceptance-tests.md](acceptance-tests.md)

---

### Artifact Index

**Purpose**: Track observed artifacts (PDF/HTML/text) with content hashes.

**Problem**: Same PDF may be downloaded multiple times if re-ingested. Avoid redundant blob storage.

**Solution**: Content-addressable storage - hash PDF bytes, check if already stored.

**Key Methods**:
```python
class ArtifactIndex:
    def track_artifact(self, case_version_id, artifact_type, content_bytes):
        """
        Compute content hash, check if artifact already exists.
        If new, upload to blob storage and create artifact record.
        Returns artifact_id.
        """
        
    def _compute_content_hash(self, content_bytes):
        """SHA-256 hash of raw bytes."""
        
    def _upload_to_blob(self, artifact_id, content_bytes, artifact_type):
        """Upload to Azure Blob Storage if not already present."""
```

**Test Coverage**: C1, C2, C3, C4 from [acceptance-tests.md](acceptance-tests.md)

---

### Corpus Registry

**Purpose**: Multi-corpus management with SLO tiers and freshness tracking.

**Problem**: MS-InfoJP will eventually manage 10+ corpora (SST, FC, FCA, SCC, provincial tribunals), each with different SLO guarantees.

**Solution**: `corpus_registry` table tracks SLO config, freshness metrics, alerting state.

**Key Methods**:
```python
class CorpusRegistry:
    def register_corpus(self, corpus_id, corpus_name, priority_tier, slo_config):
        """Create or update corpus configuration."""
        
    def track_freshness_metrics(self, corpus_id, poll_run):
        """
        Update staleness_lag_seconds, coverage_pct, last_ingested_case_date.
        Check for SLO violations.
        """
        
    def alert_on_slo_violations(self, corpus_id):
        """
        Send alert if staleness_lag > max_staleness_hours.
        Update slo_violated_since_utc timestamp.
        """
```

**Schema**:
```sql
CREATE TABLE corpus_registry (
  corpus_id                   TEXT PRIMARY KEY,
  corpus_name                 TEXT NOT NULL,
  priority_tier               INTEGER NOT NULL,
  search_index_name           TEXT NOT NULL,
  slo_config_json             TEXT NOT NULL,
  last_poll_completed_at_utc  TIMESTAMP,
  staleness_lag_seconds       INTEGER,
  coverage_pct                REAL,
  last_ingested_case_date     DATE,
  slo_violated_since_utc      TIMESTAMP,
  is_active                   BOOLEAN NOT NULL DEFAULT TRUE
);
```

**Test Coverage**: New (not in original 26 tests - add in Phase 1)

---

### Downstream Processor

**Purpose**: Execute downstream actions (fetch, extract, chunk, embed, index) based on change_class.

**Architecture**:
```python
class DownstreamProcessor:
    def process_change_event(self, change_event):
        """
        Read change_event.change_class, look up actions in change-policy.yaml.
        Execute actions: fetch_artifact → extract_text → generate_chunks → embed_chunks → update_index.
        """
        
    # 11 action handlers:
    def update_registry(self, case_id):
    def fetch_artifact(self, case_id, artifact_type):
    def extract_text(self, artifact_id):
    def generate_chunks(self, case_text_id):
    def embed_chunks(self, chunks):
    def update_index(self, case_version_id):
    def update_index_metadata_only(self, case_version_id):
    def mark_withdrawn_or_deleted(self, case_id):
    def update_index_tombstone(self, case_id):
    def record_failure(self, change_event_id, error):
    def retry_with_backoff(self, change_event_id):
```

**Integration Points**:
- **Existing Functions**: [TextEnrichment](../../functions/TextEnrichment/__init__.py), [FileFormRecSubmissionPDF](../../functions/FileFormRecSubmissionPDF/__init__.py)
- **Search Client**: From [shared_constants.py](../../app/backend/core/shared_constants.py)
- **Enrichment Service**: `ENRICHMENT_APPSERVICE_URL` from [backend.env](../../app/backend/backend.env)

**Test Coverage**: I1, I2, J1, J2 from [acceptance-tests.md](acceptance-tests.md)

---

## Key Design Decisions

### Decision 1: Cosmos DB over SQL Server

**Options Considered**:
1. Azure SQL Database (PaaS)
2. Azure Cosmos DB (NoSQL, serverless)
3. SQLite embedded (local dev only)

**Decision**: Cosmos DB Serverless

**Rationale**:
- **Native JSON support** - No schema migrations for change_event.action_taken_json
- **Serverless billing** - Pay per operation, not reserved capacity (cost-effective for MVP)
- **Existing pattern** - Info-Assistant already uses Cosmos DB for sessions/logs
- **No foreign keys** - Application-enforced referential integrity (acceptable for MVP)
- **Partition key design** - Natural CDC partitions: /scope_id for poll_run, /poll_run_id for change_event

**Trade-offs**:
- ✅ Pros: Lower MVP cost, faster iteration, JSON flexibility
- ❌ Cons: No foreign key constraints, eventual consistency (mitigated by Session consistency level)

---

### Decision 2: Scheduled Polling First, Event-Driven Later

**Options Considered**:
1. Tier 2 CDC only (event-driven via webhooks)
2. Tier 1 CDC only (scheduled polling)
3. Hybrid: Start with Tier 1, add Tier 2 in Phase 2

**Decision**: Hybrid (Tier 1 now, Tier 2 later)

**Rationale**:
- **CanLII webhook availability**: Unknown if CanLII provides webhooks (API docs don't mention)
- **Proof of concept**: Validate CDC architecture with simpler scheduled polling
- **Cost certainty**: Scheduled polling has predictable cost (N API calls/day)
- **Incremental complexity**: Add event-driven triggers after core CDC stable

**Implementation**:
- Phase 1: Azure Function timer trigger (daily 2 AM UTC)
- Phase 2: Azure Event Grid + CanLII webhooks (if available)

---

### Decision 3: Soft Delete Only (Phase 1)

**Options Considered**:
1. Hard delete immediately (purge from index)
2. Soft delete with `is_deleted=true` flag
3. Retention policy: soft delete + hard delete after N days

**Decision**: Soft delete only in Phase 1

**Rationale**:
- **ATO compliance** - Audit trail requires retention of deleted cases
- **"Show deleted" filter** - Operators can review withdrawn cases
- **Reversibility** - If case reinstated (rare but possible), easy to un-delete
- **Phase 2 retention** - Hard delete after 365-day retention policy

**Implementation**:
```python
# change-policy.yaml excerpt
deleted:
  downstream_actions:
    - mark_withdrawn_or_deleted  # Sets is_deleted=true in index
    # NOT: update_index_tombstone (hard delete) - Phase 2 only
```

---

### Decision 4: Language-Specific Embeddings

**Options Considered**:
1. Single embedding model for EN/FR (text-embedding-3-small supports 100+ languages)
2. Separate EN/FR embedding models
3. Translate FR → EN, embed in English only

**Decision**: Single multilingual model (text-embedding-3-small)

**Rationale**:
- **Cost**: One embedding API call per chunk (no translation step)
- **Quality**: text-embedding-3-small has strong FR performance per OpenAI benchmarks
- **Simplicity**: No separate embedding indexes for EN/FR
- **Bilingual search**: Users can query in either language

**Implementation**:
```yaml
# language-policy.yaml excerpt
embedding_strategy:
  model: text-embedding-3-small
  multilingual: true
  notes: |
    Model supports 100+ languages with strong FR performance.
    No translation needed for embedding generation.
```

**Disclaimer** (added to language-policy.yaml):
```yaml
assumptions:
  - text-embedding-3-small French performance assumed comparable to English
    (not independently verified in MS-InfoJP context)
```

---

### Decision 5: Immutability Classes Drive Polling Frequency

**Options Considered**:
1. Poll all tribunals daily (simple but expensive)
2. Poll based on SLO tier only (ignores immutability)
3. Poll based on immutability class (mutable=daily, immutable=weekly)

**Decision**: Immutability-driven with SLO override

**Rationale**:
- **Cost efficiency**: SCC (Supreme Court) publishes 50 decisions/year → weekly polling sufficient
- **Freshness**: SST-GD publishes 100+ decisions/day → daily polling required
- **SLO enforcement**: If SLO tier 1 (<1hr), override to hourly regardless of immutability

**Implementation**:
```yaml
# immutability.yaml excerpt
immutability_classes:
  mutable:
    tribunals: [SST-GD, SST-AD]
    polling_frequency: daily
  mostly_immutable:
    tribunals: [FC, FCA]
    polling_frequency: weekly
  fully_immutable:
    tribunals: [SCC]
    polling_frequency: monthly
    
# Override for SLO tier 1 corpora:
slo_overrides:
  tier_1:
    polling_frequency: hourly  # Even if SCC (tier 1 override)
```

---

## Testing Strategy

### Unit Tests
- `test_case_registry.py` - B1, B2, B3 scenarios
- `test_artifact_index.py` - C1, C2, C3, C4 scenarios
- `test_corpus_registry.py` - New (SLO tracking, alerting)
- `test_downstream_processor.py` - Action execution, retries

### Integration Tests
- `test_tier1_poller.py` - End-to-end CDC run (mock CanLII API)
- `test_change_classification.py` - Policy-driven classification
- `test_idempotent_replay.py` - A3 scenario (replay determinism)

### Acceptance Tests
- All 26 scenarios from [acceptance-tests.md](acceptance-tests.md)
- Categories: A) Scope, B) Registry, C) Artifacts, D) Metadata, E) Cosmetic, F) Language, G) Versioning, H) Evidence, I) Minimal Recompute, J) Failures, K) Bootstrap

**Hard Stop**: All 26 tests must pass before production deployment.

---

## Monitoring & Alerting

### Key Metrics (Phase 1)

1. **Freshness Lag** - Time between newest case decision_date and ingested_at
2. **SLO Compliance** - % of poll_runs completing within SLO window
3. **Change Detection Rate** - changes_detected / cases_polled ratio
4. **Downstream Success Rate** - % of change_events successfully processed
5. **Cost per CDC Run** - API calls + embeddings + storage cost

### Alerts (Phase 1)

1. **SLO Violation** - staleness_lag > max_staleness_hours
2. **Poll Run Failure** - poll_run.completed_at_utc = NULL after 30 min
3. **High Failure Rate** - >5% of change_events with action='record_failure'
4. **Cost Spike** - Embeddings cost >2x baseline

**Implementation**: Azure Monitor + Log Analytics + Action Groups

---

## Phase 2+ Roadmap

### Event-Driven CDC (Tier 2)
- CanLII webhook integration (if available)
- Azure Event Grid routing
- Single-case change processing
- <1 hour freshness for Tier 1 SLO

### Advanced Delete Detection
- Hard delete after retention period (365 days)
- Tombstone records in index
- Purge from blob storage

### Multi-Source CDC
- SharePoint document libraries
- Westlaw/LexisNexis integration
- Government gazette feeds

### Freshness Telemetry Dashboard
- Real-time staleness metrics
- Corpus health heatmap
- SLO compliance trends

---

## References

**Implementation Guide**: [CDC-IMPLEMENTATION-START.md](CDC-IMPLEMENTATION-START.md)  
**Schema Specification**: [minimal-schema-ddl.md](minimal-schema-ddl.md)  
**Policy Pack**: [change-policy.yaml](change-policy.yaml), [scope.yaml](scope.yaml), [immutability.yaml](immutability.yaml), [language-policy.yaml](language-policy.yaml)  
**Acceptance Tests**: [acceptance-tests.md](acceptance-tests.md)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2026-01-28 | Initial cdc-mvp-design.md with two-plane architecture, 5 design principles, 5 key decisions | Architecture Team |

---

**Status**: Architecture foundation complete ✅  
**Next Step**: Begin Week 1 implementation (Cosmos DB schema deployment)
