"""Arc — thread-safe reference-counted shared ownership.

``Arc[T]`` provides atomic reference counting so a single value can be
shared across multiple threads. Strong-reference and counter updates are
guarded by a lock, making ``clone`` and the destructor safe to call
concurrently.
"""

from __future__ import annotations

import threading
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class Arc(Generic[T]):
    """Thread-safe, atomically reference-counted shared ownership.

    Analogous to Rust's ``Arc``, this type lets multiple owners share one
    value across threads. Use :meth:`clone` to create additional strong
    references and :meth:`strong_count` to observe how many remain.

    Examples:
        >>> arc = Arc.new([1, 2])
        >>> other = arc.clone()
        >>> arc.strong_count()
        2
        >>> arc.as_ptr() == other.as_ptr()
        True
    """

    __slots__ = ("_inner", "_ref_count", "_lock")

    def __init__(self, value: T) -> None:
        """Construct a new Arc with the given value and a strong count of one.

        Args:
            value (T): The value to share across threads.
        """
        self._inner = value
        self._ref_count = 1
        self._lock = threading.Lock()

    @classmethod
    def new(cls, value: T) -> Arc[T]:
        """Create a new Arc with the given value and a reference count of one.

        Args:
            value (T): The value to share.

        Returns:
            Arc[T]: A new Arc owning ``value``.

        Examples:
            >>> arc = Arc.new(10)
            >>> arc.strong_count()
            1
        """
        return cls(value)

    def clone(self) -> Arc[T]:
        """Clone the Arc, atomically incrementing the reference count.

        Both the original and the returned clone share the same value; the
        value is only finalized when all strong references are dropped.

        Returns:
            Arc[T]: A new strong reference sharing the same value.

        Examples:
            >>> arc = Arc.new([1, 2])
            >>> other = arc.clone()
            >>> arc.strong_count()
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
        """Return the number of strong references to the value.

        Returns:
            int: The current strong reference count.
        """
        with self._lock:
            return self._ref_count

    def try_unwrap(self) -> T | None:
        """Attempt to extract the value if this is the only strong reference.

        Returns:
            T | None: The contained value if there are no other strong
                references, otherwise ``None``.

        Examples:
            >>> arc = Arc.new(5)
            >>> _ = arc.clone()
            >>> arc.try_unwrap() is None
            True
        """
        with self._lock:
            if self._ref_count == 1:
                return self._inner
        return None

    def as_ptr(self) -> int:
        """Return the identity of the contained value.

        Returns:
            int: The identity of the shared value (``id`` of the underlying
                object).
        """
        return id(self._inner)

    def into_inner(self) -> T:
        """Consume the Arc and return the contained value.

        Returns:
            T: The shared value handed back to the caller.
        """
        return self._inner

    def make_mut(self) -> T:
        """Return a mutable reference to the contained value.

        Returns:
            T: The contained value, viewed as mutable.
        """
        return self._inner

    def __enter__(self) -> Arc[T]:
        """Enter the context manager, returning self.

        Returns:
            Arc[T]: The Arc itself, ready for use inside the ``with`` block.
        """
        return self

    def __exit__(self, *_: Any) -> None:
        """Exit the context manager, performing no extra cleanup.

        Args:
            *_ (Any): The exception type, value, and traceback (if any), which
                are ignored.
        """
        pass

    def __del__(self) -> None:
        """Atomically decrement the reference count on destruction."""
        with self._lock:
            self._ref_count -= 1

    def __repr__(self) -> str:
        """Return a string representation including the reference count.

        Returns:
            str: A repr of the form ``Arc(<value>, strong=...)``.
        """
        return f"Arc({self._inner!r}, strong={self._ref_count})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another Arc by comparing the contained values.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: ``True`` if ``other`` is an ``Arc`` wrapping an equal value,
                otherwise ``NotImplemented``.
        """
        if isinstance(other, Arc):
            return self._inner == other._inner
        return NotImplemented

    def __hash__(self) -> int:
        """Return the hash of the contained value.

        Returns:
            int: The hash of the shared value.
        """
        return hash(self._inner)

    def __bool__(self) -> bool:
        """Return whether the Arc is truthy.

        An Arc is always truthy regardless of its contents.

        Returns:
            bool: Always ``True``.
        """
        return True