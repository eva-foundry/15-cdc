# CDC (Change Data Capture) for MS-InfoJP Jurisprudence Corpus

**Status**: Documentation Complete, Implementation Ready  
**Version**: 1.0.0  
**Last Updated**: 2026-01-28

---

## Purpose

**Problem**: RAG systems experience "knowledge decay" when indexes aren't kept current with new legal precedents, leading to incorrect legal guidance and compliance risk.

**Solution**: CDC maintains freshness in the MS-InfoJP jurisprudence RAG corpus by:
- **Detecting changes** in CanLII case metadata and artifacts (scheduled + event-driven)
- **Tracking versions** with full provenance (audit trail for every change)
- **Minimizing recompute** (only changed artifacts/chunks/vectors are reprocessed)
- **Providing freshness guarantees** via SLO tiers (1hr/24hr/weekly)
- **Enabling audit compliance** (ATO-friendly evidence logging)

---

## ⚠️ Prerequisites (Week 0 - MUST COMPLETE FIRST)

**BLOCKING TASKS** before implementation:

1. **CanLII Data Access Validation** 🔴 CRITICAL
   - Investigate actual CanLII API availability (public API vs web scraping)
   - Document PDF artifact access mechanism
   - Verify ToS compliance for automated polling
   - **Deliverable**: `docs/adr/001-canlii-data-access-strategy.md`

2. **Azure Environment Validation** 🔴 CRITICAL
   - Verify subscription access (c59ee575...)
   - Test Cosmos DB connectivity
   - Confirm Blob Storage and Azure AI Search access
   - **Deliverable**: `docs/infrastructure/azure-environment-validated.md`

3. **Cost Modeling & Budget Approval** 🟡 HIGH
   - Complete cost breakdown (Cosmos DB, embeddings, storage)
   - Set up Azure cost alerts
   - Get budget approval before deployment
   - **Deliverable**: `docs/cost-analysis.xlsx`

4. **Development Environment Setup** 🟡 HIGH
   - Create local dev environment guide
   - Set up Cosmos DB emulator (docker-compose.yml)
   - Configure VS Code debugging
   - **Deliverable**: `DEVELOPMENT.md`

**Time Commitment**: 10-18 hours (1-2 days)

---

## Quick Start

**For Implementers**:
1. Read [CDC-IMPLEMENTATION-START.md](CDC-IMPLEMENTATION-START.md) - Complete implementation guide
2. Review [cdc-mvp-design.md](cdc-mvp-design.md) - Architecture principles
3. Check [cdc-mvp-artifacts.md](cdc-mvp-artifacts.md) - Build deliverables

**For Reviewers**:
1. See [CDC-INDEX.md](CDC-INDEX.md) - Complete documentation map
2. Review [acceptance-tests.md](acceptance-tests.md) - 26 test specifications
3. Check [change-policy.yaml](change-policy.yaml) - Classification rules

**For Operators** (Phase 2):
1. See [operations-admin-control-plane.md](operations-admin-control-plane.md) - Admin UI design
2. Review monitoring and alerting requirements

---

## Architecture Overview

### Two-Plane Architecture

**Data Plane** (does the work):
1. **Change Detection** → Scheduled + event-driven polling of CanLII metadata
2. **CDC Evidence** → Case registry, artifact index, change events (Cosmos DB)
3. **Downstream Processing** → Extract, chunk, embed, index (delta only)
4. **Freshness-Aware Retrieval** → Recency-boosted Azure AI Search

**Control Plane** (keeps it running):
1. **Corpus Registry** → Multi-corpus management with SLO tiers
2. **CDC Operations Dashboard** → Run status, freshness lag monitoring
3. **Policy Management** → Change classification, scope definitions
4. **Client Reporting** → What changed, why, freshness guarantees

---

## Key Concepts

- **scope_id**: Partition for reproducible CDC runs (e.g., "SST-GD-EN-rolling-24mo")
- **poll_run**: One CDC execution record (always created, even if no changes)
- **change_event**: One detected change with classification + actions taken
- **case_version**: Versioned case state (created only for meaningful changes)
- **artifact**: Stored/observed item (PDF/HTML/text) with content hashes
- **change_class**: Structural / Availability / Metadata / Content / Cosmetic / Unreachable / Deleted
- **SLO tier**: Freshness guarantee (1=<1hr, 2=<24hr, 3=weekly)

---

## Documentation Index

**Complete Map**: See [CDC-INDEX.md](CDC-INDEX.md) ✅ COMPLETE - Navigation hub (242 lines)

**Core Documents**:
- **[cdc-mvp-design.md](cdc-mvp-design.md)** ✅ COMPLETE - Architecture principles (671 lines)
- **[CDC-IMPLEMENTATION-START.md](CDC-IMPLEMENTATION-START.md)** - Implementation roadmap ⭐ Start here for coding
- **[cdc-mvp-artifacts.md](cdc-mvp-artifacts.md)** - Build deliverables & acceptance criteria

