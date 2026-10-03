"""Iterator adapters: 18 chainable lazy transformer types.

Provides the adapter types Enumerate, Zip, Map, FilterIter, FilterMap, FlatMap,
Flatten, Peekable, Fuse, Chain, Cycle, Take, Skip, Rev, Inspect, Copied,
Cloned, and Partition. Each adapter wraps an iterable (and often a callable)
and produces a new iterator when iterated, leaving consumption lazy.
"""
from __future__ import annotations

from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Iterator,
    TypeVar,
)

T = TypeVar("T")
U = TypeVar("U")


class _EnumerateIterator(Generic[T]):
    """Internal iterator that yields (index, value) pairs from an iterable.

    Not part of the public API; obtain one via :class:`Enumerate`.
    """
    __slots__ = ("_iter", "_index")

    def __init__(self, iterable: Iterable[T], start: int = 0) -> None:
        """Initialize with an iterable and the starting index.

        Args:
            iterable: The values to pair with their indexes.
            start: The index assigned to the first element.
        """
        self._iter = iter(iterable)
        self._index = start

    def __iter__(self) -> _EnumerateIterator[T]:
        """Return self as its own iterator."""
        return self

    def __next__(self) -> tuple[int, T]:
        """Return the next ``(index, value)`` pair, incrementing the index."""
        idx = self._index
        val = next(self._iter)
        self._index += 1
        return (idx, val)


class Enumerate(Generic[T]):
    """Adapter that yields (index, value) pairs from an iterable.

    Examples:
        >>> list(Enumerate(["a", "b"], start=1))
        [(1, 'a'), (2, 'b')]
    """

    __slots__ = ("_iterable", "_start")

    def __init__(self, iterable: Iterable[T], start: int = 0) -> None:
        """Initialize with an iterable and an optional starting index.

        Args:
            iterable: The values to pair with their indexes.
            start: The index assigned to the first element. Defaults to 0.
        """
        self._iterable = iterable
        self._start = start

    def __iter__(self) -> _EnumerateIterator[T]:
        """Return an iterator over ``(index, value)`` pairs."""
        return _EnumerateIterator(self._iterable, self._start)

    def __repr__(self) -> str:
        """Return a concise representation of this adapter."""
        return "Enumerate(...)"


class _ZipIterator(Generic[T, U]):
    """Internal iterator that yields paired tuples from two iterators.

    Not part of the public API; obtain one via :class:`Zip`.
    """
    __slots__ = ("_iter_a", "_iter_b")

    def __init__(self, a: Iterator[T], b: Iterator[U]) -> None:
        """Initialize with the two iterators to pair.

        Args:
            a: The first iterator to pair from.
            b: The second iterator to pair from.
        """
        self._iter_a = a
        self._iter_b = b

    def __iter__(self) -> _ZipIterator[T, U]:
        """Return self as its own iterator."""
        return self

    def __next__(self) -> tuple[T, U]:
        """Return the next pair, stopping when either input is exhausted."""
        return (next(self._iter_a), next(self._iter_b))


class Zip(Generic[T, U]):
    """Adapter that pairs elements from two iterables into tuples.

    Iteration stops once the shorter iterable is exhausted.

    Examples:
        >>> list(Zip([1, 2], ["a", "b"]))
        [(1, 'a'), (2, 'b')]
    """

    __slots__ = ("_iter_a", "_iter_b")

    def __init__(self, a: Iterable[T], b: Iterable[U]) -> None:
        """Initialize with two iterables to pair together.

        Args:
            a: The first iterable to pair from.
            b: The second iterable to pair from.
        """
        self._iter_a = a
        self._iter_b = b

    def __iter__(self) -> _ZipIterator[T, U]:
        """Return an iterator over paired ``(a_item, b_item)`` tuples."""
        return _ZipIterator(iter(self._iter_a), iter(self._iter_b))

    def __repr__(self) -> str:
        """Return a concise representation of this adapter."""
        return "Zip(...)"


