# app/data_sources/yfinance_provider.py
import asyncio
from typing import List
import pandas as pd
import yfinance as yf
from datetime import datetime
from app.data_sources.base import DataSourceProvider
from app.models.market_data import (
    TranscriptResponse,
    FinancialMetricsResponse,
    FinancialMetrics,
    CashFlowStatement,
    PeerListResponse,
    PriceCandle
)
from app.core.exceptions import (
    DataFetchException,
    SymbolNotFoundException,
    ProviderNotImplementedException
)
from app.core.decorators import handle_exceptions
from app.core.logging_config import get_logger

import pandas as pd


logger = get_logger(__name__)


class YFinanceProvider(DataSourceProvider):
    """Yahoo Finance data provider (free alternative to FMP)"""
    
    @property
    def name(self) -> str:
        return "YFinance"
    
    async def get_transcript(self, symbol: str, quarter: int, year: int) -> TranscriptResponse:
        """
        YFinance does not provide earnings call transcripts.
        This feature is not supported.
        """
        logger.warning(f"[{self.name}] Transcript feature not supported")
        raise ProviderNotImplementedException(
            provider=self.name,
            feature="earnings_transcript"
        )
    
    @handle_exceptions(default_exception=DataFetchException)
    async def get_financial_metrics(self, symbol: str, limit: int = 5) -> FinancialMetricsResponse:
        """
        Fetch financial metrics from Yahoo Finance.
        
        Note: yfinance is synchronous, so we run it in an executor to maintain async interface.
        """
        logger.debug(f"[{self.name}] Fetching financial metrics for {symbol}")
        
        try:
            # Run yfinance in thread pool since it's synchronous
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, symbol)
            
            # Set timeout for yfinance operations
            import signal
            from contextlib import contextmanager
            
            # Fetch data in parallel using thread pool
            info_task = loop.run_in_executor(None, lambda: ticker.info)
            cashflow_task = loop.run_in_executor(None, lambda: ticker.cashflow)
            
            info, cashflow = await asyncio.gather(info_task, cashflow_task)
            
            # Validate symbol exists
            if not info or info.get('regularMarketPrice') is None:
                logger.error(f"[{self.name}] Symbol {symbol} not found or has no data")
                raise SymbolNotFoundException(
                    symbol=symbol,
                    details={"provider": self.name}
                )
            
            # Extract metrics (map YFinance fields to FMP-like structure)
            current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            
            # Build metrics using Pydantic model
            metrics = FinancialMetrics(
                peRatioTTM=info.get('trailingPE'),
                pbRatioTTM=info.get('priceToBook'),
                netIncomePerShareTTM=info.get('trailingEps'),
                bookValuePerShareTTM=info.get('bookValue'),
                dividendYieldTTM=info.get('dividendYield'),
                marketCapTTM=info.get('marketCap'),
                debtToEquityTTM=info.get('debtToEquity'),
                returnOnEquityTTM=info.get('returnOnEquity'),
                revenuePerShareTTM=info.get('revenuePerShare')
            )
            
            # Parse cash flow data (convert DataFrame to list of CashFlowStatement)
            cash_flows = []
            if cashflow is not None and not cashflow.empty:
                # Take latest N years
                cashflow_subset = cashflow.iloc[:, :limit]
                for col in cashflow_subset.columns:
                    fcf = cashflow_subset.loc['Free Cash Flow', col] if 'Free Cash Flow' in cashflow_subset.index else 0
                    cash_flows.append(
                        CashFlowStatement(
                            date=col.strftime('%Y-%m-%d') if isinstance(col, datetime) else str(col),
                            freeCashFlow=float(fcf) if fcf and not pd.isna(fcf) else None
                        )
                    )
            
            logger.info(f"✅ [{self.name}] Successfully fetched financial metrics for {symbol}")
            return FinancialMetricsResponse(
                metrics=metrics,
                price=float(current_price),
                cash_flows=cash_flows
            )
            
        except SymbolNotFoundException:
            raise
        except Exception as e:
            logger.error(f"[{self.name}] Error fetching metrics for {symbol}: {str(e)}")
            raise DataFetchException(
                source=f"{self.name} API",
                details={"symbol": symbol, "error": str(e)}
            )
    
    @handle_exceptions(default_exception=DataFetchException)
    async def get_peers(self, symbol: str) -> PeerListResponse:
        """
        YFinance doesn't provide direct peer comparison data.
        We could potentially scrape from Yahoo Finance website, but that's fragile.
        For now, raise NotImplemented.
        """
        logger.warning(f"[{self.name}] Peer comparison feature not fully supported")
        raise ProviderNotImplementedException(
            provider=self.name,
            feature="peer_comparison"
        )
    
    @handle_exceptions(default_exception=DataFetchException)
    async def get_historical_prices(self, symbol: str, interval: str = "1d", limit: int = 200) -> List[PriceCandle]:
        try:
            period_map = {"1d": "1y", "1h": "1mo", "15m": "5d"}
            period = period_map.get(interval, "1y")
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                return []
            
            candles = []
            for index, row in hist.iterrows():
                candles.append(PriceCandle(
                    timestamp=index.to_pydatetime(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume'])
                ))
            
            return candles[-limit:]
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return []
