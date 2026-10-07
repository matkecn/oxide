"""LFU (Least Frequently Used) cache."""
from __future__ import annotations

from collections import defaultdict
from typing import Generic, Hashable, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class LFUCache(Generic[K, V]):
    """A simple LFU cache implementation."""

    __slots__ = ("_data", "_freq", "_capacity", "_min_freq")

    def __init__(self, capacity: int = 128) -> None:
        if capacity < 0:
            raise ValueError("capacity must be non-negative")
        self._capacity = capacity
        self._data: dict[K, V] = {}
        self._freq: dict[K, int] = {}
        self._min_freq = 0

    def get(self, key: K, default: V | None = None) -> V | None:
        if key not in self._data:
            return default
        self._freq[key] = self._freq.get(key, 0) + 1
        return self._data[key]

    def set(self, key: K, value: V) -> None:
        if self._capacity == 0:
            return
        if key in self._data:
            self._data[key] = value
            self._freq[key] = self._freq.get(key, 0) + 1
            return
        if len(self._data) >= self._capacity:
            # Evict least frequently used
            lfu_keys = [k for k, f in self._freq.items() if f == min(self._freq.values())]
            evict = lfu_keys[0] if lfu_keys else next(iter(self._data))
            self._data.pop(evict, None)
            self._freq.pop(evict, None)
        self._data[key] = value
        self._freq[key] = 1

    def __contains__(self, key: K) -> bool:
        return key in self._data

    def __len__(self) -> int:
        return len(self._data)
