"""Derive subpackage — Rust attributes and derive macros as decorators.

Rust leans on two kinds of compile-time annotation:

**Attribute macros** rewrite or annotate an item in place — ``#[warn]``,
``#[deprecated]``, ``#[must_use]``, ``#[cfg]``. :mod:`oxide.derive.attributes`
emulates those as decorators.

**Derive macros** generate boilerplate from a type's fields —
``#[derive(Debug, Clone, PartialEq)]``. :func:`derive` does that too, generating
``__repr__``, ``__eq__``, ``__hash__``, comparison operators, ``clone()``, and
``default()`` from a field list.

On top of that, :mod:`oxide.derive.functions` adds the runtime instrumentation
Rust only expresses as hints: ``memoize``, ``pure``, ``timed``, ``log_calls``,
and ``once``.

Lint levels are configured the Rust way — ``allow``, ``warn``, ``deny``,
``forbid`` — and resolved at call time, since Python has no compile step. Use
:func:`set_lint_level` to raise or lower a lint globally and :func:`lint_scope`
to change it for a block.

Example:
    >>> @derive("Debug", "Clone", "PartialEq", "Default")
    ... class Point:
    ...     __slots__ = ("x", "y")
    ...     def __init__(self, x=0, y=0):
    ...         self.x = x
    ...         self.y = y
    >>> Point(1, 2) == Point(1, 2)
    True
    >>> Point.default()
    Point { x: 0, y: 0 }

At the top level of the ``oxide`` package the lint decorators are exported with a
``lint_`` prefix — ``lint_warn``, ``lint_allow``, ``lint_deny``, ``lint_forbid`` —
so that ``warn`` there stays unambiguous. Inside this namespace the plain Rust
spellings are available: ``from oxide.derive import warn``.
"""

from __future__ import annotations

from .attributes import (
    ATTRIBUTES,
    DEPRECATED_LINT,
    DEPRECATION_CATEGORY,
    ENABLED_FEATURES,
    MUST_USE_LINT,
    FeatureDisabledError,
    allow,
    attributes_of,
    cfg,
    deny,
    deprecated,
    doc,
    enable_feature,
    export_name,
    find_attribute,
    forbid,
    inline,
    is_non_exhaustive,
    lint_allow,
    lint_deny,
    lint_forbid,
    lint_warn,
    must_use,
    non_exhaustive,
    warn,
)
from .derive import (
    DERIVE_ALIASES,
    SUPPORTED_DERIVES,
    DeriveError,
    derive,
    derive_fields,
    derives_of,
    is_derived,
    resolve_derive,
)
from .functions import (
    CacheInfo,
    log_calls,
    memoize,
    once,
    pure,
    timed,
)
from .registry import (
    ALLOW,
    DENY,
    FORBID,
    LINT_LEVELS,
    WARN,
    LintError,
    LintLevel,
    LintWarning,
    forbid as cap_lint,
    get_lint_level,
    lint_levels,
    lint_scope,
    normalize_level,
    reset_lints,
    resolve,
    set_lint_level,
)

__all__ = [
    # attribute macros
    "ATTRIBUTES",
    "DEPRECATED_LINT",
    "DEPRECATION_CATEGORY",
    "ENABLED_FEATURES",
    "MUST_USE_LINT",
    "FeatureDisabledError",
    "allow",
    "attributes_of",
    "cfg",
    "deny",
    "deprecated",
    "doc",
    "enable_feature",
    "export_name",
    "find_attribute",
    "forbid",
    "inline",
    "is_non_exhaustive",
    "lint_allow",
    "lint_deny",
    "lint_forbid",
    "lint_warn",
    "must_use",
    "non_exhaustive",
    "warn",
    # derive macros
    "DERIVE_ALIASES",
    "SUPPORTED_DERIVES",
    "DeriveError",
    "derive",
    "derive_fields",
    "derives_of",
    "is_derived",
    "resolve_derive",
    # function decorators
    "CacheInfo",
    "log_calls",
    "memoize",
    "once",
    "pure",
    "timed",
    # lint configuration
    "ALLOW",
    "DENY",
    "FORBID",
    "LINT_LEVELS",
    "WARN",
    "LintError",
    "LintLevel",
    "LintWarning",
    "cap_lint",
    "get_lint_level",
    "lint_levels",
    "lint_scope",
    "normalize_level",
    "reset_lints",
    "resolve",
    "set_lint_level",
]
