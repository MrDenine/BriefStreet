# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.database import init_db, engine
from app.core.error_handlers import register_exception_handlers
from app.core.logging_config import setup_logging, get_logger
from app.api.v1.endpoints import analyze_router, chat_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging("INFO")
    logger.info("🚀 Starting BriefStreet API...")
    await init_db()
    logger.info("✅ Database connected successfully")
    
    yield
    
    logger.info("🛑 Shutting down BriefStreet API...")
    await engine.dispose()
    logger.info("✅ Database connection closed")


app = FastAPI(
    title="BriefStreet API",
    description="Financial earnings analysis API powered by AI",
    version="1.0.0",
    lifespan=lifespan
)

register_exception_handlers(app)

# Include routers
app.include_router(analyze_router, prefix="/api/v1", tags=["Analysis"])
app.include_router(chat_router, prefix="/api/v1", tags=["Chat"])


@app.get("/", tags=["Health"])
def read_root():
    logger.info("Health check endpoint accessed")
    return {"message": "Welcome to BriefStreet API! 🚀", "version": "1.0.0"}
