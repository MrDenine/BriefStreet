from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from openai import OpenAIError, RateLimitError, APIError

from app.core.exceptions import BaseException
from app.core.logging_config import get_logger

logger = get_logger(__name__)


async def base_exception_handler(request: Request, exc: BaseException):
    logger.warning(
        f"BriefStreet Exception: {exc.message} | "
        f"Status: {exc.status_code} | "
        f"Path: {request.url.path} | "
        f"Details: {exc.details}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "message": exc.message,
                "details": exc.details,
                "path": request.url.path
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        f"Validation Error | Path: {request.url.path} | Errors: {exc.errors()}"
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "message": "Validation error",
                "details": exc.errors(),
                "path": request.url.path
            }
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(
        f"Database Error: {str(exc)} | Path: {request.url.path}",
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "message": "Database error occurred",
                "details": {"type": type(exc).__name__},
                "path": request.url.path
            }
        }
    )


async def openai_exception_handler(request: Request, exc: OpenAIError):
    if isinstance(exc, RateLimitError):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
        message = "OpenAI rate limit exceeded"
    elif isinstance(exc, APIError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        message = "OpenAI API error"
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        message = "OpenAI service error"
    
    logger.error(
        f"OpenAI Error: {message} | {str(exc)} | Path: {request.url.path}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "message": message,
                "details": {"error_type": type(exc).__name__},
                "path": request.url.path
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    logger.critical(
        f"Unhandled Exception: {str(exc)} | Path: {request.url.path}",
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "message": "An unexpected error occurred",
                "details": {"error_type": type(exc).__name__},
                "path": request.url.path
            }
        }
    )


def register_exception_handlers(app):
    logger.info("Registering exception handlers...")
    app.add_exception_handler(BaseException, base_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(OpenAIError, openai_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    logger.info("✅ Exception handlers registered successfully")
