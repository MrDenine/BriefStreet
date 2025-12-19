# app/core/dependencies.py
"""
Dependency Injection Factory สำหรับ Repositories

ตัดสินใจว่าจะใช้ repository implementation ไหนตาม environment config
"""

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings, RepositoryConfig, DatabaseType
from app.core.database import get_session

from app.repositories.base import ICacheRepository, IMarketDataRepository
from app.repositories.cache.sql_cache import SQLCacheRepository
from app.repositories.market_data.sql_market_data import SQLMarketDataRepository
from app.services.market_data_manager import MarketDataManager

from app.core.logging_config import get_logger

logger = get_logger(__name__)


# ======================
# Cache Repository Factory
# ======================

async def get_cache_repository(
    session: AsyncSession = Depends(get_session)
) -> AsyncGenerator[ICacheRepository, None]:
    """
    Factory สำหรับ Cache Repository
    
    Returns:
        ICacheRepository implementation ตาม config
    """
    
    config = RepositoryConfig.get("cache")
    
    logger.debug(f"Creating cache repository with {config.primary_db.value}")
    
    if config.primary_db in [DatabaseType.SQLITE, DatabaseType.POSTGRES]:
        yield SQLCacheRepository(session)
    else:
        raise ValueError(f"Unsupported database type for cache: {config.primary_db}")


# ======================
# Market Data Repository Factory
# ======================

async def get_market_data_repository(
    session: AsyncSession = Depends(get_session)
) -> AsyncGenerator[IMarketDataRepository, None]:
    """
    Factory สำหรับ Market Data Repository
    
    Returns:
        IMarketDataRepository implementation ตาม config
    """
    
    config = RepositoryConfig.get("market_data")
    
    logger.debug(f"Creating market_data repository with {config.primary_db.value}")
    
    if config.primary_db in [DatabaseType.SQLITE, DatabaseType.POSTGRES]:
        yield SQLMarketDataRepository(session)
    else:
        raise ValueError(f"Unsupported database type for market_data: {config.primary_db}")


# ======================
# Universal Repository Getter (Optional)
# ======================

def get_repository_factory(domain: str):
    """
    Universal repository factory getter
    
    Usage:
        cache_repo = Depends(get_repository_factory("cache"))
    
    Args:
        domain: ชื่อ domain (cache, market_data, etc.)
    
    Returns:
        Factory function สำหรับ domain นั้น
    """
    
    factories = {
        "cache": get_cache_repository,
        "market_data": get_market_data_repository,
    }
    
    if domain not in factories:
        raise ValueError(f"Unknown domain: {domain}")
    
    return factories[domain]


# ======================
# Market Data Manager (Orchestrator)
# ======================

async def get_market_data_manager(
    market_data_repo: IMarketDataRepository = Depends(get_market_data_repository)
) -> MarketDataManager:
    """
    Factory สำหรับ Market Data Manager (Orchestrator Service)
    
    Usage in endpoint:
        manager: MarketDataManager = Depends(get_market_data_manager)
        result = await manager.sync_transcript("AAPL", 3, 2024)
    
    Returns:
        MarketDataManager instance with injected dependencies
    """
    return MarketDataManager(market_data_repo)
