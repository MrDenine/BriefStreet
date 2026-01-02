# app/api/v1/endpoints/bot_control.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List, Dict, Any
from pydantic import BaseModel
from app.services.scheduler_service import bot_job_wrapper
from app.services.bot_engine import BotEngine
from app.models.bot_config import BotConfig
from app.core.database import get_db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic Models สำหรับ Request/Response
class BotCreateRequest(BaseModel):
    symbol: str
    strategy_name: str = "Mock_Test"
    parameters: Dict[str, Any] = {"trade_amount": 10, "force_buy": False}
    is_active: bool = False

class BotUpdateRequest(BaseModel):
    is_active: bool

@router.post("/run-now")
async def trigger_bot_manually(background_tasks: BackgroundTasks):
    """
    ปุ่มกดสำหรับสั่ง Bot ทำงานทันที 1 รอบ (Run Cycle)
    ใช้ BackgroundTasks เพื่อไม่ให้หน้าเว็บค้างรอ
    """
    try:
        # สั่งให้ทำงานใน Background ทันที (เหมือน Scheduler เรียก)
        background_tasks.add_task(bot_job_wrapper)
        return {"status": "success", "message": "Bot cycle started in background!"}
    except Exception as e:
        logger.error(f"Manual trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_bot_status():
    """ดึงสถานะล่าสุดมาโชว์ที่หน้าเว็บ"""
    return {"status": "active", "last_run": "Checking logs..."}

@router.get("/bots")
async def list_bots(db: AsyncSession = Depends(get_db)):
    """ดึงรายการ Bot ทั้งหมด"""
    try:
        statement = select(BotConfig)
        result = await db.execute(statement)
        bots = result.scalars().all()
        return {"bots": bots, "count": len(bots)}
    except Exception as e:
        logger.error(f"Failed to list bots: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bots")
async def create_bot(bot_data: BotCreateRequest, db: AsyncSession = Depends(get_db)):
    """สร้าง Bot instance ใหม่"""
    try:
        # ตรวจสอบว่ามี symbol ซ้ำหรือไม่
        statement = select(BotConfig).where(BotConfig.symbol == bot_data.symbol)
        result = await db.execute(statement)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(status_code=400, detail=f"Bot for {bot_data.symbol} already exists")
        
        # สร้าง Bot ใหม่
        new_bot = BotConfig(
            symbol=bot_data.symbol,
            strategy_name=bot_data.strategy_name,
            parameters=bot_data.parameters,
            is_active=bot_data.is_active
        )
        
        db.add(new_bot)
        await db.commit()
        await db.refresh(new_bot)
        
        logger.info(f"Created new bot: {bot_data.symbol}")
        return {"status": "success", "bot": new_bot}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/bots/{symbol}/start")
async def start_bot(symbol: str, db: AsyncSession = Depends(get_db)):
    """เปิดใช้งาน Bot (Start)"""
    try:
        statement = select(BotConfig).where(BotConfig.symbol == symbol)
        result = await db.execute(statement)
        bot = result.scalar_one_or_none()
        
        if not bot:
            raise HTTPException(status_code=404, detail=f"Bot {symbol} not found")
        
        bot.is_active = True
        await db.commit()
        await db.refresh(bot)
        
        logger.info(f"Started bot: {symbol}")
        return {"status": "success", "message": f"Bot {symbol} started", "bot": bot}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to start bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/bots/{symbol}/stop")
async def stop_bot(symbol: str, db: AsyncSession = Depends(get_db)):
    """ปิดการใช้งาน Bot (Stop)"""
    try:
        statement = select(BotConfig).where(BotConfig.symbol == symbol)
        result = await db.execute(statement)
        bot = result.scalar_one_or_none()
        
        if not bot:
            raise HTTPException(status_code=404, detail=f"Bot {symbol} not found")
        
        bot.is_active = False
        await db.commit()
        await db.refresh(bot)
        
        logger.info(f"Stopped bot: {symbol}")
        return {"status": "success", "message": f"Bot {symbol} stopped", "bot": bot}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to stop bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/bots/{symbol}")
async def delete_bot(symbol: str, db: AsyncSession = Depends(get_db)):
    """ลบ Bot instance"""
    try:
        statement = select(BotConfig).where(BotConfig.symbol == symbol)
        result = await db.execute(statement)
        bot = result.scalar_one_or_none()
        
        if not bot:
            raise HTTPException(status_code=404, detail=f"Bot {symbol} not found")
        
        await db.delete(bot)
        await db.commit()
        
        logger.info(f"Deleted bot: {symbol}")
        return {"status": "success", "message": f"Bot {symbol} deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bots/create-and-test")
async def create_and_test_bot(bot_data: BotCreateRequest, db: AsyncSession = Depends(get_db)):
    """
    สร้าง Bot instance ใหม่และทดสอบการทำงานทันทีในเส้นเดียว
    - ถ้ายังไม่มี bot สำหรับ symbol นี้ → สร้างใหม่
    - ถ้ามีอยู่แล้ว → อัพเดท strategy และ parameters แล้วทดสอบเลย (ไม่ต้องสร้างใหม่)
    - return ทั้ง bot config และผลลัพธ์จากการทดสอบ
    """
    try:
        # 1. ตรวจสอบว่ามี symbol อยู่แล้วหรือไม่
        statement = select(BotConfig).where(BotConfig.symbol == bot_data.symbol)
        result = await db.execute(statement)
        existing_bot = result.scalar_one_or_none()
        
        bot_to_test = None
        action = "created"
        
        if existing_bot:
            # ✅ มีอยู่แล้ว → อัพเดท config แล้วทดสอบเลย
            existing_bot.strategy_name = bot_data.strategy_name
            existing_bot.parameters = bot_data.parameters
            # ไม่เปลี่ยน is_active เพื่อรักษาสถานะเดิม (ไม่ให้ bot หยุดทำงานถ้ากำลังรันอยู่)
            
            await db.commit()
            await db.refresh(existing_bot)
            
            bot_to_test = existing_bot
            action = "updated"
            logger.info(f"Updated existing bot: {bot_data.symbol}")
            
        else:
            # ✅ ยังไม่มี → สร้างใหม่
            new_bot = BotConfig(
                symbol=bot_data.symbol,
                strategy_name=bot_data.strategy_name,
                parameters=bot_data.parameters,
                is_active=bot_data.is_active
            )
            
            db.add(new_bot)
            await db.commit()
            await db.refresh(new_bot)
            
            bot_to_test = new_bot
            action = "created"
            logger.info(f"Created new bot: {bot_data.symbol}")
        
        # 3. ทดสอบ Bot ทันที (ส่ง db session เข้าไป)
        bot_engine = BotEngine(db=db)
        test_result = {
            "test_executed": False,
            "message": "Test skipped",
            "details": None
        }
        
        try:
            logger.info(f"Testing bot: {bot_data.symbol}")
            await bot_engine.process_bot(bot_to_test)
            
            # Refresh เพื่อดึงข้อมูลล่าสุดหลังจากทดสอบเสร็จ
            await db.refresh(bot_to_test)
            
            test_result = {
                "test_executed": True,
                "message": "Bot test completed successfully",
                "details": {
                    "symbol": bot_to_test.symbol,
                    "strategy": bot_to_test.strategy_name,
                    "last_action": bot_to_test.last_action,
                    "updated_at": str(bot_to_test.updated_at)
                }
            }
            logger.info(f"Bot test successful: {bot_data.symbol}")
            
        except Exception as test_error:
            logger.error(f"Bot test failed for {bot_data.symbol}: {test_error}")
            test_result = {
                "test_executed": True,
                "message": "Bot test failed",
                "details": {"error": str(test_error)}
            }
        
        # 4. Return ทั้ง bot config และผลลัพธ์การทดสอบ
        return {
            "status": "success",
            "action": action,  # "created" หรือ "updated"
            "bot": bot_to_test,
            "test_result": test_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create and test bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))