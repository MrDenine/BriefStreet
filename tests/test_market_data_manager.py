# tests/test_market_data_manager.py
"""
Tests for Market Data Manager (Orchestrator Service)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.market_data_manager import MarketDataManager
from app.models.market_data import TranscriptResponse, FinancialMetricsResponse
from app.models.market_data_storage import TranscriptStorage, FinancialDataStorage
from app.core.exceptions import DataFetchException


# ==================== Fixtures ====================

@pytest.fixture
def mock_market_data_repo():
    """Mock IMarketDataRepository"""
    repo = AsyncMock()
    return repo


@pytest.fixture
def manager(mock_market_data_repo):
    """MarketDataManager instance with mocked dependencies"""
    return MarketDataManager(mock_market_data_repo)


@pytest.fixture
def sample_transcript_response():
    """Sample transcript response from provider"""
    return TranscriptResponse(
        date="2024-10-31",
        content="Q3 2024 earnings call transcript content..."
    )


@pytest.fixture
def sample_financial_metrics():
    """Sample financial metrics response"""
    from app.models.market_data import FinancialMetrics, CashFlowStatement
    return FinancialMetricsResponse(
        metrics=FinancialMetrics(
            peRatioTTM=28.5,
            pbRatioTTM=5.2,
            returnOnEquityTTM=0.45
        ),
        price=180.50,
        cash_flows=[
            CashFlowStatement(
                date="2024-09-30",
                freeCashFlow=28000000000
            )
        ]
    )


@pytest.fixture
def sample_transcript_storage():
    """Sample stored transcript"""
    return TranscriptStorage(
        id=1,
        symbol="AAPL",
        quarter=3,
        year=2024,
        quarter_date=datetime(2024, 10, 31),
        content="Q3 2024 earnings call transcript content...",
        extra_data={"source": "FMP"}
    )


@pytest.fixture
def sample_financial_storage():
    """Sample stored financial data"""
    return FinancialDataStorage(
        id=1,
        symbol="AAPL",
        year=2024,
        quarter=3,
        data_type="income_statement",
        data={"metrics": [{"revenue": 89000000000}]},
        extra_data={"source": "FMP"}
    )


# ==================== sync_transcript Tests ====================

@pytest.mark.asyncio
async def test_sync_transcript_success(
    manager, 
    mock_market_data_repo,
    sample_transcript_response,
    sample_transcript_storage
):
    """Test successful transcript sync"""
    # Mock: No existing data
    manager.storage_service.get_transcript = AsyncMock(return_value=None)
    
    # Mock: Provider returns transcript
    with patch('app.services.market_data_manager.market_data.get_earnings_transcript') as mock_fetch:
        mock_fetch.return_value = sample_transcript_response
        
        # Mock: Storage saves successfully
        manager.storage_service.save_transcript = AsyncMock(return_value=sample_transcript_storage)
        
        # Execute
        result = await manager.sync_transcript("AAPL", 3, 2024)
        
        # Assert
        assert result["status"] == "synced"
        assert result["symbol"] == "AAPL"
        assert result["quarter"] == 3
        assert result["year"] == 2024
        assert result["transcript_id"] == 1
        assert result["content_length"] > 0
        
        # Verify fetch was called with fallback=True
        mock_fetch.assert_called_once_with(symbol="AAPL", quarter=3, year=2024, fallback=True)
        
        # Verify save was called
        manager.storage_service.save_transcript.assert_called_once()


@pytest.mark.asyncio
async def test_sync_transcript_already_exists(manager, sample_transcript_storage):
    """Test sync when transcript already exists in database"""
    # Mock: Existing data found
    manager.storage_service.get_transcript = AsyncMock(return_value=sample_transcript_storage)
    
    # Execute (without force_refresh)
    result = await manager.sync_transcript("AAPL", 3, 2024, force_refresh=False)
    
    # Assert
    assert result["status"] == "exists"
    assert result["symbol"] == "AAPL"
    assert result["message"] == "Data already in database"
    
    # Verify save was NOT called
    manager.storage_service.save_transcript = AsyncMock()
    manager.storage_service.save_transcript.assert_not_called()


@pytest.mark.asyncio
async def test_sync_transcript_force_refresh(
    manager,
    sample_transcript_response,
    sample_transcript_storage
):
    """Test force refresh bypasses existing data check"""
    # Mock: Existing data found, but force_refresh=True
    manager.storage_service.get_transcript = AsyncMock(return_value=sample_transcript_storage)
    
    with patch('app.services.market_data_manager.market_data.get_earnings_transcript') as mock_fetch:
        mock_fetch.return_value = sample_transcript_response
        manager.storage_service.save_transcript = AsyncMock(return_value=sample_transcript_storage)
        
        # Execute with force_refresh=True
        result = await manager.sync_transcript("AAPL", 3, 2024, force_refresh=True)
        
        # Assert: Data was fetched and saved despite existing
        assert result["status"] == "synced"
        mock_fetch.assert_called_once()
        manager.storage_service.save_transcript.assert_called_once()


@pytest.mark.asyncio
async def test_sync_transcript_fetch_fails(manager):
    """Test when provider fails to fetch transcript"""
    # Mock: No existing data
    manager.storage_service.get_transcript = AsyncMock(return_value=None)
    
    # Mock: Provider raises exception
    with patch('app.services.market_data_manager.market_data.get_earnings_transcript') as mock_fetch:
        mock_fetch.side_effect = Exception("API rate limit exceeded")
        
        # Execute and expect DataFetchException
        with pytest.raises(DataFetchException) as exc_info:
            await manager.sync_transcript("AAPL", 3, 2024)
        
        assert "transcript for AAPL" in exc_info.value.message


@pytest.mark.asyncio
async def test_sync_transcript_empty_content(manager, sample_transcript_storage):
    """Test when transcript content is empty"""
    # Mock: No existing data
    manager.storage_service.get_transcript = AsyncMock(return_value=None)
    
    # Mock: Provider returns empty transcript
    empty_transcript = TranscriptResponse(
        date="2024-10-31",
        content=""  # Empty content
    )
    
    with patch('app.services.market_data_manager.market_data.get_earnings_transcript') as mock_fetch:
        mock_fetch.return_value = empty_transcript
        
        # Execute
        result = await manager.sync_transcript("AAPL", 3, 2024)
        
        # Assert
        assert result["status"] == "empty"
        assert result["message"] == "Transcript is empty"
        
        # Verify save was NOT called
        manager.storage_service.save_transcript = AsyncMock()
        manager.storage_service.save_transcript.assert_not_called()


# ==================== sync_financial_data Tests ====================

@pytest.mark.asyncio
async def test_sync_financial_data_success(
    manager,
    sample_financial_metrics,
    sample_financial_storage
):
    """Test successful financial data sync"""
    # Mock: No existing data
    manager.storage_service.get_financial_data = AsyncMock(return_value=None)
    
    # Mock: Provider returns metrics
    with patch('app.services.market_data_manager.market_data.get_financial_metrics') as mock_fetch:
        mock_fetch.return_value = sample_financial_metrics
        
        # Mock: Storage saves successfully
        manager.storage_service.save_financial_data = AsyncMock(return_value=sample_financial_storage)
        
        # Execute
        result = await manager.sync_financial_data("AAPL", 2024, quarter=3)
        
        # Assert
        assert result["status"] == "synced"
        assert result["symbol"] == "AAPL"
        assert result["year"] == 2024
        assert result["quarter"] == 3
        assert result["financial_data_id"] == 1
        
        # Verify fetch was called with fallback=True
        mock_fetch.assert_called_once()


@pytest.mark.asyncio
async def test_sync_financial_data_already_exists(manager, sample_financial_storage):
    """Test sync when financial data already exists"""
    # Mock: Existing data found
    manager.storage_service.get_financial_data = AsyncMock(return_value=sample_financial_storage)
    
    # Execute
    result = await manager.sync_financial_data("AAPL", 2024, quarter=3, force_refresh=False)
    
    # Assert
    assert result["status"] == "exists"
    assert result["message"] == "Data already in database"


@pytest.mark.asyncio
async def test_sync_financial_data_fetch_fails(manager):
    """Test when provider fails to fetch financial data"""
    # Mock: No existing data
    manager.storage_service.get_financial_data = AsyncMock(return_value=None)
    
    # Mock: Provider raises exception
    with patch('app.services.market_data_manager.market_data.get_financial_metrics') as mock_fetch:
        mock_fetch.side_effect = Exception("Invalid symbol")
        
        # Execute and expect DataFetchException
        with pytest.raises(DataFetchException) as exc_info:
            await manager.sync_financial_data("INVALID", 2024, quarter=3)
        
        assert "financial data for INVALID" in exc_info.value.message


@pytest.mark.asyncio
async def test_sync_financial_data_empty_metrics(manager):
    """Test when metrics response is empty"""
    # Mock: No existing data
    manager.storage_service.get_financial_data = AsyncMock(return_value=None)
    
    # Mock: Provider returns None metrics (simulating no data)
    # Since the validation checks `if not metrics.metrics`, 
    # we need to make metrics itself None or falsy
    with patch('app.services.market_data_manager.market_data.get_financial_metrics') as mock_fetch:
        # Create a mock response where metrics is None
        mock_response = MagicMock()
        mock_response.metrics = None
        mock_fetch.return_value = mock_response
        
        # Execute
        result = await manager.sync_financial_data("AAPL", 2024, quarter=3)
        
        # Assert
        assert result["status"] == "empty"
        assert result["message"] == "Financial data is empty"


# ==================== sync_all Tests ====================

@pytest.mark.asyncio
async def test_sync_all_success(
    manager,
    sample_transcript_response,
    sample_financial_metrics,
    sample_transcript_storage,
    sample_financial_storage
):
    """Test sync_all when both operations succeed"""
    # Mock: No existing data
    manager.storage_service.get_transcript = AsyncMock(return_value=None)
    manager.storage_service.get_financial_data = AsyncMock(return_value=None)
    
    # Mock: Providers return data
    with patch('app.services.market_data_manager.market_data.get_earnings_transcript') as mock_transcript, \
         patch('app.services.market_data_manager.market_data.get_financial_metrics') as mock_metrics:
        
        mock_transcript.return_value = sample_transcript_response
        mock_metrics.return_value = sample_financial_metrics
        
        # Mock: Storage saves
        manager.storage_service.save_transcript = AsyncMock(return_value=sample_transcript_storage)
        manager.storage_service.save_financial_data = AsyncMock(return_value=sample_financial_storage)
        
        # Execute
        result = await manager.sync_all("AAPL", 3, 2024)
        
        # Assert
        assert result["status"] == "success"
        assert result["message"] == "All data synced successfully"
        assert result["transcript"]["status"] == "synced"
        assert result["financial_data"]["status"] == "synced"
        assert len(result["errors"]) == 0


@pytest.mark.asyncio
async def test_sync_all_partial_success(
    manager,
    sample_transcript_response,
    sample_transcript_storage
):
    """Test sync_all when only transcript succeeds"""
    # Mock: No existing data
    manager.storage_service.get_transcript = AsyncMock(return_value=None)
    manager.storage_service.get_financial_data = AsyncMock(return_value=None)
    
    with patch('app.services.market_data_manager.market_data.get_earnings_transcript') as mock_transcript, \
         patch('app.services.market_data_manager.market_data.get_financial_metrics') as mock_metrics:
        
        # Transcript succeeds
        mock_transcript.return_value = sample_transcript_response
        manager.storage_service.save_transcript = AsyncMock(return_value=sample_transcript_storage)
        
        # Financial data fails
        mock_metrics.side_effect = Exception("API error")
        
        # Execute
        result = await manager.sync_all("AAPL", 3, 2024)
        
        # Assert
        assert result["status"] == "partial"
        assert result["message"] == "Some data synced with errors"
        assert result["transcript"]["status"] == "synced"
        assert result["financial_data"] is None
        assert len(result["errors"]) == 1
        assert result["errors"][0]["type"] == "financial_data"


@pytest.mark.asyncio
async def test_sync_all_complete_failure(manager):
    """Test sync_all when both operations fail"""
    # Mock: No existing data
    manager.storage_service.get_transcript = AsyncMock(return_value=None)
    manager.storage_service.get_financial_data = AsyncMock(return_value=None)
    
    with patch('app.services.market_data_manager.market_data.get_earnings_transcript') as mock_transcript, \
         patch('app.services.market_data_manager.market_data.get_financial_metrics') as mock_metrics:
        
        # Both fail
        mock_transcript.side_effect = Exception("Transcript API error")
        mock_metrics.side_effect = Exception("Metrics API error")
        
        # Execute
        result = await manager.sync_all("AAPL", 3, 2024)
        
        # Assert
        assert result["status"] == "failed"
        assert result["message"] == "All sync operations failed"
        assert result["transcript"] is None
        assert result["financial_data"] is None
        assert len(result["errors"]) == 2


@pytest.mark.asyncio
async def test_sync_all_with_force_refresh(
    manager,
    sample_transcript_response,
    sample_financial_metrics,
    sample_transcript_storage,
    sample_financial_storage
):
    """Test sync_all with force_refresh bypasses existing checks"""
    # Mock: Existing data
    manager.storage_service.get_transcript = AsyncMock(return_value=sample_transcript_storage)
    manager.storage_service.get_financial_data = AsyncMock(return_value=sample_financial_storage)
    
    with patch('app.services.market_data_manager.market_data.get_earnings_transcript') as mock_transcript, \
         patch('app.services.market_data_manager.market_data.get_financial_metrics') as mock_metrics:
        
        mock_transcript.return_value = sample_transcript_response
        mock_metrics.return_value = sample_financial_metrics
        
        manager.storage_service.save_transcript = AsyncMock(return_value=sample_transcript_storage)
        manager.storage_service.save_financial_data = AsyncMock(return_value=sample_financial_storage)
        
        # Execute with force_refresh=True
        result = await manager.sync_all("AAPL", 3, 2024, force_refresh=True)
        
        # Assert: Both were fetched and saved
        assert result["status"] == "success"
        mock_transcript.assert_called_once()
        mock_metrics.assert_called_once()


# ==================== Integration Tests ====================

@pytest.mark.asyncio
async def test_manager_initialization(mock_market_data_repo):
    """Test MarketDataManager initialization"""
    manager = MarketDataManager(mock_market_data_repo)
    
    assert manager.storage_service is not None
    assert hasattr(manager, 'sync_transcript')
    assert hasattr(manager, 'sync_financial_data')
    assert hasattr(manager, 'sync_all')


@pytest.mark.asyncio
async def test_sync_transcript_metadata_includes_source(
    manager,
    sample_transcript_response,
    sample_transcript_storage
):
    """Test that saved transcript includes source metadata"""
    manager.storage_service.get_transcript = AsyncMock(return_value=None)
    
    with patch('app.services.market_data_manager.market_data.get_earnings_transcript') as mock_fetch:
        mock_fetch.return_value = sample_transcript_response
        
        # Capture the call arguments
        save_call_args = None
        async def capture_save(**kwargs):
            nonlocal save_call_args
            save_call_args = kwargs
            return sample_transcript_storage
        
        manager.storage_service.save_transcript = capture_save
        
        # Execute
        await manager.sync_transcript("AAPL", 3, 2024)
        
        # Assert: extra_data includes source and timestamp
        assert save_call_args is not None
        assert "extra_data" in save_call_args
        assert save_call_args["extra_data"]["source"] == "FMP"
        assert "fetched_at" in save_call_args["extra_data"]
