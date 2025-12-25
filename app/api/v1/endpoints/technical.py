"""
Technical Analysis Endpoints
- Single Symbol Technical Analysis (Trend, RSI, Signals)
- Market Scanner (Multiple symbols with filters)
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Body, Query, HTTPException
from app.core.dependencies import get_technical_analysis_service, get_market_scanner_service
from app.services.technical_analysis_service import TechnicalAnalysisService
from app.services.market_scanner_service import MarketScannerService
from app.models.market_data import TechnicalAnalysisResult
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Preset ง่ายๆ สำหรับทดสอบ (ของจริงควรอยู่ใน Database หรือ Config)
PRESETS = {
    "CRYPTO_TOP": ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD"],
    "TECH_GIANTS": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"]
}


# ============================================================================
# SINGLE SYMBOL ANALYSIS
# ============================================================================

@router.get("/{symbol}", response_model=TechnicalAnalysisResult)
async def get_technical_analysis(
    symbol: str,
    service: TechnicalAnalysisService = Depends(get_technical_analysis_service)
):
    """
    Get technical analysis summary (Trend, RSI, Signals) for a given symbol.
    """
    logger.info(f"Requesting technical analysis for symbol: {symbol}")
    try:
        result = await service.analyze(symbol)
        logger.info(f"Technical analysis completed successfully for {symbol}")
        return result
    except ValueError as e:
        logger.warning(f"Symbol not found: {symbol} - {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MARKET SCANNER
# ============================================================================

@router.post("/scan", response_model=List[TechnicalAnalysisResult])
async def scan_market(
    symbols: Optional[List[str]] = Body(None, description="Custom list of symbols"),
    preset: Optional[str] = Query(None, description="Use preset list: CRYPTO_TOP, TECH_GIANTS"),
    signal_filter: Optional[str] = Query(None, description="Filter by signal: BUY_DIP, SELL_RALLY"),
    service: MarketScannerService = Depends(get_market_scanner_service)
):
    """
    Scan a list of assets to find trading signals.
    """
    logger.info(f"Starting market scan - preset: {preset}, signal_filter: {signal_filter}")
    
    try:
        target_symbols = []
        default_preset = "TECH_GIANTS"
        
        # 1. Determine list of symbols
        if symbols:
            target_symbols = symbols
            logger.info(f"Using custom symbols: {symbols}")
        elif preset and preset in PRESETS:
            target_symbols = PRESETS[preset]
            logger.info(f"Using preset '{preset}' with {len(target_symbols)} symbols")
        else:
            # Default ถ้าไม่ส่งอะไรมาเลย
            target_symbols = PRESETS[default_preset]
            logger.info(f"Using default preset '{default_preset}' with {len(target_symbols)} symbols")

        if not target_symbols:
            logger.warning("No symbols to scan")
            raise HTTPException(status_code=400, detail="No symbols provided for scanning")

        # 2. Execute Scan
        logger.info(f"Scanning {len(target_symbols)} symbols: {target_symbols}")
        results = await service.scan(target_symbols, filter_signal=signal_filter)
        
        logger.info(f"Market scan completed successfully. Found {len(results)} results")
        return results
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid input for market scan: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during market scan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Market scan failed: {str(e)}")