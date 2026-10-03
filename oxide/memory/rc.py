"""Rc and Weak — single-threaded reference-counted shared ownership.

``Rc[T]`` provides shared ownership of a value through reference counting,
letting multiple read access points coexist without copying the value.
``Weak[T]`` holds a non-owning reference that does not keep the value
alive, which is useful for breaking reference cycles.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

T = TypeVar("T")


class Rc(Generic[T]):
    """Reference-counted shared ownership for single-threaded contexts.

    Analogous to Rust's ``Rc``, this pointer allows a single value to be
    shared by several owners. Use :meth:`clone` to create another strong
    reference and :meth:`downgrade` to obtain a non-owning ``Weak``.

    Examples:
        >>> rc = Rc.new(42)
        >>> rc.strong_count()
        1
        >>> clone = rc.clone()
        >>> rc.strong_count()
        2
        >>> rc.into_inner()
        42
    """

    __slots__ = ("_value", "_ref_count", "_weak_count")

    def __init__(self, value: T) -> None:
        """Construct a new Rc with the given value and a strong count of one.

        Args:
            value (T): The value to share.
        """
        self._value = value
        self._ref_count = 1
        self._weak_count = 0

    @classmethod
    def new(cls, value: T) -> Rc[T]:
        """Create a new Rc with the given value and a reference count of one.

        Args:
            value (T): The value to share.

        Returns:
            Rc[T]: A new Rc owning ``value``.

        Examples:
            >>> rc = Rc.new(10)
            >>> rc.strong_count()
            1
        """
        return cls(value)

    def clone(self) -> Rc[T]:
        """Clone the Rc, incrementing the reference count.

        Both the original and the returned clone share the same value; the
        underlying value is only finalized when all strong references are
        dropped.

        Returns:
            Rc[T]: A new strong reference sharing the same value.

        Examples:
            >>> rc = Rc.new(1)
            >>> other = rc.clone()
            >>> rc.strong_count()
            2
        """
        self._ref_count += 1
        return Rc._from_raw(self._value, self._ref_count, self._weak_count)

    @classmethod
    def _from_raw(cls, value: T, ref_count: int, weak_count: int) -> Rc[T]:
        rc = cls.__new__(cls)
        rc._value = value
        rc._ref_count = ref_count
        rc._weak_count = weak_count
        return rc

    def downgrade(self) -> Weak[T]:
        """Create a weak reference without adding a strong reference.

        Returns:
            Weak[T]: A non-owning weak reference that does not keep the value
                alive.

        Examples:
            >>> rc = Rc.new(1)
            >>> weak = rc.downgrade()
            >>> weak.is_alive()
            True
        """
        self._weak_count += 1
        return Weak._from_raw(self._value, self._ref_count, self._weak_count)

    def strong_count(self) -> int:
        """Return the number of strong references to the value.

        Returns:
            int: The current strong reference count.
        """
        return self._ref_count

    def weak_count(self) -> int:
        """Return the number of weak references to the value.

        Returns:
            int: The current weak reference count.
        """
        return self._weak_count

    def try_unwrap(self) -> T | None:
        """Attempt to extract the value if this is the only strong reference.

        Returns:
            T | None: The contained value if there are no other strong
                references, otherwise ``None``.

        Examples:
            >>> rc = Rc.new(5)
            >>> _ = rc.clone()
            >>> rc.try_unwrap() is None
            True
        """
        if self._ref_count == 1:
            return self._value
        return None

    def as_ptr(self) -> int:
        """Return the identity of the contained value.

        Returns:
            int: The identity of the shared value (``id`` of the underlying
                object).
        """
        return id(self._value)

    def into_inner(self) -> T:
        """Consume the Rc and return the contained value.

        Returns:
            T: The shared value handed back to the caller.
        """
        return self._value

    def __enter__(self) -> Rc[T]:
        """Enter the context manager, returning self.

        Returns:
            Rc[T]: The Rc itself, ready for use inside the ``with`` block.
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
        """Decrement the strong reference count on destruction."""
        self._ref_count -= 1

    def __repr__(self) -> str:
        """Return a string representation including reference counts.

        Returns:
            str: A repr of the form ``Rc(<value>, strong=..., weak=...)``.
        """
        return f"Rc({self._value!r}, strong={self._ref_count}, weak={self._weak_count})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another Rc by comparing the contained values.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: ``True`` if ``other`` is an ``Rc`` wrapping an equal value,
                otherwise ``NotImplemented``.
        """
        if isinstance(other, Rc):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        """Return the hash of the contained value.

        Returns:
            int: The hash of the shared value.
        """
        return hash(self._value)

    def __bool__(self) -> bool:
        """Return whether the Rc is truthy.

        An Rc is always truthy regardless of its contents.

        Returns:
            bool: Always ``True``.
        """
        return True


class Weak(Generic[T]):
    """A non-owning weak reference to a value managed by an Rc.

    A ``Weak`` does not keep the referenced value alive; use :meth:`upgrade`
    to obtain a strong ``Rc`` while strong references still exist, which is
    useful for breaking reference cycles.

    Examples:
        >>> rc = Rc.new(10)
        >>> weak = rc.downgrade()
        >>> weak.upgrade().into_inner()
        10
    """

    __slots__ = ("_value", "_ref_count", "_weak_count")

    def __init__(self, value: T) -> None:
        """Construct a new Weak referencing the given value.

        Args:
            value (T): The value to reference weakly.
        """
        self._value = value
        self._ref_count = 0
        self._weak_count = 1

    @classmethod
    def _from_raw(cls, value: T, ref_count: int, weak_count: int) -> Weak[T]:
        w = cls.__new__(cls)
        w._value = value
        w._ref_count = ref_count
        w._weak_count = weak_count
        return w

    def upgrade(self) -> Rc[T] | None:
        """Attempt to upgrade to a strong Rc; returns None if the value is gone.

        Returns:
            Rc[T] | None: A strong ``Rc`` referencing the value if it is still
                alive, otherwise ``None``.

        Examples:
            >>> rc = Rc.new(1)
            >>> weak = rc.downgrade()
            >>> weak.upgrade().into_inner()
            1
        """
        if self._ref_count > 0:
            self._ref_count += 1
            return Rc._from_raw(self._value, self._ref_count, self._weak_count)
        return None

    def strong_count(self) -> int:
        """Return the number of strong references to the value.

        Returns:
            int: The number of live ``Rc`` handles for the value.
        """
        return self._ref_count

    def weak_count(self) -> int:
        """Return the number of weak references to the value.

        Returns:
            int: The current weak reference count.
        """
        return self._weak_count

    def as_ptr(self) -> int:
        """Return the identity of the referenced value.

        Returns:
            int: The identity of the underlying value.
        """
        return id(self._value)

    def is_alive(self) -> bool:
        """Return whether the referenced value is still alive.

        A value is alive as long as at least one strong reference exists.

        Returns:
            bool: ``True`` if the value has strong references.

        Examples:
            >>> rc = Rc.new(1)
            >>> weak = rc.downgrade()
            >>> weak.is_alive()
            True
        """
        return self._ref_count > 0

    def __repr__(self) -> str:
        """Return a string representation including reference counts.

        Returns:
            str: A repr of the form ``Weak(strong=..., weak=...)``.
        """
        return f"Weak(strong={self._ref_count}, weak={self._weak_count})"

    def __bool__(self) -> bool:
        """Return whether the referenced value is still alive.

        Returns:
            bool: ``True`` if the value has strong references.
        """
        return self._ref_count > 0

    def __del__(self) -> None:
        """Decrement the weak reference count on destruction."""
        self._weak_count -= 1