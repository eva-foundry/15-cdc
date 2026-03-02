# Downstream Invalidation Contract (CDC → RAG Pipeline)

**Purpose**: Define strict, enforceable rules for what downstream work is allowed when CDC detects change. This is the "minimal recompute" contract that prevents full re-embed/re-index waste and preserves auditability.

**Version**: 1.0.0  
**Last Updated**: 2026-01-25  
**Status**: Authoritative specification for implementation

---

## Scope

**Applies to**:
- After CDC classification (`change_class`) and versioning (`case_version`)
- All consumers (EVA DA, MS PubSec-Info-Assistant, any RAG indexer)
- CanLII API is metadata-only; content-bearing artifacts come from blob and/or mirrored web artifacts

**Key principle**: CDC triggers **delta processing only**:
- Only changed artifacts
- Only changed texts
- Only changed chunks
- Only affected vectors/index entries

---

## 1) Vocabulary (Canonical Action Names)

**Downstream actions** (must match `action_taken` vocabulary in `change_event`):

| Action | Purpose |
|--------|---------|
| `update_registry` | Update case registry metadata |
| `fetch_artifact` | Download/retrieve artifact (PDF/HTML) |
| `extract_text` | Extract text from artifact |
| `generate_chunks` | Chunk extracted text for embedding |
| `embed_chunks` | Generate vector embeddings for chunks |
| `update_index` | Full index update (metadata + vectors) |
| `update_index_metadata_only` | Metadata-only index update (no vectors) |
| `mark_withdrawn_or_deleted` | Mark case as withdrawn in registry |
| `update_index_tombstone` | Update index with deletion marker |
| `record_failure` | Log failure for retry |
| `retry_with_backoff` | Retry failed operation with backoff |

**Hard rule**: Every executed downstream action **MUST** be recorded in `change_event.action_taken_json`. No "silent work".

---

## 2) Inputs and Outputs (Contracts)

### Inputs to Downstream Processing

```json
{
  "case_id": "01JGQP2VWXYZ...",
  "case_version_id": "01JGQP5DEF...",
  "artifact_ids": ["01JGQP6ABC..."],
  "language": "EN",
  "reason": "content_change",
  "change_class": "content",
  "policy_id": "change-policy",
  "policy_version": "0.1.0",
  "poll_run_id": "01JGQP8ABC..."
}
```

### Outputs of Downstream Processing

- **case_text records** (EN/FR) with `normalized_text_hash` + `text_uri`
- **Chunk records** (conceptual; may be stored in DB or generated on-the-fly)
- **Embeddings/vectors** for changed chunks only
- **Index update records** for affected docs/vectors only
- **Evidence**: Updated `change_event.status` (`executed`/`failed`) + counts

---

## 3) Change-Class → Allowed Downstream Actions

### 3.1 Structural (new case, identity mapping change, canonical URL drift)

**Allowed actions**:
- `update_registry`
- `fetch_artifact` (if needed)
- `extract_text`
- `generate_chunks`
- `embed_chunks`
- `update_index`

**Required**:
- Create new `case_version` (`is_current=true`)
- Do NOT delete prior versions

**Forbidden**:
- ❌ Corpus-wide rebuild
- ❌ Reprocessing other cases in the scope

---

### 3.2 Availability (language availability changed; artifact missing/new)

**Allowed actions**:
- `update_registry` (if language set changes)
- `fetch_artifact` (for missing/new artifacts)
- `extract_text` (for newly available language)
- `generate_chunks` / `embed_chunks` / `update_index` (for affected language only)

**Required**:
- New `case_version` when language set changes OR a new artifact materially changes what can be retrieved

**Forbidden**:
- ❌ Reprocessing unchanged language streams for the same case unless policy explicitly says so

---

### 3.3 Metadata_meaningful (retrieval/citation-impacting fields changed)

**Allowed actions**:
- `update_registry`
- `update_index_metadata_only`

**Required**:
- New `case_version` (traceability for "what did we know when")

**Forbidden**:
- ❌ `extract_text`, `generate_chunks`, `embed_chunks`, `update_index` (full) unless content hashes changed

---

### 3.4 Metadata_nonmeaningful (housekeeping fields only)

**Allowed actions**:
- `update_registry`

**Required**:
- **No** new `case_version`

**Forbidden**:
- ❌ Any content pipeline actions

---

### 3.5 Content (PDF bytes drift, extracted text drift, normalized content drift)

**Allowed actions**:
- `extract_text` (if artifact changed)
- `generate_chunks`
- `embed_chunks`
- `update_index`

