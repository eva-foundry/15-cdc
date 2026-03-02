# CDC MVP — Build-Ready Artifact Set

This is the **minimum complete set of artifacts** that must exist for CDC to be considered *real*, testable, and enforceable.

Think of this as **"what must exist in the repo / DB / backlog"**, not prose.

---

## 1️⃣ CDC Policy Pack (authoritative rules)

**Files / records that must exist**

* ✅ `cdc/change-policy.yaml` - **COMPLETED** (v0.1.0, 2026-01-25)
  - 8 change classes (structural → deleted)
  - 25+ signals (registry, HTTP, artifact, ops)
  - 13 classification rules (ordered, first-match wins)
  - 11 action types (minimal recompute)
  - Versioning rules, operational thresholds
* ⏳ `cdc/scope.yaml` - Scope definitions and validation
* ⏳ `cdc/immutability.yaml` - Polling frequency by source type
* ⏳ `cdc/language-policy.yaml` - EN/FR handling rules

### Acceptance criteria

* A scope_id can be **parsed** and validated
* Given an input change, the policy can answer:

  * *ignore*
  * *metadata-only*
  * *content-change*
* Policies are **referenced by poll_run**, not embedded in code

If a developer asks "what do we do when X changes?", the answer is **not in code**.

### Change Policy Details

The [change-policy.yaml](cdc/change-policy.yaml) defines:

**8 Change Classes**:
- `structural` - New/removed identifiers or key mappings changed
- `availability` - Language availability (EN/FR) or artifact presence changed
- `metadata_meaningful` - Metadata affecting retrieval/filtering/ranking
- `metadata_nonmeaningful` - Housekeeping metadata changes
- `content` - PDF bytes or extracted text drift
- `cosmetic` - Formatting/layout noise (no action)
- `unreachable` - Transient source failures
- `deleted` - Permanently removed cases

**25+ Signal Types** categorized by source:
- Registry signals (new_case_id, missing_case_id, metadata_hash_changed, etc.)
- HTTP observation (redirect, ETag, Last-Modified, content-length)
- Artifact signals (pdf_hash, text_hash, html_normalized_hash)
- Operational signals (unreachable, permanently_gone)

**13 Classification Rules** (ordered, first-match wins):
- R1: New case → structural
- R2: Missing case → deleted
- R3: External key changed → structural
- R4: Language set changed → availability
- R5-R6: Artifact presence changes → availability
- R7-R9: Content hash changes → content
- R10-R11: Metadata drift → metadata_meaningful/nonmeaningful
- R12: HTTP changes without content drift → cosmetic (no-op)
- R13: Source unreachable → unreachable (retry)
- R99: Default → cosmetic (no-op)

**11 Action Types**:
- update_registry, fetch_artifact, extract_text, generate_chunks, embed_chunks
- update_index, update_index_metadata_only, mark_withdrawn_or_deleted
- update_index_tombstone, record_failure, retry_with_backoff

**Key Policy Features**:
- **Idempotency**: Same inputs + same policy = same classification + same actions
- **Evidence required**: Every action must trace to a change_event
- **Prohibited triggers**: No raw HTML hashing, no full corpus re-embed/re-index
- **Minimal recompute**: Only changed artifacts/chunks/vectors are reprocessed

---

## 2️⃣ Case Registry (Output A)

**Concrete artifact**

* Table or dataset: `case`
* Table or dataset: `case_source_key`

### Acceptance criteria

* Every decision has:

  * exactly **one internal `case_id`**
  * ≥1 external key (CanLII, URL, seed)
* Registry can be rebuilt from:

  * stored registry snapshots
  * without re-downloading content
* Registry supports:

  * scope filtering
  * language availability queries
  * tribunal hierarchy queries

If registry rebuild requires scraping PDFs → ❌ not done.

---

## 3️⃣ Artifact Index (Output B)

**Concrete artifact**

* Table or dataset: `artifact`

### Acceptance criteria

* Every artifact row includes:

  * `artifact_type`
  * `source_system`
  * `content_hash` (or observation hash)
  * `retrieved_at`
  * `storage_uri`
* Artifact hashes are:

  * deterministic
  * idempotent across re-runs
* CDC decisions are made **from artifact metadata**, not downstream text

If artifact rows can't explain *why* content was reprocessed → ❌ not done.

---

## 4️⃣ CDC State & Evidence (Output D)

**Concrete artifacts**