class _MapIterator(Generic[T, U]):
    """Internal iterator that applies a function to each element.

    Not part of the public API; obtain one via :class:`Map`.
    """
    __slots__ = ("_iter", "_fn")

    def __init__(self, iterable: Iterator[T], fn: Callable[[T], U]) -> None:
        """Initialize with an iterator and the mapping function.

        Args:
            iterable: The iterator to transform.
            fn: Function called once per element.
        """
        self._iter = iterable
        self._fn = fn

    def __iter__(self) -> _MapIterator[T, U]:
        """Return self as its own iterator."""
        return self

    def __next__(self) -> U:
        """Return the next mapped result."""
        return self._fn(next(self._iter))


class Map(Generic[T, U]):
    """Adapter that applies a function to each element of an iterable.

    Examples:
        >>> list(Map([1, 2, 3], lambda n: n * 2))
        [2, 4, 6]
    """

    __slots__ = ("_iterable", "_fn")

    def __init__(self, iterable: Iterable[T], fn: Callable[[T], U]) -> None:
        """Initialize with an iterable and a transformation function.

        Args:
            iterable: The values to transform.
            fn: Function called once per element.
        """
        self._iterable = iterable
        self._fn = fn

    def __iter__(self) -> _MapIterator[T, U]:
        """Return an iterator applying fn to each element."""
        return _MapIterator(iter(self._iterable), self._fn)

    def __repr__(self) -> str:
        """Return a concise representation of this adapter."""
        return "Map(...)"


class _FilterIterator(Generic[T]):
    """Internal iterator that yields only elements satisfying a predicate.

    Not part of the public API; obtain one via :class:`FilterIter`.
    """
    __slots__ = ("_iter", "_pred")

    def __init__(self, iterable: Iterator[T], pred: Callable[[T], bool]) -> None:
        """Initialize with an iterator and the filter predicate.

        Args:
            iterable: The iterator to filter.
            pred: Function returning True for elements to keep.
        """
        self._iter = iterable
        self._pred = pred

    def __iter__(self) -> _FilterIterator[T]:
        """Return self as its own iterator."""
        return self

    def __next__(self) -> T:
        """Return the next element that satisfies the predicate."""
        while True:
            val = next(self._iter)
            if self._pred(val):
                return val


class FilterIter(Generic[T]):
    """Adapter that yields only elements satisfying a predicate.

    Named ``FilterIter`` rather than ``Filter`` so the top-level ``Filter``
    name stays free for the PHP-style validation filters in
    :mod:`oxide.filter`.

    Examples:
        >>> list(FilterIter(range(6), lambda n: n % 2 == 0))
        [0, 2, 4]
    """

    __slots__ = ("_iterable", "_pred")

    def __init__(self, iterable: Iterable[T], pred: Callable[[T], bool]) -> None:
        """Initialize with an iterable and a filter predicate.

        Args:
            iterable: The values to filter.
            pred: Function returning True for elements to keep.
        """
        self._iterable = iterable
        self._pred = pred

    def __iter__(self) -> _FilterIterator[T]:
        """Return an iterator yielding only matching elements."""
        return _FilterIterator(iter(self._iterable), self._pred)

    def __repr__(self) -> str:
        """Return a concise representation of this adapter."""
        return "FilterIter(...)"


class _FilterMapIterator(Generic[T, U]):
    """Internal iterator that maps elements and yields only non-None results.

    Not part of the public API; obtain one via :class:`FilterMap`.
    """
    __slots__ = ("_iter", "_fn")

    def __init__(self, iterable: Iterator[T], fn: Callable[[T], U | None]) -> None:
        """Initialize with an iterator and a mapping function.

        Args:
            iterable: The iterator to map.
            fn: Function returning a value to keep or None to drop.
        """
        self._iter = iterable
        self._fn = fn

    def __iter__(self) -> _FilterMapIterator[T, U]:
        """Return self as its own iterator."""
        return self

    def __next__(self) -> U:
        """Return the next non-None mapped result."""
        while True:
            val = self._fn(next(self._iter))
            if val is not None:
                return val


