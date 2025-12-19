# app/data_sources/fmp_provider.py
import asyncio
from typing import List
import httpx
from app.data_sources.base import DataSourceProvider
from app.models.market_data import (
    CUSIPResponse,
    CentralIndexKeyResponse,
    CompanyScreenerResponse,
    ExchangeVariantsResponse,
    FinancialStatementSymbolResponse,
    InternationalSecurityIdentifierNumberResponse,
    SearchSymbolResponse,
    StocksResponse,
    TranscriptResponse,
    FinancialMetricsResponse,
    FinancialMetrics,
    CashFlowStatement,
    PeerListResponse,
    CIKResponse,
    SymbolChangeResponse,
    ETFListResponse,
    ExchangeResponse,
    SectorResponse,
    IndustryResponse,
    CountryResponse,
    CompanyProfileResponse,
    CompanyNotesResponse,
    DelistedCompanyResponse,
    EmployeeCountResponse,
    MarketCapResponse,
    SharesFloatResponse,
    MergerAcquisitionResponse,
    ExecutiveResponse,
    ExecutiveCompensationResponse
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
        self._validate_api_key()
        
    @property
    def name(self) -> str:
        return "FMP"
    
    def _validate_api_key(self):
        """Validate API key on initialization"""
        if not self.api_key:
            raise AuthenticationException(
                message="FMP API key not configured",
                details={"provider": self.name}
            )
    
    async def _make_request(self, url: str, params: dict) -> dict:
        """Centralized HTTP request handler with common error handling"""
        params["apikey"] = self.api_key
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=settings.FMP_TIMEOUT)
            
            # Handle rate limiting
            if response.status_code == 429:
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
            return response.json()
    
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def search_symbol(self, query:str, limit:int=50, exchange:str=None) -> List[SearchSymbolResponse]:
        """Stock Symbol Search from FMP API"""
        logger.debug(f"[{self.name}] Searching for symbols matching query: {query}")
        url = f"{self.base_url}/search-symbol"
        params = {"query": query, "limit": limit, "exchange": exchange}
        
        try:
            data = await self._make_request(url, params)
            results = [SearchSymbolResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Found {len(results)} symbols for query: {query}")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error during symbol search: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"query": query, "error": str(e)}
            )
        
    
            
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def search_company(self, query: str, limit: int = 50, exchange: str = None) -> List[SearchSymbolResponse]:
        """Company search from FMP API"""
        logger.debug(f"[{self.name}] Searching for companies matching query: {query}")
        url = f"{self.base_url}/search-name"
        params = {"query": query, "limit": limit, "exchange": exchange}
        
        try:
            data = await self._make_request(url, params)
            results = [SearchSymbolResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Found {len(results)} companies for query: {query}")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error during company search: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"query": query, "error": str(e)}
            )
        
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def search_cik(self, cik:str, limit:int=50) -> List[CentralIndexKeyResponse]:
        """CIK Search from FMP API"""
        logger.debug(f"[{self.name}] Searching for CIK: {cik}")
        url = f"{self.base_url}/search-cik"
        params = {"cik": cik, "limit": limit}
        
        try:
            data = await self._make_request(url, params)
            results = [CentralIndexKeyResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Found {len(results)} entries for CIK: {cik}")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error during CIK search: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"cik": cik, "error": str(e)}
        )

    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def search_cusip(self, cusip:str) -> List[CUSIPResponse]:
        """CUSIP Search from FMP API"""
        logger.debug(f"[{self.name}] Searching for CUSIP: {cusip}")
        url = f"{self.base_url}/search-cusip"
        params = {"cusip": cusip}
        
        try:
            data = await self._make_request(url, params)
            results = [CUSIPResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Found {len(results)} entries for CUSIP: {cusip}")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error during CUSIP search: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"cusip": cusip, "error": str(e)}
            )
        
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def search_isin(self, isin:str) -> List[InternationalSecurityIdentifierNumberResponse]:
        """ISIN Search from FMP API"""
        logger.debug(f"[{self.name}] Searching for ISIN: {isin}")
        url = f"{self.base_url}/search-isin"
        params = {"isin": isin}
        
        try:
            data = await self._make_request(url, params)
            results = [InternationalSecurityIdentifierNumberResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Found {len(results)} entries for ISIN: {isin}")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error during ISIN search: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"isin": isin, "error": str(e)}
            )
        
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def company_screener(
            self,
            marketCapMoreThan: float = None,
            marketCapLessThan: float = None,
            sector: str = None,
            industry: str = None,
            betaMoreThan: float = None,
            betaLessThan: float = None,
            priceMoreThan: float = None,
            priceLessThan: float = None,
            dividendMoreThan: float = None,
            dividendLessThan: float = None,
            volumeMoreThan: int = None,
            volumeLessThan: int = None,
            exchange: str = None,
            country: str = None,
            isEtf: bool = None,
            isFund: bool = None,
            isActivelyTrading: bool = None,
            limit: int = 1000,
            includeAllShareClasses: bool = False
        ) -> List[CompanyScreenerResponse]: 
            """Company Screener from FMP API"""
            logger.debug(f"[{self.name}] Running company screener with provided filters")
            url = f"{self.base_url}/company-screener"
            params = {
                "marketCapMoreThan": marketCapMoreThan,
                "marketCapLessThan": marketCapLessThan,
                "sector": sector,
                "industry": industry,
                "betaMoreThan": betaMoreThan,
                "betaLessThan": betaLessThan,
                "priceMoreThan": priceMoreThan,
                "priceLessThan": priceLessThan,
                "dividendMoreThan": dividendMoreThan,
                "dividendLessThan": dividendLessThan,
                "volumeMoreThan": volumeMoreThan,
                "volumeLessThan": volumeLessThan,
                "exchange": exchange,
                "country": country,
                "isEtf": isEtf,
                "isFund": isFund,
                "isActivelyTrading": isActivelyTrading,
                "limit": limit,
                "includeAllShareClasses": str(includeAllShareClasses).lower()
            }
            try:
                data = await self._make_request(url, params)
                results = [CompanyScreenerResponse(**item) for item in data]
                logger.info(f"✅ [{self.name}] Company screener returned {len(results)} results")
                return results
            except httpx.HTTPError as e:
                logger.error(f"[{self.name}] HTTP error during company screener: {str(e)}")
                raise DataFetchException(
                    source=f"{self.name} API",
                    details={"error": str(e)}
                )
            
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def search_exchange_variants(self, symbol: str) -> List[ExchangeVariantsResponse]:
        """Exchange Variants Search from FMP API"""
        logger.debug(f"[{self.name}] Searching for exchange variants of symbol: {symbol}")
        url = f"{self.base_url}/search-exchange-variants"
        params = {"symbol": symbol}
        
        try:
            data = await self._make_request(url, params)
            results = [ExchangeVariantsResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Found {len(results)} exchange variants for symbol: {symbol}")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error during exchange variants search: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"symbol": symbol, "error": str(e)}
            )
        
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_stock_list(self)-> List[StocksResponse]:
        """Fetch list of all stocks from FMP API"""
        logger.debug(f"[{self.name}] Fetching stock list")
        url = f"{self.base_url}/stock-list"
        params = {}
        
        try:
            data = await self._make_request(url, params)
            results = [StocksResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched {len(results)} stocks from stock list")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching stock list: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"error": str(e)}
            )
        
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_financial_statement_symbol(self) -> List[FinancialStatementSymbolResponse]:
        """Fetch financial statement symbols from FMP API"""
        logger.debug(f"[{self.name}] Fetching financial statement symbols")
        url = f"{self.base_url}/financial-statement-symbol-list"
        params = {}
        
        try:
            data = await self._make_request(url, params)
            results = [FinancialStatementSymbolResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched {len(results)} financial statement symbols")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching financial statement symbols: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"error": str(e)}
            )

    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_transcript(self, symbol: str, quarter: int, year: int) -> TranscriptResponse:
        """Fetch earnings call transcript from FMP API"""
        logger.debug(f"[{self.name}] Fetching transcript for {symbol} Q{quarter} {year}")
        url = f"{self.base_url}/earning-call-transcript"
        params = {"symbol": symbol, "quarter": quarter, "year": year}
        
        try:
            data = await self._make_request(url, params)
            
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
        logger.debug(f"[{self.name}] Fetching financial metrics for {symbol}")
        
        # Build URLs and params for parallel requests
        metrics_url = f"{self.base_url}/key-metrics-ttm"
        quote_url = f"{self.base_url}/quote"
        cf_url = f"{self.base_url}/cash-flow-statement"
        
        params_metrics = {"symbol": symbol, "apikey": self.api_key}
        params_quote = {"symbol": symbol, "apikey": self.api_key}
        params_cf = {"symbol": symbol, "period": "annual", "limit": limit, "apikey": self.api_key}
        
        async with httpx.AsyncClient() as client:
            try:
                # Execute requests in parallel
                responses = await asyncio.gather(
                    client.get(metrics_url, params=params_metrics, timeout=settings.FMP_TIMEOUT),
                    client.get(quote_url, params=params_quote, timeout=settings.FMP_TIMEOUT),
                    client.get(cf_url, params=params_cf, timeout=settings.FMP_TIMEOUT)
                )
                
                # Check for rate limiting and errors on any response
                for resp in responses:
                    if resp.status_code == 429:
                        raise RateLimitException(
                            message=f"{self.name} rate limit exceeded",
                            retry_after=settings.FMP_RATE_LIMIT_RETRY_AFTER
                        )
                    if resp.status_code == 503:
                        raise ProviderUnavailableException(
                            provider=self.name,
                            reason="API maintenance or temporary outage"
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
        logger.debug(f"[{self.name}] Fetching peers for {symbol}")
        url = f"{self.base_url}/stock-peers"
        params = {"symbol": symbol}
        
        try:
            peers_list = await self._make_request(url, params)
            
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
    
    # ============= New API Methods from FMP_api.md =============
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_cik_list(self, page: int = 0, limit: int = 1000) -> List[CIKResponse]:
        """Fetch CIK (Central Index Key) list from FMP API"""
        logger.debug(f"[{self.name}] Fetching CIK list (page={page}, limit={limit})")
        url = f"{self.base_url}/cik-list"
        params = {"page": page, "limit": limit}
        
        try:
            data = await self._make_request(url, params)
            results = [CIKResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched {len(results)} CIK entries")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching CIK list: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_symbol_changes(self, invalid: str = "false", limit: int = 1000) -> List[SymbolChangeResponse]:
        """Fetch stock symbol changes from FMP API"""
        logger.debug(f"[{self.name}] Fetching symbol changes (limit={limit})")
        url = f"{self.base_url}/symbol-change"
        params = {"invalid": invalid, "limit": limit}
        
        try:
            data = await self._make_request(url, params)
            results = [SymbolChangeResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched {len(results)} symbol changes")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching symbol changes: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_etf_list(self) -> List[ETFListResponse]:
        """Fetch ETF list from FMP API"""
        logger.debug(f"[{self.name}] Fetching ETF list")
        url = f"{self.base_url}/etf-list"
        params = {}
        
        try:
            data = await self._make_request(url, params)
            results = [ETFListResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched {len(results)} ETFs")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching ETF list: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_actively_trading_list(self) -> List[ETFListResponse]:
        """Fetch actively trading companies list from FMP API"""
        logger.debug(f"[{self.name}] Fetching actively trading list")
        url = f"{self.base_url}/actively-trading-list"
        params = {}
        
        try:
            data = await self._make_request(url, params)
            results = [ETFListResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched {len(results)} actively trading companies")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching actively trading list: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_available_exchanges(self) -> List[ExchangeResponse]:
        """Fetch available stock exchanges from FMP API"""
        logger.debug(f"[{self.name}] Fetching available exchanges")
        url = f"{self.base_url}/available-exchanges"
        params = {}
        
        try:
            data = await self._make_request(url, params)
            results = [ExchangeResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched {len(results)} exchanges")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching exchanges: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_available_sectors(self) -> List[SectorResponse]:
        """Fetch available sectors from FMP API"""
        logger.debug(f"[{self.name}] Fetching available sectors")
        url = f"{self.base_url}/available-sectors"
        params = {}
        
        try:
            data = await self._make_request(url, params)
            results = [SectorResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched {len(results)} sectors")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching sectors: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_available_industries(self) -> List[IndustryResponse]:
        """Fetch available industries from FMP API"""
        logger.debug(f"[{self.name}] Fetching available industries")
        url = f"{self.base_url}/available-industries"
        params = {}
        
        try:
            data = await self._make_request(url, params)
            results = [IndustryResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched {len(results)} industries")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching industries: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_available_countries(self) -> List[CountryResponse]:
        """Fetch available countries from FMP API"""
        logger.debug(f"[{self.name}] Fetching available countries")
        url = f"{self.base_url}/available-countries"
        params = {}
        
        try:
            data = await self._make_request(url, params)
            results = [CountryResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched {len(results)} countries")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching countries: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_company_profile(self, symbol: str) -> CompanyProfileResponse:
        """Fetch company profile data from FMP API"""
        logger.debug(f"[{self.name}] Fetching company profile for {symbol}")
        url = f"{self.base_url}/profile"
        params = {"symbol": symbol}
        
        try:
            data = await self._make_request(url, params)
            if not data:
                raise DataFetchException(
                    source=f"{self.name} API",
                    details={"symbol": symbol, "reason": "No profile data found"}
                )
            logger.info(f"✅ [{self.name}] Fetched company profile for {symbol}")
            return CompanyProfileResponse(**data[0])
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching profile for {symbol}: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"symbol": symbol, "error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_company_profile_by_cik(self, cik: str) -> CompanyProfileResponse:
        """Fetch company profile by CIK from FMP API"""
        logger.debug(f"[{self.name}] Fetching company profile for CIK {cik}")
        url = f"{self.base_url}/profile-cik"
        params = {"cik": cik}
        
        try:
            data = await self._make_request(url, params)
            if not data:
                raise DataFetchException(
                    source=f"{self.name} API",
                    details={"cik": cik, "reason": "No profile data found"}
                )
            logger.info(f"✅ [{self.name}] Fetched company profile for CIK {cik}")
            return CompanyProfileResponse(**data[0])
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching profile for CIK {cik}: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"cik": cik, "error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_company_notes(self, symbol: str) -> List[CompanyNotesResponse]:
        """Fetch company notes from FMP API"""
        logger.debug(f"[{self.name}] Fetching company notes for {symbol}")
        url = f"{self.base_url}/company-notes"
        params = {"symbol": symbol}
        
        try:
            data = await self._make_request(url, params)
            results = [CompanyNotesResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched {len(results)} company notes for {symbol}")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching company notes for {symbol}: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"symbol": symbol, "error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_delisted_companies(self, page: int = 0, limit: int = 100) -> List[DelistedCompanyResponse]:
        """Fetch delisted companies from FMP API"""
        logger.debug(f"[{self.name}] Fetching delisted companies (page={page}, limit={limit})")
        url = f"{self.base_url}/delisted-companies"
        params = {"page": page, "limit": limit}
        
        try:
            data = await self._make_request(url, params)
            results = [DelistedCompanyResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched {len(results)} delisted companies")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching delisted companies: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_employee_count(self, symbol: str, limit: int = 100) -> List[EmployeeCountResponse]:
        """Fetch employee count data from FMP API"""
        logger.debug(f"[{self.name}] Fetching employee count for {symbol}")
        url = f"{self.base_url}/employee-count"
        params = {"symbol": symbol, "limit": limit}
        
        try:
            data = await self._make_request(url, params)
            results = [EmployeeCountResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched {len(results)} employee count records for {symbol}")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching employee count for {symbol}: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"symbol": symbol, "error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_historical_employee_count(self, symbol: str, limit: int = 100) -> List[EmployeeCountResponse]:
        """Fetch historical employee count data from FMP API"""
        logger.debug(f"[{self.name}] Fetching historical employee count for {symbol}")
        url = f"{self.base_url}/historical-employee-count"
        params = {"symbol": symbol, "limit": limit}
        
        try:
            data = await self._make_request(url, params)
            results = [EmployeeCountResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched {len(results)} historical employee count records for {symbol}")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching historical employee count for {symbol}: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"symbol": symbol, "error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_market_cap(self, symbol: str) -> MarketCapResponse:
        """Fetch market capitalization from FMP API"""
        logger.debug(f"[{self.name}] Fetching market cap for {symbol}")
        url = f"{self.base_url}/market-capitalization"
        params = {"symbol": symbol}
        
        try:
            data = await self._make_request(url, params)
            if not data:
                raise DataFetchException(
                    source=f"{self.name} API",
                    details={"symbol": symbol, "reason": "No market cap data found"}
                )
            logger.info(f"✅ [{self.name}] Fetched market cap for {symbol}")
            return MarketCapResponse(**data[0])
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching market cap for {symbol}: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"symbol": symbol, "error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_batch_market_cap(self, symbols: List[str]) -> List[MarketCapResponse]:
        """Fetch market cap for multiple symbols from FMP API"""
        symbols_str = ",".join(symbols)
        logger.debug(f"[{self.name}] Fetching batch market cap for {len(symbols)} symbols")
        url = f"{self.base_url}/market-capitalization-batch"
        params = {"symbols": symbols_str}
        
        try:
            data = await self._make_request(url, params)
            results = [MarketCapResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched market cap for {len(results)} symbols")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching batch market cap: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_historical_market_cap(self, symbol: str, limit: int = 100, from_date: str = None, to_date: str = None) -> List[MarketCapResponse]:
        """Fetch historical market cap from FMP API"""
        logger.debug(f"[{self.name}] Fetching historical market cap for {symbol}")
        url = f"{self.base_url}/historical-market-capitalization"
        params = {"symbol": symbol, "limit": limit}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        
        try:
            data = await self._make_request(url, params)
            results = [MarketCapResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched {len(results)} historical market cap records for {symbol}")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching historical market cap for {symbol}: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"symbol": symbol, "error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_shares_float(self, symbol: str) -> SharesFloatResponse:
        """Fetch shares float data from FMP API"""
        logger.debug(f"[{self.name}] Fetching shares float for {symbol}")
        url = f"{self.base_url}/shares-float"
        params = {"symbol": symbol}
        
        try:
            data = await self._make_request(url, params)
            if not data:
                raise DataFetchException(
                    source=f"{self.name} API",
                    details={"symbol": symbol, "reason": "No shares float data found"}
                )
            logger.info(f"✅ [{self.name}] Fetched shares float for {symbol}")
            return SharesFloatResponse(**data[0])
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching shares float for {symbol}: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"symbol": symbol, "error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_all_shares_float(self, page: int = 0, limit: int = 1000) -> List[SharesFloatResponse]:
        """Fetch all shares float data from FMP API"""
        logger.debug(f"[{self.name}] Fetching all shares float (page={page}, limit={limit})")
        url = f"{self.base_url}/shares-float-all"
        params = {"page": page, "limit": limit}
        
        try:
            data = await self._make_request(url, params)
            results = [SharesFloatResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched {len(results)} shares float records")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching all shares float: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_latest_mergers_acquisitions(self, page: int = 0, limit: int = 100) -> List[MergerAcquisitionResponse]:
        """Fetch latest mergers and acquisitions from FMP API"""
        logger.debug(f"[{self.name}] Fetching latest M&A (page={page}, limit={limit})")
        url = f"{self.base_url}/mergers-acquisitions-latest"
        params = {"page": page, "limit": limit}
        
        try:
            data = await self._make_request(url, params)
            results = [MergerAcquisitionResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched {len(results)} M&A records")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching M&A: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_company_executives(self, symbol: str, active: str = None) -> List[ExecutiveResponse]:
        """Fetch company executives from FMP API"""
        logger.debug(f"[{self.name}] Fetching executives for {symbol}")
        url = f"{self.base_url}/key-executives"
        params = {"symbol": symbol}
        if active:
            params["active"] = active
        
        try:
            data = await self._make_request(url, params)
            results = [ExecutiveResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched {len(results)} executives for {symbol}")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching executives for {symbol}: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"symbol": symbol, "error": str(e)}
            )
    
    @retry_on_exception(max_retries=settings.FMP_MAX_RETRIES, exceptions=(httpx.HTTPError,), delay=settings.FMP_RETRY_DELAY)
    @handle_exceptions(default_exception=DataFetchException)
    async def get_executive_compensation(self, symbol: str) -> List[ExecutiveCompensationResponse]:
        """Fetch executive compensation from FMP API"""
        logger.debug(f"[{self.name}] Fetching executive compensation for {symbol}")
        url = f"{self.base_url}/governance-executive-compensation"
        params = {"symbol": symbol}
        
        try:
            data = await self._make_request(url, params)
            results = [ExecutiveCompensationResponse(**item) for item in data]
            logger.info(f"✅ [{self.name}] Fetched {len(results)} executive compensation records for {symbol}")
            return results
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] HTTP error fetching executive compensation for {symbol}: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"symbol": symbol, "error": str(e)}
            )
