"""Console output and the standard streams.

Rust's ``println!``, ``eprint!``, and the ``std::io::stdin``/``stdout``/
``stderr`` handles. Every name here is also a plain function, so the common case
needs no object:

    >>> from oxide.logging import println
    >>> println("hello", 42)
    hello 42
    >>> from oxide.logging import print_
    >>> print_("no trailing newline", end="")
    no trailing newline
"""

from __future__ import annotations

import io
import os
import sys
from typing import Any, Iterator, TextIO

#: Whether ANSI colour should be emitted. ``None`` means "decide from the TTY".
_COLOR_OVERRIDE: bool | None = None

_ANSI = frozenset({"bold", "dim", "italic", "underline", "red", "green", "yellow", "blue", "magenta", "cyan", "grey", "white"})

_STDIN: "Stdin | None" = None
_STDOUT: "Stdout | None" = None
_STDERR: "Stderr | None" = None


def color_enabled() -> bool:
    """Return whether ANSI colour should be emitted.

    Honours the ``NO_COLOR`` convention and the ``FORCE_COLOR`` escape hatch,
    otherwise deferring to whether the stream is a terminal.

    Returns:
        bool: True when colour codes will be written.

    Example:
        >>> isinstance(color_enabled(), bool)
        True
    """
    if _COLOR_OVERRIDE is not None:
        return _COLOR_OVERRIDE
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stderr.isatty()


def set_color(enabled: bool | None) -> bool | None:
    """Force colour on or off, overriding terminal detection.

    Args:
        enabled: True to always colour, False to never colour, ``None`` to go
            back to detecting it.

    Returns:
        bool | None: The override that is now in effect.

    Example:
        >>> set_color(False)
        False
        >>> set_color(None)
        >>> isinstance(set_color(False), bool)
        True
        >>> set_color(None)
    """
    global _COLOR_OVERRIDE
    _COLOR_OVERRIDE = enabled
    return _COLOR_OVERRIDE


def style(text: Any, *names: str) -> str:
    """Wrap text in ANSI style codes, doing nothing when colour is off.

    Args:
        text: The value to style, formatted with :func:`str`.
        *names: Style names such as ``"red"``, ``"bold"``, or ``"cyan"``.

    Returns:
        str: The styled text, or the plain text when colour is disabled.

    Raises:
        ValueError: If a name is not a known style.

    Example:
        >>> set_color(False)
        False
        >>> style("hi", "red")
        'hi'
        >>> set_color(None)
    """
    plain = str(text)
    unknown = [name for name in names if name not in _ANSI]
    if unknown:
        raise ValueError(f"unknown style(s): {', '.join(unknown)}")
    if not names or not color_enabled():
        return plain
    codes = ";".join(str(_ANSI_CODES[name]) for name in names)
    return f"\033[{codes}m{plain}\033[0m"


_ANSI_CODES = {
    "bold": 1,
    "dim": 2,
    "italic": 3,
    "underline": 4,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "grey": 90,
    "white": 37,
}


class Stdin:
    """A handle on the process's standard input.

    Returned by :func:`stdin`. Wraps a :class:`io.TextIOBase` so line-oriented
    and whole-buffer reads both work without importing :mod:`sys`.

    Example:
        >>> from oxide.logging import stdin
        >>> stdin().is_terminal in (True, False)
        True
    """

    __slots__ = ("_stream",)

    def __init__(self, stream: TextIO | None = None) -> None:
        """Wrap a text stream.

        Args:
            stream: The stream to wrap. Defaults to :data:`sys.stdin`.
        """
        self._stream = stream if stream is not None else sys.stdin

    @property
    def stream(self) -> TextIO:
        """Return the wrapped stream.

        Returns:
            TextIO: The underlying stream.
        """
        return self._stream

    @property
    def is_terminal(self) -> bool:
        """Return whether input is attached to an interactive terminal.

        Returns:
            bool: True when the stream is a TTY.

        Example:
            >>> from oxide.logging import stdin
            >>> isinstance(stdin().is_terminal, bool)
            True
        """
        try:
            return bool(self._stream.isatty())
        except (AttributeError, ValueError):
            return False

    def read_line(self) -> str | None:
        """Read one line, keeping its trailing newline.

        Returns:
            str | None: The line, or None at end of input.
        """
        line = self._stream.readline()
        return line if line else None

    def read_line_or(self, fallback: str) -> str:
        """Read one line, substituting a fallback at end of input.

        Args:
            fallback: The value to return when input is exhausted.

        Returns:
            str: The line without its trailing newline, or ``fallback``.
        """
        line = self.read_line()
        return fallback if line is None else line.rstrip("\n")

    def read_all(self) -> str:
        """Read the stream to end of input.

        Returns:
            str: Everything that was left to read.
        """
        return self._stream.read()

    def __iter__(self) -> Iterator[str]:
        """Iterate over lines, stripping the trailing newline from each."""
        return (line.rstrip("\n") for line in self._stream)

    def __repr__(self) -> str:
        return "Stdin"


