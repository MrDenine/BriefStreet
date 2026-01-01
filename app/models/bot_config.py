# app/models/bot_config.py

from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import DateTime, SQLModel, Field, Column, JSON
from sqlalchemy.sql import func

class BotConfig(SQLModel, table=True):
    __tablename__ = "bot_configs"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    symbol: str = Field(index=True, unique=True)
    strategy_name: str
    
    # ใช้ Column(JSON) เพื่อเก็บค่า Config ที่ยืดหยุ่น
    parameters: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    
    is_active: bool = Field(default=False)
    
    last_action: Optional[str] = Field(default=None)
    last_trade_time: Optional[datetime] = Field(default=None)
    
    # Field ที่ใช้ func.now() ของ SQLAlchemy
    updated_at: Optional[datetime] = Field(
        default=None, 
        sa_column_kwargs={"onupdate": func.now()}
    )
    created_at: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )