# tests/test_config.py
"""
Unit tests สำหรับ Configuration และ Repository Config

ทดสอบ:
- Environment-based configuration
- Repository config per environment
- Database URL generation
"""

import pytest
import os
from pathlib import Path

from app.core.config import (
    settings,
    RepositoryConfig,
    DatabaseType,
    RepositoryStrategy,
    DevelopmentRepositoryConfig,
    UATRepositoryConfig,
    ProductionRepositoryConfig
)


# ======================
# Settings Tests
# ======================

def test_settings_default_environment():
    """ทดสอบ default environment"""
    assert settings.ENVIRONMENT in ["development", "uat", "staging", "production"]


def test_settings_database_url_development():
    """ทดสอบ DATABASE_URL สำหรับ development"""
    # Assume dev environment
    if settings.ENVIRONMENT == "development":
        assert "sqlite" in settings.DATABASE_URL.lower()
        assert "aiosqlite" in settings.DATABASE_URL


def test_settings_postgres_url_format():
    """ทดสอบ POSTGRES_DATABASE_URL format"""
    url = settings.POSTGRES_DATABASE_URL
    
    assert url.startswith("postgresql+asyncpg://")
    assert settings.POSTGRES_USER in url
    assert str(settings.POSTGRES_PORT) in url


def test_settings_sqlite_url_format():
    """ทดสอบ SQLITE_DATABASE_URL format"""
    url = settings.SQLITE_DATABASE_URL
    
    assert url.startswith("sqlite+aiosqlite:///")
    assert settings.ENVIRONMENT in url


def test_settings_data_dir_creation():
    """ทดสอบว่า DATA_DIR ถูกสร้างอัตโนมัติ"""
    data_dir = settings.DATA_DIR
    
    assert data_dir.exists()
    assert data_dir.is_dir()
    assert settings.ENVIRONMENT in str(data_dir)


# ======================
# Repository Config Tests
# ======================

def test_repository_config_initialization():
    """ทดสอบ initialize repository config"""
    RepositoryConfig.initialize("development")
    
    config = RepositoryConfig.get("cache")
    
    assert config is not None
    assert config.primary_db == DatabaseType.SQLITE


def test_repository_config_development():
    """ทดสอบ Development repository config"""
    config = DevelopmentRepositoryConfig()
    
    cache_config = config.DOMAINS["cache"]
    assert cache_config.primary_db == DatabaseType.SQLITE
    assert cache_config.strategy == RepositoryStrategy.PRIMARY
    assert cache_config.cache_ttl == 300  # 5 minutes
    
    market_data_config = config.DOMAINS["market_data"]
    assert market_data_config.primary_db == DatabaseType.SQLITE


def test_repository_config_uat():
    """ทดสอบ UAT repository config"""
    config = UATRepositoryConfig()
    
    cache_config = config.DOMAINS["cache"]
    assert cache_config.primary_db == DatabaseType.POSTGRES
    assert cache_config.strategy == RepositoryStrategy.PRIMARY
    assert cache_config.cache_ttl == 3600  # 1 hour
    
    market_data_config = config.DOMAINS["market_data"]
    assert market_data_config.primary_db == DatabaseType.POSTGRES


def test_repository_config_production():
    """ทดสอบ Production repository config"""
    config = ProductionRepositoryConfig()
    
    cache_config = config.DOMAINS["cache"]
    assert cache_config.primary_db == DatabaseType.POSTGRES
    assert cache_config.cache_ttl == 86400  # 24 hours


def test_repository_config_get_all():
    """ทดสอบ get_all domains"""
    RepositoryConfig.initialize("development")
    
    all_configs = RepositoryConfig.get_all()
    
    assert "cache" in all_configs
    assert "market_data" in all_configs
    assert len(all_configs) == 2


def test_repository_config_invalid_domain():
    """ทดสอบ get config ของ domain ที่ไม่มี"""
    RepositoryConfig.initialize("development")
    
    with pytest.raises(ValueError, match="Unknown domain"):
        RepositoryConfig.get("nonexistent_domain")


def test_repository_config_auto_initialize():
    """ทดสอบ auto-initialize ถ้ายังไม่ได้ initialize"""
    # Reset
    RepositoryConfig._config = None
    
    # Get จะ auto-initialize
    config = RepositoryConfig.get("cache")
    
    assert config is not None


# ======================
# Environment Switching Tests
# ======================

def test_config_per_environment():
    """ทดสอบ config แต่ละ environment"""
    
    # Development
    RepositoryConfig.initialize("development")
    dev_config = RepositoryConfig.get("cache")
    assert dev_config.primary_db == DatabaseType.SQLITE
    assert dev_config.cache_ttl == 300
    
    # UAT
    RepositoryConfig.initialize("uat")
    uat_config = RepositoryConfig.get("cache")
    assert uat_config.primary_db == DatabaseType.POSTGRES
    assert uat_config.cache_ttl == 3600
    
    # Production
    RepositoryConfig.initialize("production")
    prod_config = RepositoryConfig.get("cache")
    assert prod_config.primary_db == DatabaseType.POSTGRES
    assert prod_config.cache_ttl == 86400


def test_database_type_enum():
    """ทดสอบ DatabaseType enum"""
    assert DatabaseType.SQLITE.value == "sqlite"
    assert DatabaseType.POSTGRES.value == "postgres"
    assert DatabaseType.FIREBASE.value == "firebase"
    assert DatabaseType.REDIS.value == "redis"
    assert DatabaseType.MOCK.value == "mock"


def test_repository_strategy_enum():
    """ทดสอบ RepositoryStrategy enum"""
    assert RepositoryStrategy.PRIMARY.value == "primary"
    assert RepositoryStrategy.DUAL_WRITE.value == "dual_write"
    assert RepositoryStrategy.READ_WRITE_SPLIT.value == "read_write_split"
    assert RepositoryStrategy.FALLBACK.value == "fallback"


# ======================
# Domain Config Tests
# ======================

def test_domain_config_defaults():
    """ทดสอบ DomainConfig defaults"""
    from app.core.config import DomainConfig
    
    config = DomainConfig(
        strategy=RepositoryStrategy.PRIMARY,
        primary_db=DatabaseType.SQLITE
    )
    
    assert config.secondary_db is None
    assert config.sync_enabled is False
    assert config.cache_ttl == 3600


def test_domain_config_with_secondary():
    """ทดสอบ DomainConfig กับ secondary database"""
    from app.core.config import DomainConfig
    
    config = DomainConfig(
        strategy=RepositoryStrategy.DUAL_WRITE,
        primary_db=DatabaseType.POSTGRES,
        secondary_db=DatabaseType.FIREBASE,
        sync_enabled=True,
        cache_ttl=7200
    )
    
    assert config.strategy == RepositoryStrategy.DUAL_WRITE
    assert config.primary_db == DatabaseType.POSTGRES
    assert config.secondary_db == DatabaseType.FIREBASE
    assert config.sync_enabled is True
    assert config.cache_ttl == 7200
