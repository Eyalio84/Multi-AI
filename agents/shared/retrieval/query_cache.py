#!/usr/bin/env python3
"""
Query Cache — Unified Retrieval Layer

LRU + TTL query result cache adapted from eco-system unified_retriever.py.
OrderedDict-based with MD5 key generation and metrics tracking.

Level 0 dependency — no internal imports.

Created: February 8, 2026
"""

import hashlib
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Optional, Dict


@dataclass
class CacheMetrics:
    """Track cache performance."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "expirations": self.expirations,
            "hit_rate": round(self.hit_rate, 4),
            "total_queries": self.hits + self.misses,
        }


@dataclass
class CacheEntry:
    """Single cached result with timestamp."""
    value: Any
    timestamp: float
    access_count: int = 0


class QueryCache:
    """LRU + TTL cache for retrieval query results.

    Features:
        - OrderedDict-based LRU eviction
        - Timestamp-based TTL expiration
        - MD5 key generation from query + parameters
        - Metrics tracking (hits, misses, evictions)

    Adapted from eco-system unified_retriever.py QueryCache.
    """

    def __init__(self, maxsize: int = 500, ttl_seconds: int = 600):
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.metrics = CacheMetrics()

    @staticmethod
    def _make_key(query: str, **params) -> str:
        """Generate deterministic cache key from query + params."""
        raw = f"{query}|{sorted(params.items())}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, query: str, **params) -> Optional[Any]:
        """Retrieve cached result, or None if miss/expired."""
        key = self._make_key(query, **params)

        if key not in self._cache:
            self.metrics.misses += 1
            return None

        entry = self._cache[key]

        # Check TTL expiration
        if time.time() - entry.timestamp > self.ttl_seconds:
            del self._cache[key]
            self.metrics.expirations += 1
            self.metrics.misses += 1
            return None

        # LRU: move to end
        self._cache.move_to_end(key)
        entry.access_count += 1
        self.metrics.hits += 1
        return entry.value

    def put(self, query: str, value: Any, **params) -> None:
        """Store result in cache with LRU eviction."""
        key = self._make_key(query, **params)

        # Update existing
        if key in self._cache:
            self._cache[key] = CacheEntry(value=value, timestamp=time.time())
            self._cache.move_to_end(key)
            return

        # Evict LRU if at capacity
        while len(self._cache) >= self.maxsize:
            self._cache.popitem(last=False)
            self.metrics.evictions += 1

        self._cache[key] = CacheEntry(value=value, timestamp=time.time())

    def invalidate(self, query: str, **params) -> bool:
        """Remove specific entry. Returns True if existed."""
        key = self._make_key(query, **params)
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> int:
        """Clear all entries. Returns count cleared."""
        count = len(self._cache)
        self._cache.clear()
        return count

    def __len__(self) -> int:
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        return key in self._cache


# ============================================================================
# Self-test
# ============================================================================

if __name__ == "__main__":
    cache = QueryCache(maxsize=3, ttl_seconds=2)

    # Basic put/get
    cache.put("test query", [{"result": 1}], k=10)
    result = cache.get("test query", k=10)
    assert result == [{"result": 1}], f"Expected result, got {result}"
    assert cache.metrics.hits == 1

    # Miss
    result2 = cache.get("nonexistent")
    assert result2 is None
    assert cache.metrics.misses == 1

    # LRU eviction
    cache.put("q1", "r1")
    cache.put("q2", "r2")
    cache.put("q3", "r3")  # This should evict "test query" (maxsize=3)
    assert len(cache) == 3
    assert cache.get("test query", k=10) is None
    assert cache.metrics.evictions >= 1

    # TTL expiration
    cache_ttl = QueryCache(maxsize=10, ttl_seconds=0)  # 0-second TTL
    cache_ttl.put("expire me", "value")
    time.sleep(0.01)
    assert cache_ttl.get("expire me") is None
    assert cache_ttl.metrics.expirations == 1

    # Invalidation
    cache.put("to_remove", "data")
    assert cache.invalidate("to_remove") is True
    assert cache.invalidate("to_remove") is False

    print(f"query_cache.py OK: metrics={cache.metrics.to_dict()}")
    print(f"  LRU eviction: working")
    print(f"  TTL expiration: working")
    print(f"  Invalidation: working")