class FilterMap(Generic[T, U]):
    """Adapter that maps elements and yields only non-None results.

    Examples:
        >>> list(FilterMap(["1", "x", "3"], lambda s: int(s) if s.isdigit() else None))
        [1, 3]
    """

    __slots__ = ("_iterable", "_fn")

    def __init__(self, iterable: Iterable[T], fn: Callable[[T], U | None]) -> None:
        """Initialize with an iterable and a mapping function that may return None.

        Args:
            iterable: The values to map.
            fn: Function returning a value to keep or None to drop.
        """
        self._iterable = iterable
        self._fn = fn

    def __iter__(self) -> _FilterMapIterator[T, U]:
        """Return an iterator yielding only non-None mapped results."""
        return _FilterMapIterator(iter(self._iterable), self._fn)

    def __repr__(self) -> str:
        """Return a concise representation of this adapter."""
        return "FilterMap(...)"


class _FlatMapIterator(Generic[T, U]):
    """Internal iterator that maps elements to iterables and flattens the results.

    Not part of the public API; obtain one via :class:`FlatMap`.
    """
    __slots__ = ("_iter", "_fn", "_current")

    def __init__(self, iterable: Iterator[T], fn: Callable[[T], Iterable[U]]) -> None:
        """Initialize with an iterator and an expanding function.

        Args:
            iterable: The iterator to expand.
            fn: Function returning an iterable for each element.
        """
        self._iter = iterable
        self._fn = fn
        self._current: Iterator[U] | None = None

    def __iter__(self) -> _FlatMapIterator[T, U]:
        """Return self as its own iterator."""
        return self

    def __next__(self) -> U:
        """Return the next flattened element from the current inner iterable."""
        while True:
            if self._current is not None:
                try:
                    return next(self._current)
                except StopIteration:
                    self._current = None
            val = next(self._iter)
            self._current = iter(self._fn(val))


class FlatMap(Generic[T, U]):
    """Adapter that maps each element to an iterable and flattens the results.

    Examples:
        >>> list(FlatMap([[1, 2], [3]], lambda lst: [x * 10 for x in lst]))
        [10, 20, 30]
    """

    __slots__ = ("_iterable", "_fn")

    def __init__(self, iterable: Iterable[T], fn: Callable[[T], Iterable[U]]) -> None:
        """Initialize with an iterable and a function returning an iterable.

        Args:
            iterable: The values to expand.
            fn: Function returning an iterable for each element.
        """
        self._iterable = iterable
        self._fn = fn

    def __iter__(self) -> _FlatMapIterator[T, U]:
        """Return an iterator over the flattened results."""
        return _FlatMapIterator(iter(self._iterable), self._fn)

    def __repr__(self) -> str:
        """Return a concise representation of this adapter."""
        return "FlatMap(...)"


class _FlattenIterator(Generic[T]):
    """Internal iterator that flattens one level of nesting from an iterable.

    Not part of the public API; obtain one via :class:`Flatten`.
    """
    __slots__ = ("_iter", "_current")

    def __init__(self, iterable: Iterable[Iterable[T]]) -> None:
        """Initialize with the nested iterable to flatten.

        Args:
            iterable: An iterable whose elements are themselves iterables.
        """
        self._iter = iter(iterable)
        self._current: Iterator[T] | None = None

    def __iter__(self) -> _FlattenIterator[T]:
        """Return self as its own iterator."""
        return self

    def __next__(self) -> T:
        """Return the next element from the current inner iterable."""
        while True:
            if self._current is not None:
                try:
                    return next(self._current)
                except StopIteration:
                    self._current = None
            inner = next(self._iter)
            self._current = iter(inner)


class Flatten(Generic[T]):
    """Adapter that flattens one level of nesting from an iterable of iterables.

    Examples:
        >>> list(Flatten([[1, 2], [3, 4]]))
        [1, 2, 3, 4]
    """

    __slots__ = ("_iterable",)

    def __init__(self, iterable: Iterable[Iterable[T]]) -> None:
        """Initialize with a nested iterable to flatten.

        Args:
            iterable: An iterable whose elements are themselves iterables.
        """
        self._iterable = iterable

    def __iter__(self) -> _FlattenIterator[T]:
        """Return an iterator over the flattened elements."""
        return _FlattenIterator(self._iterable)

    def __repr__(self) -> str:
        """Return a concise representation of this adapter."""
        return "Flatten(...)"


