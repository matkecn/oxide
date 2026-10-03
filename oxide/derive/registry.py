"""Lint-level registry backing :mod:`oxide.derive`.

Rust resolves ``#[allow]``, ``#[warn]``, ``#[deny]`` and ``#[forbid]``
attributes against per-lint configuration levels at compile time. Python has no
compile step, so :mod:`oxide.derive` resolves them at call time instead. This
module holds that configuration.

The four levels mirror Rust exactly:

============  ==========================================================
Level         Behaviour
============  ==========================================================
``allow``     The lint is silenced, whatever any decorator asks for.
``warn``      A Python warning is emitted through :mod:`warnings`.
``deny``      A :class:`LintError` is raised.
``forbid``    A :class:`LintError` is raised and the level is capped, so a
              later ``allow`` cannot downgrade it.
============  ==========================================================

Levels can be set globally (:func:`set_lint_level`), per scope
(:func:`lint_scope`), or overridden for a single decorator through its
``level=`` argument.

Example:
    >>> from oxide.derive import set_lint_level, get_lint_level, reset_lints
    >>> set_lint_level("unused_result", "deny")
    'deny'
    >>> get_lint_level("unused_result")
    'deny'
    >>> reset_lints()
"""

from __future__ import annotations

import warnings
from contextlib import contextmanager
from typing import Any, Iterator

ALLOW = "allow"
WARN = "warn"
DENY = "deny"
FORBID = "forbid"

#: Every level, ordered from least to most severe.
LINT_LEVELS: tuple[str, ...] = (ALLOW, WARN, DENY, FORBID)

#: Aliases accepted wherever a level is expected, normalised to a canonical level.
_ALIASES: dict[str, str] = {
    "allow": ALLOW,
    "off": ALLOW,
    "ignore": ALLOW,
    "silent": ALLOW,
    "warn": WARN,
    "warning": WARN,
    "deny": DENY,
    "error": DENY,
    "forbid": FORBID,
}

_levels: dict[str, str] = {}
_caps: dict[str, str] = {}


class LintError(Exception):
    """Raised when a lint configured at ``deny`` or ``forbid`` fires.

    Attributes:
        lint (str): The lint name that fired.
        message (str): The human-readable message.
    """

    __slots__ = ("lint", "message")

    def __init__(self, lint: str, message: str) -> None:
        """Initialise the error.

        Args:
            lint: The lint name that fired.
            message: The human-readable message.
        """
        super().__init__(f"{lint}: {message}")
        self.lint = lint
        self.message = message


class LintWarning(UserWarning):
    """Warning category used for lints configured at ``warn``."""

    __slots__ = ("lint", "message")

    def __init__(self, lint: str, message: str) -> None:
        """Initialise the warning.

        Args:
            lint: The lint name that fired.
            message: The human-readable message.
        """
        super().__init__(f"{lint}: {message}")
        self.lint = lint
        self.message = message


def normalize_level(level: Any) -> str:
    """Normalise a level name or alias to one of :data:`LINT_LEVELS`.

    Args:
        level: A level name, alias, or :class:`LintLevel`.

    Returns:
        str: One of ``allow``, ``warn``, ``deny``, ``forbid``.

    Raises:
        ValueError: If the level is not recognised.

    Example:
        >>> normalize_level("warning")
        'warn'
    """
    key = str(level).strip().lower()
    try:
        return _ALIASES[key]
    except KeyError:
        raise ValueError(
            f"unknown lint level {level!r}; expected one of {', '.join(LINT_LEVELS)}"
        ) from None


def set_lint_level(lint: str, level: Any) -> str:
    """Configure the level of a lint globally.

    Args:
        lint: The lint name, such as ``"unused_result"``.
        level: The level to apply, normalised through :func:`normalize_level`.

    Returns:
        str: The normalised level that was stored.

    Raises:
        LintError: If the lint is already ``forbid`` and cannot be lowered.

    Example:
        >>> set_lint_level("unused_variable", "warn")
        'warn'
    """
    canonical = normalize_level(level)
    if _caps.get(lint) == FORBID and canonical != FORBID:
        raise LintError(lint, "lint was configured to forbid and cannot be lowered")
    _levels[lint] = canonical
    return canonical


def get_lint_level(lint: str) -> str:
    """Return the effective level of a lint.

    A lint that has never been configured resolves to ``warn``, matching Rust's
    default for most built-in lints.

    Args:
        lint: The lint name.

    Returns:
        str: One of :data:`LINT_LEVELS`.

    Example:
        >>> get_lint_level("never_configured")
        'warn'
    """
    return _levels.get(lint, WARN)


def lint_levels() -> dict[str, str]:
    """Return a snapshot of every explicitly configured lint.

    Returns:
        dict: Mapping of lint name to level, for lints set via
        :func:`set_lint_level` or a ``forbid`` cap only.
    """
    snapshot = dict(_levels)
    for lint, cap in _caps.items():
        if cap == FORBID:
            snapshot[lint] = FORBID
    return snapshot


def reset_lints() -> None:
    """Forget every lint level and cap.

    Example:
        >>> set_lint_level("demo", "deny")
        'deny'
        >>> _ = reset_lints()
        >>> get_lint_level("demo")
        'warn'
    """
    _levels.clear()
    _caps.clear()


