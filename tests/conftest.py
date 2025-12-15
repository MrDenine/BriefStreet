# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_session

# ใช้ In-Memory Database สำหรับ Testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def test_engine():
    """สร้าง Test Database Engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    
    # สร้างตาราง
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    # ลบตารางหลังเทสเสร็จ
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    
    await engine.dispose()

@pytest_asyncio.fixture
async def test_session(test_engine):
    """สร้าง Test Database Session"""
    async_session = sessionmaker(
        test_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture
async def client(test_session):
    """สร้าง Test Client พร้อม Override Database"""
    
    async def override_get_session():
        yield test_session
    
    app.dependency_overrides[get_session] = override_get_session
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
def mock_transcript():
    """Mock Earnings Transcript Data"""
    return [
        {
            "date": "2024-10-25",
            "content": """
            Operator: Good afternoon. Welcome to AAPL Q4 Earnings Call.
            CEO: Thank you. We are happy to report a record-breaking quarter. 
            Revenue is up 25% year-over-year due to strong demand in our AI sector.
            However, we are seeing some supply chain headwinds in Asia.
            Overall, we are very confident in our long-term strategy.
            
            Question-and-Answer Session
            
            Analyst: What about the supply chain issues?
            CEO: We are actively working on diversifying our suppliers.
            """
        }
    ]

@pytest.fixture
def mock_analysis_response():
    """Mock AI Analysis Response"""
    return {
        "symbol": "AAPL",
        "overall_sentiment_score": 75,
        "ceo_tone": "Confident",
        "highlights": [
            {
                "topic": "Revenue Growth",
                "summary": "Revenue up 25% YoY",
                "sentiment": "Positive"
            },
            {
                "topic": "Supply Chain",
                "summary": "Some headwinds in Asia",
                "sentiment": "Negative"
            }
        ]
    }
