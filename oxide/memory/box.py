"""Box — a heap-allocated value with automatic cleanup.

``Box[T]`` owns a value and releases it automatically when the Box is no
longer used. It supports creating a box from a value or a function, taking
the value back out again, borrowing it, leaking it, or pinning it.
"""

from __future__ import annotations

from typing import Any, Callable, Generic, TypeVar

from .pin import Pin

T = TypeVar("T")


class Box(Generic[T]):
    """A heap-allocated value with automatic cleanup and ownership semantics.

    Analogous to Rust's ``Box``, this wrapper transfers ownership of a value
    into a heap-allocated slot that is cleaned up automatically when the Box
    itself is dropped. Use :meth:`new` to create a Box and :meth:`into_inner`
    to take the owned value back out.

    Examples:
        >>> box = Box.new([1, 2, 3])
        >>> box.as_ref()
        [1, 2, 3]
        >>> box.into_inner()
        [1, 2, 3]
    """

    __slots__ = ("_value",)

    def __init__(self, value: T) -> None:
        """Construct a new Box wrapping the given value.

        Args:
            value (T): The value to own.
        """
        self._value = value

    @classmethod
    def new(cls, value: T) -> Box[T]:
        """Create a new Box containing the given value.

        Args:
            value (T): The value to store in the Box.

        Returns:
            Box[T]: A new Box owning ``value``.

        Examples:
            >>> box = Box.new("hello")
            >>> box.as_ref()
            'hello'
        """
        return cls(value)

    @classmethod
    def from_fn(cls, fn: Callable[[], T]) -> Box[T]:
        """Create a new Box by calling the provided function.

        The function is invoked immediately and its return value is placed in
        the resulting Box.

        Args:
            fn (Callable[[], T]): A zero-argument callable producing the value
                to store.

        Returns:
            Box[T]: A new Box containing the result of ``fn()``.

        Examples:
            >>> Box.from_fn(lambda: 2 + 2).into_inner()
            4
        """
        return cls(fn())

    def into_inner(self) -> T:
        """Consume the Box and return the contained value.

        Ownership is transferred back to the caller and the Box can no longer
        be used afterwards.

        Returns:
            T: The value previously held by the Box.

        Examples:
            >>> Box.new(7).into_inner()
            7
        """
        return self._value

    def as_ref(self) -> T:
        """Return the contained value without consuming the Box.

        Returns:
            T: The value held by the Box; the Box remains usable.

        Examples:
            >>> box = Box.new([10, 20])
            >>> box.as_ref()
            [10, 20]
        """
        return self._value

    def as_mut(self) -> T:
        """Return a mutable reference to the contained value.

        The Box is not consumed, so the value can be accessed again later;
        mutations made through the returned value are reflected in the Box.

        Returns:
            T: The value held by the Box, viewed as mutable.

        Examples:
            >>> box = Box.new(1)
            >>> box.as_mut()
            1
        """
        return self._value

    def leak(self) -> T:
        """Leak the Box and return the contained value without cleanup.

        The returned value is detached from the Box's cleanup logic and will
        not be reset when the Box is eventually destroyed.

        Returns:
            T: The leaked value.

        Examples:
            >>> Box.new(3).leak()
            3
        """
        return self._value

    def pin(self) -> Pin[T]:
        """Pin the contained value, preventing it from being moved.

        Returns:
            Pin[T]: A ``Pin`` guarding the contained value.

        Examples:
            >>> pin = Box.new([1, 2]).pin()
            >>> pin.is_pinned()
            True
        """
        return Pin(self._value)

    def __enter__(self) -> Box[T]:
        """Enter the context manager, returning self.

        Returns:
            Box[T]: The Box itself, ready for use inside the ``with`` block.
        """
        return self

    def __exit__(self, *_: Any) -> None:
        """Exit the context manager, performing no extra cleanup.

        Args:
            *_ (Any): The exception type, value, and traceback (if any), which
                are ignored.
        """
        pass

    def __repr__(self) -> str:
        """Return a string representation of the Box.

        Returns:
            str: A repr of the form ``Box(<value>)``.
        """
        return f"Box({self._value!r})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another Box by comparing the contained values.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: ``True`` if ``other`` is a ``Box`` wrapping an equal value,
                otherwise ``NotImplemented``.
        """
        if isinstance(other, Box):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        """Return the hash of the contained value.

        Returns:
            int: The hash of the value held by the Box.
        """
        return hash(self._value)

    def __bool__(self) -> bool:
        """Return whether the Box is truthy.

        A Box is always truthy regardless of its contents.

        Returns:
            bool: Always ``True``.
        """
        return True

    def __del__(self) -> None:
        """Clean up by clearing the contained value."""
        self._value = None