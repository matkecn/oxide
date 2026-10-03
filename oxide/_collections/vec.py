"""Vec — a growable array with push, pop, insert, remove, and list protocol support.

Provides ``Vec``, a dynamically sized contiguous array (analogous to Rust's
``Vec``) with amortized O(1) push/pop at the end, index-based insertion and
removal, capacity management, and full Python list protocol support.
"""
from __future__ import annotations

from typing import Any, Callable, Generic, Iterable, Iterator, TypeVar, overload

from ..core.option import Option, Some, None_

T = TypeVar("T")


class Vec(Generic[T]):
    """A growable array type with push, pop, insert, remove, and list protocol support.

    ``Vec`` is a dynamically sized, contiguous sequence of elements. Elements
    can be added to or removed from the end in amortized O(1) time, and accessed
    by index. It mirrors Rust's ``std::vec::Vec`` while integrating with Python's
    iteration, indexing, and membership protocols.

    Examples:
        >>> v = Vec([1, 2, 3])
        >>> v.push(4)
        >>> v.pop()
        Some(4)
        >>> len(v)
        3
        >>> v[0]
        1
    """

    __slots__ = ("_data", "_capacity")

    def __init__(
        self,
        values: Iterable[T] = (),
        *,
        capacity: int | None = None,
    ) -> None:
        """Initialize a Vec, optionally from an iterable and with a capacity hint.

        Args:
            values (Iterable[T]): An iterable of initial elements. Defaults to
                empty.
            capacity (int | None): The initial capacity to allocate. Must not be
                smaller than the number of ``values``. Defaults to the number of
                values provided.

        Raises:
            ValueError: If ``capacity`` is smaller than the length of ``values``.

        Examples:
            >>> Vec()
            Vec([])
            >>> Vec([1, 2, 3])
            Vec([1, 2, 3])
            >>> Vec([1, 2], capacity=10)
            Vec([1, 2])
        """
        self._data = list(values)

        if capacity is None:
            self._capacity = len(self._data)
        else:
            if capacity < len(self._data):
                raise ValueError(
                    "capacity cannot be smaller than length"
                )

            self._capacity = capacity

    @classmethod
    def new(cls) -> Vec[T]:
        """Create a new empty Vec.

        Returns:
            Vec[T]: An empty Vec.

        Examples:
            >>> Vec.new()
            Vec([])
        """
        return cls()

    @classmethod
    def with_capacity(cls, capacity: int) -> Vec[T]:
        """Create a new Vec with pre-allocated capacity.

        Args:
            capacity (int): The number of elements to allocate space for.

        Returns:
            Vec[T]: An empty Vec with the given capacity.

        Raises:
            ValueError: If ``capacity`` is negative.

        Examples:
            >>> v = Vec.with_capacity(10)
            >>> v.capacity()
            10
        """
        if capacity < 0:
            raise ValueError("capacity must be non-negative")

        return cls(capacity=capacity)

    @classmethod
    def from_iter(cls, values: Iterable[T]) -> Vec[T]:
        """Create a Vec from an iterable of values.

        Args:
            values (Iterable[T]): An iterable whose elements populate the Vec.

        Returns:
            Vec[T]: A new Vec containing the elements of ``values``.

        Examples:
            >>> Vec.from_iter(range(3))
            Vec([0, 1, 2])
        """
        return cls(values)

    @classmethod
    def repeat(cls, value: T, n: int) -> Vec[T]:
        """Create a Vec containing `n` copies of `value`.

        Args:
            value (T): The value to replicate.
            n (int): The number of copies. Must be non-negative.

        Returns:
            Vec[T]: A Vec of length ``n`` where every element is ``value``.

        Raises:
            ValueError: If ``n`` is negative.

        Examples:
            >>> Vec.repeat(0, 3)
            Vec([0, 0, 0])
        """
        if n < 0:
            raise ValueError("n must be non-negative")

        return cls([value] * n)

    def len(self) -> int:
        """Return the number of elements in the Vec.

        Returns:
            int: The current number of elements.

        Examples:
            >>> Vec([1, 2]).len()
            2
        """
        return len(self._data)

    def is_empty(self) -> bool:
        """Return True if the Vec contains no elements.

        Returns:
            bool: True if the Vec has length zero.

        Examples:
            >>> Vec().is_empty()
            True
        """
        return not self._data

    def capacity(self) -> int:
        """Return the total number of elements the Vec can hold without reallocating.

        Returns:
            int: The current capacity.

        Examples:
            >>> Vec([1, 2, 3]).capacity()
            3
        """
        return self._capacity


    def reserve(self, additional: int) -> None:
        """Reserve capacity for at least `additional` more elements, growing exponentially.

        Ensures the Vec can hold at least ``len() + additional`` elements without
        reallocating, doubling capacity as needed to keep growth amortized O(1).

        Args:
            additional (int): The desired number of additional elements. Must be
                non-negative.

        Raises:
            ValueError: If ``additional`` is negative.

        Examples:
            >>> v = Vec([1])
            >>> v.reserve(10)
            >>> v.capacity() >= 11
            True
        """
        if additional < 0:
            raise ValueError("additional must be non-negative")

        required = self.len() + additional

        if required <= self._capacity:
            return

        new_capacity = max(
            required,
            max(1, self._capacity * 2),
        )

        self._capacity = new_capacity

    def reserve_exact(self, additional: int) -> None:
        """Reserve capacity for exactly `additional` more elements if needed.

        Args:
            additional (int): The number of additional elements to reserve room
                for. Must be non-negative.

        Raises:
            ValueError: If ``additional`` is negative.

        Examples:
            >>> v = Vec([1])
            >>> v.reserve_exact(5)
            >>> v.capacity()
            6
        """
        if additional < 0:
            raise ValueError("additional must be non-negative")

        required = self.len() + additional

        if required > self._capacity:
            self._capacity = required

    def shrink_to_fit(self) -> None:
        """Shrink the capacity to match the current length.

        Examples:
            >>> v = Vec([1, 2], capacity=10)
            >>> v.shrink_to_fit()
            >>> v.capacity()
            2
        """
        self._capacity = self.len()

    def shrink_to(self, min_capacity: int) -> None:
        """Shrink the capacity to at most `min_capacity`, but no less than the length.

        Args:
            min_capacity (int): The desired upper bound on capacity. Must be
                non-negative.

        Raises:
            ValueError: If ``min_capacity`` is negative.

        Examples:
            >>> v = Vec([1, 2, 3], capacity=100)
            >>> v.shrink_to(5)
            >>> v.capacity()
            5
        """
        if min_capacity < 0:
            raise ValueError(
                "min_capacity must be non-negative"
            )

        self._capacity = max(
            self.len(),
            min_capacity,
        )

    def push(self, value: T) -> None:
        """Append a value to the end of the Vec.

        Args:
            value (T): The value to append.

        Examples:
            >>> v = Vec([1])
            >>> v.push(2)
            >>> v
            Vec([1, 2])
        """
        self.reserve(1)
        self._data.append(value)

    def pop(self) -> Option[T]:
        """Remove and return the last element, or None_ if empty.

        Returns:
            Option[T]: ``Some(value)`` with the removed element, or ``None_`` if
                the Vec is empty.

        Examples:
            >>> v = Vec([1, 2])
            >>> v.pop()
            Some(2)
            >>> v.pop()
            Some(1)
            >>> v.pop()
            None_
        """
        if not self._data:
            return None_

        return Some(self._data.pop())

    def insert(self, index: int, value: T) -> None:
        """Insert a value at the given index, shifting subsequent elements right.

        Args:
            index (int): The position at which to insert, in ``[0, len()]``.
            value (T): The value to insert.

        Raises:
            IndexError: If ``index`` is negative or greater than the current
                length.

        Examples:
            >>> v = Vec([1, 3])
            >>> v.insert(1, 2)
            >>> v
            Vec([1, 2, 3])
        """
        if index < 0 or index > self.len():
            raise IndexError(
                f"index {index} out of bounds"
            )

        self.reserve(1)
        self._data.insert(index, value)

    def remove(self, index: int) -> T:
        """Remove and return the element at `index`, shifting subsequent elements left.

        Args:
            index (int): The index of the element to remove.

        Returns:
            T: The removed element.

        Raises:
            IndexError: If ``index`` is out of bounds.

        Examples:
            >>> v = Vec([1, 2, 3])
            >>> v.remove(1)
            2
            >>> v
            Vec([1, 3])
        """
        self._check_index(index)
        return self._data.pop(index)

    def swap_remove(self, index: int) -> T:
        """Remove and return the element at `index` by swapping with the last element (O(1)).

        Removes the element without preserving order, which makes this an O(1)
        operation (unlike :meth:`remove`, which is O(n)).

        Args:
            index (int): The index of the element to remove.

        Returns:
            T: The removed element.

        Raises:
            IndexError: If ``index`` is out of bounds.

        Examples:
            >>> v = Vec([1, 2, 3])
            >>> v.swap_remove(0)
            1
            >>> v
            Vec([3, 2])
        """
        self._check_index(index)

        last = self._data.pop()

        if index == self.len():
            return last

        removed = self._data[index]
        self._data[index] = last

        return removed

    def clear(self) -> None:
        """Remove all elements from the Vec.

        Examples:
            >>> v = Vec([1, 2])
            >>> v.clear()
            >>> v
            Vec([])
        """
        self._data.clear()

    def truncate(self, length: int) -> None:
        """Shorten the Vec to `length` elements, dropping the rest.

        Args:
            length (int): The desired length. Must be non-negative.

        Raises:
            ValueError: If ``length`` is negative.

        Examples:
            >>> v = Vec([1, 2, 3, 4])
            >>> v.truncate(2)
            >>> v
            Vec([1, 2])
        """
        if length < 0:
            raise ValueError(
                "length must be non-negative"
            )

        del self._data[length:]


    def _check_index(self, index: int) -> None:
        if index < 0 or index >= self.len():
            raise IndexError(
                f"index {index} out of bounds "
                f"for Vec of length {self.len()}"
            )

    @overload
    def __getitem__(self, index: int) -> T:
        ...

    @overload
    def __getitem__(self, index: slice) -> Vec[T]:
        ...

    def __getitem__(
        self,
        index: int | slice,
    ) -> T | Vec[T]:
        """Return the element at `index`, or a sub-Vec for a slice.

        Args:
            index (int | slice): The positional index of an element, or a slice.

        Returns:
            T | Vec[T]: The element at the integer index, or a new ``Vec``
                containing the selected range for a slice.

        Raises:
            IndexError: If an integer ``index`` is out of bounds.

        Examples:
            >>> v = Vec([1, 2, 3])
            >>> v[1]
            2
            >>> v[1:]
            Vec([2, 3])
        """
        if isinstance(index, slice):
            return Vec(self._data[index])

        self._check_index(index)
        return self._data[index]

    def get(self, index: int) -> Option[T]:
        """Return the element at `index`, or None_ if out of bounds.

        Args:
            index (int): The index of the element to retrieve.

        Returns:
            Option[T]: ``Some(value)`` if the index is in bounds, otherwise
                ``None_``.

        Examples:
            >>> v = Vec([1, 2])
            >>> v.get(0)
            Some(1)
            >>> v.get(5)
            None_
        """
        if index < 0 or index >= self.len():
            return None_

        return Some(self._data[index])

    def first(self) -> Option[T]:
        """Return the first element, or None_ if empty.

        Returns:
            Option[T]: ``Some`` containing the first element, or ``None_`` if the
                Vec is empty.

        Examples:
            >>> Vec([1, 2]).first()
            Some(1)
            >>> Vec().first()
            None_
        """
        if not self._data:
            return None_

        return Some(self._data[0])

    def last(self) -> Option[T]:
        """Return the last element, or None_ if empty.

        Returns:
            Option[T]: ``Some`` containing the last element, or ``None_`` if the
                Vec is empty.

        Examples:
            >>> Vec([1, 2]).last()
            Some(2)
        """
        if not self._data:
            return None_

        return Some(self._data[-1])

    def contains(self, value: T) -> bool:
        """Return True if the Vec contains the given value.

        Args:
            value (T): The value to search for.

        Returns:
            bool: True if ``value`` is present, otherwise False.

        Examples:
            >>> Vec([1, 2, 3]).contains(2)
            True
        """
        return value in self._data

    def position(
        self,
        predicate: Callable[[T], bool],
    ) -> Option[int]:
        """Return the index of the first element matching the predicate, or None_.

        Args:
            predicate (Callable[[T], bool]): A function returning True for the
                desired element.

        Returns:
            Option[int]: ``Some`` with the index of the first match, or ``None_``
                if no element matches.

        Examples:
            >>> Vec([1, 2, 3]).position(lambda x: x > 1)
            Some(1)
        """
        for index, value in enumerate(self._data):
            if predicate(value):
                return Some(index)

        return None_

    def find(
        self,
        predicate: Callable[[T], bool],
    ) -> Option[T]:
        """Return the first element matching the predicate, or None_.

        Args:
            predicate (Callable[[T], bool]): A function returning True for the
                desired element.

        Returns:
            Option[T]: ``Some`` with the first matching element, or ``None_`` if
                no element matches.

        Examples:
            >>> Vec([1, 2, 3]).find(lambda x: x % 2 == 0)
            Some(2)
        """
        for value in self._data:
            if predicate(value):
                return Some(value)

        return None_

    def reverse(self) -> None:
        """Reverse the order of elements in place.

        Examples:
            >>> v = Vec([1, 2, 3])
            >>> v.reverse()
            >>> v
            Vec([3, 2, 1])
        """
        self._data.reverse()

    def sort(
        self,
        *,
        key: Callable[[T], Any] | None = None,
        reverse: bool = False,
    ) -> None:
        """Sort the elements in place using a stable sort.

        Args:
            key (Callable[[T], Any] | None): A function used to extract a
                comparison key from each element.
            reverse (bool): If True, sort in descending order.

        Examples:
            >>> v = Vec([3, 1, 2])
            >>> v.sort()
            >>> v
            Vec([1, 2, 3])
        """
        self._data.sort(
            key=key,
            reverse=reverse,
        )

    def sort_unstable(
        self,
        *,
        key: Callable[[T], Any] | None = None,
        reverse: bool = False,
    ) -> None:
        """Sort the elements in place using an unstable sort.

        Provided for API parity with Rust. The underlying implementation uses a
        stable sort, but callers should not rely on order preservation.

        Args:
            key (Callable[[T], Any] | None): A function used to extract a
                comparison key from each element.
            reverse (bool): If True, sort in descending order.

        Examples:
            >>> v = Vec([3, 1, 2])
            >>> v.sort_unstable()
            >>> v
            Vec([1, 2, 3])
        """
        self._data.sort(
            key=key,
            reverse=reverse,
        )

    def retain(
        self,
        predicate: Callable[[T], bool],
    ) -> None:
        """Keep only elements for which the predicate returns True.

        Args:
            predicate (Callable[[T], bool]): A function returning True for
                elements to keep.

        Examples:
            >>> v = Vec([1, 2, 3, 4])
            >>> v.retain(lambda x: x % 2 == 0)
            >>> v
            Vec([2, 4])
        """
        self._data[:] = [
            value
            for value in self._data
            if predicate(value)
        ]

    def dedup(self) -> None:
        """Remove consecutive duplicate elements from the Vec.

        Keeps the first occurrence of each run of equal adjacent elements, in
        place.

        Examples:
            >>> v = Vec([1, 1, 2, 2, 2, 3])
            >>> v.dedup()
            >>> v
            Vec([1, 2, 3])
        """
        if len(self._data) < 2:
            return

        result = [self._data[0]]

        for value in self._data[1:]:
            if value != result[-1]:
                result.append(value)

        self._data[:] = result

    def append(self, other: Vec[T]) -> None:
        """Append all elements from another Vec to this one.

        Args:
            other (Vec[T]): The Vec whose elements are appended to the end.

        Examples:
            >>> a = Vec([1, 2])
            >>> a.append(Vec([3, 4]))
            >>> a
            Vec([1, 2, 3, 4])
        """
        self.reserve(other.len())
        self._data.extend(other._data)

    def extend(
        self,
        values: Iterable[T],
    ) -> None:
        """Extend the Vec with elements from an iterable.

        Args:
            values (Iterable[T]): An iterable of elements to append.

        Examples:
            >>> v = Vec([1])
            >>> v.extend([2, 3])
            >>> v
            Vec([1, 2, 3])
        """
        values = list(values)

        self.reserve(len(values))
        self._data.extend(values)

    def split_off(self, at: int) -> Vec[T]:
        """Split the Vec at `at`, returning the tail and keeping the head.

        Leaves the first ``at`` elements in place and returns a new Vec
        containing the elements from index ``at`` onward.

        Args:
            at (int): The split index, in ``[0, len()]``.

        Returns:
            Vec[T]: A new Vec containing the tail elements.

        Raises:
            IndexError: If ``at`` is negative or greater than the length.

        Examples:
            >>> v = Vec([1, 2, 3, 4])
            >>> tail = v.split_off(2)
            >>> v
            Vec([1, 2])
            >>> tail
            Vec([3, 4])
        """
        if at < 0 or at > self.len():
            raise IndexError(
                f"split index {at} out of bounds"
            )

        result = Vec(self._data[at:])
        del self._data[at:]

        return result

    def iter(self) -> Iterator[T]:
        """Return an iterator over the elements.

        Returns:
            Iterator[T]: An iterator yielding each element in order.

        Examples:
            >>> list(Vec([1, 2, 3]).iter())
            [1, 2, 3]
        """
        return iter(self._data)

    def enumerate(self) -> Iterator[tuple[int, T]]:
        """Return an iterator of (index, value) pairs.

        Returns:
            Iterator[tuple[int, T]]: An iterator yielding ``(index, value)``
                pairs.

        Examples:
            >>> list(Vec(['a', 'b']).enumerate())
            [(0, 'a'), (1, 'b')]
        """
        return enumerate(self._data)

    def __iter__(self) -> Iterator[T]:
        """Return an iterator over the elements in order.

        Examples:
            >>> [x for x in Vec([1, 2])]
            [1, 2]
        """
        return iter(self._data)

    def to_list(self) -> list[T]:
        """Return a new list containing a copy of all elements.

        Returns:
            list[T]: A shallow copy of the Vec's elements as a list.

        Examples:
            >>> Vec([1, 2]).to_list()
            [1, 2]
        """
        return self._data.copy()

    def into_iter(self) -> Iterator[T]:
        """Consume the Vec and return an iterator over its elements.

        The Vec is emptied and its capacity reset as a result.

        Returns:
            Iterator[T]: An iterator over the elements before consumption.

        Examples:
            >>> v = Vec([1, 2, 3])
            >>> list(v.into_iter())
            [1, 2, 3]
            >>> v.is_empty()
            True
        """
        data = self._data

        self._data = []
        self._capacity = 0

        return iter(data)

    def __len__(self) -> int:
        """Return the number of elements in the Vec.

        Examples:
            >>> len(Vec([1, 2, 3]))
            3
        """
        return self.len()

    def __bool__(self) -> bool:
        """Return True if the Vec is non-empty.

        Examples:
            >>> bool(Vec([1]))
            True
        """
        return not self.is_empty()

    def __contains__(self, value: object) -> bool:
        """Return True if the Vec contains the given value.

        Examples:
            >>> 2 in Vec([1, 2])
            True
        """
        return value in self._data

    def __repr__(self) -> str:
        """Return a string representation of the Vec.

        Examples:
            >>> repr(Vec([1, 2]))
            'Vec([1, 2])'
        """
        return f"Vec({self._data!r})"

    def __eq__(self, other: object) -> bool:
        """Return True if the Vec equals another Vec.

        Two Vecs are equal when they contain the same elements in the same order.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: True if ``other`` is a Vec with equal contents; ``NotImplemented``
                otherwise.

        Examples:
            >>> Vec([1, 2]) == Vec([1, 2])
            True
        """
        if isinstance(other, Vec):
            return self._data == other._data

        return NotImplemented
