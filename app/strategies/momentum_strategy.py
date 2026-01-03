"""
Momentum Strategy

Strategy Logic:
- Buy when price shows strong upward momentum
- Ride the trend using momentum indicators
"""

import pandas as pd
import pandas_ta as ta
from app.strategies.base_strategy import BaseStrategy, StrategyConfig


class MomentumStrategy(BaseStrategy):
    """
    Momentum/Trend Following Strategy
    
    Entry Conditions:
    1. Short EMA crosses above Long EMA (Golden Cross)
    2. RSI > threshold (Strong momentum confirmation)
    3. ADX > threshold (Trend strength confirmation)
    
    Exit: After holding_days or when momentum weakens
    """
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate momentum indicators: EMA crossover, RSI, ADX"""
        short_ema = self.config.parameters.get("short_ema", 12)
        long_ema = self.config.parameters.get("long_ema", 26)
        rsi_length = self.config.parameters.get("rsi_length", 14)
        adx_length = self.config.parameters.get("adx_length", 14)
        
        # EMA crossover
        df['EMA_SHORT'] = ta.ema(df['close'], length=short_ema)
        df['EMA_LONG'] = ta.ema(df['close'], length=long_ema)
        
        # RSI for momentum confirmation
        df['RSI'] = ta.rsi(df['close'], length=rsi_length)
        
        # ADX for trend strength
        adx_result = ta.adx(df['high'], df['low'], df['close'], length=adx_length)
        df['ADX'] = adx_result[f'ADX_{adx_length}']
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate buy signals on strong momentum"""
        rsi_threshold = self.config.parameters.get("rsi_threshold", 50)
        adx_threshold = self.config.parameters.get("adx_threshold", 25)
        
        # Buy Signal: 
        # 1. Golden Cross (short EMA > long EMA)
        # 2. Strong momentum (RSI > threshold)
        # 3. Strong trend (ADX > threshold)
        df['Signal'] = (
            (df['EMA_SHORT'] > df['EMA_LONG']) & 
            (df['RSI'] > rsi_threshold) & 
            (df['ADX'] > adx_threshold)
        )
        
        return df
    
    @classmethod
    def get_default_config(cls) -> StrategyConfig:
        """Default configuration for Momentum strategy"""
        return StrategyConfig(
            name="momentum",
            holding_days=10,
            stop_loss_pct=5.0,
            take_profit_pct=15.0,
            parameters={
                "short_ema": 12,        # Short EMA period
                "long_ema": 26,         # Long EMA period
                "rsi_length": 14,       # RSI period
                "rsi_threshold": 50,    # RSI bullish threshold
                "adx_length": 14,       # ADX period
                "adx_threshold": 25     # ADX trend strength threshold
            }
        )
