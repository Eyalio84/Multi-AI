# PLAYBOOK-10: Production Resilience

> **Synthesis Origin**: Distributed Systems Patterns + Claude API Behavior + Error Classification
> **Color Mix**: Blue (Retry Logic) + Yellow (Rate Limiting) = Green (Fault-Tolerant Systems)

## Overview

This playbook covers building **production-grade Claude integrations** that handle failures gracefully. Master exponential backoff, circuit breakers, multi-model fallback, and rate limiting.

**Key Insight**: Most Claude API failures are transient. Proper retry logic with backoff converts a 5% error rate into 99.9% effective availability.

### Strategic Value

| Without Resilience | With Resilience |
|-------------------|-----------------|
| 5% request failures | <0.1% failures |
| User sees errors | Graceful degradation |
| Random rate limits | Predictable throughput |
| Single model dependency | Multi-model fallback |
| Hard crashes | Soft failures |

---

## Part 1: Error Classification

### 1.1 Error Taxonomy

```
┌─────────────────────────────────────────────────────────────┐
│                    ERROR CLASSIFICATION                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  TRANSIENT (Retry)              PERMANENT (Don't Retry)     │
│  ──────────────────             ────────────────────────    │
│                                                              │
│  • 429 Rate Limited             • 400 Bad Request           │
│  • 500 Internal Server          • 401 Authentication        │
│  • 502 Bad Gateway              • 403 Permission Denied     │
│  • 503 Service Unavailable      • 404 Not Found             │
│  • 504 Gateway Timeout          • 413 Payload Too Large     │
│  • Connection Reset                                          │
│  • Timeout                      SPECIAL HANDLING             │
│                                 ─────────────────            │
│  Action: Retry with backoff     • 529 Overloaded            │
│                                   (long backoff)             │
│                                 • Context length exceeded    │
│                                   (reduce input)             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Error Handler Implementation

```python
# resilience/errors.py
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import re

class ErrorCategory(Enum):
    TRANSIENT = "transient"           # Retry with backoff
    RATE_LIMITED = "rate_limited"     # Retry with longer backoff
    OVERLOADED = "overloaded"         # Retry with very long backoff
    CONTEXT_EXCEEDED = "context"      # Reduce input and retry
    AUTHENTICATION = "auth"           # Don't retry, fix credentials
    PERMISSION = "permission"         # Don't retry, fix permissions
    BAD_REQUEST = "bad_request"       # Don't retry, fix request
    UNKNOWN = "unknown"               # Log and maybe retry once


@dataclass
class ClassifiedError:
    category: ErrorCategory
    status_code: Optional[int]
    message: str
    should_retry: bool
    suggested_wait: float  # seconds
    reduce_input: bool = False


