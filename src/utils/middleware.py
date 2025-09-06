"""Middleware for error handling and logging."""

import asyncio
import time
from typing import Callable, Any
from functools import wraps

from src.utils.logging import get_logger, log_error
from src.utils.exceptions import TGuardError

logger = get_logger(__name__)


def async_error_handler(func: Callable) -> Callable:
    """Decorator for async function error handling."""
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except TGuardError as e:
            logger.error(
                "TGuard error occurred",
                function=func.__name__,
                error_code=e.error_code,
                error_message=e.message,
                args=str(args)[:200],  # Limit args length
                kwargs=str(kwargs)[:200]
            )
            raise
        except Exception as e:
            log_error(
                e,
                {
                    "function": func.__name__,
                    "args": str(args)[:200],
                    "kwargs": str(kwargs)[:200]
                }
            )
            raise
    
    return wrapper


def sync_error_handler(func: Callable) -> Callable:
    """Decorator for sync function error handling."""
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TGuardError as e:
            logger.error(
                "TGuard error occurred",
                function=func.__name__,
                error_code=e.error_code,
                error_message=e.message,
                args=str(args)[:200],
                kwargs=str(kwargs)[:200]
            )
            raise
        except Exception as e:
            log_error(
                e,
                {
                    "function": func.__name__,
                    "args": str(args)[:200],
                    "kwargs": str(kwargs)[:200]
                }
            )
            raise
    
    return wrapper


def performance_monitor(threshold_seconds: float = 1.0):
    """Decorator to monitor function performance."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                if execution_time > threshold_seconds:
                    logger.warning(
                        "Slow function execution",
                        function=func.__name__,
                        execution_time=execution_time,
                        threshold=threshold_seconds
                    )
                else:
                    logger.debug(
                        "Function execution completed",
                        function=func.__name__,
                        execution_time=execution_time
                    )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                if execution_time > threshold_seconds:
                    logger.warning(
                        "Slow function execution",
                        function=func.__name__,
                        execution_time=execution_time,
                        threshold=threshold_seconds
                    )
                else:
                    logger.debug(
                        "Function execution completed",
                        function=func.__name__,
                        execution_time=execution_time
                    )
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator to retry function on failure."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            "Function failed after all retries",
                            function=func.__name__,
                            attempts=attempt + 1,
                            final_error=str(e)
                        )
                        break
                    
                    logger.warning(
                        "Function failed, retrying",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        error=str(e),
                        retry_delay=current_delay
                    )
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            "Function failed after all retries",
                            function=func.__name__,
                            attempts=attempt + 1,
                            final_error=str(e)
                        )
                        break
                    
                    logger.warning(
                        "Function failed, retrying",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        error=str(e),
                        retry_delay=current_delay
                    )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
