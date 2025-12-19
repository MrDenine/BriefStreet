import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from app.core.config import settings


def setup_logging(log_level: str = "INFO"):
    """
    ตั้งค่า logging สำหรับแสดงใน terminal และบันทึกลงไฟล์
    รวมถึง log file แยกสำหรับ API requests
    """
    log_format = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    colored_format = logging.Formatter(
        fmt="%(asctime)s - %(name)-20s - %(levelname)-8s - %(message)s",
        datefmt="%H:%M:%S"
    )
    
    # สร้าง log directory
    log_dir = settings.DATA_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Console handler (แสดงใน terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(colored_format)
    
    # Main application log file
    main_log_file = log_dir / "briefstreet.log"
    main_file_handler = RotatingFileHandler(
        main_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    main_file_handler.setLevel(logging.INFO)
    main_file_handler.setFormatter(log_format)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(main_file_handler)
    
    # ตั้งค่า API log file แยกต่างหาก
    setup_api_logging(log_dir, log_format)
    
    # ปิด log ที่ไม่จำเป็นจาก libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    return root_logger


def setup_api_logging(log_dir: Path, log_format: logging.Formatter):
    """
    ตั้งค่า logging แยกสำหรับ API endpoints
    บันทึก API requests, responses, และ errors ไปยังไฟล์แยก
    """
    # API log file
    api_log_file = log_dir / "api.log"
    # สร้างไฟล์เปล่าถ้ายังไม่มี
    api_log_file.touch(exist_ok=True)
    
    api_file_handler = RotatingFileHandler(
        api_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    api_file_handler.setLevel(logging.INFO)
    api_file_handler.setFormatter(log_format)
    
    # Error log file สำหรับ API errors
    error_log_file = log_dir / "api_errors.log"
    # สร้างไฟล์เปล่าถ้ายังไม่มี
    error_log_file.touch(exist_ok=True)
    
    error_file_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(log_format)
    
    # เพิ่ม handlers ให้กับ API loggers และ middleware
    api_loggers = [
        "app.api.v1.endpoints.analyze",
        "app.api.v1.endpoints.chat",
        "app.api.v1.endpoints.market_data",
        "app.api.v1.endpoints.valuation",
        "app.core.middleware"  # เพิ่ม middleware logging
    ]
    
    for logger_name in api_loggers:
        logger = logging.getLogger(logger_name)
        # ลบ handlers เก่าก่อน (ถ้ามี) เพื่อป้องกันการ log ซ้ำ
        logger.handlers.clear()
        logger.addHandler(api_file_handler)
        logger.addHandler(error_file_handler)
        logger.propagate = True  # ให้ส่งต่อไปยัง root logger ด้วย
    
    # Log ข้อความเริ่มต้นเพื่อทดสอบว่าไฟล์ทำงาน
    test_logger = logging.getLogger("app.core.logging_config")
    test_logger.info("✅ API logging initialized - log files created")


def get_logger(name: str) -> logging.Logger:
    """
    สร้าง logger สำหรับ module ต่างๆ
    """
    return logging.getLogger(name)
