"""Rust attribute macros as Python decorators.

Each decorator here mirrors an attribute macro from the Rust reference:

===========================  ==================================================
Decorator                    Rust equivalent
===========================  ==================================================
:func:`allow`                ``#[allow(lint)]``
:func:`warn`                 ``#[warn(lint)]``
:func:`deny`                 ``#[deny(lint)]``
:func:`forbid`               ``#[forbid(lint)]``
:func:`deprecated`           ``#[deprecated]``
:func:`must_use`             ``#[must_use]``
:func:`inline`               ``#[inline]``
:func:`non_exhaustive`       ``#[non_exhaustive]``
:func:`export_name`          ``#[export_name = "..."]``
:func:`cfg`                  ``#[cfg(...)]``
:func:`doc`                  ``///`` doc comments
===========================  ==================================================

Attributes are recorded on the decorated object under
:data:`ATTRIBUTES` so they can be read back at runtime with
:func:`attributes_of` and :func:`find_attribute`, which is how Rust tooling
inspects its own metadata.

Where Rust's compiler can enforce an attribute, the decorator enforces it too:
:func:`deny` raises, :func:`deprecated` emits a real
:class:`DeprecationWarning`, and :func:`cfg` replaces the object with a stub
that refuses to run. Where the compiler is the only thing that could enforce it
— inlining, in particular — the attribute is recorded as metadata and costs
nothing at runtime.

Example:
    >>> @deprecated("use Option::unwrap_or instead")
    ... def old_api():
    ...     return 1
    >>> import warnings
    >>> with warnings.catch_warnings(record=True) as caught:
    ...     warnings.simplefilter("always")
    ...     old_api()
    1
    >>> caught[0].category.__name__
    'DeprecationWarning'
"""

from __future__ import annotations

import functools
import warnings
from typing import Any, Callable, TypeVar

from .registry import (
    ALLOW,
    DENY,
    FORBID,
    WARN,
    LintError,
    forbid as _cap_lint,
    normalize_level,
    resolve,
)

F = TypeVar("F", bound=Callable[..., Any])

#: Key under which recorded attributes live on a decorated object.
ATTRIBUTES = "__oxide_attributes__"

#: Warning category emitted by :func:`deprecated`.
DEPRECATION_CATEGORY = DeprecationWarning

#: Default lint name used by :func:`must_use`.
MUST_USE_LINT = "unused_result"

#: Default lint name used by :func:`deprecated`.
DEPRECATED_LINT = "deprecated"


class FeatureDisabledError(RuntimeError):
    """Raised when a ``cfg``-gated object is used in a disabled configuration.

    This is the Python analogue of "this item was compiled out": the object
    still exists so imports keep working, but calling it is an error.

    Attributes:
        condition (str): The ``cfg`` condition that did not hold.
    """

    __slots__ = ("condition",)

    def __init__(self, condition: str) -> None:
        """Initialise the error.

        Args:
            condition: The ``cfg`` condition that evaluated false.
        """
        super().__init__(f"item was compiled out by cfg({condition})")
        self.condition = condition


