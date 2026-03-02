# CDC DevBox Container Deployment Guide

**Purpose**: Step-by-step guide for deploying CDC system in Microsoft DevBox container  
**Version**: 1.0.0  
**Date**: February 7, 2026  
**Status**: Production-ready deployment instructions

---

## Overview

This guide covers deploying the MS-InfoJP CDC (Change Data Capture) system in a Microsoft DevBox container environment with full Azure connectivity.

**DevBox Benefits**:
- Pre-configured development environment
- Full Azure private endpoint access (no VPN required)
- Consistent across team members
- Isolated from local machine configuration

---

## Prerequisites

### 1. Azure Access Requirements

```powershell
# Verify Azure subscription access
az login --tenant bfb12ca1-7f37-47d5-9cf5-8aa52214a0d8
az account set --subscription "d2d4e571-e0f2-4f6c-901a-f88f7669bcba"

# Required RBAC roles:
# - Cosmos DB Data Contributor (Cosmos DB operations)
# - Storage Blob Data Contributor (Blob + Queue operations)
# - Search Service Contributor (Azure AI Search operations)
# - Key Vault Secrets User (Key Vault access)
```

### 2. Required Azure Resources

**Already Deployed** (from sandbox analysis):
- ✅ **marco-sandbox-cosmos** - Cosmos DB account
- ✅ **marcosand20260203** - Storage account (Blob + Queue)
- ✅ **marco-sandbox-func** - Function App (Consumption Plan)
- ✅ **marcosandkv20260203** - Key Vault
- ✅ **marco-sandbox-search** - Azure AI Search

**No new resources needed** - CDC uses existing sandbox infrastructure!

---

## Step 1: Environment Configuration

### 1.1 Copy Environment Template

```bash
# In DevBox container
cd /workspace/15-cdc
cp .env.template .env
```

### 1.2 Fill Environment Variables

Edit `.env` with your Azure resource details:

```bash
# Azure Credentials
AZURE_SUBSCRIPTION_ID=d2d4e571-e0f2-4f6c-901a-f88f7669bcba
AZURE_TENANT_ID=bfb12ca1-7f37-47d5-9cf5-8aa52214a0d8

# Cosmos DB
AZURE_COSMOSDB_ENDPOINT=https://marco-sandbox-cosmos.documents.azure.com
AZURE_COSMOSDB_DATABASE=cdc-jurisprudence

# Blob Storage
AZURE_STORAGE_ACCOUNT_NAME=marcosand20260203
AZURE_STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
  --name marcosand20260203 \
  --resource-group EsDAICoE-Sandbox \
  --query connectionString -o tsv)

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://marco-sandbox-search.search.windows.net
AZURE_SEARCH_INDEX_NAME=index-jurisprudence

# Function App
AZURE_FUNCTION_APP_NAME=marco-sandbox-func
AZURE_RESOURCE_GROUP=EsDAICoE-Sandbox

# Key Vault
AZURE_KEY_VAULT_URL=https://marcosandkv20260203.vault.azure.net

# CanLII API
CANLII_API_KEY=<YOUR_CANLII_API_KEY>

# DevBox Container Settings
DEVBOX_CONTAINER_NAME=cdc-devbox
DEVBOX_WORKSPACE_PATH=/workspace
LOCAL_DEBUG=false
AZURE_IDENTITY_EXCLUDE_MANAGED_IDENTITY_CREDENTIAL=true
```

### 1.3 Load Environment

```bash
# Load environment variables
export $(cat .env | grep -v '^#' | xargs)
```

---

## Step 2: Validation (Week 0)

### 2.1 Install Python Dependencies

```bash
# Install testing dependencies
pip install -r tests/requirements.txt

# Install deployment dependencies
pip install azure-cosmos azure-storage-blob azure-storage-queue azure-identity
```

### 2.2 Run Connectivity Tests

