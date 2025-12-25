# app/data_sources/base.py
from abc import ABC, abstractmethod
from typing import List
from app.models.market_data import (
    TranscriptResponse,
    FinancialMetricsResponse,
    PeerListResponse,
    PriceCandle
)


class DataSourceProvider(ABC):
    """
    Abstract base class for all market data providers.
    
    This interface defines the contract that all data providers must implement.
    Providers can choose to raise ProviderNotImplementedException for features they don't support.
    """

    @abstractmethod
    async def get_historical_prices(self, symbol: str, interval: str = "1d", limit: int = 200) -> List[PriceCandle]:
        """Fetch historical OHLCV data."""
        pass
    
    @abstractmethod
    async def get_transcript(self, symbol: str, quarter: int, year: int) -> TranscriptResponse:
        """
        Fetch earnings call transcript for a given symbol, quarter, and year.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            quarter: Quarter number (1-4)
            year: Year (e.g., 2024)
            
        Returns:
            TranscriptResponse containing date and content
                
        Raises:
            TranscriptNotFoundException: If transcript is not found
            ProviderNotImplementedException: If provider doesn't support transcripts
            DataFetchException: If API request fails
        """
        pass
    
    @abstractmethod
    async def get_financial_metrics(self, symbol: str, limit: int = 5) -> FinancialMetricsResponse:
        """
        Fetch key financial metrics for valuation analysis.
        
        Args:
            symbol: Stock ticker symbol
            limit: Number of historical periods to fetch
            
        Returns:
            FinancialMetricsResponse containing metrics, price, and cash flows
                
        Raises:
            SymbolNotFoundException: If symbol is not found
            DataFetchException: If API request fails
        """
        pass
    
    @abstractmethod
    async def get_peers(self, symbol: str) -> PeerListResponse:
        """
        Fetch list of peer companies for comparative analysis.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            PeerListResponse containing list of peer ticker symbols
            
        Raises:
            ProviderNotImplementedException: If provider doesn't support peer data
            DataFetchException: If API request fails
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name for logging and error messages"""
        pass
