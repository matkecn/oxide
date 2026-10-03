"""Range types — Python equivalents of Rust range syntax.

Provides Range, RangeInclusive, RangeFrom, RangeTo, RangeToInclusive, RangeFull
with factory functions for constructing range objects.
"""

from __future__ import annotations

from typing import Generic, Iterator, TypeVar


T = TypeVar("T")


class Range(Generic[T]):
    """A half-open range [start, end) equivalent to Rust's start..end.

    Represents all values ``v`` such that ``start <= v < end``. Supports
    membership and equality tests, iteration over integer values, and counting.

    Example:
        >>> r = Range(1, 5)
        >>> 3 in r
        True
        >>> list(r)
        [1, 2, 3, 4]
    """

    __slots__ = ("start", "end")

    def __init__(self, start: T, end: T) -> None:
        """Create a half-open range over [start, end).

        Args:
            start (T): The inclusive lower bound.
            end (T): The exclusive upper bound.
        """
        self.start = start
        self.end = end

    def contains(self, value: T) -> bool:
        """Return True if value is within [start, end).

        Args:
            value (T): The value to test.

        Returns:
            bool: True if ``start <= value < end``, else False.
        """
        return self.start <= value < self.end

    def contains_inclusive(self, value: T) -> bool:
        """Return True if value is within [start, end].

        Args:
            value (T): The value to test.

        Returns:
            bool: True if ``start <= value <= end``, else False.
        """
        return self.start <= value <= self.end

    def is_empty(self) -> bool:
        """Return True if the range contains no elements.

        Returns:
            bool: True when ``start >= end``, else False.
        """
        return self.start >= self.end

    def iter(self) -> Iterator[T]:
        """Yield the integer values in the half-open range.

        Yields:
            T: Each integer from ``int(start)`` up to but excluding ``int(end)``.

        Example:
            >>> list(Range(0, 3).iter())
            [0, 1, 2]
        """
        yield from range(int(self.start), int(self.end))

    def __iter__(self) -> Iterator[T]:
        """Iterate over the integer values in the range.

        Yields:
            T: Each integer from ``int(start)`` up to excluding ``int(end)``.
        """
        yield from range(int(self.start), int(self.end))

    def __len__(self) -> int:
        """Return the number of elements in the range.

        Returns:
            int: The count of elements, never negative.
        """
        return max(0, int(self.end) - int(self.start))

    def __contains__(self, value: T) -> bool:
        """Return True if value is within [start, end).

        Args:
            value (T): The value to test.

        Returns:
            bool: True if ``start <= value < end``, else False.
        """
        return self.start <= value < self.end

    def __eq__(self, other: object) -> bool:
        """Return True if another Range has the same start and end.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: True if both bounds match, else NotImplemented.
        """
        if isinstance(other, Range):
            return self.start == other.start and self.end == other.end
        return NotImplemented

    def __hash__(self) -> int:
        """Return a hash based on the range bounds.

        Returns:
            int: The hash of the ``(start, end)`` pair.
        """
        return hash((self.start, self.end))

    def __repr__(self) -> str:
        """Return the Rust-style notation for this range.

        Returns:
            str: The range formatted as ``start..end``.
        """
        return f"{self.start}..{self.end}"


class RangeInclusive(Generic[T]):
    """An inclusive range [start, end] equivalent to Rust's start..=end.

    Represents all values ``v`` such that ``start <= v <= end``, including the
    endpoint. Supports membership, iteration, and counting.

    Example:
        >>> r = RangeInclusive(1, 3)
        >>> list(r)
        [1, 2, 3]
    """

    __slots__ = ("start", "end")

    def __init__(self, start: T, end: T) -> None:
        """Create an inclusive range over [start, end].

        Args:
            start (T): The inclusive lower bound.
            end (T): The inclusive upper bound.
        """
        self.start = start
        self.end = end

    def contains(self, value: T) -> bool:
        """Return True if value is within [start, end].

        Args:
            value (T): The value to test.

        Returns:
            bool: True if ``start <= value <= end``, else False.
        """
        return self.start <= value <= self.end

    def is_empty(self) -> bool:
        """Return True if the range contains no elements.

        Returns:
            bool: True when ``start > end``, else False.
        """
        return self.start > self.end

    def iter(self) -> Iterator[T]:
        """Yield the integer values in the inclusive range.

        Yields:
            T: Each integer from ``int(start)`` through ``int(end)`` inclusive.

        Example:
            >>> list(RangeInclusive(-1, 1).iter())
            [-1, 0, 1]
        """
        yield from range(int(self.start), int(self.end) + 1)

    def __iter__(self) -> Iterator[T]:
        """Iterate over the integer values in the range.

        Yields:
            T: Each integer from ``int(start)`` through ``int(end)`` inclusive.
        """
        yield from range(int(self.start), int(self.end) + 1)

    def __len__(self) -> int:
        """Return the number of elements in the range.

        Returns:
            int: The count of elements, never negative.
        """
        return max(0, int(self.end) - int(self.start) + 1)

    def __contains__(self, value: T) -> bool:
        """Return True if value is within [start, end].

        Args:
            value (T): The value to test.

        Returns:
            bool: True if ``start <= value <= end``, else False.
        """
        return self.start <= value <= self.end

    def __eq__(self, other: object) -> bool:
        """Return True if another RangeInclusive has the same bounds.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: True if both bounds match, else NotImplemented.
        """
        if isinstance(other, RangeInclusive):
            return self.start == other.start and self.end == other.end
        return NotImplemented

    def __hash__(self) -> int:
        """Return a hash based on the range bounds.

        Returns:
            int: The hash of the ``(start, end)`` pair.
        """
        return hash((self.start, self.end))

    def __repr__(self) -> str:
        """Return the Rust-style notation for this range.

        Returns:
            str: The range formatted as ``start..=end``.
        """
        return f"{self.start}..={self.end}"


