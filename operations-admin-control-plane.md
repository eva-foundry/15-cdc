# Feature: CDC Operations Reporting + Admin Control Plane

**Purpose**: Provide an auditable, client-facing way to:
- See what CDC did (and why)
- Manage CDC parameters safely (without redeploying)
- Monitor health/cost/quality over time

**Version**: 1.0.0  
**Last Updated**: 2026-01-25  
**Status**: Feature specification for Phase 2+

---

## Non-goals (for now)

- Editing case content or overriding judicial text
- Manual "rewrite" of decisions
- Anything that bypasses evidence logging

---

## A) Client Reporting (What Clients Can See)

### A1. "What changed?" report (per period)

**Views**:
- Last run summary (per scope_id)
- Daily/weekly digest
- "Top changed tribunals"
- "New cases added"

**Data fields shown**:
- `scope_id`
- `poll_run` start/end timestamps
- **Counts**:
  - Cases checked
  - New cases
  - Content changed
  - Metadata changed
  - Failures
  - Ignored cosmetic changes
- Bytes ingested (if available)
- Downstream actions executed:
  - Extract count
  - Chunk count
  - Embed count
  - Index updates

**Key UX rule**: Every number links back to evidence
- `poll_run` → list of `change_events` → affected `case_versions` → `artifacts`

**Example UI Card**:
```
┌─────────────────────────────────────────────────────┐
│ Last Poll Run: SST-GD-EN-rolling-24mo              │
│ Started: 2026-01-25 10:00 UTC                      │
│ Ended: 2026-01-25 10:15 UTC                        │
│                                                     │
│ Cases checked: 150                                  │
│ ├─ New: 2                                          │
│ ├─ Content changed: 1                              │
│ ├─ Metadata changed: 3                             │
│ ├─ Cosmetic (ignored): 12                          │
│ └─ Out of scope (ignored): 5                       │
│                                                     │
│ Actions executed:                                   │
│ ├─ Artifacts fetched: 3                            │
│ ├─ Text extracted: 3                               │
│ ├─ Chunks generated: 127                           │
│ ├─ Embeddings created: 127                         │
│ └─ Index updates: 3                                │
│                                                     │
│ [View Details] [View Change Log]                   │
└─────────────────────────────────────────────────────┘
```

---

### A2. "Why did we ingest this?" (case drilldown)

From any surfaced case, show:
- **Current version** (vN)
- **Prior versions list** (v1, v2, ..., vN-1)
- **What signal triggered version bump**:
  - Hash drift (PDF changed)
  - New registry ID
  - Redirect
  - Metadata meaningful change
- **Artifacts involved**:
  - PDF/HTML/text
  - Content hashes
  - Timestamps (retrieved_at_utc)
- **Actions taken**:
  - Metadata-only vs full reprocess