**Required**:
- New `case_version`
- Delta-only processing (see Section 4)

**Forbidden**:
- ❌ Full corpus re-embed/re-index

---

### 3.6 Cosmetic (HTML noise only, no normalized content change)

**Allowed actions**:
- None (or record cosmetic count in `poll_run`)

**Required**:
- **No** `case_version`

**Forbidden**:
- ❌ Any downstream processing

---

### 3.7 Unreachable (transient failures)

**Allowed actions**:
- `record_failure`
- `retry_with_backoff`

**Required**:
- **No** `case_version` unless threshold later promotes to `deleted`

**Forbidden**:
- ❌ Marking deleted on first failure

---

### 3.8 Deleted (permanently gone / withdrawn)

**Allowed actions**:
- `mark_withdrawn_or_deleted`
- `update_index_tombstone`

**Required**:
- New `case_version` (`reason=deleted_or_withdrawn`)
- Retrieval must prefer not to surface deleted as active

**Forbidden**:
- ❌ Deleting evidence, artifacts, or prior versions prematurely (retention rules apply)

---

## 4) Delta Processing Rules (Minimal Recompute)

### 4.1 Artifact-level delta

**IF** artifact `content_hash` changes (pdf/html/text):  
**THEN** only that artifact's dependent outputs are eligible to change.

- Changed PDF → re-extract text for that language
- Changed extracted text → re-chunk for that language
- Changed chunks → re-embed those chunks
- Changed embeddings → update index entries for those vectors

**Example**:
```python
if artifact.content_hash != previous_artifact.content_hash:
    extract_text(artifact_id, language)
    generate_chunks(case_text_id)
    embed_chunks(chunk_ids)
    update_index(case_version_id, language)
```

---

### 4.2 Text-level delta

**IF** `normalized_text_hash` unchanged:  
**THEN** chunking and embedding **MUST NOT** run for that language.

**Example**:
```python
if case_text.normalized_text_hash == previous_case_text.normalized_text_hash:
    # Skip chunking and embedding
    log.info(f"Text unchanged for {case_text_id}, skipping downstream")
    return
```

---

### 4.3 Chunk-level delta

**IF** chunk boundaries/content change:  
**THEN** only changed chunks are re-embedded.

Unchanged chunks retain prior embeddings/vector ids (or equivalent stable identity).

**Example**:
```python
# Compute chunk diffs
new_chunks = generate_chunks(case_text)
changed_chunks = [c for c in new_chunks if c.hash not in old_chunk_hashes]

# Only embed changed chunks
embed_chunks(changed_chunks)
update_index(changed_chunks, case_version_id)
```

---

### 4.4 Index-level delta

Index updates must be scoped to:
- `case_version_id` (new or updated)
- Affected language
- Affected chunk ids/vectors only

**No** "drop and rebuild index" unless explicitly authorized as a recovery event.

**Example**:
```python
# Update index for specific case version and language
update_index(
    case_version_id="01JGQP5DEF...",
    language="EN",
    chunk_ids=["chunk_001", "chunk_045", "chunk_127"]
)
```

---

## 5) Identity & Versioning Rules (Critical for Traceability)

### 5.1 Versioned documents

Each indexed unit must carry:
- `case_id`
- `case_version_id`
- `language`
- `tribunal_id`
- `decision_date`
- `canonical_url` (if applicable)
- Provenance pointers (`artifact_id`, `retrieved_at`)

**Example indexed document**:
```json
{
  "id": "chunk_001_v2",
  "case_id": "01JGQP2VWXYZ...",
  "case_version_id": "01JGQP5DEF...",
  "version_seq": 2,
  "language": "EN",
  "tribunal_id": "SST-GD",
  "decision_date": "2020-03-15",
  "canonical_url": "https://www.canlii.org/en/ca/sst/doc/2020/2020sst123/2020sst123.html",
  "artifact_id": "01JGQP6ABC...",
  "retrieved_at": "2026-01-25T10:00:00Z",
  "chunk_text": "...",
  "chunk_embedding": [0.123, 0.456, ...]
}
```

---

### 5.2 Current vs historical

Retrieval must default to:
- `is_current = true` `case_version` only

**BUT** must allow:
- Audit queries to retrieve prior versions

**Example query**:
```sql
-- Default retrieval (current versions only)
SELECT * FROM indexed_documents WHERE case_id = '...' AND is_current = true;

-- Audit query (all versions)
SELECT * FROM indexed_documents WHERE case_id = '...' ORDER BY version_seq;
```

---

### 5.3 Never overwrite in place

