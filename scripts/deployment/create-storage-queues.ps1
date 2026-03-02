# Create Azure Storage Queues for CDC Downstream Processing
# Purpose: Create 5 queues for queue-based downstream action execution
# Version: 1.0.0
# Date: 2026-02-07

param(
    [string]$StorageAccountName = $env:AZURE_STORAGE_ACCOUNT_NAME,
    [string]$ResourceGroup = $env:AZURE_RESOURCE_GROUP,
    [switch]$DryRun
)

# Set UTF-8 encoding for Windows
$env:PYTHONIOENCODING = "utf-8"

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "CDC Azure Storage Queue Creation" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan

if (-not $StorageAccountName) {
    Write-Host "[FAIL] AZURE_STORAGE_ACCOUNT_NAME not set" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[INFO] Storage Account: $StorageAccountName"

if ($DryRun) {
    Write-Host "[INFO] DRY RUN MODE - No actual queue creation" -ForegroundColor Yellow
}

Write-Host ""

# Define CDC queues
$queues = @(
    @{
        Name = "fetch-artifact-queue"
        Description = "Triggers FetchArtifact function (download PDFs/HTML)"
    },
    @{
        Name = "extract-text-queue"
        Description = "Triggers FileFormRecSubmissionPDF (OCR extraction)"
    },
    @{
        Name = "generate-chunks-queue"
        Description = "Triggers TextEnrichment (chunking)"
    },
    @{
        Name = "embed-chunks-queue"
        Description = "Triggers TextEnrichment (embedding generation)"
    },
    @{
        Name = "update-index-queue"
        Description = "Triggers UpdateSearchIndex (Azure AI Search)"
    }
)

$successCount = 0
$failCount = 0

foreach ($queue in $queues) {
    $queueName = $queue.Name
    $description = $queue.Description
    
    Write-Host "[INFO] Creating queue: $queueName" -ForegroundColor Cyan
    Write-Host "       Purpose: $description" -ForegroundColor Gray
    
    if ($DryRun) {
        Write-Host "[DRY-RUN] Would create queue: $queueName" -ForegroundColor Yellow
        $successCount++
    }
    else {
        try {
            # Create queue using Azure CLI
            $result = az storage queue create `
                --name $queueName `
                --account-name $StorageAccountName `
                --auth-mode login `
                2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[PASS] Queue '$queueName' created successfully" -ForegroundColor Green
                $successCount++
            }
            else {
                Write-Host "[FAIL] Queue creation failed: $result" -ForegroundColor Red
                $failCount++
            }
        }
        catch {
            Write-Host "[FAIL] Queue creation error: $_" -ForegroundColor Red
            $failCount++
        }
    }
    
    Write-Host ""
}

# Summary
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "Queue Creation Summary: $successCount/$($queues.Count) queues created" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan

if ($successCount -eq $queues.Count) {
    Write-Host ""
    Write-Host "[PASS] All queues created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Deploy CDC functions (run: python scripts/deployment/deploy-cdc-functions.py)" -ForegroundColor White
    Write-Host "2. Configure queue triggers in function apps" -ForegroundColor White
    Write-Host "3. Test queue message flow" -ForegroundColor White
    exit 0
}
else {
    Write-Host ""
    Write-Host "[FAIL] Some queues failed to create - Review errors above" -ForegroundColor Red
    exit 1
}
