"""LRU (Least Recently Used) cache."""
from __future__ import annotations

from collections import OrderedDict
from typing import Any, Callable, Generic, Hashable, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class LRUCache(Generic[K, V]):
    """An LRU (Least Recently Used) cache with fixed capacity.

    When the cache reaches capacity and a new item is added, the least recently
    used item is evicted.
    """

    __slots__ = ("_data", "_capacity")

    def __init__(self, capacity: int = 128) -> None:
        if capacity < 0:
            raise ValueError("capacity must be non-negative")
        self._capacity = capacity
        self._data: OrderedDict[K, V] = OrderedDict()

    def get(self, key: K, default: V | None = None) -> V | None:
        if key not in self._data:
            return default
        # Move to end (most recently used)
        self._data.move_to_end(key)
        return self._data[key]

    def set(self, key: K, value: V) -> None:
        if key in self._data:
            self._data[key] = value
            self._data.move_to_end(key)
            return
        self._data[key] = value
        if self._capacity > 0 and len(self._data) > self._capacity:
            self._data.popitem(last=False)

    def __setitem__(self, key: K, value: V) -> None:
        self.set(key, value)

    def __getitem__(self, key: K) -> V:
        if key not in self._data:
            raise KeyError(key)
        self._data.move_to_end(key)
        return self._data[key]

    def __contains__(self, key: K) -> bool:
        return key in self._data

    def __len__(self) -> int:
        return len(self._data)

    def clear(self) -> None:
        self._data.clear()

    def pop(self, key: K, default: V | None = None) -> V | None:
        return self._data.pop(key, default)

    def items(self):
        return list(self._data.items())
