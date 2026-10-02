"""Panic and resource-management helpers.

Provides intentional runtime failures (``panic``, ``todo``, ``unimplemented``)
and RAII-style cleanup via :class:`ScopeGuard` and :func:`defer`.

Example:
    >>> from oxide.macros import ScopeGuard, defer
    >>> events = []
    >>> guard = defer(lambda: events.append("cleanup"))
    >>> guard.cancel()
"""

from __future__ import annotations

import traceback
from typing import Any, Callable, Generic, TypeVar, NoReturn

T = TypeVar("T")


class UnimplementedError(Exception):
    """Raised when a code path has not been implemented yet.

    Used by :func:`unimplemented` and :func:`todo` to signal incomplete work.

    Example:
        >>> from oxide.macros import UnimplementedError
        >>> try:
        ...     raise UnimplementedError("coming soon")
        ... except UnimplementedError as e:
        ...     str(e)
        'coming soon'
    """

    __slots__ = ("_message",)

    def __init__(self, message: str | None = None) -> None:
        """Initialize the error with an optional message.

        Args:
            message: Custom message; defaults to ``"not yet implemented"``.
        """
        self._message = message or "not yet implemented"
        super().__init__(self._message)


def unimplemented(message: str | None = None) -> NoReturn:
    """Signal that code has not been implemented and stop execution.

    Args:
        message: Optional message describing what is missing.

    Raises:
        UnimplementedError: Always.

    Example:
        >>> from oxide.macros import unimplemented, UnimplementedError
        >>> try:
        ...     unimplemented("not done")
        ... except UnimplementedError:
        ...     print("not implemented")
        not implemented
    """
    raise UnimplementedError(message)


def todo(message: str | None = None) -> NoReturn:
    """Signal incomplete work, typically in a code path still being developed.

    Args:
        message: Optional message describing the pending work.

    Raises:
        UnimplementedError: Always, with the message or ``"not yet implemented"``.

    Example:
        >>> from oxide.macros import todo, UnimplementedError
        >>> try:
        ...     todo("finish this")
        ... except UnimplementedError as e:
        ...     str(e)
        'finish this'
    """
    raise UnimplementedError(message or "not yet implemented")


class PanicError(Exception):
    """Exception representing an explicit panic with a captured backtrace.

    Raised by :func:`panic` and :func:`panic_fmt`. The stack trace at the point
    of construction is captured and exposed via the :attr:`backtrace` property.

    Example:
        >>> from oxide.macros import PanicError
        >>> try:
        ...     raise PanicError("boom")
        ... except PanicError as e:
        ...     "boom" in str(e)
        True
    """

    __slots__ = ("_message", "_backtrace")

    def __init__(self, message: str | None = None) -> None:
        """Initialize the panic with an optional message.

        Args:
            message: Custom panic message; defaults to ``"explicit panic"``.
        """
        self._message = message or "explicit panic"
        self._backtrace = traceback.format_stack()
        super().__init__(self._message)

    @property
    def backtrace(self) -> list[str]:
        """Return the captured stack trace as a list of strings.

        Returns:
            The formatted stack frames captured when the panic was created.
        """
        return self._backtrace

    def __str__(self) -> str:
        tb = "".join(self._backtrace[:-1])
        return f"panicked at '{self._message}'\n{tb}"


def panic(message: str | None = None) -> NoReturn:
    """Trigger an explicit panic, raising a PanicError.

    Args:
        message: Optional panic message; defaults to ``"explicit panic"``.

    Raises:
        PanicError: Always.

    Example:
        >>> from oxide.macros import panic, PanicError
        >>> try:
        ...     panic("fatal")
        ... except PanicError as e:
        ...     "fatal" in str(e)
        True
    """
    raise PanicError(message)


def panic_fmt(*args: Any, **kwargs: Any) -> NoReturn:
    """Trigger a panic with a message built from the given arguments.

    Positional arguments are joined with spaces; keyword arguments are appended
    as ``name=value`` pairs.

    Args:
        *args: Values to include in the panic message.
        **kwargs: Named values to include in the panic message.

    Raises:
        PanicError: Always.

    Example:
        >>> from oxide.macros import panic_fmt, PanicError
        >>> try:
        ...     panic_fmt("oops", code=7)
        ... except PanicError as e:
        ...     "code=7" in str(e)
        True
    """
    msg = " ".join(str(a) for a in args)
    for k, v in kwargs.items():
        msg += f" {k}={v!r}"
    raise PanicError(msg)


class ScopeGuard(Generic[T]):
    """RAII guard that runs a cleanup function on scope exit.

    The cleanup function runs when the guard is garbage-collected, exits the
    ``with`` block, or is explicitly executed via :meth:`execute`. Use
    :meth:`cancel` to suppress the cleanup.

    Example:
        >>> from oxide.macros import ScopeGuard
        >>> log = []
        >>> with ScopeGuard(lambda: log.append("exiting")):
        ...     pass
        >>> log
        ['exiting']
    """

    __slots__ = ("_fn", "_cancelled", "_value")

    def __init__(self, fn: Callable[[], T], value: T | None = None) -> None:
        """Initialize the guard with a cleanup function.

        Args:
            fn: The callable to run on exit.
            value: An optional value held by the guard; not used internally.
        """
        self._fn = fn
        self._cancelled = False
        self._value = value

    def cancel(self) -> None:
        """Prevent the cleanup function from running later."""
        self._cancelled = True

    def is_cancelled(self) -> bool:
        """Return True if the guard has been cancelled.

        Returns:
            Whether the cleanup function was suppressed via :meth:`cancel`.
        """
        return self._cancelled

    def execute(self) -> T | None:
        """Run the cleanup function now, at most once, and return its result.

        Returns:
            The cleanup function's return value if it has not already run, else
            ``None``.
        """
        if not self._cancelled:
            self._cancelled = True
            return self._fn()
        return None

    def __enter__(self) -> ScopeGuard[T]:
        return self

    def __exit__(self, *_: Any) -> None:
        if not self._cancelled:
            self._cancelled = True
            self._fn()

    def __repr__(self) -> str:
        return f"ScopeGuard(cancelled={self._cancelled})"


def defer(fn: Callable[[], Any]) -> ScopeGuard:
    """Create a ScopeGuard that runs ``fn`` on scope exit.

    Convenience factory for :class:`ScopeGuard` without needing to import the
    class directly.

    Args:
        fn: The cleanup callable to run on exit.

    Returns:
        A :class:`ScopeGuard` wrapping ``fn``.

    Example:
        >>> from oxide.macros import defer
        >>> calls = []
        >>> g = defer(lambda: calls.append("ran"))
        >>> g.execute()
        >>> calls
        ['ran']
    """
    return ScopeGuard(fn)
