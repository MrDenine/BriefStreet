from fastapi import APIRouter, HTTPException, Depends, Body
from app.core.logging_config import get_logger
from app.models.sentiment import ChatResponse, ChatRequest
from app.services import llm_service, market_data
from app.services.technical_analysis_service import TechnicalAnalysisService
from app.core.dependencies import get_technical_analysis_service

logger = get_logger(__name__)
router = APIRouter()


# ============================================================================
# CHAT WITH EARNINGS
# ============================================================================

@router.post("/earnings/{symbol}", response_model=ChatResponse)
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
# TECHNICAL MENTOR CHAT (NEW)
# ============================================================================

@router.post("/technical/{symbol}", response_model=ChatResponse)
async def chat_technical_mentor(
    symbol: str, 
    request: ChatRequest,
    tech_service: TechnicalAnalysisService = Depends(get_technical_analysis_service)
):
    """
    คุยกับ AI Mentor โดยอ้างอิงข้อมูล Technical Analysis ปัจจุบัน
    เช่น "BTC ตอนนี้น่าซื้อไหม?", "แนวรับแนวต้าน AAPL อยู่ตรงไหน?"
    """
    symbol = symbol.upper()
    logger.info(f"📉 Technical chat request for {symbol}: {request.question}")
    
    try:
        # 1. ดึงข้อมูล Technical สดๆ จาก Service ของเรา
        # (AI จะได้ไม่มั่ว เพราะเราป้อน Data จริงให้)
        tech_data = await tech_service.analyze(symbol)
        
        # 2. ส่งข้อมูล + คำถาม ไปให้ AI Mentor ประมวลผล
        answer = llm_service.analyze_technical_outlook(
            symbol=symbol,
            tech_data=tech_data,
            question=request.question
        )
        
        return ChatResponse(answer=answer)

    except ValueError as e:
        # กรณีไม่เจอข้อมูลหุ้น/เหรียญ
        logger.warning(f"Symbol data not found: {symbol}")
        raise HTTPException(status_code=404, detail=f"ไม่พบข้อมูลกราฟของ {symbol}")
    except Exception as e:
        logger.error(f"Error in technical chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการวิเคราะห์")