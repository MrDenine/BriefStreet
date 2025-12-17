# app/data_sources/fmp_provider.py
import asyncio
import httpx
from app.data_sources.base import DataSourceProvider
from app.models.market_data import (
    TranscriptResponse,
    FinancialMetricsResponse,
    FinancialMetrics,
    CashFlowStatement,
    PeerListResponse
)
from app.core.config import settings
from app.core.exceptions import (
    DataFetchException,
    TranscriptNotFoundException,
    AuthenticationException,
    RateLimitException,
    ProviderUnavailableException
)
from app.core.decorators import retry_on_exception, handle_exceptions
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class FMPProvider(DataSourceProvider):
    """Financial Modeling Prep API data provider"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.FMP_API_KEY
        self.base_url = settings.FMP_BASE_URL
        
    @property
    def name(self) -> str:
        return "FMP"
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_transcript(self, symbol: str, quarter: int, year: int) -> TranscriptResponse:
        """Fetch earnings call transcript from FMP API"""
        if not self.api_key:
            logger.error("FMP API key not configured")
            raise AuthenticationException(
                message="FMP API key not configured",
                details={"provider": self.name}
            )
        
        logger.debug(f"[{self.name}] Fetching transcript for {symbol} Q{quarter} {year}")
        url = f"{self.base_url}/earning-call-transcript"
        params = {
            "symbol": symbol,
            "quarter": quarter,
            "year": year,
            "apikey": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, timeout=settings.FMP_TIMEOUT)
                
                # Handle rate limiting
                if response.status_code == 429:
                    logger.warning(f"[{self.name}] Rate limit exceeded for {symbol}")
                    raise RateLimitException(
                        message=f"{self.name} rate limit exceeded",
                        retry_after=settings.FMP_RATE_LIMIT_RETRY_AFTER
                    )
                
                # Handle service unavailable
                if response.status_code == 503:
                    raise ProviderUnavailableException(
                        provider=self.name,
                        reason="API maintenance or temporary outage"
                    )
                
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    logger.warning(f"[{self.name}] No transcript data found for {symbol}")
                    raise TranscriptNotFoundException(
                        symbol=symbol,
                        quarter=f"Q{quarter} {year}"
                    )
                
                logger.info(f"✅ [{self.name}] Successfully fetched transcript for {symbol} (Date: {data[0]['date']})")
                return TranscriptResponse(
                    date=data[0]['date'],
                    content=data[0]['content']
                )
                
            except httpx.HTTPError as e:
                logger.error(f"[{self.name}] HTTP error fetching {symbol}: {str(e)}")
                raise DataFetchException(
                    source=f"{self.name} API",
                    details={"symbol": symbol, "error": str(e)}
                )
            except (KeyError, IndexError) as e:
                logger.error(f"[{self.name}] Data parsing error for {symbol}: {str(e)}")
                raise TranscriptNotFoundException(
                    symbol=symbol,
                    quarter=f"Q{quarter} {year}"
                )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_financial_metrics(self, symbol: str, limit: int = 5) -> FinancialMetricsResponse:
        """Fetch financial metrics from FMP API using parallel requests"""
        if not self.api_key:
            raise AuthenticationException(
                message="FMP API key not configured",
                details={"provider": self.name}
            )
        
        logger.debug(f"[{self.name}] Fetching financial metrics for {symbol}")
        
        async with httpx.AsyncClient() as client:
            # Build URLs for parallel requests
            metrics_url = f"{self.base_url}/key-metrics-ttm"
            quote_url = f"{self.base_url}/quote"
            cf_url = f"{self.base_url}/cash-flow-statement"
            
            params_metrics = {"symbol": symbol, "apikey": self.api_key}
            params_quote = {"symbol": symbol, "apikey": self.api_key}
            params_cf = {
                "symbol": symbol,
                "period": "annual",
                "limit": limit,
                "apikey": self.api_key
            }
            
            try:
                # Execute requests in parallel
                responses = await asyncio.gather(
                    client.get(metrics_url, params=params_metrics, timeout=settings.FMP_TIMEOUT),
                    client.get(quote_url, params=params_quote, timeout=settings.FMP_TIMEOUT),
                    client.get(cf_url, params=params_cf, timeout=settings.FMP_TIMEOUT)
                )
                
                # Check for rate limiting on any response
                for i, resp in enumerate(responses):
                    if resp.status_code == 429:
                        raise RateLimitException(
                            message=f"{self.name} rate limit exceeded",
                            retry_after=settings.FMP_RATE_LIMIT_RETRY_AFTER
                        )
                    resp.raise_for_status()
                
                # Parse responses
                metrics_data = responses[0].json()
                quote_data = responses[1].json()
                cf_data = responses[2].json()
                
                if not metrics_data or not quote_data:
                    raise DataFetchException(
                        source=f"{self.name} Metrics",
                        details={"symbol": symbol, "reason": "Empty response data"}
                    )
                
                # Convert cash flows to CashFlowStatement models
                cash_flow_statements = [
                    CashFlowStatement(**cf) for cf in cf_data
                ] if cf_data else []
                
                logger.info(f"✅ [{self.name}] Successfully fetched financial metrics for {symbol}")
                return FinancialMetricsResponse(
                    metrics=FinancialMetrics(**metrics_data[0]),
                    price=float(quote_data[0]['price']),
                    cash_flows=cash_flow_statements
                )
                
            except httpx.HTTPError as e:
                logger.error(f"[{self.name}] HTTP error fetching metrics for {symbol}: {str(e)}")
                raise DataFetchException(
                    source=f"{self.name} API",
                    details={"symbol": symbol, "error": str(e)}
                )
            except (KeyError, IndexError) as e:
                logger.error(f"[{self.name}] Data parsing error for {symbol}: {str(e)}")
                raise DataFetchException(
                    source=f"{self.name} Metrics",
                    details={"symbol": symbol, "error": f"Invalid data format: {str(e)}"}
                )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_peers(self, symbol: str) -> PeerListResponse:
        """Fetch list of peer companies from FMP API"""
        if not self.api_key:
            raise AuthenticationException(
                message="FMP API key not configured",
                details={"provider": self.name}
            )
        
        logger.debug(f"[{self.name}] Fetching peers for {symbol}")
        url = f"{self.base_url}/stock-peers"
        params = {"symbol": symbol, "apikey": self.api_key}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, timeout=settings.FMP_TIMEOUT)
                
                if response.status_code == 429:
                    raise RateLimitException(
                        message=f"{self.name} rate limit exceeded",
                        retry_after=settings.FMP_RATE_LIMIT_RETRY_AFTER
                    )
                
                response.raise_for_status()
                peers_list = response.json()
                
                if not peers_list:
                    logger.warning(f"[{self.name}] No peers found for {symbol}")
                    return PeerListResponse(peers=[])
                
                # Return top N peers based on config
                top_peers = peers_list[0].get('peersList', [])[:settings.DEFAULT_PEERS_LIMIT]
                logger.info(f"✅ [{self.name}] Found {len(top_peers)} peers for {symbol}")
                return PeerListResponse(peers=top_peers)
                
            except httpx.HTTPError as e:
                logger.error(f"[{self.name}] HTTP error fetching peers for {symbol}: {str(e)}")
                raise DataFetchException(
                    source=f"{self.name} API",
                    details={"symbol": symbol, "error": str(e)}
                )
            except (KeyError, IndexError) as e:
                logger.warning(f"[{self.name}] Could not parse peers data for {symbol}: {str(e)}")
                return PeerListResponse(peers=[])