class ErrorClassifier:
    """Classify API errors for appropriate handling."""

    # Status code mappings
    TRANSIENT_CODES = {500, 502, 503, 504}
    RATE_LIMIT_CODES = {429}
    OVERLOAD_CODES = {529}
    AUTH_CODES = {401}
    PERMISSION_CODES = {403}
    BAD_REQUEST_CODES = {400, 404, 413}

    @classmethod
    def classify(cls, error: Exception) -> ClassifiedError:
        """Classify an error for handling strategy."""

        # Extract status code and message
        status_code = getattr(error, 'status_code', None)
        message = str(error)

        # Check for context length errors (can appear in various forms)
        if cls._is_context_error(message):
            return ClassifiedError(
                category=ErrorCategory.CONTEXT_EXCEEDED,
                status_code=status_code,
                message=message,
                should_retry=True,
                suggested_wait=0,
                reduce_input=True
            )

        # Classify by status code
        if status_code:
            if status_code in cls.RATE_LIMIT_CODES:
                # Extract retry-after header if available
                retry_after = cls._extract_retry_after(error)
                return ClassifiedError(
                    category=ErrorCategory.RATE_LIMITED,
                    status_code=status_code,
                    message=message,
                    should_retry=True,
                    suggested_wait=retry_after or 60
                )

            if status_code in cls.OVERLOAD_CODES:
                return ClassifiedError(
                    category=ErrorCategory.OVERLOADED,
                    status_code=status_code,
                    message=message,
                    should_retry=True,
                    suggested_wait=300  # 5 minutes for overload
                )

            if status_code in cls.TRANSIENT_CODES:
                return ClassifiedError(
                    category=ErrorCategory.TRANSIENT,
                    status_code=status_code,
                    message=message,
                    should_retry=True,
                    suggested_wait=1
                )

            if status_code in cls.AUTH_CODES:
                return ClassifiedError(
                    category=ErrorCategory.AUTHENTICATION,
                    status_code=status_code,
                    message=message,
                    should_retry=False,
                    suggested_wait=0
                )

            if status_code in cls.PERMISSION_CODES:
                return ClassifiedError(
                    category=ErrorCategory.PERMISSION,
                    status_code=status_code,
                    message=message,
                    should_retry=False,
                    suggested_wait=0
                )

            if status_code in cls.BAD_REQUEST_CODES:
                return ClassifiedError(
                    category=ErrorCategory.BAD_REQUEST,
                    status_code=status_code,
                    message=message,
                    should_retry=False,
                    suggested_wait=0
                )

        # Network errors (connection reset, timeout)
        if cls._is_network_error(error):
            return ClassifiedError(
                category=ErrorCategory.TRANSIENT,
                status_code=None,
                message=message,
                should_retry=True,
                suggested_wait=2
            )

        # Unknown - retry once with caution
        return ClassifiedError(
            category=ErrorCategory.UNKNOWN,
            status_code=status_code,
            message=message,
            should_retry=True,
            suggested_wait=5
        )

    @staticmethod
    def _is_context_error(message: str) -> bool:
        patterns = [
            r'context.*(length|limit|exceeded)',
            r'too many tokens',
            r'maximum.*tokens',
            r'input.*too (long|large)',
        ]
        message_lower = message.lower()
        return any(re.search(p, message_lower) for p in patterns)

    @staticmethod
    def _is_network_error(error: Exception) -> bool:
        network_errors = (
            'ConnectionError', 'Timeout', 'ConnectionReset',
            'ConnectionRefused', 'NetworkError'
        )
        return any(err in type(error).__name__ for err in network_errors)

    @staticmethod
    def _extract_retry_after(error: Exception) -> Optional[float]:
        """Extract Retry-After header value if present."""
        if hasattr(error, 'response') and error.response:
            retry_after = error.response.headers.get('Retry-After')
            if retry_after:
                try:
                    return float(retry_after)
                except ValueError:
                    pass
        return None
```

---

## Part 2: Retry Strategies

### 2.1 Exponential Backoff with Jitter

```
┌─────────────────────────────────────────────────────────────┐
│           EXPONENTIAL BACKOFF WITH JITTER                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Without Jitter (Thundering Herd Problem):                   │
│  ─────────────────────────────────────────                   │
│                                                              │
│  Request 1: [fail] → wait 1s → wait 2s → wait 4s            │
│  Request 2: [fail] → wait 1s → wait 2s → wait 4s            │
│  Request 3: [fail] → wait 1s → wait 2s → wait 4s            │
│                 ↓                                            │
│  All retry at same time = another overload!                  │
│                                                              │
│                                                              │
│  With Jitter (Distributed Retries):                          │
│  ──────────────────────────────────                          │
│                                                              │
│  Request 1: [fail] → wait 0.7s → wait 1.8s → wait 3.2s      │
│  Request 2: [fail] → wait 1.2s → wait 2.4s → wait 4.9s      │
│  Request 3: [fail] → wait 0.9s → wait 1.5s → wait 3.8s      │
│                 ↓                                            │
│  Retries spread out = gradual recovery                       │
│                                                              │
│                                                              │
│  FORMULA: wait = min(cap, base * 2^attempt) * random(0.5,1) │
│                                                              │
│  Default values:                                             │
│  • base = 1 second                                           │
│  • cap = 60 seconds                                          │
│  • max_attempts = 5                                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Retry Implementation

