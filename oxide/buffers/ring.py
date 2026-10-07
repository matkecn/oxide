"""Ring buffer implementation."""
from __future__ import annotations

from collections import deque
from typing import Generic, TypeVar

T = TypeVar("T")


class RingBuffer(Generic[T]):
    """A fixed-size ring buffer."""

    __slots__ = ("_data", "_capacity")

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self._capacity = capacity
        self._data: deque[T] = deque(maxlen=capacity)

    def push(self, value: T) -> None:
        self._data.append(value)

    def pop(self) -> T:
        if not self._data:
            raise IndexError("pop from empty ring buffer")
        return self._data.popleft()

    def peek(self) -> T | None:
        if not self._data:
            return None
        return self._data[0]

    def is_full(self) -> bool:
        return len(self._data) == self._capacity

    def is_empty(self) -> bool:
        return len(self._data) == 0

    def __len__(self) -> int:
        return len(self._data)

    def clear(self) -> None:
        self._data.clear()
