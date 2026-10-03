"""Iterator consumers: functions that consume or construct iterators.

Provides standalone functions such as collect, fold, for_each, count, sum,
min, max, any, all, find, and position, plus factory helpers that build the
adapter types and the ``Iter`` wrapper from plain iterables.
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

from .adapters import (
    Chain,
    Cloned,
    Copied,
    Cycle,
    Enumerate,
    FilterIter,
    FilterMap,
    FlatMap,
    Flatten,
    Inspect,
    Map,
    Peekable,
    Rev,
    Skip,
    Take,
    Zip,
)
from .iterator import Iter, PeekableIter

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


def collect(iterable: Iterable[T]) -> list[T]:
    """Consume an iterable and return all elements as a list.

    Args:
        iterable: The values to collect.

    Returns:
        A list containing every element of the iterable.

    Examples:
        >>> collect([1, 2, 3])
        [1, 2, 3]
    """
    return list(iterable)


def fold(iterable: Iterable[T], init: U, fn: Callable[[U, T], U]) -> U:
    """Fold all elements into a single accumulator using the given function.

    Applies ``fn(acc, v)`` from left to right, starting with ``init``.

    Args:
        iterable: The values to fold over.
        init: The initial accumulator value.
        fn: Function called as ``fn(acc, v)`` for each element.

    Returns:
        The final accumulated value.

    Examples:
        >>> fold([1, 2, 3], 0, lambda acc, n: acc + n)
        6
    """
    acc = init
    for v in iterable:
        acc = fn(acc, v)
    return acc


def for_each(iterable: Iterable[T], fn: Callable[[T], Any]) -> None:
    """Apply a function to each element for its side effects.

    Args:
        iterable: The values to pass to fn.
        fn: Function called with each element; its return value is ignored.

    Examples:
        >>> for_each([1, 2], print)
        1
        2
    """
    for v in iterable:
        fn(v)


def count(iterable: Iterable[T]) -> int:
    """Count and return the total number of elements in the iterable.

    Args:
        iterable: The values to count.

    Returns:
        The number of elements.

    Examples:
        >>> count([1, 2, 3])
        3
    """
    n = 0
    for _ in iterable:
        n += 1
    return n


def sum(iterable: Iterable[T]) -> T:
    """Sum all numeric elements in the iterable.

    Args:
        iterable: The numeric values to add.

    Returns:
        The total of all elements, starting from 0.

    Examples:
        >>> sum([1, 2, 3])
        6
    """
    return fold(iterable, 0, lambda a, b: a + b)  # type: ignore


def min(iterable: Iterable[T]) -> T | None:
    """Return the minimum element, or None if the iterable is empty.

    Args:
        iterable: The values to compare.

    Returns:
        The smallest element, or None if the iterable is empty.

    Examples:
        >>> min([3, 1, 2])
        1
    """
    it = iter(iterable)
    try:
        acc = next(it)
    except StopIteration:
        return None
    for v in it:
        if v < acc:
            acc = v
    return acc


def max(iterable: Iterable[T]) -> T | None:
    """Return the maximum element, or None if the iterable is empty.

    Args:
        iterable: The values to compare.

    Returns:
        The largest element, or None if the iterable is empty.

    Examples:
        >>> max([3, 1, 2])
        3
    """
    it = iter(iterable)
    try:
        acc = next(it)
    except StopIteration:
        return None
    for v in it:
        if v > acc:
            acc = v
    return acc


def any(iterable: Iterable[T], predicate: Callable[[T], bool]) -> bool:
    """Return True if any element in the iterable satisfies the predicate.

    Short-circuits on the first matching element.

    Args:
        iterable: The values to test.
        predicate: Function tested against each element.

    Returns:
        True if any element matches, False otherwise.

    Examples:
        >>> any([1, 2, 3], lambda n: n > 2)
        True
    """
    for v in iterable:
        if predicate(v):
            return True
    return False


def all(iterable: Iterable[T], predicate: Callable[[T], bool]) -> bool:
    """Return True if all elements in the iterable satisfy the predicate.

    Short-circuits on the first failing element.

    Args:
        iterable: The values to test.
        predicate: Function tested against each element.

    Returns:
        True if every element matches, False otherwise. An empty iterable
        returns True.

    Examples:
        >>> all([2, 4], lambda n: n % 2 == 0)
        True
    """
    for v in iterable:
        if not predicate(v):
            return False
    return True


def find(iterable: Iterable[T], predicate: Callable[[T], bool]) -> T | None:
    """Return the first element satisfying the predicate, or None if not found.

    Args:
        iterable: The values to search.
        predicate: Function tested against each element.

    Returns:
        The first matching element, or None if none match.

    Examples:
        >>> find([1, 2, 3], lambda n: n > 1)
        2
    """
    for v in iterable:
        if predicate(v):
            return v
    return None


def position(iterable: Iterable[T], predicate: Callable[[T], bool]) -> int | None:
    """Return the index of the first element satisfying the predicate, or None.

    Args:
        iterable: The values to search.
        predicate: Function tested against each element.

    Returns:
        The 0-based index of the first match, or None if none match.

    Examples:
        >>> position([10, 20, 30], lambda n: n == 20)
        1
    """
    for i, v in enumerate(iterable):
        if predicate(v):
            return i
    return None


def zip(a: Iterable[T], b: Iterable[U]) -> Zip[T, U]:
    """Create a Zip adapter pairing elements from two iterables.

    Iteration stops once the shorter iterable is exhausted.

    Args:
        a: The first iterable to pair from.
        b: The second iterable to pair from.

    Returns:
        A Zip adapter yielding ``(x, y)`` tuples.

    Examples:
        >>> list(zip([1, 2], ["a", "b"]))
        [(1, 'a'), (2, 'b')]
    """
    return Zip(a, b)


def enumerate(iterable: Iterable[T], start: int = 0) -> Enumerate[T]:
    """Create an Enumerate adapter yielding (index, value) pairs.

    Args:
        iterable: The values to pair with their indexes.
        start: The index assigned to the first element. Defaults to 0.

    Returns:
        An Enumerate adapter.

    Examples:
        >>> list(enumerate(["a", "b"], start=1))
        [(1, 'a'), (2, 'b')]
    """
    return Enumerate(iterable, start)


def chain(a: Iterable[T], b: Iterable[T]) -> Chain[T]:
    """Create a Chain adapter concatenating two iterables.

    Args:
        a: The first iterable to yield from.
        b: The second iterable to yield from after a is exhausted.

    Returns:
        A Chain adapter.

    Examples:
        >>> list(chain([1, 2], [3, 4]))
        [1, 2, 3, 4]
    """
    return Chain(a, b)


def peek(iterable: Iterable[T]) -> Peekable[T]:
    """Create a Peekable adapter for lookahead iteration.

    Args:
        iterable: The values to iterate over with lookahead support.

    Returns:
        A Peekable adapter.

    Examples:
        >>> p = iter(peek([1, 2]))
        >>> p.peek()
        1
        >>> next(p)
        1
    """
    return Peekable(iterable)


def step_by(iterable: Iterable[T], step: int) -> Iter[T]:
    """Create an Iter and take every step-th element.

    Args:
        iterable: The values to draw from.
        step: The stride between yielded elements; must be a positive integer.

    Returns:
        An Iter yielding elements at indexes 0, step, 2 * step, ...

    Examples:
        >>> step_by(range(8), 3).collect()
        [0, 3, 6]
    """
    return Iter(iterable).step_by(step)


def skip(iterable: Iterable[T], n: int) -> Skip[T]:
    """Create a Skip adapter that skips the first n elements.

    Args:
        iterable: The values to draw from.
        n: The number of leading elements to drop.

    Returns:
        A Skip adapter.

    Examples:
        >>> list(skip(range(5), 2))
        [2, 3, 4]
    """
    return Skip(iterable, n)


def take(iterable: Iterable[T], n: int) -> Take[T]:
    """Create a Take adapter that yields at most n elements.

    Args:
        iterable: The values to draw from.
        n: The maximum number of elements to yield.

    Returns:
        A Take adapter.

    Examples:
        >>> list(take(range(10), 3))
        [0, 1, 2]
    """
    return Take(iterable, n)


def rev(iterable: Iterable[T]) -> Rev[T]:
    """Create a Rev adapter that reverses element order.

    Args:
        iterable: The values to yield in reverse order.

    Returns:
        A Rev adapter.

    Examples:
        >>> list(rev([1, 2, 3]))
        [3, 2, 1]
    """
    return Rev(iterable)


def inspect(iterable: Iterable[T], fn: Callable[[T], Any]) -> Inspect[T]:
    """Create an Inspect adapter that calls fn on each element for side effects.

    Args:
        iterable: The values to pass through.
        fn: Function called with each element for its side effects.

    Returns:
        An Inspect adapter.

    Examples:
        >>> seen = []
        >>> list(inspect([1, 2], seen.append))
        [1, 2]
    """
    return Inspect(iterable, fn)


def copied(iterable: Iterable[T]) -> Copied[T]:
    """Create a Copied adapter that yields elements from the source.

    Args:
        iterable: The values to iterate over.

    Returns:
        A Copied adapter.

    Examples:
        >>> list(copied([1, 2, 3]))
        [1, 2, 3]
    """
    return Copied(iterable)


def cloned(iterable: Iterable[T]) -> Cloned[T]:
    """Create a Cloned adapter that clones each element.

    Args:
        iterable: The values to iterate over.

    Returns:
        A Cloned adapter.

    Examples:
        >>> list(cloned([1, 2, 3]))
        [1, 2, 3]
    """
    return Cloned(iterable)


def filter(iterable: Iterable[T], predicate: Callable[[T], bool]) -> FilterIter[T]:
    """Create a FilterIter adapter yielding only elements matching the predicate.

    Args:
        iterable: The values to filter.
        predicate: Function returning True for elements to keep.

    Returns:
        A FilterIter adapter.

    Examples:
        >>> list(filter(range(6), lambda n: n % 2 == 0))
        [0, 2, 4]
    """
    return FilterIter(iterable, predicate)


def filter_map(iterable: Iterable[T], fn: Callable[[T], U | None]) -> FilterMap[T, U]:
    """Create a FilterMap adapter mapping elements and yielding non-None results.

    Args:
        iterable: The values to map.
        fn: Function returning a value to keep or None to drop.

    Returns:
        A FilterMap adapter.

    Examples:
        >>> list(filter_map(["1", "x", "3"], lambda s: int(s) if s.isdigit() else None))
        [1, 3]
    """
    return FilterMap(iterable, fn)


def flat_map(iterable: Iterable[T], fn: Callable[[T], Iterable[U]]) -> FlatMap[T, U]:
    """Create a FlatMap adapter mapping elements to iterables and flattening.

    Args:
        iterable: The values to expand.
        fn: Function returning an iterable for each element.

    Returns:
        A FlatMap adapter.

    Examples:
        >>> list(flat_map([[1, 2], [3]], lambda lst: [x * 10 for x in lst]))
        [10, 20, 30]
    """
    return FlatMap(iterable, fn)


def flatten(iterable: Iterable[Iterable[T]]) -> Flatten[T]:
    """Create a Flatten adapter that flattens one level of nesting.

    Args:
        iterable: An iterable whose elements are themselves iterables.

    Returns:
        A Flatten adapter.

    Examples:
        >>> list(flatten([[1, 2], [3, 4]]))
        [1, 2, 3, 4]
    """
    return Flatten(iterable)


def map(iterable: Iterable[T], fn: Callable[[T], U]) -> Map[T, U]:
    """Create a Map adapter applying fn to each element.

    Args:
        iterable: The values to transform.
        fn: Function called once per element.

    Returns:
        A Map adapter.

    Examples:
        >>> list(map([1, 2, 3], lambda n: n * 2))
        [2, 4, 6]
    """
    return Map(iterable, fn)
