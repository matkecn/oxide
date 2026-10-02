"""Thread-safe reference-counted smart pointer for shared ownership across threads."""

from __future__ import annotations

import threading
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class Arc(Generic[T]):
    """Thread-safe, reference-counted smart pointer for shared ownership of a value.

    Multiple Arc instances can share the same underlying value without copying it.
    The value is kept alive for as long as at least one Arc reference remains.
    The reference count is protected by a lock, making this safe to share across
    threads.

    Examples:
        >>> import threading
        >>> from oxide.sync import Arc
        >>> arc = Arc.new([1, 2, 3])
        >>> clones = [arc.clone() for _ in range(4)]
        >>> arc.strong_count()
        5
    """

    __slots__ = ("_inner", "_ref_count", "_lock")

    def __init__(self, value: T) -> None:
        self._inner = value
        self._ref_count = 1
        self._lock = threading.Lock()

    @classmethod
    def new(cls, value: T) -> Arc[T]:
        """Create a new Arc wrapping the given value.

        Args:
            value: The value to wrap.

        Returns:
            A new Arc with a reference count of one.

        Examples:
            >>> from oxide.sync import Arc
            >>> arc = Arc.new("hello")
        """
        return cls(value)

    def clone(self) -> Arc[T]:
        """Create a new Arc sharing the same inner value.

        The reference count is incremented, and the new Arc points to the same
        underlying value. No copy of the value is made.

        Returns:
            A new Arc sharing the same inner value.

        Examples:
            >>> from oxide.sync import Arc
            >>> original = Arc.new("shared")
            >>> clone = original.clone()
            >>> original.strong_count()
            2
        """
        with self._lock:
            self._ref_count += 1
        return Arc._from_raw(self._inner, self._ref_count, self._lock)

    @classmethod
    def _from_raw(cls, value: T, ref_count: int, lock: threading.Lock) -> Arc[T]:
        arc = cls.__new__(cls)
        arc._inner = value
        arc._ref_count = ref_count
        arc._lock = lock
        return arc

    def strong_count(self) -> int:
        """Return the current number of strong references to the inner value.

        Returns:
            The number of live Arc instances sharing this value.
        """
        with self._lock:
            return self._ref_count

    def try_unwrap(self) -> T | None:
        """Take ownership of the inner value if no other references exist.

        This only succeeds when this is the sole remaining reference. Otherwise
        the Arc is left untouched and None is returned.

        Returns:
            The inner value if this is the last reference, else None.
        """
        with self._lock:
            if self._ref_count == 1:
                return self._inner
        return None

    def as_ptr(self) -> int:
        """Return the identity (id) of the inner value as a pointer-like reference.

        Returns:
            The object identity of the wrapped value.
        """
        return id(self._inner)

    def into_inner(self) -> T:
        """Return the underlying value, ignoring reference counting.

        Note:
            This does not decrement the reference count; it simply exposes the
            wrapped value directly.

        Returns:
            The wrapped inner value.
        """
        return self._inner

    def make_mut(self) -> T:
        """Return a reference to the inner value for mutation (no cloning occurs).

        Note:
            Unlike the Rust standard library, this does not guarantee uniqueness
            and performs no copy-on-write. Mutating the returned value affects all
            Arcs sharing it.

        Returns:
            The wrapped inner value.
        """
        return self._inner

    def __enter__(self) -> Arc[T]:
        """Enter the context manager protocol, returning this Arc unchanged."""
        return self

    def __exit__(self, *_: Any) -> None:
        """Exit the context manager protocol without taking additional action."""

    def __del__(self) -> None:
        """Decrement the reference count when the Arc is garbage-collected."""
        with self._lock:
            self._ref_count -= 1

    def __repr__(self) -> str:
        return f"Arc({self._inner!r}, strong={self._ref_count})"

    def __eq__(self, other: object) -> bool:
        """Return True if the other object wraps an equal inner value."""
        if isinstance(other, Arc):
            return self._inner == other._inner
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._inner)

    def __bool__(self) -> bool:
        return True
