# app/services/market_data.py
"""
High-level market data service with provider abstraction.

This service acts as a facade, delegating to configured data providers.
Supports multiple providers with fallback mechanisms.
"""
from typing import Dict, List, Optional
from app.data_sources.base import DataSourceProvider
from app.data_sources import FMPProvider, YFinanceProvider, MockProvider
from app.core.config import settings
from app.core.exceptions import (
    AllProvidersFailedException,
    ProviderNotImplementedException,
    DataFetchException
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Global provider instance (can be changed via dependency injection)
_current_provider: Optional[DataSourceProvider] = None


def get_provider() -> DataSourceProvider:
    """
    Get the currently configured data provider.
    
    Priority:
    1. Explicitly set provider via set_provider()
    2. Provider from settings.DATA_PROVIDER
    3. Default to FMP
    """
    global _current_provider
    
    if _current_provider is not None:
        return _current_provider
    
    # Get provider from settings
    provider_name = getattr(settings, 'DATA_PROVIDER', 'fmp').lower()
    
    if provider_name == 'yfinance':
        logger.info("Using YFinance data provider")
        return YFinanceProvider()
    elif provider_name == 'mock':
        logger.info("Using Mock data provider")
        return MockProvider()
    else:  # Default to FMP
        logger.info("Using FMP data provider")
        return FMPProvider()


def set_provider(provider: DataSourceProvider) -> None:
    """
    Set the data provider to use for all subsequent requests.
    Useful for testing and runtime provider switching.
    
    Args:
        provider: Instance of DataSourceProvider to use
    """
    global _current_provider
    _current_provider = provider
    logger.info(f"Data provider set to: {provider.name}")


def reset_provider() -> None:
    """Reset to default provider from settings"""
    global _current_provider
    _current_provider = None
    logger.info("Data provider reset to default")


async def get_earnings_transcript(
    symbol: str, 
    quarter: int = 3, 
    year: int = 2024,
    fallback: bool = False
) -> Dict:
    """
    Fetch earnings call transcript using configured provider.
    
    Args:
        symbol: Stock ticker symbol
        quarter: Quarter (1-4)
        year: Year
        fallback: If True, try alternative providers on failure
        
    Returns:
        Dictionary with 'date' and 'content' keys
    """
    provider = get_provider()
    
    if not fallback:
        # Single provider mode
        return await provider.get_transcript(symbol, quarter, year)
    
    # Multi-provider fallback mode
    providers = [provider]
    
    # Add fallback providers (skip if same as primary)
    if not isinstance(provider, MockProvider):
        providers.append(MockProvider())
    
    errors = {}
    for prov in providers:
        try:
            logger.info(f"Attempting to fetch transcript from {prov.name}")
            return await prov.get_transcript(symbol, quarter, year)
        except ProviderNotImplementedException as e:
            logger.warning(f"{prov.name} doesn't support transcripts: {e.message}")
            errors[prov.name] = e.message
            continue
        except Exception as e:
            logger.error(f"{prov.name} failed: {str(e)}")
            errors[prov.name] = str(e)
            continue
    
    # All providers failed
    raise AllProvidersFailedException(
        feature="earnings_transcript",
        attempted_providers=[p.name for p in providers],
        errors=errors
    )


async def get_financial_metrics(
    symbol: str, 
    limit: int = 5,
    fallback: bool = False
) -> Dict:
    """
    Fetch financial metrics for valuation analysis.
    
    Args:
        symbol: Stock ticker symbol
        limit: Number of historical periods
        fallback: If True, try alternative providers on failure
        
    Returns:
        Dictionary with 'metrics', 'price', and 'cash_flows' keys
    """
    provider = get_provider()
    
    if not fallback:
        return await provider.get_financial_metrics(symbol, limit)
    
    # Multi-provider fallback mode
    providers = [provider]
    
    # Add YFinance as fallback if not primary
    if not isinstance(provider, YFinanceProvider):
        providers.append(YFinanceProvider())
    
    # Add Mock as last resort
    if not isinstance(provider, MockProvider):
        providers.append(MockProvider())
    
    errors = {}
    for prov in providers:
        try:
            logger.info(f"Attempting to fetch metrics from {prov.name}")
            return await prov.get_financial_metrics(symbol, limit)
        except ProviderNotImplementedException as e:
            logger.warning(f"{prov.name} doesn't support metrics: {e.message}")
            errors[prov.name] = e.message
            continue
        except Exception as e:
            logger.error(f"{prov.name} failed: {str(e)}")
            errors[prov.name] = str(e)
            continue
    
    raise AllProvidersFailedException(
        feature="financial_metrics",
        attempted_providers=[p.name for p in providers],
        errors=errors
    )


async def get_peers_valuation(symbol: str, fallback: bool = False) -> List[str]:
    """
    Fetch list of peer companies.
    
    Args:
        symbol: Stock ticker symbol
        fallback: If True, try alternative providers on failure
        
    Returns:
        List of peer ticker symbols
    """
    provider = get_provider()
    
    if not fallback:
        return await provider.get_peers(symbol)
    
    # Multi-provider fallback mode
    providers = [provider, MockProvider()]
    
    errors = {}
    for prov in providers:
        try:
            logger.info(f"Attempting to fetch peers from {prov.name}")
            return await prov.get_peers(symbol)
        except ProviderNotImplementedException as e:
            logger.warning(f"{prov.name} doesn't support peers: {e.message}")
            errors[prov.name] = e.message
            continue
        except Exception as e:
            logger.error(f"{prov.name} failed: {str(e)}")
            errors[prov.name] = str(e)
            continue
    
    raise AllProvidersFailedException(
        feature="peer_comparison",
        attempted_providers=[p.name for p in providers],
        errors=errors
    )