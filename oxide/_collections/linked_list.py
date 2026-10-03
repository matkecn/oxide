"""LinkedList — a doubly-linked list.

Provides ``LinkedList`` (and its node type ``LinkedListNode``), a doubly-linked
list supporting O(1) push/pop at both ends and forward/reverse iteration,
analogous to Rust's ``std::collections::LinkedList``.
"""
from __future__ import annotations

from typing import Generic, Iterable, Iterator, TypeVar

from .extra import Drain

T = TypeVar("T")


class LinkedListNode(Generic[T]):
    """A node in a doubly-linked list containing a value and pointers to adjacent nodes.

    Each node stores a value and references to the next and previous nodes. Users
    typically do not construct nodes directly; they are created internally by
    :class:`LinkedList`.

    Examples:
        >>> node = LinkedListNode(1)
        >>> node.value
        1
    """

    __slots__ = ("value", "next", "prev")

    def __init__(self, value: T) -> None:
        """Initialize a node with the given value.

        Args:
            value (T): The value to store in the node.

        Examples:
            >>> n = LinkedListNode(5)
            >>> n.value
            5
            >>> n.next is None and n.prev is None
            True
        """
        self.value = value
        self.next: LinkedListNode[T] | None = None
        self.prev: LinkedListNode[T] | None = None


