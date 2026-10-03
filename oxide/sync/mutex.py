"""Mutex — mutual exclusion lock with MutexGuard."""
from __future__ import annotations
"""Mutex — mutual exclusion lock.

Provides Mutex[T] with MutexGuard for protecting shared data across threads.
Supports lock, try_lock, and context manager protocols.
"""

import threading
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class MutexPoisoned(Exception):
    """Raised when attempting to lock a poisoned mutex."""

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("mutex is poisoned")


class MutexLock:
    """Context manager that acquires a mutex on enter and releases on exit."""

    __slots__ = ("_mutex", "_guard")

    def __init__(self, mutex: Mutex) -> None:
        self._mutex = mutex
        self._guard = None

    def __enter__(self) -> Any:
        self._guard = self._mutex.lock()
        return self._guard

    def __exit__(self, *_: Any) -> None:
        if self._guard is not None:
            self._guard.release()
            self._guard = None


class MutexGuard:
    """RAII guard providing protected access to a mutex's inner value."""

    __slots__ = ("_mutex",)

    def __init__(self, mutex: Mutex) -> None:
        self._mutex = mutex

    @property
    def value(self) -> Any:
        """Return the protected value."""
        return self._mutex._value

    @value.setter
    def value(self, v: Any) -> None:
        """Set the protected value."""
        self._mutex._value = v

    def replace(self, v: Any) -> Any:
        """Replace the protected value and return the old one."""
        old = self._mutex._value
        self._mutex._value = v
        return old

    def swap(self, other: Mutex) -> None:
        """Swap the protected value with another mutex's value."""
        self._mutex._value, other._value = other._value, self._mutex._value

    def into_inner(self) -> Any:
        """Consume the guard and return the protected value."""
        return self._mutex._value

    def release(self) -> None:
        """Release the underlying mutex lock."""
        self._mutex._lock.release()

    def __repr__(self) -> str:
        return f"MutexGuard({self._mutex._value!r})"


class Mutex(Generic[T]):
    """Mutual exclusion lock protecting a shared value with poisoning support."""

    __slots__ = ("_value", "_lock", "_poisoned")

    def __init__(self, value: T) -> None:
        self._value = value
        self._lock = threading.Lock()
        self._poisoned = False

    @classmethod
    def new(cls, value: T) -> Mutex[T]:
        """Create a new Mutex wrapping the given value."""
        return cls(value)

    def lock(self) -> MutexGuard:
        """Acquire the mutex and return a guard for protected access."""
        if self._poisoned:
            raise MutexPoisoned()
        self._lock.acquire()
        return MutexGuard(self)

    def try_lock(self) -> MutexGuard | None:
        """Attempt to acquire the mutex without blocking. Returns None if unavailable."""
        if self._poisoned:
            raise MutexPoisoned()
        acquired = self._lock.acquire(blocking=False)
        if acquired:
            return MutexGuard(self)
        return None

    def into_inner(self) -> T:
        """Consume the mutex and return the inner value."""
        return self._value

    def is_poisoned(self) -> bool:
        """Return whether the mutex has been poisoned."""
        return self._poisoned

    def poison(self) -> None:
        """Mark the mutex as poisoned, preventing further locks."""
        self._poisoned = True

    def clear_poison(self) -> None:
        """Clear the poisoned state, allowing locks again."""
        self._poisoned = False

    def __enter__(self) -> MutexGuard:
        return self.lock()

    def __exit__(self, *_: Any) -> None:
        self._lock.release()

    def __repr__(self) -> str:
        return f"Mutex({self._value!r})"
