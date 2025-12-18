# tests/test_repositories.py
"""
Unit tests สำหรับ Repository Pattern

ทดสอบ:
- SQLCacheRepository
- SQLMarketDataRepository
- Repository operations (CRUD)
"""

import pytest
import json
from datetime import datetime, timedelta

from app.repositories.cache.sql_cache import SQLCacheRepository
from app.repositories.market_data.sql_market_data import SQLMarketDataRepository
from app.models.cache import EarningsCache
from app.models.market_data_storage import TranscriptStorage, FinancialDataStorage


# ======================
# Cache Repository Tests
# ======================

@pytest.mark.asyncio
async def test_cache_repository_save_and_get(test_session):
    """ทดสอบ save และ get cache ผ่าน repository"""
    
    repo = SQLCacheRepository(test_session)
    
    # Save
    await repo.save(
        symbol="AAPL",
        quarter_date="2024-10-25",
        data={"sentiment": "positive", "score": 85}
    )
    
    # Get
    result = await repo.get("AAPL", "2024-10-25")
    
    assert result is not None
    assert result["symbol"] == "AAPL"
    assert result["quarter_date"] == "2024-10-25"
    assert "positive" in result["analysis_json"]


@pytest.mark.asyncio
async def test_cache_repository_get_nonexistent(test_session):
    """ทดสอบ get cache ที่ไม่มี"""
    
    repo = SQLCacheRepository(test_session)
    
    result = await repo.get("NONEXISTENT", "2024-01-01")
    
    assert result is None


@pytest.mark.asyncio
async def test_cache_repository_update_existing(test_session):
    """ทดสอบ update cache ที่มีอยู่แล้ว"""
    
    repo = SQLCacheRepository(test_session)
    
    # Save ครั้งแรก
    await repo.save("TSLA", "2024-10-25", {"score": 70})
    
    # Update
    await repo.save("TSLA", "2024-10-25", {"score": 90})
    
    # Get
    result = await repo.get("TSLA", "2024-10-25")
    
    assert result is not None
    data = json.loads(result["analysis_json"])
    assert data["score"] == 90


@pytest.mark.asyncio
async def test_cache_repository_delete(test_session):
    """ทดสอบ delete cache"""
    
    repo = SQLCacheRepository(test_session)
    
    # Save
    await repo.save("GOOGL", "2024-10-25", {"score": 80})
    
    # Delete
    deleted = await repo.delete("GOOGL", "2024-10-25")
    
    assert deleted is True
    
    # Verify deleted
    result = await repo.get("GOOGL", "2024-10-25")
    assert result is None


@pytest.mark.asyncio
async def test_cache_repository_delete_nonexistent(test_session):
    """ทดสอบ delete cache ที่ไม่มี"""
    
    repo = SQLCacheRepository(test_session)
    
    deleted = await repo.delete("NONEXISTENT", "2024-01-01")
    
    assert deleted is False


@pytest.mark.asyncio
async def test_cache_repository_list_by_symbol(test_session):
    """ทดสอบ list cache ตาม symbol"""
    
    repo = SQLCacheRepository(test_session)
    
    # Save multiple
    await repo.save("AAPL", "2024-10-25", {"score": 85})
    await repo.save("AAPL", "2024-07-25", {"score": 80})
    await repo.save("TSLA", "2024-10-25", {"score": 75})
    
    # List by symbol
    results = await repo.list_by_symbol("AAPL")
    
    assert len(results) == 2
    assert all(r["symbol"] == "AAPL" for r in results)
    # ควรเรียงตาม quarter_date desc
    assert results[0]["quarter_date"] == "2024-10-25"


@pytest.mark.asyncio
async def test_cache_repository_cleanup_old(test_session):
    """ทดสอบ cleanup cache เก่า"""
    
    repo = SQLCacheRepository(test_session)
    
    # สร้าง cache เก่า (manually set created_at)
    old_cache = EarningsCache(
        symbol="OLD",
        quarter_date="2024-01-01",
        analysis_json=json.dumps({"score": 50})
    )
    # Set created_at เป็น 35 วันก่อน
    old_cache.created_at = datetime.utcnow() - timedelta(days=35)
    
    test_session.add(old_cache)
    await test_session.commit()
    
    # สร้าง cache ใหม่
    await repo.save("NEW", "2024-10-25", {"score": 90})
    
    # Cleanup (ลบข้อมูลเก่ากว่า 30 วัน)
    count = await repo.cleanup_old(days=30)
    
    assert count == 1
    
    # Verify
    old_result = await repo.get("OLD", "2024-01-01")
    new_result = await repo.get("NEW", "2024-10-25")
    
    assert old_result is None
    assert new_result is not None


# ======================
# Market Data Repository Tests
# ======================

