# app/models/cache.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class EarningsCache(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)           # ดัชนีช่วยให้ค้นหาเร็ว
    quarter_date: str                         # วันที่ของ Earnings Call (ใช้เช็คว่าเป็นอันใหม่หรือเก่า)
    analysis_json: str                        # เก็บผลลัพธ์จาก AI เป็นก้อน Text (JSON String)
    created_at: datetime = Field(default_factory=datetime.utcnow)