class _PeekableIterator(Generic[T]):
    """Internal iterator that supports peeking at the next element.

    Not part of the public API; obtain one via :class:`Peekable`.
    """
    __slots__ = ("_iter", "_peeked", "_has_peeked")

    def __init__(self, iterable: Iterator[T]) -> None:
        """Initialize with the iterator to make peekable.

        Args:
            iterable: The iterator to wrap for lookahead access.
        """
        self._iter = iterable
        self._peeked: T | None = None
        self._has_peeked = False

    def __iter__(self) -> _PeekableIterator[T]:
        """Return self as its own iterator."""
        return self

    def __next__(self) -> T:
        """Return the next element, consuming a peeked value if present."""
        if self._has_peeked:
            self._has_peeked = False
            return self._peeked  # type: ignore
        return next(self._iter)

    def peek(self) -> T | None:  # type: ignore
        """Return the next element without advancing the iterator, or None.

        Returns:
            The next element, or None if the iterator is empty.
        """
        if not self._has_peeked:
            try:
                self._peeked = next(self._iter)
                self._has_peeked = True
            except StopIteration:
                return None
        return self._peeked

    def peek_mut(self) -> PeekMut[T]:  # type: ignore
        """Return a PeekMut guard for mutable access to the peeked value.

        Returns:
            A PeekMut guard that is truthy when a value is available.
        """
        if not self._has_peeked:
            try:
                self._peeked = next(self._iter)
                self._has_peeked = True
            except StopIteration:
                return PeekMut(None, False)
        return PeekMut(self._peeked, True)


class PeekMut(Generic[T]):
    """A mutable peek guard that holds a value and validity flag for peek operations.

    Acts like an ``Option``: it is truthy when the underlying iterator had a
    value to peek, and its repr is ``Some(value)`` or ``None`` accordingly.

    Examples:
        >>> it = Peekable([1, 2])
        >>> p = iter(it)
        >>> pm = p.peek_mut()
        >>> bool(pm)
        True
    """

    __slots__ = ("_value", "_valid")

    def __init__(self, value: T | None, valid: bool) -> None:
        """Initialize with an optional value and a validity flag.

        Args:
            value: The peeked value, or None when nothing was available.
            valid: True when a value is available to inspect.
        """
        self._value = value
        self._valid = valid

    def __bool__(self) -> bool:
        """Return True when a value is available to inspect."""
        return self._valid

    def __enter__(self) -> PeekMut:
        """Enter the guard's context manager, returning self."""
        return self

    def __exit__(self, *_: Any) -> None:
        """Exit the context manager without side effects."""
        pass

    def __repr__(self) -> str:
        """Return ``Some(value)`` when valid and ``None`` otherwise."""
        if self._valid:
            return f"Some({self._value!r})"
        return "None"


class Peekable(Generic[T]):
    """Adapter that allows peeking at the next element without consuming it.

    Examples:
        >>> it = Peekable([1, 2])
        >>> p = iter(it)
        >>> p.peek()
        1
        >>> p.peek()
        1
        >>> next(p)
        1
    """

    __slots__ = ("_iterable",)

    def __init__(self, iterable: Iterable[T]) -> None:
        """Initialize with an iterable to make peekable.

        Args:
            iterable: The values to iterate over with lookahead support.
        """
        self._iterable = iterable

    def __iter__(self) -> _PeekableIterator[T]:
        """Return a peekable iterator over the wrapped iterable."""
        return _PeekableIterator(iter(self._iterable))

    def __repr__(self) -> str:
        """Return a concise representation of this adapter."""
        return "Peekable(...)"


