import asyncio
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine  
from app.services.bot_engine import BotEngine
import logging
from app.core.config import settings


logger = logging.getLogger(__name__)

# สร้าง Scheduler
scheduler = BackgroundScheduler()

# ✅ Lock mechanism เพื่อป้องกัน race condition
_bot_running_lock = threading.Lock()

async def _run_bot_async_logic():
    """
    ทำหน้าที่สร้าง Session และสั่งรัน Bot
    """
    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as db:
        try:
            logger.info("🔄 Scheduler: Starting Bot Cycle...")
            
            bot = BotEngine(db)
            await bot.run_cycle()
            
            logger.info("✅ Scheduler: Bot Cycle Finished")
            
        except Exception as e:
            logger.error(f"❌ Scheduler Error: {e}", exc_info=True)
            # Rollback any pending transactions
            await db.rollback()

def bot_job_wrapper():
    """
    Wrapper function - แปลง Sync (Scheduler) -> Async (Database/Bot)
    """
    # ตรวจสอบว่ามี job กำลังทำงานอยู่หรือไม่
    if not _bot_running_lock.acquire(blocking=False):
        logger.warning("⚠️  Previous bot cycle still running, skipping this cycle")
        return
    
    try:
        logger.debug("Acquired bot execution lock")
        asyncio.run(_run_bot_async_logic())
    except Exception as e:
        logger.error(f"Critical Error in Job Wrapper: {e}", exc_info=True)
    finally:
        _bot_running_lock.release()
        logger.debug("Released bot execution lock")

def start_scheduler():
    """เริ่มทำงาน Scheduler (เรียกจาก main.py)"""
    if not scheduler.running:
        interval_minutes = settings.BOT_INTERVAL_MINUTES
        
        scheduler.add_job(
            bot_job_wrapper, 
            'interval', 
            minutes=interval_minutes, 
            id='main_bot_loop',
            max_instances=1,  # ✅ ป้องกัน concurrent jobs
            coalesce=True     # ✅ รวม missed jobs เป็น 1 job
        )
        scheduler.start()
        logger.info(f"Scheduler started with {interval_minutes} minute interval")
    else:
        logger.warning("Scheduler already running")

def stop_scheduler():
    """✅ หยุด Scheduler อย่างปลอดภัย (เรียกตอน shutdown)"""
    if scheduler.running:
        logger.info("Stopping scheduler...")
        scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped gracefully")