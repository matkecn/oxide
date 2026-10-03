"""BinaryHeap — a max-heap priority queue.

Provides ``BinaryHeap``, a priority queue implemented as a binary heap
(analogous to Rust's ``std::collections::BinaryHeap``). By default it is a
max-heap; set ``reverse=True`` to obtain a min-heap. It supports push, pop,
peek, and bulk-conversion operations.
"""
from __future__ import annotations

from typing import Generic, Iterable, Iterator, TypeVar

T = TypeVar("T")


class BinaryHeap(Generic[T]):
    """A priority queue implemented as a binary heap.

    ``BinaryHeap`` always exposes the greatest element (for a max-heap) or the
    smallest element (for a min-heap created with ``reverse=True``) at the top.
    Construct with ``reverse=True`` for min-heap semantics.

    Examples:
        >>> h = BinaryHeap([1, 3, 2])
        >>> h.peek()
        3
        >>> h.pop()
        3
        >>> h.push(9)
        >>> h.peek()
        9

        Min-heap:
        >>> h = BinaryHeap([1, 3, 2], reverse=True)
        >>> h.pop()
        1
    """

    __slots__ = ("_data", "_reverse")

    def __init__(self, values: Iterable[T] | None = None, *, reverse: bool = False) -> None:
        """Initialize a BinaryHeap, optionally from values and with polarity.

        Args:
            values (Iterable[T] | None): Initial elements to heapify. Defaults to
                empty.
            reverse (bool): If True, the heap is a min-heap (smallest popped
                first); otherwise a max-heap. Defaults to False.

        The elements are stored in pop order, so a max-heap lists them
        largest first.

        Examples:
            >>> BinaryHeap([3, 1, 2])
            BinaryHeap([3, 2, 1])
            >>> BinaryHeap([3, 1, 2], reverse=True)
            BinaryHeap([1, 2, 3])
        """
        self._data: list[T] = list(values) if values else []
        self._reverse = reverse
        self._data.sort(reverse=not reverse)

    @classmethod
    def new(cls) -> BinaryHeap[T]:
        """Create a new empty BinaryHeap.

        Returns:
            BinaryHeap[T]: An empty max-heap.

        Examples:
            >>> BinaryHeap.new()
            BinaryHeap([])
        """
        return cls()

    @classmethod
    def with_capacity(cls, capacity: int) -> BinaryHeap[T]:
        """Create a new BinaryHeap (capacity hint is accepted for API compatibility).

        Args:
            capacity (int): An ignored capacity hint, for API compatibility.

        Returns:
            BinaryHeap[T]: An empty heap.
        """
        return cls()

    @classmethod
    def from_iter(cls, values: Iterable[T], *, reverse: bool = False) -> BinaryHeap[T]:
        """Create a BinaryHeap from an iterable of values.

        Args:
            values (Iterable[T]): Initial elements to heapify.
            reverse (bool): If True, create a min-heap. Defaults to False.

        Returns:
            BinaryHeap[T]: A new heap containing the elements.

        Examples:
            >>> BinaryHeap.from_iter([1, 3, 2])
            BinaryHeap([3, 2, 1])
        """
        return cls(values, reverse=reverse)

    def push(self, value: T) -> None:
        """Add a value to the heap, maintaining heap order.

        Args:
            value (T): The value to add.

        Examples:
            >>> h = BinaryHeap([1])
            >>> h.push(5)
            >>> h.peek()
            5
        """
        self._data.append(value)
        self._data.sort(reverse=not self._reverse)

    def pop(self) -> T | None:
        """Remove and return the top element, or None if empty.

        For a max-heap this is the greatest element; for a min-heap the smallest.

        Returns:
            T | None: The top element, or None if the heap is empty.

        Examples:
            >>> h = BinaryHeap([1, 3, 2])
            >>> h.pop()
            3
        """
        if self._data:
            return self._data.pop(0)
        return None

    def peek(self) -> T | None:
        """Return a reference to the top element without removing it.

        Returns:
            T | None: The top element, or None if the heap is empty.

        Examples:
            >>> h = BinaryHeap([1, 3, 2])
            >>> h.peek()
            3
        """
        return self._data[0] if self._data else None

    def push_pop(self, push_value: T) -> T:
        """Push a value and immediately pop the top, returning the popped value.

        Pushes ``push_value`` then pops and returns the top of the resulting
        heap.

        Args:
            push_value (T): The value to push.

        Returns:
            T: The value popped after pushing.

        Examples:
            >>> h = BinaryHeap([1, 2])
            >>> h.push_pop(9)
            9
            >>> h.peek()
            2
        """
        self.push(push_value)
        return self.pop()  # type: ignore

    def peek_mut(self) -> T | None:
        """Return a mutable reference to the top element without removing it.

        This is an alias of :meth:`peek`; it does not actually provide a mutable
        reference.

        Returns:
            T | None: The top element, or None if the heap is empty.
        """
        return self.peek()

    def len(self) -> int:
        """Return the number of elements in the heap.

        Returns:
            int: The number of elements.

        Examples:
            >>> BinaryHeap([1, 2]).len()
            2
        """
        return len(self._data)

    def is_empty(self) -> bool:
        """Return True if the heap contains no elements.

        Returns:
            bool: True if the heap is empty.

        Examples:
            >>> BinaryHeap().is_empty()
            True
        """
        return len(self._data) == 0

    def clear(self) -> None:
        """Remove all elements from the heap.

        Examples:
            >>> h = BinaryHeap([1, 2])
            >>> h.clear()
            >>> h.is_empty()
            True
        """
        self._data.clear()

    def contains(self, value: T) -> bool:
        """Return True if the heap contains the given value.

        Args:
            value (T): The value to search for.

        Returns:
            bool: True if ``value`` is present.

        Examples:
            >>> BinaryHeap([1, 2]).contains(2)
            True
        """
        return value in self._data

    def drain(self) -> Iterator[T]:
        """Consume the heap and return elements in sorted (heap) order.

        Returns elements from top to bottom. The heap is emptied as a result.

        Returns:
            Iterator[T]: An iterator over the elements in heap order.

        Examples:
            >>> h = BinaryHeap([1, 3, 2])
            >>> list(h.drain())
            [3, 2, 1]
        """
        items = sorted(self._data, reverse=not self._reverse)
        self._data.clear()
        return iter(items)

    def iter(self) -> Iterator[T]:
        """Return an iterator over elements in heap order.

        Returns:
            Iterator[T]: An iterator yielding elements from top to bottom.

        Examples:
            >>> list(BinaryHeap([1, 3, 2]).iter())
            [3, 2, 1]
        """
        return iter(sorted(self._data, reverse=not self._reverse))

    def to_list(self) -> list[T]:
        """Return a list of elements in heap order.

        Returns:
            list[T]: The elements sorted from top to bottom.

        Examples:
            >>> BinaryHeap([1, 3, 2]).to_list()
            [3, 2, 1]
        """
        return sorted(self._data, reverse=not self._reverse)

    def __len__(self) -> int:
        """Return the number of elements in the heap.

        Examples:
            >>> len(BinaryHeap([1, 2]))
            2
        """
        return len(self._data)

    def __iter__(self) -> Iterator[T]:
        """Return an iterator over elements in heap order.

        Examples:
            >>> list(BinaryHeap([1, 3, 2]))
            [3, 2, 1]
        """
        return self.iter()

    def __contains__(self, value: object) -> bool:
        """Return True if the heap contains the value.

        Examples:
            >>> 2 in BinaryHeap([1, 2])
            True
        """
        return value in self._data

    def __repr__(self) -> str:
        """Return a string representation of the heap.

        Elements are listed in pop order: largest first for a max-heap,
        smallest first for a min-heap.

        Examples:
            >>> repr(BinaryHeap([1, 2]))
            'BinaryHeap([2, 1])'
            >>> repr(BinaryHeap([1, 2], reverse=True))
            'BinaryHeap([1, 2])'
        """
        return f"BinaryHeap({self._data!r})"

    def __eq__(self, other: object) -> bool:
        """Return True if the heap has the same elements as another BinaryHeap.

        Order is ignored.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: True if ``other`` is a ``BinaryHeap`` with the same set of
                elements; ``NotImplemented`` otherwise.

        Examples:
            >>> BinaryHeap([1, 2]) == BinaryHeap([2, 1])
            True
        """
        if isinstance(other, BinaryHeap):
            return sorted(self._data) == sorted(other._data)
        return NotImplemented

    def __hash__(self) -> int:
        """Return a hash of the heap's contents.

        Returns:
            int: A hash based on the sorted elements.
        """
        return hash(tuple(sorted(self._data)))

    def __bool__(self) -> bool:
        """Return True if the heap is non-empty.

        Examples:
            >>> bool(BinaryHeap([1]))
            True
        """
        return bool(self._data)
