"""Debugging, formatting, and inspection utilities.

Provides the :class:`Formatter` string builder, string formatting helpers,
value inspection (``dbg``/``dbg_``), configuration lookup, compile-time
file inclusion, and pattern matching.

Example:
    >>> from oxide.macros import dbg, format_
    >>> format_("{} and {}", "a", "b")
    'a and b'
"""

from __future__ import annotations

import inspect
import os
import traceback
from typing import Any


class Formatter:
    """String builder that collects fragments until they are joined.

    Mirrors Rust's ``fmt::Formatter``: write pieces to the internal buffer and
    call :meth:`finish` (or :meth:`as_str`) to obtain the concatenated result.
    This is useful when assembling output incrementally without intermediate
    string concatenation.

    Example:
        >>> from oxide.macros import Formatter
        >>> f = Formatter()
        >>> f.write_str("hello")
        >>> f.write_char("!")
        >>> f.finish()
        'hello!'
    """

    __slots__ = ("_buf",)

    def __init__(self) -> None:
        self._buf: list[str] = []

    def write_str(self, s: str) -> None:  # type: ignore
        """Append a whole string to the buffer.

        Args:
            s: The string to append.
        """
        self._buf.append(s)

    def write_char(self, c: str) -> None:  # type: ignore
        """Append a single character to the buffer.

        Args:
            c: A one-character string to append.
        """
        self._buf.append(c)

    def write_fmt(self, args: str) -> None:  # type: ignore
        """Append an already-formatted string to the buffer.

        Args:
            args: The formatted string to append.
        """
        self._buf.append(args)

    def finish(self) -> str:  # type: ignore
        """Return the concatenated contents of the buffer as a string.

        Returns:
            The accumulated buffer contents joined into one string.
        """
        return "".join(self._buf)

    def as_str(self) -> str:  # type: ignore
        """Return the concatenated contents of the buffer as a string.

        Alias for :meth:`finish`.

        Returns:
            The accumulated buffer contents joined into one string.
        """
        return "".join(self._buf)

    def __str__(self) -> str:
        return "".join(self._buf)


def format_(template: str, *args: Any, **kwargs: Any) -> str:
    """Format a template string with positional and keyword arguments.

    Thin wrapper around :meth:`str.format` provided for parity with Rust's
    ``format!`` macro.

    Args:
        template: A format string using :meth:`str.format` syntax.
        *args: Positional values substituted into the template.
        **kwargs: Keyword values substituted into the template by name.

    Returns:
        The formatted string.

    Example:
        >>> from oxide.macros import format_
        >>> format_("{} = {value}", 3, value="three")
        '3 = three'
    """
    return template.format(*args, **kwargs)


def write_(buf: Any, template: str, *args: Any, **kwargs: Any) -> None:
    """Write a formatted string into a buffer-like object.

    Supports any object with a ``write`` method (e.g. file-like objects) or an
    ``append`` method (e.g. lists and :class:`Formatter` buffers).

    Args:
        buf: The destination buffer; must expose ``write`` or ``append``.
        template: A format string.
        *args: Positional values for the template.
        **kwargs: Keyword values for the template.

    Example:
        >>> from oxide.macros import write_
        >>> out = []
        >>> write_(out, "x={}", 42)
        >>> out
        ['x=42']
    """
    formatted = template.format(*args, **kwargs)
    if hasattr(buf, 'write'):
        buf.write(formatted)
    elif hasattr(buf, 'append'):
        buf.append(formatted)


def writeln_(buf: Any, template: str = "", *args: Any, **kwargs: Any) -> None:
    """Write a formatted string followed by a newline into a buffer.

    If no template is given, only a newline is written.

    Args:
        buf: The destination buffer; must expose ``write`` or ``append``.
        template: An optional format string. Defaults to an empty string.
        *args: Positional values for the template.
        **kwargs: Keyword values for the template.

    Example:
        >>> from oxide.macros import writeln_
        >>> out = []
        >>> writeln_(out, "{}!", "hi")
        >>> out
        ['hi!\\n']
    """
    formatted = template.format(*args, **kwargs) if template else ""
    if hasattr(buf, 'write'):
        buf.write(formatted + "\n")
    elif hasattr(buf, 'append'):
        buf.append(formatted + "\n")


