# app/core/middleware.py
"""
Middleware สำหรับ logging API requests และ responses
"""
import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class APILoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware สำหรับบันทึก API requests และ responses
    
    บันทึกข้อมูล:
    - Request method, path, query params
    - Response status code
    - Response time
    - Client IP address
    - Errors (ถ้ามี)
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # เริ่มจับเวลา
        start_time = time.time()
        
        # ดึงข้อมูล request
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        client_ip = request.client.host if request.client else "unknown"
        
        # เก็บ request body (ถ้าเป็น POST/PUT)
        request_body = None
        if method in ["POST", "PUT", "PATCH"]:
            try:
                # อ่าน body และเก็บไว้ใน state เพื่อให้ endpoint ใช้ได้
                body_bytes = await request.body()
                if body_bytes:
                    try:
                        request_body = json.loads(body_bytes.decode())
                    except:
                        request_body = body_bytes.decode()[:200]  # เก็บแค่ 200 ตัวอักษรแรก
            except:
                pass
        
        # Log request
        logger.info(
            f"➡️  {method} {path} "
            f"| Client: {client_ip} "
            f"{f'| Params: {query_params}' if query_params else ''}"
        )
        
        if request_body:
            logger.debug(f"Request body: {request_body}")
        
        # ประมวลผล request
        try:
            response = await call_next(request)
            
            # คำนวณเวลาที่ใช้
            process_time = time.time() - start_time
            
            # Log response
            status_emoji = "✅" if response.status_code < 400 else "❌"
            logger.info(
                f"{status_emoji} {method} {path} "
                f"| Status: {response.status_code} "
                f"| Time: {process_time:.3f}s"
            )
            
            # เพิ่ม header เวลาที่ใช้
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # คำนวณเวลาที่ใช้
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"💥 {method} {path} "
                f"| Error: {str(e)} "
                f"| Time: {process_time:.3f}s",
                exc_info=True
            )
            
            # Re-raise exception ให้ FastAPI error handler จัดการ
            raise


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    เพิ่ม unique request ID ให้กับทุก request
    เพื่อให้ติดตาม logs ได้ง่ายขึ้น
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import uuid
        
        # สร้าง request ID
        request_id = str(uuid.uuid4())
        
        # เพิ่ม request ID ลง request state
        request.state.request_id = request_id
        
        # ประมวลผล request
        response = await call_next(request)
        
        # เพิ่ม request ID ใน response header
        response.headers["X-Request-ID"] = request_id
        
        return response
