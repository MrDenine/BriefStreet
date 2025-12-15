# app/main.py
import json
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import init_db, get_session, engine
from app.models.sentiment import AnalysisResponse , ChatRequest, ChatResponse, ConsistencyResponse
from app.models.cache import EarningsCache
from app.services import llm_service, market_data

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
    session: AsyncSession = Depends(get_session)
):
    symbol = symbol.upper()
    

    raw_data = await market_data.get_earnings_transcript(symbol)
    
    if not raw_data or len(raw_data) == 0:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"No earnings data found for {symbol}")
    
    transcript_text = raw_data[0]['content']
    call_date = raw_data[0]['date'] 

    statement = select(EarningsCache).where(
        EarningsCache.symbol == symbol,
        EarningsCache.quarter_date == call_date
    )
    result = await session.execute(statement)
    cached_entry = result.scalar_one_or_none()

    if cached_entry:
        print(f"⚡ CACHE HIT: ใช้ข้อมูลเก่าของ {symbol} ({call_date})")
        return AnalysisResponse.model_validate_json(cached_entry.analysis_json)

    print(f"🤖 CACHE MISS: เรียก AI วิเคราะห์ {symbol}...")
    analysis_result = llm_service.analyze_transcript(symbol, transcript_text)

    new_cache = EarningsCache(
        symbol=symbol,
        quarter_date=call_date,
        analysis_json=analysis_result.model_dump_json() 
    )
    session.add(new_cache)
    await session.commit()
    
    return analysis_result

@app.post("/chat/{symbol}", response_model=ChatResponse)
async def chat_earnings(symbol: str, request: ChatRequest):
    symbol = symbol.upper()
    
    raw_data = await market_data.get_earnings_transcript(symbol)
    transcript_text = raw_data['content']
    
    answer_text = await llm_service.chat_with_transcript(symbol, transcript_text, request.question)
    
    return ChatResponse(answer=answer_text)

@app.post("/analyze/consistency/{symbol}", response_model=ConsistencyResponse)
async def analyze_consistency_route(symbol: str):
    symbol = symbol.upper()
    
    raw_data = await market_data.get_earnings_transcript(symbol)
    transcript_text = raw_data['content']
    
    result = await llm_service.analyze_consistency(symbol, transcript_text)
    
    return result

