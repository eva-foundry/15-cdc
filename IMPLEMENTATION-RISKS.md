# CDC Implementation - Risk Register

**Purpose**: Track and mitigate implementation risks for MS-InfoJP CDC system  
**Last Updated**: 2026-02-02  
**Status**: Active monitoring required

---

## 🚨 Critical Risks (Week 0 Validation Required)

### Risk 1: CanLII API Availability/Access Method

**Risk ID**: RISK-001  
**Category**: Technical - Data Access  
**Probability**: HIGH (70%)  
**Impact**: CRITICAL (Project blocker)

**Description**: Documentation assumes CanLII has a public API, but as of 2024-2026, CanLII may not provide:
- Public REST API for metadata access
- Structured JSON responses
- Programmatic PDF download capability
- Rate-limited but free access

**Potential Consequences**:
- Architecture changes required (web scraping vs API polling)
- Different error modes (HTML parsing errors vs 4xx/5xx)
- ToS compliance issues with automated scraping
- Implementation timeline extended by 1-2 weeks

**Mitigation Strategy**:
1. **Week 0 Task 0.1**: Investigate actual CanLII data access (4-8 hours)
2. Create ADR documenting findings: `docs/adr/001-canlii-data-access-strategy.md`
3. If no API: Design web scraping abstraction layer
4. If API exists: Document rate limits and authentication
5. **Fallback Option**: Contact CanLII for partnership/data access agreement

**Status**: 🔴 UNMITIGATED - Week 0 validation required

**Owner**: Technical Lead  
**Due Date**: Before Week 1 starts

---

### Risk 2: Azure Resources Not Provisioned

**Risk ID**: RISK-002  
**Category**: Infrastructure  
**Probability**: MEDIUM (50%)  
**Impact**: HIGH (Deployment blocker)

**Description**: README references `infojp-sandbox` subscription (c59ee575...) but:
- Cosmos DB account may not exist
- Blob Storage may not be configured
- Azure AI Search instance may be missing
- RBAC roles may not be assigned

**Potential Consequences**:
- Cannot deploy schema (Week 1 blocked)
- Provisioning delays (1-3 days for Azure resource creation)
- Cost approval required before provisioning
- Development team idle waiting for infrastructure

**Mitigation Strategy**:
1. **Week 0 Task 0.2**: Validate Azure environment (2-4 hours)
2. Create validation script: `scripts/dev/test-azure-connectivity.py`
3. Document existing resources: `docs/infrastructure/azure-environment-validated.md`
4. If resources missing: Submit Azure resource request immediately
5. **Fallback Option**: Use Cosmos DB emulator for Week 1-2 development

**Status**: 🟡 PARTIALLY MITIGATED - Cosmos DB emulator available for local dev

**Owner**: DevOps Lead  
**Due Date**: Before Week 1 Task 1.3 (schema deployment)

---

### Risk 3: Budget Not Approved

**Risk ID**: RISK-003  
**Category**: Financial  
**Probability**: MEDIUM (40%)  
**Impact**: HIGH (Deployment blocker)

**Description**: No documented budget approval for:
- Cosmos DB RU/s consumption (could be $50-200/month)
- Azure AI Search indexing costs
- Embedding API calls (text-embedding-3-small)
- Blob Storage (minimal cost)

**Potential Consequences**:
- Cannot deploy to Azure (blocked on budget approval)
- Scope reduction required (smaller corpus, lower SLO tiers)
- Cost overruns if not monitored

**Mitigation Strategy**:
1. **Week 0 Task 0.3**: Complete cost modeling (2-3 hours)
2. Create cost analysis: `docs/cost-analysis.xlsx`
3. Present to stakeholder with break-even analysis (CDC vs full reindex)
4. Set up Azure cost alerts ($100/month threshold)
5. **Fallback Option**: Start with free tier / Cosmos DB serverless

**Status**: 🟡 PARTIALLY MITIGATED - Can use Cosmos DB serverless (pay-per-request)

**Owner**: Project Manager  
**Due Date**: Before Week 1 Task 1.3 (schema deployment)

