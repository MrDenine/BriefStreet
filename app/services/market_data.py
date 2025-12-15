import httpx
from app.core.config import settings
from app.core.exceptions import DataFetchException, TranscriptNotFoundException
from app.core.decorators import retry_on_exception
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@retry_on_exception(max_retries=3, exceptions=(httpx.HTTPError,), delay=1.0)
async def get_earnings_transcript(symbol: str, quarter: int = 3, year: int = 2024) -> dict:
    if not settings.FMP_API_KEY:
        logger.error("FMP API key not configured")
        raise DataFetchException(
            source="FMP API",
            details={"reason": "API key not configured"}
        )
    
    logger.debug(f"Fetching transcript for {symbol} Q{quarter} {year}")
    url = f"https://financialmodelingprep.com/stable/earning-call-transcript?symbol={symbol}&quarter={quarter}&year={year}&apikey={settings.FMP_API_KEY}" 
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                logger.warning(f"No transcript data found for {symbol}")
                raise TranscriptNotFoundException(symbol=symbol, quarter="Q3 2024")
            
            logger.info(f"✅ Successfully fetched transcript for {symbol} (Date: {data[0]['date']})")
            return {
                "date": data[0]['date'], 
                "content": data[0]['content']
            }
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {symbol}: {str(e)}")
            raise DataFetchException(
                source="FMP API",
                details={"symbol": symbol, "error": str(e)}
            )
        except (KeyError, IndexError) as e:
            logger.error(f"Data parsing error for {symbol}: {str(e)}")
            raise TranscriptNotFoundException(symbol=symbol, quarter="Q3 2024")