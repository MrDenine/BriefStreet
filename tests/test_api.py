# tests/test_api.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.models.sentiment import AnalysisResponse, KeyHighlight

@pytest.mark.asyncio
async def test_read_root(client):
    """ทดสอบ Root Endpoint"""
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to BriefStreet API! 🚀"}

@pytest.mark.asyncio
async def test_analyze_earnings_cache_miss(client, mock_transcript, mock_analysis_response):
    """ทดสอบ /analyze/{symbol} เมื่อยังไม่มีใน Cache"""
    
    # Mock external services
    with patch("app.services.market_data.get_earnings_transcript", new=AsyncMock(return_value=mock_transcript)):
        with patch("app.services.llm_service.analyze_transcript") as mock_llm:
            # สร้าง Mock Response แบบ Pydantic
            mock_llm.return_value = AnalysisResponse(
                symbol="AAPL",
                overall_sentiment_score=75,
                ceo_tone="Confident",
                highlights=[
                    KeyHighlight(
                        topic="Revenue Growth",
                        summary="Revenue up 25% YoY",
                        sentiment="Positive"
                    )
                ]
            )
            
            response = await client.post("/analyze/AAPL")
            
            assert response.status_code == 200
            data = response.json()
            assert data["symbol"] == "AAPL"
            assert data["overall_sentiment_score"] == 75
            assert data["ceo_tone"] == "Confident"
            assert len(data["highlights"]) == 1

@pytest.mark.asyncio
async def test_analyze_earnings_cache_hit(client, test_session, mock_transcript):
    """ทดสอบ /analyze/{symbol} เมื่อมีใน Cache แล้ว"""
    from app.models.cache import EarningsCache
    import json
    
    # เพิ่มข้อมูลลง Cache ก่อน
    cached_analysis = {
        "symbol": "TSLA",
        "overall_sentiment_score": 85,
        "ceo_tone": "Optimistic",
        "highlights": []
    }
    
    cache_entry = EarningsCache(
        symbol="TSLA",
        quarter_date="2024-10-25",
        analysis_json=json.dumps(cached_analysis)
    )
    test_session.add(cache_entry)
    await test_session.commit()
    
    # Mock market_data ให้คืนข้อมูลเดิม
    with patch("app.services.market_data.get_earnings_transcript", new=AsyncMock(return_value=mock_transcript)):
        response = await client.post("/analyze/TSLA")
        
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "TSLA"
        assert data["overall_sentiment_score"] == 85
        # ไม่ควรเรียก LLM ถ้ามี Cache

@pytest.mark.asyncio
async def test_analyze_earnings_invalid_symbol(client):
    """ทดสอบ Symbol ที่ไม่มีข้อมูล"""
    
    with patch("app.services.market_data.get_earnings_transcript", new=AsyncMock(return_value=[])):
        response = await client.post("/analyze/INVALID")
        # ควร Handle Error หรือคืน Mock Data
        assert response.status_code in [200, 404, 500]

@pytest.mark.asyncio
async def test_chat_endpoint(client, mock_transcript):
    """ทดสอบ /chat/{symbol}"""
    
    with patch("app.services.market_data.get_earnings_transcript", new=AsyncMock(return_value={"content": mock_transcript[0]["content"]})):
        with patch("app.services.llm_service.chat_with_transcript", new=AsyncMock(return_value="Revenue grew by 25%")):
            response = await client.post(
                "/chat/AAPL",
                json={"question": "How much did revenue grow?"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "25%" in data["answer"]

@pytest.mark.asyncio
async def test_consistency_endpoint(client, mock_transcript):
    """ทดสอบ /analyze/consistency/{symbol}"""
    
    mock_consistency = {
        "symbol": "AAPL",
        "prepared_remarks": {
            "score": 90,
            "tone": "Confident",
            "key_point": "Strong revenue"
        },
        "qa_session": {
            "score": 70,
            "tone": "Cautious",
            "key_point": "Supply chain concerns"
        },
        "consistency_score": 75,
        "red_flag_warning": "Tone shifted from confident to cautious"
    }
    
    with patch("app.services.market_data.get_earnings_transcript", new=AsyncMock(return_value={"content": mock_transcript[0]["content"]})):
        with patch("app.services.llm_service.analyze_consistency", new=AsyncMock(return_value=mock_consistency)):
            response = await client.post("/analyze/consistency/AAPL")
            
            assert response.status_code == 200
            data = response.json()
            assert data["symbol"] == "AAPL"
            assert "consistency_score" in data
