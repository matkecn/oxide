"""Memory utilities (C-style)."""
from __future__ import annotations

import sys

def size_of(obj: object) -> int:
    return sys.getsizeof(obj)

def memcpy(dst: bytearray, src: bytes, n: int | None = None) -> None:
    if n is None:
        n = len(src)
    dst[:n] = src[:n]

def memset(dst: bytearray, value: int, n: int | None = None) -> None:
    if n is None:
        n = len(dst)
    for i in range(n):
        dst[i] = value % 256

__all__ = ["size_of", "memcpy", "memset"]
