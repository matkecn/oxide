"""C/FFI inspired utilities."""
from __future__ import annotations

from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")

class Ptr(Generic[T]):
    def __init__(self, obj: T = None):
        self._obj = obj
    def get(self) -> T:
        return self._obj
    def set(self, obj: T):
        self._obj = obj
    @property
    def value(self):
        return self._obj

class Struct:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class FunctionPtr:
    def __init__(self, func: Callable):
        self._func = func
    def __call__(self, *a, **kw):
        return self._func(*a, **kw)

class Bits:
    def __init__(self, value: int = 0):
        self.value = value & ((1 << 64) - 1) if False else value
    def set(self, pos: int):
        self.value |= (1 << pos)
    def clear(self, pos: int):
        self.value &= ~(1 << pos)
    def test(self, pos: int):
        return bool(self.value & (1 << pos))

bits = Bits

alloc = lambda size: bytearray(size)
memory = type('memory', (), {
    'copy': lambda dst, src, n=None: (dst.__setitem__(slice(0,n or len(src)), src[:n or len(src)])) if hasattr(dst, '__setitem__') else None,
    'move': lambda dst, src, n=None: (dst.__setitem__(slice(0,n or len(src)), src[:n or len(src)])),
})()

def simd_add(a, b):
    try:
        return a + b
    except Exception:
        return [x+y for x,y in zip(a,b)]

simd = type('simd', (), {'add': simd_add})()

ffi = type('ffi', (), {'cdef': lambda *a,**kw: None})()

class mmap:
    def __init__(self, *a, **kw):
        pass

__all__ = ["Ptr", "Struct", "FunctionPtr", "Bits", "bits", "alloc", "memory", "simd", "ffi", "mmap"]
