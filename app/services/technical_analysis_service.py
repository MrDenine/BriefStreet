import pandas as pd
import pandas_ta as ta
from typing import List
from app.models.market_data import TechnicalAnalysisResult
from app.data_sources.base import DataSourceProvider

class TechnicalAnalysisService:
    def __init__(self, data_provider: DataSourceProvider):
        self.data_provider = data_provider

    async def analyze(self, symbol: str) -> TechnicalAnalysisResult:
        candles = await self.data_provider.get_historical_prices(symbol, interval="1d", limit=300)

        if not candles:
            raise ValueError(f"No historical data found for {symbol}")
        
        df = pd.DataFrame([c.dict() for c in candles])
        df.set_index('timestamp', inplace=True)

        # Trend: EMA 200
        df['EMA_200'] = ta.ema(df['close'], length=200)
        # Momentum: RSI 14
        df['RSI'] = ta.rsi(df['close'], length=14)

        # Determine Current State (Last Candle)
        current = df.iloc[-1]
        prev = df.iloc[-2]

        # --- Logic: Trend Determination ---
        trend = "SIDEWAY"
        if current['close'] > current['EMA_200']:
            trend = "UPTREND"
        elif current['close'] < current['EMA_200']:
            trend = "DOWNTREND"

        # --- Logic: Signal Generation (Tier 1 & 2 Strategy) ---
        signal = "WAIT"
        
        # Strategy: Buy the Dip in Uptrend
        if trend == "UPTREND" and current['RSI'] < 35:
            signal = "BUY_DIP"
        
        # Strategy: Sell Rally in Downtrend
        elif trend == "DOWNTREND" and current['RSI'] > 65:
            signal = "SELL_RALLY"

        # --- Logic: Simple Support/Resistance (Local Min/Max 20 days) ---
        recent_low = df['low'].tail(20).min()
        recent_high = df['high'].tail(20).max()

        return TechnicalAnalysisResult(
            symbol=symbol,
            current_price=current['close'],
            trend=trend,
            rsi=round(current['RSI'], 2),
            signal=signal,
            support_levels=[recent_low], 
            resistance_levels=[recent_high]
        )