class _MustUse:
    """Transparent proxy that reports a return value that was discarded unread.

    Wrapping a value in this proxy preserves attribute access, iteration,
    indexing, truth tests, equality, and formatting, so ordinary code behaves
    normally. The proxy counts itself used on any of those and reports the
    unused result from ``__del__`` if it is collected while still unread.
    """

    __slots__ = ("_value", "_message", "_lint", "_level", "_used", "_consumed")

    def __init__(self, value: Any, message: str, lint: str, level: str) -> None:
        """Wrap a value.

        Args:
            value: The value to wrap.
            message: Message used if the value is discarded.
            lint: Lint name to report under.
            level: Level requested by the caller.
        """
        object.__setattr__(self, "_value", value)
        object.__setattr__(self, "_message", message)
        object.__setattr__(self, "_lint", lint)
        object.__setattr__(self, "_level", level)
        object.__setattr__(self, "_used", False)
        object.__setattr__(self, "_consumed", False)

    def _touch(self) -> None:
        object.__setattr__(self, "_used", True)

    def _value_of(self) -> Any:
        self._touch()
        return object.__getattribute__(self, "_value")

    @property
    def value(self) -> Any:
        """Return the wrapped value, marking it used.

        Returns:
            Any: The value the wrapped callable returned.
        """
        self._touch()
        object.__setattr__(self, "_consumed", True)
        return object.__getattribute__(self, "_value")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._value_of(), name)

    def __iter__(self):
        self._touch()
        return iter(object.__getattribute__(self, "_value"))

    def __next__(self):
        self._touch()
        return next(object.__getattribute__(self, "_value"))

    def __len__(self) -> int:
        self._touch()
        return len(object.__getattribute__(self, "_value"))

    def __getitem__(self, key: Any) -> Any:
        return self._value_of()[key]

    def __bool__(self) -> bool:
        self._touch()
        return bool(object.__getattribute__(self, "_value"))

    def __eq__(self, other: object) -> bool:
        self._touch()
        return object.__getattribute__(self, "_value") == other

    def __ne__(self, other: object) -> bool:
        self._touch()
        return object.__getattribute__(self, "_value") != other

    def __hash__(self) -> int:
        self._touch()
        return hash(object.__getattribute__(self, "_value"))

    def __contains__(self, item: object) -> bool:
        self._touch()
        return item in object.__getattribute__(self, "_value")

    def __str__(self) -> str:
        self._touch()
        return str(object.__getattribute__(self, "_value"))

    def __repr__(self) -> str:
        return repr(object.__getattribute__(self, "_value"))

    def __int__(self) -> int:
        self._touch()
        return int(object.__getattribute__(self, "_value"))

    def __float__(self) -> float:
        self._touch()
        return float(object.__getattribute__(self, "_value"))

    def __index__(self) -> int:
        self._touch()
        return object.__getattribute__(self, "_value").__index__()

    def __enter__(self):
        self._touch()
        return object.__getattribute__(self, "_value").__enter__()

    def __exit__(self, *exc: Any) -> Any:
        return object.__getattribute__(self, "_value").__exit__(*exc)

    def __del__(self) -> None:
        if object.__getattribute__(self, "_consumed"):
            return
        if object.__getattribute__(self, "_used"):
            return
        try:
            resolve(
                object.__getattribute__(self, "_lint"),
                object.__getattribute__(self, "_level"),
                object.__getattribute__(self, "_message"),
                stacklevel=2,
            )
        except LintError:
            pass


def _record(target: Any, name: str, value: Any) -> Any:
    """Append one attribute record to ``target``.

    Args:
        target: The decorated object.
        name: The attribute name, such as ``"warn"``.
        value: The attribute payload.

    Returns:
        Any: ``target``, unchanged, so this composes inside a decorator.
    """
    recorded = list(getattr(target, ATTRIBUTES, ()))
    recorded.append((name, value))
    setattr(target, ATTRIBUTES, recorded)
    return target


def attributes_of(target: Any) -> dict[str, Any]:
    """Return the Rust-style attributes recorded on an object.

    Args:
        target: Any object decorated by this module.

    Returns:
        dict: Mapping of attribute name to the most recent payload recorded
        under that name. Empty when the object carries no attributes.

    Example:
        >>> @warn("unused", message="check me")
        ... def f():
        ...     return 1
        >>> attributes_of(f)["warn"]["lint"]
        'unused'
    """
    out: dict[str, Any] = {}
    for name, value in getattr(target, ATTRIBUTES, ()):
        out[name] = value
    return out


def find_attribute(target: Any, name: str) -> Any | None:
    """Return the payload of a single recorded attribute.

    Args:
        target: Any object decorated by this module.
        name: The attribute name to look up.

    Returns:
        Any | None: The payload, or None when the attribute is absent.

    Example:
        >>> @deprecated("gone")
        ... def g():
        ...     return 1
        >>> find_attribute(g, "deprecated")["note"]
        'gone'
    """
    for recorded_name, value in getattr(target, ATTRIBUTES, ()):
        if recorded_name == name:
            return value
    return None


