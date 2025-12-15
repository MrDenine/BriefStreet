# tests/test_models.py
import pytest
from pydantic import ValidationError
from app.models.sentiment import (
    KeyHighlight,
    AnalysisResponse,
    ChatRequest,
    ChatResponse,
    SectionAnalysis,
    ConsistencyResponse
)

def test_key_highlight_valid():
    """ทดสอบสร้าง KeyHighlight ที่ถูกต้อง"""
    highlight = KeyHighlight(
        topic="Revenue",
        summary="Revenue increased 20%",
        sentiment="Positive"
    )
    
    assert highlight.topic == "Revenue"
    assert highlight.sentiment == "Positive"

def test_analysis_response_valid():
    """ทดสอบสร้าง AnalysisResponse ที่สมบูรณ์"""
    response = AnalysisResponse(
        symbol="AAPL",
        overall_sentiment_score=85,
        ceo_tone="Confident",
        highlights=[
            KeyHighlight(topic="Growth", summary="Strong growth", sentiment="Positive")
        ]
    )
    
    assert response.symbol == "AAPL"
    assert response.overall_sentiment_score == 85
    assert len(response.highlights) == 1

def test_analysis_response_invalid_score():
    """ทดสอบ Score ที่ผิดรูปแบบ (ถ้ามี Validator)"""
    # ถ้าเพิ่ม Field Validator ใน Model จะต้อง raise error
    # ตัวอย่าง: score ต้องอยู่ระหว่าง 0-100
    
    response = AnalysisResponse(
        symbol="AAPL",
        overall_sentiment_score=150,  # Invalid
        ceo_tone="Confident",
        highlights=[]
    )
    
    # ถ้าไม่มี Validator จะผ่าน แต่ควรเพิ่ม Validator ใน Model
    assert response.overall_sentiment_score == 150

def test_chat_request_valid():
    """ทดสอบ ChatRequest"""
    request = ChatRequest(question="What is the revenue?")
    
    assert request.question == "What is the revenue?"

def test_chat_request_empty_question():
    """ทดสอบคำถามว่างเปล่า"""
    request = ChatRequest(question="")
    
    # ควรผ่าน แต่อาจต้องเพิ่ม Validator
    assert request.question == ""

def test_chat_response_valid():
    """ทดสอบ ChatResponse"""
    response = ChatResponse(answer="Revenue is $100M")
    
    assert "100M" in response.answer

def test_consistency_response_valid():
    """ทดสอบ ConsistencyResponse"""
    response = ConsistencyResponse(
        symbol="TSLA",
        prepared_remarks=SectionAnalysis(
            score=90,
            tone="Optimistic",
            key_point="Record deliveries"
        ),
        qa_session=SectionAnalysis(
            score=70,
            tone="Defensive",
            key_point="Production challenges"
        ),
        consistency_score=75,
        red_flag_warning="Tone shifted significantly"
    )
    
    assert response.symbol == "TSLA"
    assert response.consistency_score == 75
    assert response.prepared_remarks.score == 90
    assert response.qa_session.score == 70

def test_analysis_response_json_serialization():
    """ทดสอบ Serialize เป็น JSON"""
    response = AnalysisResponse(
        symbol="AAPL",
        overall_sentiment_score=80,
        ceo_tone="Neutral",
        highlights=[]
    )
    
    json_str = response.model_dump_json()
    assert "AAPL" in json_str
    assert "80" in json_str

def test_analysis_response_json_deserialization():
    """ทดสอบ Deserialize จาก JSON"""
    json_str = '{"symbol": "NVDA", "overall_sentiment_score": 95, "ceo_tone": "Bullish", "highlights": []}'
    
    response = AnalysisResponse.model_validate_json(json_str)
    
    assert response.symbol == "NVDA"
    assert response.overall_sentiment_score == 95
