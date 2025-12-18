# app/services/market_data_storage.py
"""
Service สำหรับจัดการ Market Data Storage

เป็นตัวกลางระหว่าง data sources (FMP, YFinance) กับ repository
"""

from typing import Optional
from app.repositories.base import IMarketDataRepository
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class MarketDataStorageService:
    """
    Service สำหรับบันทึกและดึง market data จาก repository
    
    หน้าที่:
    - รับข้อมูลจาก data provider (FMP, YFinance)
    - บันทึกลง repository
    - ดึงข้อมูลจาก repository
    """
    
    def __init__(self, repository: IMarketDataRepository):
        self.repository = repository
    
    async def store_transcript(
        self,
        symbol: str,
        quarter_date: str,
        content: str,
        extra_data: Optional[dict] = None
    ) -> bool:
        """
        บันทึก earnings transcript
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            quarter_date: วันที่ earnings call (e.g., '2024-10-25')
            content: เนื้อหา transcript
            extra_data: ข้อมูลเพิ่มเติม (optional)
        
        Returns:
            True ถ้าบันทึกสำเร็จ
        """
        logger.info(f"Storing transcript for {symbol} ({quarter_date})")
        
        success = await self.repository.save_transcript(
            symbol=symbol,
            quarter_date=quarter_date,
            content=content,
            extra_data=extra_data
        )
        
        if success:
            logger.info(f"✅ Successfully stored transcript for {symbol}")
        else:
            logger.error(f"❌ Failed to store transcript for {symbol}")
        
        return success
    
    async def get_transcript(
        self,
        symbol: str,
        quarter_date: str
    ) -> Optional[dict]:
        """
        ดึง earnings transcript จาก storage
        
        Args:
            symbol: Stock symbol
            quarter_date: วันที่ earnings call
        
        Returns:
            dict ของ transcript หรือ None ถ้าไม่มี
        """
        logger.info(f"Retrieving transcript for {symbol} ({quarter_date})")
        
        transcript = await self.repository.get_transcript(symbol, quarter_date)
        
        if transcript:
            logger.info(f"✅ Found transcript for {symbol}")
        else:
            logger.info(f"ℹ️ No transcript found for {symbol} ({quarter_date})")
        
        return transcript
    
    async def store_financial_data(
        self,
        symbol: str,
        year: int,
        quarter: int,
        data: dict
    ) -> bool:
        """
        บันทึกข้อมูลทางการเงิน
        
        Args:
            symbol: Stock symbol
            year: ปี (e.g., 2024)
            quarter: ไตรมาส (1-4)
            data: ข้อมูลทางการเงิน
        
        Returns:
            True ถ้าบันทึกสำเร็จ
        """
        logger.info(f"Storing financial data for {symbol} ({year} Q{quarter})")
        
        success = await self.repository.save_financial_data(
            symbol=symbol,
            year=year,
            quarter=quarter,
            data=data
        )
        
        if success:
            logger.info(f"✅ Successfully stored financial data for {symbol}")
        else:
            logger.error(f"❌ Failed to store financial data for {symbol}")
        
        return success
    
    async def get_financial_data(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[dict]:
        """
        ดึงข้อมูลทางการเงิน
        
        Args:
            symbol: Stock symbol
            year: ปี
            quarter: ไตรมาส
        
        Returns:
            dict ของข้อมูลทางการเงิน หรือ None
        """
        logger.info(f"Retrieving financial data for {symbol} ({year} Q{quarter})")
        
        financial_data = await self.repository.get_financial_data(symbol, year, quarter)
        
        if financial_data:
            logger.info(f"✅ Found financial data for {symbol}")
        else:
            logger.info(f"ℹ️ No financial data found for {symbol} ({year} Q{quarter})")
        
        return financial_data
    
    async def get_all_transcripts(self, symbol: str) -> list:
        """ดึง transcript ทั้งหมดของ symbol"""
        logger.info(f"Retrieving all transcripts for {symbol}")
        
        transcripts = await self.repository.list_by_symbol(symbol)
        
        logger.info(f"Found {len(transcripts)} transcripts for {symbol}")
        
        return transcripts
