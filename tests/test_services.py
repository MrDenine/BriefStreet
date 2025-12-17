# tests/test_services.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services import market_data, llm_service
from app.models.sentiment import AnalysisResponse
from app.models.market_data import (
    TranscriptResponse, 
    FinancialMetricsResponse, 
    FinancialMetrics,
    CashFlowStatement
)

@pytest.mark.asyncio
async def test_get_earnings_transcript_success():
    """ทดสอบดึง transcript จาก provider สำเร็จ"""
    
    mock_transcript = TranscriptResponse(
        date="2024-10-25",
        content="Earnings call transcript..."
    )
    
    with patch("app.data_sources.fmp_provider.FMPProvider.get_transcript", new=AsyncMock(return_value=mock_transcript)):
        result = await market_data.get_earnings_transcript("AAPL")
        
        assert isinstance(result, TranscriptResponse)
        assert result.date == "2024-10-25"
        assert "transcript" in result.content

@pytest.mark.asyncio
async def test_get_earnings_transcript_fallback_to_mock():
    """ทดสอบเมื่อ primary provider ล้มเหลว ควรใช้ Mock"""
    
    mock_transcript = TranscriptResponse(
        date="2024-11-01",
        content="Mock earnings call transcript for AAPL"
    )
    
    # FMP ล้มเหลว แต่ Mock สำเร็จ
    with patch("app.data_sources.fmp_provider.FMPProvider.get_transcript", side_effect=Exception("API Error")):
        with patch("app.data_sources.mock_provider.MockProvider.get_transcript", new=AsyncMock(return_value=mock_transcript)):
            result = await market_data.get_earnings_transcript("AAPL", fallback=True)
            
            assert isinstance(result, TranscriptResponse)
            assert result.date == "2024-11-01"

@pytest.mark.asyncio
async def test_get_financial_metrics():
    """ทดสอบดึง financial metrics"""
    
    mock_metrics = FinancialMetricsResponse(
        metrics=FinancialMetrics(
            peRatioTTM=28.5,
            pbRatioTTM=45.2,
            netIncomePerShareTTM=6.42
        ),
        price=182.50,
        cash_flows=[
            CashFlowStatement(date="2024-09-30", freeCashFlow=26850000000)
        ]
    )
    
    with patch("app.data_sources.fmp_provider.FMPProvider.get_financial_metrics", new=AsyncMock(return_value=mock_metrics)):
        result = await market_data.get_financial_metrics("AAPL")
        
        assert isinstance(result, FinancialMetricsResponse)
        assert result.price == 182.50
        assert result.metrics.peRatioTTM == 28.5

@pytest.mark.skip(reason="OpenAI client mocking requires actual API key or complex setup")
def test_analyze_transcript():
    """ทดสอบการวิเคราะห์ Transcript (Mock OpenAI)"""
    
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.parsed = AnalysisResponse(
        symbol="AAPL",
        overall_sentiment_score=80,
        ceo_tone="Confident",
        highlights=[]
    )
    
    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.beta.chat.completions.parse.return_value = mock_completion
        
        # Re-import เพื่อใช้ mocked client
        from importlib import reload
        from app.services import llm_service
        reload(llm_service)
        
        result = llm_service.analyze_transcript("AAPL", "Sample transcript")
        
        assert isinstance(result, AnalysisResponse)
        assert result.symbol == "AAPL"
        assert result.overall_sentiment_score == 80

@pytest.mark.asyncio
async def test_chat_with_transcript():
    """ทดสอบ Chat Function"""
    
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = "Revenue increased by 25%"
    
    with patch("app.services.llm_service.client.chat.completions.create", new=AsyncMock(return_value=mock_completion)):
        result = await llm_service.chat_with_transcript(
            "AAPL", 
            "Sample transcript with revenue data",
            "How much did revenue grow?"
        )
        
        assert isinstance(result, str)
        assert "25%" in result
