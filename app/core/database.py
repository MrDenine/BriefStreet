import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# สร้าง engine ตาม environment
if settings.ENVIRONMENT == "development":
    # SQLite สำหรับ development
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
else:
    # PostgreSQL สำหรับ UAT/Production
    engine = create_async_engine(
        settings.DATABASE_URL, 
        echo=False,
        pool_pre_ping=True,      # ตรวจสอบ connection ก่อนใช้
        pool_size=5,             # connection pool
        max_overflow=10          # max connections ที่เกินจาก pool
    )

async def init_db():
    """สร้างตารางทั้งหมด"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session():
    """Dependency สำหรับ database session"""
    async_session = sessionmaker(
        engine, class_ = AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

    
