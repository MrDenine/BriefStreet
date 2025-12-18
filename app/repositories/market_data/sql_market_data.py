# app/repositories/market_data/sql_market_data.py
"""SQL implementation สำหรับ Market Data Repository"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Optional, List
from datetime import datetime
import json

from app.repositories.base import IMarketDataRepository
from app.models.market_data_storage import TranscriptStorage, FinancialDataStorage
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class SQLMarketDataRepository(IMarketDataRepository):
    """
    SQL implementation สำหรับ Market Data Repository
    ใช้ได้กับทั้ง SQLite และ PostgreSQL
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save_transcript(
        self, 
        symbol: str, 
        quarter_date: str, 
        content: str,
        extra_data: Optional[dict] = None
    ) -> bool:
        """บันทึก earnings transcript"""
        try:
            # เช็คว่ามีอยู่แล้วไหม
            statement = select(TranscriptStorage).where(
                TranscriptStorage.symbol == symbol,
                TranscriptStorage.quarter_date == quarter_date
            )
            result = await self.session.execute(statement)
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update
                existing.content = content
                existing.extra_data = extra_data
                existing.updated_at = datetime.utcnow()
                logger.info(f"Updated transcript for {symbol} ({quarter_date})")
            else:
                # Insert
                new_transcript = TranscriptStorage(
                    symbol=symbol,
                    quarter_date=quarter_date,
                    content=content,
                    extra_data=extra_data
                )
                self.session.add(new_transcript)
                logger.info(f"Saved new transcript for {symbol} ({quarter_date})")
            
            await self.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving transcript for {symbol}: {str(e)}")
            await self.session.rollback()
            return False
    
    async def get_transcript(
        self, 
        symbol: str, 
        quarter_date: str
    ) -> Optional[dict]:
        """ดึง transcript"""
        statement = select(TranscriptStorage).where(
            TranscriptStorage.symbol == symbol,
            TranscriptStorage.quarter_date == quarter_date
        )
        result = await self.session.execute(statement)
        transcript = result.scalar_one_or_none()
        
        if transcript:
            return {
                "id": transcript.id,
                "symbol": transcript.symbol,
                "quarter_date": transcript.quarter_date,
                "content": transcript.content,
                "extra_data": transcript.extra_data,
                "created_at": transcript.created_at,
                "updated_at": transcript.updated_at
            }
        return None
    
    async def save_financial_data(
        self,
        symbol: str,
        year: int,
        quarter: int,
        data: dict
    ) -> bool:
        """บันทึกข้อมูลทางการเงิน"""
        try:
            # ดึง data_type จาก data หรือใช้ default
            data_type = data.get("type", "financial_data")
            
            # เช็คว่ามีอยู่แล้วไหม
            statement = select(FinancialDataStorage).where(
                FinancialDataStorage.symbol == symbol,
                FinancialDataStorage.year == year,
                FinancialDataStorage.quarter == quarter,
                FinancialDataStorage.data_type == data_type
            )
            result = await self.session.execute(statement)
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update
                existing.data = data
                existing.updated_at = datetime.utcnow()
                logger.info(f"Updated financial data for {symbol} ({year} Q{quarter})")
            else:
                # Insert
                new_data = FinancialDataStorage(
                    symbol=symbol,
                    year=year,
                    quarter=quarter,
                    data_type=data_type,
                    data=data
                )
                self.session.add(new_data)
                logger.info(f"Saved new financial data for {symbol} ({year} Q{quarter})")
            
            await self.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving financial data for {symbol}: {str(e)}")
            await self.session.rollback()
            return False
    
    async def get_financial_data(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[dict]:
        """ดึงข้อมูลทางการเงิน"""
        statement = select(FinancialDataStorage).where(
            FinancialDataStorage.symbol == symbol,
            FinancialDataStorage.year == year,
            FinancialDataStorage.quarter == quarter
        )
        result = await self.session.execute(statement)
        financial_data = result.scalar_one_or_none()
        
        if financial_data:
            return {
                "id": financial_data.id,
                "symbol": financial_data.symbol,
                "year": financial_data.year,
                "quarter": financial_data.quarter,
                "data_type": financial_data.data_type,
                "data": financial_data.data,
                "source": financial_data.source,
                "created_at": financial_data.created_at,
                "updated_at": financial_data.updated_at
            }
        return None
    
    async def list_by_symbol(self, symbol: str) -> List[dict]:
        """ดึงข้อมูลทั้งหมดของ symbol"""
        statement = select(TranscriptStorage).where(
            TranscriptStorage.symbol == symbol
        ).order_by(TranscriptStorage.quarter_date.desc())
        
        result = await self.session.execute(statement)
        transcripts = result.scalars().all()
        
        return [
            {
                "id": t.id,
                "symbol": t.symbol,
                "quarter_date": t.quarter_date,
                "content": t.content[:200] + "..." if len(t.content) > 200 else t.content,  # Preview
                "extra_data": t.extra_data,
                "created_at": t.created_at
            }
            for t in transcripts
        ]