class LinkedList(Generic[T]):
    """A doubly-linked list with push/pop operations at both ends.

    ``LinkedList`` provides constant-time insertion and removal at either end,
    plus forward and reverse iteration via :meth:`iter` and :meth:`iter_rev`.
    Operations in the middle are not provided; use a different container for
    random access.

    Examples:
        >>> ll = LinkedList([1, 2, 3])
        >>> ll.push_front(0)
        >>> ll.pop_back()
        3
        >>> list(ll.iter())
        [0, 1, 2]
    """

    __slots__ = ("_head", "_tail", "_len")

    def __init__(self, values: Iterable[T] | None = None) -> None:
        """Initialize a LinkedList, optionally from an iterable of values.

        Args:
            values (Iterable[T] | None): Initial elements, front to back.
                Defaults to empty.

        Examples:
            >>> LinkedList([1, 2])
            LinkedList([1, 2])
        """
        self._head: LinkedListNode[T] | None = None
        self._tail: LinkedListNode[T] | None = None
        self._len = 0
        if values is not None:
            for v in values:
                self.push_back(v)

    @classmethod
    def new(cls) -> LinkedList[T]:
        """Create a new empty LinkedList.

        Returns:
            LinkedList[T]: An empty list.

        Examples:
            >>> LinkedList.new()
            LinkedList([])
        """
        return cls()

    @classmethod
    def from_iter(cls, values: Iterable[T]) -> LinkedList[T]:
        """Create a LinkedList from an iterable of values.

        Args:
            values (Iterable[T]): An iterable whose elements populate the list,
                front to back.

        Returns:
            LinkedList[T]: A new list containing the elements of ``values``.

        Examples:
            >>> LinkedList.from_iter([1, 2])
            LinkedList([1, 2])
        """
        return cls(values)

    def push_front(self, value: T) -> None:
        """Add a value to the front of the list.

        Args:
            value (T): The value to add.

        Examples:
            >>> ll = LinkedList([1])
            >>> ll.push_front(0)
            >>> list(ll.iter())
            [0, 1]
        """
        node = LinkedListNode(value)
        if self._head is None:
            self._head = node
            self._tail = node
        else:
            node.next = self._head
            self._head.prev = node
            self._head = node
        self._len += 1

    def push_back(self, value: T) -> None:
        """Add a value to the back of the list.

        Args:
            value (T): The value to add.

        Examples:
            >>> ll = LinkedList([1])
            >>> ll.push_back(2)
            >>> list(ll.iter())
            [1, 2]
        """
        node = LinkedListNode(value)
        if self._tail is None:
            self._head = node
            self._tail = node
        else:
            node.prev = self._tail
            self._tail.next = node
            self._tail = node
        self._len += 1

    def pop_front(self) -> T | None:
        """Remove and return the front element, or None if empty.

        Returns:
            T | None: The first element, or None if the list is empty.

        Examples:
            >>> ll = LinkedList([1, 2])
            >>> ll.pop_front()
            1
        """
        if self._head is None:
            return None
        value = self._head.value
        if self._head == self._tail:
            self._head = None
            self._tail = None
        else:
            self._head = self._head.next
            if self._head:
                self._head.prev = None
        self._len -= 1
        return value

    def pop_back(self) -> T | None:
        """Remove and return the back element, or None if empty.

        Returns:
            T | None: The last element, or None if the list is empty.

        Examples:
            >>> ll = LinkedList([1, 2])
            >>> ll.pop_back()
            2
        """
        if self._tail is None:
            return None
        value = self._tail.value
        if self._head == self._tail:
            self._head = None
            self._tail = None
        else:
            self._tail = self._tail.prev
            if self._tail:
                self._tail.next = None
        self._len -= 1
        return value

    def front(self) -> T | None:
        """Return the value at the front, or None if empty.

        Returns:
            T | None: The first element's value, or None if empty.

        Examples:
            >>> LinkedList([1, 2]).front()
            1
        """
        return self._head.value if self._head else None

    def back(self) -> T | None:
        """Return the value at the back, or None if empty.

        Returns:
            T | None: The last element's value, or None if empty.

        Examples:
            >>> LinkedList([1, 2]).back()
            2
        """
        return self._tail.value if self._tail else None

    def len(self) -> int:
        """Return the number of elements in the list.

        Returns:
            int: The number of elements.

        Examples:
            >>> LinkedList([1, 2]).len()
            2
        """
        return self._len

    def is_empty(self) -> bool:
        """Return True if the list contains no elements.

        Returns:
            bool: True if the list is empty.

        Examples:
            >>> LinkedList().is_empty()
            True
        """
        return self._len == 0

    def clear(self) -> None:
        """Remove all elements from the list.

        Examples:
            >>> ll = LinkedList([1, 2])
            >>> ll.clear()
            >>> ll.is_empty()
            True
        """
        self._head = None
        self._tail = None
        self._len = 0

    def contains(self, value: T) -> bool:
        """Return True if the list contains the given value.

        Args:
            value (T): The value to search for.

        Returns:
            bool: True if ``value`` is present.

        Examples:
            >>> LinkedList([1, 2]).contains(2)
            True
        """
        node = self._head
        while node:
            if node.value == value:
                return True
            node = node.next
        return False

    def reverse(self) -> None:
        """Reverse the order of elements in place.

        Examples:
            >>> ll = LinkedList([1, 2, 3])
            >>> ll.reverse()
            >>> list(ll.iter())
            [3, 2, 1]
        """
        node = self._head
        while node:
            node.next, node.prev = node.prev, node.next
            node = node.prev
        self._head, self._tail = self._tail, self._head

    def iter(self) -> Iterator[T]:
        """Return an iterator over elements from front to back.

        Yields:
            Iterator[T]: Each element from front to back.

        Examples:
            >>> list(LinkedList([1, 2]).iter())
            [1, 2]
        """
        node = self._head
        while node:
            yield node.value
            node = node.next

    def iter_rev(self) -> Iterator[T]:
        """Return an iterator over elements from back to front.

        Yields:
            Iterator[T]: Each element from back to front.

        Examples:
            >>> list(LinkedList([1, 2]).iter_rev())
            [2, 1]
        """
        node = self._tail
        while node:
            yield node.value
            node = node.prev

    def drain(self) -> Drain[T]:
        """Consume the list and return a Drain iterator over its elements.

        The list is emptied as a result.

        Returns:
            Drain[T]: An iterator yielding the elements in order.

        Examples:
            >>> ll = LinkedList([1, 2])
            >>> list(ll.drain())
            [1, 2]
            >>> ll.is_empty()
            True
        """
        items = list(self.iter())
        self.clear()
        return Drain(items)

    def to_list(self) -> list[T]:
        """Return a new list containing all elements from front to back.

        Returns:
            list[T]: A list of the elements in order.

        Examples:
            >>> LinkedList([1, 2]).to_list()
            [1, 2]
        """
        return list(self.iter())

    def __len__(self) -> int:
        """Return the number of elements in the list.

        Examples:
            >>> len(LinkedList([1, 2]))
            2
        """
        return self._len

    def __iter__(self) -> Iterator[T]:
        """Return an iterator over elements from front to back.

        Examples:
            >>> [x for x in LinkedList([1, 2])]
            [1, 2]
        """
        return self.iter()

    def __contains__(self, value: object) -> bool:
        """Return True if the list contains the value.

        Examples:
            >>> 2 in LinkedList([1, 2])
            True
        """
        return self.contains(value)  # type: ignore[arg-type]

    def __repr__(self) -> str:
        """Return a string representation of the list.

        Examples:
            >>> repr(LinkedList([1, 2]))
            'LinkedList([1, 2])'
        """
        return f"LinkedList({self.to_list()})"

    def __eq__(self, other: object) -> bool:
        """Return True if the list equals another LinkedList.

        Two lists are equal when they contain the same elements in the same
        order.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: True if ``other`` is a ``LinkedList`` with equal contents;
                ``NotImplemented`` otherwise.

        Examples:
            >>> LinkedList([1, 2]) == LinkedList([1, 2])
            True
        """
        if isinstance(other, LinkedList):
            return self.to_list() == other.to_list()
        return NotImplemented

    def __hash__(self) -> int:
        """Return a hash of the list's contents.

        Returns:
            int: A hash based on the elements in order.
        """
        return hash(tuple(self.iter()))

    def __bool__(self) -> bool:
        """Return True if the list is non-empty.

        Examples:
            >>> bool(LinkedList([1]))
            True
        """
        return self._len > 0