```python
# resilience/retry.py
import asyncio
import random
import time
from typing import TypeVar, Callable, Any, Optional
from functools import wraps
from dataclasses import dataclass

from .errors import ErrorClassifier, ErrorCategory

T = TypeVar('T')


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_range: tuple = (0.5, 1.0)


class RetryExhausted(Exception):
    """All retry attempts failed."""
    def __init__(self, last_error: Exception, attempts: int):
        self.last_error = last_error
        self.attempts = attempts
        super().__init__(f"Failed after {attempts} attempts: {last_error}")


def calculate_backoff(
    attempt: int,
    config: RetryConfig,
    error_wait: float = 0
) -> float:
    """Calculate wait time for retry attempt."""
    # Use error's suggested wait if provided
    if error_wait > 0:
        base_wait = error_wait
    else:
        # Exponential backoff
        base_wait = config.base_delay * (config.exponential_base ** attempt)

    # Apply cap
    wait = min(base_wait, config.max_delay)

    # Apply jitter
    if config.jitter:
        jitter_min, jitter_max = config.jitter_range
        wait *= random.uniform(jitter_min, jitter_max)

    return wait


async def retry_async(
    func: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
    **kwargs
) -> T:
    """
    Retry an async function with exponential backoff.

    Args:
        func: Async function to retry
        config: Retry configuration
        on_retry: Callback(attempt, error, wait_time) on each retry

    Returns:
        Function result on success

    Raises:
        RetryExhausted: If all attempts fail
    """
    config = config or RetryConfig()
    last_error = None

    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)

        except Exception as e:
            last_error = e
            classified = ErrorClassifier.classify(e)

            # Don't retry non-retryable errors
            if not classified.should_retry:
                raise

            # Check if we have attempts left
            if attempt + 1 >= config.max_attempts:
                break

            # Calculate wait time
            wait = calculate_backoff(attempt, config, classified.suggested_wait)

            # Notify callback
            if on_retry:
                on_retry(attempt + 1, e, wait)

            # Wait before retry
            await asyncio.sleep(wait)

    raise RetryExhausted(last_error, config.max_attempts)


def retry_sync(
    func: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
    **kwargs
) -> T:
    """Synchronous version of retry."""
    config = config or RetryConfig()
    last_error = None

    for attempt in range(config.max_attempts):
        try:
            return func(*args, **kwargs)

        except Exception as e:
            last_error = e
            classified = ErrorClassifier.classify(e)

            if not classified.should_retry:
                raise

            if attempt + 1 >= config.max_attempts:
                break

            wait = calculate_backoff(attempt, config, classified.suggested_wait)

            if on_retry:
                on_retry(attempt + 1, e, wait)

            time.sleep(wait)

    raise RetryExhausted(last_error, config.max_attempts)


# Decorator versions
def with_retry(config: Optional[RetryConfig] = None):
    """Decorator for adding retry logic to functions."""
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await retry_async(func, *args, config=config, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return retry_sync(func, *args, config=config, **kwargs)
            return sync_wrapper
    return decorator
```

---

## Part 3: Circuit Breaker Pattern

### 3.1 Circuit States

```
┌─────────────────────────────────────────────────────────────┐
│                    CIRCUIT BREAKER STATES                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                      ┌─────────┐                            │
│                      │ CLOSED  │ ← Normal operation         │
│                      │(Healthy)│   All requests pass        │
│                      └────┬────┘                            │
│                           │                                  │
│                           │ Failure threshold reached        │
│                           │ (e.g., 5 failures in 60s)       │
│                           │                                  │
│                           ▼                                  │
│                      ┌─────────┐                            │
│                      │  OPEN   │ ← Fail fast                │
│                      │(Broken) │   Reject immediately       │
│                      └────┬────┘                            │
│                           │                                  │
│                           │ Recovery timeout elapsed         │
│                           │ (e.g., 30 seconds)              │
│                           │                                  │
│                           ▼                                  │
│                      ┌─────────┐                            │
│                      │HALF-OPEN│ ← Testing recovery         │
│                      │(Testing)│   Allow limited requests   │
│                      └────┬────┘                            │
│                           │                                  │
│               ┌───────────┴───────────┐                     │
│               │                       │                      │
│               ▼                       ▼                      │
│          Success                   Failure                   │
│          → CLOSED                  → OPEN                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Circuit Breaker Implementation

```python
# resilience/circuit_breaker.py
import asyncio
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable, Any, List
from collections import deque
import threading


