"""Result type — Ok(value) or Err(error) with ? propagation via propagate/ask.

Provides Result, Ok, Err for explicit error handling. Supports the ? operator
via propagate/ask for clean error propagation through call chains.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, NoReturn, TypeVar

from .option import Option, Some, None_


T = TypeVar("T")
E = TypeVar("E", bound=BaseException)
U = TypeVar("U")
F = TypeVar("F", bound=Callable[..., Any])


class Result(Generic[T, E]):
    """A container for either a success value or a failure error.

    A ``Result`` is exactly one of two variants: ``Ok(value)`` wrapping the
    success value of type ``T``, or ``Err(error)`` wrapping a failure of type
    ``E`` (by default a ``BaseException``). Every operation forces the caller
    to handle both outcomes, providing explicit, composable error handling.

    Example:
        >>> def div(a: int, b: int) -> Result[int, str]:
        ...     return Ok(a // b) if b else Err("division by zero")
        >>> div(10, 2).unwrap()
        5
        >>> div(1, 0).unwrap_or(-1)
        -1
    """

    def is_ok(self) -> bool:
        """Return True if this Result is an Ok variant.

        Returns:
            bool: True if this Result is ``Ok``, else False.
        """
        return isinstance(self, Ok)

    def is_err(self) -> bool:
        """Return True if this Result is an Err variant.

        Returns:
            bool: True if this Result is ``Err``, else False.
        """
        return isinstance(self, Err)

    def unwrap(self) -> T:
        """Return the Ok value, or raise if this Result is Err.

        Returns:
            T: The value wrapped by this Result when it is ``Ok``.

        Raises:
            RuntimeError: If this Result is ``Err``.
        """
        if isinstance(self, Ok):
            return self.value

        raise RuntimeError(
            "called `Result.unwrap()` on an `Err` value: "
            f"{self.error!r}"
        )

    def expect(self, message: str) -> T:
        """Return the Ok value, using a custom message if this is Err.

        Args:
            message (str): Message included in the raised error.

        Returns:
            T: The value wrapped by this Result when it is ``Ok``.

        Raises:
            RuntimeError: If this Result is ``Err``, carrying ``message``.
        """
        if isinstance(self, Ok):
            return self.value
        raise RuntimeError(
            f"{message}: {self.error!r}"
        )

    def unwrap_err(self) -> E:
        """Return the Err value, or raise if this Result is Ok.

        Returns:
            E: The error wrapped by this Result when it is ``Err``.

        Raises:
            RuntimeError: If this Result is ``Ok``.
        """
        if isinstance(self, Err):
            return self.error
        raise RuntimeError(
            "called `Result.unwrap_err()` on an `Ok` value: "
            f"{self.value!r}"
        )

    def expect_err(self, message: str) -> E:
        """Return the Err value, using a custom message if this is Ok.

        Args:
            message (str): Message included in the raised error.

        Returns:
            E: The error wrapped by this Result when it is ``Err``.

        Raises:
            RuntimeError: If this Result is ``Ok``, carrying ``message``.
        """
        if isinstance(self, Err):
            return self.error
        raise RuntimeError(
            f"{message}: {self.value!r}"
        )

    def unwrap_or(self, default: T) -> T:
        """Return the Ok value, or a fallback default if this is Err.

        Args:
            default (T): Value returned when this Result is ``Err``.

        Returns:
            T: The Ok value if present, otherwise ``default``.
        """
        if isinstance(self, Ok):
            return self.value
        return default

    def unwrap_or_else(
        self,
        fn: Callable[[E], T],
    ) -> T:
        """Return the Ok value, or compute a default from the error if Err.

        Args:
            fn (Callable[[E], T]): Callable producing a fallback from the error.

        Returns:
            T: The Ok value if present, otherwise ``fn(self.error)``.
        """
        if isinstance(self, Ok):
            return self.value
        return fn(self.error)

    def map(
        self,
        fn: Callable[[T], U],
    ) -> Result[U, E]:
        """Transform the Ok value, leaving an Err unchanged.

        Args:
            fn (Callable[[T], U]): Function applied to the Ok value.

        Returns:
            Result[U, E]: ``Ok(fn(value))`` if this is ``Ok``, else this ``Err``.

        Example:
            >>> Ok(2).map(lambda v: v * 10)
            Ok(value=20)
        """
        if isinstance(self, Ok):
            return Ok(fn(self.value))
        return self

    def map_err(
        self,
        fn: Callable[[E], U],
    ) -> Result[T, U]:
        """Transform the Err value, leaving an Ok unchanged.

        Args:
            fn (Callable[[E], U]): Function applied to the Err value.

        Returns:
            Result[T, U]: ``Err(fn(error))`` if this is ``Err``, else this ``Ok``.
        """
        if isinstance(self, Err):
            return Err(fn(self.error))
        return self

    def map_or(
        self,
        default: U,
        fn: Callable[[T], U],
    ) -> U:
        """Apply a function to the Ok value, or return a default if Err.

        Args:
            default (U): Value returned when this Result is ``Err``.
            fn (Callable[[T], U]): Function applied to the Ok value.

        Returns:
            U: ``fn(value)`` if this is ``Ok``, otherwise ``default``.
        """
        if isinstance(self, Ok):
            return fn(self.value)
        return default

    def map_or_else(
        self,
        default: Callable[[E], U],
        fn: Callable[[T], U],
    ) -> U:
        """Apply a function to the Ok value, or compute a default from the error.

        Args:
            default (Callable[[E], U]): Callable producing a fallback.
            fn (Callable[[T], U]): Function applied to the Ok value.

        Returns:
            U: ``fn(value)`` if this is ``Ok``, otherwise ``default(self.error)``.
        """
        if isinstance(self, Ok):
            return fn(self.value)
        return default(self.error)

    def and_(
        self,
        other: Result[U, E],
    ) -> Result[U, E]:
        """Return ``other`` if this is Ok, otherwise return this Err.

        Args:
            other (Result[U, E]): The Result to return when this is ``Ok``.

        Returns:
            Result[U, E]: ``other`` if this is ``Ok``, else this ``Err``.
        """
        if isinstance(self, Ok):
            return other
        return self

    def and_then(
        self,
        fn: Callable[[T], Result[U, E]],
    ) -> Result[U, E]:
        """Chain a function that returns a Result from the Ok value.

        Args:
            fn (Callable[[T], Result[U, E]]): Function returning a Result.

        Returns:
            Result[U, E]: ``fn(value)`` if this is ``Ok``, else this ``Err``.

        Example:
            >>> Ok(2).and_then(lambda v: Ok(v + 1))
            Ok(value=3)
        """
        if isinstance(self, Ok):
            return fn(self.value)
        return self

    def or_(
        self,
        other: Result[T, U],
    ) -> Result[T, U]:
        """Return self if Ok, otherwise return the other Result.

        Args:
            other (Result[T, U]): Fallback Result used when this is ``Err``.

        Returns:
            Result[T, U]: This Result if it is ``Ok``, else ``other``.
        """
        if isinstance(self, Ok):
            return self
        return other

    def or_else(
        self,
        fn: Callable[[E], Result[T, U]],
    ) -> Result[T, U]:
        """Return self if Ok, or compute a fallback Result from the error.

        Args:
            fn (Callable[[E], Result[T, U]]): Callable producing a fallback.

        Returns:
            Result[T, U]: This Result if it is ``Ok``, else ``fn(self.error)``.
        """
        if isinstance(self, Err):
            return fn(self.error)
        return self

    def ok(self) -> Option[T]:
        """Convert this Result into an Option holding the Ok value.

        Returns:
            Option[T]: ``Some(value)`` if this is ``Ok``, else ``None_``.

        Example:
            >>> Ok(7).ok()
            Some(7)
        """
        if isinstance(self, Ok):
            return Some(self.value)
        return None_

    def err(self) -> Option[E]:
        """Convert this Result into an Option holding the Err value.

        Returns:
            Option[E]: ``Some(error)`` if this is ``Err``, else ``None_``.
        """
        if isinstance(self, Err):
            return Some(self.error)
        return None_

    def inspect(
        self,
        fn: Callable[[T], Any],
    ) -> Result[T, E]:
        """Apply a side-effecting function to the Ok value without changing it.

        Args:
            fn (Callable[[T], Any]): Function whose result is discarded.

        Returns:
            Result[T, E]: This same Result, unchanged.

        Example:
            >>> Ok(1).inspect(print).is_ok()
            1
            True
        """
        if isinstance(self, Ok):
            fn(self.value)
        return self

    def inspect_err(
        self,
        fn: Callable[[E], Any],
    ) -> Result[T, E]:
        """Apply a side-effecting function to the Err value without changing it.

        Args:
            fn (Callable[[E], Any]): Function whose result is discarded.

        Returns:
            Result[T, E]: This same Result, unchanged.
        """
        if isinstance(self, Err):
            fn(self.error)
        return self

    def __bool__(self) -> bool:
        """Return True if this Result is an Ok variant.

        Returns:
            bool: True for ``Ok``, False for ``Err``.
        """
        return self.is_ok()

    def __repr__(self) -> str:
        """Return a stable string representation of this Result.

        Returns:
            str: ``Ok(value)`` for ``Ok``, or ``Err(error)`` for ``Err``.
        """
        if isinstance(self, Ok):
            return f"Ok({self.value!r})"
        return f"Err({self.error!r})"


@dataclass(frozen=True)
class Ok(Result[T, NoReturn]):
    """The Ok variant of Result, holding a success value.

    Construct with ``Ok(value)`` to represent a successful outcome. The inner
    value is immutable, hashable, and compared by structural equality.

    Example:
        >>> Ok("done").is_ok()
        True
    """
    value: T

@dataclass(frozen=True)
class Err(Result[NoReturn, E]):
    """The Err variant of Result, holding a failure error.

    Construct with ``Err(error)`` to represent a failure. The inner error is
    immutable, hashable, and compared by structural equality.

    Example:
        >>> Err("boom").is_err()
        True
    """
    error: E


class PropagateError(Exception):
    """Internal exception carrying a Result for ?-like error propagation.

    This is not meant to be caught directly by user code; it is used
    internally by ``propagate``/``ask`` to short-circuit error handling.
    """

    __slots__ = ("_result",)

    def __init__(self, result: Result) -> None:
        self._result = result

    @property
    def result(self) -> Result:
        """Return the Result carried by this propagation error.

        Returns:
            Result: The Result that triggered propagation.
        """
        return self._result


class Propagate:
    """Descriptor that wraps a function to automatically propagate Result errors.

    When a wrapped function calls ``ask()`` and the ask unwraps to an ``Err``,
    a ``PropagateError`` is raised, caught by this descriptor, and returned as a
    plain ``Result`` from the decorated call. This emulates Rust's ``?``.

    Example:
        >>> @propagate
        ... def inner() -> int:
        ...     return ask(Ok(1))
        >>> inner()
        1
    """

    __slots__ = ("_fn",)

    def __init__(self, fn: F) -> None:
        """Wrap a callable so that ask() propagates Result errors as results.

        Args:
            fn (F): The callable to wrap.
        """
        self._fn = fn

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Invoke the wrapped function, returning Err instead of raising.

        Returns:
            Any: The function's return value, or the propagated Err Result.
        """
        try:
            return self._fn(*args, **kwargs)
        except PropagateError as e:
            return e.result

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        """Support descriptor access, binding the instance when called on an object.

        Returns:
            Any: This descriptor when accessed on the class, or a bound
            Propagate wrapping ``fn`` when accessed through an instance.
        """
        if obj is None:
            return self
        return Propagate(lambda *a, **kw: self._fn(obj, *a, **kw))


def propagate(fn: F) -> F:
    """Decorator enabling ?-like error propagation via ask() inside fn.

    Wrap a function so that any ``ask()`` that reaches an ``Err`` returns that
    Err as the function's result instead of raising.

    Args:
        fn (F): The callable to wrap.

    Returns:
        F: A wrapped callable that propagates Result errors.

    Example:
        >>> @propagate
        ... def f() -> int:
        ...     return ask(Ok(5))
        >>> f()
        5
    """
    return Propagate(fn)  # type: ignore[return-value]


def ask(result: Result) -> Any:
    """Unwrap a Result or raise PropagateError to propagate the error.

    Returns the value of an ``Ok``, or raises a ``PropagateError`` carrying the
    ``Err`` so an enclosing ``@propagate`` function can return it as its result.

    Args:
        result (Result): The Result to unwrap.

    Returns:
        Any: The value if ``result`` is ``Ok``.

    Raises:
        PropagateError: If ``result`` is ``Err`` (propagates to the caller).

    Example:
        >>> asked = ask(Ok("hello"))
        >>> asked
        'hello'
    """
    if isinstance(result, Err):
        raise PropagateError(result)
    return result.value


def try_ask(fn: F) -> F:
    """Decorator that wraps a function to return Ok/Err instead of raising.

    The wrapped function runs normally; a successful return becomes ``Ok(value)``
    and any raised exception becomes ``Err(exception)``.

    Args:
        fn (F): The callable to wrap.

    Returns:
        F: A wrapped callable returning a Result.

    Example:
        >>> @try_ask
        ... def risky() -> int:
        ...     return int("abc")
        >>> risky().is_err()
        True
    """
    def wrapper(*args: Any, **kwargs: Any) -> Result:
        try:
            return Ok(fn(*args, **kwargs))
        except Exception as e:
            return Err(e)
    return wrapper  # type: ignore[return-value]
