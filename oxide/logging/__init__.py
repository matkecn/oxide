"""Logging subpackage — console output, the standard streams, and loggers.

Three layers, from simplest to most configurable:

1. **Functions.** :func:`println` and :func:`eprintln` for direct console output,
   matching Rust's ``println!`` and ``eprintln!``. :func:`print_` and
   :func:`eprint_` are the same without the newline. Every name that would
   shadow a builtin carries a trailing underscore, following the convention
   already used by ``assert_`` and ``dbg_`` elsewhere in the library.

2. **Streams.** :func:`stdin`, :func:`stdout`, and :func:`stderr` return handles
   on the process's standard streams, for buffered writes and line-oriented
   reads. Each returns the same object on every call.

3. **Loggers.** :class:`Logger` pairs a name with a level threshold and a sink.
   The module-level :func:`log_info` and friends route to a default logger, so
   most programs never construct one.

The top-level names are prefixed to stay unambiguous: ``log_info`` rather than
``info`` (which :mod:`oxide.core.traits` already owns), and ``log_warn`` rather
than ``warn`` (which :mod:`oxide.derive` already owns). The unprefixed spellings
live in this namespace, where they read better:
``from oxide.logging import warn, error, trace``.

Example:
    >>> from oxide.logging import Logger, MemorySink, println, log_info
    >>> println("starting")
    starting
    >>> sink = MemorySink()
    >>> _ = set_default_logger(Logger("oxide", sink=sink))
    >>> log_info("listening on {port}", port=8080)
    True
    >>> sink.messages()
    ['listening on 8080']
    >>> _ = set_default_logger(None)
"""

from __future__ import annotations

from .console import (
    Stderr,
    Stdin,
    Stdout,
    capture,
    color_enabled,
    eprint_,
    eprintln,
    print_,
    println,
    set_color,
    set_stderr,
    set_stdin,
    set_stdout,
    stdin,
    stderr,
    stdout,
    style,
)
from .level import (
    DEBUG,
    ERROR,
    INFO,
    LOG_LEVELS,
    TRACE,
    WARN,
    LogLevel,
    level_rank,
    resolve_level,
)
from .logger import (
    DEFAULT_LEVEL,
    DEFAULT_TARGET,
    LogRecord,
    Logger,
    MemorySink,
    Sink,
    console_sink,
    default_logger,
    enabled_levels,
    levels,
    log,
    log_at_level,
    log_debug,
    log_error,
    log_info,
    log_trace,
    log_warn,
    set_default_logger,
    set_level,
)

# Unprefixed severity shorthands. These shadow nothing inside this namespace but
# are deliberately *not* re-exported from the ``oxide`` top level, where the
# ``log_``-prefixed names above take their place.
trace = log_trace
debug = log_debug
info = log_info
warn = log_warn
error = log_error

__all__ = [
    # console
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
    # levels
    "DEBUG",
    "ERROR",
    "INFO",
    "LOG_LEVELS",
    "TRACE",
    "WARN",
    "LogLevel",
    "level_rank",
    "resolve_level",
    # logger
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
    # namespace-local severity shorthands
    "debug",
    "error",
    "info",
    "trace",
    "warn",
]
