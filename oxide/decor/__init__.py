"""The ``decor`` subpackage — every Rust decorator in one namespace.

Rust decorates items with attributes: ``#[derive(Clone)]``,
``#[inline(always)]``, ``#[cfg(feature = "x")]``, ``#[deprecated]``,
``#[tokio::main]``, ``#[test]``. They are spread across the language, the
standard library, and a pile of procedural-macro crates, so knowing which one
does what means knowing which crate it came from.

This package gathers them behind one import. It is a facade: the attribute
machinery lives in :mod:`oxide.derive`, and the item-level and test-harness
attributes Rust adds on top live in :mod:`oxide.decor.items`. Nothing is
reimplemented here, so ``oxide.decor.derive`` and ``oxide.derive.derive`` are
the same object.

Three groups:

**Type-level attributes** come from :mod:`oxide.derive` — ``derive`` for the
eleven standard traits, the ``allow``/``warn``/``deny``/``forbid`` lint levels,
``cfg``, ``deprecated``, ``must_use``, ``inline``, ``non_exhaustive``,
``export_name``, ``doc``, and the runtime instrumentation ``memoize``, ``once``,
``pure``, ``timed``, and ``log_calls``.

**Item attributes** come from :mod:`oxide.decor.items` — the codegen and
symbol hints ``no_mangle``, ``used``, ``cold``, ``naked``, ``link``,
``link_name``, ``crate_type``, ``crate_name``, ``path``, and ``repr_``. These
are metadata in Python, as they are in Rust: they cannot change what CPython
generates, so they record intent and read back through
:func:`~oxide.derive.attributes.attributes_of`.

**Test attributes** — ``test``, ``bench``, ``ignore``, ``should_panic``, and
``serial`` — are emulated for real. :func:`run_tests` executes everything marked
``#[test]`` in the calling module and honours the rest.

Plus :func:`masterclass`, which has no Rust spelling: the combination of
``classmethod`` and ``staticmethod``, binding the class always and the instance
when one is reachable.

Example:
    >>> from oxide.decor import test, run_tests
    >>> @test
    ... def test_adding():
    ...     assert 1 + 1 == 2
    >>> @test
    ... def test_multiplying():
    ...     assert 2 * 3 == 6
    >>> result = run_tests()
    >>> result.passed, result.failed
    (('test_adding', 'test_multiplying'), ())

    >>> from oxide.decor import masterclass
    >>> class Config:
    ...     def __init__(self, value):
    ...         self.value = value
    ...     @masterclass
    ...     def describe(cls, self):
    ...         if self is None:
    ...             return f"{cls.__name__} describes itself"
    ...         return f"{cls.__name__} holds {self.value!r}"
    >>> Config(7).describe()
    'Config holds 7'
    >>> Config.describe()
    'Config describes itself'

Inside this namespace the plain Rust spellings are available — ``warn``,
``inline``, ``cfg``, ``test`` — because nothing here collides with a builtin. At
the top level of the ``oxide`` package the colliding names are disambiguated
instead: ``lint_warn`` for the lint decorators, ``derive_`` so
``oxide.derive`` keeps naming the subpackage, ``cfg_`` for ``cfg``, and
``masterclass`` unchanged.
"""

from __future__ import annotations

from ..derive import (
    ALLOW,
    ATTRIBUTES,
    DENY,
    DEPRECATED_LINT,
    DEPRECATION_CATEGORY,
    DERIVE_ALIASES,
    ENABLED_FEATURES,
    FORBID,
    LINT_LEVELS,
    MUST_USE_LINT,
    SUPPORTED_DERIVES,
    WARN,
    CacheInfo,
    DeriveError,
    FeatureDisabledError,
    LintError,
    LintLevel,
    LintWarning,
    allow,
    attributes_of,
    cap_lint,
    cfg,
    deny,
    deprecated,
    doc,
    derive,
    derive_fields,
    derives_of,
    enable_feature,
    export_name,
    find_attribute,
    forbid,
    get_lint_level,
    inline,
    is_derived,
    is_non_exhaustive,
    lint_allow,
    lint_deny,
    lint_forbid,
    lint_levels,
    lint_scope,
    lint_warn,
    log_calls,
    memoize,
    must_use,
    non_exhaustive,
    normalize_level,
    once,
    pure,
    reset_features,
    reset_lints,
    resolve,
    resolve_derive,
    set_lint_level,
    timed,
    warn,
)
from .items import (
    TestResult,
    bench,
    benches,
    caller_location,
    cold,
    crate_name,
    crate_type,
    ignore,
    ignored_reason,
    is_bench,
    is_ignored,
    is_serial,
    is_test,
    link,
    link_name,
    main,
    naked,
    no_mangle,
    path,
    repr_,
    repr_kinds_of,
    run_tests,
    serial,
    should_panic,
    should_panic_of,
    test,
    tests,
    track_caller,
    used,
)
from .masterclass import MasterMethod, is_master, masterclass

__all__ = [
    # type-level attributes, re-exported from oxide.derive
    "ALLOW",
    "ATTRIBUTES",
    "DENY",
    "DEPRECATED_LINT",
    "DEPRECATION_CATEGORY",
    "DERIVE_ALIASES",
    "ENABLED_FEATURES",
    "FORBID",
    "LINT_LEVELS",
    "MUST_USE_LINT",
    "SUPPORTED_DERIVES",
    "WARN",
    "CacheInfo",
    "DeriveError",
    "FeatureDisabledError",
    "LintError",
    "LintLevel",
    "LintWarning",
    "allow",
    "attributes_of",
    "cap_lint",
    "cfg",
    "deny",
    "deprecated",
    "derive",
    "derive_fields",
    "derives_of",
    "doc",
    "enable_feature",
    "export_name",
    "find_attribute",
    "forbid",
    "get_lint_level",
    "ignore",
    "inline",
    "is_derived",
    "is_non_exhaustive",
    "lint_allow",
    "lint_deny",
    "lint_forbid",
    "lint_levels",
    "lint_scope",
    "lint_warn",
    "log_calls",
    "memoize",
    "must_use",
    "non_exhaustive",
    "normalize_level",
    "once",
    "pure",
    "reset_features",
    "reset_lints",
    "resolve",
    "resolve_derive",
    "set_lint_level",
    "timed",
    "warn",
    # item attributes
    "cold",
    "crate_name",
    "crate_type",
    "link",
    "link_name",
    "main",
    "naked",
    "no_mangle",
    "path",
    "repr_",
    "repr_kinds_of",
    "track_caller",
    "used",
    # test attributes
    "TestResult",
    "bench",
    "benches",
    "ignored_reason",
    "is_bench",
    "is_ignored",
    "is_serial",
    "is_test",
    "run_tests",
    "serial",
    "should_panic",
    "should_panic_of",
    "test",
    "tests",
    # combined class/instance methods
    "MasterMethod",
    "is_master",
    "masterclass",
    # caller tracking
    "caller_location",
]

