"""
Mean Reversion Strategy

Strategy Logic:
- Buy when price deviates significantly below moving average
- Assumes price will revert back to the mean
"""

import pandas as pd
import pandas_ta as ta
from app.strategies.base_strategy import BaseStrategy, StrategyConfig


class MeanReversionStrategy(BaseStrategy):
    """
    Mean Reversion Strategy using Bollinger Bands
    
    Entry Conditions:
    1. Price crosses below lower Bollinger Band
    2. RSI < oversold threshold (confirmation)
    
    Exit: After holding_days or when price reaches mean/upper band
    """
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands and RSI"""
        bb_length = self.config.parameters.get("bb_length", 20)
        bb_std = self.config.parameters.get("bb_std", 2.0)
        rsi_length = self.config.parameters.get("rsi_length", 14)
        
        # Bollinger Bands
        bbands = ta.bbands(df['close'], length=bb_length, std=bb_std)
        df['BB_UPPER'] = bbands[f'BBU_{bb_length}_{bb_std}']
        df['BB_MIDDLE'] = bbands[f'BBM_{bb_length}_{bb_std}']
        df['BB_LOWER'] = bbands[f'BBL_{bb_length}_{bb_std}']
        
        # RSI for confirmation
        df['RSI'] = ta.rsi(df['close'], length=rsi_length)
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate buy signals when price overshoots to downside"""
        rsi_threshold = self.config.parameters.get("rsi_threshold", 30)
        
        # Buy Signal: Price below lower BB + RSI oversold
        df['Signal'] = (df['close'] < df['BB_LOWER']) & (df['RSI'] < rsi_threshold)
        
        return df
    
    @classmethod
    def get_default_config(cls) -> StrategyConfig:
        """Default configuration for Mean Reversion strategy"""
        return StrategyConfig(
            name="mean_reversion",
            holding_days=5,
            stop_loss_pct=3.0,
            take_profit_pct=8.0,
            parameters={
                "bb_length": 20,        # Bollinger Bands period
                "bb_std": 2.0,          # Standard deviation multiplier
                "rsi_length": 14,       # RSI period
                "rsi_threshold": 30     # RSI oversold threshold
            }
        )
