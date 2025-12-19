# app/api/v1/endpoints/market_data.py
"""
Market Data API Endpoints - Direct access to FMP provider data
"""
from fastapi import APIRouter, Query
from app.core.logging_config import get_logger
from app.services import market_data
from app.models.market_data import (
    TranscriptResponse,
    FinancialMetricsResponse,
    PeerListResponse
)

logger = get_logger(__name__)
router = APIRouter()

@router.get("/transcript/{symbol}", response_model=TranscriptResponse)
async def get_transcript(
    symbol: str,
    quarter: int = Query(..., ge=1, le=4, description="Quarter number (1-4)"),
    year: int = Query(..., ge=2000, le=2030, description="Year")
):
    """
    ดึง Earnings Call Transcript จาก FMP
    
    - **symbol**: Stock ticker symbol (e.g., AAPL, MSFT)
    - **quarter**: Quarter number (1-4)
    - **year**: Year (e.g., 2024)
    """
    symbol = symbol.upper()
    logger.info(f"📄 Fetching transcript for {symbol} Q{quarter} {year}")
    
    try:
        result = await market_data.get_earnings_transcript(
            symbol=symbol,
            quarter=quarter,
            year=year
        )
        
        logger.info(f"✅ Successfully fetched transcript for {symbol} (Date: {result.date}, Length: {len(result.content)} chars)")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch transcript for {symbol} Q{quarter} {year}: {str(e)}")
        raise


@router.get("/metrics/{symbol}", response_model=FinancialMetricsResponse)
async def get_financial_metrics(
    symbol: str,
    limit: int = Query(5, ge=1, le=10, description="Number of historical periods")
):
    """
    ดึงข้อมูลทางการเงินสำหรับการวิเคราะห์
    
    - **symbol**: Stock ticker symbol
    - **limit**: จำนวนงวดย้อนหลังที่ต้องการ (default: 5)
    
    Returns:
    - Key financial metrics (P/E, P/B, EPS, etc.)
    - Current stock price
    - Historical cash flow statements
    """
    symbol = symbol.upper()
    logger.info(f"📊 Fetching financial metrics for {symbol} (limit: {limit})")
    
    try:
        result = await market_data.get_financial_metrics(
            symbol=symbol,
            limit=limit
        )
        
        logger.info(
            f"✅ Successfully fetched metrics for {symbol} | "
            f"Price: ${result.price:.2f} | "
            f"P/E: {result.metrics.peRatioTTM or 'N/A'} | "
            f"Cash Flows: {len(result.cash_flows)} periods"
        )
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch metrics for {symbol}: {str(e)}")
        raise


@router.get("/peers/{symbol}", response_model=PeerListResponse)
async def get_peers(symbol: str):
    """
    ดึงรายชื่อบริษัทคู่แข่งเพื่อใช้ในการเปรียบเทียบ
    
    - **symbol**: Stock ticker symbol
    
    Returns:
    - List of peer company ticker symbols
    """
    symbol = symbol.upper()
    logger.info(f"🏢 Fetching peers for {symbol}")
    
    try:
        result = await market_data.get_peers(symbol=symbol)
        
        if result.peers:
            logger.info(f"✅ Found {len(result.peers)} peers for {symbol}: {', '.join(result.peers[:5])}{'...' if len(result.peers) > 5 else ''}")
        else:
            logger.warning(f"⚠️  No peers found for {symbol}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch peers for {symbol}: {str(e)}")
        raise
