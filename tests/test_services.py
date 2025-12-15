# tests/test_services.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services import market_data, llm_service
from app.models.sentiment import AnalysisResponse

@pytest.mark.asyncio
async def test_get_mock_transcript():
    """ทดสอบ Mock Transcript"""
    result = await market_data.get_mock_transcript("AAPL")
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert "date" in result[0]
    assert "content" in result[0]
    assert "AAPL" in result[0]["content"]

@pytest.mark.asyncio
async def test_get_earnings_transcript_success():
    """ทดสอบดึงข้อมูลจริงจาก API สำเร็จ"""
    
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "date": "2024-10-25",
            "content": "Earnings call transcript..."
        }
    ]
    
    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_response)):
        with patch("app.core.config.settings.FMP_API_KEY", "test_key"):
            result = await market_data.get_earnings_transcript("AAPL")
            
            assert "date" in result
            assert "content" in result
            assert result["date"] == "2024-10-25"

@pytest.mark.asyncio
async def test_get_earnings_transcript_fallback_to_mock():
    """ทดสอบเมื่อ API ล้มเหลว ควรใช้ Mock"""
    
    with patch("httpx.AsyncClient.get", side_effect=Exception("API Error")):
        with patch("app.core.config.settings.FMP_API_KEY", "test_key"):
            result = await market_data.get_earnings_transcript("AAPL")
            
            # ควรได้ Mock Data กลับมา
            assert isinstance(result, list) or isinstance(result, dict)

@pytest.mark.asyncio
async def test_get_earnings_transcript_no_api_key():
    """ทดสอบเมื่อไม่มี API Key"""
    
    with patch("app.core.config.settings.FMP_API_KEY", "xxxxxxxx"):
        result = await market_data.get_earnings_transcript("AAPL")
        
        # ควรใช้ Mock Data
        assert isinstance(result, list)

def test_analyze_transcript():
    """ทดสอบการวิเคราะห์ Transcript (Mock OpenAI)"""
    
    mock_completion = MagicMock()
    mock_completion.choices[0].message.parsed = AnalysisResponse(
        symbol="AAPL",
        overall_sentiment_score=80,
        ceo_tone="Confident",
        highlights=[]
    )
    
    with patch("app.services.llm_service.client.beta.chat.completions.parse", return_value=mock_completion):
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
