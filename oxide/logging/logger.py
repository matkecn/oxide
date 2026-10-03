"""Structured logging, in the shape of Rust's ``log`` and ``tracing`` crates.

A :class:`Logger` owns a name, a minimum level, and a sink. The module-level
functions route to a default logger, so ``log_warn("disk almost full")`` is all
most programs need:

    >>> from oxide.logging import Logger, MemorySink, log_info, set_default_logger
    >>> sink = MemorySink()
    >>> set_default_logger(Logger("worker", sink=sink))
    Logger('worker', level='INFO', enabled)
    >>> log_info("started")
    True
    >>> sink.messages()
    ['started']
    >>> _ = set_default_logger(None)

Sinks are callables taking ``(level, target, message)``. Passing ``sink=None``
builds a console sink that writes to standard error, matching Rust's convention
of keeping diagnostics off standard output. :class:`MemorySink` captures records
in memory for tests.

Example:
    >>> from oxide.logging import MemorySink
    >>> sink = MemorySink()
    >>> log = Logger("app", sink=sink)
    >>> log.warn("disk almost full")
    True
    >>> log.debug("cache size {n}", n=4)
    False
    >>> sink.messages()
    ['disk almost full']
    >>> sink.levels()
    ['WARN']
    >>> sink.records()[0].message
    'disk almost full'
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Iterable, Sequence

from .console import Stderr, Stdout, color_enabled, eprint_
from .level import DEBUG, ERROR, INFO, LOG_LEVELS, TRACE, WARN, LogLevel, resolve_level

#: The type of a sink: called with ``(level, target, message)``.
Sink = Callable[[LogLevel, str, str], Any]

DEFAULT_LEVEL = INFO
DEFAULT_TARGET = "oxide"


class LogRecord:
    """One captured log event.

    Attributes:
        level (LogLevel): The severity the event was reported at.
        target (str): The logger name that emitted it.
        message (str): The rendered message.
        timestamp (float): Time since the epoch when the record was created.

    Example:
        >>> record = LogRecord(LogLevel.WARN, "app", "careful", 0.0)
        >>> str(record)
        'WARN app: careful'
    """

    __slots__ = ("level", "target", "message", "timestamp")

    def __init__(self, level: Any, target: str, message: str,
                 timestamp: float | None = None) -> None:
        """Create a record.

        Args:
            level: The severity, as a name or :class:`LogLevel`.
            target: The logger name.
            message: The rendered message.
            timestamp: Time since the epoch. Defaults to now.
        """
        self.level = LogLevel(resolve_level(level))
        self.target = target
        self.message = message
        self.timestamp = time.time() if timestamp is None else timestamp

    def __str__(self) -> str:
        return f"{self.level.short} {self.target}: {self.message}"

    def __repr__(self) -> str:
        return f"LogRecord({self.level.name!r}, {self.target!r}, {self.message!r})"

    def to_dict(self) -> dict[str, Any]:
        """Return the record as a plain dictionary.

        Returns:
            dict: Keys ``level``, ``target``, ``message``, and ``timestamp``.

        Example:
            >>> LogRecord("info", "app", "up", 0.0).to_dict()["level"]
            'INFO'
        """
        return {
            "level": self.level.name,
            "target": self.target,
            "message": self.message,
            "timestamp": self.timestamp,
        }


class MemorySink:
    """A sink that keeps records in memory, for tests and diagnostics.

    Example:
        >>> from oxide.logging import LogLevel, MemorySink
        >>> sink = MemorySink()
        >>> sink(LogLevel.ERROR, "app", "boom")
        >>> sink.messages()
        ['boom']
    """

    __slots__ = ("_records", "_lock")

    def __init__(self) -> None:
        """Create an empty sink."""
        self._records: list[LogRecord] = []
        self._lock = threading.Lock()

    def __call__(self, level: LogLevel, target: str, message: str) -> None:
        """Record one event.

        Args:
            level: The severity.
            target: The logger name.
            message: The rendered message.
        """
        with self._lock:
            self._records.append(LogRecord(level, target, message))

    def records(self) -> list[LogRecord]:
        """Return a copy of every record captured so far.

        Returns:
            list[LogRecord]: The records, oldest first.
        """
        with self._lock:
            return list(self._records)

    def messages(self) -> list[str]:
        """Return just the messages of every captured record.

        Returns:
            list[str]: The messages, oldest first.
        """
        return [record.message for record in self.records()]

    def levels(self) -> list[str]:
        """Return just the level names of every captured record.

        Returns:
            list[str]: The level names, oldest first.
        """
        return [record.level.name for record in self.records()]

    def clear(self) -> None:
        """Discard every captured record."""
        with self._lock:
            self._records.clear()

    def __len__(self) -> int:
        return len(self._records)

    def __repr__(self) -> str:
        return f"MemorySink({len(self)} records)"


def console_sink(
    stream: Stderr | Stdout | None = None,
    *,
    color: bool | None = None,
    format_: str = "{level} {target}: {message}",
) -> Sink:
    """Build a sink that writes formatted lines to a console stream.

    Args:
        stream: The destination. Defaults to standard error, keeping diagnostics
            out of program output.
        color: Force colour on or off. None auto-detects.
        format_: A template accepting ``level``, ``target``, and ``message``.

    Returns:
        Sink: A callable suitable for :class:`Logger`.

    Example:
        >>> from io import StringIO
        >>> from oxide.logging import Stdout
        >>> buffer = StringIO()
        >>> sink = console_sink(Stdout(buffer))
        >>> from oxide.logging import LogLevel
        >>> sink(LogLevel.INFO, "app", "ready")
        >>> buffer.getvalue()
        'INFO app: ready\\n'
    """
    destination = stream if stream is not None else None

    def sink(level: LogLevel, target: str, message: str) -> None:
        """Format and write one record.

        Args:
            level: The severity.
            target: The logger name.
            message: The rendered message.
        """
        line = format_.format(level=level.name, target=target, message=message)
        if color is None:
            use_color = color_enabled()
        else:
            use_color = color
        if use_color:
            from .level import _RESET

            line = f"{level.color}{line}{_RESET}"
        if destination is not None:
            destination.print(line)
        else:
            eprint_(line)

    return sink


class Logger:
    """A named logger with a level threshold and a pluggable sink.

    Loggers nest with :meth:`child`, so a subsystem can inherit its parent's
    configuration and add to the target name without repeating the level or the
    sink.

    Example:
