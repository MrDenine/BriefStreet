# app/models/market_data_storage.py
"""Models สำหรับเก็บ market data ใน database"""

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, Text
from typing import Optional
from datetime import datetime


class TranscriptStorage(SQLModel, table=True):
    """เก็บ Earnings Call Transcript"""
    __tablename__ = "transcripts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True, max_length=10)
    quarter_date: str = Field(index=True, max_length=20)
    content: str = Field(sa_column=Column(Text))  # ใช้ Text สำหรับข้อความยาว
    extra_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))  # เปลี่ยนจาก metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True


class FinancialDataStorage(SQLModel, table=True):
    """เก็บข้อมูลทางการเงิน (Income Statement, Balance Sheet, etc.)"""
    __tablename__ = "financial_data"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True, max_length=10)
    year: int = Field(index=True)
    quarter: int = Field(index=True)  # 1-4
    data_type: str = Field(max_length=50)  # 'income_statement', 'balance_sheet', 'cash_flow'
    data: dict = Field(sa_column=Column(JSON))  # ข้อมูลจริง
    source: str = Field(default="fmp", max_length=20)  # แหล่งข้อมูล
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
