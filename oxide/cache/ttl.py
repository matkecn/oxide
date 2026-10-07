"""TTL (Time To Live) cache."""
from __future__ import annotations

import time
from typing import Generic, Hashable, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class TTLCache(Generic[K, V]):
    """A TTL cache that expires items after a given time."""

    __slots__ = ("_data", "_expiry", "_ttl", "_capacity")

    def __init__(self, capacity: int = 128, ttl: float = 60.0) -> None:
        if capacity < 0:
            raise ValueError("capacity must be non-negative")
        self._capacity = capacity
        self._ttl = ttl
        self._data: dict[K, V] = {}
        self._expiry: dict[K, float] = {}

    def _clean_expired(self) -> None:
        now = time.time()
        expired = [k for k, exp in self._expiry.items() if exp <= now]
        for k in expired:
            self._data.pop(k, None)
            self._expiry.pop(k, None)

    def get(self, key: K, default: V | None = None) -> V | None:
        self._clean_expired()
        return self._data.get(key, default)

    def set(self, key: K, value: V, ttl: float | None = None) -> None:
        self._clean_expired()
        if self._capacity == 0:
            return
        if len(self._data) >= self._capacity and key not in self._data:
            # Simple eviction: remove oldest expired or first
            if self._expiry:
                # Remove item with earliest expiry
                oldest = min(self._expiry, key=self._expiry.get)
                self._data.pop(oldest, None)
                self._expiry.pop(oldest, None)
        self._data[key] = value
        self._expiry[key] = time.time() + (ttl if ttl is not None else self._ttl)

    def __contains__(self, key: K) -> bool:
        self._clean_expired()
        return key in self._data

    def __len__(self) -> int:
        self._clean_expired()
        return len(self._data)
