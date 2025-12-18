# tests/test_dependencies.py
"""
Unit tests สำหรับ Dependency Injection (Repository Factories)

ทดสอบ:
- get_cache_repository factory
- get_market_data_repository factory
- Repository creation ตาม environment
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.core.dependencies import (
    get_cache_repository,
    get_market_data_repository,
    get_repository_factory
)
from app.core.config import RepositoryConfig, DatabaseType
from app.repositories.base import ICacheRepository, IMarketDataRepository
from app.repositories.cache.sql_cache import SQLCacheRepository
from app.repositories.market_data.sql_market_data import SQLMarketDataRepository


# ======================
# Cache Repository Factory Tests
# ======================

@pytest.mark.asyncio
async def test_get_cache_repository_sqlite(test_session):
    """ทดสอบ factory สร้าง SQLite cache repository"""
    
    # Initialize config สำหรับ development (SQLite)
    RepositoryConfig.initialize("development")
    
    # Get repository จาก factory
    async for repo in get_cache_repository(test_session):
        assert isinstance(repo, SQLCacheRepository)
        assert isinstance(repo, ICacheRepository)
        break


@pytest.mark.asyncio
async def test_get_cache_repository_postgres(test_session):
    """ทดสอบ factory สร้าง PostgreSQL cache repository"""
    
    # Initialize config สำหรับ UAT (PostgreSQL)
    RepositoryConfig.initialize("uat")
    
    # Get repository จาก factory
    async for repo in get_cache_repository(test_session):
        # ยังคงเป็น SQLCacheRepository เพราะรองรับทั้ง SQLite และ Postgres
        assert isinstance(repo, SQLCacheRepository)
        break


@pytest.mark.asyncio
async def test_cache_repository_factory_with_operations(test_session):
    """ทดสอบ repository จาก factory สามารถทำงานได้จริง"""
    
    RepositoryConfig.initialize("development")
    
    async for repo in get_cache_repository(test_session):
        # Save
        await repo.save("FACTORY_TEST", "2024-10-25", {"test": "data"})
        
        # Get
        result = await repo.get("FACTORY_TEST", "2024-10-25")
        
        assert result is not None
        assert result["symbol"] == "FACTORY_TEST"
        break


# ======================
# Market Data Repository Factory Tests
# ======================

@pytest.mark.asyncio
async def test_get_market_data_repository_sqlite(test_session):
    """ทดสอบ factory สร้าง SQLite market data repository"""
    
    RepositoryConfig.initialize("development")
    
    async for repo in get_market_data_repository(test_session):
        assert isinstance(repo, SQLMarketDataRepository)
        assert isinstance(repo, IMarketDataRepository)
        break


@pytest.mark.asyncio
async def test_get_market_data_repository_postgres(test_session):
    """ทดสอบ factory สร้าง PostgreSQL market data repository"""
    
    RepositoryConfig.initialize("uat")
    
    async for repo in get_market_data_repository(test_session):
        assert isinstance(repo, SQLMarketDataRepository)
        break


@pytest.mark.asyncio
async def test_market_data_repository_factory_with_operations(test_session):
    """ทดสอบ market data repository จาก factory"""
    
    RepositoryConfig.initialize("development")
    
    async for repo in get_market_data_repository(test_session):
        # Save transcript
        success = await repo.save_transcript(
            "FACTORY_TEST",
            "2024-10-25",
            "Test transcript content"
        )
        
        assert success is True
        
        # Get transcript
        result = await repo.get_transcript("FACTORY_TEST", "2024-10-25")
        
        assert result is not None
        assert result["symbol"] == "FACTORY_TEST"
        break


# ======================
# Universal Factory Tests
# ======================

def test_get_repository_factory_cache():
    """ทดสอบ universal factory สำหรับ cache domain"""
    
    factory = get_repository_factory("cache")
    
    assert factory == get_cache_repository


def test_get_repository_factory_market_data():
    """ทดสอบ universal factory สำหรับ market_data domain"""
    
    factory = get_repository_factory("market_data")
    
    assert factory == get_market_data_repository


def test_get_repository_factory_invalid_domain():
    """ทดสอบ universal factory กับ domain ที่ไม่มี"""
    
    with pytest.raises(ValueError, match="Unknown domain"):
        get_repository_factory("invalid_domain")


# ======================
# Integration Tests
# ======================

@pytest.mark.asyncio
async def test_multiple_repositories_from_factory(test_session):
    """ทดสอบสร้างหลาย repository พร้อมกัน"""
    
    RepositoryConfig.initialize("development")
    
    # Get cache repository
    async for cache_repo in get_cache_repository(test_session):
        # Get market data repository
        async for market_data_repo in get_market_data_repository(test_session):
            # ใช้ทั้งสอง repository
            await cache_repo.save("MULTI", "2024-10-25", {"score": 90})
            await market_data_repo.save_transcript("MULTI", "2024-10-25", "Content")
            
            # Verify
            cache_result = await cache_repo.get("MULTI", "2024-10-25")
            transcript_result = await market_data_repo.get_transcript("MULTI", "2024-10-25")
            
            assert cache_result is not None
            assert transcript_result is not None
            break
        break


@pytest.mark.asyncio
async def test_repository_isolation(test_session):
    """ทดสอบว่า repository แต่ละ domain แยกกัน"""
    
    RepositoryConfig.initialize("development")
    
    async for cache_repo in get_cache_repository(test_session):
        async for market_data_repo in get_market_data_repository(test_session):
            # Save data ใน cache
            await cache_repo.save("ISOLATED", "2024-10-25", {"cache": "data"})
            
            # ไม่ควรเห็นใน market_data
            transcript = await market_data_repo.get_transcript("ISOLATED", "2024-10-25")
            
            # ควร None เพราะยังไม่ได้ save transcript
            assert transcript is None
            break
        break


@pytest.mark.asyncio
async def test_factory_respects_environment_config(test_session):
    """ทดสอบว่า factory สร้าง repository ตาม environment config"""
    
    # Development: SQLite
    RepositoryConfig.initialize("development")
    async for repo_dev in get_cache_repository(test_session):
        config_dev = RepositoryConfig.get("cache")
        assert config_dev.primary_db == DatabaseType.SQLITE
        break
    
    # UAT: PostgreSQL
    RepositoryConfig.initialize("uat")
    async for repo_uat in get_cache_repository(test_session):
        config_uat = RepositoryConfig.get("cache")
        assert config_uat.primary_db == DatabaseType.POSTGRES
        break


# ======================
# Error Handling Tests
# ======================

@pytest.mark.asyncio
async def test_factory_with_unsupported_database():
    """ทดสอบ factory กับ database type ที่ไม่รองรับ"""
    
    # Mock config ให้คืน unsupported DB type
    with patch("app.core.dependencies.RepositoryConfig.get") as mock_get:
        from app.core.config import DomainConfig, RepositoryStrategy, DatabaseType
        
        # Mock ให้คืน FIREBASE (ยังไม่รองรับ)
        mock_config = DomainConfig(
            strategy=RepositoryStrategy.PRIMARY,
            primary_db=DatabaseType.FIREBASE
        )
        mock_get.return_value = mock_config
        
        # Mock session
        mock_session = AsyncMock()
        
        # ควร raise ValueError
        with pytest.raises(ValueError, match="Unsupported database type"):
            async for repo in get_cache_repository(mock_session):
                pass