def forbid(lint: str) -> str:
    """Cap a lint at ``forbid`` so it can never be downgraded again.

    Args:
        lint: The lint name.

    Returns:
        str: ``"forbid"``.

    Example:
        >>> forbid("legacy_api")
        'forbid'
        >>> reset_lints()
    """
    _levels[lint] = FORBID
    _caps[lint] = FORBID
    return FORBID


@contextmanager
def lint_scope(**levels: Any) -> Iterator[None]:
    """Temporarily override lint levels inside a ``with`` block.

    Levels given as keyword arguments are restored on exit, even if the block
    raises. Keyword names are the lint names, so hyphens must be written as
    underscores.

    Args:
        **levels: Lint name to level.

    Yields:
        None: Control returns to the caller with the overrides in place.

    Example:
        >>> with lint_scope(unused_result="allow"):
        ...     get_lint_level("unused_result")
        'allow'
    """
    previous = {name: _levels.get(name) for name in levels}
    try:
        for name, level in levels.items():
            canonical = normalize_level(level)
            if _caps.get(name) == FORBID and canonical != FORBID:
                raise LintError(name, "lint was configured to forbid and cannot be lowered")
            _levels[name] = canonical
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                _levels.pop(name, None)
            else:
                _levels[name] = value


def resolve(lint: str, requested: Any, message: str, stacklevel: int = 3) -> str:
    """Resolve one lint occurrence against the current configuration and act.

    This is the single place where a lint actually has an effect. The requested
    level acts as a *floor*: a decorator asking for ``warn`` cannot silence a
    lint the project has configured as ``deny``.

    Args:
        lint: The lint name.
        requested: The level requested by the decorator.
        message: The message to report.
        stacklevel: How many frames to skip when reporting, so the warning
            points at the user's call site rather than at oxide internals.

    Returns:
        str: The level that was actually applied — ``allow`` when silenced,
        ``warn`` when a warning was emitted, otherwise the raising level.

    Raises:
        LintError: If the effective level is ``deny`` or ``forbid``.

    Example:
        >>> from oxide.derive import set_lint_level, reset_lints
        >>> _ = set_lint_level("quiet_lint", "allow")
        >>> resolve("quiet_lint", "allow", "never mind")
        'allow'
        >>> import warnings
        >>> _ = set_lint_level("noisy_lint", "warn")
        >>> with warnings.catch_warnings(record=True) as caught:
        ...     warnings.simplefilter("always")
        ...     _ = resolve("noisy_lint", "allow", "hmm")
        ...     len(caught)
        1
        >>> _ = set_lint_level("fatal_lint", "deny")
        >>> resolve("fatal_lint", "warn", "stop")
        Traceback (most recent call last):
            ...
        oxide.derive.registry.LintError: fatal_lint: stop
        >>> _ = reset_lints()
    """
    requested_level = normalize_level(requested)
    configured = get_lint_level(lint)

    order = {ALLOW: 0, WARN: 1, DENY: 2, FORBID: 3}
    effective = requested_level if order[requested_level] > order[configured] else configured

    if effective == ALLOW:
        return ALLOW
    if effective == WARN:
        warnings.warn(LintWarning(lint, message), stacklevel=stacklevel)
        return WARN
    raise LintError(lint, message)


class LintLevel(str):
    """A string enum of lint levels, usable wherever a level name is expected.

    Inherits from :class:`str`, so ``LintLevel.WARN == "warn"`` holds and
    instances work anywhere a plain level string is accepted.

    Example:
        >>> LintLevel("deny").name
        'deny'
        >>> LintLevel.WARN == "warn"
        True
    """

    __slots__ = ()

    @property
    def name(self) -> str:
        """Return the canonical level name.

        Returns:
            str: One of ``allow``, ``warn``, ``deny``, ``forbid``.
        """
        return normalize_level(self)

    def is_at_least(self, level: Any) -> bool:
        """Return whether this level is as severe as or more severe than ``level``.

        Args:
            level: The level to compare against.

        Returns:
            bool: True when this level's severity is greater or equal.

        Example:
            >>> LintLevel.DENY.is_at_least("warn")
            True
        """
        order = {ALLOW: 0, WARN: 1, DENY: 2, FORBID: 3}
        return order[self.name] >= order[normalize_level(level)]

    def __repr__(self) -> str:
        return f"LintLevel({self.name!r})"


# The named levels are real instances rather than plain strings, so that
# ``LintLevel.DENY.is_at_least("warn")`` works. Assigning them after the class
# body is the only way to construct instances of the class being defined.
LintLevel.ALLOW = LintLevel(ALLOW)  # type: ignore[attr-defined]
LintLevel.WARN = LintLevel(WARN)  # type: ignore[attr-defined]
LintLevel.DENY = LintLevel(DENY)  # type: ignore[attr-defined]
LintLevel.FORBID = LintLevel(FORBID)  # type: ignore[attr-defined]


__all__ = [
    "ALLOW",
    "WARN",
    "DENY",
    "FORBID",
    "LINT_LEVELS",
    "LintError",
    "LintLevel",
    "LintWarning",
    "forbid",
    "get_lint_level",
    "lint_levels",
    "lint_scope",
    "normalize_level",
    "reset_lints",
    "resolve",
    "set_lint_level",
]