class Stdout:
    """A handle on the process's standard output.

    Returned by :func:`stdout`. :meth:`write` returns the number of characters
    written so it can be chained like :meth:`io.TextIOBase.write`, and
    :meth:`print` appends a newline.

    Example:
        >>> from io import StringIO
        >>> from oxide.logging import stdout, set_stdout
        >>> buffer = StringIO()
        >>> set_stdout(buffer)
        Stdout
        >>> stdout().write("hi")
        2
        >>> buffer.getvalue()
        'hi'
        >>> set_stdout(None)
        Stdout
    """

    __slots__ = ("_stream",)

    def __init__(self, stream: TextIO | None = None) -> None:
        """Wrap a text stream.

        Args:
            stream: The stream to wrap. Defaults to :data:`sys.stdout`.
        """
        self._stream = stream if stream is not None else sys.stdout

    @property
    def stream(self) -> TextIO:
        """Return the wrapped stream.

        Returns:
            TextIO: The underlying stream.
        """
        return self._stream

    @property
    def is_terminal(self) -> bool:
        """Return whether output is attached to an interactive terminal.

        Returns:
            bool: True when the stream is a TTY.

        Example:
            >>> from oxide.logging import stdout
            >>> isinstance(stdout().is_terminal, bool)
            True
        """
        try:
            return bool(self._stream.isatty())
        except (AttributeError, ValueError):
            return False

    def write(self, text: str) -> int:
        """Write text without a trailing newline.

        Args:
            text: The text to write.

        Returns:
            int: The number of characters written.
        """
        return self._stream.write(text)

    def print(self, *values: Any, sep: str = " ", end: str = "\n", flush: bool = False) -> None:
        """Write values and a newline.

        Args:
            *values: The values to write, formatted with :func:`str`.
            sep: Separator placed between values.
            end: Text appended after the last value.
            flush: Flush the stream afterwards.
        """
        self._stream.write(sep.join(str(value) for value in values) + end)
        if flush:
            self.flush()

    def flush(self) -> None:
        """Flush the underlying stream."""
        flush = getattr(self._stream, "flush", None)
        if flush is not None:
            flush()

    def __repr__(self) -> str:
        return "Stdout"


class Stderr(Stdout):
    """A handle on the process's standard error.

    Identical to :class:`Stdout` in every way except its default stream.

    Example:
        >>> from oxide.logging import stderr
        >>> stderr().is_terminal in (True, False)
        True
    """

    __slots__ = ()

    def __init__(self, stream: TextIO | None = None) -> None:
        """Wrap a text stream.

        Args:
            stream: The stream to wrap. Defaults to :data:`sys.stderr`.
        """
        super().__init__(stream if stream is not None else sys.stderr)

    def __repr__(self) -> str:
        return "Stderr"


def stdin() -> Stdin:
    """Return a handle on standard input.

    Unless :func:`set_stdin` has installed an override, each call returns a
    fresh handle bound to the *current* :data:`sys.stdin`, so replacing that
    stream — as test harnesses and doctests do — is picked up immediately.

    Returns:
        Stdin: A handle on standard input.
    """
    return _STDIN if _STDIN is not None else Stdin()


def set_stdin(stream: TextIO | None) -> Stdin:
    """Redirect standard input, mainly for tests.

    Args:
        stream: The stream to read from. ``None`` restores :data:`sys.stdin`.

    Returns:
        Stdin: The handle now in effect.

    Example:
        >>> from io import StringIO
        >>> set_stdin(StringIO("one\\ntwo\\n")).read_line_or("done")
        'one'
        >>> set_stdin(None)
        Stdin
    """
    global _STDIN
    _STDIN = None if stream is None else Stdin(stream)
    return stdin()


def stdout() -> Stdout:
    """Return a handle on standard output.

    Unless :func:`set_stdout` has installed an override, each call returns a
    fresh handle bound to the *current* :data:`sys.stdout`, so replacing that
    stream — as test harnesses and doctests do — is picked up immediately.

    Returns:
        Stdout: A handle on standard output.
    """
    return _STDOUT if _STDOUT is not None else Stdout()


def set_stdout(stream: TextIO | None) -> Stdout:
    """Redirect standard output, mainly for tests.

    Args:
        stream: The stream to write to. ``None`` restores :data:`sys.stdout`.

    Returns:
        Stdout: The handle now in effect.

    Example:
        >>> from io import StringIO
        >>> buffer = StringIO()
        >>> set_stdout(buffer)
        Stdout
        >>> println("captured")
        >>> buffer.getvalue().strip()
        'captured'
        >>> set_stdout(None)
        Stdout
    """
    global _STDOUT
    _STDOUT = None if stream is None else Stdout(stream)
    return stdout()