class _FuseIterator(Generic[T]):
    """Internal iterator that stops permanently after first exhaustion.

    Not part of the public API; obtain one via :class:`Fuse`.
    """
    __slots__ = ("_iter", "_exhausted")

    def __init__(self, iterable: Iterator[T]) -> None:
        """Initialize with the iterator to fuse.

        Args:
            iterable: The iterator to make permanently empty once exhausted.
        """
        self._iter = iterable
        self._exhausted = False

    def __iter__(self) -> _FuseIterator[T]:
        """Return self as its own iterator."""
        return self

    def __next__(self) -> T:
        """Return the next element, or StopIteration once permanently done."""
        if self._exhausted:
            raise StopIteration
        try:
            return next(self._iter)
        except StopIteration:
            self._exhausted = True
            raise

    def is_exhausted(self) -> bool:  # type: ignore
        """Return True if the iterator has been exhausted.

        Returns:
            True once the underlying iterator has been fully consumed.
        """
        return self._exhausted


class Fuse(Generic[T]):
    """Adapter that fuses an iterator so it yields nothing after first exhaustion.

    Examples:
        >>> it = iter(Fuse([1, 2]))
        >>> list(it)
        [1, 2]
        >>> list(it)
        []
    """

    __slots__ = ("_iterable",)

    def __init__(self, iterable: Iterable[T]) -> None:
        """Initialize with an iterable to fuse.

        Args:
            iterable: The values to iterate over.
        """
        self._iterable = iterable

    def __iter__(self) -> _FuseIterator[T]:
        """Return a fused iterator over the wrapped iterable."""
        return _FuseIterator(iter(self._iterable))

    def __repr__(self) -> str:
        """Return a concise representation of this adapter."""
        return "Fuse(...)"


class _ChainIterator(Generic[T]):
    """Internal iterator that chains two iterators sequentially.

    Not part of the public API; obtain one via :class:`Chain`.
    """
    __slots__ = ("_iter_a", "_iter_b", "_first_done")

    def __init__(self, a: Iterator[T], b: Iterator[T]) -> None:
        """Initialize with the two iterators to chain.

        Args:
            a: The first iterator to yield from.
            b: The second iterator to yield from after a is exhausted.
        """
        self._iter_a = a
        self._iter_b = b
        self._first_done = False

    def __iter__(self) -> _ChainIterator[T]:
        """Return self as its own iterator."""
        return self

    def __next__(self) -> T:
        """Return the next element from a, then from b once a is done."""
        if not self._first_done:
            try:
                return next(self._iter_a)
            except StopIteration:
                self._first_done = True
        return next(self._iter_b)


class Chain(Generic[T]):
    """Adapter that chains two iterables into a single sequential iterator.

    Examples:
        >>> list(Chain([1, 2], [3, 4]))
        [1, 2, 3, 4]
    """

    __slots__ = ("_iter_a", "_iter_b")

    def __init__(self, a: Iterable[T], b: Iterable[T]) -> None:
        """Initialize with two iterables to chain together.

        Args:
            a: The first iterable to yield from.
            b: The second iterable to yield from after a is exhausted.
        """
        self._iter_a = a
        self._iter_b = b

    def __iter__(self) -> _ChainIterator[T]:
        """Return an iterator yielding a's elements then b's."""
        return _ChainIterator(iter(self._iter_a), iter(self._iter_b))

    def __repr__(self) -> str:
        """Return a concise representation of this adapter."""
        return "Chain(...)"


class _CycleIterator(Generic[T]):
    """Internal iterator that infinitely cycles through an iterable.

    Not part of the public API; obtain one via :class:`Cycle`.
    """
    __slots__ = ("_original", "_iter", "_exhausted")

    def __init__(self, iterable: Iterable[T]) -> None:
        """Initialize with the iterable to cycle through.

        Args:
            iterable: The values to repeat forever (buffered eagerly).
        """
        self._original = list(iterable)
        self._iter = iter(self._original)
        self._exhausted = False

    def __iter__(self) -> _CycleIterator[T]:
        """Return self as its own iterator."""
        return self

    def __next__(self) -> T:
        """Return the next element, restarting from the beginning when done."""
        if self._exhausted:
            self._iter = iter(self._original)
            self._exhausted = False
        try:
            return next(self._iter)
        except StopIteration:
            self._exhausted = True
            self._iter = iter(self._original)
            return next(self._iter)