```bash
# Full validation
python scripts/dev/test-azure-connectivity.py

# Expected output:
# [PASS] Cosmos DB: Create/read/delete successful
# [PASS] Blob Storage: Upload/download/delete successful
# [PASS] Queue Service: Send/receive/delete successful
# [PASS] CanLII API accessible - X cases returned
# [PASS] Function App 'marco-sandbox-func' accessible
# [PASS] Azure Search endpoint accessible
# [PASS] Key Vault accessible - X secrets found
#
# Results: 7/7 tests passed
```

### 2.3 Validate Prerequisites

```bash
# Run test suite
pytest tests/ -v -m unit

# Expected: All unit tests pass
```

---

## Step 3: Schema Deployment (Week 1)

### 3.1 Deploy Cosmos DB Schema

```bash
# Deploy all 12 CDC containers
python scripts/deployment/deploy-cosmos-schema.py

# Expected output:
# [PASS] Database 'cdc-jurisprudence' ready
# [PASS] Container 'corpus_registry' created
# [PASS] Container 'case_registry' created
# [PASS] Container 'case_source_key' created
# [PASS] Container 'case_version' created
# [PASS] Container 'case_text' created
# [PASS] Container 'artifact' created
# [PASS] Container 'poll_run' created
# [PASS] Container 'change_event' created
# [PASS] Container 'scope_definition' created
# [PASS] Container 'policy_version' created
# [PASS] Container 'downstream_action' created
# [PASS] Container 'freshness_metric' created
#
# Deployment Summary: 12 containers processed
```

### 3.2 Create Storage Queues

```powershell
# Create 5 downstream processing queues
pwsh scripts/deployment/create-storage-queues.ps1

# Expected output:
# [PASS] Queue 'fetch-artifact-queue' created successfully
# [PASS] Queue 'extract-text-queue' created successfully
# [PASS] Queue 'generate-chunks-queue' created successfully
# [PASS] Queue 'embed-chunks-queue' created successfully
# [PASS] Queue 'update-index-queue' created successfully
#
# Queue Creation Summary: 5/5 queues created
```

### 3.3 Verify Deployment

```bash
# Verify Cosmos DB containers
az cosmosdb sql container list \
  --account-name marco-sandbox-cosmos \
  --database-name cdc-jurisprudence \
  --resource-group EsDAICoE-Sandbox

# Verify storage queues
az storage queue list \
  --account-name marcosand20260203 \
  --auth-mode login
```

---

## Step 4: Function Deployment (Week 2)

### 4.1 Review Function Architecture

**Existing Functions** (already deployed - will reuse):
- `FileFormRecSubmissionPDF` - OCR extraction (reuse for extract_text action)
- `TextEnrichment` - Chunking + embedding (reuse for generate_chunks + embed_chunks actions)

**New CDC Functions** (to be implemented):
- `Tier1CDCPoller` - Timer trigger (daily 2AM UTC) - Polls CanLII metadata
- `FetchArtifact` - Queue trigger (fetch-artifact-queue) - Downloads PDFs/HTML
- `ProcessChangeEvent` - Queue trigger (change-event processing)
- `UpdateSearchIndex` - Queue trigger (update-index-queue) - Updates Azure AI Search

### 4.2 Deploy CDC Functions

```bash
# Deploy CDC functions (implementation in Week 2)
# python scripts/deployment/deploy-cdc-functions.py

echo "[INFO] CDC functions to be implemented in Week 2"
echo "[INFO] Will integrate with existing FileFormRecSubmissionPDF + TextEnrichment"
```

---

## Step 5: Professional Components Integration

### 5.1 Enable Professional Components

Already configured in `.env`:

```bash
# Professional Components Configuration
ENABLE_DEBUG_ARTIFACT_COLLECTOR=true
ENABLE_SESSION_MANAGER=true
ENABLE_STRUCTURED_ERROR_HANDLER=true
SESSION_CHECKPOINT_INTERVAL=100
```

### 5.2 Create Evidence Directories

```bash
# Create professional component directories
mkdir -p debug/cdc-poller
mkdir -p sessions/tier1-poller
mkdir -p logs/errors
mkdir -p logs/validation
```

### 5.3 Verify Component Integration

```bash
# Test professional components (when implemented)
# pytest tests/test_professional_components.py -v
```

