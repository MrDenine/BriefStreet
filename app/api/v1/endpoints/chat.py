from fastapi import APIRouter

from app.core.logging_config import get_logger
from app.models.sentiment import ChatRequest, ChatResponse
from app.services import llm_service, market_data

logger = get_logger(__name__)
router = APIRouter()


@router.post("/chat/{symbol}", response_model=ChatResponse)
async def chat_earnings(symbol: str, request: ChatRequest):
    symbol = symbol.upper()
    logger.info(f"💬 Chat request for {symbol}: {request.question[:50]}...")
    
    try:
        raw_data = await market_data.get_earnings_transcript(symbol)
        transcript_text = raw_data.content  # Pydantic model attribute
        
        answer_text = await llm_service.chat_with_transcript(symbol, transcript_text, request.question)
        logger.info(f"✅ Chat response generated for {symbol}")
        
        return ChatResponse(answer=answer_text)
    except Exception as e:
        logger.error(f"❌ Error in chat for {symbol}: {str(e)}")
        raise
