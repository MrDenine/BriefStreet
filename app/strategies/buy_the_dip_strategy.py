"""
Buy The Dip Strategy

Strategy Logic:
- Buy when price is in uptrend (above EMA) but RSI shows oversold condition
- This captures pullbacks in a trending market
"""

import pandas as pd
import pandas_ta as ta
from app.strategies.base_strategy import BaseStrategy, StrategyConfig


class BuyTheDipStrategy(BaseStrategy):
    """
    Trend Following + Pullback Strategy
    
    Entry Conditions:
    1. Price > EMA (Uptrend confirmation)
    2. RSI < threshold (Oversold pullback)
    
    Exit: After holding_days or when stop_loss/take_profit hit
    """
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate EMA and RSI indicators"""
        ema_length = self.config.parameters.get("ema_length", 200)
        rsi_length = self.config.parameters.get("rsi_length", 14)
        
        df['EMA'] = ta.ema(df['close'], length=ema_length)
        df['RSI'] = ta.rsi(df['close'], length=rsi_length)
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate buy signals for dip buying opportunities"""
        rsi_threshold = self.config.parameters.get("rsi_threshold", 35)
        
        # Condition 1: Trend is UP
        uptrend = df['close'] > df['EMA']
        
        # Condition 2: RSI just Crossed Below Threshold (ไม่เอาแช่)
        # วิธีเช็ค: วันนี้ RSI < 35 แต่เมื่อวาน RSI >= 35
        # shift(1) คือดึงค่าก่อนหน้ามาเทียบ
        rsi_cross_under = (df['RSI'] < rsi_threshold) & (df['RSI'].shift(1) >= rsi_threshold)
        
        # Final Signal
        df['Signal'] = uptrend & rsi_cross_under
        
        return df
    
    @classmethod
    def get_default_config(cls) -> StrategyConfig:
        """Default configuration for Buy The Dip strategy"""
        return StrategyConfig(
            name="buy_the_dip",
            holding_days=5,
            stop_loss_pct=5.0,
            take_profit_pct=10.0,
            parameters={
                "ema_length": 200,      # EMA period for trend detection
                "rsi_length": 14,       # RSI period
                "rsi_threshold": 35     # RSI oversold threshold
            }
        )
