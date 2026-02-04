"""
Retry decorator with exponential backoff.

Provides resilient retry logic for CLI calls and external operations.

Usage:
    from .retry import with_retry

    @with_retry(max_attempts=3, base_delay=1.0)
    def call_codex(prompt: str) -> str:
        # This will retry up to 3 times with 1s, 2s, 4s delays
        return subprocess.run(['codex', 'exec', ...])
"""

import time
import logging
from functools import wraps
from typing import TypeVar, Callable, Tuple, Type, Optional

T = TypeVar('T')

logger = logging.getLogger(__name__)


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retry with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay cap in seconds (default: 30.0)
        exponential_base: Base for exponential growth (default: 2.0)
        retryable_exceptions: Tuple of exceptions to retry on
        on_retry: Optional callback called on each retry (exception, attempt)

    Returns:
        Decorated function with retry logic

    Example:
        @with_retry(max_attempts=3, base_delay=1.0)
        def call_external_api():
            return requests.get('https://api.example.com')
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception: Optional[Exception] = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt < max_attempts:
                        # Calculate delay with exponential backoff
                        delay = min(
                            base_delay * (exponential_base ** (attempt - 1)),
                            max_delay
                        )

                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )

                        # Call retry callback if provided
                        if on_retry:
                            on_retry(e, attempt)

                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )

            # All attempts exhausted
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Unexpected state in retry for {func.__name__}")

        return wrapper
    return decorator


class RetryConfig:
    """
    Reusable retry configuration.

    Usage:
        config = RetryConfig(max_attempts=5, base_delay=2.0)

        @config.decorator
        def my_function():
            ...
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions

    @property
    def decorator(self) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """Get a decorator with this configuration."""
        return with_retry(
            max_attempts=self.max_attempts,
            base_delay=self.base_delay,
            max_delay=self.max_delay,
            exponential_base=self.exponential_base,
            retryable_exceptions=self.retryable_exceptions,
        )


# Pre-configured retry policies
CLI_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=10.0,
    exponential_base=2.0,
)

NETWORK_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
)