---

## 🟡 High Risks (Week 1-2 Monitoring)

### Risk 4: CanLII Rate Limiting

**Risk ID**: RISK-004  
**Category**: Technical - External Dependency  
**Probability**: HIGH (60%)  
**Impact**: MEDIUM (Performance degradation)

**Description**: CanLII may enforce rate limits:
- Requests per second (RPS) limits
- Daily request quotas
- IP-based blocking for excessive requests

**Potential Consequences**:
- CDC polling takes longer than expected
- SLO violations (cannot meet 24-hour freshness)
- Need to implement exponential backoff
- May need to reduce polling frequency

**Mitigation Strategy**:
1. Monitor 429 (Too Many Requests) responses
2. Implement exponential backoff: `backoff.expo()` decorator
3. Add request throttling: max 1 request per 2 seconds
4. Log all rate limit events for analysis
5. **Fallback Option**: Reduce polling frequency to weekly (SLO tier 3)

**Status**: 🟡 MITIGATED - Retry logic in poll executor design

**Owner**: Backend Developer  
**Monitoring**: Application Insights rate limit metrics

---

### Risk 5: Cosmos DB Throughput Insufficient

**Risk ID**: RISK-005  
**Category**: Infrastructure - Performance  
**Probability**: MEDIUM (40%)  
**Impact**: MEDIUM (Performance degradation)

**Description**: Initial estimate of 400 RU/s may be insufficient for:
- Parallel writes during bulk imports
- High-frequency polling (daily for multiple scopes)
- Complex queries during retrieval

**Potential Consequences**:
- 429 errors from Cosmos DB
- Slow poll_run execution (>10 minutes per 100 cases)
- Need to increase RU/s (higher cost)

**Mitigation Strategy**:
1. Start with autoscale (400-4000 RU/s)
2. Monitor RU/s consumption via Application Insights
3. Optimize queries (use partition keys effectively)
4. Batch writes where possible (up to 100 items)
5. **Fallback Option**: Use provisioned throughput if autoscale too expensive

**Status**: 🟡 MITIGATED - Autoscale provides headroom

**Owner**: Database Administrator  
**Monitoring**: Cosmos DB metrics (RU/s consumption, throttling rate)

---

### Risk 6: Integration Tests Unstable

**Risk ID**: RISK-006  
**Category**: Quality - Testing  
**Probability**: HIGH (70%)  
**Impact**: MEDIUM (Development velocity)

**Description**: Integration tests may be flaky due to:
- External dependency on Azure services
- Network latency variability
- Test data pollution (not cleaning up after tests)
- Race conditions in async operations

**Potential Consequences**:
- CI/CD pipeline failures
- False positives/negatives
- Developer time wasted debugging flaky tests
- Cannot trust test results

**Mitigation Strategy**:
1. Use test fixtures (mock CanLII data)
2. Implement test data cleanup (teardown methods)
3. Add retries for network operations (3 attempts)
4. Use `@pytest.mark.flaky` for known unstable tests
5. Document flaky tests in `docs/test-stability.md`
6. **Fallback Option**: Run integration tests manually before merge

**Status**: 🟡 MITIGATED - Test fixtures + retry logic

**Owner**: QA Engineer  
**Monitoring**: Test pass rate over time

---

## 🟢 Medium Risks (Monitoring Only)

### Risk 7: Performance Targets Missed

**Risk ID**: RISK-007  
**Category**: Performance  
**Probability**: MEDIUM (30%)  
**Impact**: MEDIUM (User experience)

**Description**: May not achieve target of <5 minutes per 100 cases due to:
- Slow CanLII API responses
- Azure service latency
- Inefficient chunking/embedding logic
- Database query performance

**Potential Consequences**:
- Longer poll_run execution times
- Delayed freshness updates
- Higher Azure costs (more RU/s needed)

**Mitigation Strategy**:
1. Establish baselines in Week 2 (measure current performance)
2. Profile code with `cProfile` to identify bottlenecks
3. Optimize hot paths (top 20% of execution time)
4. Parallel processing where possible (asyncio)
5. **Acceptance Criteria**: 90% of polls complete in <10 minutes

