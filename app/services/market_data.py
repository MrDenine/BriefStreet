import asyncio
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
            raise TranscriptNotFoundException(symbol=symbol, quarter=f"Q{quarter} {year}")
        
@retry_on_exception(max_retries=3, exceptions=(httpx.HTTPError,), delay=1.0)
async def get_financial_metrics(symbol: str, limit: int = 5) -> dict:
    """ดึงข้อมูลการเงินสำคัญสำหรับ Valuation"""
    async with httpx.AsyncClient() as client:
        # 1. ดึง Key Metrics (PE, PBV, BVPS, EPS, FCF)
        metrics_url = f"https://financialmodelingprep.com/stable/key-metrics-ttm?symbol={symbol}&apikey={settings.FMP_API_KEY}"
        
        # 2. ดึงราคาปัจจุบัน
        quote_url = f"https://financialmodelingprep.com/stable/quote?symbol={symbol}&apikey={settings.FMP_API_KEY}"
        
        # 3. ดึง Cash Flow ย้อนหลัง 5 ปี (สำหรับ DCF)
        cf_url = f"https://financialmodelingprep.com/stable/cash-flow-statement?symbol={symbol}&period=annual&limit={limit}&apikey={settings.FMP_API_KEY}"

        # ยิง Request แบบ Parallel (เพื่อให้เร็ว)
        responses = await asyncio.gather(
            client.get(metrics_url),
            client.get(quote_url),
            client.get(cf_url)
        )
        
        metrics_data = responses[0].json()
        quote_data = responses[1].json()
        cf_data = responses[2].json()

        if not metrics_data or not quote_data:
             raise DataFetchException(source="FMP Metrics", details={"symbol": symbol})

        return {
            "metrics": metrics_data[0], # PE, PBV, DividendYield, etc.
            "price": quote_data[0]['price'],
            "cash_flows": cf_data # List of annual reports
        }
    
@retry_on_exception(max_retries=3, exceptions=(httpx.HTTPError,), delay=1.0)
async def get_peers_valuation(symbol: str) -> list:
    """ดึง PE/PBV ของคู่แข่ง"""
    # 1. หา list คู่แข่ง
    peers_url = f"https://financialmodelingprep.com/stable/stock-peers?symbol={symbol}&apikey={settings.FMP_API_KEY}"
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(peers_url)
        peers_list = resp.json() 
        if not peers_list: return []
        
        # สมมติเอาแค่ 5 ตัวแรก
        top_peers = peers_list[0]['peersList'][:5]
        
        # ดึง Quote ของคู่แข่งเพื่อหา PE (แบบง่าย) หรือจะวนลูปดึง Key Metrics ก็ได้
        # FMP มี endpoint /v4/batch-request-end-of-day-prices หรือวนลูปเอาก็ได้สำหรับ Micro SaaS
        # เพื่อความง่ายในตัวอย่างนี้ ผมจะสมมติว่าดึง PE/PBV มาได้แล้ว
        return top_peers # ส่งรายชื่อกลับไปก่อน (ใน valuation_service ค่อยไปดึงค่า)