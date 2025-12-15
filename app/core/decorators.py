import functools
import logging
from typing import Callable, Optional, Type
from app.core.exceptions import BaseException

logger = logging.getLogger(__name__)


def handle_exceptions(
    default_exception: Type[BaseException] = BaseException,
    log_error: bool = True,
    reraise: bool = True
):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except BaseException:
                raise
            except Exception as e:
                if log_error:
                    logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                if reraise:
                    raise default_exception(
                        message=f"Error in {func.__name__}",
                        details={"original_error": str(e)}
                    )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseException:
                raise
            except Exception as e:
                if log_error:
                    logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                if reraise:
                    raise default_exception(
                        message=f"Error in {func.__name__}",
                        details={"original_error": str(e)}
                    )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def retry_on_exception(
    max_retries: int = 3,
    exceptions: tuple = (Exception,),
    delay: float = 1.0,
    backoff: float = 2.0,
    log_errors: bool = True
):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            import asyncio
            current_delay = delay
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        if log_errors:
                            logger.error(
                                f"All {max_retries} attempts failed for {func.__name__}: {str(e)}",
                                exc_info=True
                            )
                        raise
                    
                    if log_errors:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay}s..."
                        )
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            current_delay = delay
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        if log_errors:
                            logger.error(
                                f"All {max_retries} attempts failed for {func.__name__}: {str(e)}",
                                exc_info=True
                            )
                        raise
                    
                    if log_errors:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay}s..."
                        )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


import asyncio
