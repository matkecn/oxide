"""Cell — interior mutability for Copy types without references.

``Cell[T]`` supports single-threaded interior mutability: the value inside
can be replaced, swapped, or taken even when the Cell itself is only
immutably shared. Values are retrieved by copying; pass ``deep=True`` when
constructing to make retrievals deep copies.
"""

from __future__ import annotations

import copy
from typing import Generic, TypeVar

T = TypeVar("T")


class Cell(Generic[T]):
    """Interior mutability for Copy types, allowing mutation without references.

    A ``Cell`` can be mutated through a shared reference by copying values in
    and out rather than exposing references into its interior. Intended for
    single-threaded use with copyable values.

    Examples:
        >>> cell = Cell.new(1)
        >>> cell.replace(2)
        1
        >>> cell.get()
        2
    """

    __slots__ = ("_value", "_copy")

    def __init__(self, value: T, *, deep: bool = False) -> None:
        """Construct a new Cell containing the given value.

        Args:
            value (T): The value to store in the cell.
            deep (bool, optional): If ``True``, :meth:`get` returns a deep
                copy of the contained value instead of the value itself.
        """
        self._value = value
        self._copy = deep

    @classmethod
    def new(cls, value: T) -> Cell[T]:
        """Create a new Cell containing the given value.

        Args:
            value (T): The value to store in the cell.

        Returns:
            Cell[T]: A new Cell holding ``value``.

        Examples:
            >>> cell = Cell.new([1, 2])
            >>> cell.get()
            [1, 2]
        """
        return cls(value)

    def get(self) -> T:
        """Return a copy of the contained value.

        If the Cell was constructed with ``deep=True``, a deep copy is
        returned; otherwise the contained value itself is returned.

        Returns:
            T: The contained value (or a copy of it).
        """
        if self._copy:
            return copy.deepcopy(self._value)
        return self._value

    def set(self, value: T) -> None:
        """Replace the contained value with the given value.

        Args:
            value (T): The new value to store in the Cell.

        Examples:
            >>> cell = Cell.new(1)
            >>> cell.set(2)
            >>> cell.get()
            2
        """
        self._value = value

    def replace(self, value: T) -> T:
        """Replace the contained value and return the previous value.

        Args:
            value (T): The new value to store.

        Returns:
            T: The value previously held by the Cell.

        Examples:
            >>> cell = Cell.new(1)
            >>> cell.replace(2)
            1
        """
        old = self._value
        self._value = value
        return old

    def swap(self, other: Cell[T]) -> None:
        """Swap the contained values with another Cell.

        Args:
            other (Cell[T]): Another Cell whose value will be exchanged with
                this one.

        Examples:
            >>> a = Cell.new(1)
            >>> b = Cell.new(2)
            >>> a.swap(b)
            >>> a.get()
            2
        """
        self._value, other._value = other._value, self._value

    def take(self) -> T:
        """Take the contained value out, leaving None in its place.

        After this call the Cell holds ``None`` and the previous value is
        returned to the caller.

        Returns:
            T: The value previously held by the Cell.

        Examples:
            >>> cell = Cell.new(3)
            >>> cell.take()
            3
        """
        old = self._value
        self._value = None  # type: ignore[assignment]
        return old

    def into_inner(self) -> T:
        """Consume the Cell and return the contained value.

        Returns:
            T: The value held by the Cell.
        """
        return self._value

    def as_ptr(self) -> int:
        """Return the identity of the contained value.

        Returns:
            int: The identity of the stored value.
        """
        return id(self._value)

    def __repr__(self) -> str:
        """Return a string representation of the Cell.

        Returns:
            str: A repr of the form ``Cell(<value>)``.
        """
        return f"Cell({self._value!r})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another Cell by comparing the contained values.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: ``True`` if ``other`` is a ``Cell`` holding an equal value,
                otherwise ``NotImplemented``.
        """
        if isinstance(other, Cell):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        """Return the hash of the contained value.

        Returns:
            int: The hash of the stored value.
        """
        return hash(self._value)

    def __bool__(self) -> bool:
        """Return the truthiness of the contained value.

        Returns:
            bool: ``True`` if the stored value is truthy.
        """
        return bool(self._value)