class CircuitState(Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing fast
    HALF_OPEN = "half_open" # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Failures to trigger open
    success_threshold: int = 2          # Successes to close from half-open
    timeout: float = 30.0               # Seconds before half-open
    window_size: float = 60.0           # Window for counting failures
    half_open_max_calls: int = 3        # Max concurrent calls in half-open


@dataclass
class CircuitStats:
    """Statistics for circuit breaker."""
    state: CircuitState = CircuitState.CLOSED
    failures: int = 0
    successes: int = 0
    rejected: int = 0
    last_failure_time: Optional[float] = None
    last_state_change: float = field(default_factory=time.time)


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascade failures.

    Usage:
        breaker = CircuitBreaker("claude-api")

        @breaker
        async def call_api():
            return await client.messages.create(...)
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        on_state_change: Optional[Callable[[CircuitState, CircuitState], None]] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.on_state_change = on_state_change

        self._state = CircuitState.CLOSED
        self._failure_times: deque = deque()
        self._half_open_calls = 0
        self._half_open_successes = 0
        self._stats = CircuitStats()
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._check_state_transition()
            return self._state

    @property
    def stats(self) -> CircuitStats:
        return self._stats

    def _check_state_transition(self):
        """Check if state should transition based on time."""
        if self._state == CircuitState.OPEN:
            # Check if timeout has elapsed for half-open
            elapsed = time.time() - self._stats.last_state_change
            if elapsed >= self.config.timeout:
                self._transition_to(CircuitState.HALF_OPEN)

    def _transition_to(self, new_state: CircuitState):
        """Transition to new state."""
        old_state = self._state
        self._state = new_state
        self._stats.state = new_state
        self._stats.last_state_change = time.time()

        if new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
            self._half_open_successes = 0

        if self.on_state_change:
            self.on_state_change(old_state, new_state)

    def _count_recent_failures(self) -> int:
        """Count failures within the time window."""
        now = time.time()
        cutoff = now - self.config.window_size

        # Remove old failures
        while self._failure_times and self._failure_times[0] < cutoff:
            self._failure_times.popleft()

        return len(self._failure_times)

    def _record_failure(self):
        """Record a failure."""
        now = time.time()
        self._failure_times.append(now)
        self._stats.failures += 1
        self._stats.last_failure_time = now

        if self._state == CircuitState.CLOSED:
            if self._count_recent_failures() >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)

        elif self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open goes back to open
            self._transition_to(CircuitState.OPEN)

    def _record_success(self):
        """Record a success."""
        self._stats.successes += 1

        if self._state == CircuitState.HALF_OPEN:
            self._half_open_successes += 1
            if self._half_open_successes >= self.config.success_threshold:
                self._transition_to(CircuitState.CLOSED)
                self._failure_times.clear()

    def can_execute(self) -> bool:
        """Check if a call can be made."""
        with self._lock:
            self._check_state_transition()

            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                self._stats.rejected += 1
                return False

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                self._stats.rejected += 1
                return False

        return False

    def __call__(self, func: Callable) -> Callable:
        """Decorator for protecting functions with circuit breaker."""
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                if not self.can_execute():
                    raise CircuitOpenError(self.name, self._stats)

                try:
                    result = await func(*args, **kwargs)
                    with self._lock:
                        self._record_success()
                    return result
                except Exception as e:
                    with self._lock:
                        self._record_failure()
                    raise
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                if not self.can_execute():
                    raise CircuitOpenError(self.name, self._stats)

                try:
                    result = func(*args, **kwargs)
                    with self._lock:
                        self._record_success()
                    return result
                except Exception as e:
                    with self._lock:
                        self._record_failure()
                    raise
            return sync_wrapper


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    def __init__(self, name: str, stats: CircuitStats):
        self.name = name
        self.stats = stats
        super().__init__(
            f"Circuit '{name}' is OPEN. "
            f"Failures: {stats.failures}, Rejected: {stats.rejected}"
        )
```

---

## Part 4: Rate Limiting

### 4.1 Token Bucket Algorithm

```
┌─────────────────────────────────────────────────────────────┐
│                    TOKEN BUCKET ALGORITHM                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                    ┌───────────────┐                        │
│                    │    Bucket     │                        │
│                    │   (capacity)  │                        │
│                    │               │                        │
│   Tokens added  →  │  ● ● ● ● ●  │  → Tokens consumed      │
│   at rate R        │  ● ● ● ●    │    per request         │
│                    │  ● ● ●      │                        │
│                    │  ● ●        │                        │
│                    └───────────────┘                        │
│                                                              │
│  PARAMETERS:                                                 │
│  ───────────                                                 │
│  • Capacity: Maximum tokens (burst size)                    │
│  • Rate: Tokens added per second                            │
│  • Cost: Tokens consumed per request                        │
│                                                              │
│  EXAMPLE (Claude API Tier 1):                               │
│  ────────────────────────────                               │
│  • Rate: 60,000 tokens per minute = 1,000/sec              │
│  • Capacity: 60,000 (1 minute burst)                        │
│  • Request cost: Estimated tokens in request                │
│                                                              │
│  BEHAVIOR:                                                   │
│  ─────────                                                   │
│  • Request arrives → Check if tokens available              │
│  • Available → Deduct tokens, allow request                 │
│  • Not available → Wait or reject                           │
│  • Tokens refill at constant rate                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Rate Limiter Implementation

