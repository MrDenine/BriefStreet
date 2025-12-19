from fastapi import APIRouter
from app.services import valuation_service
from app.models.valuation import ValuationResponse
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/valuation/{symbol}", response_model=ValuationResponse)
async def get_valuation(symbol: str):
    """
    วิเคราะห์มูลค่าหุ้นด้วย DCF และ Relative Valuation
    """
    symbol = symbol.upper()
    logger.info(f"💰 Analyzing valuation for {symbol}")
    
    result = await valuation_service.analyze_valuation(symbol)
    
    logger.info(f"✅ Valuation analysis completed for {symbol}")
    return result