"""Rust derive macros as a single decorator.

Rust's ``#[derive(...)]`` asks the compiler to write boilerplate implementations
from a type's field list. :func:`derive` does the same thing at runtime: point
it at a class, name the traits you want, and it generates the corresponding
dunders and helper methods.

Fields are discovered in this order:

1. The ``fields=`` argument, when given.
2. The class's ``__annotations__``, minus anything annotated ``ClassVar``.
3. ``__slots__``, with a single leading underscore stripped so ``_cache`` is
   treated as the field ``cache``.

Generated methods never clobber something the class defines itself — Rust panics
on a duplicate implementation, and so does this, via the ``overwrite`` argument
if you explicitly ask for it.

============  ==========================================================
Derive        Generates
============  ==========================================================
``Debug``     ``__repr__`` in Rust's ``Type { field: value }`` style
``Display``   ``__str__``, delegating to a ``display()`` method if present
``Clone``     ``clone()`` and ``__copy__``
``Copy``      ``clone()`` returning ``self`` — trivially copyable
``PartialEq`` ``__eq__``, field by field
``Eq``        ``__eq__`` plus ``__hash__``
``PartialOrd````__lt__``, ``__le__``, ``__gt__``, ``__ge__``
``Ord``       ``PartialOrd`` plus total ``__eq__`` and ``__hash__``
``Hash``      ``__hash__`` over the field tuple
``Default``   ``default()`` classmethod
``Error``     ``__str__`` carrying an error message, plus ``is_error``
============  ==========================================================

Example:
    >>> @derive("Debug", "Clone", "PartialEq", "Hash", "Default")
    ... class Point:
    ...     __slots__ = ("x", "y")
    ...     def __init__(self, x=0, y=0):
    ...         self.x = x
    ...         self.y = y
    >>> Point(1, 2)
    Point { x: 1, y: 2 }
    >>> Point(1, 2) == Point(1, 2)
    True
    >>> Point(1, 2).clone()
    Point { x: 1, y: 2 }
    >>> sorted([Point(2, 0), Point(1, 1)], key=lambda p: (p.x, p.y))
    [Point { x: 1, y: 1 }, Point { x: 2, y: 0 }]
"""

from __future__ import annotations

import copy as _copy
from typing import Any, Callable, Iterable, Mapping, Sequence

from .attributes import _record

#: Canonical derive name to accepted aliases, lowercased.
DERIVE_ALIASES: dict[str, str] = {
    "debug": "Debug",
    "repr": "Debug",
    "display": "Display",
    "fmt": "Display",
    "clone": "Clone",
    "copy": "Copy",
    "partialeq": "PartialEq",
    "eq": "Eq",
    "partialord": "PartialOrd",
    "ord": "Ord",
    "hash": "Hash",
    "default": "Default",
    "error": "Error",
}

#: Every derive this module knows how to generate, in generation order.
SUPPORTED_DERIVES: tuple[str, ...] = (
    "Debug",
    "Display",
    "Clone",
    "Copy",
    "PartialEq",
    "Eq",
    "PartialOrd",
    "Ord",
    "Hash",
    "Default",
    "Error",
)


class DeriveError(TypeError):
    """Raised when a derive cannot be generated for a class.

    Attributes:
        derive (str): The canonical derive name that failed.
        cls_name (str): The class the derive was requested for.
    """

    __slots__ = ("derive", "cls_name")

    def __init__(self, derive: str, cls_name: str, reason: str) -> None:
        """Initialise the error.

        Args:
            derive: The canonical derive name that failed.
            cls_name: Name of the class the derive was requested for.
            reason: Why generation failed.
        """
        super().__init__(f"cannot derive {derive} for {cls_name}: {reason}")
        self.derive = derive
        self.cls_name = cls_name


def resolve_derive(name: Any) -> str:
    """Normalise a derive name or alias to its canonical spelling.

    Args:
        name: A derive name such as ``"Debug"``, ``"repr"``, or an object whose
            ``__name__`` is one of those.

    Returns:
        str: The canonical derive name.

    Raises:
        DeriveError: If the name is not a supported derive.

    Example:
        >>> resolve_derive("repr")
        'Debug'
    """
    key = getattr(name, "__name__", name)
    key = str(key).replace("_", "").replace("-", "").lower()
    try:
        return DERIVE_ALIASES[key]
    except KeyError:
        raise DeriveError(
            str(name), "?", f"unknown derive; expected one of {', '.join(SUPPORTED_DERIVES)}"
        ) from None


