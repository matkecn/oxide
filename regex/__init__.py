"""``oxide.regex`` — a linear-time regular expression engine.

A dependency-free reimplementation of the regular expression surface offered by
Rust's ``regex`` crate, exposed through an API close enough to Python's ``re``
that the two are interchangeable for supported constructs.

The engine compiles patterns to a Thompson NFA and simulates the resulting state
set with a Pike VM, so matching is ``O(len(text) * len(program))`` for every
pattern. Catastrophic backtracking is impossible by construction rather than
merely unlikely.

Supported: literals, ``.``, character classes with ranges, negation and POSIX
names, ``\\d \\D \\w \\W \\s \\S``, escapes, anchors ``^ $ \\A \\Z \\b \\B``, groups
(plain, non-capturing, and named), alternation, all quantifiers including
``{n,m}`` and every lazy variant, the ``MULTILINE``, ``DOTALL``, ``IGNORECASE``,
``ASCII``, ``UNICODE``, and ``VERBOSE`` flags, and scoped inline flags.

Rejected with a clear :class:`RegexError`: backreferences, lookaround, atomic
groups, possessive quantifiers, and unicode property escapes. Each of these
requires backtracking or unbounded state, so omitting them is what makes the
linear-time guarantee possible. Rust's ``regex`` crate rejects them too.

Example:
    >>> from oxide.regex import compile, findall, IGNORECASE
    >>> findall(r"[a-z]+@[a-z]+\\.[a-z]+", "Ann@Example.COM bob@test", IGNORECASE)
    ['Ann@Example.COM']
    >>> compile("A").search("abc") is None
    True
"""

from __future__ import annotations

from ._syntax import ASCII, DOTALL, IGNORECASE, MULTILINE, UNICODE, VERBOSE
from ._syntax import RegexError as RegexError
from .api import (
    Match, Regex, compile, escape, findall, finditer, fullmatch, match, purge,
    search, split, sub, subn,
)

error = RegexError

A = ASCII
I = IGNORECASE
M = MULTILINE
S = DOTALL
U = UNICODE
X = VERBOSE

__all__ = [
    "Regex",
    "Match",
    "RegexError",
    "error",
    "compile",
    "match",
    "fullmatch",
    "search",
    "findall",
    "finditer",
    "split",
    "sub",
    "subn",
    "escape",
    "purge",
    "ASCII",
    "IGNORECASE",
    "MULTILINE",
    "DOTALL",
    "UNICODE",
    "VERBOSE",
    "A",
    "I",
    "M",
    "S",
    "U",
    "X",
]