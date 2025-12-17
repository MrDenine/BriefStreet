from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class BaseException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class SymbolNotFoundException(BaseException):
    def __init__(self, symbol: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Symbol '{symbol}' not found or has no data available",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details or {"symbol": symbol}
        )


class DataFetchException(BaseException):
    def __init__(self, source: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Failed to fetch data from {source}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details or {"source": source}
        )


class LLMServiceException(BaseException):
    def __init__(self, message: str = "LLM service error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


class DatabaseException(BaseException):
    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class ValidationException(BaseException):
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=error_details
        )


class CacheException(BaseException):
    def __init__(self, message: str = "Cache operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class RateLimitException(BaseException):
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )


class AuthenticationException(BaseException):
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class TranscriptNotFoundException(BaseException):
    def __init__(self, symbol: str, quarter: Optional[str] = None):
        details = {"symbol": symbol}
        if quarter:
            details["quarter"] = quarter
        
        message = f"No earnings transcript found for {symbol}"
        if quarter:
            message += f" in {quarter}"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class ProviderNotImplementedException(BaseException):
    """Exception raised when a data provider doesn't support a specific feature"""
    def __init__(self, provider: str, feature: str):
        super().__init__(
            message=f"Provider '{provider}' does not support '{feature}'",
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            details={"provider": provider, "feature": feature}
        )


class ProviderUnavailableException(BaseException):
    """Exception raised when a data provider is temporarily unavailable"""
    def __init__(self, provider: str, reason: Optional[str] = None):
        details = {"provider": provider}
        if reason:
            details["reason"] = reason
        
        super().__init__(
            message=f"Data provider '{provider}' is currently unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


class AllProvidersFailedException(BaseException):
    """Exception raised when all configured providers fail to fetch data"""
    def __init__(self, feature: str, attempted_providers: list, errors: dict):
        super().__init__(
            message=f"All providers failed to fetch '{feature}'",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={
                "feature": feature,
                "attempted_providers": attempted_providers,
                "errors": errors
            }
        )