class Cycle(Generic[T]):
    """Adapter that infinitely cycles through an iterable.

    The wrapped iterable is buffered so the cycle can repeat even if the
    source is a non-reiterable iterator.

    Examples:
        >>> c = Cycle([1, 2])
        >>> it = iter(c)
        >>> [next(it) for _ in range(6)]
        [1, 2, 1, 1, 2, 1]
    """

    __slots__ = ("_iterable",)

    def __init__(self, iterable: Iterable[T]) -> None:
        """Initialize with an iterable to cycle through.

        Args:
            iterable: The values to repeat forever.
        """
        self._iterable = iterable

    def __iter__(self) -> _CycleIterator[T]:
        """Return an iterator that repeats the wrapped elements forever."""
        return _CycleIterator(self._iterable)

    def __repr__(self) -> str:
        """Return a concise representation of this adapter."""
        return "Cycle(...)"


class _TakeIterator(Generic[T]):
    """Internal iterator that yields at most n elements.

    Not part of the public API; obtain one via :class:`Take`.
    """
    __slots__ = ("_iter", "_remaining")

    def __init__(self, iterable: Iterator[T], n: int) -> None:
        """Initialize with an iterator and the maximum element count.

        Args:
            iterable: The iterator to draw from.
            n: The maximum number of elements to yield.
        """
        self._iter = iterable
        self._remaining = n

    def __iter__(self) -> _TakeIterator[T]:
        """Return self as its own iterator."""
        return self

    def __next__(self) -> T:
        """Return the next element, or StopIteration once n elements are done."""
        if self._remaining <= 0:
            raise StopIteration
        self._remaining -= 1
        return next(self._iter)


class Take(Generic[T]):
    """Adapter that yields at most n elements from an iterable.

    Examples:
        >>> list(Take(range(10), 3))
        [0, 1, 2]
    """

    __slots__ = ("_iterable", "_n")

    def __init__(self, iterable: Iterable[T], n: int) -> None:
        """Initialize with an iterable and the maximum number of elements.

        Args:
            iterable: The values to draw from.
            n: The maximum number of elements to yield.
        """
        self._iterable = iterable
        self._n = n

    def __iter__(self) -> _TakeIterator[T]:
        """Return an iterator yielding at most n elements."""
        return _TakeIterator(iter(self._iterable), self._n)

    def __repr__(self) -> str:
        """Return a concise representation of this adapter."""
        return "Take(...)"


class _SkipIterator(Generic[T]):
    """Internal iterator that skips the first n elements.

    Not part of the public API; obtain one via :class:`Skip`.
    """
    __slots__ = ("_iter", "_remaining")

    def __init__(self, iterable: Iterable[T], n: int) -> None:
        """Initialize with an iterable and the number of elements to skip.

        Args:
            iterable: The values to draw from.
            n: The number of leading elements to drop.
        """
        self._iter = iter(iterable)
        self._remaining = n

    def __iter__(self) -> _SkipIterator[T]:
        """Return self as its own iterator."""
        return self

    def __next__(self) -> T:
        """Return the next element after dropping the first n."""
        while self._remaining > 0:
            next(self._iter)
            self._remaining -= 1
        return next(self._iter)


class Skip(Generic[T]):
    """Adapter that skips the first n elements and yields the rest.

    Examples:
        >>> list(Skip(range(5), 2))
        [2, 3, 4]
    """

    __slots__ = ("_iterable", "_n")

    def __init__(self, iterable: Iterable[T], n: int) -> None:
        """Initialize with an iterable and the number of elements to skip.

        Args:
            iterable: The values to draw from.
            n: The number of leading elements to drop.
        """
        self._iterable = iterable
        self._n = n

    def __iter__(self) -> _SkipIterator[T]:
        """Return an iterator yielding the elements after the first n."""
        return _SkipIterator(self._iterable, self._n)

    def __repr__(self) -> str:
        """Return a concise representation of this adapter."""
        return "Skip(...)"


