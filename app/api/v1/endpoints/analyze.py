from fastapi import APIRouter
from app.services import market_data, llm_service
from app.models.sentiment import AnalysisResponse

router = APIRouter()

@router.post("/analyze/{symbol}", response_model=AnalysisResponse)
async def analyze_stock(symbol: str):
    transcript = await market_data.get_earnings_transcript(symbol)
    
    result = llm_service.analyze_transcript(symbol, transcript['content'])
    
    return result