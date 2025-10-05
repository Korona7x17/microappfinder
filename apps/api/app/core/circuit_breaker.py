"""
T020: Circuit breaker pattern for external APIs
Prevents cascading failures when external services are down
"""
from datetime import datetime, timedelta
from typing import Callable, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failures detected, circuit open
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker implementation

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests blocked
    - HALF_OPEN: Testing recovery, limited requests allowed

    Thresholds:
    - failure_threshold: Number of failures before opening (default: 5)
    - timeout: Seconds before attempting recovery (default: 60)
    - success_threshold: Successes needed to close from half-open (default: 2)
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: int = 60,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker

        Args:
            name: Circuit breaker identifier
            failure_threshold: Failures before opening
            timeout: Seconds before recovery attempt
            success_threshold: Successes to close from half-open
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        # Check if circuit should transition to half-open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"Circuit breaker {self.name}: Transitioning to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(
                    f"Circuit breaker {self.name} is OPEN. "
                    f"Service unavailable. Retry after {self.timeout}s."
                )

        try:
            # Execute function
            result = func(*args, **kwargs)

            # Record success
            self._on_success()

            return result

        except Exception as e:
            # Record failure
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True

        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout

    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.debug(
                f"Circuit breaker {self.name}: Success in HALF_OPEN "
                f"({self.success_count}/{self.success_threshold})"
            )

            if self.success_count >= self.success_threshold:
                logger.info(f"Circuit breaker {self.name}: Closing circuit")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.last_failure_time = None
        else:
            # Reset failure count on success in CLOSED state
            self.failure_count = 0

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        logger.warning(
            f"Circuit breaker {self.name}: Failure #{self.failure_count} "
            f"(threshold: {self.failure_threshold})"
        )

        if self.state == CircuitState.HALF_OPEN:
            # Single failure in half-open reopens circuit
            logger.error(f"Circuit breaker {self.name}: Reopening circuit after HALF_OPEN failure")
            self.state = CircuitState.OPEN
            self.success_count = 0

        elif self.failure_count >= self.failure_threshold:
            # Too many failures, open circuit
            logger.error(
                f"Circuit breaker {self.name}: Opening circuit "
                f"({self.failure_count} failures)"
            )
            self.state = CircuitState.OPEN

    def reset(self):
        """Manually reset circuit breaker"""
        logger.info(f"Circuit breaker {self.name}: Manual reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def get_state(self) -> str:
        """Get current circuit state"""
        return self.state.value


# Global circuit breaker instances
_circuit_breakers = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout: int = 60,
    success_threshold: int = 2
) -> CircuitBreaker:
    """
    Get or create circuit breaker instance

    Args:
        name: Circuit breaker identifier
        failure_threshold: Failures before opening
        timeout: Seconds before recovery attempt
        success_threshold: Successes to close from half-open

    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            timeout=timeout,
            success_threshold=success_threshold
        )

    return _circuit_breakers[name]
