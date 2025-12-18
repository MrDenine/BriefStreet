# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.database import init_db, engine
from app.core.error_handlers import register_exception_handlers
from app.core.logging_config import setup_logging, get_logger
from app.core.config import settings, RepositoryConfig
from app.api.v1.endpoints import analyze_router, chat_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging("INFO")
    logger.info(f"🚀 Starting {settings.PROJECT_NAME}...")
    logger.info(f"🌍 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🐛 Debug Mode: {settings.DEBUG}")
    
    # Initialize repository config
    RepositoryConfig.initialize(settings.ENVIRONMENT)
    
    # แสดง database config
    logger.info("📊 Database Configuration:")
    for domain, config in RepositoryConfig.get_all().items():
        logger.info(
            f"  - {domain}: {config.strategy.value} "
            f"(Primary: {config.primary_db.value})"
        )
    
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