def _wrap_with_check(target: Any, check: Callable[..., None]) -> Any:
    """Wrap a function or class so ``check`` runs on every call.

    Args:
        target: The function or class to wrap.
        check: Called with the same arguments as the wrapped object.

    Returns:
        Any: The wrapped object, or ``target`` when it cannot be wrapped.
    """
    if isinstance(target, type):
        original_init = target.__init__

        @functools.wraps(original_init)
        def wrapped_init(self: Any, *args: Any, **kwargs: Any) -> None:
            check(self, *args, **kwargs)
            original_init(self, *args, **kwargs)

        target.__init__ = wrapped_init
        return target

    if not callable(target):
        return target

    @functools.wraps(target)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        check(*args, **kwargs)
        return target(*args, **kwargs)

    return wrapper


def _make_lint_decorator(attribute: str, default_level: str) -> Callable[..., Any]:
    """Build a lint-level attribute decorator such as :func:`warn`.

    The result supports three forms: bare (``@warn``), with a lint name
    (``@warn("unused")``), and with options
    (``@warn("unused", level="deny")``).

    Args:
        attribute: The Rust attribute name being emulated.
        default_level: The level requested when the caller does not pass one.

    Returns:
        Callable: The decorator.
    """

    def build(
        lint: str | None = None,
        *,
        level: Any = None,
        message: str | None = None,
        only_for_types: tuple[type, ...] = (),
    ) -> Callable[[Any], Any]:
        """Build the decorator for one specific configuration.

        Args:
            lint: The lint name to report under. Defaults to the decorated
                object's ``__name__``.
            level: The level to request. Defaults to ``default_level``.
            message: Diagnostic text. A bare ``{}`` placeholder is filled with
                the lint name.
            only_for_types: When non-empty, only calls whose arguments include
                one of these types fire the lint.

        Returns:
            Callable: A decorator that records the attribute and enforces it.
        """
        requested = default_level if level is None else normalize_level(level)

        def decorate(target: Any) -> Any:
            """Record the attribute and enforce it on every call."""
            name = lint or getattr(target, "__name__", "anonymous")
            text = message.format(name) if message and "{}" in message else message
            text = text or f"lint {name!r} fired for {name}"

            def check(*args: Any, **kwargs: Any) -> None:
                """Fire the lint if the call matches the configured type filter."""
                if only_for_types and not any(
                    isinstance(arg, only_for_types) for arg in (*args, *kwargs.values())
                ):
                    return
                resolve(name, requested, text)

            _record(
                target,
                attribute,
                {
                    "lint": name,
                    "level": requested,
                    "message": text,
                    "only_for_types": only_for_types,
                    "check": check,
                },
            )

            if attribute == FORBID:
                _cap_lint(name)
                return target

            if attribute == ALLOW:
                return target

            wrapped = _wrap_with_check(target, check)
            _record(
                wrapped,
                attribute,
                {
                    "lint": name,
                    "level": requested,
                    "message": text,
                    "only_for_types": only_for_types,
                    "check": check,
                },
            )
            return wrapped

        return decorate

    def decorator(*args: Any, **kwargs: Any) -> Any:
        """Dispatch between bare usage and configured usage."""
        if args and not kwargs and not isinstance(args[0], str) and callable(args[0]):
            return build()(args[0])
        lint = args[0] if args and isinstance(args[0], str) else None
        return build(lint, **kwargs)

    decorator.__name__ = attribute
    decorator.__qualname__ = attribute
    decorator.__doc__ = f"""Emulate Rust's ``#[{attribute}(lint)]`` on a function or class.

Usage:
    >>> @{attribute}                      # bare, lint name taken from __name__
    ... def target():
    ...     pass
    >>> @{attribute}("my_lint")            # explicit lint name
    ... def other():
    ...     pass
    >>> @{attribute}("my_lint", level="deny")
    ... def strict():
    ...     pass

The attribute is recorded on the target and readable with
:func:`find_attribute`. At ``{default_level}`` it is also enforced at call
time: ``allow`` is silent, ``warn`` emits a :class:`~oxide.derive.LintWarning`,
and ``deny``/``forbid`` raise :class:`~oxide.derive.LintError`.
"""
    return decorator


allow = _make_lint_decorator(ALLOW, ALLOW)
warn = _make_lint_decorator(WARN, WARN)
deny = _make_lint_decorator(DENY, DENY)
forbid = _make_lint_decorator(FORBID, FORBID)