No downstream stage may overwrite prior version artifacts/text/vectors without creating a new `case_version`.

**Rationale**: Ensures auditability - "What did the system know on 2026-01-20?" must be answerable.

---

## 6) Evidence & Audit Requirements

### 6.1 Mandatory links

For every executed change:
- `poll_run` exists
- `change_event` exists
- `case_version` exists (when `change_class` requires it)
- Artifacts and `case_text` records can be traced by foreign keys or URIs

**Validation query**:
```sql
-- Verify evidence chain integrity
SELECT 
  cv.case_version_id,
  cv.created_by_poll_run_id,
  cv.created_by_change_event_id,
  pr.poll_run_id,
  ce.change_event_id
FROM case_version cv
LEFT JOIN poll_run pr ON pr.poll_run_id = cv.created_by_poll_run_id
LEFT JOIN change_event ce ON ce.change_event_id = cv.created_by_change_event_id
WHERE cv.created_by_poll_run_id IS NOT NULL
  AND (pr.poll_run_id IS NULL OR ce.change_event_id IS NULL);
-- Should return 0 rows (no broken links)
```

---

### 6.2 Action trace

- `change_event.action_taken_json` must list exactly what ran
- `change_event.status` must be updated to `executed` or `failed`
- Failures must record error category and retry plan

**Example**:
```json
{
  "change_event_id": "01JGQP9ABC...",
  "case_id": "01JGQP2VWXYZ...",
  "change_class": "content",
  "action_taken_json": "[\"extract_text\",\"generate_chunks\",\"embed_chunks\",\"update_index\"]",
  "status": "executed",
  "notes": "Successfully processed EN PDF hash change"
}
```

---

### 6.3 Replay support

**Given**:
- `poll_run_id`
- `policy_hash`
- `scope_id`
- Referenced artifacts

**The system must be able to reproduce the same downstream outcomes** (or explain why not).

**Replay workflow**:
```python
def replay_poll_run(poll_run_id):
    poll_run = get_poll_run(poll_run_id)
    policy = load_policy(poll_run.policy_version, poll_run.policy_hash)
    
    for change_event in get_change_events(poll_run_id):
        # Validate artifacts still exist
        artifacts = get_artifacts(change_event.case_id)
        
        # Re-execute actions
        for action in change_event.action_taken_json:
            execute_action(action, change_event, artifacts, policy)
```

---

## 7) Cost Guardrails (FinOps-Friendly)

### 7.1 Per-run budgets (optional but recommended)

A run may enforce:
- Max artifacts fetched
- Max bytes fetched
- Max embeddings generated

**When exceeded**:
- Stop and record partial completion in `poll_run`
- Do **NOT** silently continue

**Example**:
```python
MAX_EMBEDDINGS_PER_RUN = 5000
embeddings_generated = 0

for change_event in poll_run_changes:
    if embeddings_generated >= MAX_EMBEDDINGS_PER_RUN:
        poll_run.status = "partial_completion"
        poll_run.notes = f"Budget exceeded: {embeddings_generated} embeddings generated"
        break
    
    chunks = generate_chunks(change_event)
    embed_chunks(chunks)
    embeddings_generated += len(chunks)
```

---

### 7.2 Rate limits per source

Honor source limits (e.g., CanLII API constraints: **60 req/min**) via configured caps.

Record any throttling/backoff in `poll_run` metrics.

**Example**:
```python
# CanLII API rate limiter
rate_limiter = RateLimiter(max_requests=60, per_seconds=60)

for artifact_url in artifacts_to_fetch:
    with rate_limiter:
        fetch_artifact(artifact_url)
    
    if rate_limiter.throttled:
        poll_run.metrics["throttled_requests"] += 1
```

---

## 8) Explicitly Forbidden Operations (Hard Stops)

❌ **NEVER**:
- Re-embedding the entire corpus "to be safe"
- Rebuilding the entire index on routine CDC runs
- Using raw HTML hash as the only content change signal
- Creating `case_versions` without `change_event` evidence
- Running downstream actions without recording them in `change_event`
- Mixing EN/FR chunks without explicit language tagging
- Deleting evidence logs or prior versions as part of routine processing

**Enforcement**: These operations should be **rejected at runtime** with policy violation errors.

---

## 9) Acceptance Criteria (Binary)

This contract is satisfied when:

✅ **Scoped processing**: Any single-case change results in downstream actions limited to that case and affected language only

✅ **No silent work**: No action executes without a recorded `change_event`

✅ **No full rebuilds**: No full corpus rebuild actions occur during routine operations

