"""Once — execute a function exactly once across threads."""
from __future__ import annotations
"""Once — execute a function exactly once.

Provides Once for one-time initialization that is safe across threads.
"""

import threading
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class Once:
    """Ensures a function is executed exactly once, thread-safely."""

    __slots__ = ("_executed", "_lock", "_result")

    def __init__(self) -> None:
        self._executed = False
        self._lock = threading.Lock()
        self._result: Any = None

    @classmethod
    def new(cls) -> Once:
        """Create a new Once instance."""
        return cls()

    def call_once(self, fn: Callable[[], T]) -> T:
        """Execute fn exactly once and cache the result. Subsequent calls return the cached value."""
        if self._executed:
            return self._result
        with self._lock:
            if not self._executed:
                self._result = fn()
                self._executed = True
        return self._result

    def is_completed(self) -> bool:
        """Return whether the function has already been executed."""
        return self._executed

    def __repr__(self) -> str:
        return f"Once(completed={self._executed})"
