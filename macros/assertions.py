"""Runtime assertion macros for validating values and conditions.

Provides ``assert_eq``, ``assert_ne``, ``assert_``, ``assert_matches``,
``assert_type`` and their debug-only counterparts (``debug_assert``,
``debug_assert_eq``, ``debug_assert_ne``) for runtime correctness checks.

Example:
    >>> from oxide.macros import assert_eq
    >>> assert_eq(2 + 2, 4)
"""

from __future__ import annotations

import re
from typing import Any


class AssertionError(Exception):
    """Raised when an assertion check fails.

    This is the exception raised by the assertion macros in this module when
    the condition being checked is not satisfied. It serves the same purpose
    as the built-in ``AssertionError`` but is a distinct type so callers can
    catch assertion failures raised by these macros specifically.
    """

    pass


def assert_(condition: bool, message: str = "assertion failed") -> None:
    """Raise AssertionError if ``condition`` is False, otherwise do nothing.

    Use this when you need to assert a plain boolean condition with a custom
    message that is shown if the assertion fails.

    Args:
        condition: The boolean condition to validate.
        message: The message to include in the raised error. Defaults to
            ``"assertion failed"``.

    Raises:
        AssertionError: If ``condition`` is False.

    Example:
        >>> import oxide.macros.assertions as a
        >>> a.assert_(1 < 2)
        >>> a.assert_(False, "must be true")
        Traceback (most recent call last):
        ...
        oxide.macros.assertions.AssertionError: must be true
    """
    if not condition:
        raise AssertionError(message)


def assert_eq(a: Any, b: Any, message: str | None = None) -> None:
    """Raise AssertionError if ``a`` is not equal to ``b``.

    Args:
        a: The first value to compare.
        b: The second value to compare.
        message: Optional custom error message. If omitted, a default message
            showing the two differing values is used.

    Raises:
        AssertionError: If ``a != b``.

    Example:
        >>> from oxide.macros import assert_eq
        >>> assert_eq(2 + 2, 4)
    """
    if a != b:
        msg = message or f"assertion failed: {a!r} != {b!r}"
        raise AssertionError(msg)


def assert_ne(a: Any, b: Any, message: str | None = None) -> None:
    """Raise AssertionError if ``a`` is equal to ``b``.

    Args:
        a: The first value to compare.
        b: The second value to compare.
        message: Optional custom error message. If omitted, a default message
            showing the unexpectedly equal values is used.

    Raises:
        AssertionError: If ``a == b``.

    Example:
        >>> from oxide.macros import assert_ne
        >>> assert_ne(1, 2)
    """
    if a == b:
        msg = message or f"assertion failed: {a!r} == {b!r}"
        raise AssertionError(msg)


def assert_matches(value: Any, pattern: str, message: str | None = None) -> None:
    """Raise AssertionError if ``value`` does not match a regular expression.

    The string form of ``value`` is matched (at the beginning, like
    :func:`re.match`) against ``pattern``.

    Args:
        value: The value whose string representation is tested.
        pattern: The regular expression pattern to match against.
        message: Optional custom error message.

    Raises:
        AssertionError: If the value does not match the pattern.

    Example:
        >>> from oxide.macros import assert_matches
        >>> assert_matches("hello-42", r"hello-\\d+")
    """
    if not re.match(pattern, str(value)):
        msg = message or f"assertion failed: {value!r} does not match {pattern!r}"
        raise AssertionError(msg)


def assert_type(value: Any, expected: type, message: str | None = None) -> None:
    """Raise AssertionError if ``value`` is not an instance of ``expected``.

    Args:
        value: The value to type check.
        expected: The type (or tuple of types) that ``value`` must be an
            instance of.
        message: Optional custom error message.

    Raises:
        AssertionError: If ``value`` is not an instance of ``expected``.

    Example:
        >>> from oxide.macros import assert_type
        >>> assert_type("hi", str)
    """
    if not isinstance(value, expected):
        msg = message or f"assertion failed: expected {expected.__name__}, got {type(value).__name__}"
        raise AssertionError(msg)


def debug_assert(condition: bool, message: str = "") -> None:
    """Assert a condition only when running in debug mode.

    These checks are compiled away when Python runs with optimization enabled
    (``-O``), making them useful for invariants that should not cost anything
    in production.

    Args:
        condition: The boolean condition to check.
        message: An optional message shown if the assertion fails.

    Raises:
        AssertionError: If ``condition`` is False and ``__debug__`` is True.

    Example:
        >>> from oxide.macros import debug_assert
        >>> debug_assert(3 > 1)
    """
    if __debug__:
        assert condition, message


def debug_assert_eq(a: Any, b: Any, message: str = "") -> None:
    """Assert ``a == b`` only when running in debug mode.

    Args:
        a: The first value to compare.
        b: The second value to compare.
        message: An optional message shown if the assertion fails.

    Raises:
        AssertionError: If ``a != b`` and ``__debug__`` is True.
    """
    if __debug__:
        assert_eq(a, b, message)


def debug_assert_ne(a: Any, b: Any, message: str = "") -> None:
    """Assert ``a != b`` only when running in debug mode.

    Args:
        a: The first value to compare.
        b: The second value to compare.
        message: An optional message shown if the assertion fails.

    Raises:
        AssertionError: If ``a == b`` and ``__debug__`` is True.
    """
    if __debug__:
        assert_ne(a, b, message)