class _RevIterator(Generic[T]):
    """Internal iterator that yields elements in reverse order.

    Not part of the public API; obtain one via :class:`Rev`.
    """
    __slots__ = ("_buffer", "_index")

    def __init__(self, iterable: Iterable[T]) -> None:
        """Initialize with the iterable to reverse.

        Args:
            iterable: The values to yield in reverse order.
        """
        self._buffer = list(iterable)
        self._index = len(self._buffer) - 1

    def __iter__(self) -> _RevIterator[T]:
        """Return self as its own iterator."""
        return self

    def __next__(self) -> T:
        """Return the next element from the end towards the start."""
        if self._index < 0:
            raise StopIteration
        val = self._buffer[self._index]
        self._index -= 1
        return val


class Rev(Generic[T]):
    """Adapter that reverses the order of elements from an iterable.

    Buffers the entire input eagerly so the reversal can be produced lazily.

    Examples:
        >>> list(Rev([1, 2, 3]))
        [3, 2, 1]
    """

    __slots__ = ("_iterable",)

    def __init__(self, iterable: Iterable[T]) -> None:
        """Initialize with an iterable to reverse.

        Args:
            iterable: The values to yield in reverse order.
        """
        self._iterable = iterable

    def __iter__(self) -> _RevIterator[T]:
        """Return an iterator yielding the elements in reverse order."""
        return _RevIterator(self._iterable)

    def __repr__(self) -> str:
        """Return a concise representation of this adapter."""
        return "Rev(...)"


class _InspectIterator(Generic[T]):
    """Internal iterator that calls a side-effect function on each element.

    Not part of the public API; obtain one via :class:`Inspect`.
    """
    __slots__ = ("_iter", "_fn")

    def __init__(self, iterable: Iterator[T], fn: Callable[[T], Any]) -> None:
        """Initialize with an iterator and a side-effect function.

        Args:
            iterable: The iterator to pass through.
            fn: Function called with each element for its side effects.
        """
        self._iter = iterable
        self._fn = fn

    def __iter__(self) -> _InspectIterator[T]:
        """Return self as its own iterator."""
        return self

    def __next__(self) -> T:
        """Return the next element after invoking fn on it."""
        val = next(self._iter)
        self._fn(val)
        return val


class Inspect(Generic[T]):
    """Adapter that calls a side-effect function on each element without altering the stream.

    Ideal for logging or debugging a pipeline without changing its output.

    Examples:
        >>> seen = []
        >>> list(Inspect([1, 2], seen.append))
        [1, 2]
        >>> seen
        [1, 2]
    """

    __slots__ = ("_iterable", "_fn")

    def __init__(self, iterable: Iterable[T], fn: Callable[[T], Any]) -> None:
        """Initialize with an iterable and a side-effect function.

        Args:
            iterable: The values to pass through.
            fn: Function called with each element for its side effects.
        """
        self._iterable = iterable
        self._fn = fn

    def __iter__(self) -> _InspectIterator[T]:
        """Return an iterator that passes elements through while calling fn."""
        return _InspectIterator(iter(self._iterable), self._fn)

    def __repr__(self) -> str:
        """Return a concise representation of this adapter."""
        return "Inspect(...)"


class _CopiedIterator(Generic[T]):
    """Internal iterator that yields elements from the source.

    Acts as the backing iterator for both :class:`Copied` and :class:`Cloned`.
    """
    __slots__ = ("_iter",)

    def __init__(self, iterable: Iterator[T]) -> None:
        """Initialize with the source iterator.

        Args:
            iterable: The iterator whose elements are yielded.
        """
        self._iter = iterable

    def __iter__(self) -> _CopiedIterator[T]:
        """Return self as its own iterator."""
        return self

    def __next__(self) -> T:
        """Return the next element from the source."""
        return next(self._iter)


