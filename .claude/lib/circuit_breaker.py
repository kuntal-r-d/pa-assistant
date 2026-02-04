"""
Circuit breaker pattern for external service calls.

Prevents cascading failures by stopping calls to failing services.

Usage:
    from .circuit_breaker import CircuitBreaker

    codex_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

    try:
        result = codex_breaker.call(lambda: call_codex(prompt))
    except CircuitOpenError:
        # Service is unavailable, use fallback
        pass
"""

import time
import threading
import logging
from enum import Enum
from typing import TypeVar, Callable, Optional

T = TypeVar('T')

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation, requests pass through
    OPEN = "open"          # Failing, reject requests immediately
    HALF_OPEN = "half_open"  # Testing recovery, allow one request


class CircuitOpenError(Exception):
    """Raised when circuit is open and requests are rejected."""

    def __init__(self, message: str, retry_after: float = 0):
        super().__init__(message)
        self.retry_after = retry_after


class CircuitBreaker:
    """
    Circuit breaker for external service calls.

    Tracks failures and opens the circuit when threshold is reached.
    After recovery_timeout, allows a test request (half-open state).
    If test succeeds, closes circuit. If test fails, opens again.

    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before testing recovery
        name: Optional name for logging

    Example:
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

        for prompt in prompts:
            try:
                result = breaker.call(lambda: call_codex(prompt))
            except CircuitOpenError as e:
                print(f"Service unavailable, retry after {e.retry_after}s")
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        name: Optional[str] = None,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name or "CircuitBreaker"

        self._state = CircuitState.CLOSED
        self._failures = 0
        self._last_failure_time: float = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (rejecting requests)."""
        return self.state == CircuitState.OPEN

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func

        Raises:
            CircuitOpenError: If circuit is open
            Exception: Any exception from func
        """
        with self._lock:
            state = self._check_state()

            if state == CircuitState.OPEN:
                retry_after = self._time_until_recovery()
                raise CircuitOpenError(
                    f"{self.name}: Circuit open. Retry after {retry_after:.1f}s",
                    retry_after=retry_after
                )

        # Execute the function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise

    def _check_state(self) -> CircuitState:
        """Check and potentially transition state."""
        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                logger.info(f"{self.name}: Transitioning to HALF_OPEN")
                self._state = CircuitState.HALF_OPEN

        return self._state

    def _on_success(self) -> None:
        """Handle successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                logger.info(f"{self.name}: Recovery successful, closing circuit")

            self._failures = 0
            self._state = CircuitState.CLOSED

    def _on_failure(self, error: Exception) -> None:
        """Handle failed call."""
        with self._lock:
            self._failures += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Test request failed, reopen circuit
                logger.warning(f"{self.name}: Recovery test failed, reopening circuit: {error}")
                self._state = CircuitState.OPEN

            elif self._failures >= self.failure_threshold:
                # Threshold reached, open circuit
                logger.warning(
                    f"{self.name}: Failure threshold ({self.failure_threshold}) reached, "
                    f"opening circuit: {error}"
                )
                self._state = CircuitState.OPEN

    def _time_until_recovery(self) -> float:
        """Get seconds until recovery test is allowed."""
        elapsed = time.time() - self._last_failure_time
        return max(0, self.recovery_timeout - elapsed)

    def reset(self) -> None:
        """Manually reset the circuit breaker."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failures = 0
            self._last_failure_time = 0
            logger.info(f"{self.name}: Manually reset")

    def get_status(self) -> dict:
        """Get current status information."""
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "failures": self._failures,
                "failure_threshold": self.failure_threshold,
                "last_failure_time": self._last_failure_time,
                "recovery_timeout": self.recovery_timeout,
                "time_until_recovery": self._time_until_recovery() if self._state == CircuitState.OPEN else 0,
            }


# Pre-configured circuit breakers for CLI tools
CODEX_CIRCUIT = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0,
    name="Codex"
)

GEMINI_CIRCUIT = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0,
    name="Gemini"
)
