from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy import func
from app.models.bot_config import BotConfig
from app.services.exchange_service import ExchangeService
import logging

logger = logging.getLogger(__name__)

class BotEngine:
    def __init__(self, db: AsyncSession, exchange: ExchangeService = None):
        self.db = db
        # ✅ สร้าง ExchangeService ใหม่ทุกครั้งเพื่อหลีกเลี่ยง event loop conflict
        self.exchange = exchange if exchange else ExchangeService()
        self._exchange_created = exchange is None  # Track ว่าเราสร้าง exchange เอง

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
            raise
        finally:
            # ✅ ปิด exchange connection หลังใช้งานเสร็จ (ถ้าเราสร้างเอง)
            if self._exchange_created:
                try:
                    await self.exchange.close()
                    logger.debug("Exchange connection closed")
                except Exception as e:
                    logger.warning(f"Failed to close exchange: {e}")

    async def process_bot(self, bot: BotConfig):
        symbol = bot.symbol
        params = bot.parameters
        strategy = bot.strategy_name
        
        logger.info(f"{'='*60}")
        logger.info(f"🤖 Processing Bot: {symbol}")
        logger.info(f"   Strategy: {strategy}")
        logger.info(f"   Parameters: {params}")
        logger.info(f"   Active: {bot.is_active}")
        
        try:
            # ====== Step 1: ดึงข้อมูลตลาด ======
            logger.info(f"📊 Step 1: Fetching market data for {symbol}...")
            current_price = await self.exchange.get_current_price(symbol)
            logger.info(f"   ✅ Current Price: ${current_price:,.2f}")
            
            # ====== Step 2: ตัดสินใจตาม Strategy ======
            logger.info(f"🧠 Step 2: Analyzing strategy '{strategy}'...")
            signal = "WAIT"
            
            if strategy == "Mock_Test":
                force_buy = params.get("force_buy", False)
                logger.info(f"   Checking force_buy parameter: {force_buy}")
                if force_buy == True:
                    signal = "BUY"
                    logger.info(f"   ✅ Signal: {signal} (forced by parameter)")
                else:
                    logger.info(f"   ⏸️  Signal: {signal} (force_buy is False)")
            else:
                logger.warning(f"   ⚠️  Strategy '{strategy}' not implemented, using WAIT")
            
            logger.info(f"   📍 Final Decision: {signal}")
            
            # ====== Step 3: Execute Trade (ถ้ามี signal) ======
            if signal == "BUY":
                amount_in_usdt = params.get("trade_amount", 10)
                amount = amount_in_usdt / current_price 
                
                logger.info(f"💰 Step 3: Executing {signal} order...")
                logger.info(f"   Amount (USDT): ${amount_in_usdt}")
                logger.info(f"   Amount ({symbol.split('/')[0]}): {amount:.8f}")
                logger.info(f"   Order Type: market")
                
                # เรียก Broker API
                order = await self.exchange.create_order(symbol, 'buy', amount, order_type='market')
                
                if order:
                    logger.info(f"   ✅ Order executed successfully")
                    logger.info(f"   Order ID: {order.get('id', 'N/A')}")
                    
                    # ====== Step 4: บันทึกลง Database ======
                    try:
                        logger.info(f"💾 Step 4: Recording order to database...")
                        bot.last_action = "BUY"
                        bot.last_trade_time = func.now()
                        
                        self.db.add(bot)
                        await self.db.commit()
                        await self.db.refresh(bot)
                        logger.info(f"   ✅ Database updated successfully")
                    except Exception as db_error:
                        await self.db.rollback()
                        logger.error(f"   ❌ Database update failed: {db_error}")
                        raise
                else:
                    logger.warning(f"   ⚠️  Order execution failed - no order returned")
            else:
                logger.info(f"⏭️  Step 3: Skipping trade execution (Signal: {signal})")
            
            logger.info(f"✅ Bot {symbol} processing completed successfully")
            logger.info(f"{'='*60}\n")

        except Exception as e:
            logger.error(f"❌ Error processing {symbol}: {e}", exc_info=True)
            await self.db.rollback()
            logger.info(f"{'='*60}\n")
            # ไม่ raise ต่อ เพื่อให้ bot ตัวอื่นทำงานต่อได้