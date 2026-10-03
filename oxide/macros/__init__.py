"""Utility macros: assertions, debugging, panic helpers, and RAII cleanup.

Re-exports the assertion, debugging, and panic macros from the ``macros``
subpackage so they can be imported directly from ``oxide.macros``. Includes
``assert_eq``, ``assert_ne``, ``dbg``, ``format_``, ``panic``, ``todo``,
``unimplemented``, ``ScopeGuard``, ``defer``, and more.

Example:
    >>> from oxide.macros import assert_eq, dbg, defer
    >>> assert_eq(1 + 1, 2)
"""

from __future__ import annotations

from .assertions import assert_eq, assert_ne, assert_, debug_assert, debug_assert_eq, debug_assert_ne, assert_matches, assert_type
from .debugging import Formatter, format_, write_, writeln_, dbg_, dbg, cfg, compile_error, option_env, include_str, include_bytes, matches
from .panic import todo, unimplemented, PanicError, UnimplementedError, panic, panic_fmt, ScopeGuard, defer

__all__ = [
    "assert_eq",
    "assert_ne",
    "assert_",
    "debug_assert",
    "debug_assert_eq",
    "debug_assert_ne",
    "assert_matches",
    "assert_type",
    "Formatter",
    "format_",
    "write_",
    "writeln_",
    "dbg_",
    "dbg",
    "cfg",
    "compile_error",
    "option_env",
    "include_str",
    "include_bytes",
    "matches",
    "todo",
    "unimplemented",
    "PanicError",
    "UnimplementedError",
    "panic",
    "panic_fmt",
    "ScopeGuard",
    "defer",
]
