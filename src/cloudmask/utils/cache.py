"""Caching utilities for performance optimization."""

import functools
from collections import OrderedDict
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class LRUCache:
    """Simple LRU cache for pattern matching results."""

    def __init__(self, maxsize: int = 1000):
        """Initialize LRU cache.

        Args:
            maxsize: Maximum number of items to cache
        """
        self.cache: OrderedDict[str, str] = OrderedDict()
        self.maxsize = maxsize

    def get(self, key: str) -> str | None:
        """Get value from cache, moving to end if found."""
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key: str, value: str) -> None:
        """Put value in cache, evicting oldest if full."""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.maxsize:
                self.cache.popitem(last=False)
        self.cache[key] = value

    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()

    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)


def memoize(maxsize: int = 128) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Memoization decorator with LRU eviction.

    Args:
        maxsize: Maximum cache size

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache: OrderedDict[tuple[Any, ...], T] = OrderedDict()

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Create cache key from args and kwargs
            key = (args, tuple(sorted(kwargs.items())))

            if key in cache:
                cache.move_to_end(key)
                return cache[key]

            result = func(*args, **kwargs)

            if len(cache) >= maxsize:
                cache.popitem(last=False)

            cache[key] = result
            return result

        wrapper.cache_clear = cache.clear  # type: ignore
        wrapper.cache_info = lambda: {"size": len(cache), "maxsize": maxsize}  # type: ignore

        return wrapper

    return decorator