```python
# resilience/rate_limiter.py
import asyncio
import time
from dataclasses import dataclass
from typing import Optional
import threading


@dataclass
class RateLimiterConfig:
    """Rate limiter configuration."""
    tokens_per_minute: int = 60000    # Claude Tier 1 default
    capacity: Optional[int] = None     # Defaults to tokens_per_minute
    initial_tokens: Optional[int] = None  # Defaults to capacity


class TokenBucket:
    """
    Token bucket rate limiter for API calls.

    Implements smooth rate limiting that allows bursts up to
    capacity while maintaining long-term rate.
    """

    def __init__(self, config: Optional[RateLimiterConfig] = None):
        self.config = config or RateLimiterConfig()

        # Calculate rates
        self.rate = self.config.tokens_per_minute / 60.0  # tokens per second
        self.capacity = self.config.capacity or self.config.tokens_per_minute

        # Initialize bucket
        initial = self.config.initial_tokens
        self.tokens = initial if initial is not None else self.capacity

        self.last_update = time.time()
        self._lock = threading.Lock()

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now

        # Add tokens based on elapsed time
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.rate
        )

    def acquire(self, tokens: int = 1, block: bool = True) -> bool:
        """
        Acquire tokens from bucket.

        Args:
            tokens: Number of tokens to acquire
            block: If True, wait for tokens. If False, return immediately.

        Returns:
            True if tokens acquired, False if not available (non-blocking only)
        """
        with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            if not block:
                return False

        # Calculate wait time
        wait_time = (tokens - self.tokens) / self.rate

        # Wait and retry
        time.sleep(wait_time)

        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def acquire_async(self, tokens: int = 1) -> bool:
        """Async version of acquire."""
        with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

        # Calculate wait time
        wait_time = (tokens - self.tokens) / self.rate
        await asyncio.sleep(wait_time)

        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def wait_time(self, tokens: int = 1) -> float:
        """Calculate wait time for acquiring tokens."""
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                return 0.0
            return (tokens - self.tokens) / self.rate

    @property
    def available_tokens(self) -> float:
        """Get current available tokens."""
        with self._lock:
            self._refill()
            return self.tokens


class AdaptiveRateLimiter(TokenBucket):
    """
    Rate limiter that adapts based on API responses.

    Reduces rate on 429 errors, increases on success.
    """

    def __init__(self, config: Optional[RateLimiterConfig] = None):
        super().__init__(config)
        self.original_rate = self.rate
        self.backoff_factor = 0.5  # Reduce by 50% on rate limit
        self.recovery_factor = 1.1  # Increase by 10% on success
        self.min_rate = self.original_rate * 0.1  # Minimum 10% of original
        self.consecutive_successes = 0
        self.recovery_threshold = 10  # Successes before rate increase

    def on_rate_limited(self):
        """Called when 429 received."""
        with self._lock:
            self.rate = max(self.min_rate, self.rate * self.backoff_factor)
            self.consecutive_successes = 0

    def on_success(self):
        """Called on successful request."""
        with self._lock:
            self.consecutive_successes += 1
            if self.consecutive_successes >= self.recovery_threshold:
                self.rate = min(self.original_rate, self.rate * self.recovery_factor)
                self.consecutive_successes = 0
```

---

## Part 5: Multi-Model Fallback

### 5.1 Fallback Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                  MULTI-MODEL FALLBACK CHAIN                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Primary Model (Opus 4.5)                                   │
│  ─────────────────────────                                   │
│         │                                                    │
│         │ Try first (best quality)                          │
│         │                                                    │
│         ▼                                                    │
│    ┌─────────┐                                              │
│    │ Success │ → Return result                              │
│    └────┬────┘                                              │
│         │                                                    │
│    Failure (rate limit, overload, timeout)                  │
│         │                                                    │
│         ▼                                                    │
│  Fallback Model 1 (Sonnet 4)                                │
│  ───────────────────────────                                 │
│         │                                                    │
│         │ Try second (good quality, faster)                 │
│         │                                                    │
│         ▼                                                    │
│    ┌─────────┐                                              │
│    │ Success │ → Return result (with quality note)          │
│    └────┬────┘                                              │
│         │                                                    │
│    Failure                                                   │
│         │                                                    │
│         ▼                                                    │
│  Fallback Model 2 (Haiku 4)                                 │
│  ──────────────────────────                                  │
│         │                                                    │
│         │ Last resort (basic quality, very fast)            │
│         │                                                    │
│         ▼                                                    │
│    ┌─────────┐                                              │
│    │ Success │ → Return result (with degradation note)      │
│    └────┬────┘                                              │
│         │                                                    │
│    Failure → Raise error (all models failed)                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Fallback Implementation

