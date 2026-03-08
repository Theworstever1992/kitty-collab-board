"""
retry.py — Kitty Collab Board
Retry logic with exponential backoff for API calls.
"""

import time
import functools
import logging
from typing import TypeVar, Callable, Optional, Type, Union

T = TypeVar('T')

# Exceptions that are considered transient and should be retried
TRANSIENT_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,  # Includes network errors
)


def is_transient_error(exception: Exception) -> bool:
    """
    Determine if an exception is transient (should be retried).
    
    Args:
        exception: The exception that was raised
        
    Returns:
        True if the error is transient and should be retried
    """
    # Check for rate limit errors (various SDKs implement this differently)
    error_str = str(exception).lower()
    error_type = type(exception).__name__.lower()
    
    # Rate limit indicators
    rate_limit_indicators = [
        "rate limit",
        "ratelimit",
        "429",
        "too many requests",
        "throttled",
    ]
    
    if any(ind in error_str for ind in rate_limit_indicators):
        return True
    
    if any(ind in error_type for ind in ["ratelimit", "rate_limit"]):
        return True
    
    # Timeout indicators
    timeout_indicators = [
        "timeout",
        "timed out",
        "connection reset",
        "connection refused",
        "temporary failure",
        "service unavailable",
        "503",
        "502",
        "504",
    ]
    
    if any(ind in error_str for ind in timeout_indicators):
        return True
    
    # Check if it's a known transient exception type
    if isinstance(exception, TRANSIENT_EXCEPTIONS):
        return True
    
    # Permanent errors that should NOT be retried
    permanent_indicators = [
        "authentication",
        "unauthorized",
        "forbidden",
        "permission",
        "invalid api key",
        "not found",
        "invalid request",
        "bad request",
        "validation",
        "context limit",
        "too large",
    ]
    
    if any(ind in error_str for ind in permanent_indicators):
        return False
    if any(ind in error_type for ind in ["authentication", "authorization", "permission", "notfound"]):
        return False
    
    # Default: retry unknown errors (conservative approach)
    return True


def retry_with_backoff(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None,
    logger: Optional[logging.Logger] = None,
) -> Callable:
    """
    Decorator that adds retry logic with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 5)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        exponential_base: Base for exponential calculation (default: 2.0)
        on_retry: Optional callback function(exception, attempt, delay) called before each retry
        logger: Optional logger for retry messages
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry this error
                    if not is_transient_error(e):
                        if logger:
                            logger.debug(f"Non-transient error in {func.__name__}, not retrying: {e}")
                        raise
                    
                    # Last attempt failed, don't retry
                    if attempt >= max_retries:
                        if logger:
                            logger.warning(f"All {max_retries} retries exhausted for {func.__name__}: {e}")
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    # Log retry attempt
                    if logger:
                        logger.info(f"Retry {attempt + 1}/{max_retries} for {func.__name__} after {delay:.1f}s: {e}")
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(e, attempt + 1, delay)
                    
                    # Wait before retry
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            raise last_exception if last_exception else RuntimeError("Retry loop exited unexpectedly")
        
        return wrapper
    return decorator


class RetryableProvider:
    """
    Mixin class for providers that want retry logic.
    
    Usage:
        class MyProvider(BaseProvider, RetryableProvider):
            def __init__(self):
                super().__init__()
                self.setup_retry(max_retries=3)
            
            @self.with_retry
            def complete(self, prompt, system="", config=None):
                # ... API call
    """
    
    def __init__(self):
        self._retry_config = {
            "max_retries": 5,
            "base_delay": 1.0,
            "max_delay": 60.0,
            "exponential_base": 2.0,
        }
        self._retry_logger = logging.getLogger(self.__class__.__name__)
    
    def setup_retry(
        self,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        logger: Optional[logging.Logger] = None,
    ):
        """Configure retry parameters."""
        self._retry_config.update({
            "max_retries": max_retries,
            "base_delay": base_delay,
            "max_delay": max_delay,
            "exponential_base": exponential_base,
        })
        if logger:
            self._retry_logger = logger
    
    def with_retry(self, func: Callable[..., T]) -> Callable[..., T]:
        """Apply retry decorator to a function."""
        return retry_with_backoff(
            max_retries=self._retry_config["max_retries"],
            base_delay=self._retry_config["base_delay"],
            max_delay=self._retry_config["max_delay"],
            exponential_base=self._retry_config["exponential_base"],
            logger=self._retry_logger,
        )(func)


def create_retry_wrapper(
    provider_instance,
    method_name: str,
    max_retries: int = 5,
    base_delay: float = 1.0,
):
    """
    Wrap a provider method with retry logic dynamically.
    
    Args:
        provider_instance: The provider instance
        method_name: Name of the method to wrap
        max_retries: Maximum retry attempts
        base_delay: Initial delay between retries
    """
    original_method = getattr(provider_instance, method_name)
    logger = logging.getLogger(provider_instance.__class__.__name__)
    
    @functools.wraps(original_method)
    def wrapped(*args, **kwargs):
        return retry_with_backoff(
            max_retries=max_retries,
            base_delay=base_delay,
            logger=logger,
        )(original_method)(*args, **kwargs)
    
    setattr(provider_instance, method_name, wrapped)