**Example UI**:
```
┌─────────────────────────────────────────────────────┐
│ Case: 2020 SST 123 (Smith v. Minister)            │
│ Current Version: v2                                 │
│                                                     │
│ Version History:                                    │
│ ┌─ v2 (current) ─────────────────────────────────┐ │
│ │ Created: 2026-01-25 10:10 UTC                  │ │
│ │ Reason: content_change                          │ │
│ │ Signal: artifact_pdf_hash_changed               │ │
│ │                                                 │ │
│ │ Evidence:                                       │ │
│ │ • Poll run: 01JGQP8ABC... (SST-GD-EN-rolling)  │ │
│ │ • Change event: 01JGQP9ABC...                   │ │
│ │ • Previous hash: sha256:old_abc123...           │ │
│ │ • New hash: sha256:new_xyz789...                │ │
│ │                                                 │ │
│ │ Actions taken:                                  │ │
│ │ ✓ fetch_artifact                                │ │
│ │ ✓ extract_text                                  │ │
│ │ ✓ generate_chunks                               │ │
│ │ ✓ embed_chunks                                  │ │
│ │ ✓ update_index                                  │ │
│ │                                                 │ │
│ │ Artifacts:                                      │ │
│ │ • EN PDF: 524 KB, retrieved 2026-01-25 10:05   │ │
│ │   Hash: sha256:new_xyz789...                    │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ┌─ v1 (seed) ────────────────────────────────────┐ │
│ │ Created: 2026-01-20 00:00 UTC                  │ │
│ │ Reason: seed                                    │ │
│ │ Source: Accenture seed corpus                   │ │
│ │ Artifacts: EN PDF (520 KB)                      │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

### A3. Transparency safeguards

**What to show**:
- What the system **observed** (signals, hashes, timestamps)
- What the system **did** (actions taken)
- Why the system **decided** (policy version, classification rule)

**What NOT to show**:
- Internal secrets (API keys, connection strings)
- PII in logs (unless explicitly authorized)
- Raw system errors (sanitize for client view)

**Access control**:
- **Client read-only**: Can view reports and drilldowns
- **Operators**: Can see detailed logs and errors
- **Enforce role-based access** (RBAC via Entra ID)

---

## B) Admin Panel (Control Plane)

### B1. Manage Scopes (scope_id catalog)

**CRUD operations** on scope definitions (through files or DB-backed config):
- Enable/disable scope
- Adjust cadence profile (hourly, daily, weekly)
- Adjust time window (ROLL-24MO → ROLL-36MO)
- Adjust source profile (BLOB/HYB/WEB)
- Assign immutability (IMM/MUT/MIX)

**Hard rule**: Changes create a new "config version" record with:
- Who changed it (operator identity)
- When (timestamp)
- Before/after diff
- Reason (mandatory text field)

**Example UI**:
```
┌─────────────────────────────────────────────────────┐
│ Manage Scopes                                       │
│                                                     │
│ Active Scopes (5)                                   │
│ ┌─ SST-GD-EN-rolling-24mo ──────────────────────┐  │
│ │ Enabled: ✓                                     │  │
│ │ Cadence: Daily at 00:00 UTC                    │  │
│ │ Time window: Rolling 24 months                 │  │
│ │ Source: BLOB (primary), CANLII_API (fallback)  │  │
│ │ Immutability: MUT (mutable tribunal)           │  │
│ │ Last run: 2026-01-25 10:15 UTC (success)       │  │
│ │                                                 │  │
│ │ [Edit] [Disable] [Run Now]                     │  │
│ └─────────────────────────────────────────────────┘  │
│                                                     │
│ ┌─ FCA-EN-IMM-2020-2025 ─────────────────────────┐  │
│ │ Enabled: ✓                                     │  │
│ │ Cadence: Weekly (Sundays at 02:00 UTC)         │  │
│ │ Time window: Fixed 2020-2025                   │  │
│ │ Source: CANLII_API                              │  │
│ │ Immutability: IMM (immutable court)            │  │
│ │ Last run: 2026-01-20 02:00 UTC (success)       │  │
│ │                                                 │  │
│ │ [Edit] [Disable] [Run Now]                     │  │
│ └─────────────────────────────────────────────────┘  │
│                                                     │
│ [+ Create New Scope]                                │
└─────────────────────────────────────────────────────┘
```

**Config change audit trail**:
```sql
CREATE TABLE scope_config_version (
  config_version_id      TEXT PRIMARY KEY,
  scope_id               TEXT NOT NULL,
  
  changed_by             TEXT NOT NULL,         -- operator identity
  changed_at_utc         TIMESTAMP NOT NULL,
  reason                 TEXT NOT NULL,
  
  before_json            TEXT NOT NULL,         -- full scope config before
  after_json             TEXT NOT NULL,         -- full scope config after
  
  created_at_utc         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

### B2. Manage CDC thresholds (guardrails)

**Configurable but controlled parameters**:
- `permanently_gone_after_n_consecutive_observations` (default: 3)
- `unreachable_quarantine_after_n_failures` (default: 5)
- Max retries / backoff profile (exponential with jitter)
- Max requests/sec and daily quota caps per source (aligns with CanLII limits: 60 req/min)
- "Max bytes per run" budget cap (optional cost control)

**Hard rule**: No parameter change can bypass policy constraints:
- ❌ **Cannot enable raw HTML hashing** (policy violation)
- ❌ **Cannot enable "full corpus rebuild"** (cost overrun risk)
- ❌ **Cannot disable evidence logging** (ATO requirement)

**Example UI**:
```
┌─────────────────────────────────────────────────────┐
│ CDC Thresholds & Guardrails                         │
│                                                     │
│ Failure Handling:                                   │
│ • Permanently gone after: [3▼] consecutive 404/410  │
│ • Quarantine after: [5▼] consecutive failures       │
│ • Max retries per artifact: [3▼]                    │
│ • Backoff strategy: Exponential with jitter         │
│                                                     │
│ Rate Limits (per source):                           │
│ • CanLII API: [60▼] requests/min                    │
│ • CanLII HTML: [120▼] requests/min                  │
│ • Daily quota cap: [10000▼] requests/day            │
│                                                     │
│ Cost Controls:                                      │
│ • Max bytes per run: [1GB▼] (optional)              │
│ • Max embedding calls per run: [5000▼] (optional)   │
│                                                     │
│ Policy Constraints (LOCKED):                        │
│ • Raw HTML hashing: PROHIBITED                      │
│ • Full corpus rebuild: PROHIBITED                   │
│ • Evidence logging: MANDATORY                       │
│                                                     │
│ [Save Changes] [Reset to Defaults]                  │
└─────────────────────────────────────────────────────┘
```

---

### B3. Manual ops actions (safe levers)

**Available operations**:
1. **Re-run a scope** (on-demand poll_run)
   - Creates manual `poll_run` record
   - Reason required
   - Operator attribution

2. **Reprocess a specific case_version** (force re-extract/chunk/embed)
   - **Mandatory reason** field
   - Creates `change_event` with `signal=manual_reprocess`
   - Operator attribution

3. **Quarantine/unquarantine a source URL**
   - Temporarily block a failing source
   - Record reason and duration
   - Auto-expire after N days

4. **Mark a change_event as "false positive"**
   - For tuning metrics
   - Does NOT undo downstream actions
   - Used for analysis only

**All manual actions must create**:
- `poll_run` record (with `manual=true` flag)
- `change_event` records (with operator attribution)
- Operator identity + notes (mandatory)

**Example UI**:
```
┌─────────────────────────────────────────────────────┐
│ Manual Operations                                   │
│                                                     │
│ ┌─ Re-run Scope ───────────────────────────────────┐ │
│ │ Scope ID: [SST-GD-EN-rolling-24mo ▼]            │ │
│ │ Reason: [e.g., "Network failure during last run"]│ │
│ │                                                  │ │
│ │ [Run Now]                                        │ │
│ └──────────────────────────────────────────────────┘ │
│                                                     │
│ ┌─ Reprocess Case ────────────────────────────────┐ │
│ │ Case ID: [01JGQP2VWXYZ... ▼]                    │ │
│ │ Reason: [e.g., "Extraction quality issue"]      │ │
│ │                                                  │ │
│ │ Actions to perform:                              │ │
│ │ ☑ Re-extract text                               │ │
│ │ ☑ Re-chunk                                       │ │
│ │ ☑ Re-embed                                       │ │
│ │ ☑ Re-index                                       │ │
│ │                                                  │ │
│ │ [Reprocess]                                      │ │
│ └──────────────────────────────────────────────────┘ │
│                                                     │
│ ┌─ Quarantine Source ─────────────────────────────┐ │
│ │ Source URL: [https://example.com/failing-case]  │ │
│ │ Reason: [e.g., "Repeated 503 errors"]           │ │
│ │ Duration: [7 days ▼]                             │ │
│ │                                                  │ │
│ │ [Quarantine]                                     │ │
│ └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## C) Logging & Monitoring (Operator-Grade)

### C1. Health dashboards (minimum)

**Metrics**:
- **Run success rate**: % of poll_runs that completed successfully
- **Failure rate by source_system**: CanLII API vs web vs blob
- **Queue backlog**: (if applicable) number of pending change_events
- **Average time per scope**: Duration distribution for poll_runs
- **Cost per delta**: API calls, bytes transferred, embeddings generated

**Example Dashboard**:
```
┌─────────────────────────────────────────────────────┐
│ CDC Health Dashboard (Last 7 Days)                  │
│                                                     │
│ Run Success Rate: 98.5% (67/68 runs)               │
│ ├─ Successful: 67                                  │
│ ├─ Failed: 1 (network timeout)                     │
│ └─ Average duration: 12 minutes                    │
│                                                     │
│ Failure Rate by Source:                             │
│ ├─ CanLII API: 0.2% (1/500 requests)               │
│ ├─ Blob Mirror: 0% (0/300 requests)                │
│ └─ CanLII HTML: 2.1% (5/240 requests - deprecated) │
│                                                     │
│ Queue Backlog: 0 pending change_events              │
│                                                     │
│ Cost Metrics:                                       │
│ ├─ API calls: 5,243 (avg 77/run)                   │
│ ├─ Bytes transferred: 12.3 GB                      │
│ └─ Embeddings generated: 1,847 (avg 27/run)        │
└─────────────────────────────────────────────────────┘
```

---

### C2. Quality dashboards (CDC correctness)

**Metrics**:
- **False positive rate**: Cosmetic changes flagged as meaningful
- **"No-op ratio"**: Too many runs with nothing changing
- **"Drift hotspots"**: Scopes with high change rates
- **Bilingual anomalies count**: Cases missing expected language pairs

**Example Dashboard**:
```
┌─────────────────────────────────────────────────────┐
│ CDC Quality Dashboard (Last 30 Days)                │
│                                                     │
│ False Positive Rate: 3.2% (8/250 changes)          │
│ ├─ Cosmetic flagged as meaningful: 8               │
│ └─ Trend: Decreasing (was 5.1% last month)         │
│                                                     │
│ No-op Ratio: 12% (24/200 runs found no changes)    │
│ └─ Within expected range (10-15% normal)           │
│                                                     │
│ Drift Hotspots (Top 3):                             │
│ ├─ SST-GD-EN-rolling-24mo: 45 changes/week         │
│ ├─ SST-AD-EN-rolling-24mo: 12 changes/week         │
│ └─ FCA-EN-rolling-36mo: 8 changes/week             │
│                                                     │
│ Bilingual Anomalies: 2 cases                        │
│ ├─ Expected EN+FR, only EN found: 2                │
│ └─ [View Cases]                                     │
└─────────────────────────────────────────────────────┘
```

---

### C3. Audit views (ATO-friendly)

**Views**:
- `poll_run` timeline (all CDC executions)
- Config change history (all scope/threshold edits)
- Operator action log (who did what)

**Example Query**:
```sql
-- Audit trail: Who changed what, when, and why?
SELECT 
  scv.scope_id,
  scv.changed_by,
  scv.changed_at_utc,
  scv.reason,
  scv.before_json,
  scv.after_json
FROM scope_config_version scv
WHERE scv.changed_at_utc >= CURRENT_TIMESTAMP - INTERVAL '90 days'
ORDER BY scv.changed_at_utc DESC;
```

---

## D) Roles & Access (Minimal RBAC)

**Suggested roles**:

| Role | Permissions | Use Case |
|------|-------------|----------|
| **Client Viewer** | Read reports + drilldowns | Client-facing dashboard access |
| **CDC Operator** | Run scopes, manage quarantine, view logs | Day-to-day operations |
| **CDC Admin** | Edit scope config + thresholds | Configuration management |
| **Auditor** | Read-only access to evidence + config history | ATO compliance reviews |

**Implementation**:
- Use **Entra ID security groups** for role assignment
- Enforce at API level (backend checks roles)
- Frontend hides/shows UI elements based on role

---

## E) How to Build It Incrementally (3 Slices)

### Slice 1 — Read-only reporting (fast win)

**Deliverables**:
- `poll_run` list + summary cards
- `change_event` drilldown by `scope_id`
- Per-case "why ingested" view

**Effort**: 2-3 weeks  
**Value**: Immediate transparency for clients

**Tech Stack**:
- Backend: FastAPI endpoints that query Cosmos DB
- Frontend: React dashboard with Fluent UI components
- Authentication: Entra ID OAuth 2.0

---

### Slice 2 — Admin config (controlled)

**Deliverables**:
- Scope enable/disable
- Cadence + window edits
- Thresholds editing with audit trail

**Effort**: 3-4 weeks  
**Value**: Self-service CDC management without redeployment

**Tech Stack**:
- Backend: Admin API with RBAC enforcement
- Config storage: Cosmos DB or Azure Blob (YAML files)
- Audit trail: `scope_config_version` table

---

### Slice 3 — Full monitoring + FinOps

**Deliverables**:
- Cost per delta analytics
- Failure analytics
- False positive analytics
- Notifications (optional - email/Teams on failures)

**Effort**: 4-5 weeks  
**Value**: Proactive cost control and quality monitoring

**Tech Stack**:
- Monitoring: Azure Monitor + Application Insights
- Dashboards: Grafana or Power BI
- Notifications: Azure Logic Apps or Functions

---

## F) The One Design Decision to Lock Now

**If you want this future UI to be easy, ensure CDC writes consistent evidence**:

✅ **Required fields in every record**:

1. **poll_run**:
   - `policy_version` + `policy_hash` (policy used for classification)
   - `scope_id` (what was checked)
   - `result_counts_json` (summary metrics)
   - Operator attribution (if manual run)

2. **change_event**:
   - `signal_id` (what triggered the change)
   - `previous_hash` / `new_hash` (evidence of drift)
   - `action_taken_json` (what the system did)
   - `status` (recorded, executed, failed, skipped)

3. **case_version**:
   - Links back to `poll_run_id` + `change_event_id`
   - `reason` (why this version was created)
   - `supersedes_case_version_id` (version chain)

4. **Config changes**:
   - Versioned (via `scope_config_version` table)
   - Before/after diffs
   - Operator attribution + reason

**If these are in place, the admin/reporting layer is mostly "queries + UI"**.

---

## G) Integration with Existing CDC Components

**Dependencies**:

| CDC Component | Required Fields | Status |
|---------------|-----------------|--------|
| [change-policy.yaml](change-policy.yaml) | Referenced by `poll_run.policy_version` | ✅ Complete |
| [minimal-schema-ddl.md](minimal-schema-ddl.md) | All tables defined | ✅ Complete |
| [acceptance-tests.md](acceptance-tests.md) | Evidence chain tests (H1, H2) | ✅ Complete |

**New schema additions** (for this feature):

```sql
-- Config change audit trail
CREATE TABLE scope_config_version (
  config_version_id      TEXT PRIMARY KEY,
  scope_id               TEXT NOT NULL,
  
  changed_by             TEXT NOT NULL,
  changed_at_utc         TIMESTAMP NOT NULL,
  reason                 TEXT NOT NULL,
  
  before_json            TEXT NOT NULL,
  after_json             TEXT NOT NULL,
  
  created_at_utc         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Operator action log
CREATE TABLE operator_action_log (
  action_id              TEXT PRIMARY KEY,
  operator_identity      TEXT NOT NULL,
  action_type            TEXT NOT NULL,  -- run_scope | reprocess_case | quarantine_url | edit_config
  
  target_id              TEXT NOT NULL,  -- scope_id | case_id | url
  reason                 TEXT NOT NULL,
  
  action_json            TEXT NOT NULL,  -- full action details
  result                 TEXT NOT NULL,  -- success | failed
  
  created_at_utc         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

## References

- **Change Policy**: [change-policy.yaml](change-policy.yaml) - Classification rules
- **Database Schema**: [minimal-schema-ddl.md](minimal-schema-ddl.md) - 11-table schema
- **Acceptance Tests**: [acceptance-tests.md](acceptance-tests.md) - Evidence chain validation
- **Design Principles**: [../cdc-mvp-design.md](../cdc-mvp-design.md) - Architecture rationale

---

**Status**: Feature specification for Phase 2+ implementation  
**Owner**: Product/Engineering Team  
**Priority**: Medium (after MVP CDC implementation)
