from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy import func
from app.models.bot_config import BotConfig
from app.services.exchange_service import ExchangeService
import logging

logger = logging.getLogger(__name__)

# ✅ Singleton instance ของ ExchangeService เพื่อป้องกัน memory leak
_exchange_instance = None

class BotEngine:
    def __init__(self, db: AsyncSession, exchange: ExchangeService = None):
        self.db = db
        # ใช้ shared instance หรือสร้างใหม่ถ้าไม่มี
        global _exchange_instance
        if exchange:
            self.exchange = exchange
        elif _exchange_instance is None:
            _exchange_instance = ExchangeService()
            self.exchange = _exchange_instance
        else:
            self.exchange = _exchange_instance

    async def run_cycle(self):
        """
        ฟังก์ชันหลักที่จะโดนเรียกทุกๆ Loop
        ✅ ปรับปรุง: เพิ่ม exception handling และ resource cleanup
        """
        try:
            # Query active bots
            statement = select(BotConfig).where(BotConfig.is_active == True)
            result = await self.db.execute(statement)
            active_bots = result.scalars().all()
            
            if not active_bots:
                logger.info("No active bots configured.")
                return

            logger.info(f"Processing {len(active_bots)} active bots...")

            # Process each bot
            for bot in active_bots:
                await self.process_bot(bot)
                
        except Exception as e:
            logger.error(f"Critical error in bot cycle: {e}", exc_info=True)
            # ไม่ close exchange ที่นี่ เพราะเป็น singleton
            raise

    async def process_bot(self, bot: BotConfig):
        symbol = bot.symbol
        params = bot.parameters
        strategy = bot.strategy_name
        
        try:

            # TODO: Implement strategy logic here

            # ดึงข้อมูลตลาด
            current_price = await self.exchange.get_current_price(symbol)
            logger.info(f"[{symbol}] Price: {current_price} | Strategy: {strategy}")

            # ตัดสินใจตาม Strategy
            signal = "WAIT"
            
            if strategy == "Mock_Test":
                 if params.get("force_buy") == True:
                    signal = "BUY"
            
            # ส่งคำสั่ง Trade
            if signal == "BUY":
                amount_in_usdt = params.get("trade_amount", 10)
                amount = amount_in_usdt / current_price 
                
                logger.info(f"🚀 Executing BUY {symbol} amount {amount:.6f}")
                
                # เรียก Broker API
                order = await self.exchange.create_order(symbol, 'buy', amount, order_type='market')
                
                if order:
                    # ✅ บันทึกลง DB พร้อม error handling
                    try:
                        bot.last_action = "BUY"
                        bot.last_trade_time = func.now()
                        
                        self.db.add(bot)
                        await self.db.commit()
                        await self.db.refresh(bot)
                        logger.info(f"✅ Order recorded for {symbol}")
                    except Exception as db_error:
                        await self.db.rollback()
                        logger.error(f"Failed to record order in DB: {db_error}")
                        raise
                else:
                    logger.warning(f"Order failed for {symbol}")

        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}", exc_info=True)
            await self.db.rollback()
            # ไม่ raise ต่อ เพื่อให้ bot ตัวอื่นทำงานต่อได้