from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.exceptions import DatabaseException
from app.core.logging_config import get_logger
from app.models.sentiment import AnalysisResponse, ConsistencyResponse
from app.models.cache import EarningsCache
from app.services import llm_service, market_data

logger = get_logger(__name__)
router = APIRouter()


@router.post("/analyze/{symbol}", response_model=AnalysisResponse)
async def analyze_earnings(
    symbol: str, 
    session: AsyncSession = Depends(get_session)
):
    symbol = symbol.upper()
    logger.info(f"📊 Analyzing earnings for symbol: {symbol}")
    
    try:
        raw_data = await market_data.get_earnings_transcript(symbol)
        
        transcript_text = raw_data.content  # Pydantic model attribute
        call_date = raw_data.date  # Pydantic model attribute
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


@router.post("/analyze/consistency/{symbol}", response_model=ConsistencyResponse)
async def analyze_consistency(symbol: str):
    symbol = symbol.upper()
    logger.info(f"🕵️ Analyzing consistency for {symbol}")
    
    try:
        raw_data = await market_data.get_earnings_transcript(symbol)
        transcript_text = raw_data.content  # Pydantic model attribute
        
        result = await llm_service.analyze_consistency(symbol, transcript_text)
        logger.info(f"✅ Consistency analysis completed for {symbol}")
        
        return result
    except Exception as e:
        logger.error(f"❌ Error analyzing consistency for {symbol}: {str(e)}")
        raise