```python
# resilience/fallback.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from enum import Enum
import asyncio


class ModelTier(Enum):
    OPUS = "claude-opus-4-5-20251101"
    SONNET = "claude-sonnet-4-20250514"
    HAIKU = "claude-haiku-4-20250514"


@dataclass
class ModelConfig:
    """Configuration for a model in the fallback chain."""
    model_id: str
    tier: ModelTier
    max_tokens: int = 4096
    timeout: float = 120.0
    is_fallback: bool = False

    # Cost per million tokens
    input_cost: float = 0.0
    output_cost: float = 0.0


@dataclass
class FallbackResult:
    """Result from fallback chain."""
    response: Any
    model_used: str
    tier_used: ModelTier
    was_fallback: bool
    attempts: List[Dict[str, Any]] = field(default_factory=list)


# Default fallback chain
DEFAULT_CHAIN = [
    ModelConfig(
        model_id=ModelTier.OPUS.value,
        tier=ModelTier.OPUS,
        input_cost=15.0,
        output_cost=75.0
    ),
    ModelConfig(
        model_id=ModelTier.SONNET.value,
        tier=ModelTier.SONNET,
        is_fallback=True,
        input_cost=3.0,
        output_cost=15.0
    ),
    ModelConfig(
        model_id=ModelTier.HAIKU.value,
        tier=ModelTier.HAIKU,
        is_fallback=True,
        timeout=30.0,
        input_cost=0.25,
        output_cost=1.25
    ),
]


class FallbackChain:
    """
    Multi-model fallback chain for resilient Claude API calls.

    Falls back to cheaper/faster models when primary fails.
    """

    def __init__(
        self,
        client,  # Anthropic client
        chain: Optional[List[ModelConfig]] = None,
        on_fallback: Optional[Callable[[str, str, Exception], None]] = None
    ):
        self.client = client
        self.chain = chain or DEFAULT_CHAIN
        self.on_fallback = on_fallback

    async def call(
        self,
        messages: List[Dict],
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> FallbackResult:
        """
        Make API call with automatic fallback.

        Tries each model in chain until one succeeds.
        """
        attempts = []

        for i, config in enumerate(self.chain):
            try:
                # Build request
                request = {
                    "model": config.model_id,
                    "messages": messages,
                    "max_tokens": max_tokens or config.max_tokens,
                    **kwargs
                }
                if system:
                    request["system"] = system

                # Make request with timeout
                response = await asyncio.wait_for(
                    self.client.messages.create(**request),
                    timeout=config.timeout
                )

                return FallbackResult(
                    response=response,
                    model_used=config.model_id,
                    tier_used=config.tier,
                    was_fallback=config.is_fallback,
                    attempts=attempts
                )

            except Exception as e:
                attempts.append({
                    "model": config.model_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                })

                # Check if we should try next model
                if not self._should_fallback(e):
                    raise

                # Notify callback
                if self.on_fallback and i + 1 < len(self.chain):
                    next_model = self.chain[i + 1].model_id
                    self.on_fallback(config.model_id, next_model, e)

        # All models failed
        raise FallbackExhausted(attempts)

    def _should_fallback(self, error: Exception) -> bool:
        """Determine if we should try the next model."""
        # Always fallback on these errors
        fallback_errors = [
            "rate_limit",
            "overloaded",
            "timeout",
            "service_unavailable",
        ]

        error_str = str(error).lower()
        return any(err in error_str for err in fallback_errors)


class FallbackExhausted(Exception):
    """All models in fallback chain failed."""
    def __init__(self, attempts: List[Dict]):
        self.attempts = attempts
        models = [a["model"] for a in attempts]
        super().__init__(f"All models failed: {models}")


# Convenience function
async def resilient_call(
    client,
    messages: List[Dict],
    system: Optional[str] = None,
    **kwargs
) -> FallbackResult:
    """Make a resilient API call with fallback chain."""
    chain = FallbackChain(client)
    return await chain.call(messages, system, **kwargs)
```

---

## Part 6: Complete Resilient Client

### 6.1 Integrated Client

