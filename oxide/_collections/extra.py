"""Drain, IntoIter, Slice — supporting iterator and view types for collections.

Provides ``Drain`` and ``IntoIter``, iterator types for consuming collection
contents, and ``Slice``, a borrowed view into a contiguous sequence of elements.
"""
from __future__ import annotations

from typing import Generic, Iterable, Iterator, Sequence, TypeVar

T = TypeVar("T")


class Drain(Generic[T]):
    """An iterator that consumes a list, yielding elements and clearing the source.

    ``Drain`` wraps a list and yields its elements while incrementing an internal
    index; when exhausted, it clears the source list. Iterating over it consumes
    the backing collection.

    Examples:
        >>> data = [1, 2, 3]
        >>> d = Drain(data)
        >>> list(d)
        [1, 2, 3]
        >>> data
        []
    """

    __slots__ = ("_source", "_index")

    def __init__(self, source: list[T]) -> None:
        """Initialize a Drain over a list.

        Args:
            source (list[T]): The list to drain; it will be cleared when
                exhausted.
        """
        self._source = source
        self._index = 0

    def __iter__(self) -> Iterator[T]:
        """Yield the remaining elements and clear the source when exhausted.

        Yields:
            Iterator[T]: Each element of the source not yet yielded.
        """
        while self._index < len(self._source):
            yield self._source[self._index]
            self._index += 1
        self._source.clear()

    def __next__(self) -> T:
        """Return the next element, raising StopIteration when exhausted.

        Returns:
            T: The next element.

        Raises:
            StopIteration: When all elements have been yielded.
        """
        if self._index >= len(self._source):
            raise StopIteration
        value = self._source[self._index]
        self._index += 1
        return value

    def __repr__(self) -> str:
        """Return a string representation of the remaining count.

        Examples:
            >>> repr(Drain([1, 2, 3]))
            'Drain(remaining=3)'
        """
        return f"Drain(remaining={len(self._source) - self._index})"


class IntoIter(Generic[T]):
    """An owning iterator that wraps an iterable's iterator for consumption.

    ``IntoIter`` is a thin wrapper around the iterator produced by calling
    ``iter()`` on a source iterable, providing a unified iterator interface.

    Examples:
        >>> it = IntoIter([1, 2, 3])
        >>> list(it)
        [1, 2, 3]
    """

    __slots__ = ("_iter",)

    def __init__(self, source: Iterable[T]) -> None:
        """Initialize an IntoIter over an iterable.

        Args:
            source (Iterable[T]): Any iterable to consume.
        """
        self._iter = iter(source)

    def __iter__(self) -> Iterator[T]:
        """Return the underlying iterator.

        Returns:
            Iterator[T]: The wrapped iterator.
        """
        return self._iter

    def __next__(self) -> T:
        """Return the next element, raising StopIteration when exhausted.

        Returns:
            T: The next element.

        Raises:
            StopIteration: When all elements have been consumed.
        """
        return next(self._iter)

    def __repr__(self) -> str:
        """Return an opaque string representation.

        Examples:
            >>> repr(IntoIter([1]))
            'IntoIter(...)'
        """
        return "IntoIter(...)"


