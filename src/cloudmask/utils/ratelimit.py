"""Rate limiting for CloudMask operations."""

import time
from collections import deque
from typing import Any


class RateLimiter:
    """Simple token bucket rate limiter."""

    def __init__(self, max_operations: int, time_window: float = 1.0):
        """Initialize rate limiter.

        Args:
            max_operations: Maximum operations allowed in time window
            time_window: Time window in seconds
        """
        self.max_operations = max_operations
        self.time_window = time_window
        self.operations: deque[float] = deque()

    def acquire(self) -> bool:
        """Attempt to acquire permission for an operation.

        Returns:
            True if operation is allowed, False if rate limit exceeded
        """
        now = time.time()

        # Remove old operations outside time window
        while self.operations and self.operations[0] < now - self.time_window:
            self.operations.popleft()

        # Check if we can perform operation
        if len(self.operations) < self.max_operations:
            self.operations.append(now)
            return True

        return False

    def wait(self) -> None:
        """Wait until operation is allowed."""
        while not self.acquire():
            time.sleep(0.01)


class BatchRateLimiter:
    """Rate limiter for batch operations."""

    def __init__(self, max_items_per_second: int = 1000):
        """Initialize batch rate limiter.

        Args:
            max_items_per_second: Maximum items to process per second
        """
        self.limiter = RateLimiter(max_items_per_second, 1.0)

    def process_batch(self, items: list[Any], processor: Any) -> list[Any]:
        """Process items with rate limiting.

        Args:
            items: Items to process
            processor: Function to process each item

        Returns:
            List of processed items
        """
        results = []
        for item in items:
            self.limiter.wait()
            results.append(processor(item))
        return results