✅ **Version retention**: Retrieval can prefer `is_current` versions while retaining audit access to older versions

✅ **Transparency**: Operators can answer "what changed, why, what ran, what did it cost" for any `poll_run`

---

## 10) Implementation Example (Python)

```python
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class DownstreamAction:
    change_class: str
    case_id: str
    case_version_id: str
    artifact_ids: List[str]
    language: str
    
    def execute(self, change_event_id: str):
        """Execute downstream actions based on change class"""
        actions_executed = []
        
        if self.change_class == "structural":
            actions_executed.extend([
                self.update_registry(),
                self.fetch_artifact(),
                self.extract_text(),
                self.generate_chunks(),
                self.embed_chunks(),
                self.update_index()
            ])
        
        elif self.change_class == "availability":
            actions_executed.extend([
                self.update_registry(),
                self.fetch_artifact(),
                self.extract_text(),
                self.generate_chunks(),
                self.embed_chunks(),
                self.update_index()
            ])
        
        elif self.change_class == "metadata_meaningful":
            actions_executed.extend([
                self.update_registry(),
                self.update_index_metadata_only()
            ])
        
        elif self.change_class == "metadata_nonmeaningful":
            actions_executed.append(self.update_registry())
        
        elif self.change_class == "content":
            actions_executed.extend([
                self.extract_text(),
                self.generate_chunks(),
                self.embed_chunks(),
                self.update_index()
            ])
        
        elif self.change_class == "cosmetic":
            # No-op
            pass
        
        elif self.change_class == "unreachable":
            actions_executed.extend([
                self.record_failure(),
                self.retry_with_backoff()
            ])
        
        elif self.change_class == "deleted":
            actions_executed.extend([
                self.mark_withdrawn_or_deleted(),
                self.update_index_tombstone()
            ])
        
        # Record actions in change_event
        self.record_actions(change_event_id, actions_executed)
        
        return actions_executed
    
    def update_registry(self) -> str:
        # Update case registry metadata
        return "update_registry"
    
    def fetch_artifact(self) -> str:
        # Fetch artifact from blob/mirror
        for artifact_id in self.artifact_ids:
            download_artifact(artifact_id, self.case_version_id)
        return "fetch_artifact"
    
    def extract_text(self) -> str:
        # Extract text for language
        extract_text_from_artifact(self.artifact_ids, self.language)
        return "extract_text"
    
    def generate_chunks(self) -> str:
        # Generate chunks (delta-only)
        chunks = chunk_text(self.case_version_id, self.language)
        return "generate_chunks"
    
    def embed_chunks(self) -> str:
        # Embed chunks (delta-only)
        chunks = get_changed_chunks(self.case_version_id, self.language)
        embeddings = generate_embeddings(chunks)
        return "embed_chunks"
    
    def update_index(self) -> str:
        # Update index (delta-only)
        update_search_index(self.case_version_id, self.language)
        return "update_index"
    
    def update_index_metadata_only(self) -> str:
        # Update metadata without vectors
        update_search_index_metadata(self.case_version_id)
        return "update_index_metadata_only"
    
    def mark_withdrawn_or_deleted(self) -> str:
        # Mark case as deleted in registry
        mark_case_deleted(self.case_id)
        return "mark_withdrawn_or_deleted"
    
    def update_index_tombstone(self) -> str:
        # Update index with tombstone
        update_search_index_tombstone(self.case_version_id)
        return "update_index_tombstone"
    
    def record_failure(self) -> str:
        # Log failure
        log_failure(self.case_id, self.artifact_ids)
        return "record_failure"
    
    def retry_with_backoff(self) -> str:
        # Schedule retry
        schedule_retry(self.case_id, self.artifact_ids)
        return "retry_with_backoff"
    
    def record_actions(self, change_event_id: str, actions: List[str]):
        """Record executed actions in change_event"""
        update_change_event(
            change_event_id,
            action_taken_json=json.dumps(actions),
            status="executed"
        )
```

---

## References

- **Change Policy**: [change-policy.yaml](change-policy.yaml) - Classification rules that determine allowed actions
- **Database Schema**: [minimal-schema-ddl.md](minimal-schema-ddl.md) - Schema for evidence tracking
- **Acceptance Tests**: [acceptance-tests.md](acceptance-tests.md) - Test cases for delta processing (I1, I2)
- **Design Principles**: [../cdc-mvp-design.md](../cdc-mvp-design.md) - Minimal recompute architecture

---

**Status**: Authoritative specification for implementation  
**Owner**: Development Team  
**Approval**: Required from Architecture Review Board before implementation
