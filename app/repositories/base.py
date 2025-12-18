# app/repositories/base.py
from abc import ABC, abstractmethod
from typing import Optional, List, Generic, TypeVar

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Base repository สำหรับทุก domain"""
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """ดึงข้อมูลตาม ID"""
        pass
    
    @abstractmethod
    async def save(self, entity: T) -> T:
        """บันทึกข้อมูล"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """ลบข้อมูล"""
        pass
    
    @abstractmethod
    async def list_all(self, limit: int = 100) -> List[T]:
        """ดึงข้อมูลทั้งหมด"""
        pass


class ICacheRepository(ABC):
    """Interface เฉพาะสำหรับ Cache operations"""
    
    @abstractmethod
    async def get(self, symbol: str, quarter_date: str) -> Optional[dict]:
        """ดึง cache ตาม symbol และ date"""
        pass
    
    @abstractmethod
    async def save(self, symbol: str, quarter_date: str, data: dict) -> None:
        """บันทึก cache"""
        pass
    
    @abstractmethod
    async def delete(self, symbol: str, quarter_date: str) -> bool:
        """ลบ cache"""
        pass
    
    @abstractmethod
    async def list_by_symbol(self, symbol: str) -> List[dict]:
        """ดึงข้อมูลทั้งหมดของ symbol"""
        pass
    
    @abstractmethod
    async def cleanup_old(self, days: int = 30) -> int:
        """ลบข้อมูลเก่า"""
        pass


class IMarketDataRepository(ABC):
    """Interface สำหรับ Market Data storage"""
    
    @abstractmethod
    async def save_transcript(
        self, 
        symbol: str, 
        quarter_date: str, 
        content: str,
        extra_data: Optional[dict] = None
    ) -> bool:
        """บันทึก earnings transcript"""
        pass
    
    @abstractmethod
    async def get_transcript(
        self, 
        symbol: str, 
        quarter_date: str
    ) -> Optional[dict]:
        """ดึง transcript"""
        pass
    
    @abstractmethod
    async def save_financial_data(
        self,
        symbol: str,
        year: int,
        quarter: int,
        data: dict
    ) -> bool:
        """บันทึกข้อมูลทางการเงิน"""
        pass
    
    @abstractmethod
    async def get_financial_data(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[dict]:
        """ดึงข้อมูลทางการเงิน"""
        pass
    
    @abstractmethod
    async def list_by_symbol(self, symbol: str) -> List[dict]:
        """ดึงข้อมูลทั้งหมดของ symbol"""
        pass
