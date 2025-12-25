import pandas as pd
import pandas_ta as ta
from typing import List
from app.models.market_data import TechnicalAnalysisResult, BacktestResult
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

    async def backtest(self, symbol: str, days: int = 365) -> dict:
        """
        จำลองการเทรดด้วยกลยุทธ์ Trend Following + Pullback
        """
        # 1. เตรียมข้อมูล (Data)
        candles = await self.data_provider.get_historical_prices(symbol, interval="1d", limit=days + 50) # เผื่อวันสำหรับ EMA
        if not candles:
            return {"error": "No data"}

        df = pd.DataFrame([c.model_dump() for c in candles])
        df.set_index('timestamp', inplace=True)

        # 2. คำนวณ Indicator ทั้งตาราง (Vectorization)
        df['EMA_200'] = ta.ema(df['close'], length=200)
        df['RSI'] = ta.rsi(df['close'], length=14)

        # 3. สร้างสัญญาณเข้าซื้อ (Entry Logic)
        # เงื่อนไข: เป็นขาขึ้น (ราคา > EMA) และ ย่อตัว (RSI < 35)
        df['Signal'] = (df['close'] > df['EMA_200']) & (df['RSI'] < 35)

        # 4. จำลองการเทรด (Simulation Loop)
        trades = []
        holding_days = 5  # กติกา: ถือ 5 วันแล้วขาย
        
        # ดึงเฉพาะวันที่เกิดสัญญาณ (ที่เป็น True)
        entry_dates = df[df['Signal']].index

        for entry_date in entry_dates:
            try:
                # หาตำแหน่ง Index ของวันเข้า
                idx = df.index.get_loc(entry_date)
                
                # เช็คว่ามีข้อมูลในอนาคตพอให้ขายไหม
                if idx + holding_days >= len(df):
                    continue
                
                # ราคาเข้า (Buy) และ ราคาออก (Sell)
                entry_price = df.iloc[idx]['close']
                exit_price = df.iloc[idx + holding_days]['close']
                exit_date = df.index[idx + holding_days]

                # คำนวณกำไร %
                pnl = (exit_price - entry_price) / entry_price * 100
                
                trades.append({
                    "entry_date": entry_date,
                    "entry_price": entry_price,
                    "exit_date": exit_date,
                    "exit_price": exit_price,
                    "pnl_percent": pnl,
                    "win": pnl > 0
                })
            except Exception:
                continue

        # 5. สรุปผล (Metrics)
        if not trades:
            return {"symbol": symbol, "total_trades": 0, "message": "No trades found"}

        df_trades = pd.DataFrame(trades)
        
        return {
            "symbol": symbol,
            "period_days": days,
            "total_trades": len(trades),
            "win_rate": round((df_trades['win'].sum() / len(trades)) * 100, 2),
            "avg_return": round(df_trades['pnl_percent'].mean(), 2),
            "best_trade": round(df_trades['pnl_percent'].max(), 2),
            "worst_trade": round(df_trades['pnl_percent'].min(), 2),
            # ส่งรายการเทรดล่าสุดไปแสดงผล 5 รายการ
            "recent_trades": trades[-5:] 
        }
    
