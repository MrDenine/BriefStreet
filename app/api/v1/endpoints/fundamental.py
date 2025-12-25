"""
Fundamental Analysis Endpoints
- Earnings Analysis with AI
- Consistency Analysis
- Chat with Earnings Transcript
- Valuation Analysis (DCF & Relative)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.dependencies import get_cache_repository
from app.repositories.base import ICacheRepository
from app.core.exceptions import DatabaseException
from app.core.logging_config import get_logger
from app.models.sentiment import AnalysisResponse, ConsistencyResponse, ChatRequest, ChatResponse
from app.models.valuation import ValuationResponse
from app.services import llm_service, market_data, valuation_service

logger = get_logger(__name__)
router = APIRouter()


# ============================================================================
# EARNINGS ANALYSIS
# ============================================================================

@router.post("/analyze/{symbol}", response_model=AnalysisResponse)
async def analyze_earnings(
    symbol: str, 
    cache_repo: ICacheRepository = Depends(get_cache_repository)
):
    """
    วิเคราะห์ Earnings Call ด้วย AI
    
    ใช้ Repository Pattern - รองรับทั้ง SQLite (dev) และ PostgreSQL (uat/prod)
    """
    symbol = symbol.upper()
    logger.info(f"📊 Analyzing earnings for symbol: {symbol}")
    
    try:
        # ดึง transcript จาก data source
        raw_data = await market_data.get_earnings_transcript(symbol)
        
        transcript_text = raw_data.content  # Pydantic model attribute
        call_date = raw_data.date  # Pydantic model attribute
        
        # เช็ค cache ผ่าน repository
        cached_entry = await cache_repo.get(symbol, call_date)

        if cached_entry:
            logger.info(f"⚡ CACHE HIT: Using cached data for {symbol} ({call_date})")
            return AnalysisResponse.model_validate_json(cached_entry["analysis_json"])

        # CACHE MISS - วิเคราะห์ด้วย AI
        logger.info(f"🤖 CACHE MISS: Calling AI to analyze {symbol}")
        analysis_result = llm_service.analyze_transcript(symbol, transcript_text)

        # บันทึกลง cache ผ่าน repository
        await cache_repo.save(
            symbol=symbol,
            quarter_date=call_date,
            data=analysis_result.model_dump_json()
        )
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
    """
    วิเคราะห์ความสอดคล้องของข้อมูลใน Earnings Call
    """
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


# ============================================================================
# CHAT WITH EARNINGS
# ============================================================================

@router.post("/chat/{symbol}", response_model=ChatResponse)
async def chat_earnings(symbol: str, request: ChatRequest):
    """
    สนทนาเกี่ยวกับ Earnings Call Transcript ด้วย AI
    """
    symbol = symbol.upper()
    logger.info(f"💬 Chat request for {symbol}: {request.question[:50]}...")
    
    try:
        raw_data = await market_data.get_earnings_transcript(symbol)
        transcript_text = raw_data.content  # Pydantic model attribute
        
        answer_text = await llm_service.chat_with_transcript(symbol, transcript_text, request.question)
        logger.info(f"✅ Chat response generated for {symbol}")
        
        return ChatResponse(answer=answer_text)
    except ValueError as e:
        logger.warning(f"⚠️ Invalid input for chat {symbol}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error in chat for {symbol}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


# ============================================================================
# VALUATION ANALYSIS
# ============================================================================

@router.get("/valuation/{symbol}", response_model=ValuationResponse)
async def get_valuation(symbol: str):
    """
    วิเคราะห์มูลค่าหุ้นด้วย DCF และ Relative Valuation
    """
    symbol = symbol.upper()
    logger.info(f"💰 Analyzing valuation for {symbol}")
    
    try:
        result = await valuation_service.analyze_valuation(symbol)
        logger.info(f"✅ Valuation analysis completed for {symbol}")
        return result
    except ValueError as e:
        logger.warning(f"⚠️ Symbol not found or invalid: {symbol} - {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error analyzing valuation for {symbol}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Valuation analysis failed: {str(e)}")
