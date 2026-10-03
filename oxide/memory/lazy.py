"""Lazy — deferred computation, evaluated on first access.

``Lazy[T]`` wraps a zero-argument callable and evaluates it only the first
time the value is needed, caching the result for every later access. The
initialization is guarded by a lock, so concurrent forcing computes the
value exactly once.
"""

from __future__ import annotations

import threading
from typing import Callable, Generic, Iterator, TypeVar

T = TypeVar("T")


class Lazy(Generic[T]):
    """A lazily computed value that is evaluated on first access.

    Analogous to Rust's ``Lazy``, the computation function is stored without
    being run and is invoked by :meth:`force` on the first access. Subsequent
    reads return the cached result.

    Examples:
        >>> lazy = Lazy.new(lambda: 1 + 2)
        >>> lazy.is_forced()
        False
        >>> lazy.force()
        3
        >>> lazy.is_forced()
        True
    """

    __slots__ = ("_fn", "_value", "_computed", "_lock")

    def __init__(self, fn: Callable[[], T]) -> None:
        """Construct a new lazy value from the given computation function.

        Args:
            fn (Callable[[], T]): A zero-argument callable computing the
                value on first access.
        """
        self._fn = fn
        self._value: T = None  # type: ignore[assignment]
        self._computed = False
        self._lock = threading.Lock()

    @classmethod
    def new(cls, fn: Callable[[], T]) -> Lazy[T]:
        """Create a new lazy value with the given computation function.

        Args:
            fn (Callable[[], T]): A zero-argument callable computing the
                value on first access.

        Returns:
            Lazy[T]: A new lazy value.

        Examples:
            >>> lazy = Lazy.new(lambda: [1, 2])
            >>> lazy.force()
            [1, 2]
        """
        return cls(fn)

    def force(self) -> T:
        """Compute and return the value, caching the result for later calls.

        The computation function is invoked at most once; subsequent calls
        return the cached result.

        Returns:
            T: The computed value.

        Examples:
            >>> lazy = Lazy.new(lambda: 2 + 2)
            >>> lazy.force()
            4
            >>> lazy.force()
            4
        """
        if self._computed:
            return self._value
        with self._lock:
            if not self._computed:
                self._value = self._fn()
                self._computed = True
        return self._value

    def is_forced(self) -> bool:
        """Return True if the value has already been computed.

        Returns:
            bool: ``True`` if the computation function has run.
        """
        return self._computed

    def try_into_inner(self) -> T | None:
        """Return the computed value if available, otherwise None.

        Returns:
            T | None: The cached value, or ``None`` if it has not been forced
                yet (the computation function is not invoked).
        """
        if not self._computed:
            return None
        return self._value

    def __repr__(self) -> str:
        """Return a string representation of the Lazy value.

        Returns:
            str: A repr of the form ``Lazy(<value>)``, or
                ``Lazy(<not initialized>)`` before the value is forced.
        """
        if self._computed:
            return f"Lazy({self._value!r})"
        return "Lazy(<not initialized>)"

    def __eq__(self, other: object) -> bool:
        """Check equality by force-computing both values.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: ``True`` if ``other`` is a ``Lazy`` whose forced value is
                equal to this one, otherwise ``NotImplemented``.
        """
        if isinstance(other, Lazy):
            return self.force() == other.force()
        return NotImplemented

    def __hash__(self) -> int:
        """Return the hash of the force-computed value.

        Returns:
            int: The hash of the computed value.
        """
        return hash(self.force())

    def __bool__(self) -> bool:
        """Return the truthiness of the force-computed value.

        Returns:
            bool: Whether the computed value is truthy.
        """
        return bool(self.force())

    def __iter__(self) -> Iterator[T]:
        """Iterate over the force-computed value.

        Forces the value first, then returns an iterator over it.

        Yields:
            T: Elements of the force-computed value.

        Examples:
            >>> lazy = Lazy.new(lambda: [1, 2, 3])
            >>> list(lazy)
            [1, 2, 3]
        """
        return iter(self.force())