**Status**: 🟢 MONITORED - Week 3 performance testing will validate

**Owner**: Performance Engineer  
**Monitoring**: Application Insights duration metrics

---

### Risk 8: Team Availability Gaps

**Risk ID**: RISK-008  
**Category**: Resources  
**Probability**: LOW (20%)  
**Impact**: HIGH (Timeline delay)

**Description**: Key team members unavailable due to:
- Sick leave
- Conflicting priorities
- Knowledge silos (only one person knows CDC architecture)

**Potential Consequences**:
- Development delays (1-2 weeks)
- Lower code quality (rushed work)
- Technical debt accumulation

**Mitigation Strategy**:
1. **Document everything** (architecture, decisions, code patterns)
2. Pair programming for complex modules
3. Code reviews (at least 1 reviewer per PR)
4. Weekly knowledge sharing sessions
5. **Buffer**: Add 20% time buffer to estimates

**Status**: 🟢 MONITORED - Documentation emphasis mitigates

**Owner**: Project Manager  
**Monitoring**: Team velocity tracking

---

## Risk Matrix

| Risk ID | Risk Name | Probability | Impact | Severity | Status | Owner |
|---------|-----------|-------------|--------|----------|--------|-------|
| RISK-001 | CanLII API Availability | HIGH | CRITICAL | 🔴 CRITICAL | Unmitigated | Tech Lead |
| RISK-002 | Azure Resources Missing | MEDIUM | HIGH | 🟡 HIGH | Partial | DevOps |
| RISK-003 | Budget Not Approved | MEDIUM | HIGH | 🟡 HIGH | Partial | PM |
| RISK-004 | CanLII Rate Limiting | HIGH | MEDIUM | 🟡 MEDIUM | Mitigated | Backend Dev |
| RISK-005 | Cosmos DB Throughput | MEDIUM | MEDIUM | 🟡 MEDIUM | Mitigated | DBA |
| RISK-006 | Flaky Integration Tests | HIGH | MEDIUM | 🟡 MEDIUM | Mitigated | QA |
| RISK-007 | Performance Targets | MEDIUM | MEDIUM | 🟢 LOW | Monitored | Perf Eng |
| RISK-008 | Team Availability | LOW | HIGH | 🟢 LOW | Monitored | PM |

---

## Risk Escalation Process

**Trigger Conditions**:
1. Any 🔴 CRITICAL risk remains unmitigated after 2 weeks
2. Two or more 🟡 HIGH risks escalate to CRITICAL
3. Performance degrades >50% below targets
4. Budget exceeds approved amount by >20%

**Escalation Path**:
1. **Level 1**: Project Manager (daily standup)
2. **Level 2**: Technical Lead (weekly review)
3. **Level 3**: Director/Stakeholder (immediate for CRITICAL)

---

## Risk Review Cadence

- **Daily**: Review CRITICAL risks (🔴) during standup
- **Weekly**: Review all HIGH risks (🟡) in team meeting
- **Biweekly**: Update risk register with new risks
- **End of Phase**: Retrospective on risk mitigation effectiveness

---

## Appendix: Risk Definitions

**Probability Levels**:
- **HIGH**: >60% chance of occurring
- **MEDIUM**: 30-60% chance
- **LOW**: <30% chance

**Impact Levels**:
- **CRITICAL**: Project blocker, >2 week delay, or >$10K cost
- **HIGH**: Major feature impact, 1-2 week delay, or >$5K cost
- **MEDIUM**: Feature degradation, <1 week delay, or <$5K cost
- **LOW**: Minor inconvenience, no delay, minimal cost

**Severity Matrix**:
- 🔴 **CRITICAL**: HIGH probability × CRITICAL impact
- 🟡 **HIGH/MEDIUM**: Any combination of MEDIUM/HIGH
- 🟢 **LOW**: LOW probability × any impact, or any × LOW impact

---

**Last Updated**: 2026-02-02  
**Next Review**: 2026-02-09 (weekly)  
**Owner**: Project Manager
