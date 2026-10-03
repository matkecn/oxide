"""VecDeque — a double-ended queue with O(1) push/pop at both ends.

Provides ``VecDeque``, a double-ended queue (analogous to Rust's
``std::collections::VecDeque``) that supports efficient insertion and removal at
both the front and the back, plus rotation and draining operations.
"""
from __future__ import annotations

from typing import Generic, Iterable, Iterator, TypeVar

from ..core.option import Option, Some, None_
from .extra import Drain

T = TypeVar("T")


class VecDeque(Generic[T]):
    """A double-ended queue with O(1) push/pop at both ends.

    ``VecDeque`` supports efficient access, insertion, and removal at both ends.
    Use :meth:`push_back`/:meth:`pop_back` for stack-like behavior and
    :meth:`push_front`/:meth:`pop_front` for queue-like behavior, and
    :meth:`rotate_left`/:meth:`rotate_right` to cycle elements.

    Examples:
        >>> d = VecDeque([1, 2, 3])
        >>> d.push_front(0)
        >>> d.pop_back()
        Some(3)
        >>> list(d.iter())
        [0, 1, 2]
    """

    __slots__ = ("_data",)

    def __init__(self, values: Iterable[T] | None = None) -> None:
        """Initialize a VecDeque, optionally from an iterable of values.

        Args:
            values (Iterable[T] | None): Initial elements, front to back.
                Defaults to empty.

        Examples:
            >>> VecDeque([1, 2])
            VecDeque([1, 2])
        """
        self._data: list[T] = list(values) if values else []

    @classmethod
    def new(cls) -> VecDeque[T]:
        """Create a new empty VecDeque.

        Returns:
            VecDeque[T]: An empty deque.

        Examples:
            >>> VecDeque.new()
            VecDeque([])
        """
        return cls()

    @classmethod
    def with_capacity(cls, capacity: int) -> VecDeque[T]:
        """Create a new VecDeque (capacity hint is accepted for API compatibility).

        Args:
            capacity (int): An ignored capacity hint, for API compatibility.

        Returns:
            VecDeque[T]: An empty deque.
        """
        return cls()

    @classmethod
    def from_iter(cls, values: Iterable[T]) -> VecDeque[T]:
        """Create a VecDeque from an iterable of values.

        Args:
            values (Iterable[T]): An iterable whose elements populate the deque
                from front to back.

        Returns:
            VecDeque[T]: A new deque containing the elements of ``values``.

        Examples:
            >>> VecDeque.from_iter([1, 2])
            VecDeque([1, 2])
        """
        return cls(values)

    def push_back(self, value: T) -> None:
        """Add an element to the back of the deque.

        Args:
            value (T): The value to add.

        Examples:
            >>> d = VecDeque([1])
            >>> d.push_back(2)
            >>> list(d.iter())
            [1, 2]
        """
        self._data.append(value)

    def push_front(self, value: T) -> None:
        """Add an element to the front of the deque.

        Args:
            value (T): The value to add.

        Examples:
            >>> d = VecDeque([1])
            >>> d.push_front(0)
            >>> list(d.iter())
            [0, 1]
        """
        self._data.insert(0, value)

    def pop_back(self) -> Option[T]:
        """Remove and return the back element.

        Returns:
            Option[T]: ``Some(last)``, or ``None_`` if the deque is empty.

        Examples:
            >>> d = VecDeque([1, 2])
            >>> d.pop_back()
            Some(2)
            >>> VecDeque().pop_back()
            None_
        """
        if self._data:
            return Some(self._data.pop())
        return None_

    def pop_front(self) -> Option[T]:
        """Remove and return the front element.

        Returns:
            Option[T]: ``Some(first)``, or ``None_`` if the deque is empty.

        Examples:
            >>> d = VecDeque([1, 2])
            >>> d.pop_front()
            Some(1)
            >>> VecDeque().pop_front()
            None_
        """
        if self._data:
            return Some(self._data.pop(0))
        return None_

    def front(self) -> T | None:
        """Return a reference to the front element, or None if empty.

        Returns:
            T | None: The first element, or None if the deque is empty.

        Examples:
            >>> VecDeque([1, 2]).front()
            1
        """
        return self._data[0] if self._data else None

    def back(self) -> T | None:
        """Return a reference to the back element, or None if empty.

        Returns:
            T | None: The last element, or None if the deque is empty.

        Examples:
            >>> VecDeque([1, 2]).back()
            2
        """
        return self._data[-1] if self._data else None

    def get(self, index: int) -> T | None:
        """Return the element at `index`, or None if out of bounds.

        Args:
            index (int): The index of the element to retrieve.

        Returns:
            T | None: The element if the index is in bounds, otherwise None.

        Examples:
            >>> d = VecDeque([1, 2])
            >>> d.get(0)
            1
            >>> d.get(5) is None
            True
        """
        if 0 <= index < len(self._data):
            return self._data[index]
        return None

    def len(self) -> int:
        """Return the number of elements in the deque.

        Returns:
            int: The number of elements.

        Examples:
            >>> VecDeque([1, 2]).len()
            2
        """
        return len(self._data)

    def is_empty(self) -> bool:
        """Return True if the deque contains no elements.

        Returns:
            bool: True if the deque is empty.

        Examples:
            >>> VecDeque().is_empty()
            True
        """
        return len(self._data) == 0

    def clear(self) -> None:
        """Remove all elements from the deque.

        Examples:
            >>> d = VecDeque([1, 2])
            >>> d.clear()
            >>> d.is_empty()
            True
        """
        self._data.clear()

    def insert(self, index: int, value: T) -> None:
        """Insert a value at the given index.

        Args:
            index (int): The position at which to insert.
            value (T): The value to insert.

        Examples:
            >>> d = VecDeque([1, 3])
            >>> d.insert(1, 2)
            >>> list(d.iter())
            [1, 2, 3]
        """
        self._data.insert(index, value)

    def remove(self, index: int) -> T | None:
        """Remove and return the element at `index`, or None if out of bounds.

        Args:
            index (int): The index of the element to remove.

        Returns:
            T | None: The removed element, or None if out of bounds.

        Examples:
            >>> d = VecDeque([1, 2, 3])
            >>> d.remove(1)
            2
        """
        if 0 <= index < len(self._data):
            return self._data.pop(index)
        return None

    def contains(self, value: T) -> bool:
        """Return True if the deque contains the given value.

        Args:
            value (T): The value to search for.

        Returns:
            bool: True if ``value`` is present.

        Examples:
            >>> VecDeque([1, 2]).contains(2)
            True
        """
        return value in self._data

    def rotate_left(self, k: int) -> None:
        """Rotate the deque to the left by `k` positions.

        Moves the first ``k`` elements to the back. ``k`` is taken modulo the
        deque length; a no-op on an empty deque.

        Args:
            k (int): The number of positions to rotate left.

        Examples:
            >>> d = VecDeque([1, 2, 3])
            >>> d.rotate_left(1)
            >>> list(d.iter())
            [2, 3, 1]
        """
        if self._data:
            k = k % len(self._data)
            self._data = self._data[k:] + self._data[:k]

    def rotate_right(self, k: int) -> None:
        """Rotate the deque to the right by `k` positions.

        Moves the last ``k`` elements to the front. ``k`` is taken modulo the
        deque length; a no-op on an empty deque.

        Args:
            k (int): The number of positions to rotate right.

        Examples:
            >>> d = VecDeque([1, 2, 3])
            >>> d.rotate_right(1)
            >>> list(d.iter())
            [3, 1, 2]
        """
        if self._data:
            k = k % len(self._data)
            self._data = self._data[-k:] + self._data[:-k]

    def truncate(self, length: int) -> None:
        """Shorten the deque to `length` elements, dropping the rest.

        Args:
            length (int): The desired length.

        Examples:
            >>> d = VecDeque([1, 2, 3, 4])
            >>> d.truncate(2)
            >>> list(d.iter())
            [1, 2]
        """
        del self._data[length:]

    def drain(self) -> Drain[T]:
        """Consume the deque and return a Drain iterator over its elements.

        Returns:
            Drain[T]: An iterator that yields the elements and clears the deque.

        Examples:
            >>> d = VecDeque([1, 2])
            >>> list(d.drain())
            [1, 2]
            >>> d.is_empty()
            True
        """
        return Drain(self._data)

    def iter(self) -> Iterator[T]:
        """Return an iterator over the elements from front to back.

        Returns:
            Iterator[T]: An iterator yielding elements front to back.

        Examples:
            >>> list(VecDeque([1, 2]).iter())
            [1, 2]
        """
        return iter(self._data)

    def __len__(self) -> int:
        """Return the number of elements in the deque.

        Examples:
            >>> len(VecDeque([1, 2]))
            2
        """
        return len(self._data)

    def __iter__(self) -> Iterator[T]:
        """Return an iterator over the elements from front to back.

        Examples:
            >>> [x for x in VecDeque([1, 2])]
            [1, 2]
        """
        return iter(self._data)

    def __getitem__(self, index: int) -> T:
        """Return the element at the given index.

        Args:
            index (int): The index to retrieve.

        Returns:
            T: The element at ``index``.

        Examples:
            >>> VecDeque([1, 2])[0]
            1
        """
        return self._data[index]

    def __setitem__(self, index: int, value: T) -> None:
        """Set the element at the given index.

        Args:
            index (int): The index to write.
            value (T): The new value.

        Examples:
            >>> d = VecDeque([1, 2])
            >>> d[0] = 9
            >>> list(d.iter())
            [9, 2]
        """
        self._data[index] = value

    def __contains__(self, value: object) -> bool:
        """Return True if the deque contains the value.

        Examples:
            >>> 2 in VecDeque([1, 2])
            True
        """
        return value in self._data

    def __repr__(self) -> str:
        """Return a string representation of the deque.

        Examples:
            >>> repr(VecDeque([1, 2]))
            'VecDeque([1, 2])'
        """
        return f"VecDeque({self._data!r})"

    def __eq__(self, other: object) -> bool:
        """Return True if the deque equals another VecDeque.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: True if ``other`` is a ``VecDeque`` with equal contents;
                ``NotImplemented`` otherwise.

        Examples:
            >>> VecDeque([1, 2]) == VecDeque([1, 2])
            True
        """
        if isinstance(other, VecDeque):
            return self._data == other._data
        return NotImplemented

    def __hash__(self) -> int:
        """Return a hash of the deque's contents.

        Returns:
            int: A hash based on the elements in order.
        """
        return hash(tuple(self._data))

    def __bool__(self) -> bool:
        """Return True if the deque is non-empty.

        Examples:
            >>> bool(VecDeque([1]))
            True
        """
        return bool(self._data)