>>> from oxide.logging import Logger, MemorySink
    >>> sink = MemorySink()
    >>> root = Logger("app", sink=sink, level="info")
    >>> db = root.child("db")
    >>> db.info("connected")
    True
    >>> sink.messages()
    ['connected']
    >>> [record.target for record in sink.records()]
    ['app.db']
        >>> [record.target for record in sink.records()]
        ['app.db']
        >>> db.level_name
        'INFO'
    """

    __slots__ = ("_target", "_level", "_sink", "_parent", "_lock", "_enabled")

    def __init__(
        self,
        target: str = DEFAULT_TARGET,
        *,
        sink: Sink | None = None,
        level: Any = None,
        parent: "Logger | None" = None,
        enabled: bool = True,
    ) -> None:
        """Create a logger.

        Args:
            target: The logger name, used as the prefix of every record.
            sink: Where records go. ``None`` builds a console sink on standard
                error. When ``parent`` is given and ``sink`` is omitted, the
                parent's sink is inherited.
            level: Minimum severity to emit. Defaults to ``parent``'s level,
                then ``INFO``.
            parent: A logger to inherit configuration from.
            enabled: When False, every call is a no-op regardless of level.

        Raises:
            ValueError: If ``level`` cannot be resolved.
        """
        self._parent = parent
        self._target = f"{parent.target}.{target}" if parent is not None else target
        self._level = LogLevel(resolve_level(level if level is not None
                                             else (parent.level if parent else DEFAULT_LEVEL)))
        if sink is not None:
            self._sink: Sink = sink
        elif parent is not None:
            self._sink = parent._sink
        else:
            self._sink = console_sink()
        self._lock = threading.Lock()
        self._enabled = enabled

    @property
    def target(self) -> str:
        """Return the logger's full name.

        Returns:
            str: The name including any parent prefixes.
        """
        return self._target

    @property
    def level(self) -> LogLevel:
        """Return the minimum severity this logger emits.

        Returns:
            LogLevel: The current threshold.

        Example:
            >>> Logger("app").level == "INFO"
            True
        """
        return self._level

    @property
    def level_name(self) -> str:
        """Return the minimum severity as a plain name.

        Returns:
            str: One of ``ERROR``, ``WARN``, ``INFO``, ``DEBUG``, ``TRACE``.
        """
        return self._level.name

    @property
    def sink(self) -> Sink:
        """Return the callable records are handed to.

        Returns:
            Sink: The configured sink.
        """
        return self._sink

    @property
    def enabled(self) -> bool:
        """Return whether this logger emits anything at all.

        Returns:
            bool: The current enabled flag.
        """
        return self._enabled

    def set_level(self, level: Any) -> LogLevel:
        """Change the minimum severity.

        Args:
            level: The new threshold.

        Returns:
            LogLevel: The threshold now in effect.

        Example:
            >>> log = Logger("app")
            >>> log.set_level("debug").name
            'DEBUG'
        """
        self._level = LogLevel(resolve_level(level))
        return self._level

    def set_sink(self, sink: Sink | None) -> Sink:
        """Replace the sink.

        Args:
            sink: The new sink, or None to restore a console sink on stderr.

        Returns:
            Sink: The sink now in effect.
        """
        self._sink = sink if sink is not None else console_sink()
        return self._sink

    def set_enabled(self, enabled: bool) -> bool:
        """Turn emission on or off without discarding configuration.

        Args:
            enabled: Whether the logger should emit.

        Returns:
            bool: The flag now in effect.

        Example:
            >>> log = Logger("app")
            >>> log.set_enabled(False)
            False
        """
        self._enabled = enabled
        return self._enabled

    def child(self, target: str, **kwargs: Any) -> "Logger":
        """Create a sub-logger that inherits this logger's configuration.

        Args:
            target: The suffix appended to this logger's name.
            **kwargs: Overrides forwarded to :class:`Logger`.

        Returns:
            Logger: The child logger.

        Example:
            >>> Logger("app").child("db").target
            'app.db'
        """
        return Logger(target, parent=self, **kwargs)

    def enabled_for(self, level: Any) -> bool:
        """Return whether a record at ``level`` would be emitted.

        Args:
            level: The severity to test.

        Returns:
            bool: True when the record would reach the sink.

        Example:
            >>> log = Logger("app", level="warn")
            >>> log.enabled_for("error"), log.enabled_for("debug")
            (True, False)
        """
        resolved = LogLevel(resolve_level(level))
        return self._enabled and resolved.rank <= self._level.rank

    def log(self, level: Any, message: Any, *args: Any, **kwargs: Any) -> bool:
        """Emit a record at an arbitrary level.

        ``args`` and ``kwargs`` are formatted into ``message`` with
        :meth:`str.format` when any are supplied, so log lines are not built
        unless they are emitted.

        Args:
            level: The severity.
            message: The message, or a format template when arguments are given.
            *args: Positional values substituted into ``message``.
            **kwargs: Named values substituted into ``message``.

        Returns:
            bool: True when the record was emitted, False when filtered out.

        Example:
            >>> from oxide.logging import MemorySink
            >>> sink = MemorySink()
            >>> log = Logger("app", sink=sink)
            >>> log.log("info", "loaded {n} rows", n=3)
            True
            >>> log.log("info", "skipped {} rows", 1)
            True
            >>> sink.messages()
            ['loaded 3 rows', 'skipped 1 rows']
        """
        resolved = LogLevel(resolve_level(level))
        if not self.enabled_for(resolved):
            return False
        if args or kwargs:
            text = message.format(*args, **kwargs)
        else:
            text = str(message)
        with self._lock:
            self._sink(resolved, self._target, text)
        return True

    def trace(self, message: Any, *args: Any, **kwargs: Any) -> bool:
        """Emit a TRACE record.

        Args:
            message: The message, or a format template when arguments are given.
            *args: Positional values substituted into ``message``.
            **kwargs: Named values substituted into ``message``.

        Returns:
            bool: True when the record was emitted.
        """
        return self.log(TRACE, message, *args, **kwargs)

    def debug(self, message: Any, *args: Any, **kwargs: Any) -> bool:
        """Emit a DEBUG record.

        Args:
            message: The message, or a format template when arguments are given.
            *args: Positional values substituted into ``message``.
            **kwargs: Named values substituted into ``message``.

        Returns:
            bool: True when the record was emitted.
        """
        return self.log(DEBUG, message, *args, **kwargs)

    def info(self, message: Any, *args: Any, **kwargs: Any) -> bool:
        """Emit an INFO record.

        Args:
            message: The message, or a format template when arguments are given.
            *args: Positional values substituted into ``message``.
            **kwargs: Named values substituted into ``message``.

        Returns:
            bool: True when the record was emitted.
        """
        return self.log(INFO, message, *args, **kwargs)

    def warn(self, message: Any, *args: Any, **kwargs: Any) -> bool:
        """Emit a WARN record.

        Args:
            message: The message, or a format template when arguments are given.
            *args: Positional values substituted into ``message``.
            **kwargs: Named values substituted into ``message``.

        Returns:
            bool: True when the record was emitted.
        """
        return self.log(WARN, message, *args, **kwargs)

    def error(self, message: Any, *args: Any, **kwargs: Any) -> bool:
        """Emit an ERROR record.

        Args:
            message: The message, or a format template when arguments are given.
            *args: Positional values substituted into ``message``.
            **kwargs: Named values substituted into ``message``.

        Returns:
            bool: True when the record was emitted.
        """
        return self.log(ERROR, message, *args, **kwargs)

    def records(self) -> list[LogRecord]:
        """Return the records captured by this logger's sink, if any.

        Returns:
            list[LogRecord]: Captured records. Empty when the sink is not a
            :class:`MemorySink`.
        """
        capture = getattr(self._sink, "records", None)
        return capture() if callable(capture) else []

    def __repr__(self) -> str:
        state = "enabled" if self._enabled else "disabled"
        return f"Logger({self._target!r}, level={self._level.name!r}, {state})"


_default_logger = Logger(DEFAULT_TARGET)


def default_logger() -> Logger:
    """Return the logger the module-level functions route to.

    Returns:
        Logger: The current default logger.

    Example:
        >>> from oxide.logging import Logger, MemorySink, set_default_logger
        >>> previous = set_default_logger(Logger("probe"))
        >>> default_logger().target
        'probe'
        >>> _ = set_default_logger(previous)
    """
    return _default_logger


def set_default_logger(logger: Logger | None) -> Logger:
    """Replace the default logger used by the module-level functions.

    Args:
        logger: The new default, or None to rebuild a fresh console logger.

    Returns:
        Logger: The default now in effect.

    Example:
        >>> probe = Logger("probe", sink=MemorySink())
        >>> set_default_logger(probe)
        Logger('probe', level='INFO', enabled)
        >>> set_default_logger(None)
        Logger('oxide', level='INFO', enabled)
    """
    global _default_logger
    _default_logger = logger if logger is not None else Logger(DEFAULT_TARGET)
    return _default_logger


def set_level(level: Any) -> LogLevel:
    """Set the minimum severity on the default logger.

    Args:
        level: The new threshold.

    Returns:
        LogLevel: The threshold now in effect.

    Example:
        >>> previous = set_level("debug")
        >>> set_level("info")
        LogLevel('INFO')
    """
    return _default_logger.set_level(level)


def log_at_level(level: Any) -> Callable[..., bool]:
    """Build a logging function bound to one level on the default logger.

    This is how :func:`oxide.derive.log_calls` resolves its ``level`` argument
    without importing the whole module at definition time.

    Args:
        level: The severity to log at.

    Returns:
        Callable: A function taking ``(message, *args)`` and returning whether
        the record was emitted.

    Example:
        >>> warn = log_at_level("warn")
        >>> callable(warn)
        True
    """
    resolved = resolve_level(level)

    def emit(message: Any, *args: Any) -> bool:
        """Emit one record on the default logger.

        Args:
            message: The message, or a format template when ``args`` are given.
            *args: Values substituted into ``message``.

        Returns:
            bool: True when the record was emitted.
        """
        return _default_logger.log(resolved, message, *args, **kwargs)

    emit.__name__ = f"log_{resolved.lower()}"
    return emit


def log(level: Any, message: Any, *args: Any, **kwargs: Any) -> bool:
    """Emit a record on the default logger at an arbitrary level.

    Args:
        level: The severity.
        message: The message, or a format template when ``args`` are given.
        *args: Values substituted into ``message``.

    Returns:
        bool: True when the record was emitted.

    Example:
        >>> sink = MemorySink()
        >>> _ = set_default_logger(Logger("app", sink=sink))
        >>> log("info", "ready in {ms}ms", ms=12)
        True
        >>> sink.messages()
        ['ready in 12ms']
        >>> _ = set_default_logger(None)
    """
    return _default_logger.log(level, message, *args, **kwargs)


def log_trace(message: Any, *args: Any, **kwargs: Any) -> bool:
    """Emit a TRACE record on the default logger.

    Args:
        message: The message, or a format template when ``args`` are given.
        *args: Values substituted into ``message``.

    Returns:
        bool: True when the record was emitted.
    """
    return _default_logger.trace(message, *args, **kwargs)


def log_debug(message: Any, *args: Any, **kwargs: Any) -> bool:
    """Emit a DEBUG record on the default logger.

    Args:
        message: The message, or a format template when ``args`` are given.
        *args: Values substituted into ``message``.

    Returns:
        bool: True when the record was emitted.

    Example:
        >>> from oxide.logging import Logger, MemorySink, set_default_logger
        >>> previous = set_default_logger(Logger("t", sink=MemorySink()))
        >>> log_debug("cache size {n}", n=4)
        False
        >>> _ = set_default_logger(previous)
    """
    return _default_logger.debug(message, *args, **kwargs)


def log_info(message: Any, *args: Any, **kwargs: Any) -> bool:
    """Emit an INFO record on the default logger.

    Args:
        message: The message, or a format template when ``args`` are given.
        *args: Values substituted into ``message``.

    Returns:
        bool: True when the record was emitted.
    """
    return _default_logger.info(message, *args, **kwargs)


def log_warn(message: Any, *args: Any, **kwargs: Any) -> bool:
    """Emit a WARN record on the default logger.

    Args:
        message: The message, or a format template when ``args`` are given.
        *args: Values substituted into ``message``.

    Returns:
        bool: True when the record was emitted.

    Example:
        >>> from oxide.logging import Logger, MemorySink, set_default_logger
        >>> sink = MemorySink()
        >>> previous = set_default_logger(Logger("t", sink=sink))
        >>> log_warn("retrying {n}/{total}", n=1, total=3)
        True
        >>> sink.messages()
        ['retrying 1/3']
        >>> _ = set_default_logger(previous)
    """
    return _default_logger.warn(message, *args, **kwargs)


def log_error(message: Any, *args: Any, **kwargs: Any) -> bool:
    """Emit an ERROR record on the default logger.

    Args:
        message: The message, or a format template when ``args`` are given.
        *args: Values substituted into ``message``.

    Returns:
        bool: True when the record was emitted.
    """
    return _default_logger.error(message, *args, **kwargs)


def levels() -> Sequence[str]:
    """Return every level name, from least to most verbose.

    Returns:
        Sequence[str]: The level names.

    Example:
        >>> list(levels())
        ['ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE']
    """
    return LOG_LEVELS


def enabled_levels(level: Any = None) -> Iterable[str]:
    """Return the level names a threshold would admit.

    Args:
        level: The threshold. Defaults to the default logger's level.

    Returns:
        Iterable[str]: The admitted level names, least to most verbose.

    Example:
        >>> list(enabled_levels("warn"))
        ['ERROR', 'WARN']
    """
    threshold = LogLevel(resolve_level(level if level is not None else _default_logger.level))
    return tuple(name for name in LOG_LEVELS
                 if LogLevel(name).rank <= threshold.rank)


__all__ = [
    "DEFAULT_LEVEL",
    "DEFAULT_TARGET",
    "LogRecord",
    "Logger",
    "MemorySink",
    "Sink",
    "console_sink",
    "default_logger",
    "enabled_levels",
    "levels",
    "log",
    "log_at_level",
    "log_debug",
    "log_error",
    "log_info",
    "log_trace",
    "log_warn",
    "set_default_logger",
    "set_level",
]
