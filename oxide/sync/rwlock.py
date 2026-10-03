"""RwLock — readers-writer lock with read/write guards."""
from __future__ import annotations
"""RwLock — readers-writer lock.

Provides RwLock[T] with RwLockReadGuard and RwLockWriteGuard for
concurrent reads with exclusive writes.
"""

import threading
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class RwLockReadGuard(Generic[T]):
    """RAII guard for holding a read lock on a RwLock."""

    __slots__ = ("_lock",)

    def __init__(self, lock: RwLock) -> None:
        self._lock = lock

    @property
    def value(self) -> Any:
        """Return the protected value."""
        return self._lock._value

    def release(self) -> None:
        """Release the read lock."""
        self._lock._readers -= 1

    def __enter__(self) -> RwLockReadGuard[T]:
        return self

    def __exit__(self, *_: Any) -> None:
        self.release()

    def __repr__(self) -> str:
        return f"RwLockReadGuard({self._lock._value!r})"


class RwLockWriteGuard(Generic[T]):
    """RAII guard for holding an exclusive write lock on a RwLock."""

    __slots__ = ("_lock",)

    def __init__(self, lock: RwLock) -> None:
        self._lock = lock

    @property
    def value(self) -> Any:
        """Return the protected value."""
        return self._lock._value

    @value.setter
    def value(self, v: Any) -> None:
        """Set the protected value."""
        self._lock._value = v

    def replace(self, v: Any) -> Any:
        """Replace the protected value and return the old one."""
        old = self._lock._value
        self._lock._value = v
        return old

    def release(self) -> None:
        """Release the write lock."""
        self._lock._writing = False
        self._lock._write_lock.release()

    def __enter__(self) -> RwLockWriteGuard[T]:
        return self

    def __exit__(self, *_: Any) -> None:
        self.release()

    def __repr__(self) -> str:
        return f"RwLockWriteGuard({self._lock._value!r})"


class RwLock(Generic[T]):
    """Readers-writer lock allowing concurrent reads and exclusive writes."""

    __slots__ = ("_value", "_readers", "_writing", "_read_lock", "_write_lock", "_cond")

    def __init__(self, value: T) -> None:
        self._value = value
        self._readers = 0
        self._writing = False
        self._read_lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._cond = threading.Condition(threading.Lock())

    @classmethod
    def new(cls, value: T) -> RwLock[T]:
        """Create a new RwLock wrapping the given value."""
        return cls(value)

    def read(self) -> RwLockReadGuard[T]:
        """Acquire a read lock, blocking until no writers are active."""
        with self._cond:
            while self._writing:
                self._cond.wait()
            self._readers += 1
        return RwLockReadGuard(self)

    def write(self) -> RwLockWriteGuard[T]:
        """Acquire an exclusive write lock, blocking until all readers and writers are done."""
        self._write_lock.acquire()
        with self._cond:
            while self._writing or self._readers > 0:
                self._cond.wait()
            self._writing = True
        return RwLockWriteGuard(self)

    def try_read(self) -> RwLockReadGuard[T] | None:
        """Attempt to acquire a read lock without blocking. Returns None if a write is active."""
        with self._cond:
            if not self._writing:
                self._readers += 1
                return RwLockReadGuard(self)
        return None

    def try_write(self) -> RwLockWriteGuard[T] | None:
        """Attempt to acquire a write lock without blocking. Returns None if unavailable."""
        if self._write_lock.acquire(blocking=False):
            with self._cond:
                if not self._writing and self._readers == 0:
                    self._writing = True
                    return RwLockWriteGuard(self)
            self._write_lock.release()
        return None

    def into_inner(self) -> T:
        """Consume the RwLock and return the inner value."""
        return self._value

    def __repr__(self) -> str:
        return f"RwLock({self._value!r})"
