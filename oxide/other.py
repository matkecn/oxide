"""Miscellaneous types inspired by the Rust standard library.

Provides comparison and flow-control types (``Ordering``, ``ControlFlow``),
arithmetic wrappers (``Reverse``, ``Wrapping``, ``Saturating``, ``NonZero``),
and small-vector data structures (``SmallVec``, ``ArrayVec``, ``TinyVec``,
``BitVec``) as well as the :class:`CreateMeta` metadata type.

Example:
    >>> from oxide import Ordering, SmallVec
    >>> Ordering.from_cmp(1, 2).is_less()
    True
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, Iterable, Iterator, TypeVar

from ._collections.extra import Drain

T = TypeVar("T")


class Ordering:
    """Three-way comparison result: Less, Equal, or Greater.

    Mirrors Rust's ``std::cmp::Ordering``. Instances can be compared to each
    other and support combinational methods like :meth:`then` and
    :meth:`reverse`.

    Example:
        >>> from oxide import Ordering
        >>> Ordering.from_cmp(3, 1).is_greater()
        True
        >>> Ordering.less().reverse().is_greater()
        True
    """

    __slots__ = ("_kind",)

    LESS = -1
    EQUAL = 0
    GREATER = 1

    def __init__(self, kind: int) -> None:
        """Initialize with an internal integer kind.

        Args:
            kind: One of ``LESS``, ``EQUAL``, or ``GREATER``.
        """
        self._kind = kind

    @classmethod
    def less(cls) -> Ordering:
        """Return the Less ordering.

        Returns:
            The ordering indicating ``a < b``.
        """
        return cls(cls.LESS)

    @classmethod
    def equal(cls) -> Ordering:
        """Return the Equal ordering.

        Returns:
            The ordering indicating ``a == b``.
        """
        return cls(cls.EQUAL)

    @classmethod
    def greater(cls) -> Ordering:
        """Return the Greater ordering.

        Returns:
            The ordering indicating ``a > b``.
        """
        return cls(cls.GREATER)

    @classmethod
    def from_cmp(cls, a: Any, b: Any) -> Ordering:  # type: ignore
        """Return the ordering between ``a`` and ``b``.

        Args:
            a: The first value.
            b: The second value.

        Returns:
            ``Less`` if ``a < b``, ``Greater`` if ``a > b``, else ``Equal``.

        Example:
            >>> from oxide import Ordering
            >>> Ordering.from_cmp(5, 2).is_greater()
            True
        """
        if a < b:
            return cls(cls.LESS)
        if a > b:
            return cls(cls.GREATER)
        return cls(cls.EQUAL)

    def reverse(self) -> Ordering:
        """Return the reversed ordering.

        Returns:
            The opposite ordering: Less becomes Greater and vice versa, Equal
            stays Equal.
        """
        return Ordering(-self._kind)

    def then(self, other: Ordering) -> Ordering:  # type: ignore
        """Return this ordering if not Equal, otherwise return ``other``.

        Args:
            other: The ordering to fall back to when this one is Equal.

        Returns:
            This ordering when it is Less or Greater; otherwise ``other``.
        """
        if self._kind != 0:
            return self
        return other

    def then_with(self, f: Callable[[], Ordering]) -> Ordering:  # type: ignore
        """Return this ordering if not Equal, otherwise call ``f`` for the result.

        Args:
            f: A zero-argument callable returning an Ordering.

        Returns:
            This ordering when Less or Greater; otherwise ``f()``.
        """
        if self._kind != 0:
            return self
        return f()

    def is_less(self) -> bool:  # type: ignore
        """Return True if this is the Less ordering.

        Returns:
            ``True`` when the ordering represents ``a < b``.
        """
        return self._kind < 0

    def is_equal(self) -> bool:  # type: ignore
        """Return True if this is the Equal ordering.

        Returns:
            ``True`` when the ordering represents ``a == b``.
        """
        return self._kind == 0

    def is_greater(self) -> bool:  # type: ignore
        """Return True if this is the Greater ordering.

        Returns:
            ``True`` when the ordering represents ``a > b``.
        """
        return self._kind > 0

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Ordering):
            return self._kind == other._kind
        return NotImplemented

    def __ne__(self, other: object) -> bool:
        if isinstance(other, Ordering):
            return self._kind != other._kind
        return NotImplemented

    def __lt__(self, other: Ordering) -> bool:
        if isinstance(other, Ordering):
            return self._kind < other._kind
        return NotImplemented

    def __le__(self, other: Ordering) -> bool:
        if isinstance(other, Ordering):
            return self._kind <= other._kind
        return NotImplemented

    def __gt__(self, other: Ordering) -> bool:
        if isinstance(other, Ordering):
            return self._kind > other._kind
        return NotImplemented

    def __ge__(self, other: Ordering) -> bool:
        if isinstance(other, Ordering):
            return self._kind >= other._kind
        return NotImplemented

    def __hash__(self) -> int:
        return self._kind

    def __repr__(self) -> str:
        if self._kind < 0:
            return "Ordering::Less"
        if self._kind == 0:
            return "Ordering::Equal"
        return "Ordering::Greater"


class ControlFlow:
    """Represents a break or continue result from a loop.

    Mirrors Rust's ``std::ops::ControlFlow``. Use :meth:`cont` and :meth:`brk`
    to produce a continue or break variant carrying an optional value.

    Example:
        >>> from oxide import ControlFlow
        >>> ControlFlow.cont(1).is_continue()
        True
        >>> ControlFlow.brk(9).break_value()
        9
    """

    __slots__ = ("_break", "_value", "_is_break")

    def __init__(self, is_break: bool = False, value: Any = None) -> None:
        """Initialize the flow control value.

        Args:
            is_break: Whether this is a break variant.
            value: An optional payload value.
        """
        self._is_break = is_break
        self._value = value

    @classmethod
    def cont(cls, value: Any = None) -> ControlFlow:
        """Create a continue variant carrying an optional value.

        Args:
            value: Optional payload to attach.

        Returns:
            A continue variant of ControlFlow.
        """
        return cls(False, value)

    @classmethod
    def brk(cls, value: Any = None) -> ControlFlow:
        """Create a break variant carrying an optional value.

        Args:
            value: Optional payload to attach.

        Returns:
            A break variant of ControlFlow.
        """
        return cls(True, value)

    def is_break(self) -> bool:  # type: ignore
        """Return True if this is a break variant.

        Returns:
            Whether the variant is a break.
        """
        return self._is_break

    def is_continue(self) -> bool:  # type: ignore
        """Return True if this is a continue variant.

        Returns:
            Whether the variant is a continue.
        """
        return not self._is_break

    def break_value(self) -> Any | None:  # type: ignore
        """Return the break value, or None if this is a continue.

        Returns:
            The payload when this is a break variant; otherwise ``None``.
        """
        if self._is_break:
            return self._value
        return None

    def continue_value(self) -> Any | None:  # type: ignore
        """Return the continue value, or None if this is a break.

        Returns:
            The payload when this is a continue variant; otherwise ``None``.
        """
        if not self._is_break:
            return self._value
        return None

    def map_break(self, f: Callable[[Any], Any]) -> ControlFlow:  # type: ignore
        """Transform the break value with ``f`` if this is a break.

        Args:
            f: A callable applied to the break value.

        Returns:
            A new break variant if this is a break; otherwise this unchanged.
        """
        if self._is_break:
            return ControlFlow(True, f(self._value))
        return self

    def map_continue(self, f: Callable[[Any], Any]) -> ControlFlow:  # type: ignore
        """Transform the continue value with ``f`` if this is a continue.

        Args:
            f: A callable applied to the continue value.

        Returns:
            A new continue variant if this is a continue; otherwise this
            unchanged.
        """
        if not self._is_break:
            return ControlFlow(False, f(self._value))
        return self

    def __repr__(self) -> str:
        if self._is_break:
            return f"ControlFlow::Break({self._value!r})"
        return f"ControlFlow::Continue({self._value!r})"


class Reverse(Generic[T]):
    """Wrapper that reverses the natural ordering of a wrapped value.

    Mirrors Rust's ``std::cmp::Reverse``. Comparisons on the wrapper compare
    the wrapped values in reverse, making it easy to sort in descending order.

    Example:
        >>> from oxide import Reverse
        >>> Reverse(2) < Reverse(1)
        True
        >>> sorted([Reverse(3), Reverse(1), Reverse(2)])
        [Reverse(3), Reverse(2), Reverse(1)]
    """

    __slots__ = ("_value",)

    def __init__(self, value: T) -> None:
        """Wrap a value with reversed comparison semantics.

        Args:
            value: The value to wrap.
        """
        self._value = value

    def into_inner(self) -> T:  # type: ignore
        """Return the wrapped value.

        Returns:
            The original value stored in the wrapper.
        """
        return self._value

    def as_ref(self) -> Any:  # type: ignore
        """Return a reference to the wrapped value.

        Returns:
            The wrapped value.
        """
        return self._value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Reverse):
            return self._value == other._value
        return NotImplemented

    def __ne__(self, other: object) -> bool:
        if isinstance(other, Reverse):
            return self._value != other._value
        return NotImplemented

    def __lt__(self, other: Reverse) -> bool:
        if isinstance(other, Reverse):
            return other._value < self._value
        return NotImplemented

    def __le__(self, other: Reverse) -> bool:
        if isinstance(other, Reverse):
            return other._value <= self._value
        return NotImplemented

    def __gt__(self, other: Reverse) -> bool:
        if isinstance(other, Reverse):
            return other._value > self._value
        return NotImplemented

    def __ge__(self, other: Reverse) -> bool:
        if isinstance(other, Reverse):
            return other._value >= self._value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)

    def __repr__(self) -> str:
        return f"Reverse({self._value!r})"


class Wrapping(Generic[T]):
    """Integer wrapper with wrapping (overflow) arithmetic.

    Mirrors Rust's ``std::num::Wrapping``. Arithmetic operations wrap around at
    32 bits (``0xFFFFFFFF``) instead of overflowing.

    Example:
        >>> from oxide import Wrapping
        >>> Wrapping(0xFFFFFFFF).wrapping_add(1).into_inner()
        0
    """

    __slots__ = ("_value",)

    def __init__(self, value: T) -> None:
        """Wrap an integer value.

        Args:
            value: The integer to wrap.
        """
        self._value = value

    def new(val: T) -> Wrapping[T]:
        """Create a new Wrapping value.

        Args:
            val: The integer to wrap.

        Returns:
            A new Wrapping instance containing ``val``.
        """
        return Wrapping(val)

    def into_inner(self) -> T:
        """Return the wrapped integer value.

        Returns:
            The underlying integer.
        """
        return self._value

    def wrapping_add(self, other: T) -> Wrapping[T]:
        """Add with wrapping semantics.

        Args:
            other: The value to add.

        Returns:
            The sum masked to 32 bits.
        """
        return Wrapping((int(self._value) + int(other)) & 0xFFFFFFFF)

    def wrapping_sub(self, other: T) -> Wrapping[T]:
        """Subtract with wrapping semantics.

        Args:
            other: The value to subtract.

        Returns:
            The difference masked to 32 bits.
        """
        return Wrapping((int(self._value) - int(other)) & 0xFFFFFFFF)

    def wrapping_mul(self, other: T) -> Wrapping[T]:
        """Multiply with wrapping semantics.

        Args:
            other: The value to multiply by.

        Returns:
            The product masked to 32 bits.
        """
        return Wrapping((int(self._value) * int(other)) & 0xFFFFFFFF)

    def wrapping_div(self, other: T) -> Wrapping[T]:  # type: ignore
        """Divide with wrapping semantics; returns 0 on division by zero.

        Args:
            other: The divisor.

        Returns:
            The quotient masked to 32 bits, or ``Wrapping(0)`` if ``other`` is
            zero.
        """
        if int(other) == 0:
            return Wrapping(0)
        return Wrapping((int(self._value) // int(other)) & 0xFFFFFFFF)

    def wrapping_neg(self) -> Wrapping[int]:  # type: ignore
        """Negate with wrapping semantics.

        Returns:
            The two's-complement negation masked to 32 bits.
        """
        return Wrapping((-int(self._value)) & 0xFFFFFFFF)

    def __add__(self, other: Wrapping | int) -> Wrapping:
        if isinstance(other, Wrapping):
            return self.wrapping_add(other._value)
        return self.wrapping_add(other)

    def __sub__(self, other: Wrapping | int) -> Wrapping:
        if isinstance(other, Wrapping):
            return self.wrapping_sub(other._value)
        return self.wrapping_sub(other)

    def __mul__(self, other: Wrapping | int) -> Wrapping:
        if isinstance(other, Wrapping):
            return self.wrapping_mul(other._value)
        return self.wrapping_mul(other)

    def __floordiv__(self, other: Wrapping | int) -> Wrapping:
        if isinstance(other, Wrapping):
            return self.wrapping_div(other._value)
        return self.wrapping_div(other)

    def __neg__(self) -> Wrapping:
        return self.wrapping_neg()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Wrapping):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)

    def __repr__(self) -> str:
        return f"Wrapping({self._value})"


class Saturating(Generic[T]):
    """Integer wrapper with saturating arithmetic that clamps at min/max.

    Mirrors Rust's ``std::num::Saturating``. Results are clamped to the 32-bit
    signed range defined by :attr:`MIN` and :attr:`MAX` rather than wrapping or
    overflowing.

    Example:
        >>> from oxide import Saturating
        >>> Saturating(2**31 - 1).saturating_add(1).into_inner()
        2147483647
    """

    __slots__ = ("_value",)

    MAX = 2**31 - 1
    MIN = -(2**31)

    def __init__(self, value: T) -> None:
        """Wrap an integer value.

        Args:
            value: The integer to wrap.
        """
        self._value = value

    def new(val: T) -> Saturating[T]:
        """Create a new Saturating value.

        Args:
            val: The integer to wrap.

        Returns:
            A new Saturating instance containing ``val``.
        """
        return Saturating(val)

    def into_inner(self) -> T:
        """Return the wrapped integer value.

        Returns:
            The underlying integer.
        """
        return self._value

    def saturating_add(self, other: T) -> Saturating[T]:
        """Add with saturating semantics.

        Args:
            other: The value to add.

        Returns:
            The sum clamped to :attr:`MIN`/:attr:`MAX`.
        """
        result = int(self._value) + int(other)
        return Saturating(max(self.MIN, min(self.MAX, result)))

    def saturating_sub(self, other: T) -> Saturating[T]:
        """Subtract with saturating semantics.

        Args:
            other: The value to subtract.

        Returns:
            The difference clamped to :attr:`MIN`/:attr:`MAX`.
        """
        result = int(self._value) - int(other)
        return Saturating(max(self.MIN, min(self.MAX, result)))

    def saturating_mul(self, other: T) -> Saturating[T]:
        """Multiply with saturating semantics.

        Args:
            other: The value to multiply by.

        Returns:
            The product clamped to :attr:`MIN`/:attr:`MAX`.
        """
        result = int(self._value) * int(other)
        return Saturating(max(self.MIN, min(self.MAX, result)))

    def __add__(self, other: Saturating | int) -> Saturating:
        if isinstance(other, Saturating):
            return self.saturating_add(other._value)
        return self.saturating_add(other)

    def __sub__(self, other: Saturating | int) -> Saturating:
        if isinstance(other, Saturating):
            return self.saturating_sub(other._value)
        return self.saturating_sub(other)

    def __mul__(self, other: Saturating | int) -> Saturating:
        if isinstance(other, Saturating):
            return self.saturating_mul(other._value)
        return self.saturating_mul(other)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Saturating):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)

    def __repr__(self) -> str:
        return f"Saturating({self._value})"


class NonZero(Generic[T]):
    """A numeric value guaranteed to be non-zero.

    Mirrors Rust's ``std::num::NonZero*`` types. Construction rejects zero, so
    instances always hold a non-zero value.

    Example:
        >>> from oxide import NonZero
        >>> NonZero.new(5).get()
        5
        >>> NonZero.try_new(0) is None
        True
    """

    __slots__ = ("_value",)

    def __init__(self, value: T) -> None:
        """Initialize with a non-zero value.

        Args:
            value: A numeric value; must not be zero.

        Raises:
            ValueError: If ``value`` is zero.
        """
        if value == 0:
            raise ValueError("NonZero cannot be zero")
        self._value = value

    @classmethod
    def new(cls, value: T) -> NonZero[T]:  # type: ignore
        """Create a NonZero, raising ValueError if the value is zero.

        Args:
            value: The non-zero value to wrap.

        Returns:
            A new NonZero instance.

        Raises:
            ValueError: If ``value`` is zero.
        """
        return cls(value)

    @classmethod
    def try_new(cls, value: T) -> NonZero[T] | None:  # type: ignore
        """Create a NonZero, or return None if the value is zero.

        Args:
            value: The value to wrap.

        Returns:
            A new NonZero instance, or ``None`` if ``value`` is zero.
        """
        if value == 0:
            return None
        return cls(value)

    @classmethod
    def from_unsigned(cls, value: int) -> NonZero[int]:  # type: ignore
        """Create a NonZero from a positive integer.

        Args:
            value: A strictly positive integer.

        Returns:
            A New NonZero wrapping ``value``.

        Raises:
            ValueError: If ``value`` is not positive.
        """
        if value <= 0:
            raise ValueError("value must be positive")
        return cls(value)

    def get(self) -> T:
        """Return the inner non-zero value.

        Returns:
            The wrapped value.
        """
        return self._value

    def checked_add(self, other: int) -> NonZero[T] | None:  # type: ignore
        """Add and return a NonZero, or None if the result is zero.

        Args:
            other: The value to add.

        Returns:
            A NonZero with the sum, or ``None`` if the result is zero.
        """
        result = int(self._value) + other
        if result == 0:
            return None
        return NonZero(result)

    def checked_sub(self, other: int) -> NonZero[T] | None:  # type: ignore
        """Subtract and return a NonZero, or None if the result is zero.

        Args:
            other: The value to subtract.

        Returns:
            A NonZero with the difference, or ``None`` if the result is zero.
        """
        result = int(self._value) - other
        if result == 0:
            return None
        return NonZero(result)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, NonZero):
            return self._value == other._value
        return NotImplemented

    def __ne__(self, other: object) -> bool:
        if isinstance(other, NonZero):
            return self._value != other._value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)

    def __repr__(self) -> str:
        return f"NonZero({self._value})"


class SmallVec(Generic[T]):
    """Small-vector optimization: inline storage up to a limit, then the heap.

    Items are stored inline (in a small list) until ``stack_limit`` is reached,
    at which point further items spill into a separate heap list. This avoids
    allocation overhead for small vectors.

    Example:
        >>> from oxide import SmallVec
        >>> v = SmallVec([1, 2, 3])
        >>> v.push(4)
        >>> list(v)
        [1, 2, 3, 4]
    """

    __slots__ = ("_data", "_inline", "_stack_limit")

    def __init__(self, items: Iterable[T] | None = None, stack_limit: int = 8) -> None:
        """Initialize an optionally pre-filled SmallVec.

        Args:
            items: Optional iterable of initial items to push.
            stack_limit: Number of items to keep inline before spilling to the
                heap. Defaults to 8.
        """
        self._stack_limit = stack_limit
        self._inline: list[T] = []
        self._data: list[T] = []
        if items:
            for item in items:
                self.push(item)

    @classmethod
    def from_vec(cls, vec: list[T]) -> SmallVec[T]:
        """Create a SmallVec from a list.

        Args:
            vec: The list to copy into the new vector.

        Returns:
            A SmallVec containing the elements of ``vec``.
        """
        v = cls(stack_limit=8)
        for item in vec:
            v.push(item)
        return v

    def push(self, item: T) -> None:
        """Append an item to the end.

        Args:
            item: The value to append.
        """
        if len(self._inline) < self._stack_limit:
            self._inline.append(item)
        else:
            self._data.append(item)

    def pop(self) -> T | None:  # type: ignore
        """Remove and return the last item, or None if the vector is empty.

        Returns:
            The last item, or ``None`` if there are no items.
        """
        if self._data:
            return self._data.pop()
        if self._inline:
            return self._inline.pop()
        return None

    def len(self) -> int:  # type: ignore
        """Return the number of items.

        Returns:
            The count of items across inline and heap storage.
        """
        return len(self._inline) + len(self._data)

    def is_empty(self) -> bool:  # type: ignore
        """Return True if the vector has no items.

        Returns:
            Whether the vector contains zero items.
        """
        return self.len() == 0

    def capacity(self) -> int:  # type: ignore
        """Return the total capacity (inline + heap).

        Returns:
            ``stack_limit`` plus the number of allocted heap items.
        """
        return self._stack_limit + len(self._data)

    def clear(self) -> None:  # type: ignore
        """Remove all items."""
        self._inline.clear()
        self._data.clear()

    def swap_remove(self, index: int) -> T:  # type: ignore
        """Remove and return the item at ``index`` by swapping with the last.

        The element at ``index`` is swapped with the last element and the last
        is popped. Order of remaining elements is not preserved.

        Args:
            index: The position of the element to remove.

        Returns:
            The removed element.
        """
        if index < len(self._inline):
            last_idx = len(self._inline) - 1
            self._inline[index], self._inline[last_idx] = self._inline[last_idx], self._inline[index]
            return self._inline.pop()
        offset = len(self._inline)
        local_idx = index - offset
        last_idx = len(self._data) - 1
        self._data[local_idx], self._data[last_idx] = self._data[last_idx], self._data[local_idx]
        return self._data.pop()

    def retain(self, f: Callable[[T], bool]) -> None:  # type: ignore
        """Keep only items for which ``f`` returns True.

        Args:
            f: A predicate called with each item; items for which it returns
                False are removed.
        """
        self._inline = [x for x in self._inline if f(x)]
        self._data = [x for x in self._data if f(x)]

    def drain(self) -> Drain[T]:  # type: ignore
        """Remove all items and return an iterator over them.

        Returns:
            A :class:`Drain` iterator yielding the removed items in order.
        """
        items = self._inline + self._data
        self._inline.clear()
        self._data.clear()
        return Drain(items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._inline + self._data)

    def __getitem__(self, index: int) -> T:
        if index < len(self._inline):
            return self._inline[index]
        return self._data[index - len(self._inline)]

    def __setitem__(self, index: int, value: T) -> None:
        if index < len(self._inline):
            self._inline[index] = value
        else:
            self._data[index - len(self._inline)] = value

    def __len__(self) -> int:
        return self.len()

    def __bool__(self) -> bool:
        return not self.is_empty()

    def __repr__(self) -> str:
        return f"SmallVec({list(self)})"


class ArrayVec(Generic[T]):
    """A fixed-capacity vector backed by a list.

    Mirrors Rust's ``ArrayVec``. Items are appended up to a fixed maximum
    capacity; pushing beyond capacity raises :class:`OverflowError`.

    Example:
        >>> from oxide import ArrayVec
        >>> v = ArrayVec(2)
        >>> v.push(1)
        >>> v.push(2)
        >>> v.is_full()
        True
    """

    __slots__ = ("_data", "_capacity", "_len")

    def __init__(self, capacity: int) -> None:
        """Create an empty ArrayVec with a fixed capacity.

        Args:
            capacity: The maximum number of items the vector can hold.
        """
        self._capacity = capacity
        self._data: list[T] = []
        self._len = 0

    @classmethod
    def with_capacity(cls, capacity: int) -> ArrayVec[T]:  # type: ignore
        """Create an empty ArrayVec with a fixed capacity.

        Args:
            capacity: The maximum number of items the vector can hold.

        Returns:
            A new empty ArrayVec.
        """
        return cls(capacity)

    def push(self, item: T) -> None:
        """Append an item, raising OverflowError if at capacity.

        Args:
            item: The value to append.

        Raises:
            OverflowError: If the vector is already full.
        """
        if self._len >= self._capacity:
            raise OverflowError("ArrayVec is full")
        self._data.append(item)
        self._len += 1

    def pop(self) -> T | None:  # type: ignore
        """Remove and return the last item, or None if empty.

        Returns:
            The last item, or ``None`` if the vector is empty.
        """
        if self._len > 0:
            self._len -= 1
            return self._data.pop()
        return None

    def len(self) -> int:  # type: ignore
        """Return the number of items.

        Returns:
            The current item count.
        """
        return self._len

    def capacity(self) -> int:  # type: ignore
        """Return the maximum capacity.

        Returns:
            The fixed maximum number of items.
        """
        return self._capacity

    def is_empty(self) -> bool:  # type: ignore
        """Return True if the vector has no items.

        Returns:
            Whether the item count is zero.
        """
        return self._len == 0

    def is_full(self) -> bool:  # type: ignore
        """Return True if the vector is at capacity.

        Returns:
            Whether no more items can be pushed.
        """
        return self._len >= self._capacity

    def clear(self) -> None:  # type: ignore
        """Remove all items."""
        self._data.clear()
        self._len = 0

    def truncate(self, len: int) -> None:  # type: ignore
        """Shorten the vector to the given length.

        If ``len`` is greater than the current length, nothing is removed.

        Args:
            len: The desired new length.
        """
        if len < self._len:
            self._data = self._data[:len]
            self._len = len

    def as_slice(self) -> list[T]:  # type: ignore
        """Return a copy of the active portion as a list.

        Returns:
            A new list containing the current items.
        """
        return self._data[:self._len]

    def __iter__(self) -> Iterator[T]:
        return iter(self._data[:self._len])

    def __getitem__(self, index: int) -> T:
        return self._data[index]

    def __setitem__(self, index: int, value: T) -> None:
        self._data[index] = value

    def __len__(self) -> int:
        return self._len

    def __bool__(self) -> bool:
        return self._len > 0

    def __repr__(self) -> str:
        return f"ArrayVec({self._data[:self._len]})"


class TinyVec(Generic[T]):
    """Inline-up-to-limit vector that spills to the heap when full.

    Elements are stored in a small inline list until :attr:`INLINE_LIMIT` is
    reached, at which point the storage migrates to a heap list. Unlike
    :class:`SmallVec`, the inline region is emptied when spilling occurs.

    Example:
        >>> from oxide import TinyVec
        >>> v = TinyVec([1, 2])
        >>> v.push(3)
        >>> list(v)
        [1, 2, 3]
    """

    __slots__ = ("_inline", "_heap", "_is_inline")

    INLINE_LIMIT = 8

    def __init__(self, items: Iterable[T] | None = None) -> None:
        """Initialize an optionally pre-filled TinyVec.

        Args:
            items: Optional iterable of initial items to push.
        """
        self._inline: list[T] = []
        self._heap: list[T] = []
        self._is_inline = True
        if items:
            for item in items:
                self.push(item)

    def push(self, item: T) -> None:
        """Append an item, spilling to the heap if the inline limit is reached.

        Args:
            item: The value to append.
        """
        if self._is_inline and len(self._inline) < self.INLINE_LIMIT:
            self._inline.append(item)
        else:
            if self._is_inline:
                self._heap = self._inline[:]
                self._inline = []
                self._is_inline = False
            self._heap.append(item)

    def pop(self) -> T | None:  # type: ignore
        """Remove and return the last item, or None if empty.

        Returns:
            The last item, or ``None`` if there are no items.
        """
        if self._is_inline:
            if self._inline:
                return self._inline.pop()
            return None
        if self._heap:
            return self._heap.pop()
        return None

    def len(self) -> int:  # type: ignore
        """Return the number of items.

        Returns:
            The count of items across inline and heap storage.
        """
        return len(self._inline) + len(self._heap)

    def is_empty(self) -> bool:  # type: ignore
        """Return True if the vector has no items.

        Returns:
            Whether the vector contains zero items.
        """
        return self.len() == 0

    def clear(self) -> None:  # type: ignore
        """Remove all items and reset to inline mode."""
        self._inline.clear()
        self._heap.clear()
        self._is_inline = True

    def as_slice(self) -> list[T]:  # type: ignore
        """Return a copy of the active storage as a list.

        Returns:
            A new list of the current items.
        """
        if self._is_inline:
            return self._inline[:]
        return self._heap[:]

    def into_vec(self) -> list[T]:  # type: ignore
        """Return the underlying list, consuming the TinyVec.

        Returns:
            The raw backing list; the TinyVec should not be used afterward.
        """
        if self._is_inline:
            return self._inline
        return self._heap

    def retain(self, f: Callable[[T], bool]) -> None:  # type: ignore
        """Keep only items for which ``f`` returns True.

        Args:
            f: A predicate; items for which it returns False are removed.
        """
        if self._is_inline:
            self._inline = [x for x in self._inline if f(x)]
        else:
            self._heap = [x for x in self._heap if f(x)]

    def __iter__(self) -> Iterator[T]:
        if self._is_inline:
            return iter(self._inline)
        return iter(self._heap)

    def __getitem__(self, index: int) -> T:
        if self._is_inline:
            return self._inline[index]
        return self._heap[index]

    def __setitem__(self, index: int, value: T) -> None:
        if self._is_inline:
            self._inline[index] = value
        else:
            self._heap[index] = value

    def __len__(self) -> int:
        return self.len()

    def __bool__(self) -> bool:
        return not self.is_empty()

    def __repr__(self) -> str:
        return f"TinyVec({self.as_slice()})"


class BitVec:
    """A vector of boolean values packed for compact storage.

    Stores bits as a flat list of booleans with an explicit length counter for
    sparse pre-allocation. Supports bitwise-style operations like get/set/flip,
    counting, and byte packing.

    Example:
        >>> from oxide import BitVec
        >>> v = BitVec([True, False, True])
        >>> v.get(0)
        True
        >>> v.count_ones()
        2
    """

    __slots__ = ("_bits", "_len")

    def __init__(self, bits: Iterable[bool] | None = None) -> None:
        """Initialize a BitVec from an optional iterable of booleans.

        Args:
            bits: Optional iterable of boolean values to store.
        """
        self._bits: list[bool] = list(bits) if bits else []
        self._len = len(self._bits)

    @classmethod
    def with_capacity(cls, capacity: int) -> BitVec:  # type: ignore
        """Create an empty BitVec with pre-allocated capacity.

        Args:
            capacity: The number of bit slots to pre-allocate.

        Returns:
            An empty BitVec able to hold up to ``capacity`` bits.
        """
        v = cls()
        v._bits = [False] * capacity
        v._len = 0
        return v

    @classmethod
    def from_bytes(cls, data: bytes) -> BitVec:
        """Create a BitVec from raw bytes.

        Each byte contributes its 8 bits in little-endian bit order, i.e. bit
        ``i`` of byte ``n`` maps to position ``n * 8 + i``.

        Args:
            data: The bytes to expand into bits.

        Returns:
            A BitVec containing one boolean per bit of the input.

        Example:
            >>> from oxide import BitVec
            >>> v = BitVec.from_bytes(b"\\x05")
            >>> v.get(0), v.get(2)
            (True, True)
        """
        bits = []
        for byte in data:
            for i in range(8):
                bits.append(bool(byte & (1 << i)))
        return cls(bits)

    def push(self, bit: bool) -> None:
        """Append a single bit.

        Args:
            bit: The boolean value to append.
        """
        self._bits.append(bit)
        self._len += 1

    def pop(self) -> bool | None:  # type: ignore
        """Remove and return the last bit, or None if empty.

        Returns:
            The removed bit, or ``None`` if there are no bits.
        """
        if self._bits:
            self._len -= 1
            return self._bits.pop()
        return None

    def set(self, index: int, value: bool) -> None:  # type: ignore
        """Set the bit at the given index.

        Args:
            index: The position of the bit to modify.
            value: The new boolean value.
        """
        self._bits[index] = value

    def get(self, index: int) -> bool:  # type: ignore
        """Return the bit at the given index.

        Args:
            index: The position of the bit to read.

        Returns:
            The boolean value stored at ``index``.
        """
        return self._bits[index]

    def flip(self, index: int) -> None:  # type: ignore
        """Toggle the bit at the given index.

        Args:
            index: The position of the bit to invert.
        """
        self._bits[index] = not self._bits[index]

    def len(self) -> int:  # type: ignore
        """Return the number of bits.

        Returns:
            The count of active bits.
        """
        return self._len

    def is_empty(self) -> bool:  # type: ignore
        """Return True if the vector has no bits.

        Returns:
            Whether the bit count is zero.
        """
        return self._len == 0

    def capacity(self) -> int:  # type: ignore
        """Return the allocated capacity in bits.

        Returns:
            The number of bit slots in the underlying storage.
        """
        return len(self._bits)

    def clear(self) -> None:  # type: ignore
        """Remove all bits."""
        self._bits.clear()
        self._len = 0

    def count_ones(self) -> int:  # type: ignore
        """Count the number of set bits.

        Returns:
            The number of ``True`` bits.
        """
        return sum(1 for b in self._bits if b)

    def count_zeros(self) -> int:  # type: ignore
        """Count the number of unset bits.

        Returns:
            The number of ``False`` bits.
        """
        return sum(1 for b in self._bits if not b)

    def any(self) -> bool:  # type: ignore
        """Return True if any bit is set.

        Returns:
            Whether at least one bit is ``True``.
        """
        return any(self._bits)

    def all(self) -> bool:  # type: ignore
        """Return True if all active bits are set.

        Returns:
            Whether every active bit is ``True``.
        """
        return all(self._bits[:self._len])

    def to_bytes(self) -> bytes:  # type: ignore
        """Pack the bits into bytes in little-endian bit order.

        Returns:
            Each group of up to 8 bits packed into one byte, ordered from the
            least-significant bit of each byte.
        """
        result = bytearray()
        for i in range(0, self._len, 8):
            byte = 0
            for j in range(8):
                if i + j < self._len and self._bits[i + j]:
                    byte |= 1 << j
            result.append(byte)
        return bytes(result)

    def as_slice(self) -> list[bool]:  # type: ignore
        """Return the active bits as a list.

        Returns:
            A new list containing the current bits.
        """
        return self._bits[:self._len]

    def __iter__(self) -> Iterator[bool]:
        return iter(self._bits[:self._len])

    def __getitem__(self, index: int) -> bool:
        return self._bits[index]

    def __setitem__(self, index: int, value: bool) -> None:
        self._bits[index] = value

    def __len__(self) -> int:
        return self._len

    def __bool__(self) -> bool:
        return self._len > 0

    def __repr__(self) -> str:
        return f"BitVec({self._len} bits)"


class _FlagsMeta(type):
    """Metaclass that turns declared integers into flag values.

    Subclass ``BitFlags`` and declare each flag as an uppercase integer. At
    class creation those integers are replaced by instances of the class, so
    ``READ | WRITE`` yields a flags value rather than a bare int, and every
    flag method works on every flag.
    """

    def __new__(mcs, name: str, bases: Any, namespace: dict[str, Any], **kwargs: Any) -> Any:
        if name != "BitFlags" and "__slots__" not in namespace:
            namespace["__slots__"] = ()
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        declared: dict[str, int] = {
            key: value
            for key, value in namespace.items()
            if isinstance(value, int) and not key.startswith("_") and key.isupper()
        }
        cls._flags = declared  # type: ignore[attr-defined]
        for key, value in declared.items():
            setattr(cls, key, cls(value))  # type: ignore[attr-defined]
        return cls


def _flag_union(values: Iterable[int]) -> int:
    """OR every value together, returning 0 for no values."""
    out = 0
    for value in values:
        out |= value
    return out


class BitFlags(metaclass=_FlagsMeta):
    """A set of named bit flags, as Rust's ``bitflags`` crate provides.

    Declare flags as uppercase integers on a subclass; each declaration
    becomes a value of that subclass, so flag arithmetic and every flag
    method use the same type.

    Examples:
        >>> from oxide import BitFlags
        >>> class Perms(BitFlags):
        ...     READ = 0b001
        ...     WRITE = 0b010
        ...     EXEC = 0b100
        >>> Perms.READ.bits()
        1
        >>> (Perms.READ | Perms.WRITE).contains(Perms.READ)
        True
        >>> Perms.all().iter()
        ['READ', 'WRITE', 'EXEC']
        >>> Perms.READ | Perms.WRITE
        Perms(READ | WRITE)
    """

    __slots__ = ("_bits",)

    _flags: dict[str, int] = {}

    def __init__(self, bits: int = 0) -> None:
        """Create a flags value from a raw bitmask.

        Args:
            bits: The initial bit pattern.
        """
        self._bits = int(bits)

    @staticmethod
    def _to_bits(value: Any) -> int:
        """Coerce a flags value or an int to a raw mask."""
        if isinstance(value, BitFlags):
            return value._bits
        return int(value)

    @classmethod
    def declared(cls) -> dict[str, int]:
        """Return the declared flag names mapped to their bit patterns.

        Returns:
            dict[str, int]: Flag name to bit value, in declaration order.

        Examples:
            >>> class Perms(BitFlags):
            ...     READ = 1
            ...     WRITE = 2
            >>> Perms.declared()
            {'READ': 1, 'WRITE': 2}
        """
        return dict(cls._flags)

    @classmethod
    def all(cls) -> BitFlags:
        """Return a value with every declared flag set.

        Returns:
            BitFlags: The union of all declared flags.

        Examples:
            >>> class Perms(BitFlags):
            ...     READ = 1
            ...     WRITE = 2
            >>> Perms.all().bits()
            3
        """
        return cls(_flag_union(cls._flags.values()))

    @classmethod
    def from_bits(cls, bits: int) -> BitFlags:
        """Create a value from raw bits, retaining undeclared bits too.

        Args:
            bits (int): The raw pattern.

        Returns:
            BitFlags: The corresponding value.

        Examples:
            >>> class Perms(BitFlags):
            ...     READ = 1
            ...     WRITE = 2
            >>> Perms.from_bits(0b101).bits()
            5
        """
        return cls(bits)

    # --- inspection -------------------------------------------------------

    def bits(self) -> int:
        """Return the raw bitmask.

        Returns:
            int: The integer backing this value.

        Examples:
            >>> class Perms(BitFlags):
            ...     READ = 1
            ...     WRITE = 2
            >>> (Perms.READ | Perms.WRITE).bits()
            3
        """
        return self._bits

    def contains(self, other: Any) -> bool:
        """Return True if every bit of ``other`` is set here.

        Args:
            other: Another flags value or an int.

        Returns:
            bool: True if this value contains all of ``other``'s bits.

        Examples:
            >>> class Perms(BitFlags):
            ...     READ = 1
            ...     WRITE = 2
            >>> (Perms.READ | Perms.WRITE).contains(Perms.READ)
            True
            >>> Perms.READ.contains(Perms.WRITE)
            False
        """
        other_bits = self._to_bits(other)
        return (self._bits & other_bits) == other_bits

    def intersects(self, other: Any) -> bool:
        """Return True if any bit of ``other`` is set here.

        Args:
            other: Another flags value or an int.

        Returns:
            bool: True if the two values share at least one bit.

        Examples:
            >>> class Perms(BitFlags):
            ...     READ = 1
            ...     WRITE = 2
            >>> Perms.READ.intersects(Perms.WRITE)
            False
            >>> (Perms.READ | Perms.WRITE).intersects(Perms.WRITE)
            True
        """
        return (self._bits & self._to_bits(other)) != 0

    def is_empty(self) -> bool:
        """Return True if no bits are set.

        Returns:
            bool: True if the value is zero.

        Examples:
            >>> class Perms(BitFlags):
            ...     READ = 1
            >>> Perms(0).is_empty()
            True
        """
        return self._bits == 0

    def is_all(self) -> bool:
        """Return True if every declared flag is set.

        Returns:
            bool: True if this equals ``type(self).all()``.

        Examples:
            >>> class Perms(BitFlags):
            ...     READ = 1
            ...     WRITE = 2
            >>> Perms.all().is_all()
            True
            >>> Perms.READ.is_all()
            False
        """
        return self._bits == _flag_union(type(self)._flags.values())

    def count_ones(self) -> int:
        """Return the number of set bits.

        Returns:
            int: How many bits are on.

        Examples:
            >>> class Perms(BitFlags):
            ...     READ = 1
            ...     WRITE = 2
            ...     EXEC = 4
            >>> (Perms.READ | Perms.EXEC).count_ones()
            2
        """
        return bin(self._bits).count("1")

    # --- mutation ---------------------------------------------------------

    def insert(self, other: Any) -> None:
        """Set the bits of ``other`` in place.

        Args:
            other: The flags value or int to add.

        Examples:
            >>> class Perms(BitFlags):
            ...     READ = 1
            ...     WRITE = 2
            >>> p = Perms.READ
            >>> p.insert(Perms.WRITE)
            >>> p.bits()
            3
        """
        self._bits |= self._to_bits(other)

    def remove(self, other: Any) -> None:
        """Clear the bits of ``other`` in place.

        Args:
            other: The flags value or int to clear.

        Examples:
            >>> class Perms(BitFlags):
            ...     READ = 1
            ...     WRITE = 2
            >>> p = Perms.READ | Perms.WRITE
            >>> p.remove(Perms.WRITE)
            >>> p.bits()
            1
        """
        self._bits &= ~self._to_bits(other)

    def toggle(self, other: Any) -> None:
        """Flip the bits of ``other`` in place.

        Args:
            other: The flags value or int to flip.

        Examples:
            >>> class Perms(BitFlags):
            ...     READ = 1
            ...     WRITE = 2
            >>> p = Perms.READ
            >>> p.toggle(Perms.READ | Perms.WRITE)
            >>> p.bits()
            2
        """
        self._bits ^= self._to_bits(other)

    def set(self, other: Any, on: bool) -> None:
        """Set or clear the bits of ``other`` in place.

        Args:
            other: The flags value or int to change.
            on: True to set the bits, False to clear them.

        Examples:
            >>> class Perms(BitFlags):
            ...     READ = 1
            ...     WRITE = 2
            >>> p = Perms(0)
            >>> p.set(Perms.WRITE, True)
            >>> p.bits()
            2
            >>> p.set(Perms.WRITE, False)
            >>> p.bits()
            0
        """
        if on:
            self._bits |= self._to_bits(other)
        else:
            self._bits &= ~self._to_bits(other)

    # --- pure -------------------------------------------------------------

    def union(self, other: Any) -> BitFlags:
        """Return a value with the bits of both.

        Args:
            other: The flags value or int to combine with.

        Returns:
            BitFlags: The new value.

        Examples:
            >>> class Perms(BitFlags):
            ...     READ = 1
            ...     WRITE = 2
            >>> Perms.READ.union(Perms.WRITE).bits()
            3
        """
        return type(self)(self._bits | self._to_bits(other))

    def intersection(self, other: Any) -> BitFlags:
        """Return a value with only the bits both share.

        Args:
            other: The flags value or int to intersect with.

        Returns:
            BitFlags: The new value.

        Examples:
            >>> class Perms(BitFlags):
            ...     READ = 1
            ...     WRITE = 2
            >>> (Perms.READ | Perms.WRITE).intersection(Perms.READ).bits()
            1
        """
        return type(self)(self._bits & self._to_bits(other))

    def difference(self, other: Any) -> BitFlags:
        """Return a value with ``other``'s bits cleared.

        Args:
            other: The flags value or int to subtract.

        Returns:
            BitFlags: The new value.

        Examples:
            >>> class Perms(BitFlags):
            ...     READ = 1
            ...     WRITE = 2
            >>> (Perms.READ | Perms.WRITE).difference(Perms.WRITE).bits()
            1
        """
        return type(self)(self._bits & ~self._to_bits(other))

    def symmetric_difference(self, other: Any) -> BitFlags:
        """Return a value with bits set in exactly one side.

        Args:
            other: The flags value or int to compare with.

        Returns:
            BitFlags: The new value.

        Examples:
            >>> class Perms(BitFlags):
            ...     READ = 1
            ...     WRITE = 2
            >>> Perms.READ.symmetric_difference(Perms.WRITE).bits()
            3
        """
        return type(self)(self._bits ^ self._to_bits(other))

    # --- iteration --------------------------------------------------------

    def iter(self) -> list[str]:
        """Return the names of the flags that are set.

        Returns:
            list[str]: Names in declaration order. Bits with no matching
                declaration are shown in binary form.

        Examples:
            >>> class Perms(BitFlags):
            ...     READ = 0b001
            ...     WRITE = 0b010
            >>> (Perms.READ | Perms.WRITE).iter()
            ['READ', 'WRITE']
            >>> Perms(0).iter()
            []
        """
        declared = type(self)._flags
        named = [name for name, value in declared.items() if value and (self._bits & value) == value]
        remaining = self._bits
        for value in declared.values():
            remaining &= ~value
        if remaining:
            named.append(bin(remaining))
        return named

    # --- operators --------------------------------------------------------

    def __or__(self, other: Any) -> BitFlags:
        return type(self)(self._bits | self._to_bits(other))

    def __and__(self, other: Any) -> BitFlags:
        return type(self)(self._bits & self._to_bits(other))

    def __xor__(self, other: Any) -> BitFlags:
        return type(self)(self._bits ^ self._to_bits(other))

    def __invert__(self) -> BitFlags:
        """Return the complement, limited to the declared flag bits."""
        return type(self)(~self._bits & _flag_union(type(self)._flags.values()))

    def __ior__(self, other: Any) -> BitFlags:
        self.insert(other)
        return self

    def __iand__(self, other: Any) -> BitFlags:
        self._bits &= self._to_bits(other)
        return self

    def __ixor__(self, other: Any) -> BitFlags:
        self.toggle(other)
        return self

    def __contains__(self, other: Any) -> bool:
        return self.contains(other)

    def __bool__(self) -> bool:
        return self._bits != 0

    def __eq__(self, other: object) -> bool:
        if isinstance(other, BitFlags):
            return self._bits == other._bits
        if isinstance(other, int):
            return self._bits == other
        return NotImplemented

    def __ne__(self, other: object) -> bool:
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self) -> int:
        return hash((type(self).__name__, self._bits))

    def __iter__(self) -> Iterator[str]:
        return iter(self.iter())

    def __repr__(self) -> str:
        names = self.iter()
        if not names:
            return f"{type(self).__name__}()"
        return f"{type(self).__name__}({' | '.join(names)})"

    def __str__(self) -> str:
        return self.__repr__()


@dataclass(frozen=True)
class CreateMeta:
    """Metadata describing a library's creation and configuration.

    A frozen data class capturing build and packaging metadata such as name,
    version, author, license, and keywords.

    Example:
        >>> meta = CreateMeta(
        ...     libname="my-lib", libversion=(1, 0), pyversion=(3, 10),
        ...     author="A", clone="", description="", license="MIT",
        ...     homepage="", keywords=(), python_requires=">=3.10",
        ...     timestamp="2026-01-01",
        ... )
        >>> meta.unwrap()
        'my-lib'
    """

    libname: str
    libversion: tuple[int, int]
    pyversion: tuple[int, int]
    author: str
    clone: str
    description: str
    license: str
    homepage: str
    keywords: tuple[str, ...]
    python_requires: str
    timestamp: str

    def unwrap(self) -> str:
        """Return the library name.

        Returns:
            The ``libname`` field.
        """
        return self.libname
