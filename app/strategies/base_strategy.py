"""
Base Strategy Abstract Class

Defines the interface that all trading strategies must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel, Field
import pandas as pd


class StrategyConfig(BaseModel):
    """Configuration for strategy parameters"""
    name: str = Field(..., description="Strategy name")
    holding_days: int = Field(5, ge=1, le=365, description="Number of days to hold position")
    stop_loss_pct: float = Field(0.0, ge=0, le=100, description="Stop loss percentage (0 = disabled)")
    take_profit_pct: float = Field(0.0, ge=0, le=100, description="Take profit percentage (0 = disabled)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy-specific parameters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "buy_the_dip",
                "holding_days": 5,
                "stop_loss_pct": 5.0,
                "take_profit_pct": 10.0,
                "parameters": {
                    "rsi_threshold": 35,
                    "ema_length": 200
                }
            }
        }


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    All concrete strategies must implement:
    - calculate_indicators(): Add technical indicators to DataFrame
    - generate_signals(): Create buy/sell signals
    - get_default_config(): Return default strategy configuration
    """
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.name = config.name
    
    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate and add technical indicators to the DataFrame.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added indicator columns
        """
        pass
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate buy/sell signals based on strategy logic.
        
        Args:
            df: DataFrame with indicators already calculated
            
        Returns:
            DataFrame with 'Signal' column (True = Buy, False = Wait)
        """
        pass
    
    @classmethod
    @abstractmethod
    def get_default_config(cls) -> StrategyConfig:
        """
        Get default configuration for this strategy.
        
        Returns:
            StrategyConfig with default parameters
        """
        pass
    
    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data by calculating indicators and generating signals.
        
        Args:
            df: Raw OHLCV DataFrame
            
        Returns:
            DataFrame ready for backtesting (with NaN rows removed)
        """
        df = self.calculate_indicators(df)

        #Output DataFrame contains signals generated at Close, pending execution on Next Open
        df = self.generate_signals(df)
        
        # Drop rows with NaN values (from indicator warm-up period)
        # This is essential for strategies with long-period indicators like EMA(200)
        df = df.dropna()
        
        return df
    
    def check_exit_conditions(
        self, 
        entry_price: float, 
        current_close: float,
        current_low: float = None,  # เพิ่ม Low เพื่อเช็ค SL
        current_high: float = None  # เพิ่ม High เพื่อเช็ค TP
    ) -> tuple[bool, str]:
        """
        Check if stop loss or take profit conditions are met.
        
        Args:
            entry_price: Price at entry
            current_price: Current price
            
        Returns:
            Tuple of (should_exit: bool, reason: str)
        """
        # ถ้าไม่มี Low/High ให้ใช้ Close แทน (Fallback)
        if current_low is None: current_low = current_close
        if current_high is None: current_high = current_close

        # 1. เช็ค Stop Loss จาก Low (กรณีแย่สุดในแท่งนั้น)
        if self.config.stop_loss_pct > 0:
            sl_price = entry_price * (1 - self.config.stop_loss_pct / 100)
            if current_low <= sl_price:
                return True, "STOP_LOSS"

        # 2. เช็ค Take Profit จาก High (กรณีดีสุดในแท่งนั้น)
        if self.config.take_profit_pct > 0:
            tp_price = entry_price * (1 + self.config.take_profit_pct / 100)
            if current_high >= tp_price:
                return True, "TAKE_PROFIT"
        
        # หมายเหตุ: ใน Backtest ขั้นสูง ต้องระวังกรณีที่แท่งเดียวชนทั้ง High และ Low 
        # (ต้องดู Open ว่าวิ่งไปทางไหนก่อน แต่เบื้องต้นเอาแค่นี้ก็ดีขึ้นมากแล้วครับ)
        
        return False, "HOLDING"
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get information about this strategy.
        
        Returns:
            Dictionary with strategy information
        """
        return {
            "name": self.name,
            "holding_days": self.config.holding_days,
            "stop_loss_pct": self.config.stop_loss_pct,
            "take_profit_pct": self.config.take_profit_pct,
            "parameters": self.config.parameters
        }