* Table: `poll_run`
* Table: `change_event`

### Acceptance criteria

* Every CDC run creates **exactly one poll_run**
* Every downstream action maps to ≥1 change_event
* You can answer, using data only:

  * "what changed?"
  * "what triggered it?"
  * "what action happened?"
* Re-running a poll:

  * creates a new poll_run
  * does **not** duplicate artifacts or versions

If something re-embeds without a change_event → ❌ defect.

---

## 5️⃣ Versioning Model (case_version)

**Concrete artifact**

* Table: `case_version`

### Acceptance criteria

* A case_version is created **only** when policy says "meaningful change"
* Prior versions are retained
* Exactly one version is `is_current = true`
* Version creation references:

  * poll_run_id
  * change_event_id(s)

If content is overwritten in place → ❌ not CDC.

---

## 6️⃣ Language Outputs (hard requirement)

**Concrete artifacts**

* `case_text` (EN)
* `case_text` (FR)

### Acceptance criteria

* EN and FR are **separate records**
* Bilingual artifacts result in:

  * split texts **or**
  * language-tagged chunks
* No chunk exists without an explicit language label

Mixed-language chunks without tagging → ❌ retrieval poison.

---

## 7️⃣ Downstream Contract (RAG-facing)

**Status**: ✅ **COMPLETE** - Specification documented in [cdc/downstream-invalidation-contract.md](cdc/downstream-invalidation-contract.md)

**Concrete artifact**

* `cdc/downstream-invalidation-contract.md` - Authoritative downstream processing rules

Defines strict, enforceable rules for what downstream work is allowed when CDC detects change.

**Key specifications**:
- 11 canonical action names (`update_registry`, `fetch_artifact`, `extract_text`, etc.)
- Change-class → allowed actions mapping (8 classes)
- Delta processing rules at 4 levels (artifact, text, chunk, index)
- Cost guardrails (per-run budgets, rate limits)
- Evidence requirements (all actions logged in `change_event.action_taken_json`)
- Forbidden operations (no corpus-wide rebuilds, no silent work)
- Python implementation example

### Acceptance criteria

✅ No full re-index allowed  
✅ No full re-embed allowed  
✅ Changed case_id → changed chunks → changed vectors only  
✅ All actions recorded in evidence chain  
✅ Delta processing rules enforced at all levels  

If "just re-run everything" exists anywhere → ❌.

---

## 8️⃣ Bootstrap Cutover Record (Day-0)

**Concrete artifact**

* `cdc/bootstrap.json`

### Acceptance criteria

* Every seeded case has:

  * case_version = 1
  * reason = seed
* After cutover timestamp:

  * only CDC can create new versions
* Seed artifacts are clearly marked and traceable

If seed vs CDC provenance is mixed → ❌ audit failure.

---

## 9️⃣ Operational Guardrails (not exec, still mandatory)

**Concrete artifacts**

* `cdc/scopes/` directory (one file per scope_id)
* `cdc/runbook.md` (engineer-facing)
* `cdc/metrics.json`

### Acceptance criteria

* CDC runs can be replayed by scope_id
* Backoff / quarantine rules are explicit
* Metrics exist for:

  * cases checked
  * cases changed
  * false positives
  * cost per delta

No metrics → CDC is a belief system.

---

## 🔟 Hard Stop Tests (binary, no debate)

**Full Specification**: See [cdc/acceptance-tests.md](cdc/acceptance-tests.md) for complete 26 Given/When/Then test cases.

**Test Coverage**: 26 automated tests across 11 categories:
- **Scope & Reproducibility** (3 tests) - Audit trail, determinism
- **Registry & Identity** (3 tests) - Case discovery, identity management
- **Artifact & Content Change** (4 tests) - Content accuracy, embedding quality
- **Metadata Change** (2 tests) - Search relevance, cost control
- **Cosmetic HTML Noise** (2 tests) - Cost control, noise rejection
- **Language Rules** (2 tests) - Bilingual search, chunk tagging
- **Versioning & Retention** (2 tests) - Audit compliance, provenance
- **Evidence (ATO)** (2 tests) - ATO compliance, auditability
- **Minimal Recompute** (2 tests) - Cost control, performance
- **Failures & Quarantine** (2 tests) - Resilience, error handling
- **Bootstrap** (2 tests) - Migration integrity, provenance

**Critical MVP Completion Criteria**:

CDC MVP is **NOT DONE** if any of these are true:

* A case changed but no version exists
* A version exists but no change_event exists
* Content was re-embedded without a content hash change
* Language handling is implicit or inferred
* Someone says "we can't tell why this ran"

CDC MVP **IS DONE** when:

> You can delete the index, rebuild downstream, and still explain every single decision the system ever made.

**Hard Stop**: All 26 acceptance tests in [cdc/acceptance-tests.md](cdc/acceptance-tests.md) must pass before production deployment.

---

## MS-InfoJP Implementation Mapping

### Azure Cosmos DB Schema

**Full Specification**: See [cdc/minimal-schema-ddl.md](cdc/minimal-schema-ddl.md) for complete DDL with Cosmos DB mappings.

**Container: `cdc_state`** (11 tables/collections)

| Collection | Purpose | Key Fields | Partition Key |
|------------|---------|-----------|---------------|
| `tribunal` | Reference data | `tribunal_id`, `name_en`, `court_level` | `tribunal_id` |
| `source_system` | Provenance tracking | `source_system_id`, `source_type`, `trust_rank` | `source_system_id` |
| `case` | Case Registry | `case_id`, `tribunal`, `decision_date`, `is_current` | `tribunal_id` |
| `case_source_key` | External key mapping | `case_id`, `source_system`, `external_id` | `source_system_id` |
| `artifact` | Artifact Index | `artifact_id`, `case_id`, `content_hash`, `storage_uri` | `case_version_id` |
| `case_version` | Version tracking | `case_id`, `version`, `is_current`, `poll_run_id` | `case_id` |
| `case_text` | Language-specific text | `case_id`, `version`, `language`, `text_hash` | `case_version_id` |
| `case_metadata` | Enriched metadata | `case_version_id`, `key`, `value_json`, `method` | `case_version_id` |
| `poll_run` | CDC execution log | `poll_run_id`, `scope_id`, `started_at`, `cases_checked` | `scope_id` |
| `change_event` | Change audit trail | `event_id`, `poll_run_id`, `case_id`, `change_type`, `action_taken` | `poll_run_id` |

**Partition key rationale**:
- `case`: By `tribunal_id` - enables scoped queries ("all SST-GD cases")
- `poll_run`: By `scope_id` - all polls for a scope in same partition
- `change_event`: By `poll_run_id` - all changes from one poll together
- `artifact`, `case_text`, `case_metadata`: By `case_version_id` - all data for one version co-located

### Azure Blob Storage Structure

```
/cdc
  /policy
    scope.yaml
    change-policy.yaml
    immutability.yaml
    language-policy.yaml
    downstream-actions.yaml
  /scopes
    SST-GD-EN-rolling-24mo.yaml
    SST-AD-FR-2020-2023.yaml
  /bootstrap
    bootstrap.json
  /metrics
    metrics.json
  /operations
    runbook.md

/documents
  /raw-artifacts
    /{tribunal}/{year}/{case_id}.pdf
    /{tribunal}/{year}/{case_id}_EN.pdf
    /{tribunal}/{year}/{case_id}_FR.pdf
```

### Phase 1 MVP Deliverables

**Week 1 - Policy & Schema**:
- [x] Create `cdc/` directory structure in blob storage ✅
- [x] Define Cosmos DB collections with schemas ✅ (see [cdc/minimal-schema-ddl.md](cdc/minimal-schema-ddl.md))
- [ ] Write `scope.yaml` for `SST-GD-EN-rolling-24mo`
- [x] Write `change-policy.yaml` with MVP rules ✅
- [ ] Write `language-policy.yaml` for EN/FR handling
- [x] Write `acceptance-tests.md` with 26 Given/When/Then tests ✅

**Week 2 - Core Implementation**:
- [ ] Implement Case Registry (read/write to Cosmos DB)
- [ ] Implement Artifact Index (hash tracking)
- [ ] Implement `poll_run` and `change_event` creation
- [ ] Implement `case_version` management

**Week 3 - Integration & Testing**:
- [ ] Connect CDC to existing ingestion pipeline
- [ ] Implement downstream invalidation (delta-only)
- [ ] Test Day-0 bootstrap from existing corpus
- [ ] Validate Hard Stop Tests pass

---

## Phase 2+ — Operations & Admin Control Plane

**Feature Specification**: See [cdc/operations-admin-control-plane.md](cdc/operations-admin-control-plane.md) for complete design.

