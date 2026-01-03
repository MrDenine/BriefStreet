import pandas as pd
import pandas_ta as ta
from app.strategies.base_strategy import BaseStrategy, StrategyConfig

class BuyTheDipStrategy(BaseStrategy):
    """
    Advanced Buy The Dip Strategy
    
    Improvements:
    1. Dynamic RSI Entry: ปรับเกณฑ์เข้าซื้อตามความแรงของเทรนด์ (เทรนด์แรง ยอมซื้อแพงได้)
    2. Step Trailing Stop: ขยับจุด Stop Loss ขึ้นตามราคา เพื่อรันกำไร (Run Trend)
    """
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate EMA and RSI indicators"""
        ema_length = self.config.parameters.get("ema_length", 200)
        rsi_length = self.config.parameters.get("rsi_length", 14)
        
        # ใช้ EMA เพื่อดูเทรนด์หลัก
        df['EMA'] = ta.ema(df['close'], length=ema_length)
        # ใช้ RSI เพื่อดูจังหวะย่อตัว
        df['RSI'] = ta.rsi(df['close'], length=rsi_length)
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate signals with Dynamic RSI Threshold
        """
        base_threshold = self.config.parameters.get("rsi_threshold", 35)
        
        # 1. วัดความแข็งแกร่งของเทรนด์ (Trend Strength)
        # คำนวณว่าราคาอยู่เหนือ EMA กี่ %
        trend_strength = (df['close'] - df['EMA']) / df['EMA']
        
        # 2. กำหนด Dynamic Threshold
        # สร้าง Series ใหม่ที่มีค่าเท่ากับ base_threshold (35)
        dynamic_threshold = pd.Series(base_threshold, index=df.index)
        
        # Logic: ถ้าเทรนด์กระทิงดุมาก ราคาจะไม่ย่อลึก เราต้องยอมเข้าที่ RSI สูงขึ้น
        # - ถ้าเทรนด์แรงปานกลาง (> 1% เหนือ EMA) ขยับเกณฑ์เป็น 45
        dynamic_threshold[trend_strength > 0.01] = 45
        # - ถ้าเทรนด์แรงมาก (> 3% เหนือ EMA) ขยับเกณฑ์เป็น 55
        dynamic_threshold[trend_strength > 0.03] = 55
        
        # Condition 1: ต้องเป็นขาขึ้น (ราคา > EMA)
        uptrend = df['close'] > df['EMA']
        
        # Condition 2: RSI ตัดลงต่ำกว่า Dynamic Threshold
        # (ใช้วิธีเช็คการตัดลง เพื่อไม่ให้เกิดสัญญาณซ้ำในวันรุ่งขึ้น)
        rsi_cross_under = (df['RSI'] < dynamic_threshold) & (df['RSI'].shift(1) >= dynamic_threshold)
        
        # Final Signal
        df['Signal'] = uptrend & rsi_cross_under
        
        return df

    def check_exit_conditions(
        self, 
        entry_price: float, 
        current_close: float,
        current_low: float = None,
        current_high: float = None
    ) -> tuple[bool, str]:
        """
        Override Exit Logic: ใช้ Step Trailing Stop แทน Fixed Take Profit
        """
        if current_low is None: current_low = current_close
        if current_high is None: current_high = current_close

        # --- 1. Base Stop Loss (ตาม Config เดิม) ---
        sl_pct = self.config.stop_loss_pct
        stop_price = entry_price * (1 - sl_pct / 100)

        # --- 2. Step Trailing Stop (ฟีเจอร์ใหม่) ---
        # Logic: ถ้าราคาวิ่งขึ้นไปกำไร ให้ขยับ Stop Loss ตามขึ้นไป
        
        # Step 1: ถ้ากำไร > 5% ให้เลื่อน Stop Loss มาที่ทุน (Break Even)
        if current_close > entry_price * 1.05:
            stop_price = max(stop_price, entry_price * 1.005) # ล็อคกำไรนิดหน่อย (0.5%) กันค่าคอม
            
        # Step 2: ถ้ากำไร > 10% ให้เลื่อน Stop Loss มาที่กำไร 5%
        if current_close > entry_price * 1.10:
            stop_price = max(stop_price, entry_price * 1.05)

        # Step 3: ถ้ากำไร > 15% ให้เลื่อน Stop Loss มาที่กำไร 10%
        if current_close > entry_price * 1.15:
            stop_price = max(stop_price, entry_price * 1.10)
            
        # ตรวจสอบว่าราคา Low ของวันนี้ หลุด Stop Price ที่เราคำนวณใหม่หรือไม่
        if current_low <= stop_price:
            return True, "TRAILING_STOP"

        # --- 3. Take Profit (Optional) ---
        # แนะนำให้ตั้ง TP สูงๆ หรือปิดไปเลย (0) เพื่อให้ Trailing Stop ทำงานเต็มที่
        if self.config.take_profit_pct > 0:
            tp_price = entry_price * (1 + self.config.take_profit_pct / 100)
            if current_high >= tp_price:
                return True, "TAKE_PROFIT"
        
        return False, "HOLDING"
    
    @classmethod
    def get_default_config(cls) -> StrategyConfig:
        return StrategyConfig(
            name="buy_the_dip",
            holding_days=20,        # เพิ่มวันถือครองให้โอกาส Run Trend
            stop_loss_pct=5.0,      # SL ตั้งต้น
            take_profit_pct=0.0,    # ปิด TP (ใช้ 0) เพื่อใช้ Trailing Stop แทน
            parameters={
                "ema_length": 200,
                "rsi_length": 14,
                "rsi_threshold": 35 # ค่าพื้นฐาน (จะถูกปรับ Dynamic ในโค้ด)
            }
        )