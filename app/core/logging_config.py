import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from app.core.config import settings


def setup_logging(log_level: str = "INFO"):
    """
    ตั้งค่า logging สำหรับแสดงใน terminal และบันทึกลงไฟล์
    """
    log_format = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    colored_format = logging.Formatter(
        fmt="%(asctime)s - %(name)-20s - %(levelname)-8s - %(message)s",
        datefmt="%H:%M:%S"
    )
    
    # Console handler (แสดงใน terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(colored_format)
    
    # File handler (บันทึกลงไฟล์)
    log_dir = settings.DATA_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "briefstreet.log"
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(log_format)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # ปิด log ที่ไม่จำเป็นจาก libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    สร้าง logger สำหรับ module ต่างๆ
    """
    return logging.getLogger(name)
