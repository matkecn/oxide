"""HashSet — a hash-based set with advanced set operations.

Provides ``HashSet``, a hash set of unique values (analogous to Rust's
``std::collections::HashSet``). It supports insertion, removal, membership
tests, iteration, and the standard set algebra operations: union,
intersection, difference, and symmetric difference.
"""
from __future__ import annotations

from typing import Generic, Iterable, Iterator, TypeVar

from ..iter.iterator import Iter

T = TypeVar("T")


class HashSet(Generic[T]):
    """A hash-based set with union, intersection, and difference operations.

    ``HashSet`` stores unique values with average O(1) insertion, removal, and
    membership tests. Elements must be hashable. It mirrors the Python ``set``
    API and Rust's ``HashSet``, and supports set algebra via dedicated methods.

    Examples:
        >>> s = HashSet([1, 2, 3])
        >>> s.insert(4)
        True
        >>> 4 in s
        True
        >>> sorted(s.union(HashSet([3, 5])).iter())
        [1, 2, 3, 4, 5]
    """

    __slots__ = ("_data",)

    def __init__(self, values: Iterable[T] | None = None) -> None:
        """Initialize a HashSet, optionally from an iterable of values.

        Args:
            values (Iterable[T] | None): Initial elements to add. Defaults to
                empty.

        Examples:
            >>> HashSet([1, 2, 2])
            HashSet({1, 2})
        """
        self._data: set[T] = set()
        if values is not None:
            for v in values:
                self._data.add(v)

    @classmethod
    def new(cls) -> HashSet[T]:
        """Create a new empty HashSet.

        Returns:
            HashSet[T]: An empty set.

        Examples:
            >>> HashSet.new()
            HashSet(set())
        """
        return cls()

    @classmethod
    def with_capacity(cls, capacity: int) -> HashSet[T]:
        """Create a new HashSet (capacity hint is accepted for API compatibility).

        Args:
            capacity (int): An ignored capacity hint, for API compatibility.

        Returns:
            HashSet[T]: An empty set.
        """
        return cls()

    @classmethod
    def from_iter(cls, values: Iterable[T]) -> HashSet[T]:
        """Create a HashSet from an iterable of values.

        Args:
            values (Iterable[T]): An iterable whose elements populate the set.

        Returns:
            HashSet[T]: A new set containing the unique elements of ``values``.

        Examples:
            >>> HashSet.from_iter([1, 2, 2])
            HashSet({1, 2})
        """
        return cls(values)

    def insert(self, value: T) -> bool:
        """Insert a value, returning True if it was newly added.

        Args:
            value (T): The value to insert.

        Returns:
            bool: True if ``value`` was not already present, False otherwise.

        Examples:
            >>> s = HashSet([1])
            >>> s.insert(1)
            False
            >>> s.insert(2)
            True
        """
        existed = value in self._data
        self._data.add(value)
        return not existed

    def remove(self, value: T) -> None:
        """Remove the value if it is present.

        Like :meth:`set.discard`, this never raises. It reports nothing about
        whether the value was there; use :meth:`take` when you need to know.

        Args:
            value (T): The value to remove.

        Examples:
            >>> s = HashSet([1, 2])
            >>> s.remove(1)
            >>> 1 in s
            False
            >>> s.remove(1)
            >>> s.remove(99)
        """
        self._data.discard(value)

    def take(self, value: T) -> T | None:
        """Remove and return the value if present, or None.

        Args:
            value (T): The value to remove.

        Returns:
            T | None: The removed value if present, otherwise None.

        Examples:
            >>> s = HashSet([1])
            >>> s.take(1)
            1
            >>> s.take(1) is None
            True
        """
        if value in self._data:
            self._data.remove(value)
            return value
        return None

    def contains(self, value: T) -> bool:
        """Return True if the set contains the value.

        Args:
            value (T): The value to check.

        Returns:
            bool: True if ``value`` is in the set.

        Examples:
            >>> HashSet([1]).contains(1)
            True
        """
        return value in self._data

    def get(self, value: T) -> T | None:
        """Return the value if present, or None.

        Args:
            value (T): The value to look up.

        Returns:
            T | None: The value if present, otherwise None.

        Examples:
            >>> HashSet([1]).get(1)
            1
        """
        if value in self._data:
            return value
        return None

    def len(self) -> int:
        """Return the number of elements in the set.

        Returns:
            int: The number of unique elements.

        Examples:
            >>> HashSet([1, 2, 2]).len()
            2
        """
        return len(self._data)

    def is_empty(self) -> bool:
        """Return True if the set contains no elements.

        Returns:
            bool: True if the set is empty.

        Examples:
            >>> HashSet().is_empty()
            True
        """
        return len(self._data) == 0

    def clear(self) -> None:
        """Remove all elements from the set.

        Examples:
            >>> s = HashSet([1, 2])
            >>> s.clear()
            >>> s.is_empty()
            True
        """
        self._data.clear()

    def iter(self) -> Iter[T]:
        """Return an iterator over the elements.

        Returns:
            Iter[T]: An Iter yielding each element, so the adapter and consumer
                methods are available.

        Examples:
            >>> sorted(HashSet([3, 1]).iter())
            [1, 3]
            >>> HashSet([3, 1]).iter().count()
            2
        """
        return Iter(self._data)

    def drain(self) -> Iter[T]:
        """Consume the set and return an iterator over its elements.

        The set is emptied as a result.

        Returns:
            Iter[T]: An Iter over the elements before consumption.

        Examples:
            >>> s = HashSet([1, 2])
            >>> sorted(s.drain())
            [1, 2]
            >>> s.is_empty()
            True
            >>> HashSet([1, 2]).drain().max()
            2
        """
        items = list(self._data)
        self._data.clear()
        return Iter(items)

    def extend(self, values: Iterable[T]) -> None:
        """Add all values from an iterable to the set.

        Args:
            values (Iterable[T]): The values to add.

        Examples:
            >>> s = HashSet([1])
            >>> s.extend([2, 3])
            >>> len(s)
            3
        """
        for v in values:
            self._data.add(v)

    def intersection(self, other: HashSet[T]) -> HashSet[T]:
        """Return a new set containing elements common to both sets.

        Args:
            other (HashSet[T]): The set to intersect with.

        Returns:
            HashSet[T]: A new set with elements present in both sets.

        Examples:
            >>> sorted(HashSet([1, 2]).intersection(HashSet([2, 3])).iter())
            [2]
        """
        return HashSet(self._data & other._data)

    def union(self, other: HashSet[T]) -> HashSet[T]:
        """Return a new set containing all elements from both sets.

        Args:
            other (HashSet[T]): The set to union with.

        Returns:
            HashSet[T]: A new set with all unique elements from both sets.

        Examples:
            >>> sorted(HashSet([1]).union(HashSet([2])).iter())
            [1, 2]
        """
        return HashSet(self._data | other._data)

    def difference(self, other: HashSet[T]) -> HashSet[T]:
        """Return a new set with elements in self but not in other.

        Args:
            other (HashSet[T]): The set to subtract.

        Returns:
            HashSet[T]: A new set with elements of self not present in ``other``.

        Examples:
            >>> sorted(HashSet([1, 2]).difference(HashSet([2, 3])).iter())
            [1]
        """
        return HashSet(self._data - other._data)

    def symmetric_difference(self, other: HashSet[T]) -> HashSet[T]:
        """Return a new set with elements in either set but not both.

        Args:
            other (HashSet[T]): The set to compare with.

        Returns:
            HashSet[T]: A new set with elements unique to exactly one of the two
                sets.

        Examples:
            >>> sorted(HashSet([1, 2]).symmetric_difference(HashSet([2, 3])).iter())
            [1, 3]
        """
        return HashSet(self._data ^ other._data)

    def is_disjoint(self, other: HashSet[T]) -> bool:
        """Return True if the two sets share no common elements.

        Args:
            other (HashSet[T]): The set to compare with.

        Returns:
            bool: True if the two sets are disjoint.

        Examples:
            >>> HashSet([1]).is_disjoint(HashSet([2]))
            True
        """
        return self._data.isdisjoint(other._data)

    def is_subset(self, other: HashSet[T]) -> bool:
        """Return True if every element in self is also in other.

        Args:
            other (HashSet[T]): The superset candidate.

        Returns:
            bool: True if self is a subset of ``other``.

        Examples:
            >>> HashSet([1]).is_subset(HashSet([1, 2]))
            True
        """
        return self._data.issubset(other._data)

    def is_superset(self, other: HashSet[T]) -> bool:
        """Return True if every element in other is also in self.

        Args:
            other (HashSet[T]): The subset candidate.

        Returns:
            bool: True if self is a superset of ``other``.

        Examples:
            >>> HashSet([1, 2]).is_superset(HashSet([1]))
            True
        """
        return self._data.issuperset(other._data)

    def to_list(self) -> list[T]:
        """Return a list containing all elements in the set.

        Returns:
            list[T]: A list of the set's elements.

        Examples:
            >>> sorted(HashSet([1, 2]).to_list())
            [1, 2]
        """
        return list(self._data)

    def to_set(self) -> set[T]:
        """Return a copy of the underlying set.

        Returns:
            set[T]: A shallow copy of the underlying Python set.

        Examples:
            >>> HashSet([1]).to_set()
            {1}
        """
        return self._data.copy()

    def into_iter(self) -> Iter[T]:
        """Consume the set and return an iterator over its elements.

        The set is emptied as a result.

        Returns:
            Iter[T]: An Iter over the elements before consumption.

        Examples:
            >>> s = HashSet([1, 2])
            >>> sorted(s.into_iter())
            [1, 2]
            >>> s.is_empty()
            True
            >>> HashSet([1, 2]).into_iter().max()
            2
        """
        items = list(self._data)
        self._data.clear()
        return Iter(items)

    def __len__(self) -> int:
        """Return the number of elements in the set.

        Examples:
            >>> len(HashSet([1, 2]))
            2
        """
        return len(self._data)

    def __iter__(self) -> Iterator[T]:
        """Return an iterator over the elements.

        Examples:
            >>> [x for x in HashSet([1])]
            [1]
        """
        return iter(self._data)

    def __contains__(self, value: object) -> bool:
        """Return True if the set contains the value.

        Examples:
            >>> 1 in HashSet([1])
            True
        """
        return value in self._data

    def __repr__(self) -> str:
        """Return a string representation of the set.

        Examples:
            >>> repr(HashSet([1]))
            'HashSet({1})'
        """
        return f"HashSet({self._data!r})"

    def __eq__(self, other: object) -> bool:
        """Return True if the set equals another HashSet.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: True if ``other`` is a ``HashSet`` with equal contents;
                ``NotImplemented`` otherwise.

        Examples:
            >>> HashSet([1, 2]) == HashSet([2, 1])
            True
        """
        if isinstance(other, HashSet):
            return self._data == other._data
        return NotImplemented

    def __hash__(self) -> int:
        """Return a hash of the set's contents.

        The set is hashable because its contents cannot change through this
        wrapper's perspective of equality.

        Returns:
            int: A hash based on a frozenset of the elements.
        """
        return hash(frozenset(self._data))

    def __bool__(self) -> bool:
        """Return True if the set is non-empty.

        Examples:
            >>> bool(HashSet([1]))
            True
        """
        return bool(self._data)