class RangeFrom(Generic[T]):
    """An unbounded-from range [start, ..) equivalent to Rust's start..

    Represents all values ``v`` such that ``v >= start``. Since there is no
    upper bound, iteration requires a finite ``end`` argument.

    Example:
        >>> r = RangeFrom(5)
        >>> 10 in r
        True
    """

    __slots__ = ("start",)

    def __init__(self, start: T) -> None:
        """Create an unbounded-from range.

        Args:
            start (T): The inclusive lower bound.
        """
        self.start = start

    def contains(self, value: T) -> bool:
        """Return True if value is >= start.

        Args:
            value (T): The value to test.

        Returns:
            bool: True if ``value >= start``, else False.
        """
        return value >= self.start

    def iter(self, end: T) -> Iterator[T]:
        """Yield integer values from start up to (but not including) end.

        Args:
            end (T): The exclusive upper bound for iteration.

        Yields:
            T: Each integer from ``int(start)`` up to excluding ``int(end)``.

        Example:
            >>> list(RangeFrom(2).iter(5))
            [2, 3, 4]
        """
        yield from range(int(self.start), int(end))

    def __contains__(self, value: T) -> bool:
        """Return True if value is >= start.

        Args:
            value (T): The value to test.

        Returns:
            bool: True if ``value >= start``, else False.
        """
        return value >= self.start

    def __eq__(self, other: object) -> bool:
        """Return True if another RangeFrom has the same start.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: True if the starts match, else NotImplemented.
        """
        if isinstance(other, RangeFrom):
            return self.start == other.start
        return NotImplemented

    def __hash__(self) -> int:
        """Return a hash based on the start bound.

        Returns:
            int: The hash of the start value.
        """
        return hash(self.start)

    def __repr__(self) -> str:
        """Return the Rust-style notation for this range.

        Returns:
            str: The range formatted as ``start..``.
        """
        return f"{self.start}.."


class RangeTo(Generic[T]):
    """An unbounded-to range (..end) equivalent to Rust's ..end.

    Represents all values ``v`` such that ``v < end``. Since there is no lower
    bound, iteration requires a finite ``start`` argument.

    Example:
        >>> r = RangeTo(3)
        >>> 2 in r
        True
    """

    __slots__ = ("end",)

    def __init__(self, end: T) -> None:
        """Create an unbounded-to range.

        Args:
            end (T): The exclusive upper bound.
        """
        self.end = end

    def contains(self, value: T) -> bool:
        """Return True if value is < end.

        Args:
            value (T): The value to test.

        Returns:
            bool: True if ``value < end``, else False.
        """
        return value < self.end

    def iter(self, start: T = 0) -> Iterator[T]:
        """Yield integer values from start up to (but not including) end.

        Args:
            start (T, optional): The inclusive start for iteration. Defaults to 0.

        Yields:
            T: Each integer from ``int(start)`` up to excluding ``int(end)``.

        Example:
            >>> list(RangeTo(3).iter())
            [0, 1, 2]
        """
        yield from range(int(start), int(self.end))

    def __contains__(self, value: T) -> bool:
        """Return True if value is < end.

        Args:
            value (T): The value to test.

        Returns:
            bool: True if ``value < end``, else False.
        """
        return value < self.end

    def __eq__(self, other: object) -> bool:
        """Return True if another RangeTo has the same end.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: True if the ends match, else NotImplemented.
        """
        if isinstance(other, RangeTo):
            return self.end == other.end
        return NotImplemented

    def __hash__(self) -> int:
        """Return a hash based on the end bound.

        Returns:
            int: The hash of the end value.
        """
        return hash(self.end)

    def __repr__(self) -> str:
        """Return the Rust-style notation for this range.

        Returns:
            str: The range formatted as ``..end``.
        """
        return f"..{self.end}"


