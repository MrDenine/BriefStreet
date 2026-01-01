import ccxt.async_support as ccxt  # ใช้โหมด Async
import os
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class ExchangeService:
    def __init__(self, exchange_id='binance'):
        # ✅ โหลด API Key และ Validate
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_SECRET_KEY")
        
        # Security check
        if not self.api_key or not self.api_secret:
            logger.warning("⚠️  Binance API credentials not found - running in TEST mode")
            self.test_mode = True
        else:
            self.test_mode = False
            logger.info(f"✅ Exchange Service initialized with API credentials")
        
        # Setup CCXT Exchange
        try:
            self.exchange_class = getattr(ccxt, exchange_id)
            self.exchange = self.exchange_class({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                },
                # ✅ เพิ่ม sandbox mode สำหรับ testing
                'sandbox': self.test_mode,
            })
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            raise

    async def close(self):
        """ปิด Connection เมื่อเลิกใช้"""
        await self.exchange.close()

    async def get_balance(self, currency="USDT"):
        """เช็คเงินในกระเป๋า"""
        balance = await self.exchange.fetch_balance()
        return balance['total'].get(currency, 0.0)

    async def get_current_price(self, symbol):
        """ดึงราคาล่าสุด"""
        ticker = await self.exchange.fetch_ticker(symbol)
        return ticker['last']

    async def create_order(self, symbol: str, side: str, amount: float, 
                          order_type: str = "limit", price: Optional[float] = None):
        """
        ส่งคำสั่งซื้อขายจริง (Core Logic)
        side: 'buy' หรือ 'sell'
        ✅ ปรับปรุง: เพิ่ม proper error handling และ logging
        """
        # ✅ ถ้าเป็น test mode ให้ mock order
        if self.test_mode:
            logger.warning(f"TEST MODE: Mock order {side} {amount} {symbol}")
            return {"id": "TEST_ORDER", "symbol": symbol, "side": side, "amount": amount}
        
        try:
            if order_type == 'limit':
                if price is None:
                    raise ValueError("Limit order requires price parameter")
                order = await self.exchange.create_order(symbol, 'limit', side, amount, price)
            else:
                order = await self.exchange.create_order(symbol, 'market', side, amount)
            
            logger.info(f"✅ Order placed: {side} {amount} {symbol} - ID: {order.get('id')}")
            return order
            
        except ccxt.InsufficientFunds as e:
            logger.error(f"❌ Insufficient funds for {symbol}: {e}")
            return None
        except ccxt.InvalidOrder as e:
            logger.error(f"❌ Invalid order for {symbol}: {e}")
            return None
        except ccxt.NetworkError as e:
            logger.error(f"❌ Network error while placing order: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected order error for {symbol}: {e}", exc_info=True)
            return None