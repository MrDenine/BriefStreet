# app/main.py
import json
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import init_db, get_session, engine
from app.models.sentiment import AnalysisResponse
from app.models.cache import EarningsCache
from app.services import llm_service, market_data

# 1. ทำงานตอนเริ่ม Server: สร้างไฟล์ DB อัตโนมัติ
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("🚀 Database connected!")
    
    yield
    
    print("🛑 Closing database connection...")
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"message": "Welcome to BriefStreet API! 🚀"}

@app.post("/analyze/{symbol}", response_model=AnalysisResponse)
async def analyze_earnings(
    symbol: str, 
    session: AsyncSession = Depends(get_session) # 2. Inject Database Session
):
    symbol = symbol.upper()
    
    # --- PHASE 1: ดึงข้อมูลดิบ (เสียเงิน FMP น้อยมาก หรือฟรีถ้ามี cache FMP) ---
    # เราต้องแก้ market_data ให้ return ทั้ง text และ date กลับมา
    # สมมติว่าฟังก์ชัน get_earnings_transcript return dict: {"date": "2024-10-25", "content": "..."}
    # (คุณต้องไปแก้ market_data.py นิดหน่อยให้ return แบบนี้นะครับ)
    raw_data = await market_data.get_earnings_transcript(symbol)
    transcript_text = raw_data[0]['content']
    call_date = raw_data[0]['date'] # วันที่ประชุมจริง

    # --- PHASE 2: เช็ค CACHE (ประหยัดเงิน AI) ---
    statement = select(EarningsCache).where(
        EarningsCache.symbol == symbol,
        EarningsCache.quarter_date == call_date
    )
    result = await session.execute(statement)
    cached_entry = result.scalar_one_or_none()

    if cached_entry:
        print(f"⚡ CACHE HIT: ใช้ข้อมูลเก่าของ {symbol} ({call_date})")
        # แปลง JSON String ใน DB กลับเป็น Pydantic Object
        return AnalysisResponse.model_validate_json(cached_entry.analysis_json)

    # --- PHASE 3: ถ้าไม่มีของ ให้เรียก AI (เสียเงิน) ---
    print(f"🤖 CACHE MISS: เรียก AI วิเคราะห์ {symbol}...")
    analysis_result = llm_service.analyze_transcript(symbol, transcript_text)

    # --- PHASE 4: บันทึกของใหม่ลง DB ---
    new_cache = EarningsCache(
        symbol=symbol,
        quarter_date=call_date,
        analysis_json=analysis_result.model_dump_json() # แปลง Object เป็น String เพื่อยัดลง DB
    )
    session.add(new_cache)
    await session.commit()
    
    return analysis_result