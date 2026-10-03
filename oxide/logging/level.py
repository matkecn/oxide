"""Log levels, from Rust's ``tracing`` crate and the ``log`` facade.

A :class:`LogLevel` is the ordered severity scale used throughout
:mod:`oxide.logging`. The names follow Rust's ``tracing::Level``:

===========  ==========  ==================================================
Level        Short       Meaning
===========  ==========  ==================================================
:attr:`~LogLevel.ERROR`   ``ERR``  Something failed and the caller must know
:attr:`~LogLevel.WARN`    ``WARN``  Something is suspicious but recoverable
:attr:`~LogLevel.INFO`    ``INFO``  Normal, expected progress
:attr:`~LogLevel.DEBUG`   ``DBG``   Detail useful while diagnosing a problem
:attr:`~LogLevel.TRACE`   ``TRACE`` Everything, including per-iteration detail
===========  ==========  ==================================================

The class is a :class:`str` subclass, so a level interoperates with the strings
it equals and can be used anywhere a plain name is accepted. Comparisons order by
verbosity, not alphabetically, so ERROR sorts before TRACE.

Example:
    >>> from oxide.logging import LogLevel
    >>> LogLevel.ERROR < LogLevel.WARN
    True
    >>> LogLevel("info").short
    'INFO'
    >>> str(LogLevel.TRACE)
    'TRACE'
"""

from __future__ import annotations

from typing import Any

ERROR = "ERROR"
WARN = "WARN"
INFO = "INFO"
DEBUG = "DEBUG"
TRACE = "TRACE"

#: Every level, ordered from least to most verbose.
LOG_LEVELS: tuple[str, ...] = (ERROR, WARN, INFO, DEBUG, TRACE)

_ALIASES: dict[str, str] = {
    "error": ERROR,
    "err": ERROR,
    "fatal": ERROR,
    "panic": ERROR,
    "warn": WARN,
    "warning": WARN,
    "info": INFO,
    "information": INFO,
    "debug": DEBUG,
    "dbg": DEBUG,
    "trace": TRACE,
    "verbose": TRACE,
}


class LogLevel(str):
    """An ordered log severity level.

    Behaves as a plain string — ``LogLevel.WARN == "WARN"`` is True — while
    adding ordering, a short label, ANSI colouring, and name resolution from
    aliases.

    Attributes:
        ERROR (LogLevel): A failure the caller must know about.
        WARN (LogLevel): Something suspicious but recoverable.
        INFO (LogLevel): Normal, expected progress.
        DEBUG (LogLevel): Detail useful while diagnosing a problem.
        TRACE (LogLevel): Everything, including per-iteration detail.

    Example:
        >>> level = LogLevel("warn")
        >>> level.name
        'WARN'
        >>> level.rank
        1
        >>> LogLevel.TRACE.is_verbose()
        True
    """

    __slots__ = ()

    @property
    def name(self) -> str:
        """Return the canonical level name.

        Returns:
            str: One of ``ERROR``, ``WARN``, ``INFO``, ``DEBUG``, ``TRACE``.
        """
        return resolve_level(self)

    @property
    def rank(self) -> int:
        """Return the verbosity rank, where higher means more verbose.

        Returns:
            int: ``0`` for ERROR through ``4`` for TRACE.
        """
        return LOG_LEVELS.index(self.name)

    @property
    def short(self) -> str:
        """Return the abbreviated label used in aligned output.

        Returns:
            str: ``ERR``, ``WARN``, ``INFO``, ``DBG``, or ``TRACE``.
        """
        return _SHORT[self.name]

    @property
    def color(self) -> str:
        """Return the ANSI SGR escape sequence for this level.

        Returns:
            str: An escape sequence such as ``"\\x1b[31m"`` for ERROR, or an
            empty string when :mod:`oxide.logging` has colour disabled.
        """
        from .console import color_enabled

        if not color_enabled():
            return ""
        return _COLOR[self.name]

    def is_verbose(self) -> bool:
        """Return whether this level is DEBUG or TRACE.

        Returns:
            bool: True for the two diagnostic levels.
        """
        return self.rank >= LOG_LEVELS.index(DEBUG)

    def is_severe(self) -> bool:
        """Return whether this level is ERROR or WARN.

        Returns:
            bool: True for the two levels that usually need a response.
        """
        return self.rank <= LOG_LEVELS.index(WARN)

    def _compare(self, other: Any) -> Any:
        """Compare against another level by verbosity rank.

        Args:
            other: The level to compare against.

        Returns:
            Any: A negative, zero, or positive integer for use by the
            rich-comparison operators.

        Raises:
            TypeError: If ``other`` is not a level.
            ValueError: If ``other`` names an unknown level.
        """
        if not isinstance(other, (str, int)) and not hasattr(other, "name"):
            return NotImplemented
        try:
            other_rank = level_rank(other)
        except ValueError:
            return NotImplemented
        mine = self.rank
        return (mine > other_rank) - (mine < other_rank)

    def __lt__(self, other: Any) -> Any:
        result = self._compare(other)
        return NotImplemented if result is NotImplemented else result < 0

    def __le__(self, other: Any) -> Any:
        result = self._compare(other)
        return NotImplemented if result is NotImplemented else result <= 0

    def __gt__(self, other: Any) -> Any:
        result = self._compare(other)
        return NotImplemented if result is NotImplemented else result > 0

    def __ge__(self, other: Any) -> Any:
        result = self._compare(other)
        return NotImplemented if result is NotImplemented else result >= 0

    def __repr__(self) -> str:
        return f"LogLevel({self.name!r})"


