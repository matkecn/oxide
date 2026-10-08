"""C++ inspired utilities."""
from __future__ import annotations

from typing import Any, Generic, TypeVar

T = TypeVar("T")

class Resource:
    def __init__(self):
        self.acquired = True
    def release(self):
        self.acquired = False
    def __enter__(self):
        return self
    def __exit__(self, *a):
        self.release()

class Shared(Generic[T]):
    def __init__(self, obj: T):
        self._obj = obj

class Weak(Generic[T]):
    def __init__(self, shared: Shared[T]):
        self._shared = shared
    def lock(self):
        return self._shared

def move(obj: T) -> T:
    return obj

class Variant:
    def __init__(self, value: Any = None):
        self.value = value

from ..core.option import Option
from ..core.result import Result
from ..memory.box import Box
Optional = Option
Expected = Result

class Span(Generic[T]):
    def __init__(self, data: list[T]):
        self._data = data
    def __getitem__(self, i):
        return self._data[i]
    def __len__(self):
        return len(self._data)

class Pool:
    def __init__(self, factory=None):
        self._factory = factory or (lambda: object())
    def acquire(self):
        return self._factory()
    def release(self, item):
        pass

class Allocator:
    pass

class Iterator:
    pass

Vector = list
Deque = list
HashMap = dict
HashSet = set

__all__ = ["Resource", "Shared", "Weak", "move", "Optional", "Variant", "Expected", "Span", "Pool", "Allocator", "Iterator", "Box", "Vector", "Deque", "HashMap", "HashSet"]
