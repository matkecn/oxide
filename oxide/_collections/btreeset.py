"""BTreeSet — an ordered set with sorted iteration.

Provides ``BTreeSet``, a set whose elements are maintained in sorted order
(analogous to Rust's ``std::collections::BTreeSet``). It supports set algebra
(union, intersection, difference) plus ordered iteration and range queries.
"""
from __future__ import annotations

from typing import Generic, Iterable, Iterator, TypeVar

T = TypeVar("T")


class BTreeSet(Generic[T]):
    """An ordered set with elements maintained in sorted order.

    ``BTreeSet`` stores unique, comparable values that are always visited in
    ascending sorted order via iteration. It mirrors Rust's ``BTreeSet`` and
    supports efficient range queries and access to the smallest/largest element.

    Examples:
        >>> s = BTreeSet([3, 1, 2])
        >>> list(s.iter())
        [1, 2, 3]
        >>> s.first()
        1
        >>> s.last()
        3
    """

    __slots__ = ("_data",)

    def __init__(self, values: Iterable[T] | None = None) -> None:
        """Initialize a BTreeSet, optionally from an iterable of values.

        Args:
            values (Iterable[T] | None): Initial elements to add. Defaults to
                empty.

        Examples:
            >>> BTreeSet([3, 1, 2])
            BTreeSet({1, 2, 3})
        """
        self._data: set[T] = set()
        if values is not None:
            for v in values:
                self._data.add(v)

    @classmethod
    def new(cls) -> BTreeSet[T]:
        """Create a new empty BTreeSet.

        Returns:
            BTreeSet[T]: An empty set.

        Examples:
            >>> BTreeSet.new()
            BTreeSet(set())
        """
        return cls()

    @classmethod
    def from_iter(cls, values: Iterable[T]) -> BTreeSet[T]:
        """Create a BTreeSet from an iterable of values.

        Args:
            values (Iterable[T]): An iterable whose elements populate the set.

        Returns:
            BTreeSet[T]: A new set containing the unique elements of ``values``.

        Examples:
            >>> BTreeSet.from_iter([3, 1, 1])
            BTreeSet({1, 3})
        """
        return cls(values)

    def insert(self, value: T) -> bool:
        """Insert a value, returning True if it was newly added.

        Args:
            value (T): The value to insert.

        Returns:
            bool: True if ``value`` was not already present, False otherwise.

        Examples:
            >>> s = BTreeSet([1])
            >>> s.insert(1)
            False
            >>> s.insert(2)
            True
        """
        existed = value in self._data
        self._data.add(value)
        return not existed

    def remove(self, value: T) -> bool:
        """Remove the value if present, returning True on success.

        Args:
            value (T): The value to remove.

        Returns:
            bool: True if the value was present and removed, False otherwise.

        Examples:
            >>> s = BTreeSet([1])
            >>> s.remove(1)
            True
            >>> s.remove(1)
            False
        """
        if value in self._data:
            self._data.remove(value)
            return True
        return False

    def contains(self, value: T) -> bool:
        """Return True if the set contains the value.

        Args:
            value (T): The value to check.

        Returns:
            bool: True if ``value`` is in the set.

        Examples:
            >>> BTreeSet([1]).contains(1)
            True
        """
        return value in self._data

    def len(self) -> int:
        """Return the number of elements in the set.

        Returns:
            int: The number of unique elements.

        Examples:
            >>> BTreeSet([1, 2, 2]).len()
            2
        """
        return len(self._data)

    def is_empty(self) -> bool:
        """Return True if the set contains no elements.

        Returns:
            bool: True if the set is empty.

        Examples:
            >>> BTreeSet().is_empty()
            True
        """
        return len(self._data) == 0

    def clear(self) -> None:
        """Remove all elements from the set.

        Examples:
            >>> s = BTreeSet([1, 2])
            >>> s.clear()
            >>> s.is_empty()
            True
        """
        self._data.clear()

    def first(self) -> T | None:
        """Return the smallest element, or None if empty.

        Returns:
            T | None: The smallest element, or None if the set is empty.

        Examples:
            >>> BTreeSet([3, 1, 2]).first()
            1
        """
        if not self._data:
            return None
        return min(self._data)

    def last(self) -> T | None:
        """Return the largest element, or None if empty.

        Returns:
            T | None: The largest element, or None if the set is empty.

        Examples:
            >>> BTreeSet([3, 1, 2]).last()
            3
        """
        if not self._data:
            return None
        return max(self._data)

    def iter(self) -> Iterator[T]:
        """Return an iterator over the elements in sorted order.

        Returns:
            Iterator[T]: An iterator yielding elements in ascending order.

        Examples:
            >>> list(BTreeSet([3, 1]).iter())
            [1, 3]
        """
        return iter(sorted(self._data))

    def range_(self, start: T, end: T) -> Iterator[T]:
        """Return an iterator over elements where start <= value < end.

        Args:
            start (T): The inclusive lower bound.
            end (T): The exclusive upper bound.

        Yields:
            Iterator[T]: Each element with ``start <= value < end``, in ascending
                order.

        Examples:
            >>> list(BTreeSet([1, 2, 3, 4]).range_(1, 3))
            [1, 2]
        """
        for v in sorted(self._data):
            if start <= v < end:
                yield v

    def intersection(self, other: BTreeSet[T]) -> BTreeSet[T]:
        """Return a new set containing elements common to both sets.

        Args:
            other (BTreeSet[T]): The set to intersect with.

        Returns:
            BTreeSet[T]: A new set with elements present in both sets.

        Examples:
            >>> sorted(BTreeSet([1, 2]).intersection(BTreeSet([2, 3])).iter())
            [2]
        """
        return BTreeSet(self._data & other._data)

    def union(self, other: BTreeSet[T]) -> BTreeSet[T]:
        """Return a new set containing all elements from both sets.

        Args:
            other (BTreeSet[T]): The set to union with.

        Returns:
            BTreeSet[T]: A new set with all unique elements from both sets.

        Examples:
            >>> sorted(BTreeSet([1]).union(BTreeSet([2])).iter())
            [1, 2]
        """
        return BTreeSet(self._data | other._data)

    def difference(self, other: BTreeSet[T]) -> BTreeSet[T]:
        """Return a new set with elements in self but not in other.

        Args:
            other (BTreeSet[T]): The set to subtract.

        Returns:
            BTreeSet[T]: A new set with elements of self not in ``other``.

        Examples:
            >>> sorted(BTreeSet([1, 2]).difference(BTreeSet([2, 3])).iter())
            [1]
        """
        return BTreeSet(self._data - other._data)

    def symmetric_difference(self, other: BTreeSet[T]) -> BTreeSet[T]:
        """Return a new set with elements in either set but not both.

        Args:
            other (BTreeSet[T]): The set to compare with.

        Returns:
            BTreeSet[T]: A new set with elements unique to exactly one set.

        Examples:
            >>> sorted(BTreeSet([1, 2]).symmetric_difference(BTreeSet([2, 3])).iter())
            [1, 3]
        """
        return BTreeSet(self._data ^ other._data)

    def is_disjoint(self, other: BTreeSet[T]) -> bool:
        """Return True if the two sets share no common elements.

        Args:
            other (BTreeSet[T]): The set to compare with.

        Returns:
            bool: True if the two sets are disjoint.

        Examples:
            >>> BTreeSet([1]).is_disjoint(BTreeSet([2]))
            True
        """
        return self._data.isdisjoint(other._data)

    def is_subset(self, other: BTreeSet[T]) -> bool:
        """Return True if every element in self is also in other.

        Args:
            other (BTreeSet[T]): The superset candidate.

        Returns:
            bool: True if self is a subset of ``other``.

        Examples:
            >>> BTreeSet([1]).is_subset(BTreeSet([1, 2]))
            True
        """
        return self._data.issubset(other._data)

    def is_superset(self, other: BTreeSet[T]) -> bool:
        """Return True if every element in other is also in self.

        Args:
            other (BTreeSet[T]): The subset candidate.

        Returns:
            bool: True if self is a superset of ``other``.

        Examples:
            >>> BTreeSet([1, 2]).is_superset(BTreeSet([1]))
            True
        """
        return self._data.issuperset(other._data)

    def to_list(self) -> list[T]:
        """Return a sorted list of all elements.

        Returns:
            list[T]: The elements in ascending sorted order.

        Examples:
            >>> BTreeSet([3, 1]).to_list()
            [1, 3]
        """
        return sorted(self._data)

    def to_set(self) -> set[T]:
        """Return a copy of the underlying set.

        Returns:
            set[T]: A shallow copy of the underlying Python set.
        """
        return self._data.copy()

    def __len__(self) -> int:
        """Return the number of elements in the set.

        Examples:
            >>> len(BTreeSet([1, 2]))
            2
        """
        return len(self._data)

    def __iter__(self) -> Iterator[T]:
        """Return an iterator over the elements in sorted order.

        Examples:
            >>> list(BTreeSet([3, 1]))
            [1, 3]
        """
        return self.iter()

    def __contains__(self, value: object) -> bool:
        """Return True if the set contains the value.

        Examples:
            >>> 1 in BTreeSet([1])
            True
        """
        return value in self._data

    def __repr__(self) -> str:
        """Return a string representation of the set.

        Examples:
            >>> repr(BTreeSet([1]))
            'BTreeSet({1})'
        """
        return f"BTreeSet({self._data!r})"

    def __eq__(self, other: object) -> bool:
        """Return True if the set equals another BTreeSet.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: True if ``other`` is a ``BTreeSet`` with equal contents;
                ``NotImplemented`` otherwise.

        Examples:
            >>> BTreeSet([1, 2]) == BTreeSet([2, 1])
            True
        """
        if isinstance(other, BTreeSet):
            return self._data == other._data
        return NotImplemented

    def __hash__(self) -> int:
        """Return a hash of the set's contents.

        Returns:
            int: A hash based on a frozenset of the elements.
        """
        return hash(frozenset(self._data))

    def __bool__(self) -> bool:
        """Return True if the set is non-empty.

        Examples:
            >>> bool(BTreeSet([1]))
            True
        """
        return bool(self._data)
