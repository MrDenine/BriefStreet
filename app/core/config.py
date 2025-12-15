import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )
    
    PROJECT_NAME: str = "BriefStreet API"

    OPENAI_API_KEY: str
    FMP_API_KEY: str

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    @property
    def DATA_DIR(self) -> Path:
        """สร้างโฟลเดอร์ data อัตโนมัติถ้ายังไม่มี"""
        d = self.BASE_DIR / "data"
        d.mkdir(exist_ok=True)
        return d

    @property
    def DATABASE_URL(self) -> str:
        """สร้าง Connection String สำหรับ SQLite"""
        db_path = self.DATA_DIR / "cache.db"
        return f"sqlite+aiosqlite:///{db_path}"

settings = Settings()