```python
# resilience/client.py
import asyncio
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging

from .errors import ErrorClassifier, ErrorCategory
from .retry import RetryConfig, retry_async
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from .rate_limiter import AdaptiveRateLimiter, RateLimiterConfig
from .fallback import FallbackChain, FallbackResult, ModelConfig

logger = logging.getLogger(__name__)


@dataclass
class ResilientClientConfig:
    """Configuration for resilient Claude client."""
    # Retry settings
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0

    # Circuit breaker settings
    failure_threshold: int = 5
    circuit_timeout: float = 30.0

    # Rate limiting
    tokens_per_minute: int = 60000

    # Timeouts
    request_timeout: float = 120.0

    # Logging
    log_requests: bool = True
    log_errors: bool = True


class ResilientClaudeClient:
    """
    Production-grade Claude client with full resilience features.

    Features:
    - Automatic retry with exponential backoff
    - Circuit breaker for cascade failure prevention
    - Token bucket rate limiting
    - Multi-model fallback chain
    - Comprehensive error handling
    """

    def __init__(
        self,
        api_key: str,
        config: Optional[ResilientClientConfig] = None
    ):
        import anthropic
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.config = config or ResilientClientConfig()

        # Initialize components
        self.rate_limiter = AdaptiveRateLimiter(
            RateLimiterConfig(tokens_per_minute=self.config.tokens_per_minute)
        )

        self.circuit_breaker = CircuitBreaker(
            "claude-api",
            CircuitBreakerConfig(
                failure_threshold=self.config.failure_threshold,
                timeout=self.config.circuit_timeout
            ),
            on_state_change=self._on_circuit_state_change
        )

        self.retry_config = RetryConfig(
            max_attempts=self.config.max_retries,
            base_delay=self.config.base_delay,
            max_delay=self.config.max_delay
        )

        self.fallback_chain = FallbackChain(
            self.client,
            on_fallback=self._on_fallback
        )

        # Stats
        self.stats = {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "retries": 0,
            "fallbacks": 0,
            "rate_limited": 0,
            "circuit_opened": 0
        }

    async def chat(
        self,
        messages: List[Dict],
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        use_fallback: bool = True,
        **kwargs
    ) -> FallbackResult:
        """
        Make a resilient chat request.

        Args:
            messages: List of message dicts
            system: System prompt
            model: Model to use (or first in fallback chain)
            max_tokens: Maximum response tokens
            use_fallback: Whether to use fallback chain on failure

        Returns:
            FallbackResult with response and metadata
        """
        self.stats["requests"] += 1

        # Estimate tokens for rate limiting
        estimated_tokens = self._estimate_tokens(messages, system)

        # Wait for rate limit tokens
        await self.rate_limiter.acquire_async(estimated_tokens)

        try:
            # Use circuit breaker wrapped call
            result = await self._call_with_circuit_breaker(
                messages=messages,
                system=system,
                model=model,
                max_tokens=max_tokens,
                use_fallback=use_fallback,
                **kwargs
            )

            self.stats["successes"] += 1
            self.rate_limiter.on_success()

            return result

        except Exception as e:
            self.stats["failures"] += 1

            # Handle rate limiting
            classified = ErrorClassifier.classify(e)
            if classified.category == ErrorCategory.RATE_LIMITED:
                self.stats["rate_limited"] += 1
                self.rate_limiter.on_rate_limited()

            raise

    async def _call_with_circuit_breaker(self, **kwargs) -> FallbackResult:
        """Make request through circuit breaker."""
        use_fallback = kwargs.pop("use_fallback", True)

        @self.circuit_breaker
        async def _call():
            return await self._call_with_retry(**kwargs, use_fallback=use_fallback)

        return await _call()

    async def _call_with_retry(self, **kwargs) -> FallbackResult:
        """Make request with retry logic."""
        use_fallback = kwargs.pop("use_fallback", True)

        async def _do_call():
            if use_fallback:
                return await self.fallback_chain.call(**kwargs)
            else:
                response = await self.client.messages.create(**kwargs)
                return FallbackResult(
                    response=response,
                    model_used=kwargs.get("model", "unknown"),
                    tier_used=None,
                    was_fallback=False
                )

        return await retry_async(
            _do_call,
            config=self.retry_config,
            on_retry=self._on_retry
        )

    def _estimate_tokens(
        self,
        messages: List[Dict],
        system: Optional[str]
    ) -> int:
        """Estimate token count for rate limiting."""
        total_chars = sum(len(str(m.get("content", ""))) for m in messages)
        if system:
            total_chars += len(system)

        # Rough estimate: 4 chars per token
        return max(1, total_chars // 4)

    def _on_retry(self, attempt: int, error: Exception, wait: float):
        """Called on retry attempts."""
        self.stats["retries"] += 1
        if self.config.log_errors:
            logger.warning(
                f"Retry {attempt} after error: {error}. "
                f"Waiting {wait:.2f}s"
            )

    def _on_fallback(self, from_model: str, to_model: str, error: Exception):
        """Called on model fallback."""
        self.stats["fallbacks"] += 1
        if self.config.log_errors:
            logger.warning(
                f"Fallback from {from_model} to {to_model}: {error}"
            )

    def _on_circuit_state_change(self, old_state, new_state):
        """Called on circuit breaker state change."""
        if str(new_state) == "CircuitState.OPEN":
            self.stats["circuit_opened"] += 1

        logger.info(f"Circuit breaker: {old_state} -> {new_state}")

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            **self.stats,
            "circuit_state": str(self.circuit_breaker.state),
            "rate_limiter_tokens": self.rate_limiter.available_tokens,
            "success_rate": (
                self.stats["successes"] / max(1, self.stats["requests"]) * 100
            )
        }
```

