# app/repositories/cache/sql_cache.py
"""SQL implementation สำหรับ Cache (SQLite และ PostgreSQL)"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime, timedelta
from typing import Optional, List
import json

from app.repositories.base import ICacheRepository
from app.models.cache import EarningsCache
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class SQLCacheRepository(ICacheRepository):
    """
    SQL implementation สำหรับ Cache Repository
    ใช้ได้กับทั้ง SQLite และ PostgreSQL
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get(self, symbol: str, quarter_date: str) -> Optional[dict]:
        """ดึง cache ตาม symbol และ quarter_date"""
        statement = select(EarningsCache).where(
            EarningsCache.symbol == symbol,
            EarningsCache.quarter_date == quarter_date
        )
        result = await self.session.execute(statement)
        cache = result.scalar_one_or_none()
        
        if cache:
            return {
                "id": cache.id,
                "symbol": cache.symbol,
                "quarter_date": cache.quarter_date,
                "analysis_json": cache.analysis_json,
                "created_at": cache.created_at
            }
        return None
    
    async def save(self, symbol: str, quarter_date: str, data: dict) -> None:
        """บันทึก cache"""
        # เช็คว่ามีอยู่แล้วไหม
        statement = select(EarningsCache).where(
            EarningsCache.symbol == symbol,
            EarningsCache.quarter_date == quarter_date
        )
        result = await self.session.execute(statement)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update
            existing.analysis_json = json.dumps(data) if isinstance(data, dict) else data
            existing.created_at = datetime.utcnow()
            logger.info(f"Updated cache for {symbol} ({quarter_date})")
        else:
            # Insert
            new_cache = EarningsCache(
                symbol=symbol,
                quarter_date=quarter_date,
                analysis_json=json.dumps(data) if isinstance(data, dict) else data
            )
            self.session.add(new_cache)
            logger.info(f"Created new cache for {symbol} ({quarter_date})")
        
        await self.session.commit()
    
    async def delete(self, symbol: str, quarter_date: str) -> bool:
        """ลบ cache"""
        statement = select(EarningsCache).where(
            EarningsCache.symbol == symbol,
            EarningsCache.quarter_date == quarter_date
        )
        result = await self.session.execute(statement)
        cache = result.scalar_one_or_none()
        
        if cache:
            await self.session.delete(cache)
            await self.session.commit()
            logger.info(f"Deleted cache for {symbol} ({quarter_date})")
            return True
        return False
    
    async def list_by_symbol(self, symbol: str) -> List[dict]:
        """ดึงข้อมูลทั้งหมดของ symbol"""
        statement = select(EarningsCache).where(
            EarningsCache.symbol == symbol
        ).order_by(EarningsCache.quarter_date.desc())
        
        result = await self.session.execute(statement)
        caches = result.scalars().all()
        
        return [
            {
                "id": c.id,
                "symbol": c.symbol,
                "quarter_date": c.quarter_date,
                "analysis_json": c.analysis_json,
                "created_at": c.created_at
            }
            for c in caches
        ]
    
    async def cleanup_old(self, days: int = 30) -> int:
        """ลบข้อมูลเก่า"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        statement = select(EarningsCache).where(
            EarningsCache.created_at < cutoff_date
        )
        result = await self.session.execute(statement)
        old_caches = result.scalars().all()
        
        count = len(old_caches)
        for cache in old_caches:
            await self.session.delete(cache)
        
        await self.session.commit()
        logger.info(f"Cleaned up {count} old cache entries (older than {days} days)")
        
        return count
