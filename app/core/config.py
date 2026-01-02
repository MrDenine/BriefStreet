import os
from pathlib import Path
from typing import Literal, Dict
from enum import Enum
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get project root directory (3 levels up: config.py -> core -> app -> BriefStreet)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DOTENV = BASE_DIR / ".env"


# ======================
# Repository Configuration Classes
# ======================

class DatabaseType(str, Enum):
    """ประเภทของ database ที่รองรับ"""
    SQLITE = "sqlite"
    POSTGRES = "postgres"
    FIREBASE = "firebase"
    REDIS = "redis"
    MOCK = "mock"


class RepositoryStrategy(str, Enum):
    """กลยุทธ์การใช้งาน database"""
    PRIMARY = "primary"                    # ใช้ DB เดียว
    DUAL_WRITE = "dual_write"             # เขียนทั้งสอง DB
    READ_WRITE_SPLIT = "read_write_split" # อ่านจาก A เขียนไป B
    FALLBACK = "fallback"                  # ลอง A ก่อน ไม่ได้ลอง B


class DomainConfig(BaseModel):
    """การตั้งค่าสำหรับแต่ละ domain"""
    strategy: RepositoryStrategy
    primary_db: DatabaseType
    secondary_db: DatabaseType | None = None
    sync_enabled: bool = False
    cache_ttl: int = 3600  # seconds


# ======================
# Main Settings
# ======================

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(DOTENV),  # Convert Path to string
        extra="ignore"
    )
    
    PROJECT_NAME: str = "BriefStreet"
    
    # ======================
    # Environment Configuration
    # ======================
    ENVIRONMENT: Literal["development", "uat", "staging", "production"] = "development"
    DEBUG: bool = True

    # ======================
    # API Keys
    # ======================
    OPENAI_API_KEY: str
    FMP_API_KEY: str
    
    # ======================
    # Trading Bot Configuration
    # ======================
    # Binance API Keys (Optional - for live trading)
    BINANCE_API_KEY: str = ""
    BINANCE_SECRET_KEY: str = ""
    
    # Bot Scheduler Settings
    BOT_INTERVAL_MINUTES: int = 1  # รันทุกกี่นาที
    
    # ======================
    # Database Configuration
    # ======================
    
    # PostgreSQL Settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "briefstreet"
    
    @property
    def POSTGRES_DATABASE_URL(self) -> str:
        """PostgreSQL connection string"""
        # แยก database ตาม environment
        db_name = f"{self.POSTGRES_DB}_{self.ENVIRONMENT}" if self.ENVIRONMENT != "production" else self.POSTGRES_DB
        
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{db_name}"
        )
    
    @property
    def SQLITE_DATABASE_URL(self) -> str:
        """SQLite connection string"""
        db_path = self.DATA_DIR / f"cache_{self.ENVIRONMENT}.db"
        return f"sqlite+aiosqlite:///{db_path}"
    
    # ======================
    # Data Provider
    # ======================
    # Options: 'fmp', 'yfinance', 'mock'
    DATA_PROVIDER: str = "fmp"
    
    # ======================
    # LLM Configuration
    # ======================
    # Model selection
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_CHAT_MODEL: str = "gpt-4o-mini"
    LLM_CONSISTENCY_MODEL: str = "gpt-4o-mini"
    
    # Transcript text limits (characters)
    LLM_TRANSCRIPT_MAX_LENGTH_ANALYSIS: int = 15000
    LLM_TRANSCRIPT_MAX_LENGTH_CHAT: int = 25000
    LLM_TRANSCRIPT_MAX_LENGTH_CONSISTENCY_PREPARED: int = 10000
    LLM_TRANSCRIPT_MAX_LENGTH_CONSISTENCY_QA: int = 10000
    
    # Retry configuration
    LLM_MAX_RETRIES: int = 2
    LLM_RETRY_DELAY: float = 2.0
    
    # Default messages
    LLM_DEFAULT_NOT_FOUND_MESSAGE: str = "ข้อมูลนี้ไม่ได้ถูกพูดถึงในการประชุมครั้งนี้ครับ"
    
    # System prompts
    LLM_SYSTEM_PROMPT_ANALYSIS: str = "You are a helpful financial assistant. Respond in JSON format only."
    LLM_SYSTEM_PROMPT_CHAT: str = "You are a helpful financial assistant."
    LLM_SYSTEM_PROMPT_CONSISTENCY: str = "You are a cynical financial auditor looking for inconsistencies. Respond in JSON."
    
    # ======================
    # Valuation Configuration
    # ======================
    # DCF Parameters
    VALUATION_DCF_GROWTH_RATE: float = 0.05  # 5%
    VALUATION_DCF_DISCOUNT_RATE: float = 0.10  # 10%
    VALUATION_DCF_TERMINAL_GROWTH: float = 0.02  # 2%
    VALUATION_DCF_PROJECTION_YEARS: int = 5
    
    # Graham Number
    VALUATION_GRAHAM_MULTIPLIER: float = 22.5
    
    # Default peer comparison values (fallback when API unavailable)
    VALUATION_DEFAULT_PEER_PE: float = 25.0
    VALUATION_DEFAULT_SECTOR_PBV: float = 4.5
    
    # ======================
    # Data Provider Settings
    # ======================
    # FMP (Financial Modeling Prep)
    FMP_BASE_URL: str = "https://financialmodelingprep.com/stable"
    FMP_TIMEOUT: float = 30.0
    FMP_MAX_RETRIES: int = 3
    FMP_RETRY_DELAY: float = 1.0
    FMP_RATE_LIMIT_RETRY_AFTER: int = 60
    
    # YFinance
    YFINANCE_TIMEOUT: float = 30.0
    
    # ======================
    # Default Query Parameters
    # ======================
    DEFAULT_QUARTER: int = 3
    DEFAULT_YEAR: int = 2024
    DEFAULT_FINANCIAL_HISTORY_LIMIT: int = 5
    DEFAULT_PEERS_LIMIT: int = 5
    
    # ======================
    # Cache Configuration
    # ======================
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 86400  # 24 hours in seconds
    
    # ======================
    # Feature Flags
    # ======================
    ENABLE_CONSISTENCY_ANALYSIS: bool = True
    ENABLE_VALUATION: bool = True
    
    # ======================
    # Logging Configuration
    # ======================
    LOG_LEVEL: str = "INFO"
    LOG_MAX_QUESTION_LENGTH: int = 100

    # ======================
    # Paths
    # ======================
    
    @property
    def DATA_DIR(self) -> Path:
        """สร้างโฟลเดอร์ data แยกตาม environment"""
        d = BASE_DIR / "data" / self.ENVIRONMENT
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def DATABASE_URL(self) -> str:
        """
        Dynamic database URL ตาม environment
        
        - Development: SQLite
        - UAT/Production: PostgreSQL
        """
        if self.ENVIRONMENT == "development":
            return self.SQLITE_DATABASE_URL
        else:
            return self.POSTGRES_DATABASE_URL