class Slice(Generic[T]):
    """A borrowed view into a contiguous sequence of elements.

    ``Slice`` provides a read-only window into a ``Sequence``, defined by a start
    and end offset, without copying the underlying data. It supports indexed
    access and iteration restricted to the window.

    Examples:
        >>> s = Slice([1, 2, 3, 4], 1, 3)
        >>> s.to_list()
        [2, 3]
        >>> s.first()
        2
    """

    __slots__ = ("_data", "_start", "_end")

    def __init__(self, data: Sequence[T], start: int = 0, end: int | None = None) -> None:
        """Initialize a Slice over a portion of a sequence.

        Args:
            data (Sequence[T]): The underlying sequence to view.
            start (int): The inclusive start offset. Defaults to 0.
            end (int | None): The exclusive end offset. Defaults to the length
                of ``data``.

        Examples:
            >>> s = Slice([1, 2, 3], 0, 2)
            >>> s.to_list()
            [1, 2]
        """
        self._data = data
        self._start = start
        self._end = end if end is not None else len(data)

    @classmethod
    def from_list(cls, data: Sequence[T]) -> Slice[T]:
        """Create a Slice covering the entire sequence.

        Args:
            data (Sequence[T]): The sequence to view entirely.

        Returns:
            Slice[T]: A slice spanning all of ``data``.

        Examples:
            >>> Slice.from_list([1, 2, 3]).len()
            3
        """
        return cls(data)

    def get(self, index: int) -> T:
        """Return the element at the given offset within the slice.

        ``index`` is relative to the slice start, not the underlying sequence.

        Args:
            index (int): The zero-based offset within the slice.

        Returns:
            T: The element at that offset.

        Examples:
            >>> Slice([1, 2, 3], 1).get(0)
            2
        """
        return self._data[self._start + index]

    def first(self) -> T | None:
        """Return the first element in the slice, or None if empty.

        Returns:
            T | None: The first element, or None if the slice is empty.

        Examples:
            >>> Slice([1, 2]).first()
            1
        """
        if self._start >= self._end:
            return None
        return self._data[self._start]

    def last(self) -> T | None:
        """Return the last element in the slice, or None if empty.

        Returns:
            T | None: The last element, or None if the slice is empty.

        Examples:
            >>> Slice([1, 2]).last()
            2
        """
        if self._start >= self._end:
            return None
        return self._data[self._end - 1]

    def len(self) -> int:
        """Return the number of elements in the slice.

        Returns:
            int: The number of elements in the window.

        Examples:
            >>> Slice([1, 2, 3], 1, 3).len()
            2
        """
        return self._end - self._start

    def is_empty(self) -> bool:
        """Return True if the slice contains no elements.

        Returns:
            bool: True if the slice is empty.

        Examples:
            >>> Slice([1, 2], 1, 1).is_empty()
            True
        """
        return self._start >= self._end

    def contains(self, value: T) -> bool:
        """Return True if the slice contains the given value.

        Args:
            value (T): The value to search for.

        Returns:
            bool: True if ``value`` is present within the window.

        Examples:
            >>> Slice([1, 2, 3]).contains(2)
            True
        """
        for i in range(self._start, self._end):
            if self._data[i] == value:
                return True
        return False

    def split_at(self, mid: int) -> tuple[Slice[T], Slice[T]]:
        """Split the slice at `mid`, returning two sub-slices.

        The first sub-slice covers offsets ``[0, mid)`` and the second covers
        ``[mid, len)``.

        Args:
            mid (int): The offset at which to split.

        Returns:
            tuple[Slice[T], Slice[T]]: The left and right sub-slices.

        Examples:
            >>> a, b = Slice([1, 2, 3, 4]).split_at(2)
            >>> a.to_list(), b.to_list()
            ([1, 2], [3, 4])
        """
        return (
            Slice(self._data, self._start, self._start + mid),
            Slice(self._data, self._start + mid, self._end),
        )

    def iter(self) -> Iterator[T]:
        """Return an iterator over the elements in the slice.

        Yields:
            Iterator[T]: Each element within the window, in order.

        Examples:
            >>> list(Slice([1, 2, 3]).iter())
            [1, 2, 3]
        """
        for i in range(self._start, self._end):
            yield self._data[i]

    def to_list(self) -> list[T]:
        """Return a new list containing the elements in the slice.

        Returns:
            list[T]: A list copy of the windowed elements.

        Examples:
            >>> Slice([1, 2, 3]).to_list()
            [1, 2, 3]
        """
        return list(self._data[self._start:self._end])

    def __len__(self) -> int:
        """Return the number of elements in the slice.

        Examples:
            >>> len(Slice([1, 2, 3]))
            3
        """
        return self.len()

    def __iter__(self) -> Iterator[T]:
        """Return an iterator over the elements in the slice.

        Examples:
            >>> [x for x in Slice([1, 2])]
            [1, 2]
        """
        return self.iter()

    def __getitem__(self, index: int) -> T:
        """Return the element at the given offset within the slice.

        Args:
            index (int): The zero-based offset within the slice.

        Returns:
            T: The element at that offset.

        Examples:
            >>> Slice([1, 2, 3])[1]
            2
        """
        return self.get(index)

    def __contains__(self, value: object) -> bool:
        """Return True if the slice contains the value.

        Examples:
            >>> 2 in Slice([1, 2])
            True
        """
        return self.contains(value)  # type: ignore[arg-type]

    def __repr__(self) -> str:
        """Return a string representation of the slice.

        Examples:
            >>> repr(Slice([1, 2]))
            'Slice([1, 2])'
        """
        return f"Slice({self.to_list()})"

    def __eq__(self, other: object) -> bool:
        """Return True if the slice equals another slice, list, or tuple.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: True if ``other`` is a ``Slice``, ``list``, or ``tuple`` with
                the same elements; ``NotImplemented`` otherwise.

        Examples:
            >>> Slice([1, 2]) == [1, 2]
            True
        """
        if isinstance(other, Slice):
            return self.to_list() == other.to_list()
        if isinstance(other, (list, tuple)):
            return self.to_list() == list(other)
        return NotImplemented

    def __hash__(self) -> int:
        """Return a hash of the slice's contents.

        Returns:
            int: A hash based on the elements within the window.
        """
        return hash(tuple(self._data[self._start:self._end]))