# Prefixed spellings of the four lint decorators. Identical objects, exported so
# that a caller re-exporting them alongside the rest of the library can avoid
# colliding with ``oxide.core.traits`` and the ``cfg`` macro.
lint_allow = allow
lint_warn = warn
lint_deny = deny
lint_forbid = forbid


def deprecated(
    note: str = "",
    *,
    since: str | None = None,
    version: str | None = None,
    category: type[Warning] = DEPRECATION_CATEGORY,
    lint: str = DEPRECATED_LINT,
    level: Any = None,
) -> Callable[[Any], Any]:
    """Mark a callable or class as deprecated, warning when it is used.

    Mirrors Rust's ``#[deprecated]``. The note is included in the warning so
    callers learn what to use instead.

    Args:
        note: Free-form text describing the replacement.
        since: Version in which the deprecation was introduced.
        version: Alias for ``since``, kept for symmetry with
            :class:`oxide.other.CreateMeta`.
        category: Warning category to emit. Defaults to
            :class:`DeprecationWarning`.
        lint: Lint name to report under.
        level: Optional lint level override. Set it to ``allow`` to silence the
            warning while still recording the attribute.

    Returns:
        Callable: A decorator preserving the wrapped object's signature.

    Example:
        >>> @deprecated("use Vec instead", since="2.1")
        ... def old_vec():
        ...     return []
        >>> import warnings
        >>> with warnings.catch_warnings(record=True) as caught:
        ...     warnings.simplefilter("always")
        ...     old_vec()
        []
        >>> str(caught[0].message)
        "'old_vec' is deprecated: use Vec instead (since 2.1)"
    """

    def decorate(target: Any) -> Any:
        """Wrap the target so every call warns."""
        since_text = since or version
        suffix = f" (since {since_text})" if since_text else ""
        label = getattr(target, "__name__", repr(target))
        message = f"{label!r} is deprecated: {note}{suffix}"
        payload = {
            "note": note,
            "since": since_text,
            "category": category,
            "message": message,
        }

        def check(*args: Any, **kwargs: Any) -> None:
            """Emit the deprecation warning, or raise per the configured level."""
            if level is not None:
                resolve(lint, level, message)
                return
            warnings.warn(message, category, stacklevel=3)

        _record(target, "deprecated", payload)
        wrapped = _wrap_with_check(target, check)
        _record(wrapped, "deprecated", payload)
        return wrapped

    return decorate


def must_use(
    message: str | None = None,
    *,
    lint: str = MUST_USE_LINT,
    level: Any = None,
    check: bool = False,
) -> Callable[[Any], Any]:
    """Mark a function's return value as required, like Rust's ``#[must_use]``.

    Rust rejects the call at compile time when the result is dropped. Python
    cannot, so this decorator records the requirement and, when ``check=True``,
    wraps the return value in a proxy that reports the unused result when it is
    garbage-collected without ever being read.

    Args:
        message: Text for the diagnostic. Defaults to naming the function.
        lint: Lint name to report under.
        level: Level requested when the discard is detected. Defaults to
            ``warn``.
        check: Install the runtime discard check. Off by default because it
            wraps the return value in a proxy.

    Returns:
        Callable: A decorator preserving the wrapped object's signature.

    Example:
        >>> @must_use("the parsed value is required", check=True)
        ... def parse():
        ...     return 42
        >>> int(parse())
        42
        >>> find_attribute(parse, "must_use")["check"]
        True
    """

    def decorate(target: Any) -> Any:
        """Record the attribute and optionally install the discard check."""
        text = message or f"return value of {getattr(target, '__name__', target)!r} is unused"
        requested = normalize_level("warn" if level is None else level)
        payload = {
            "message": text,
            "lint": lint,
            "level": requested,
            "check": check,
        }
        _record(target, "must_use", payload)

        if not check:
            return target

        @functools.wraps(target)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return _MustUse(target(*args, **kwargs), text, lint, requested)

        _record(wrapper, "must_use", payload)
        return wrapper

    return decorate