---

## Part 7: Decision Framework

### When to Use Each Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                RESILIENCE PATTERN SELECTION                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Scenario                    Pattern                         │
│  ─────────────────────────   ───────────────────────────    │
│                                                              │
│  Occasional failures         → Retry with backoff           │
│  (transient errors)            (3-5 attempts)               │
│                                                              │
│  Burst traffic              → Token bucket rate limiter     │
│  (need to smooth requests)    (match API tier limits)       │
│                                                              │
│  Downstream dependency      → Circuit breaker               │
│  (prevent cascade)            (5 failures → 30s open)       │
│                                                              │
│  Quality vs availability    → Multi-model fallback          │
│  (degrade gracefully)         (Opus → Sonnet → Haiku)       │
│                                                              │
│  Production system          → ALL OF THE ABOVE              │
│  (maximum resilience)         (ResilientClaudeClient)       │
│                                                              │
│                                                              │
│  COMBINATION MATRIX:                                         │
│  ──────────────────                                          │
│                                                              │
│  Development     │ Retry only (simple)                      │
│  Staging         │ Retry + Rate Limit                       │
│  Production      │ Retry + Rate Limit + Circuit + Fallback  │
│  Critical Path   │ All + Custom monitoring + Alerting       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Checklist

### Error Handling
- [ ] Error classifier implemented
- [ ] Transient vs permanent errors distinguished
- [ ] Context overflow handling in place
- [ ] Rate limit detection working

### Retry Logic
- [ ] Exponential backoff implemented
- [ ] Jitter enabled to prevent thundering herd
- [ ] Max attempts configured appropriately
- [ ] Non-retryable errors bypass retry

### Circuit Breaker
- [ ] Failure threshold tuned for your traffic
- [ ] Recovery timeout appropriate
- [ ] Half-open testing configured
- [ ] State change logging enabled

### Rate Limiting
- [ ] Token bucket matches API tier
- [ ] Adaptive limiting responds to 429s
- [ ] Rate recovery on sustained success
- [ ] Burst capacity configured

### Multi-Model Fallback
- [ ] Fallback chain ordered by preference
- [ ] Fallback triggers identified
- [ ] Quality degradation acceptable
- [ ] Cost increase budgeted

### Monitoring
- [ ] Request/success/failure counts
- [ ] Retry and fallback rates
- [ ] Circuit breaker state tracking
- [ ] Rate limiter utilization

---

## Troubleshooting

### High Retry Rate

**Symptom**: >10% of requests retry

**Causes**:
1. Base delay too short → Increase to 2-5 seconds
2. Server instability → Check Anthropic status
3. Timeout too aggressive → Increase request timeout

### Circuit Keeps Opening

**Symptom**: Circuit breaker opens frequently

**Causes**:
1. Threshold too low → Increase failure_threshold
2. Window too short → Increase window_size
3. Real API issues → Check Anthropic status

### Rate Limited Despite Limiter

**Symptom**: Still getting 429s

**Causes**:
1. Token estimate too low → Improve estimation
2. Multiple clients → Share rate limiter
3. Burst too large → Reduce capacity

### All Fallbacks Failing

**Symptom**: FallbackExhausted errors

**Causes**:
1. API-wide outage → Check status, wait
2. Authentication issue → Verify API key
3. Bad request → Check message format

---

## Resources

### API Documentation
- [Claude API Error Codes](https://docs.anthropic.com/en/api/errors)
- [Rate Limits](https://docs.anthropic.com/en/api/rate-limits)
- [Model Comparison](https://docs.anthropic.com/en/docs/models)

### Patterns
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Token Bucket Algorithm](https://en.wikipedia.org/wiki/Token_bucket)
- [Exponential Backoff](https://en.wikipedia.org/wiki/Exponential_backoff)