# The named levels are real instances rather than plain strings, so that
# ``LogLevel.WARN < LogLevel.ERROR`` orders by severity instead of alphabetically.
# Assigning them after the class body is the only way to construct instances of
# the class being defined.
LogLevel.ERROR = LogLevel(ERROR)  # type: ignore[attr-defined]
LogLevel.WARN = LogLevel(WARN)  # type: ignore[attr-defined]
LogLevel.INFO = LogLevel(INFO)  # type: ignore[attr-defined]
LogLevel.DEBUG = LogLevel(DEBUG)  # type: ignore[attr-defined]
LogLevel.TRACE = LogLevel(TRACE)  # type: ignore[attr-defined]


_SHORT: dict[str, str] = {
    ERROR: "ERR",
    WARN: "WARN",
    INFO: "INFO",
    DEBUG: "DBG",
    TRACE: "TRACE",
}

_COLOR: dict[str, str] = {
    ERROR: "\x1b[1;31m",
    WARN: "\x1b[1;33m",
    INFO: "\x1b[1;32m",
    DEBUG: "\x1b[36m",
    TRACE: "\x1b[90m",
}

_RESET = "\x1b[0m"


def resolve_level(level: Any) -> str:
    """Normalise a level, alias, or :class:`LogLevel` to a canonical name.

    Args:
        level: A level name, an alias such as ``"warning"``, or a
            :class:`LogLevel`.

    Returns:
        str: One of :data:`LOG_LEVELS`.

    Raises:
        ValueError: If the level cannot be resolved.

    Example:
        >>> resolve_level("warning")
        'WARN'
        >>> resolve_level(LogLevel.INFO)
        'INFO'
    """
    key = str(level).strip().upper()
    if key in LOG_LEVELS:
        return key
    try:
        return _ALIASES[key.lower()]
    except KeyError:
        raise ValueError(
            f"unknown log level {level!r}; expected one of {', '.join(LOG_LEVELS)}"
        ) from None


def level_rank(level: Any) -> int:
    """Return the verbosity rank of a level.

    Args:
        level: A level name or :class:`LogLevel`.

    Returns:
        int: ``0`` for ERROR through ``4`` for TRACE.

    Example:
        >>> level_rank("dbg")
        3
    """
    return LOG_LEVELS.index(resolve_level(level))


__all__ = [
    "DEBUG",
    "ERROR",
    "INFO",
    "LOG_LEVELS",
    "TRACE",
    "WARN",
    "LogLevel",
    "level_rank",
    "resolve_level",
]
