# app/main.py
import json
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import init_db, get_session, engine
from app.core.error_handlers import register_exception_handlers
from app.core.logging_config import setup_logging, get_logger
from app.models.sentiment import AnalysisResponse , ChatRequest, ChatResponse, ConsistencyResponse
from app.models.cache import EarningsCache
from app.services import llm_service, market_data

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging("INFO")
    logger.info("🚀 Starting BriefStreet API...")
    await init_db()
    logger.info("✅ Database connected successfully")
    
    yield
    
    logger.info("🛑 Shutting down BriefStreet API...")
    await engine.dispose()
    logger.info("✅ Database connection closed")

app = FastAPI(lifespan=lifespan)

register_exception_handlers(app)

@app.get("/")
def read_root():
    logger.info("Health check endpoint accessed")
    return {"message": "Welcome to BriefStreet API! 🚀"}

@app.post("/analyze/{symbol}", response_model=AnalysisResponse)
async def analyze_earnings(
    symbol: str, 
    session: AsyncSession = Depends(get_session)
):
    from app.core.exceptions import DatabaseException
    
    symbol = symbol.upper()
    logger.info(f"📊 Analyzing earnings for symbol: {symbol}")
    raw_data = await market_data.get_earnings_transcript(symbol)
    
    transcript_text = raw_data['content']
    call_date = raw_data['date'] 

    try:
        statement = select(EarningsCache).where(
            EarningsCache.symbol == symbol,
            EarningsCache.quarter_date == call_date
        )
        result = await session.execute(statement)
        cached_entry = result.scalar_one_or_none()

        if cached_entry:
            logger.info(f"⚡ CACHE HIT: Using cached data for {symbol} ({call_date})")
            return AnalysisResponse.model_validate_json(cached_entry.analysis_json)

        logger.info(f"🤖 CACHE MISS: Calling AI to analyze {symbol}")
        analysis_result = llm_service.analyze_transcript(symbol, transcript_text)

        new_cache = EarningsCache(
            symbol=symbol,
            quarter_date=call_date,
            analysis_json=analysis_result.model_dump_json() 
        )
        session.add(new_cache)
        await session.commit()
        logger.info(f"💾 Cached analysis result for {symbol}")
        
        return analysis_result
    except Exception as e:
        if not isinstance(e, (DatabaseException,)):
            logger.error(f"❌ Database error for {symbol}: {str(e)}")
            raise DatabaseException(
                message="Failed to process cache operation",
                details={"symbol": symbol, "error": str(e)}
            )
        raise

@app.post("/chat/{symbol}", response_model=ChatResponse)
async def chat_earnings(symbol: str, request: ChatRequest):
    symbol = symbol.upper()
    logger.info(f"💬 Chat request for {symbol}: {request.question[:50]}...")
    
    raw_data = await market_data.get_earnings_transcript(symbol)
    transcript_text = raw_data['content']
    
    answer_text = await llm_service.chat_with_transcript(symbol, transcript_text, request.question)
    logger.info(f"✅ Chat response generated for {symbol}")
    
    return ChatResponse(answer=answer_text)

@app.post("/analyze/consistency/{symbol}", response_model=ConsistencyResponse)
async def analyze_consistency_route(symbol: str):
    symbol = symbol.upper()
    logger.info(f"🕵️ Analyzing consistency for {symbol}")
    
    raw_data = await market_data.get_earnings_transcript(symbol)
    transcript_text = raw_data['content']
    
    result = await llm_service.analyze_consistency(symbol, transcript_text)
    logger.info(f"✅ Consistency analysis completed for {symbol}")
    
    return result