**Key Capabilities**:
- **Client Reporting**: "What changed?" dashboards with drilldown to evidence
- **Admin Panel**: Manage scopes, thresholds, and manual operations
- **Monitoring**: Health dashboards (success rate, cost per delta, failure analytics)
- **Audit Trail**: ATO-friendly config change history and operator action logs
- **RBAC**: Client Viewer, CDC Operator, CDC Admin, Auditor roles

**Implementation Slices**:
1. **Slice 1** (2-3 weeks): Read-only reporting (poll_run lists, change_event drilldown)
2. **Slice 2** (3-4 weeks): Admin config UI (scope management, threshold editing)
3. **Slice 3** (4-5 weeks): Full monitoring + FinOps (cost analytics, notifications)

**Schema Additions**:
- `scope_config_version` table - Config change audit trail
- `operator_action_log` table - Manual operation tracking

**Critical Design Decision**: All evidence fields (policy_version, signal_id, action_taken_json) must be in place for UI to be "queries + UI" (no complex logic).

---

### Acceptance Test Suite

```python
# cdc/tests/test_hard_stops.py

def test_version_without_change_event_fails():
    """Every case_version must have a change_event."""
    versions = db.query("SELECT * FROM case_version WHERE version > 1")
    for v in versions:
        events = db.query(f"SELECT * FROM change_event WHERE case_id = '{v.case_id}' AND case_version = {v.version}")
        assert len(events) > 0, f"Version {v.version} has no change_event"

def test_reembed_without_hash_change_fails():
    """No re-embed without content hash change."""
    embeddings = db.query("SELECT * FROM embeddings WHERE created_at > BOOTSTRAP_CUTOVER")
    for e in embeddings:
        change_events = db.query(f"SELECT * FROM change_event WHERE case_id = '{e.case_id}' AND action_taken LIKE '%embed%'")
        assert len(change_events) > 0, f"Re-embed without change_event: {e.case_id}"
        
        # Verify hash changed
        for event in change_events:
            assert event.prev_hash != event.new_hash, f"Re-embed without hash change: {e.case_id}"

def test_language_tagging_complete():
    """All chunks have explicit language tags."""
    chunks = db.query("SELECT * FROM chunks WHERE language IS NULL OR language = ''")
    assert len(chunks) == 0, f"Found {len(chunks)} chunks without language tags"

def test_registry_rebuild_without_content():
    """Case Registry can be rebuilt from snapshots only."""
    # Simulate registry loss
    temp_db = create_temp_db()
    
    # Rebuild from poll_run snapshots
    rebuild_registry_from_snapshots(temp_db)
    
    # Verify completeness
    original_count = db.query("SELECT COUNT(*) FROM case").fetchone()[0]
    rebuilt_count = temp_db.query("SELECT COUNT(*) FROM case").fetchone()[0]
    assert original_count == rebuilt_count, "Registry rebuild incomplete"

def test_downstream_delta_only():
    """Verify no full re-index after change."""
    # Trigger change for single case
    change_event = trigger_test_case_change("TEST-CASE-001")
    
    # Verify only that case was reprocessed
    reprocessed = db.query(f"SELECT * FROM processing_log WHERE timestamp > '{change_event.timestamp}'")
    reprocessed_cases = set(r.case_id for r in reprocessed)
    
    assert reprocessed_cases == {"TEST-CASE-001"}, f"Full reprocess detected: {reprocessed_cases}"
```

### Definition of Done Checklist

- [ ] **Policy Pack exists**: All 4 YAML files committed to blob storage
- [ ] **Case Registry operational**: Can query by scope_id, tribunal, language
- [ ] **Artifact Index operational**: Hash-based drift detection working
- [ ] **Evidence trail complete**: Every change has poll_run + change_event
- [ ] **Versioning correct**: case_version only created on meaningful change
- [ ] **Language separation enforced**: No mixed-language chunks
- [ ] **Downstream contract enforced**: Delta-only recompute validated
- [ ] **Bootstrap documented**: Day-0 cutover timestamp recorded
- [ ] **Metrics exist**: Cost per delta, false positive rate tracked
- [ ] **Hard Stop Tests pass**: All 5 acceptance tests green

### Related Documentation

- [CDC MVP Design](cdc-mvp-design.md) - Comprehensive principles and policies
- [README](README.md) - Overall project goals and phases
- [Phase 1 Implementation Plan](README.md#phase-1-jp-ingestion-pipeline-weeks-2-3) - Integration roadmap