def stderr() -> Stderr:
    """Return a handle on standard error.

    Unless :func:`set_stderr` has installed an override, each call returns a
    fresh handle bound to the *current* :data:`sys.stderr`, so replacing that
    stream — as test harnesses and doctests do — is picked up immediately.

    Returns:
        Stderr: A handle on standard error.
    """
    return _STDERR if _STDERR is not None else Stderr()


def set_stderr(stream: TextIO | None) -> Stderr:
    """Redirect standard error, mainly for tests.

    Args:
        stream: The stream to write to. ``None`` restores :data:`sys.stderr`.

    Returns:
        Stderr: The handle now in effect.

    Example:
        >>> from io import StringIO
        >>> buffer = StringIO()
        >>> set_stderr(buffer)
        Stderr
        >>> eprintln("captured")
        >>> buffer.getvalue().strip()
        'captured'
        >>> set_stderr(None)
        Stderr
    """
    global _STDERR
    _STDERR = None if stream is None else Stderr(stream)
    return stderr()


def print_(*values: Any, sep: str = " ", end: str = "", flush: bool = False) -> None:
    """Write values to standard output without a newline.

    Named with a trailing underscore so it does not shadow the builtin
    ``print``.

    Args:
        *values: The values to write, formatted with :func:`str`.
        sep: Separator placed between values.
        end: Text appended after the last value.
        flush: Flush the stream afterwards.

    Example:
        >>> print_("a", 1, True)
        a 1 True
    """
    stdout().print(*values, sep=sep, end=end, flush=flush)


def println(*values: Any, sep: str = " ", end: str = "\n", flush: bool = False) -> None:
    """Write values and a newline to standard output, like Rust's ``println!``.

    Args:
        *values: The values to write, formatted with :func:`str`.
        sep: Separator placed between values.
        end: Text appended after the last value.
        flush: Flush the stream afterwards.

    Example:
        >>> println("count:", 3)
        count: 3
        >>> println("a", "b", sep="-")
        a-b
    """
    stdout().print(*values, sep=sep, end=end, flush=flush)


def eprint_(*values: Any, sep: str = " ", end: str = "", flush: bool = False) -> None:
    """Write values to standard error without a newline.

    Args:
        *values: The values to write, formatted with :func:`str`.
        sep: Separator placed between values.
        end: Text appended after the last value.
        flush: Flush the stream afterwards.

    Example:
        >>> from io import StringIO
        >>> buffer = StringIO()
        >>> set_stderr(buffer)
        Stderr
        >>> eprint_("diagnostic:", "careful")
        >>> buffer.getvalue()
        'diagnostic: careful'
        >>> set_stderr(None)
        Stderr
    """
    stderr().print(*values, sep=sep, end=end, flush=flush)


def eprintln(*values: Any, sep: str = " ", end: str = "\n", flush: bool = False) -> None:
    """Write values and a newline to standard error, like Rust's ``eprintln!``.

    Args:
        *values: The values to write, formatted with :func:`str`.
        sep: Separator placed between values.
        end: Text appended after the last value.
        flush: Flush the stream afterwards.

    Example:
        >>> from io import StringIO
        >>> buffer = StringIO()
        >>> set_stderr(buffer)
        Stderr
        >>> eprintln("error: something failed")
        >>> buffer.getvalue().strip()
        'error: something failed'
        >>> set_stderr(None)
        Stderr
    """
    stderr().print(*values, sep=sep, end=end, flush=flush)


def capture() -> tuple[io.StringIO, io.StringIO]:
    """Redirect both output streams into in-memory buffers.

    Intended for tests that need to assert on console output. Call
    :func:`set_stdout` and :func:`set_stderr` with ``None`` to restore.

    Returns:
        tuple: The stdout and stderr buffers.

    Example:
        >>> out, err = capture()
        >>> println("x")
        >>> eprintln("y")
        >>> out.getvalue().strip(), err.getvalue().strip()
        ('x', 'y')
        >>> set_stdout(None)
        Stdout
        >>> set_stderr(None)
        Stderr
    """
    out, err = io.StringIO(), io.StringIO()
    set_stdout(out)
    set_stderr(err)
    return out, err


__all__ = [
    "Stderr",
    "Stdin",
    "Stdout",
    "capture",
    "color_enabled",
    "eprint_",
    "eprintln",
    "print_",
    "println",
    "set_color",
    "set_stderr",
    "set_stdin",
    "set_stdout",
    "stdin",
    "stderr",
    "stdout",
    "style",
]