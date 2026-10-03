"""Core iterator types: ``Iter`` and ``PeekableIter``.

This module provides the Rust-style chainable ``Iter`` wrapper for lazy
iteration and ``PeekableIter`` for single-element lookahead. Use these types
together to transform and consume iterables fluently.

The ``Range`` family is *not* defined here. It lives in
:mod:`oxide.core.convert` and is re-exported from :mod:`oxide.iter` for
convenience, so ``oxide.iter.Range is oxide.Range``.
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
V = TypeVar("V")


class Iter(Generic[T]):
    """A fluent, Rust-style iterator wrapper providing chainable operations.

    Wrap any iterable or iterator, chain lazy adapters such as ``map`` and
    ``filter``, then finish with a consuming terminator such as ``collect``,
    ``fold``, ``sum``, or ``any``. Adapters are lazy: nothing is computed
    until the iterator is consumed.

    Examples:
        >>> out = Iter([1, 2, 3, 4, 5]).filter(lambda n: n % 2 == 0).map(lambda n: n * 10).collect()
        >>> out
        [20, 40]
    """

    __slots__ = ("_iter",)

    def __init__(self, source: Iterable[T] | Iterator[T]) -> None:
        """Wrap an iterable or existing iterator for chainable processing.

        Args:
            source: Any iterable or iterator whose elements will be processed.

        Examples:
            >>> Iter([1, 2, 3]).collect()
            [1, 2, 3]
        """
        if isinstance(source, Iterator):
            self._iter = source
        else:
            self._iter = iter(source)

    @classmethod
    def from_fn(cls, fn: Callable[[int], T], start: int = 0) -> Iter[T]:
        """Create an infinite iterator by applying fn to successive indices.

        Args:
            fn: Callable taking an index and returning an element.
            start: The first index passed to fn. Defaults to 0.

        Returns:
            An Iter producing ``fn(start), fn(start + 1), ...`` indefinitely.

        Examples:
            >>> Iter.from_fn(lambda i: i * i).take(4).collect()
            [0, 1, 4, 9]
        """
        def gen():
            i = start
            while True:
                yield fn(i)
                i += 1
        return cls(gen())

    @classmethod
    def repeat(cls, value: T) -> Iter[T]:
        """Create an infinite iterator that yields the same value repeatedly.

        Args:
            value: The value to yield forever.

        Returns:
            An infinite Iter of identical values.

        Examples:
            >>> Iter.repeat(7).take(3).collect()
            [7, 7, 7]
        """
        def gen():
            while True:
                yield value
        return cls(gen())

    @classmethod
    def count(cls, start: int = 0, step: int = 1) -> Iter[int]:
        """Create an infinite counting iterator from start with given step.

        Args:
            start: The first value to yield. Defaults to 0.
            step: The increment between successive values. Defaults to 1.

        Returns:
            An infinite Iter of ``start, start + step, start + 2 * step, ...``.

        Examples:
            >>> Iter.count(5, 5).take(4).collect()
            [5, 10, 15, 20]
        """
        def gen():
            i = start
            while True:
                yield i
                i += step
        return cls(gen())

    @classmethod
    def zip(cls, a: Iterable[T], b: Iterable[U]) -> Iter[tuple[T, U]]:
        """Create an iterator yielding paired tuples from two iterables.

        Iteration stops once the shorter iterable is exhausted.

        Args:
            a: The first iterable to pair from.
            b: The second iterable to pair from.

        Returns:
            An Iter of ``(x, y)`` tuples pairing elements of a and b.

        Examples:
            >>> Iter.zip([1, 2], ["a", "b"]).collect()
            [(1, 'a'), (2, 'b')]
        """
        return cls(zip(a, b))

    @classmethod
    def chain(cls, *iters: Iterable[T]) -> Iter[T]:
        """Chain multiple iterables into a single sequential iterator.

        Args:
            iters: One or more iterables to concatenate in order.

        Returns:
            An Iter yielding every element of each iterable in sequence.

        Examples:
            >>> Iter.chain([1, 2], [3], [4, 5]).collect()
            [1, 2, 3, 4, 5]
        """
        def gen():
            for it in iters:
                yield from it
        return cls(gen())

    def map(self, fn: Callable[[T], U]) -> Iter[U]:
        """Apply a function to each element and return a new iterator of results.

        Args:
            fn: Function called once per element.

        Returns:
            A new lazy Iter of ``fn(v)`` for every element v.

        Examples:
            >>> Iter([1, 2, 3]).map(lambda n: n * 2).collect()
            [2, 4, 6]
        """
        def gen():
            for v in self._iter:
                yield fn(v)
        return Iter(gen())

    def map_enumerate(self, fn: Callable[[int, T], U]) -> Iter[U]:
        """Apply a function receiving (index, value) pairs to each element.

        Args:
            fn: Function called with ``(index, value)`` for each element.

        Returns:
            A new lazy Iter of ``fn(i, v)`` for each element and its index.

        Examples:
            >>> Iter(["a", "b"]).map_enumerate(lambda i, v: f"{i}:{v}").collect()
            ['0:a', '1:b']
        """
        def gen():
            for i, v in enumerate(self._iter):
                yield fn(i, v)
        return Iter(gen())

    def filter(self, predicate: Callable[[T], bool]) -> Iter[T]:
        """Return only elements that satisfy the predicate.

        Args:
            predicate: Function returning True for elements to keep.

        Returns:
            A new lazy Iter containing only matching elements.

        Examples:
            >>> Iter(range(6)).filter(lambda n: n % 2 == 0).collect()
            [0, 2, 4]
        """
        def gen():
            for v in self._iter:
                if predicate(v):
                    yield v
        return Iter(gen())

    def filter_map(self, fn: Callable[[T], U | None]) -> Iter[U]:
        """Apply a function and yield only non-None results.

        Args:
            fn: Function returning a value to keep or None to drop.

        Returns:
            A new lazy Iter of the non-None results.

        Examples:
            >>> Iter(["1", "x", "3"]).filter_map(lambda s: int(s) if s.isdigit() else None).collect()
            [1, 3]
        """
        def gen():
            for v in self._iter:
                result = fn(v)
                if result is not None:
                    yield result
        return Iter(gen())

    def enumerate(self, start: int = 0) -> Iter[tuple[int, T]]:
        """Yield (index, value) pairs starting from the given index.

        Args:
            start: The index assigned to the first element. Defaults to 0.

        Returns:
            A new lazy Iter of ``(index, value)`` tuples.

        Examples:
            >>> Iter(["a", "b"]).enumerate(1).collect()
            [(1, 'a'), (2, 'b')]
        """
        def gen():
            for i, v in enumerate(self._iter, start):
                yield (i, v)
        return Iter(gen())

    def peekable(self) -> PeekableIter[T]:
        """Convert this iterator into a PeekableIter for lookahead.

        Returns:
            A PeekableIter wrapping the same underlying iterator.

        Examples:
            >>> p = Iter([1, 2, 3]).peekable()
            >>> p.peek()
            1
            >>> p.next()
            1
        """
        return PeekableIter(self._iter)

    def take(self, n: int) -> Iter[T]:
        """Take at most n elements from the iterator.

        Args:
            n: The maximum number of elements to yield.

        Returns:
            A new lazy Iter of at most n elements.

        Examples:
            >>> Iter(range(10)).take(3).collect()
            [0, 1, 2]
        """
        def gen():
            for i, v in enumerate(self._iter):
                if i >= n:
                    break
                yield v
        return Iter(gen())

    def take_while(self, predicate: Callable[[T], bool]) -> Iter[T]:
        """Take elements while the predicate holds, then stop.

        Args:
            predicate: Function deciding whether to keep taking.

        Returns:
            A new lazy Iter that stops at the first failing element.

        Examples:
            >>> Iter([1, 2, 3, 1]).take_while(lambda n: n < 3).collect()
            [1, 2]
        """
        def gen():
            for v in self._iter:
                if not predicate(v):
                    break
                yield v
        return Iter(gen())

    def skip(self, n: int) -> Iter[T]:
        """Skip the first n elements and yield the rest.

        Args:
            n: The number of leading elements to drop.

        Returns:
            A new lazy Iter of the remaining elements.

        Examples:
            >>> Iter(range(5)).skip(2).collect()
            [2, 3, 4]
        """
        def gen():
            for i, v in enumerate(self._iter):
                if i >= n:
                    yield v
        return Iter(gen())

    def skip_while(self, predicate: Callable[[T], bool]) -> Iter[T]:
        """Skip elements while the predicate holds, then yield the rest.

        Args:
            predicate: Function tested against leading elements.

        Returns:
            A new lazy Iter that begins after the first failing element.

        Examples:
            >>> Iter([1, 2, 3, 1]).skip_while(lambda n: n < 3).collect()
            [3, 1]
        """
        def gen():
            skipping = True
            for v in self._iter:
                if skipping and predicate(v):
                    continue
                skipping = False
                yield v
        return Iter(gen())

    def flat_map(self, fn: Callable[[T], Iterable[U]]) -> Iter[U]:
        """Map each element to an iterable and flatten the results.

        Args:
            fn: Function returning an iterable for each element.

        Returns:
            A new lazy Iter yielding the concatenation of all inner iterables.

        Examples:
            >>> Iter([[1, 2], [3]]).flat_map(lambda lst: [x * 10 for x in lst]).collect()
            [10, 20, 30]
        """
        def gen():
            for v in self._iter:
                yield from fn(v)
        return Iter(gen())

    def flatten(self) -> Iter[Any]:
        """Flatten one level of nesting from iterable elements.

        Elements that are not themselves iterable are yielded unchanged.

        Returns:
            A new lazy Iter of the flattened elements.

        Examples:
            >>> Iter([[1, 2], [3, 4]]).flatten().collect()
            [1, 2, 3, 4]
        """
        def gen():
            for v in self._iter:
                if hasattr(v, '__iter__'):
                    yield from v
                else:
                    yield v
        return Iter(gen())

    def inspect(self, fn: Callable[[T], Any]) -> Iter[T]:
        """Call a side-effect function on each element without modifying the stream.

        Args:
            fn: Function called with each element for its side effects.

        Returns:
            A new lazy Iter of the same elements, with fn applied along the way.

        Examples:
            >>> seen = []
            >>> Iter([1, 2]).inspect(seen.append).collect()
            [1, 2]
            >>> seen
            [1, 2]
        """
        def gen():
            for v in self._iter:
                fn(v)
                yield v
        return Iter(gen())

    def step_by(self, step: int) -> Iter[T]:
        """Yield every step-th element, starting with the first.

        Args:
            step: The stride between yielded elements; must be a positive integer.

        Returns:
            A new lazy Iter of elements at indexes 0, step, 2 * step, ...

        Examples:
            >>> Iter(range(8)).step_by(3).collect()
            [0, 3, 6]
        """
        def gen():
            for i, v in enumerate(self._iter):
                if i % step == 0:
                    yield v
        return Iter(gen())

    def zip_with(self, other: Iterable[U], fn: Callable[[T, U], V]) -> Iter[V]:
        """Zip with another iterable, combining pairs using the given function.

        Iteration stops once either input is exhausted.

        Args:
            other: The second iterable to pair with.
            fn: Function called with each ``(a, b)`` pair.

        Returns:
            A new lazy Iter of ``fn(a, b)`` results.

        Examples:
            >>> Iter([1, 2]).zip_with([10, 20], lambda a, b: a + b).collect()
            [11, 22]
        """
        def gen():
            for a, b in zip(self._iter, other):
                yield fn(a, b)
        return Iter(gen())

    def fuse(self) -> Iter[T]:
        """Fuse the iterator so it yields nothing after first exhaustion.

        The returned iterator becomes permanently empty once its source is
        exhausted, so further consumption never raises StopIteration.

        Returns:
            A new lazy Iter that stays exhausted once finished.

        Examples:
            >>> it = Iter([1, 2]).fuse()
            >>> it.collect()
            [1, 2]
            >>> it.collect()
            []
        """
        def gen():
            exhausted = False
            for v in self._iter:
                if exhausted:
                    break
                yield v
        return Iter(gen())

    def fold(self, init: U, fn: Callable[[U, T], U]) -> U:
        """Fold all elements into a single accumulator using the given function.

        Consumes the iterator, applying ``fn(acc, v)`` from left to right.

        Args:
            init: The initial accumulator value.
            fn: Function called as ``fn(acc, v)`` for each element.

        Returns:
            The final accumulated value.

        Examples:
            >>> Iter([1, 2, 3]).fold(0, lambda acc, n: acc + n)
            6
        """
        acc = init
        for v in self._iter:
            acc = fn(acc, v)
        return acc

    def reduce(self, fn: Callable[[T, T], T]) -> T | None:
        """Reduce elements using a binary function, returning None if empty.

        The first element seeds the accumulator; the iterator must be non-empty
        to return a value.

        Args:
            fn: Associative binary function applied left-to-right.

        Returns:
            The reduced value, or None if the iterator is empty.

        Examples:
            >>> Iter([1, 2, 3]).reduce(lambda a, b: a + b)
            6
            >>> Iter([]).reduce(lambda a, b: a + b)
        """
        it = iter(self._iter)
        try:
            acc = next(it)
        except StopIteration:
            return None
        for v in it:
            acc = fn(acc, v)
        return acc

    def collect(self) -> list[T]:
        """Consume the iterator and return all elements as a list.

        Returns:
            A list containing every remaining element.

        Examples:
            >>> Iter([1, 2, 3]).map(lambda n: n + 1).collect()
            [2, 3, 4]
        """
        return list(self._iter)

    def collect_into(self, collection: Any) -> Any:
        """Append all elements into the given collection and return it.

        Args:
            collection: Any mutable collection with an ``append`` method.

        Returns:
            The collection with all elements appended, for chaining.

        Examples:
            >>> Iter([1, 2, 3]).collect_into([])
            [1, 2, 3]
        """
        for v in self._iter:
            collection.append(v)
        return collection

    def count(self) -> int:
        """Consume the iterator and count its remaining elements.

        Returns:
            The number of elements that were remaining.

        Examples:
            >>> Iter([1, 2, 3]).count()
            3
        """
        n = 0
        for _ in self._iter:
            n += 1
        return n

    def sum(self) -> T:
        """Sum all numeric elements in the iterator.

        Returns:
            The total of all elements, starting from 0.

        Examples:
            >>> Iter([1, 2, 3]).sum()
            6
        """
        return self.fold(0, lambda a, b: a + b)  # type: ignore

    def product(self) -> T:
        """Multiply all numeric elements in the iterator.

        Returns:
            The product of all elements, starting from 1.

        Examples:
            >>> Iter([2, 3, 4]).product()
            24
        """
        return self.fold(1, lambda a, b: a * b)  # type: ignore

    def min(self) -> T | None:
        """Return the minimum element, or None if empty.

        Returns:
            The smallest element, or None if the iterator is empty.

        Examples:
            >>> Iter([3, 1, 2]).min()
            1
        """
        return self.reduce(lambda a, b: a if a < b else b)

    def max(self) -> T | None:
        """Return the maximum element, or None if empty.

        Returns:
            The largest element, or None if the iterator is empty.

        Examples:
            >>> Iter([3, 1, 2]).max()
            3
        """
        return self.reduce(lambda a, b: a if a > b else b)

    def all(self, predicate: Callable[[T], bool]) -> bool:
        """Return True if all elements satisfy the predicate.

        Short-circuits on the first failing element.

        Args:
            predicate: Function tested against each element.

        Returns:
            True if every element matches, False otherwise. An empty iterator
            returns True.

        Examples:
            >>> Iter([2, 4]).all(lambda n: n % 2 == 0)
            True
        """
        for v in self._iter:
            if not predicate(v):
                return False
        return True

    def any(self, predicate: Callable[[T], bool]) -> bool:
        """Return True if any element satisfies the predicate.

        Short-circuits on the first matching element.

        Args:
            predicate: Function tested against each element.

        Returns:
            True if any element matches, False otherwise.

        Examples:
            >>> Iter([1, 2]).any(lambda n: n > 1)
            True
        """
        for v in self._iter:
            if predicate(v):
                return True
        return False

    def position(self, predicate: Callable[[T], bool]) -> int | None:
        """Return the index of the first element satisfying the predicate, or None.

        Args:
            predicate: Function tested against each element.

        Returns:
            The 0-based index of the first match, or None if none found.

        Examples:
            >>> Iter(["a", "b", "c"]).position(lambda s: s == "b")
            1
        """
        for i, v in enumerate(self._iter):
            if predicate(v):
                return i
        return None

    def nth(self, n: int) -> T | None:
        """Return the element at index n, or None if the iterator is too short.

        Args:
            n: The 0-based index of the element to return.

        Returns:
            The element at index n, or None if fewer than n + 1 elements remain.

        Examples:
            >>> Iter([10, 20, 30]).nth(1)
            20
        """
        for i, v in enumerate(self._iter):
            if i == n:
                return v
        return None

    def last(self) -> T | None:
        """Consume the iterator and return its last element, or None if empty.

        Returns:
            The final element, or None if the iterator is empty.

        Examples:
            >>> Iter([1, 2, 3]).last()
            3
        """
        result = None
        for v in self._iter:
            result = v
        return result

    def next(self) -> T:
        """Return the next element from the iterator.

        Returns:
            The next element.

        Raises:
            StopIteration: If the iterator is exhausted.

        Examples:
            >>> it = Iter([1, 2])
            >>> it.next()
            1
        """
        return next(self._iter)

    def for_each(self, fn: Callable[[T], Any]) -> None:
        """Apply a function to each element for its side effects.

        Consumes the iterator; the function's return value is ignored.

        Args:
            fn: Function called with each element.

        Examples:
            >>> Iter([1, 2]).for_each(print)
            1
            2
        """
        for v in self._iter:
            fn(v)

    def partition(self, predicate: Callable[[T], bool]) -> tuple[list[T], list[T]]:
        """Split elements into two lists based on the predicate.

        Args:
            predicate: Function deciding which list each element joins.

        Returns:
            A ``(matching, non_matching)`` tuple of lists.

        Examples:
            >>> Iter(range(5)).partition(lambda n: n % 2 == 0)
            ([0, 2, 4], [1, 3])
        """
        a, b = [], []
        for v in self._iter:
            (a if predicate(v) else b).append(v)
        return a, b

    def __iter__(self) -> Iterator[T]:
        """Return the underlying iterator."""
        return self._iter

    def __next__(self) -> T:
        """Return the next element from the underlying iterator."""
        return next(self._iter)

    def __repr__(self) -> str:
        """Return a concise representation of this Iter."""
        return "Iter(...)"


class PeekableIter(Generic[T]):
    """An iterator that supports peeking at the next element without consuming it.

    Efficient for lookahead-based algorithms: the peeked value is cached so a
    subsequent call to :meth:`next` returns it without pulling from the
    underlying iterator again.

    Examples:
        >>> p = PeekableIter(iter([1, 2]))
        >>> p.peek()
        1
        >>> p.peek()
        1
        >>> p.next()
        1
    """

    __slots__ = ("_iter", "_peeked", "_has_peeked")

    def __init__(self, source: Iterator[T]) -> None:
        """Initialize a PeekableIter from an existing iterator.

        Args:
            source: The iterator to wrap for peekable access.
        """
        self._iter = source
        self._peeked: T = None  # type: ignore[assignment]
        self._has_peeked = False

    def peek(self) -> T | None:
        """Return the next element without advancing the iterator, or None.

        Repeated calls return the same value until :meth:`next` is called.

        Returns:
            The next element, or None if the iterator is empty.

        Examples:
            >>> p = PeekableIter(iter([1]))
            >>> p.peek()
            1
            >>> p.next()
            1
            >>> p.peek()
        """
        if self._has_peeked:
            return self._peeked
        try:
            self._peeked = next(self._iter)
            self._has_peeked = True
            return self._peeked
        except StopIteration:
            return None

    def next(self) -> T:
        """Return the next element, consuming a peeked value if available.

        Returns:
            The next element.

        Raises:
            StopIteration: If the iterator is exhausted.
        """
        if self._has_peeked:
            self._has_peeked = False
            return self._peeked
        return next(self._iter)

    def __iter__(self) -> Iterator[T]:
        """Return self as its own iterator."""
        return self

    def __next__(self) -> T:
        """Return the next element, consuming a peeked value if present."""
        return self.next()