def derive_fields(
    cls: type,
    *,
    fields: Iterable[str] | None = None,
    annotations: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    """Return the field list a derive should operate on.

    Args:
        cls: The class to inspect.
        fields: An explicit field list, which wins over everything else.
        annotations: Annotation mapping to use instead of the class's own, for
            callers resolving string annotations themselves.

    Returns:
        tuple: Field names, in declaration order, with private underscores
        stripped.

    Example:
        >>> class Sample:
        ...     __slots__ = ("_a", "b")
        >>> derive_fields(Sample)
        ('a', 'b')
    """
    if fields is not None:
        return tuple(fields)

    source = cls.__dict__.get("__annotations__") if annotations is None else annotations
    if source:
        return tuple(
            name for name in source if not str(source[name]).startswith(("ClassVar", "typing.ClassVar"))
        )

    slots = cls.__dict__.get("__slots__")
    if isinstance(slots, str):
        slots = (slots,)
    if slots:
        return tuple(name.lstrip("_") for name in slots)

    return ()


def _values(cls: type, names: Sequence[str], obj: Any) -> tuple[Any, ...]:
    """Read a field tuple off an instance, tolerating missing attributes."""
    return tuple(getattr(obj, name, None) for name in names)


def _install(cls: type, name: str, value: Any, overwrite: bool, derived: list[str]) -> bool:
    """Add a generated method to a class unless it already defines one.

    Args:
        cls: The class to install onto.
        name: The attribute name to install.
        value: The generated implementation.
        overwrite: Whether to replace an existing definition.
        derived: Accumulator of generated names, appended to on success.

    Returns:
        bool: True when the method was installed.
    """
    if name in cls.__dict__ and not overwrite:
        return False
    setattr(cls, name, value)
    derived.append(name)
    return True


def _sort_key(names: Sequence[str]) -> Callable[[Any], tuple[Any, ...]]:
    """Build a field-tuple key function usable as ``sorted(key=...)``."""
    return lambda obj: _values(type(obj), names, obj)


def derive(
    *names: Any,
    fields: Iterable[str] | None = None,
    defaults: Mapping[str, Any] | None = None,
    pretty: bool = False,
    overwrite: bool = False,
) -> Callable[[type], type]:
    """Generate boilerplate for a class, like Rust's ``#[derive(...)]``.

    Args:
        *names: The derives to generate. Accepts canonical names (``"Debug"``)
            and aliases (``"repr"``), as strings or objects with a ``__name__``.
        fields: Explicit field list. Defaults to annotations, then ``__slots__``.
        defaults: Field default values for the ``Default`` derive. A field with
            no entry falls back to its ``__init__`` parameter default, then to a
            ``default_<field>`` class attribute.
        pretty: Emit multi-line ``__repr__`` output in Rust's ``{:#?}`` style.
        overwrite: Replace dunders the class already defines. Off by default,
            so hand-written implementations always win.

    Returns:
        Callable: A class decorator returning the class, annotated with the
        ``derive`` attribute listing what was generated.

    Raises:
        DeriveError: If a derive cannot be generated, for example ``Default``
            with no default available for a field, or an unknown derive name.

    Example:
        >>> @derive("Debug", "Clone", "Default")
        ... class Config:
        ...     __slots__ = ("host", "port")
        ...     def __init__(self, host="localhost", port=8080):
        ...         self.host = host
        ...         self.port = port
        >>> Config.default()
        Config { host: 'localhost', port: 8080 }
        >>> Config.default(port=9090)
        Config { host: 'localhost', port: 9090 }
    """
    requested = [resolve_derive(name) for name in names]
    ordered = [name for name in SUPPORTED_DERIVES if name in requested]

    def decorate(cls: type) -> type:
        """Generate the requested derives on ``cls``."""
        field_names = derive_fields(cls, fields=fields)
        generated: list[str] = []
        skipped: list[str] = []

        def note(name: str, installed: bool) -> None:
            """Track whether a generated method was installed or skipped."""
            (generated if installed else skipped).append(name)

        wants_debug = "Debug" in requested
        wants_display = "Display" in requested
        wants_error = "Error" in requested

        if wants_debug and field_names:
            name = "Debug"
            if pretty:

                def __repr__(self: Any, _names: Sequence[str] = field_names,
                              _cls: type = cls) -> str:
                    """Return an indented, multi-line representation."""
                    label = _cls.__name__
                    body = "".join(f"    {field}: {getattr(self, field, None)!r},\n"
                                   for field in _names)
                    return f"{label} {{\n{body}}}"

            else:

                def __repr__(self: Any, _names: Sequence[str] = field_names,
                              _cls: type = cls) -> str:
                    """Return a single-line representation in Rust's style."""
                    body = ", ".join(f"{field}: {getattr(self, field, None)!r}"
                                     for field in _names)
                    return f"{_cls.__name__} {{ {body} }}"

            note(name, _install(cls, "__repr__", __repr__, overwrite, generated))

        if (wants_display or wants_error) and field_names:
            name = "Error" if wants_error else "Display"
            if wants_error:

                def __str__(self: Any, _names: Sequence[str] = field_names) -> str:
                    """Return the error message assembled from ``message`` fields."""
                    message = getattr(self, "message", None)
                    if message is not None:
                        return str(message)
                    parts = [f"{field}={getattr(self, field, None)!r}" for field in _names]
                    return f"{type(self).__name__}: " + ", ".join(parts)

            else:

                def __str__(self: Any) -> str:
                    """Return the class's own display text."""
                    display = getattr(self, "display", None)
                    if callable(display):
                        return str(display())
                    return repr(self)

            if wants_error:
                note(name, _install(cls, "__str__", __str__, overwrite, generated))
                _record(cls, "error", {"is_error": True, "fields": tuple(field_names)})
            else:
                note(name, _install(cls, "__str__", __str__, overwrite, generated))

        if "Copy" in requested and field_names:

            def clone(self: Any) -> Any:
                """Return ``self``: a ``Copy`` type is trivially copyable."""
                return self

            note("Copy", _install(cls, "clone", clone, overwrite, generated))

        elif "Clone" in requested and field_names:

            def clone(self: Any, _names: Sequence[str] = field_names) -> Any:
                """Return an independent copy with the same field values."""
                return _clone_instance(self, _names)

            def __copy__(self: Any, _names: Sequence[str] = field_names) -> Any:
                """Return an independent copy, for :func:`copy.copy`.

                Built from a bare instance rather than :func:`copy.copy`, which
                would dispatch straight back here.
                """
                return _clone_instance(self, _names)

            note("Clone", _install(cls, "clone", clone, overwrite, generated))
            note("Clone", _install(cls, "__copy__", __copy__, overwrite, generated))

        if "Ord" in requested or "PartialOrd" in requested:
            if not field_names:
                raise DeriveError(
                    "PartialOrd" if "PartialOrd" in requested else "Ord",
                    cls.__name__,
                    "field-wise ordering needs at least one field",
                )
            name = "Ord" if "Ord" in requested else "PartialOrd"
            key = _sort_key(field_names)

            def __lt__(self: Any, other: Any, _key: Callable[[Any], tuple[Any, ...]] = key) -> bool:
                """Return whether self sorts before other, comparing field tuples."""
                if other is None:
                    return NotImplemented
                return _key(self) < _key(other)

            def __le__(self: Any, other: Any, _key: Callable[[Any], tuple[Any, ...]] = key) -> bool:
                """Return whether self sorts at or before other."""
                if other is None:
                    return NotImplemented
                return _key(self) <= _key(other)

            def __gt__(self: Any, other: Any, _key: Callable[[Any], tuple[Any, ...]] = key) -> bool:
                """Return whether self sorts after other."""
                if other is None:
                    return NotImplemented
                return _key(self) > _key(other)

            def __ge__(self: Any, other: Any, _key: Callable[[Any], tuple[Any, ...]] = key) -> bool:
                """Return whether self sorts at or after other."""
                if other is None:
                    return NotImplemented
                return _key(self) >= _key(other)

            for dunder, impl in (("__lt__", __lt__), ("__le__", __le__),
                                 ("__gt__", __gt__), ("__ge__", __ge__)):
                note(name, _install(cls, dunder, impl, overwrite, generated))
            _record(cls, "sort_key", {"fields": tuple(field_names), "key": key})

        if "Eq" in requested or "PartialEq" in requested:
            if not field_names:
                raise DeriveError(
                    "Eq" if "Eq" in requested else "PartialEq",
                    cls.__name__,
                    "field-wise equality needs at least one field",
                )
            name = "Eq" if "Eq" in requested else "PartialEq"

            def __eq__(self: Any, other: Any,
                       _names: Sequence[str] = field_names) -> bool:
                """Return whether other is the same type with equal fields."""
                if other.__class__ is not self.__class__:
                    return NotImplemented
                return _values(type(self), _names, self) == _values(type(other), _names, other)

            note(name, _install(cls, "__eq__", __eq__, overwrite, generated))
            if "Eq" in requested and "Hash" not in requested:
                _install(cls, "__hash__", _field_hash(field_names), overwrite, generated)
                generated.append("__hash__")

        if "Ord" in requested and field_names:
            _install(cls, "__hash__", _field_hash(field_names), overwrite, generated)
            generated.append("__hash__")

        if "Hash" in requested and field_names:
            note("Hash", _install(cls, "__hash__", _field_hash(field_names), overwrite, generated))

        if "Default" in requested:

            def default(_cls: type = cls, _names: Sequence[str] = field_names,
                        _defaults: Mapping[str, Any] | None = defaults,
                        **overrides: Any) -> Any:
                """Build an instance with every field at its default value.

                Defaults are resolved in order of precedence: an override
                passed here, then the ``defaults`` mapping, then a
                ``default_<field>`` class attribute, then the matching
                ``__init__`` parameter default.

                Args:
                    **overrides: Per-field values that win over every default.

                Raises:
                    DeriveError: If a field has no default anywhere. Rust
                        refuses to compile in the same situation rather than
                        inventing a value.
                """
                declared = _constructor_defaults(_cls)
                values: dict[str, Any] = {}
                for field in _names:
                    if field in overrides:
                        values[field] = overrides[field]
                        continue
                    if _defaults is not None and field in _defaults:
                        values[field] = _defaults[field]
                        continue
                    inherited = getattr(_cls, f"default_{field}", _MISSING)
                    if inherited is not _MISSING:
                        values[field] = inherited() if callable(inherited) else inherited
                        continue
                    if field in declared:
                        values[field] = declared[field]
                        continue
                    raise DeriveError(
                        "Default",
                        _cls.__name__,
                        f"no default for field {field!r}; add an __init__ parameter "
                        f"default, a default_{field} attribute, or pass defaults={{...}}",
                    )
                return _cls(**values)

            note("Default", _install(cls, "default", classmethod(default), overwrite, generated))

        _record(
            cls,
            "derive",
            {
                "requested": tuple(ordered),
                "fields": tuple(field_names),
                "generated": tuple(generated),
                "skipped": tuple(skipped),
                "pretty": pretty,
            },
        )
        return cls

    return decorate


_MISSING: Any = object()


def _clone_instance(obj: Any, names: Sequence[str]) -> Any:
    """Build an independent copy of an instance by copying each field.

    Uses :func:`object.__new__` rather than :func:`copy.copy`, so a generated
    ``__copy__`` does not dispatch back into itself.

    Args:
        obj: The instance to copy.
        names: The field names to copy.

    Returns:
        Any: A new instance of the same class with copied field values.
    """
    duplicate = object.__new__(type(obj))
    for field in names:
        try:
            object.__setattr__(duplicate, field, _copy.copy(getattr(obj, field)))
        except (AttributeError, TypeError):
            pass
    return duplicate


def _constructor_defaults(cls: type) -> dict[str, Any]:
    """Read the declared defaults of a class's ``__init__`` parameters.

    Rust's ``#[derive(Default)]`` requires every field to name a default. The
    Python equivalent is a parameter default in ``__init__``, so that is where
    this module looks before giving up.

    Args:
        cls: The class to inspect.

    Returns:
        dict: Parameter name to default value, for parameters that have one.
    """
    import inspect as _inspect

    initializer = cls.__dict__.get("__init__")
    if initializer is None:
        return {}
    try:
        parameters = _inspect.signature(initializer).parameters
    except (TypeError, ValueError):
        return {}
    return {
        name: parameter.default
        for name, parameter in parameters.items()
        if name != "self" and parameter.default is not _inspect.Parameter.empty
    }


def _field_hash(names: Sequence[str]) -> Callable[[Any], int]:
    """Build a ``__hash__`` implementation over a field tuple."""

    def __hash__(self: Any, _names: Sequence[str] = names) -> int:
        """Return a hash of every field, so equal values hash equally."""
        return hash(_values(type(self), _names, self))

    return __hash__


def is_derived(cls: type) -> bool:
    """Return whether a class was processed by :func:`derive`.

    Args:
        cls: The class to inspect.

    Returns:
        bool: True when the class carries a ``derive`` attribute.

    Example:
        >>> @derive("Debug")
        ... class Tiny:
        ...     __slots__ = ("v",)
        >>> is_derived(Tiny)
        True
        >>> class Plain:
        ...     pass
        >>> is_derived(Plain)
        False
    """
    from .attributes import find_attribute

    return find_attribute(cls, "derive") is not None


def derives_of(cls: type) -> dict[str, Any]:
    """Return the recorded ``derive`` metadata for a class.

    Args:
        cls: The class to inspect.

    Returns:
        dict: The ``derive`` attribute payload, or an empty dict when the class
        was never processed by :func:`derive`.

    Example:
        >>> @derive("Debug")
        ... class Record:
        ...     __slots__ = ("a",)
        >>> derives_of(Record)["fields"]
        ('a',)
    """
    from .attributes import find_attribute

    return find_attribute(cls, "derive") or {}


__all__ = [
    "DERIVE_ALIASES",
    "SUPPORTED_DERIVES",
    "DeriveError",
    "derive",
    "derive_fields",
    "derives_of",
    "is_derived",
    "resolve_derive",
]