**Policy Pack** (Configuration):
- **[change-policy.yaml](change-policy.yaml)** - Classification rules (v0.1.0) ✅ COMPLETE
- **[scope.yaml](scope.yaml)** - Corpus scope definitions ✅ COMPLETE
- **[immutability.yaml](immutability.yaml)** - Polling frequencies ✅ COMPLETE
- **[language-policy.yaml](language-policy.yaml)** - EN/FR handling ✅ COMPLETE

**Technical Specifications**:
- **[minimal-schema-ddl.md](minimal-schema-ddl.md)** - 12-table Cosmos DB schema
- **[acceptance-tests.md](acceptance-tests.md)** - 26 test specifications
- **[downstream-invalidation-contract.md](downstream-invalidation-contract.md)** - RAG pipeline contract

**Advanced Topics**:
- **[preventing-stale-data.md](preventing-stale-data.md)** - Freshness-aware RAG architecture
- **[operations-admin-control-plane.md](operations-admin-control-plane.md)** - Phase 2+ admin UI

---

## Implementation Status

**Phase 1 - Week 0: Prerequisites & Validation** (🔴 CRITICAL - Current)
- 🔴 CanLII data access investigation (BLOCKING)
- 🔴 Azure environment validation (BLOCKING)
- 🟡 Cost modeling and budget approval
- 🟡 Development environment setup
- 🟡 Test infrastructure foundation
- **Exit Criteria**: CanLII access validated, Azure resources confirmed, budget approved

**Phase 1 - Week 1: Foundation & Observability** (⏳ TODO)
- ✅ Documentation complete (12 documents, ~7500 lines)
- ✅ change-policy.yaml v0.1.0 complete
- ✅ Policy pack complete (scope, immutability, language)
- ⏳ Basic observability setup (Application Insights, structured logging)
- ⏳ Deploy Cosmos DB schema (12 containers with validation)
- ⏳ Implement Corpus Registry module (with SessionManager)
- ⏳ Test infrastructure (pytest, fixtures, mock data)

**Phase 1 - Week 2: Core CDC Engine** (⏳ TODO)
- ⏳ Case Registry module (with evidence collection)
- ⏳ Artifact Index module (with checkpoint/resume)
- ⏳ Change Classifier engine (with audit trail)
- ⏳ Poll Executor framework (with retry logic)
- 🎯 Target: >80% test coverage per module

**Phase 1 - Week 3: Integration & Testing** (⏳ TODO)
- ⏳ Downstream action processor (with circuit breaker)
- ⏳ 26 acceptance tests (categories A-K)
- ⏳ Integration testing (end-to-end flows)
- ⏳ Performance testing (<5 min per 100 cases)
- ⏳ Documentation finalization (runbooks, deployment guide)

**Phase 2: Operations** (Future)
- Admin dashboard
- Event-driven triggers
- Advanced monitoring

**Risk Register**: See [IMPLEMENTATION-RISKS.md](IMPLEMENTATION-RISKS.md) for mitigation strategies

---

## Quick Reference

**8 Change Classes**:
```
structural          → New/removed case identities
availability        → Language or artifact presence changed
metadata_meaningful → Affects search/filtering/citations
metadata_nonmeaningful → Housekeeping only
content             → PDF or text changed
cosmetic            → Formatting noise (no action)
unreachable         → Temporary failure (retry)
deleted             → Permanently removed
```

**11 Action Types**:
```
update_registry               fetch_artifact
extract_text                  generate_chunks
embed_chunks                  update_index
update_index_metadata_only    mark_withdrawn_or_deleted
update_index_tombstone        record_failure
retry_with_backoff
```

---

## Contributing

1. All changes must include evidence logging (no silent work)
2. Follow policy-driven approach (rules in YAML, not code)
3. Maintain idempotency (replay must be deterministic)
4. Test against acceptance criteria (26 scenarios)
5. Update documentation with all architectural decisions

---

## References

**Parent Project**: [../README.md](../README.md) - MS-InfoJP Overview  
**Azure Resources**: infojp-sandbox (East US), Subscription c59ee575...  
**Base Platform**: base-platform/ (Microsoft PubSec-Info-Assistant commit 807ee181)

**Additional Documentation**:
- **Architecture Decisions**: `docs/adr/` - ADRs for key design choices
- **Development Guide**: `DEVELOPMENT.md` - Local setup and workflows
- **Risk Register**: `IMPLEMENTATION-RISKS.md` - Risk mitigation strategies
- **Cost Analysis**: `docs/cost-analysis.xlsx` - Budget and optimization
- **Runbooks**: `docs/runbooks/operator-guide.md` - Operations playbook

---

**⚠️ Complete Week 0 Prerequisites before beginning implementation!** 🚀
