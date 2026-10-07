"""Option type — Some(value) or None_ for explicit null handling.

Provides Option, Some, None_ for explicit null handling without None confusion.
Every Option is either Some(value) or None_, forcing callers to handle both cases.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, NoReturn, TypeVar


T = TypeVar("T")
U = TypeVar("U")


class Option(Generic[T]):
    """A container for an optional value that is either Some(value) or None_.

    Every Option is exactly one of two variants: a ``Some`` holding a value of
    type ``T``, or a ``None_`` holding nothing. Because callers must explicitly
    handle both cases, this avoids the ambiguity of Python's ``None`` while
    still composing with ``map``, ``and_then``, and chained ``or_``/``and_``.

    Example:
        >>> x: Option[int] = Some(5)
        >>> x.map(lambda v: v * 2).unwrap()
        10
        >>> None_.unwrap_or(0)
        0
    """

    def is_some(self) -> bool:
        """Return True if this Option holds a Some value.

        Returns:
            bool: True if this Option is a ``Some`` variant, else False.
        """
        return isinstance(self, Some)

    def is_none(self) -> bool:
        """Return True if this Option is the None_ variant.

        Returns:
            bool: True if this Option is a ``None_`` variant, else False.
        """
        return isinstance(self, NoneOption)

    def unwrap(self) -> T:
        """Return the inner value of a Some, or raise if this is None_.

        Returns:
            T: The value held by this Option when it is ``Some``.

        Raises:
            RuntimeError: If this Option is ``None_``.
        """
        if isinstance(self, Some):
            return self.value
        raise RuntimeError(
            "called `Option.unwrap()` on a `None` value"
        )

    def expect(self, message: str) -> T:
        """Return the inner value of a Some, using a custom failure message.

        Args:
            message (str): The message to attach to the error if this is None_.

        Returns:
            T: The value held by this Option when it is ``Some``.

        Raises:
            RuntimeError: If this Option is ``None_``, carrying ``message``.
        """
        if isinstance(self, Some):
            return self.value
        raise RuntimeError(message)

    def unwrap_or(self, default: T) -> T:
        """Return the inner value, or a fallback default if this is None_.

        Args:
            default (T): The value to return when there is no inner value.

        Returns:
            T: The held value if this is ``Some``, otherwise ``default``.

        Example:
            >>> None_.unwrap_or("fallback")
            'fallback'
        """
        if isinstance(self, Some):
            return self.value
        return default

    def unwrap_or_else(
        self,
        fn: Callable[[], T],
    ) -> T:
        """Return the inner value, or lazily compute a default if None_.

        The fallback is only evaluated when this Option is ``None_``.

        Args:
            fn (Callable[[], T]): Zero-argument callable producing the default.

        Returns:
            T: The held value if this is ``Some``, otherwise ``fn()``.
        """
        if isinstance(self, Some):
            return self.value
        return fn()

    def map(
        self,
        fn: Callable[[T], U],
    ) -> Option[U]:
        """Transform the inner value of a Some, leaving None_ unchanged.

        Args:
            fn (Callable[[T], U]): Function applied to the inner value.

        Returns:
            Option[U]: A ``Some(fn(value))`` if this is ``Some``, else ``None_``.

        Example:
            >>> Some(2).map(lambda v: v * 3)
            Some(6)
        """
        if isinstance(self, Some):
            return Some(fn(self.value))
        return None_

    def map_or(
        self,
        default: U,
        fn: Callable[[T], U],
    ) -> U:
        """Apply a function to the inner value, or return a default if None_.

        Args:
            default (U): Value returned when this Option is ``None_``.
            fn (Callable[[T], U]): Function applied to the inner value.

        Returns:
            U: ``fn(value)`` if this is ``Some``, otherwise ``default``.
        """
        if isinstance(self, Some):
            return fn(self.value)
        return default

    def map_or_else(
        self,
        default: Callable[[], U],
        fn: Callable[[T], U],
    ) -> U:
        """Apply a function to the inner value, or compute a default if None_.

        Args:
            default (Callable[[], U]): Zero-argument callable for the fallback.
            fn (Callable[[T], U]): Function applied to the inner value.

        Returns:
            U: ``fn(value)`` if this is ``Some``, otherwise ``default()``.
        """
        if isinstance(self, Some):
            return fn(self.value)
        return default()

    def and_(
        self,
        other: Option[U],
    ) -> Option[U]:
        """Return ``other`` if this is Some, otherwise return None_.

        Args:
            other (Option[U]): The Option to return when this is ``Some``.

        Returns:
            Option[U]: ``other`` if this is ``Some``, else ``None_``.
        """
        if isinstance(self, Some):
            return other
        return None_

    def and_then(
        self,
        fn: Callable[[T], Option[U]],
    ) -> Option[U]:
        """Chain a function that returns an Option from the inner value.

        Args:
            fn (Callable[[T], Option[U]]): Function that returns an Option.

        Returns:
            Option[U]: ``fn(value)`` if this is ``Some``, else ``None_``.

        Example:
            >>> Some(2).and_then(lambda v: Some(v + 1))
            Some(3)
        """
        if isinstance(self, Some):
            return fn(self.value)
        return None_

    def or_(
        self,
        other: Option[T],
    ) -> Option[T]:
        """Return self if Some, otherwise return the other Option.

        Args:
            other (Option[T]): Fallback Option used when this is ``None_``.

        Returns:
            Option[T]: This Option if it is ``Some``, else ``other``.
        """
        if isinstance(self, Some):
            return self
        return other

    def or_else(
        self,
        fn: Callable[[], Option[T]],
    ) -> Option[T]:
        """Return self if Some, or compute a fallback Option if None_.

        Args:
            fn (Callable[[], Option[T]]): Callable producing the fallback.

        Returns:
            Option[T]: This Option if it is ``Some``, else ``fn()``.
        """
        if isinstance(self, Some):
            return self
        return fn()

    def filter(
        self,
        predicate: Callable[[T], bool],
    ) -> Option[T]:
        """Retain self only if Some and the predicate holds, else None_.

        Args:
            predicate (Callable[[T], bool]): Test applied to the inner value.

        Returns:
            Option[T]: This Option if the predicate matches, else ``None_``.
        """
        if isinstance(self, Some):
            if predicate(self.value):
                return self
        return None_

    def is_some_and(self, predicate: Callable[[T], bool]) -> bool:
        """Return true if the option is Some and the predicate returns true.

        Args:
            predicate: Function to test the inner value.

        Returns:
            bool: True if Some and predicate matches.

        Example:
            >>> Some(2).is_some_and(lambda x: x % 2 == 0)
            True
            >>> Some(3).is_some_and(lambda x: x % 2 == 0)
            False
            >>> None_.is_some_and(lambda x: True)
            False
        """
        if isinstance(self, Some):
            return predicate(self.value)
        return False

    def is_none_or(self, predicate: Callable[[T], bool]) -> bool:
        """Return true if the option is None or the predicate returns true.

        Args:
            predicate: Function to test the inner value.

        Returns:
            bool: True if None or predicate matches.

        Example:
            >>> Some(2).is_none_or(lambda x: x % 2 == 0)
            True
            >>> Some(3).is_none_or(lambda x: x % 2 == 0)
            False
            >>> None_.is_none_or(lambda x: False)
            True
        """
        if type(self) is type(None_):
            return True
        if isinstance(self, Some):
            return predicate(self.value)
        return False

    def inspect(
        self,
        fn: Callable[[T], Any],
    ) -> Option[T]:
        """Apply a side-effecting function to the inner value without changing it.

        Args:
            fn (Callable[[T], Any]): Function whose result is discarded.

        Returns:
            Option[T]: This same Option, unchanged.

        Example:
            >>> Some(1).inspect(print).is_some()
            1
            True
        """
        if isinstance(self, Some):
            fn(self.value)
        return self

    def expect(self, message: str) -> T:
        """Return the contained value or panic with given message.

        Args:
            message: The message to use if None.

        Returns:
            T: The contained value.

        Raises:
            RuntimeError: If the option is None.
        """
        if isinstance(self, Some):
            return self.value
        raise RuntimeError(message)

    def expect_err(self, message: str) -> None:
        """Unwrap None, panicking if the value is Some.

        Args:
            message: The message to use if Some.

        Raises:
            RuntimeError: If the option is Some.
        """
        if type(self) is type(None_):
            return None
        if isinstance(self, Some):
            raise RuntimeError(message)
        return None

    def __bool__(self) -> bool:
        """Return True if this Option holds a Some value.

        Returns:
            bool: True for ``Some``, False for ``None_``.
        """
        return self.is_some()

    def __iter__(self):
        """Yield the inner value if Some, yielding nothing if None_.

        Yields:
            T: The held value when this Option is ``Some``.
        """
        if isinstance(self, Some):
            yield self.value

    def __repr__(self) -> str:
        """Return a stable string representation of this Option.

        Returns:
            str: ``Some(value)`` for ``Some``, or ``None_`` for the empty
            variant. The trailing underscore distinguishes it from the
            ``None`` singleton.
        """
        if isinstance(self, Some):
            return f"Some({self.value!r})"
        return "None_"


@dataclass(frozen=True, repr=False)
class Some(Option[T]):
    """The Some variant of Option, holding a concrete value.

    Construct with ``Some(value)`` to represent a present value. It is
    immutable, hashable, and compares equal to other Some instances with the
    same value.

    Example:
        >>> Some(42).unwrap()
        42
    """
    value: T


class NoneOption(Option[NoReturn]):
    """The singleton None_ variant of Option, representing an absent value.

    This class should not be instantiated directly; use the module-level
    ``None_`` (and its alias ``none``) singleton instead. It is an Option but
    carries no value.

    Example:
        >>> None_.is_none()
        True
    """
    __slots__ = ()
    _instance: NoneOption | None = None

    def __new__(cls) -> NoneOption:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

None_ = NoneOption()
none = None_