def inline(always: bool = False, *, reason: str | None = None) -> Callable[[Any], Any]:
    """Record a Rust ``#[inline]`` hint.

    Python has no inliner, so this is metadata only: it costs nothing at runtime
    and is readable through :func:`attributes_of`. It is still worth recording,
    because it documents the intent and the reasoning travels with the code.

    Args:
        always: Request unconditional inlining, as ``#[inline(always)]``.
        reason: Why the hint is present.

    Returns:
        Callable: A decorator returning the target unchanged.

    Example:
        >>> @inline(always=True, reason="hot path")
        ... def fast(x):
        ...     return x + 1
        >>> find_attribute(fast, "inline")
        {'always': True, 'reason': 'hot path'}
    """

    def decorate(target: Any) -> Any:
        """Record the inline hint and return the target unchanged."""
        return _record(target, "inline", {"always": always, "reason": reason})

    return decorate


def non_exhaustive(target: Any) -> Any:
    """Mark a type as ``#[non_exhaustive]``.

    Rust forbids downstream crates from building a ``#[non_exhaustive]`` struct
    with a struct literal, leaving the author free to add fields. The compiler
    is the only thing that can enforce that in Rust, so here the attribute is
    recorded as metadata and readable with :func:`is_non_exhaustive`. Pair it
    with a classmethod factory to get the same protection.

    Args:
        target: The class to mark.

    Returns:
        Any: The decorated class.

    Example:
        >>> @non_exhaustive
        ... class Config:
        ...     __slots__ = ("host", "port")
        ...     def __init__(self, host, port=80):
        ...         self.host = host
        ...         self.port = port
        >>> is_non_exhaustive(Config)
        True
    """
    return _record(target, "non_exhaustive", {"protected": True, "module": target.__module__})


def is_non_exhaustive(target: Any) -> bool:
    """Return whether a type is marked ``#[non_exhaustive]``.

    Args:
        target: The class to inspect.

    Returns:
        bool: True when the type carries the attribute.

    Example:
        >>> class Plain:
        ...     pass
        >>> is_non_exhaustive(Plain)
        False
    """
    return find_attribute(target, "non_exhaustive") is not None


def export_name(name: str) -> Callable[[Any], Any]:
    """Record Rust's ``#[export_name = "..."]``, an explicit public symbol name.

    Args:
        name: The exported symbol name.

    Returns:
        Callable: A decorator returning the target unchanged.

    Example:
        >>> @export_name("oxidized_entry")
        ... def entry():
        ...     return 1
        >>> find_attribute(entry, "export_name")["name"]
        'oxidized_entry'
    """

    def decorate(target: Any) -> Any:
        """Record the export name and return the target unchanged."""
        return _record(target, "export_name", {"name": name})

    return decorate


#: Feature flags considered enabled by :func:`cfg`. Extend it with
#: :func:`enable_feature` to opt into ``cfg(feature=...)`` gated code paths.
ENABLED_FEATURES: set[str] = set()


def enable_feature(*names: str) -> set[str]:
    """Enable one or more feature flags for :func:`cfg`.

    Args:
        *names: The feature names to enable.

    Returns:
        set[str]: A copy of the full set of enabled features.

    Example:
        >>> enable_feature("nightly")
        {'nightly'}
        >>> ENABLED_FEATURES.discard("nightly")
    """
    ENABLED_FEATURES.update(names)
    return set(ENABLED_FEATURES)


def reset_features() -> None:
    """Disable every feature flag, returning :data:`ENABLED_FEATURES` to empty.

    The counterpart to :func:`enable_feature`, mirroring ``reset_lints`` for the
    lint registry.

    Returns:
        None.

    Example:
        >>> enable_feature("nightly", "simd") == {"nightly", "simd"}
        True
        >>> reset_features()
        >>> ENABLED_FEATURES
        set()
    """
    ENABLED_FEATURES.clear()


def _platform_matches(token: str) -> bool:
    """Return whether a platform token matches the running interpreter."""
    import sys

    if token == "py3":
        return sys.version_info[0] >= 3
    if token.startswith("py"):
        try:
            return sys.version_info[:2] == (int(token[2]), int(token[3]))
        except (IndexError, ValueError):
            return False
    return sys.platform == token


def _under_test() -> bool:
    """Return whether the code appears to be running under a test runner."""
    import sys

    return "pytest" in sys.modules or "unittest" in sys.modules


