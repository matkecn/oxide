"""Pointer utilities."""
from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")

class Ptr(Generic[T]):
    def __init__(self, obj: T):
        self._obj = obj
    def get(self) -> T:
        return self._obj
    def set(self, obj: T) -> None:
        self._obj = obj
    def deref(self) -> T:
        return self._obj

class Box(Generic[T]):
    def __init__(self, obj: T):
        self._obj = obj
    def get(self) -> T:
        return self._obj
    def __enter__(self):
        return self._obj
    def __exit__(self, *args):
        pass

__all__ = ["Ptr", "Box"]
