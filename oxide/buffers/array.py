"""Fixed-size array wrapper."""
from __future__ import annotations

from typing import Generic, Iterable, TypeVar

T = TypeVar("T")


class Array(Generic[T]):
    """A fixed-size array."""

    __slots__ = ("_data", "_size")

    def __init__(self, size: int, default: T | None = None) -> None:
        if size < 0:
            raise ValueError("size must be non-negative")
        self._size = size
        self._data = [default] * size

    def __len__(self) -> int:
        return self._size

    def __getitem__(self, index: int) -> T:
        return self._data[index]

    def __setitem__(self, index: int, value: T) -> None:
        self._data[index] = value

    def __iter__(self):
        return iter(self._data)
