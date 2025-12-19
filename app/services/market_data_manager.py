# app/services/market_data_manager.py
"""
Market Data Manager - Orchestrator Service

This service orchestrates the process of fetching data from external providers
and persisting it to the database. It separates concerns:
- market_data.py: Fetches from external providers (FMP, YFinance)
- market_data_persistence.py: Handles database persistence
- market_data_manager.py: Orchestrates fetch → validate → store workflow
"""
from typing import Optional, Dict, Any
from datetime import datetime

from app.services import market_data
from app.services.market_data_persistence import MarketDataPersistenceService
from app.repositories.base import IMarketDataRepository
from app.core.logging_config import get_logger
from app.core.exceptions import DataFetchException

logger = get_logger(__name__)


class MarketDataManager:
    """
    Orchestrator service for managing market data lifecycle:
    fetch from providers → validate → store to database
    """
    
    def __init__(self, market_data_repo: IMarketDataRepository):
        """
        Initialize manager with required dependencies.
        
        Args:
            market_data_repo: Repository for persisting market data
        """
        self.storage_service = MarketDataPersistenceService(market_data_repo)
        logger.info("MarketDataManager initialized")
    
    async def sync_transcript(
        self, 
        symbol: str, 
        quarter: int, 
        year: int,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Fetch earnings transcript from provider and store to database.
        
        Args:
            symbol: Stock ticker symbol
            quarter: Quarter (1-4)
            year: Year
            force_refresh: If True, fetch even if data exists in DB
            
        Returns:
            Dict with status and stored data info
            
        Raises:
            DataFetchException: If fetching from provider fails
        """
        logger.info(f"Syncing transcript for {symbol} Q{quarter} {year}")
        
        # Check if already exists (unless force refresh)
        if not force_refresh:
            existing = await self.storage_service.get_transcript(symbol, quarter, year)
            if existing:
                logger.info(f"Transcript already exists for {symbol} Q{quarter} {year}")
                return {
                    "status": "exists",
                    "symbol": symbol,
                    "quarter": quarter,
                    "year": year,
                    "message": "Data already in database"
                }
        
        # Fetch from provider
        try:
            transcript_data = await market_data.get_earnings_transcript(
                symbol=symbol,
                quarter=quarter,
                year=year,
                fallback=True  # Use fallback providers if primary fails
            )
        except Exception as e:
            logger.error(f"Failed to fetch transcript for {symbol}: {str(e)}")
            raise DataFetchException(
                source=f"transcript for {symbol}",
                details={"error": str(e), "symbol": symbol, "quarter": quarter, "year": year}
            )
        
        # Validate data
        if not transcript_data.content or len(transcript_data.content.strip()) == 0:
            logger.warning(f"Empty transcript received for {symbol} Q{quarter} {year}")
            return {
                "status": "empty",
                "symbol": symbol,
                "quarter": quarter,
                "year": year,
                "message": "Transcript is empty"
            }
        
        # Store to database
        stored = await self.storage_service.save_transcript(
            symbol=symbol,
            quarter=quarter,
            year=year,
            content=transcript_data.content,
            quarter_date=transcript_data.date,
            extra_data={"source": "FMP", "fetched_at": datetime.utcnow().isoformat()}
        )
        
        logger.info(f"Successfully synced transcript for {symbol} Q{quarter} {year}")
        return {
            "status": "synced",
            "symbol": symbol,
            "quarter": quarter,
            "year": year,
            "transcript_id": stored.id,
            "content_length": len(transcript_data.content),
            "message": "Transcript fetched and stored successfully"
        }
    
    async def sync_financial_data(
        self, 
        symbol: str, 
        year: int,
        quarter: Optional[int] = None,
        data_type: str = "income_statement",
        limit: int = 5,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Fetch financial metrics from provider and store to database.
        
        Args:
            symbol: Stock ticker symbol
            year: Year
            quarter: Quarter (1-4), None for annual data
            data_type: Type of financial data (income_statement, balance_sheet, cash_flow)
            limit: Number of historical periods to fetch
            force_refresh: If True, fetch even if data exists in DB
            
        Returns:
            Dict with status and stored data info
            
        Raises:
            DataFetchException: If fetching from provider fails
        """
        logger.info(f"Syncing financial data for {symbol} {year} Q{quarter or 'annual'}")
        
        # Check if already exists (unless force refresh)
        if not force_refresh:
            existing = await self.storage_service.get_financial_data(
                symbol, year, quarter, data_type
            )
            if existing:
                logger.info(f"Financial data already exists for {symbol}")
                return {
                    "status": "exists",
                    "symbol": symbol,
                    "year": year,
                    "quarter": quarter,
                    "data_type": data_type,
                    "message": "Data already in database"
                }
        
        # Fetch from provider
        try:
            metrics = await market_data.get_financial_metrics(
                symbol=symbol,
                limit=limit,
                fallback=True
            )
        except Exception as e:
            logger.error(f"Failed to fetch financial data for {symbol}: {str(e)}")
            raise DataFetchException(
                source=f"financial data for {symbol}",
                details={"error": str(e), "symbol": symbol}
            )
        
        # Validate data
        if not metrics.metrics:
            logger.warning(f"Empty financial data received for {symbol}")
            return {
                "status": "empty",
                "symbol": symbol,
                "year": year,
                "message": "Financial data is empty"
            }
        
        # Store to database
        stored = await self.storage_service.save_financial_data(
            symbol=symbol,
            year=year,
            quarter=quarter,
            data_type=data_type,
            data=metrics.model_dump(),
            extra_data={"source": "FMP", "fetched_at": datetime.utcnow().isoformat()}
        )
        
        logger.info(f"Successfully synced financial data for {symbol}")
        return {
            "status": "synced",
            "symbol": symbol,
            "year": year,
            "quarter": quarter,
            "data_type": data_type,
            "financial_data_id": stored.id,
            "message": "Financial data fetched and stored successfully"
        }
    
    async def sync_all(
        self, 
        symbol: str, 
        quarter: int, 
        year: int,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Sync both transcript and financial data for a company.
        
        Args:
            symbol: Stock ticker symbol
            quarter: Quarter (1-4)
            year: Year
            force_refresh: If True, fetch even if data exists in DB
            
        Returns:
            Dict with results for both operations
        """
        logger.info(f"Syncing all data for {symbol} Q{quarter} {year}")
        
        results = {
            "symbol": symbol,
            "quarter": quarter,
            "year": year,
            "transcript": None,
            "financial_data": None,
            "errors": []
        }
        
        # Sync transcript
        try:
            results["transcript"] = await self.sync_transcript(
                symbol, quarter, year, force_refresh
            )
        except Exception as e:
            logger.error(f"Transcript sync failed: {str(e)}")
            results["errors"].append({
                "type": "transcript",
                "error": str(e)
            })
        
        # Sync financial data
        try:
            results["financial_data"] = await self.sync_financial_data(
                symbol, year, quarter, force_refresh=force_refresh
            )
        except Exception as e:
            logger.error(f"Financial data sync failed: {str(e)}")
            results["errors"].append({
                "type": "financial_data",
                "error": str(e)
            })
        
        # Overall status
        if not results["errors"]:
            results["status"] = "success"
            results["message"] = "All data synced successfully"
        elif results["transcript"] or results["financial_data"]:
            results["status"] = "partial"
            results["message"] = "Some data synced with errors"
        else:
            results["status"] = "failed"
            results["message"] = "All sync operations failed"
        
        return results
