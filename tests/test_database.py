# tests/test_database.py
import pytest
from datetime import datetime
from sqlmodel import select
from app.models.cache import EarningsCache
import json

@pytest.mark.asyncio
async def test_create_cache_entry(test_session):
    """ทดสอบสร้าง Cache Entry"""
    
    cache_entry = EarningsCache(
        symbol="AAPL",
        quarter_date="2024-10-25",
        analysis_json=json.dumps({"sentiment": "positive"})
    )
    
    test_session.add(cache_entry)
    await test_session.commit()
    await test_session.refresh(cache_entry)
    
    assert cache_entry.id is not None
    assert cache_entry.symbol == "AAPL"
    assert cache_entry.quarter_date == "2024-10-25"

@pytest.mark.asyncio
async def test_query_cache_by_symbol(test_session):
    """ทดสอบค้นหา Cache ตาม Symbol"""
    
    # สร้างข้อมูล
    cache1 = EarningsCache(symbol="AAPL", quarter_date="2024-Q3", analysis_json="{}")
    cache2 = EarningsCache(symbol="TSLA", quarter_date="2024-Q3", analysis_json="{}")
    
    test_session.add(cache1)
    test_session.add(cache2)
    await test_session.commit()
    
    # ค้นหา
    statement = select(EarningsCache).where(EarningsCache.symbol == "AAPL")
    result = await test_session.execute(statement)
    found = result.scalar_one_or_none()
    
    assert found is not None
    assert found.symbol == "AAPL"

@pytest.mark.asyncio
async def test_query_cache_by_symbol_and_date(test_session):
    """ทดสอบค้นหา Cache ตาม Symbol และ Date"""
    
    cache1 = EarningsCache(symbol="AAPL", quarter_date="2024-10-25", analysis_json="{}")
    cache2 = EarningsCache(symbol="AAPL", quarter_date="2024-07-25", analysis_json="{}")
    
    test_session.add_all([cache1, cache2])
    await test_session.commit()
    
    # ค้นหาแบบเฉพาะเจาะจง
    statement = select(EarningsCache).where(
        EarningsCache.symbol == "AAPL",
        EarningsCache.quarter_date == "2024-10-25"
    )
    result = await test_session.execute(statement)
    found = result.scalar_one_or_none()
    
    assert found is not None
    assert found.quarter_date == "2024-10-25"

@pytest.mark.asyncio
async def test_cache_json_parsing(test_session):
    """ทดสอบ Parse JSON จาก Cache"""
    
    analysis_data = {
        "symbol": "NVDA",
        "overall_sentiment_score": 95,
        "ceo_tone": "Bullish"
    }
    
    cache = EarningsCache(
        symbol="NVDA",
        quarter_date="2024-10-25",
        analysis_json=json.dumps(analysis_data)
    )
    
    test_session.add(cache)
    await test_session.commit()
    await test_session.refresh(cache)
    
    # Parse กลับมา
    parsed = json.loads(cache.analysis_json)
    assert parsed["symbol"] == "NVDA"
    assert parsed["overall_sentiment_score"] == 95

@pytest.mark.asyncio
async def test_cache_timestamp(test_session):
    """ทดสอบว่า created_at ถูกสร้างอัตโนมัติ"""
    
    cache = EarningsCache(
        symbol="GOOGL",
        quarter_date="2024-10-25",
        analysis_json="{}"
    )
    
    test_session.add(cache)
    await test_session.commit()
    await test_session.refresh(cache)
    
    assert cache.created_at is not None
    assert isinstance(cache.created_at, datetime)
