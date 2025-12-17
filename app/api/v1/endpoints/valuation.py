from fastapi import APIRouter
from app.services import valuation_service
from app.models.valuation import ValuationResponse

router = APIRouter()

@router.get("/valuation/{symbol}", response_model=ValuationResponse)
async def get_valuation(symbol: str):
    symbol = symbol.upper()
    result = await valuation_service.analyze_valuation(symbol)
    return result