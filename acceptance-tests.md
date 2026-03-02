# CDC Acceptance Tests (Given / When / Then)

**Purpose**: Define non-negotiable behaviors for CDC polling in a jurisprudence RAG corpus.

**Scope**: CanLII metadata-only compatible; content-bearing surfaces are blob PDFs and/or mirrored HTML/PDF URLs.

**Version**: 1.0.0  
**Last Updated**: 2026-01-25  
**Status**: Authoritative specification for implementation

---

## Conventions

- **poll_run** = one CDC execution record (must always exist)
- **change_event** = one detected change record (must exist for any non-noop action)
- **case_version** = versioned case state; created only for meaningful change classes
- **scope_id** = partition key for reproducible runs (e.g., SST-EN-2018-2020)
- **artifact** = stored/observed item (pdf/html/text) with provenance + hashes
- **meaningful metadata** = fields that affect retrieval/filtering/citations (per metadata_fields.meaningful in change-policy.yaml)

---

## Test Categories

| Category | Tests | Critical For |
|----------|-------|--------------|
| [A) Scope & Reproducibility](#a-scope--reproducibility) | 3 | Audit trail, determinism |
| [B) Registry & Identity](#b-registry--identity-output-a) | 3 | Case discovery, identity management |
| [C) Artifact & Content Change](#c-artifact--content-change-output-b) | 4 | Content accuracy, embedding quality |
| [D) Metadata Change](#d-metadata-change-meaningful-vs-non-meaningful) | 2 | Search relevance, cost control |
| [E) Cosmetic HTML Noise](#e-cosmetic-html-noise-must-not-cause-ingestion) | 2 | Cost control, noise rejection |
| [F) Language Rules](#f-language-rules-enfr--bilingual-artifacts) | 2 | Bilingual search, chunk tagging |
| [G) Versioning & Retention](#g-versioning--retention) | 2 | Audit compliance, provenance |
| [H) Evidence](#h-evidence-ato-friendly) | 2 | ATO compliance, auditability |
| [I) Minimal Recompute](#i-minimal-recompute-rag-cost-control) | 2 | Cost control, performance |
| [J) Failures & Quarantine](#j-failures-backoff-quarantine) | 2 | Resilience, error handling |
| [K) Bootstrap](#k-bootstrap-day-0-cutover) | 2 | Migration integrity, provenance |
| **TOTAL** | **26** | **Production readiness** |

---

## A) Scope & Reproducibility

### A1. Scope enforcement (ignore out-of-scope)

**GIVEN** a CDC scope_id that includes only tribunal=SST and years=2018-2020  
**AND** a detected change for a case outside SST or outside 2018-2020  
**WHEN** CDC runs for that scope_id  
**THEN**:
- The out-of-scope change is **ignored**
- `poll_run` records `ignored_out_of_scope_count` >= 1
- **No** `change_event` is created for the out-of-scope case
- **No** downstream actions occur for the out-of-scope case

**Rationale**: Prevents "whole corpus" operations; enables scoped migrations and A/B testing.

---

### A2. Every run creates poll_run

**GIVEN** a valid scope_id definition  
**WHEN** CDC executes (even if nothing changes)  
**THEN**:
- Exactly **one** `poll_run` record is created
- `poll_run` contains `started_at`, `ended_at`, `scope_id`, and `result_counts`

**Rationale**: Evidence that CDC ran; absence of poll_run = monitoring gap.

---

### A3. Replay determinism

**GIVEN** the same scope_id and the same input snapshots (registry + artifact states)  
**WHEN** CDC runs twice  
**THEN**:
- Classification outcomes are **identical**
- Downstream actions are **identical**
- **No** duplicate artifacts, case_versions, or vectors are created

**Rationale**: Idempotency for disaster recovery and debugging.

---

## B) Registry & Identity (Output A)

### B1. New case appears in registry snapshot

**GIVEN** registry snapshot N does **not** contain external_key X  
**AND** registry snapshot N+1 **contains** external_key X  
**WHEN** CDC processes the registry diff  
**THEN**:
- CDC classifies the event as **STRUCTURAL** (new case)
- Creates `change_event(change_type=new)`
- Creates `case_version=1` with `reason="new_or_identity_change"`
- Queues/initiates **Tier-2 content acquisition** for that case (`fetch_artifact`)
- Downstream actions include: `extract` → `chunk` → `embed` → `index` (per policy)

**Rationale**: New cases must enter corpus automatically.

---

### B2. External key changes for existing case_id

**GIVEN** case_id C is mapped to external_key X  
**AND** a new registry snapshot maps case_id C to external_key Y  
**WHEN** CDC runs  
**THEN**:
- CDC classifies the event as **STRUCTURAL** (identity mapping change)
- Creates `change_event(change_type=modified, signal=registry_external_key_changed)`
- Creates a **new case_version** for case_id C (superseding prior)
- Does **NOT** delete prior versions
- Updates registry mappings with **full provenance**

**Rationale**: Identity changes require new version (citation drift risk).

---

### B3. Case disappears from registry snapshot

**GIVEN** registry snapshot N contains case_id C  
**AND** registry snapshot N+1 does **not** contain case_id C  
**AND** the case cannot be observed after N consecutive checks (threshold)  
**WHEN** CDC runs  
**THEN**:
- CDC classifies the event as **DELETED**
- Creates `change_event(change_type=deleted)`
- Creates a new `case_version` with `reason="deleted_or_withdrawn"`
- Updates index with a **tombstone/withdrawn marker**
- Retrieval defaults to **not showing deleted as active**

**Rationale**: Deleted cases must not pollute search results.

---

## C) Artifact & Content Change (Output B)

### C1. PDF bytes drift (strongest signal)

**GIVEN** `artifact(pdf)` exists for case_id C, language EN with `content_hash=H1`  
**AND** a new observed/stored pdf hash is `H2` where `H2 != H1`  
**WHEN** CDC runs  
**THEN**:
- CDC classifies the event as **CONTENT** change
- Creates `change_event(previous_hash=H1, new_hash=H2)`
- Creates a **new case_version** for C
- Triggers: `extract_text` → `chunk` → `embed` → `index` for the **affected language only**
- Does **NOT** reprocess unchanged languages/artifacts for the same case

**Rationale**: PDF hash is the strongest content integrity signal.

---

### C2. Extracted text drift without pdf drift

**GIVEN** `artifact(pdf)` hash is **unchanged**  
**AND** `artifact(text_extract)` normalized_text_hash changes from T1 to T2  
**WHEN** CDC runs  
**THEN**:
- CDC classifies the event as **CONTENT** change
- Creates `change_event(previous_hash=T1, new_hash=T2)`
- Creates a **new case_version** for C
- Triggers: `chunk` → `embed` → `index` (no required re-download of pdf)

**Rationale**: Extraction improvements may change text without PDF change.

---

### C3. Artifact missing in mirror

**GIVEN** CDC expects `artifact(pdf)` for case_id C language FR  
**AND** the artifact is **missing** from the mirror at runtime  
**WHEN** CDC runs  
**THEN**:
- CDC classifies the event as **AVAILABILITY** change
- Creates `change_event(change_type=unreachable_or_missing, signal=artifact_missing)`
- Triggers `fetch_artifact` for that artifact
- Does **NOT** trigger `embed/index` unless content is successfully obtained and hashed

**Rationale**: Missing artifacts must be fetched before embedding.

---

### C4. Artifact newly appears in mirror for existing case

**GIVEN** case_id C exists and is_current version exists  
**AND** a new `artifact(pdf)` for language FR appears in mirror (`artifact_new`)  
**WHEN** CDC runs  
**THEN**:
- CDC classifies the event as **AVAILABILITY** change (language/artifact addition)
- Creates `change_event(signal=artifact_new)`
- Creates a **new case_version**
- Triggers: `extract_text` → `chunk` → `embed` → `index` for **FR only**

**Rationale**: New language availability requires new version.

---

## D) Metadata Change (meaningful vs non-meaningful)

### D1. Meaningful metadata drift triggers metadata-only index update

**GIVEN** case_id C has meaningful metadata fields (e.g., `decision_date`, `tribunal_id`, `canonical_url`)  
**AND** a new registry snapshot changes **one of those meaningful fields**  
**WHEN** CDC runs  
**THEN**:
- CDC classifies the event as **METADATA_MEANINGFUL**
- Creates `change_event(change_type=modified, signal=registry_metadata_hash_changed)`
- Creates a **new case_version**
- Triggers: `update_registry` + `update_index_metadata_only`
- Does **NOT** trigger `re-extract/chunk/embed` when content hashes are unchanged

**Rationale**: Metadata changes affect search/ranking but not embeddings.

---

### D2. Non-meaningful metadata drift does not create a version

**GIVEN** case_id C changes **only a non-meaningful metadata field** (e.g., internal tags/notes)  
**WHEN** CDC runs  
**THEN**:
- CDC classifies as **METADATA_NONMEANINGFUL**
- Creates `change_event` OR records in `poll_run` as housekeeping (implementation choice)
- Does **NOT** create a new `case_version`
- Does **NOT** trigger any content downstream actions

**Rationale**: Non-meaningful metadata should not inflate version history.

---

## E) Cosmetic HTML Noise (must not cause ingestion)

### E1. HTML ETag changes but normalized content does not

**GIVEN** an observed HTML source has ETag changed (or Last-Modified changed)  
**AND** normalized content-region hash is **unchanged**  
**WHEN** CDC runs  
**THEN**:
- CDC classifies as **COSMETIC**
- Creates **no case_version**
- Triggers **no downstream ingestion actions**
- Records cosmetic change count in `poll_run` metrics

**Rationale**: Prevents noise from ad scripts, timestamps, analytics.

---

### E2. Raw HTML hashing is prohibited

**GIVEN** a system attempts to use raw HTML hash as a change trigger  
**WHEN** CDC runs  
**THEN**:
- CDC **rejects** that trigger as invalid per policy
- Either downgrades to **COSMETIC** or requires normalized hash evidence
- Records a `policy_violation` metric/event

**Rationale**: Raw HTML contains noise; only normalized content hashes allowed.

---

## F) Language Rules (EN/FR + bilingual artifacts)

### F1. Separate EN/FR outputs required

**GIVEN** a case has EN and FR available (`registry_language_set` includes both)  
**WHEN** CDC produces canonical outputs  
**THEN**:
- It produces **two distinct** `case_text` records (EN and FR)
- Both are traceable to `artifact` ids
- Retrieval can **filter by language** deterministically

**Rationale**: Bilingual search requires separate language streams.

---

### F2. Bilingual-in-one-artifact handling

**GIVEN** an artifact is bilingual (EN+FR in same pdf/html)  
**WHEN** extraction runs  
**THEN** the system either:
- **(a)** Splits into EN text and FR text, **OR**
- **(b)** Produces language-tagged chunks
- **No mixed-language chunk exists** without an explicit language tag

**Rationale**: Prevents language contamination in retrieval.

---

## G) Versioning & Retention

### G1. Version created only for meaningful change classes

**GIVEN** a change is classified as **COSMETIC** or **UNREACHABLE**  
**WHEN** CDC runs  
**THEN**:
- It does **NOT** create a new `case_version`

**Rationale**: Only meaningful changes inflate version history.

---

### G2. Prior versions are retained

**GIVEN** `case_version` v1 exists and a new v2 is created  
**WHEN** CDC completes  
**THEN**:
- v1 **remains stored and queryable** for audit
- v2 references v1 via `supersedes_case_version_id`
- Exactly **one version** is marked `is_current=true`

**Rationale**: ATO compliance requires version audit trail.

---

## H) Evidence (ATO-friendly)

### H1. Every downstream action has a change_event

**GIVEN** any action occurs (`fetch`, `extract`, `chunk`, `embed`, `index`)  
**WHEN** CDC completes  
**THEN** there exists at least one `change_event` that references:
- `poll_run_id`
- `case_id`
- `signal(s)`
- `previous_hash`/`new_hash` where applicable
- `action_taken` list
- **Absence of this record is a defect**

**Rationale**: Every action must have evidence chain.

---

### H2. Ability to answer "why did we ingest this?"

**GIVEN** a `case_version` exists  
**WHEN** asked "Why did we ingest this version?"  
**THEN** the system can point to:
- `poll_run` record
- `change_event` record
- Signals and hashes that triggered it
- `policy_version` used at the time

**Rationale**: ATO compliance requires "why did this happen" answers.

---

## I) Minimal Recompute (RAG cost control)

### I1. Changed case does not trigger corpus-wide recompute

**GIVEN** a single case's artifact hash changes  
**WHEN** CDC runs  
**THEN**:
- Only **that case's affected language stream** is reprocessed
- **No other cases** are re-embedded or re-indexed

**Rationale**: Prevents cost overruns from single-case changes.

---

### I2. Chunk-level delta processing

**GIVEN** a case's extracted text changes **only in one section**  
**WHEN** chunking runs  
**THEN**:
- Only **chunks impacted by the change** are re-embedded
- Unchanged chunks **retain their prior embeddings/vector ids** (or equivalent)

**Rationale**: Minimize embedding API calls and vector index updates.

---

## J) Failures, Backoff, Quarantine

### J1. Transient failures recorded, not silent

**GIVEN** the source returns 429/503/timeout  
**WHEN** CDC runs  
**THEN**:
- CDC classifies as **UNREACHABLE**
- Records a failure event (`change_event` or `poll_run` failure list)
- Applies **backoff rules** (per change-policy.yaml thresholds)
- Does **NOT** mark the case as deleted on first failure

**Rationale**: Transient failures are not deletions.

---

### J2. Permanent gone threshold

**GIVEN** the source returns 404/410 for the same case **N consecutive times**  
**WHEN** CDC runs  
**THEN**:
- CDC classifies as **DELETED**
- Produces a deletion `change_event` + new `case_version` with `reason=deleted_or_withdrawn`

**Rationale**: Persistent 404 = permanent deletion.

---

## K) Bootstrap (Day-0 cutover)

### K1. Seed corpus produces v1 with provenance

**GIVEN** an Accenture seed + existing blob PDFs are used to bootstrap  
**WHEN** bootstrap completes  
**THEN**:
- Every seeded case has `case_version=1` with `reason=seed`
- Seed artifacts are recorded as `artifact_type=json_seed` and/or `pdf`
- **Cutover timestamp** is recorded

**Rationale**: Seed corpus must have provenance (not "appeared from nowhere").

---

### K2. CDC is authoritative after cutover

**GIVEN** cutover is complete  
**WHEN** new versions appear  
**THEN**:
- They are created **only by CDC runs** (`poll_run` + `change_event` evidence exists)

**Rationale**: After bootstrap, CDC owns all version creation.

---

## Implementation Checklist

### Week 1: Foundation Tests (8 tests)
- [ ] A1: Scope enforcement
- [ ] A2: Every run creates poll_run
- [ ] A3: Replay determinism
- [ ] B1: New case discovery
- [ ] B2: External key change
- [ ] G1: Version creation rules
- [ ] H1: Every action has evidence
- [ ] H2: "Why did we ingest this?" query

### Week 2: Content & Metadata Tests (10 tests)
- [ ] C1: PDF bytes drift
- [ ] C2: Text drift without PDF drift
- [ ] C3: Artifact missing
- [ ] C4: Artifact newly appears
- [ ] D1: Meaningful metadata drift
- [ ] D2: Non-meaningful metadata drift
- [ ] E1: HTML ETag changes
- [ ] E2: Raw HTML hashing prohibited
- [ ] I1: No corpus-wide recompute
- [ ] I2: Chunk-level delta processing

### Week 3: Language, Failures, Bootstrap (8 tests)
- [ ] F1: Separate EN/FR outputs
- [ ] F2: Bilingual artifact handling
- [ ] B3: Case disappears
- [ ] G2: Prior versions retained
- [ ] J1: Transient failures recorded
- [ ] J2: Permanent gone threshold
- [ ] K1: Seed corpus provenance
- [ ] K2: CDC authoritative after cutover

---

## Test Automation

**Python Test Suite Template**:

```python
import pytest
from cdc_poller import CDCPoller
from cosmos_client import CosmosClient

@pytest.fixture
def cdc_setup():
    """Initialize CDC with test scope and policy"""
    return CDCPoller(
        scope_id="TEST-SST-EN-2020",
        policy_path="cdc/change-policy.yaml"
    )

# A1: Scope enforcement
def test_scope_enforcement_ignores_out_of_scope(cdc_setup):
    """GIVEN scope SST 2018-2020, WHEN case outside scope changes, THEN ignore"""
    registry_before = [{"case_id": "SST-2019-001", "tribunal": "SST", "year": 2019}]
    registry_after = [
        {"case_id": "SST-2019-001", "tribunal": "SST", "year": 2019},
        {"case_id": "FC-2021-001", "tribunal": "FC", "year": 2021}  # Out of scope
    ]
    
    poll_run = cdc_setup.run(registry_before, registry_after)
    
    assert poll_run["ignored_out_of_scope_count"] >= 1
    assert not any(e["case_id"] == "FC-2021-001" for e in poll_run["change_events"])

# B1: New case discovery
def test_new_case_triggers_structural_change(cdc_setup):
    """GIVEN new case appears in registry, WHEN CDC runs, THEN create v1 and queue fetch"""
    registry_before = []
    registry_after = [{"case_id": "SST-2020-NEW", "external_key": "2020canlii999"}]
    
    poll_run = cdc_setup.run(registry_before, registry_after)
    
    change_events = poll_run["change_events"]
    assert any(e["change_type"] == "new" and e["case_id"] == "SST-2020-NEW" for e in change_events)
    
    case_version = CosmosClient().get_case_version("SST-2020-NEW", version=1)
    assert case_version["reason"] == "new_or_identity_change"
    assert "fetch_artifact" in change_events[0]["action_taken"]

# C1: PDF bytes drift
def test_pdf_hash_change_triggers_content_change(cdc_setup):
    """GIVEN PDF hash changes, WHEN CDC runs, THEN create new version and re-embed"""
    artifacts_before = [{"case_id": "SST-2020-001", "lang": "EN", "pdf_hash": "abc123"}]
    artifacts_after = [{"case_id": "SST-2020-001", "lang": "EN", "pdf_hash": "xyz789"}]
    
    poll_run = cdc_setup.run_artifact_check(artifacts_before, artifacts_after)
    
    change_event = next(e for e in poll_run["change_events"] if e["case_id"] == "SST-2020-001")
    assert change_event["change_type"] == "content"
    assert change_event["previous_hash"] == "abc123"
    assert change_event["new_hash"] == "xyz789"
    assert set(change_event["action_taken"]) >= {"extract_text", "chunk", "embed", "index"}

# E1: Cosmetic HTML noise
def test_etag_change_without_content_change_is_cosmetic(cdc_setup):
    """GIVEN ETag changes but normalized content unchanged, WHEN CDC runs, THEN classify as cosmetic"""
    http_before = {"url": "https://example.com/case1", "etag": "v1", "normalized_hash": "content123"}
    http_after = {"url": "https://example.com/case1", "etag": "v2", "normalized_hash": "content123"}
    
    poll_run = cdc_setup.run_http_check([http_before], [http_after])
    
    assert poll_run["cosmetic_change_count"] >= 1
    assert not any(e["change_type"] != "cosmetic" for e in poll_run["change_events"])

# H1: Evidence chain
def test_every_action_has_change_event(cdc_setup):
    """GIVEN any downstream action occurs, WHEN CDC completes, THEN change_event exists"""
    registry_after = [{"case_id": "NEW-001", "external_key": "newkey"}]
    
    poll_run = cdc_setup.run([], registry_after)
    
    change_event = next(e for e in poll_run["change_events"] if e["case_id"] == "NEW-001")
    assert "poll_run_id" in change_event
    assert "case_id" in change_event
    assert "signal" in change_event
    assert "action_taken" in change_event and len(change_event["action_taken"]) > 0
```

**Hard Stop Criteria**: All 26 tests must pass before production deployment.

---

## References

- **Change Policy**: [change-policy.yaml](change-policy.yaml) - Classification rules and actions
- **Design Principles**: [cdc-mvp-design.md](../cdc-mvp-design.md) - Architecture rationale
- **Implementation Guide**: [cdc-mvp-artifacts.md](../cdc-mvp-artifacts.md) - Build deliverables
- **Navigation Hub**: [CDC-INDEX.md](../CDC-INDEX.md) - All CDC documentation

---

**Status**: Ready for implementation (Week 1-3)  
**Owner**: Development Team  
**Approval**: Required from Security/Compliance for H1, H2 (ATO evidence tests)