class Copied(Generic[T]):
    """Adapter that yields copies of elements from the source iterable.

    In this implementation the elements are passed through as-is from the
    source; it mirrors the Rust ``copied`` adapter naming.

    Examples:
        >>> list(Copied([1, 2, 3]))
        [1, 2, 3]
    """

    __slots__ = ("_iterable",)

    def __init__(self, iterable: Iterable[T]) -> None:
        """Initialize with an iterable to copy elements from.

        Args:
            iterable: The values to iterate over.
        """
        self._iterable = iterable

    def __iter__(self) -> _CopiedIterator[T]:
        """Return an iterator yielding the elements of the wrapped iterable."""
        return _CopiedIterator(iter(self._iterable))

    def __repr__(self) -> str:
        """Return a concise representation of this adapter."""
        return "Copied(...)"


class Cloned(Generic[T]):
    """Adapter that clones each element by copying from the source iterable.

    In this implementation the elements are passed through as-is from the
    source; it mirrors the Rust ``cloned`` adapter naming.

    Examples:
        >>> list(Cloned([1, 2, 3]))
        [1, 2, 3]
    """

    __slots__ = ("_iterable",)

    def __init__(self, iterable: Iterable[T]) -> None:
        """Initialize with an iterable to clone elements from.

        Args:
            iterable: The values to iterate over.
        """
        self._iterable = iterable

    def __iter__(self) -> _CopiedIterator[T]:
        """Return an iterator yielding the elements of the wrapped iterable."""
        return _CopiedIterator(iter(self._iterable))

    def __repr__(self) -> str:
        """Return a concise representation of this adapter."""
        return "Cloned(...)"


class _PartitionIterator(Generic[T]):
    """Internal iterator that yields the partitioned (matching, non-matching) lists.

    Not part of the public API; prefer :meth:`Partition.collect`.
    """
    __slots__ = ("_iter", "_pred", "_true_buf", "_false_buf", "_true_idx", "_false_idx")

    def __init__(self, iterable: Iterator[T], pred: Callable[[T], bool]) -> None:
        """Initialize by partitioning the source into matching and non-matching lists.

        Args:
            iterable: The iterator to partition.
            pred: Function deciding which list each element joins.
        """
        items = list(iterable)
        self._true_buf = [item for item in items if pred(item)]
        self._false_buf = [item for item in items if not pred(item)]
        self._true_idx = 0
        self._false_idx = 0

    def __iter__(self) -> _PartitionIterator[T]:
        """Return self as its own iterator."""
        return self

    def __next__(self) -> tuple[list[T], list[T]]:
        """Return the partition once, then signal exhaustion."""
        if self._true_idx == 0 and self._false_idx == 0:
            self._true_idx = 1
            return (self._true_buf, self._false_buf)
        raise StopIteration


class Partition(Generic[T]):
    """Adapter that splits elements into two lists based on a predicate.

    Unlike the other adapters, use :meth:`collect` directly to obtain the
    partitioned result.

    Examples:
        >>> Partition(range(5), lambda n: n % 2 == 0).collect()
        ([0, 2, 4], [1, 3])
    """

    __slots__ = ("_iterable", "_pred")

    def __init__(self, iterable: Iterable[T], pred: Callable[[T], bool]) -> None:
        """Initialize with an iterable and a predicate for partitioning.

        Args:
            iterable: The values to partition.
            pred: Function deciding which list each element joins.
        """
        self._iterable = iterable
        self._pred = pred

    def collect(self) -> tuple[list[T], list[T]]:  # type: ignore
        """Partition elements into (matching, non-matching) lists and return both.

        Returns:
            A ``(matching, non_matching)`` tuple of lists.

        Examples:
            >>> Partition([1, 2, 3, 4], lambda n: n > 2).collect()
            ([3, 4], [1, 2])
        """
        true_list = []
        false_list = []
        for item in self._iterable:
            if self._pred(item):
                true_list.append(item)
            else:
                false_list.append(item)
        return (true_list, false_list)

    def __repr__(self) -> str:
        """Return a concise representation of this adapter."""
        return "Partition(...)"
