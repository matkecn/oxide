"""Cow — copy-on-write, lazily cloned borrowed or owned data.

``Cow[T]`` can represent either borrowed or owned data. As long as the data
is only read it is never copied; a deep copy happens lazily only when owned
data is required. Construct instances with ``CowBorrowed`` or ``CowOwned``.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Callable, ClassVar, Generic, TypeVar

T = TypeVar("T")
U = TypeVar("U")


@dataclass(frozen=True)
class Cow(Generic[T]):
    """Copy-on-write data that is cloned lazily only when mutated.

    Analogous to Rust's ``Cow``, a borrowed instance does not create any copy
    until the data must become owned. Read access never clones; use
    :meth:`into_owned` or :meth:`to_owned` to obtain standalone data, or
    :meth:`map` to transform the data while preserving the ownership variant.

    Examples:
        >>> cow = CowBorrowed([1, 2, 3])
        >>> cow.is_borrowed()
        True
        >>> cow.as_ref()
        [1, 2, 3]
    """

    _Borrowed: ClassVar[type]
    _Owned: ClassVar[type]

    def is_borrowed(self) -> bool:
        """Return True if this Cow holds borrowed (non-owned) data.

        Returns:
            bool: ``True`` if this is a borrowed variant.

        Examples:
            >>> CowBorrowed(1).is_borrowed()
            True
        """
        return isinstance(self, _CowBorrowed)

    def is_owned(self) -> bool:
        """Return True if this Cow holds owned data.

        Returns:
            bool: ``True`` if this is an owned variant.

        Examples:
            >>> CowOwned(1).is_owned()
            True
        """
        return isinstance(self, _CowOwned)

    def as_ref(self) -> T:
        """Return a reference to the contained data regardless of ownership.

        Returns:
            T: The contained data.

        Examples:
            >>> CowBorrowed([1, 2]).as_ref()
            [1, 2]
        """
        if isinstance(self, _CowBorrowed):
            return self._data
        return self._data

    def into_owned(self) -> T:
        """Consume the Cow and return owned data, deep-copying if necessary.

        If this Cow holds borrowed data, a deep copy is made and returned; if
        it is already owned, the data is returned as-is.

        Returns:
            T: Owned (standalone) data.

        Examples:
            >>> CowBorrowed([1, 2]).into_owned()
            [1, 2]
        """
        if isinstance(self, _CowOwned):
            return self._data
        return copy.deepcopy(self._data)

    def to_owned(self) -> T:
        """Return a deep copy of the data if borrowed, or the data itself if owned.

        Returns:
            T: Owned data.

        Examples:
            >>> CowOwned([1, 2]).to_owned()
            [1, 2]
        """
        if isinstance(self, _CowOwned):
            return self._data
        return copy.deepcopy(self._data)

    def map(self, fn: Callable[[T], U]) -> Cow[U]:
        """Apply a function to the contained data, preserving the ownership variant.

        Args:
            fn (Callable[[T], U]): The function to apply to the contained data.

        Returns:
            Cow[U]: A new Cow, borrowed if the original was borrowed and owned
                if the original was owned.

        Examples:
            >>> CowOwned(10).map(lambda x: x * 2).as_ref()
            20
        """
        if isinstance(self, _CowOwned):
            return CowOwned(fn(self._data))
        return CowBorrowed(fn(self._data))

    def unwrap(self) -> T:
        """Return the contained data regardless of ownership.

        Returns:
            T: The contained data.

        Examples:
            >>> CowOwned(3).unwrap()
            3
        """
        if isinstance(self, _CowOwned):
            return self._data
        return self._data

    def __repr__(self) -> str:
        """Return a string representation showing the ownership variant.

        Returns:
            str: A repr of the form ``Cow::Borrowed(<value>)`` or
                ``Cow::Owned(<value>)``.
        """
        if isinstance(self, _CowBorrowed):
            return f"Cow::Borrowed({self._data!r})"
        return f"Cow::Owned({self._data!r})"

    def __eq__(self, other: object) -> bool:
        """Check equality by comparing the contained data.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: ``True`` if ``other`` is a ``Cow`` holding equal data,
                otherwise ``NotImplemented``.
        """
        if isinstance(other, Cow):
            return self.as_ref() == other.as_ref()
        return NotImplemented

    def __hash__(self) -> int:
        """Return the hash of the contained data.

        Returns:
            int: The hash of the contained data.
        """
        return hash(self.as_ref())


@dataclass(frozen=True)
class _CowBorrowed(Cow[T]):
    _data: T


@dataclass(frozen=True)
class _CowOwned(Cow[T]):
    _data: T


Cow._Borrowed = _CowBorrowed
Cow._Owned = _CowOwned


def CowBorrowed(value: T) -> Cow[T]:
    """Create a borrowed (non-owning) variant of Cow.

    Args:
        value (T): The data to hold without owning.

    Returns:
        Cow[T]: A borrowed Cow.

    Examples:
        >>> cow = CowBorrowed([1, 2])
        >>> cow.is_borrowed()
        True
    """
    return _CowBorrowed(value)


def CowOwned(value: T) -> Cow[T]:
    """Create an owning variant of Cow.

    Args:
        value (T): The data to take ownership of.

    Returns:
        Cow[T]: An owned Cow.

    Examples:
        >>> cow = CowOwned([1, 2])
        >>> cow.is_owned()
        True
    """
    return _CowOwned(value)