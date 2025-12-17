import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get project root directory (3 levels up: config.py -> core -> app -> BriefStreet)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DOTENV = BASE_DIR / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(DOTENV),  # Convert Path to string
        extra="ignore"
    )
    
    PROJECT_NAME: str = "BriefStreet"

    # ======================
    # API Keys
    # ======================
    OPENAI_API_KEY: str
    FMP_API_KEY: str
    
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
    # BASE_DIR is already defined at module level
    # BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    @property
    def DATA_DIR(self) -> Path:
        """สฟลเดอร์ data อัตโนมัติถ้ายังไม่มี"""
        d = BASE_DIR / "data"
        d.mkdir(exist_ok=True)
        return d

    @property
    def DATABASE_URL(self) -> str:
        """สร้าง Connection String สำหรับ SQLite"""
        db_path = self.DATA_DIR / "cache.db"
        return f"sqlite+aiosqlite:///{db_path}"

settings = Settings()