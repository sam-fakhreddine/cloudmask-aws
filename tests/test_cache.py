"""Tests for caching functionality."""

from cloudmask.utils.cache import LRUCache, memoize


class TestLRUCache:
    """Test LRU cache implementation."""

    def test_basic_operations(self):
        """Test basic cache operations."""
        cache = LRUCache(maxsize=3)

        cache.put("a", "1")
        cache.put("b", "2")
        cache.put("c", "3")

        assert cache.get("a") == "1"
        assert cache.get("b") == "2"
        assert cache.get("c") == "3"
        assert cache.size() == 3

    def test_eviction(self):
        """Test LRU eviction."""
        cache = LRUCache(maxsize=2)

        cache.put("a", "1")
        cache.put("b", "2")
        cache.put("c", "3")  # Should evict "a"

        assert cache.get("a") is None
        assert cache.get("b") == "2"
        assert cache.get("c") == "3"
        assert cache.size() == 2

    def test_lru_ordering(self):
        """Test that least recently used items are evicted."""
        cache = LRUCache(maxsize=2)

        cache.put("a", "1")
        cache.put("b", "2")
        cache.get("a")  # Access "a" to make it more recent
        cache.put("c", "3")  # Should evict "b"

        assert cache.get("a") == "1"
        assert cache.get("b") is None
        assert cache.get("c") == "3"

    def test_update_existing(self):
        """Test updating existing key."""
        cache = LRUCache(maxsize=2)

        cache.put("a", "1")
        cache.put("a", "2")  # Update

        assert cache.get("a") == "2"
        assert cache.size() == 1

    def test_clear(self):
        """Test cache clearing."""
        cache = LRUCache(maxsize=3)

        cache.put("a", "1")
        cache.put("b", "2")
        cache.clear()

        assert cache.get("a") is None
        assert cache.size() == 0


class TestMemoize:
    """Test memoization decorator."""

    def test_basic_memoization(self):
        """Test basic memoization."""
        call_count = 0

        @memoize(maxsize=10)
        def expensive_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        assert expensive_func(5) == 10
        assert expensive_func(5) == 10  # Should use cache
        assert call_count == 1

    def test_different_args(self):
        """Test memoization with different arguments."""
        call_count = 0

        @memoize(maxsize=10)
        def func(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        assert func(1, 2) == 3
        assert func(2, 3) == 5
        assert func(1, 2) == 3  # Should use cache
        assert call_count == 2

    def test_kwargs_memoization(self):
        """Test memoization with keyword arguments."""
        call_count = 0

        @memoize(maxsize=10)
        def func(x, y=0):
            nonlocal call_count
            call_count += 1
            return x + y

        assert func(1, y=2) == 3
        assert func(1, y=2) == 3  # Should use cache
        assert call_count == 1

    def test_cache_eviction(self):
        """Test cache eviction in memoization."""
        call_count = 0

        @memoize(maxsize=2)
        def func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        func(1)
        func(2)
        func(3)  # Should evict func(1)
        func(1)  # Should recompute

        assert call_count == 4

    def test_cache_info(self):
        """Test cache info."""

        @memoize(maxsize=5)
        def func(x: int) -> int:
            return x * 2

        func(1)
        func(2)

        info = func.cache_info()  # type: ignore[attr-defined]
        assert info["maxsize"] == 5
        assert info["size"] == 2

    def test_cache_clear(self):
        """Test cache clearing."""
        call_count = 0

        @memoize(maxsize=10)
        def func(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        func(1)
        func.cache_clear()  # type: ignore[attr-defined]
        func(1)  # Should recompute

        assert call_count == 2