def cfg(
    *,
    feature: str | None = None,
    not_feature: str | None = None,
    platform: str | None = None,
    not_platform: str | None = None,
    test: bool | None = None,
) -> Callable[[Any], Any]:
    """Emulate Rust's ``#[cfg(...)]`` conditional compilation.

    When the condition holds the target is returned unchanged. When it does not,
    the target is replaced by a stub that raises :class:`FeatureDisabledError` on
    use — the closest Python analogue to "this item was compiled out".

    Args:
        feature: Require this feature flag to be present in
            :data:`ENABLED_FEATURES`.
        not_feature: Require this feature flag to be absent.
        platform: Require this platform token to match: ``linux``, ``darwin``,
            ``win32``, ``py3``, or ``py310``-style version tokens.
        not_platform: Require this platform token to be absent.
        test: Require the code to be running under a test runner when True, or
            not under one when False.

    Returns:
        Callable: A decorator that keeps or stubs out the target.

    Example:
        >>> @cfg(feature="never_enabled")
        ... def experimental():
        ...     return 1
        >>> find_attribute(experimental, "cfg")["compiled"]
        False
        >>> experimental()
        Traceback (most recent call last):
            ...
        oxide.derive.attributes.FeatureDisabledError: item was compiled out by cfg(feature='never_enabled')

        The negating forms behave the other way around:

        >>> @cfg(not_feature="never_enabled")
        ... def portable():
        ...     return "built"
        >>> portable()
        'built'
        >>> enable_feature("nightly")
        {'nightly'}

        Once the feature exists, ``not_feature`` compiles the item out:

        >>> @cfg(not_feature="nightly")
        ... def stable_only():
        ...     return 1
        >>> stable_only()
        Traceback (most recent call last):
            ...
        oxide.derive.attributes.FeatureDisabledError: item was compiled out by cfg(not_feature='nightly')
        >>> reset_features()
    """
    conditions: list[str] = []
    if feature is not None:
        conditions.append(f"feature={feature!r}")
    if not_feature is not None:
        conditions.append(f"not_feature={not_feature!r}")
    if platform is not None:
        conditions.append(f"platform={platform!r}")
    if not_platform is not None:
        conditions.append(f"not_platform={not_platform!r}")
    if test is not None:
        conditions.append(f"test={test!r}")
    description = ", ".join(conditions)

    holds = True
    if feature is not None:
        holds = holds and feature in ENABLED_FEATURES
    if not_feature is not None:
        holds = holds and not_feature not in ENABLED_FEATURES
    if platform is not None:
        holds = holds and _platform_matches(platform)
    if not_platform is not None:
        holds = holds and not _platform_matches(not_platform)
    if test is not None:
        holds = holds and _under_test() is test

    def decorate(target: Any) -> Any:
        """Keep the target when the cfg holds, otherwise install a stub."""
        if holds:
            _record(target, "cfg", {"compiled": True, "condition": description})
            return target

        def stub(*args: Any, **kwargs: Any) -> Any:
            """Refuse to run because the item was compiled out."""
            raise FeatureDisabledError(description)

        if callable(target):
            try:
                functools.update_wrapper(stub, target)
            except (AttributeError, TypeError):
                stub.__name__ = getattr(target, "__name__", "compiled_out")
        _record(stub, "cfg", {"compiled": False, "condition": description})
        _record(stub, "compiled_out", {"name": getattr(target, "__name__", "compiled_out")})
        return stub

    return decorate


def doc(text: str) -> Callable[[Any], Any]:
    """Attach documentation to an object, like a Rust ``///`` doc comment.

    The text is prepended to the target's docstring and also recorded under the
    ``doc`` attribute.

    Args:
        text: The documentation text.

    Returns:
        Callable: A decorator returning the target with an extended docstring.

    Example:
        >>> @doc("Return the answer.")
        ... def answer():
        ...     return 42
        >>> answer.__doc__
        'Return the answer.'
    """

    def decorate(target: Any) -> Any:
        """Prepend ``text`` to the target's docstring."""
        existing = target.__doc__ or ""
        target.__doc__ = f"{text}\n\n{existing}".strip() if existing else text.strip()
        return _record(target, "doc", {"text": text})

    return decorate


__all__ = [
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
    "reset_features",
    "export_name",
    "find_attribute",
    "forbid",
    "inline",
    "is_non_exhaustive",
    "must_use",
    "non_exhaustive",
    "warn",
]
