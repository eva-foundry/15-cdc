"""Pytest configuration and shared fixtures for CDC tests

Purpose: Common test fixtures for all CDC test modules
Version: 1.0.0
Date: 2026-02-07
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock
from datetime import datetime

# Set UTF-8 encoding for Windows
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')


@pytest.fixture
def project_root():
    """Return project root directory"""
    return Path(__file__).parent.parent


@pytest.fixture
def test_data_dir(project_root):
    """Return test data directory"""
    test_dir = project_root / "tests" / "test_data"
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


@pytest.fixture
def mock_cosmos_client():
    """Mock Cosmos DB client"""
    mock_client = Mock()
    mock_database = Mock()
    mock_container = Mock()
    
    # Setup mock chain
    mock_client.create_database_if_not_exists.return_value = mock_database
    mock_database.create_container_if_not_exists.return_value = mock_container
    
    # Mock container operations
    mock_container.upsert_item.return_value = {"id": "test", "status": "created"}
    mock_container.read_item.return_value = {"id": "test", "data": "mock"}
    mock_container.query_items.return_value = []
    
    return mock_client


@pytest.fixture
def mock_blob_service():
    """Mock Azure Blob Storage client"""
    mock_service = Mock()
    mock_container = Mock()
    
    mock_service.create_container.return_value = mock_container
    mock_container.upload_blob.return_value = Mock(name="test.txt")
    mock_container.download_blob.return_value = Mock(readall=lambda: b"test content")
    
    return mock_service


@pytest.fixture
def mock_queue_service():
    """Mock Azure Queue Storage client"""
    mock_service = Mock()
    mock_queue = Mock()
    mock_message = Mock()
    mock_message.content = "test message"
    mock_message.id = "msg-123"
    
    mock_service.create_queue.return_value = mock_queue
    mock_queue.send_message.return_value = None
    mock_queue.receive_messages.return_value = [mock_message]
    
    return mock_service


@pytest.fixture
def mock_search_client():
    """Mock Azure AI Search client"""
    mock_client = Mock()
    mock_client.search.return_value = []
    mock_client.upload_documents.return_value = [{"status": "succeeded"}]
    return mock_client


@pytest.fixture
def sample_case_metadata():
    """Sample CanLII case metadata for testing"""
    return {
        "caseId": {
            "en": "/en/sst-general-division/2024/2024sst100"
        },
        "databaseId": "sst",
        "title": "Smith v. Minister of Employment and Social Development",
        "citation": "2024 SST 100",
        "decisionDate": "2024-01-15",
        "language": "en",
        "keywords": ["employment insurance", "appeal"],
        "url": "https://canlii.ca/t/abc123"
    }


@pytest.fixture
def sample_poll_run():
    """Sample poll_run record for testing"""
    return {
        "poll_run_id": "01JGQP8ABC123",
        "scope_id": "SST-GD-EN-rolling-24mo",
        "started_at_utc": datetime.utcnow().isoformat(),
        "status": "running",
        "cases_checked": 0,
        "changes_detected": 0,
        "policy_version": "0.1.0"
    }


@pytest.fixture
def sample_change_event():
    """Sample change_event record for testing"""
    return {
        "change_event_id": "01JGQP5DEF456",
        "poll_run_id": "01JGQP8ABC123",
        "case_id": "01JGQP2VWXYZ789",
        "change_class": "content",
        "reason": "PDF content hash changed",
        "status": "detected",
        "actions_required": ["fetch_artifact", "extract_text", "generate_chunks", "embed_chunks", "update_index"]
    }


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Setup test environment variables"""
    test_env = {
        "AZURE_COSMOSDB_ENDPOINT": "https://test-cosmos.documents.azure.com",
        "AZURE_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https;AccountName=testaccount;AccountKey=test==;EndpointSuffix=core.windows.net",
        "AZURE_SEARCH_ENDPOINT": "https://test-search.search.windows.net",
        "CANLII_API_KEY": "test-api-key",
        "LOCAL_DEBUG": "true",
        "PYTHONIOENCODING": "utf-8"
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def professional_components(project_root):
    """Mock professional components"""
    from unittest.mock import AsyncMock
    
    components = {
        "debug_collector": Mock(),
        "session_manager": Mock(),
        "error_handler": Mock()
    }
    
    # Setup async methods
    components["debug_collector"].capture_state = AsyncMock()
    components["session_manager"].save_checkpoint = Mock()
    components["session_manager"].load_latest_checkpoint = Mock(return_value=None)
    components["error_handler"].log_error = Mock()
    
    return components