---

## Step 6: Monitoring Setup

### 6.1 Configure Application Insights

```bash
# Get Application Insights connection string
az monitor app-insights component show \
  --app <app-insights-name> \
  --resource-group EsDAICoE-Sandbox \
  --query connectionString -o tsv

# Add to .env
echo "APPLICATIONINSIGHTS_CONNECTION_STRING=<connection-string>" >> .env
```

### 6.2 Enable Telemetry

```bash
# In function apps, add:
# - azure-monitor-opentelemetry
# - opentelemetry-api
# - opentelemetry-sdk
```

---

## Step 7: Validation & Testing

### 7.1 Run Full Test Suite

```bash
# Run all tests
pytest tests/ -v

# Run integration tests only (requires Azure access)
pytest tests/ -v -m integration

# Run acceptance tests (end-to-end scenarios)
pytest tests/ -v -m acceptance
```

### 7.2 Manual Smoke Test

```bash
# Test Tier1CDCPoller manually (when implemented)
# python scripts/dev/test-tier1-poller.py --scope-id SST-GD-EN-rolling-24mo --dry-run
```

---

## DevBox-Specific Considerations

### Container Persistence

```bash
# Mount workspace for persistence
docker run -v /workspace:/workspace cdc-devbox

# Logs, checkpoints, debug artifacts persist across container restarts
```

### Network Access

```bash
# DevBox has full private endpoint access
# No VPN required for:
# - Cosmos DB private endpoints
# - Storage Account private endpoints
# - Azure AI Search private endpoints
# - Key Vault private endpoints
```

### Credential Management

```bash
# Use DefaultAzureCredential in DevBox
# Credential chain:
# 1. Environment variables (if set)
# 2. Managed Identity (if running in Azure)
# 3. Azure CLI (primary for DevBox)
# 4. Visual Studio Code
# 5. Azure PowerShell
```

---

## Troubleshooting

### Issue 1: Cosmos DB Connection Timeout

**Symptom**: `azure.cosmos.errors.CosmosHttpResponseError: Request timeout`  
**Cause**: Network connectivity or private endpoint configuration  
**Solution**:

```bash
# Verify Cosmos DB endpoint reachable
curl -I https://marco-sandbox-cosmos.documents.azure.com

# Check private endpoint status
az cosmosdb show --name marco-sandbox-cosmos \
  --resource-group EsDAICoE-Sandbox \
  --query "privateEndpointConnections"
```

### Issue 2: Queue Not Found

**Symptom**: `azure.core.exceptions.ResourceNotFoundError: Queue not found`  
**Cause**: Queue not created or wrong storage account  
**Solution**:

```bash
# List existing queues
az storage queue list \
  --account-name marcosand20260203 \
  --auth-mode login

# Recreate queues
pwsh scripts/deployment/create-storage-queues.ps1
```

### Issue 3: CANLII_API_KEY Invalid

**Symptom**: `[FAIL] CanLII API returned 401: Unauthorized`  
**Cause**: API key not set or expired  
**Solution**:

```bash
# Verify API key in .env
cat .env | grep CANLII_API_KEY

# Test API key manually
curl -H "API-Key: $CANLII_API_KEY" https://api.canlii.org/v1/caseBrowse/en/sst/
```

---

## Next Steps

After successful deployment:

1. **Week 2**: Implement CDC functions (Tier1CDCPoller, FetchArtifact, ProcessChangeEvent)
2. **Week 3**: Integrate professional components (SessionManager, DebugArtifactCollector)
3. **Week 4**: End-to-end testing with real CanLII data
4. **Week 5**: Production deployment preparation

---

## Support & Resources

- **Documentation**: [CDC-IMPLEMENTATION-START.md](CDC-IMPLEMENTATION-START.md)
- **Architecture**: [cdc-mvp-design.md](cdc-mvp-design.md)
- **Acceptance Tests**: [acceptance-tests.md](acceptance-tests.md)
- **Troubleshooting**: [IMPLEMENTATION-RISKS.md](IMPLEMENTATION-RISKS.md)