settings = Settings()


# ======================
# Repository Configuration per Environment
# ======================

class BaseRepositoryConfig:
    """Base config - ใช้เมื่อไม่มี environment-specific config"""
    
    DOMAINS: Dict[str, DomainConfig] = {
        "cache": DomainConfig(
            strategy=RepositoryStrategy.PRIMARY,
            primary_db=DatabaseType.SQLITE,
            cache_ttl=3600
        ),
        "market_data": DomainConfig(
            strategy=RepositoryStrategy.PRIMARY,
            primary_db=DatabaseType.SQLITE
        ),
    }


class DevelopmentRepositoryConfig(BaseRepositoryConfig):
    """🛠️ Development: SQLite, cache TTL สั้น"""
    
    DOMAINS: Dict[str, DomainConfig] = {
        "cache": DomainConfig(
            strategy=RepositoryStrategy.PRIMARY,
            primary_db=DatabaseType.SQLITE,
            cache_ttl=300  # 5 minutes
        ),
        "market_data": DomainConfig(
            strategy=RepositoryStrategy.PRIMARY,
            primary_db=DatabaseType.SQLITE
        ),
    }


class UATRepositoryConfig(BaseRepositoryConfig):
    """🧪 UAT: PostgreSQL เป็นหลัก"""
    
    DOMAINS: Dict[str, DomainConfig] = {
        "cache": DomainConfig(
            strategy=RepositoryStrategy.PRIMARY,
            primary_db=DatabaseType.POSTGRES,
            cache_ttl=3600  # 1 hour
        ),
        "market_data": DomainConfig(
            strategy=RepositoryStrategy.PRIMARY,
            primary_db=DatabaseType.POSTGRES
        ),
    }


class ProductionRepositoryConfig(BaseRepositoryConfig):
    """🚀 Production: PostgreSQL, cache TTL ยาว"""
    
    DOMAINS: Dict[str, DomainConfig] = {
        "cache": DomainConfig(
            strategy=RepositoryStrategy.PRIMARY,
            primary_db=DatabaseType.POSTGRES,
            cache_ttl=86400  # 24 hours
        ),
        "market_data": DomainConfig(
            strategy=RepositoryStrategy.PRIMARY,
            primary_db=DatabaseType.POSTGRES
        ),
    }


def get_repository_config(environment: str = "development") -> BaseRepositoryConfig:
    """Load repository config based on environment"""
    config_map = {
        "development": DevelopmentRepositoryConfig,
        "uat": UATRepositoryConfig,
        "staging": ProductionRepositoryConfig,
        "production": ProductionRepositoryConfig,
    }
    
    config_class = config_map.get(environment, BaseRepositoryConfig)
    return config_class()


class RepositoryConfig:
    """Wrapper class สำหรับเข้าถึง repository config"""
    
    _config: BaseRepositoryConfig = None
    
    @classmethod
    def initialize(cls, environment: str):
        """Initialize config ด้วย environment"""
        cls._config = get_repository_config(environment)
    
    @classmethod
    def get(cls, domain: str) -> DomainConfig:
        """Get domain config for current environment"""
        if cls._config is None:
            cls.initialize(settings.ENVIRONMENT)
        
        if domain not in cls._config.DOMAINS:
            raise ValueError(f"Unknown domain: {domain}")
        
        return cls._config.DOMAINS[domain]
    
    @classmethod
    def get_all(cls) -> Dict[str, DomainConfig]:
        """Get all domain configs"""
        if cls._config is None:
            cls.initialize(settings.ENVIRONMENT)
        
        return cls._config.DOMAINS