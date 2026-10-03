"""Semaphore — counting semaphore for concurrency limiting."""
from __future__ import annotations
"""Semaphore — counting semaphore.

Provides Semaphore for limiting concurrent access to a resource
with acquire, release, and context manager support.
"""

import threading
from typing import Any


class Semaphore:
    """Counting semaphore for limiting concurrent access to a resource."""

    __slots__ = ("_semaphore", "_max")

    def __init__(self, max_permits: int) -> None:
        if max_permits <= 0:
            raise ValueError("max_permits must be positive")
        self._semaphore = threading.Semaphore(max_permits)
        self._max = max_permits

    @classmethod
    def new(cls, max_permits: int) -> Semaphore:
        """Create a new Semaphore with the specified maximum permits."""
        return cls(max_permits)

    def acquire(self, blocking: bool = True, timeout: float | None = None) -> bool:
        """Acquire a permit, optionally blocking with a timeout. Returns True on success."""
        return self._semaphore.acquire(blocking=blocking, timeout=timeout)

    def release(self) -> None:
        """Release a permit back to the semaphore."""
        self._semaphore.release()

    def available(self) -> int:
        """Return the number of currently available permits."""
        return self._semaphore._value  # type: ignore

    @property
    def max_permits(self) -> int:
        """Return the maximum number of permits."""
        return self._max

    def __enter__(self) -> Semaphore:
        self.acquire()
        return self

    def __exit__(self, *_: Any) -> None:
        self.release()

    def __repr__(self) -> str:
        return f"Semaphore(max={self._max})"