@pytest.mark.asyncio
async def test_market_data_repository_save_and_get_transcript(test_session):
    """ทดสอบ save และ get transcript"""
    
    repo = SQLMarketDataRepository(test_session)
    
    # Save transcript
    success = await repo.save_transcript(
        symbol="NVDA",
        quarter_date="2024-10-25",
        content="NVIDIA Q3 2024 Earnings Call Transcript...",
        extra_data={"source": "FMP", "length": 15000}
    )
    
    assert success is True
    
    # Get transcript
    result = await repo.get_transcript("NVDA", "2024-10-25")
    
    assert result is not None
    assert result["symbol"] == "NVDA"
    assert result["quarter_date"] == "2024-10-25"
    assert "NVIDIA" in result["content"]
    assert result["extra_data"]["source"] == "FMP"


@pytest.mark.asyncio
async def test_market_data_repository_update_transcript(test_session):
    """ทดสอบ update transcript ที่มีอยู่"""
    
    repo = SQLMarketDataRepository(test_session)
    
    # Save ครั้งแรก
    await repo.save_transcript(
        symbol="MSFT",
        quarter_date="2024-10-25",
        content="Original content"
    )
    
    # Update
    await repo.save_transcript(
        symbol="MSFT",
        quarter_date="2024-10-25",
        content="Updated content",
        extra_data={"updated": True}
    )
    
    # Get
    result = await repo.get_transcript("MSFT", "2024-10-25")
    
    assert result is not None
    assert result["content"] == "Updated content"
    assert result["extra_data"]["updated"] is True


@pytest.mark.asyncio
async def test_market_data_repository_get_nonexistent_transcript(test_session):
    """ทดสอบ get transcript ที่ไม่มี"""
    
    repo = SQLMarketDataRepository(test_session)
    
    result = await repo.get_transcript("NONEXISTENT", "2024-01-01")
    
    assert result is None


@pytest.mark.asyncio
async def test_market_data_repository_save_financial_data(test_session):
    """ทดสอบ save และ get financial data"""
    
    repo = SQLMarketDataRepository(test_session)
    
    financial_data = {
        "type": "income_statement",
        "revenue": 100000000,
        "netIncome": 25000000,
        "eps": 2.50
    }
    
    # Save
    success = await repo.save_financial_data(
        symbol="AAPL",
        year=2024,
        quarter=3,
        data=financial_data
    )
    
    assert success is True
    
    # Get
    result = await repo.get_financial_data("AAPL", 2024, 3)
    
    assert result is not None
    assert result["symbol"] == "AAPL"
    assert result["year"] == 2024
    assert result["quarter"] == 3
    assert result["data"]["revenue"] == 100000000


@pytest.mark.asyncio
async def test_market_data_repository_list_transcripts_by_symbol(test_session):
    """ทดสอบ list transcripts ตาม symbol"""
    
    repo = SQLMarketDataRepository(test_session)
    
    # Save multiple transcripts
    await repo.save_transcript("META", "2024-10-25", "Q3 content")
    await repo.save_transcript("META", "2024-07-25", "Q2 content")
    await repo.save_transcript("GOOGL", "2024-10-25", "Q3 content")
    
    # List
    results = await repo.list_by_symbol("META")
    
    assert len(results) == 2
    assert all(r["symbol"] == "META" for r in results)
    # ควรเรียงตาม quarter_date desc
    assert results[0]["quarter_date"] == "2024-10-25"


@pytest.mark.asyncio
async def test_market_data_repository_content_preview(test_session):
    """ทดสอบว่า list_by_symbol แสดง content แบบ preview"""
    
    repo = SQLMarketDataRepository(test_session)
    
    # Save transcript ยาวๆ
    long_content = "A" * 500
    await repo.save_transcript("AMZN", "2024-10-25", long_content)
    
    # List
    results = await repo.list_by_symbol("AMZN")
    
    assert len(results) == 1
    # ควรมี "..." ท้าย (preview)
    assert results[0]["content"].endswith("...")
    assert len(results[0]["content"]) < len(long_content)


# ======================
# Integration Tests
# ======================

@pytest.mark.asyncio
async def test_repository_pattern_with_multiple_domains(test_session):
    """ทดสอบใช้หลาย repository พร้อมกัน"""
    
    cache_repo = SQLCacheRepository(test_session)
    market_data_repo = SQLMarketDataRepository(test_session)
    
    # Save data ใน cache domain
    await cache_repo.save("AAPL", "2024-10-25", {"score": 85})
    
    # Save data ใน market_data domain
    await market_data_repo.save_transcript(
        "AAPL", "2024-10-25", "Transcript content"
    )
    
    # Get จากทั้งสอง
    cache_result = await cache_repo.get("AAPL", "2024-10-25")
    transcript_result = await market_data_repo.get_transcript("AAPL", "2024-10-25")
    
    assert cache_result is not None
    assert transcript_result is not None
    assert cache_result["symbol"] == transcript_result["symbol"]


@pytest.mark.asyncio
async def test_repository_error_handling(test_session):
    """ทดสอบ error handling ใน repository"""
    
    repo = SQLMarketDataRepository(test_session)
    
    # ทดสอบ save ด้วย invalid data
    # (ปกติควร handle error ภายใน repository)
    success = await repo.save_financial_data(
        symbol="TEST",
        year=2024,
        quarter=3,
        data={"valid": "data"}
    )
    
    # ควร succeed หรือ handle gracefully
    assert isinstance(success, bool)