class RangeToInclusive(Generic[T]):
    """An unbounded-to-inclusive range (..=end) equivalent to Rust's ..=end.

    Represents all values ``v`` such that ``v <= end``. Since there is no lower
    bound, iteration requires a finite ``start`` argument.

    Example:
        >>> r = RangeToInclusive(3)
        >>> 3 in r
        True
    """

    __slots__ = ("end",)

    def __init__(self, end: T) -> None:
        """Create an unbounded-to-inclusive range.

        Args:
            end (T): The inclusive upper bound.
        """
        self.end = end

    def contains(self, value: T) -> bool:
        """Return True if value is <= end.

        Args:
            value (T): The value to test.

        Returns:
            bool: True if ``value <= end``, else False.
        """
        return value <= self.end

    def iter(self, start: T = 0) -> Iterator[T]:
        """Yield integer values from start up to and including end.

        Args:
            start (T, optional): The inclusive start for iteration. Defaults to 0.

        Yields:
            T: Each integer from ``int(start)`` through ``int(end)`` inclusive.

        Example:
            >>> list(RangeToInclusive(2).iter())
            [0, 1, 2]
        """
        yield from range(int(start), int(self.end) + 1)

    def __contains__(self, value: T) -> bool:
        """Return True if value is <= end.

        Args:
            value (T): The value to test.

        Returns:
            bool: True if ``value <= end``, else False.
        """
        return value <= self.end

    def __eq__(self, other: object) -> bool:
        """Return True if another RangeToInclusive has the same end.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: True if the ends match, else NotImplemented.
        """
        if isinstance(other, RangeToInclusive):
            return self.end == other.end
        return NotImplemented

    def __hash__(self) -> int:
        """Return a hash based on the end bound.

        Returns:
            int: The hash of the end value.
        """
        return hash(self.end)

    def __repr__(self) -> str:
        """Return the Rust-style notation for this range.

        Returns:
            str: The range formatted as ``..=end``.
        """
        return f"..={self.end}"


class RangeFull:
    """A range that covers all values, equivalent to Rust's ..

    An unbounded range that contains every value. It has no iteration support
    since no finite bounds exist.

    Example:
        >>> 42 in RangeFull()
        True
    """

    __slots__ = ()

    def contains(self, value: object) -> bool:
        """Return True for any value since the range is unbounded.

        Args:
            value (object): The value to test (ignored).

        Returns:
            bool: Always True.
        """
        return True

    def __contains__(self, value: object) -> bool:
        """Return True for any value since the range is unbounded.

        Args:
            value (object): The value to test (ignored).

        Returns:
            bool: Always True.
        """
        return True

    def __eq__(self, other: object) -> bool:
        """Return True if another object is also a RangeFull.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: True if ``other`` is a ``RangeFull``, else NotImplemented.
        """
        if isinstance(other, RangeFull):
            return True
        return NotImplemented

    def __hash__(self) -> int:
        """Return a constant hash shared by all RangeFull instances.

        Returns:
            int: A fixed hash value.
        """
        return hash(None)

    def __repr__(self) -> str:
        """Return the Rust-style notation for this range.

        Returns:
            str: The string ``".."``.
        """
        return ".."


def range_(start: T, end: T) -> Range[T]:
    """Create a half-open Range [start, end).

    Args:
        start (T): The inclusive lower bound.
        end (T): The exclusive upper bound.

    Returns:
        Range: A ``Range`` instance spanning ``[start, end)``.

    Example:
        >>> list(range_(1, 3))
        [1, 2]
    """
    return Range(start, end)


def range_inclusive(start: T, end: T) -> RangeInclusive[T]:
    """Create an inclusive RangeInclusive [start, end].

    Args:
        start (T): The inclusive lower bound.
        end (T): The inclusive upper bound.

    Returns:
        RangeInclusive: A ``RangeInclusive`` instance spanning ``[start, end]``.

    Example:
        >>> list(range_inclusive(1, 3))
        [1, 2, 3]
    """
    return RangeInclusive(start, end)


def range_from(start: T) -> RangeFrom[T]:
    """Create an unbounded-from RangeFrom [start, ..).

    Args:
        start (T): The inclusive lower bound.

    Returns:
        RangeFrom: A ``RangeFrom`` instance starting at ``start``.
    """
    return RangeFrom(start)


def range_to(end: T) -> RangeTo[T]:
    """Create an unbounded-to RangeTo (..end).

    Args:
        end (T): The exclusive upper bound.

    Returns:
        RangeTo: A ``RangeTo`` instance ending at ``end``.
    """
    return RangeTo(end)


def range_to_inclusive(end: T) -> RangeToInclusive[T]:
    """Create an unbounded-to-inclusive RangeToInclusive (..=end).

    Args:
        end (T): The inclusive upper bound.

    Returns:
        RangeToInclusive: A ``RangeToInclusive`` instance ending at ``end``.
    """
    return RangeToInclusive(end)
