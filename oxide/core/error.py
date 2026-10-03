"""Error infrastructure — structured error handling.

Provides Error, Backtrace, Location, and context() for building rich
error chains with source tracking and stack trace capture.
"""

from __future__ import annotations

import traceback


class Location:
    """Represents a source code location (file, line, column).

    Captures the origin of an error for debugging and reporting. Values default
    to empty/zero so a location can be constructed incrementally.

    Example:
        >>> loc = Location("main.py", 12, 4)
        >>> str(loc)
        'main.py:12:4'
    """

    __slots__ = ("_file", "_line", "_column")

    def __init__(self, file: str = "", line: int = 0, column: int = 0) -> None:
        """Create a source location.

        Args:
            file (str, optional): The file path. Defaults to "".
            line (int, optional): The line number. Defaults to 0.
            column (int, optional): The column number. Defaults to 0.
        """
        self._file = file
        self._line = line
        self._column = column

    def file(self) -> str:  # type: ignore
        """Return the file path of this location.

        Returns:
            str: The stored file path.
        """
        return self._file

    def line(self) -> int:  # type: ignore
        """Return the line number of this location.

        Returns:
            int: The stored line number.
        """
        return self._line

    def column(self) -> int:  # type: ignore
        """Return the column number of this location.

        Returns:
            int: The stored column number.
        """
        return self._column

    def __str__(self) -> str:
        """Return the location formatted as ``file:line:column``.

        Returns:
            str: A colon-separated string of file, line, and column.
        """
        return f"{self._file}:{self._line}:{self._column}"

    def __repr__(self) -> str:
        """Return an unambiguous string representation of this location.

        Returns:
            str: A ``Location(...)`` constructor-style string.
        """
        return f"Location({self._file!r}, {self._line}, {self._column})"


class Backtrace:
    """Captures a snapshot of the current call stack at construction time.

    Records both the raw stack frames and a formatted traceback, useful for
    attaching debugging information to an error.

    Example:
        >>> bt = Backtrace()
        >>> len(bt.frames()) > 0
        True
    """

    __slots__ = ("_frames", "_formatted")

    def __init__(self) -> None:
        """Capture the call stack at the moment of construction."""
        self._frames = traceback.extract_stack()
        self._formatted = "".join(traceback.format_stack())

    def __str__(self) -> str:
        """Return the formatted stack trace.

        Returns:
            str: A multi-line stack trace string for this backtrace.
        """
        return self._formatted

    def __repr__(self) -> str:
        """Return a short representation of this backtrace.

        Returns:
            str: A summary indicating the number of captured frames.
        """
        return f"Backtrace({len(self._frames)} frames)"

    def frames(self) -> list:  # type: ignore
        """Return the list of captured stack frames.

        Returns:
            list: The raw stack frames captured at construction time.
        """
        return self._frames


class Error(Exception):
    """Structured error with message, optional source, backtrace, and context.

    Extends ``Exception`` with rich metadata: an optional underlying ``source``
    exception, a lazily captured ``backtrace``, a source ``location``, and an
    arbitrary ``context`` message for chaining readable error reports.

    Example:
        >>> try:
        ...     raise Error("failed").with_context("in load step")
        ... except Error as e:
        ...     print(str(e))
        failed: context: in load step
    """
    __slots__ = ("_message", "_source", "_backtrace", "_location", "_context")

    def __init__(self, message: str = "", source: Exception | None = None) -> None:
        """Create an error with a message and optional source exception.

        Args:
            message (str, optional): The error message. Defaults to "".
            source (Exception, optional): An underlying exception to wrap.
        """
        super().__init__(message)
        self._message = message
        self._source = source
        self._backtrace: Backtrace | None = None
        self._location: Location | None = None
        self._context: str | None = None

    @classmethod
    def new(cls, message: str) -> Error:  # type: ignore
        """Create a new Error with the given message.

        Args:
            message (str): The error message.

        Returns:
            Error: A new Error instance.

        Example:
            >>> Error.new("boom").message()
            'boom'
        """
        return cls(message)

    @classmethod
    def from_source(cls, source: Exception) -> Error:  # type: ignore
        """Create an Error wrapping an existing exception as the source.

        Args:
            source (Exception): The exception to wrap.

        Returns:
            Error: A new Error whose message and source derive from ``source``.
        """
        return cls(str(source), source)

    def message(self) -> str:  # type: ignore
        """Return the error message.

        Returns:
            str: The message set on this error.
        """
        return self._message

    def source(self) -> Exception | None:  # type: ignore
        """Return the underlying source exception, if any.

        Returns:
            Exception, optional: The wrapped source exception, or None.
        """
        return self._source

    def backtrace(self) -> Backtrace:  # type: ignore
        """Return the captured backtrace, lazily creating it if needed.

        The backtrace is captured on first access, reflecting the stack at
        that point rather than at error construction.

        Returns:
            Backtrace: The backtrace for this error.
        """
        if self._backtrace is None:
            self._backtrace = Backtrace()
        return self._backtrace

    def location(self) -> Location | None:  # type: ignore
        """Return the source location where this error originated, if set.

        Returns:
            Location, optional: The source location, or None if unset.
        """
        return self._location

    def with_context(self, ctx: str) -> Error:  # type: ignore
        """Attach a context message and return self for chaining.

        Args:
            ctx (str): The context message to attach.

        Returns:
            Error: This same error, for chaining further calls.

        Example:
            >>> Error("op failed").with_context("uploading").context()
            'uploading'
        """
        self._context = ctx
        return self

    def context(self) -> str | None:  # type: ignore
        """Return the context message, if any.

        Returns:
            str, optional: The attached context message, or None.
        """
        return self._context

    def with_source(self, source: Exception) -> Error:  # type: ignore
        """Attach a source exception and return self for chaining.

        Args:
            source (Exception): The source exception to attach.

        Returns:
            Error: This same error, for chaining further calls.
        """
        self._source = source
        return self

    def __str__(self) -> str:
        """Return a readable summary of this error with its context and source.

        Returns:
            str: The message, optionally with ``context:`` and ``source:`` parts.
        """
        parts = [self._message]
        if self._context:
            parts.append(f"context: {self._context}")
        if self._source:
            parts.append(f"source: {self._source}")
        return ": ".join(parts)


def context(msg: str, err: Exception) -> Error:
    """Wrap an exception in an Error with a context message and backtrace.

    Builds an ``Error`` that carries ``msg`` as both message and context, with
    ``err`` as its source and a backtrace captured immediately.

    Args:
        msg (str): The context/message to associate with the error.
        err (Exception): The underlying exception to wrap.

    Returns:
        Error: A new Error linking ``err`` with the given context.

    Example:
        >>> e = context("loading", ValueError("bad"))
        >>> e.source() is not None
        True
    """
    e = Error(msg)
    e._source = err
    e._context = msg
    e._backtrace = Backtrace()
    return e