def dbg_(*args: Any) -> Any:
    """Print the given arguments with their source location and return them.

    Each argument is printed with ``repr``; if exactly one argument is given it
    is returned unchanged, otherwise a tuple of all arguments is returned.

    Args:
        *args: Values to inspect and return.

    Returns:
        The single argument if only one was supplied, otherwise a tuple of all
        arguments.

    Example:
        >>> import oxide.macros.debugging as d
        >>> d.dbg_("hello")  # doctest: +SKIP
        [<stdin>:1] 'hello'
        'hello'
    """
    frames = traceback.extract_stack()
    if len(frames) >= 2:
        frame = frames[-2]
        loc = f"{frame.filename}:{frame.lineno}"
    else:
        loc = "<unknown>"
    parts = []
    for i, arg in enumerate(args):
        parts.append(f"{arg!r}")
    print(f"[{loc}] {', '.join(parts)}")
    return args[0] if len(args) == 1 else args


def dbg(value: Any, *args: Any, **kwargs: Any) -> Any:
    """Print a value with its variable name and location, then return it.

    Inspects the caller's scope to infer the local variable name bound to the
    value, then prints it along with any extra positional/keyword hints.

    Args:
        value: The value to inspect and return.
        *args: Optional extra values to print as hints.
        **kwargs: Optional key/value hints to print.

    Returns:
        The original ``value`` unchanged, so calls can be wrapped inline.

    Example:
        >>> def f():
        ...     x = 5
        ...     return dbg(x) + 1
        >>> f()  # doctest: +SKIP
    """
    frame = inspect.currentframe()
    caller = frame.f_back if frame else None  # type: ignore
    var_name = ""
    if caller:
        code = caller.f_code
        for name in code.co_varnames:
            if caller.f_locals.get(name) is value:
                var_name = name
                break
    loc = ""
    if caller:
        loc = f"{caller.f_code.co_filename}:{caller.f_lineno}"
    prefix = f"[{var_name}]" if var_name else ""
    suffix = ""
    if args:
        suffix = " " + " ".join(str(a) for a in args)
    if kwargs:
        suffix += " " + " ".join(f"{k}={v!r}" for k, v in kwargs.items())
    print(f"{prefix} {value!r}{suffix} @ {loc}")
    return value


def cfg(key: str, default: str = "") -> str:
    """Read a configuration value from the ``CFG_<KEY>`` environment variable.

    Args:
        key: The config name; looked up as ``CFG_<KEY>`` (case-insensitive,
            uppercased).
        default: Value returned if the variable is unset. Defaults to "".

    Returns:
        The environment variable value or ``default``.

    Example:
        >>> from oxide.macros import cfg
        >>> cfg("HOST", "localhost")  # reads CFG_HOST
        'localhost'
    """
    return os.environ.get(f"CFG_{key.upper()}", default)


def compile_error(message: str) -> None:
    """Raise a SyntaxError to signal that compilation should not continue.

    Intended to mirror Rust's ``compile_error!`` macro for cases where a
    configuration or usage error should be surfaced at import time.

    Args:
        message: The error message to include in the raised SyntaxError.

    Raises:
        SyntaxError: Always, with the message prefixed by ``compile_error:``.
    """
    raise SyntaxError(f"compile_error: {message}")


def option_env(key: str) -> str | None:
    """Return the value of an environment variable, or None if it is unset.

    Args:
        key: The environment variable name.

    Returns:
        The variable's value, or ``None`` if it is not set.

    Example:
        >>> from oxide.macros import option_env
        >>> option_env("PATH") is None or isinstance(option_env("PATH"), str)
        True
    """
    return os.environ.get(key)


def include_str(path: str) -> str:
    """Read and return the contents of a file as a string.

    Mirrors Rust's ``include_str!`` macro.

    Args:
        path: Path to the file to read.

    Returns:
        The file contents as text.

    Raises:
        OSError: If the file cannot be opened or read.
    """
    with open(path, 'r') as f:
        return f.read()


def include_bytes(path: str) -> bytes:
    """Read and return the contents of a file as bytes.

    Mirrors Rust's ``include_bytes!`` macro.

    Args:
        path: Path to the file to read.

    Returns:
        The raw file contents as bytes.

    Raises:
        OSError: If the file cannot be opened or read.
    """
    with open(path, 'rb') as f:
        return f.read()


def matches(value: Any, pattern: Any) -> bool:
    """Return True if ``value`` matches ``pattern``.

    If ``pattern`` is callable it is invoked with ``value`` and its result is
    returned; otherwise a plain equality comparison is performed.

    Args:
        value: The value to test.
        pattern: Either a callable ``(value) -> bool`` or a value to compare
            with ``==``.

    Returns:
        Whether the value matches the pattern.

    Example:
        >>> from oxide.macros import matches
        >>> matches(4, lambda n: n > 3)
        True
        >>> matches("a", "a")
        True
    """
    if callable(pattern):
        return pattern(value)
    return value == pattern
