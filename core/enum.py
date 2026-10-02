"""Enum and Variant — tagged unions with match() pattern matching.

Provides Enum, Variant for building algebraic data types, and the match()
function for exhaustive pattern matching with wildcard support.
"""

from __future__ import annotations

from typing import Any, Callable, Generic, Iterable, Iterator, TypeVar


T = TypeVar("T")
R = TypeVar("R")


class MatchError(Exception):
    """Raised when no case in a match expression matches the given value.

    Example:
        >>> match(1).case_eq(2, "two").execute()
        Traceback (most recent call last):
            ...
        oxide.core.enum.MatchError: no match found for 1
    """
    pass


class _Case(Generic[T, R]):
    """Internal holder linking a pattern, handler, and optional guard.

    This class is an implementation detail of the ``Match`` builder and is not
    intended to be used directly by consumers.
    """

    __slots__ = ("pattern", "handler", "guard")

    def __init__(
        self,
        pattern: T | type | tuple[type, ...] | None,
        handler: Callable[[T], R] | R,
        guard: Callable[[T], bool] | None,
    ) -> None:
        """Store the pattern, handler, and guard for a single match case.

        Args:
            pattern: The value, type, tuple of types, or wildcard to match.
            handler: A callable invoked on match or a constant to return.
            guard: An optional predicate that must also hold for the match.
        """
        self.pattern = pattern
        self.handler = handler
        self.guard = guard

    def matches(self, value: object) -> bool:
        """Return True if the pattern and guard match the given value.

        Args:
            value (object): The value being tested against this case.

        Returns:
            bool: True if this case matches ``value``, else False.
        """
        if self.pattern is _:
            return True
        if self.pattern is None:
            return value is None
        if isinstance(self.pattern, type):
            if not isinstance(value, self.pattern):
                return False
        elif isinstance(self.pattern, tuple):
            if not isinstance(value, self.pattern):
                return False
        elif self.pattern != value:
            return False
        if self.guard is not None and not self.guard(value):
            return False
        return True

    def execute(self, value: T) -> R:
        """Invoke the handler with the value or return it as a constant.

        Args:
            value (T): The matched value passed to a callable handler.

        Returns:
            R: The result of calling ``handler(value)``, or ``handler`` itself
            when it is a non-callable constant.
        """
        if callable(self.handler) and not isinstance(self.handler, type):
            return self.handler(value)
        return self.handler  # type: ignore[return-value]


class Match(Generic[T, R]):
    """Fluent builder for pattern matching on a value.

    Accumulate cases with ``case``/``case_type``/``case_eq`` and friends, then
    evaluate with ``execute()`` or ``otherwise(...)`` to obtain the result of
    the first matching case.

    Example:
        >>> def describe(n: int) -> str:
        ...     return (
        ...         match(n)
        ...         .case_eq(0, "zero")
        ...         .case_range(1, 10, "small")
        ...         .otherwise("large")
        ...     )
        >>> describe(0), describe(5), describe(100)
        ('zero', 'small', 'large')
    """

    __slots__ = ("_value", "_cases", "_executed", "_result")

    def __init__(self, value: T) -> None:
        """Start a match expression over the given value.

        Args:
            value (T): The value to match against.
        """
        self._value = value
        self._cases: list[_Case] = []
        self._executed = False
        self._result: R = None  # type: ignore[assignment]

    def case(
        self,
        pattern: object | type | tuple[type, ...] | None,
        handler: Callable[[T], R] | R | None = None,
        *,
        guard: Callable[[T], bool] | None = None,
    ) -> Match[T, R]:
        """Add a case with an arbitrary pattern and optional guard.

        Args:
            pattern: The value, type, tuple of types, or wildcard to match.
            handler: A callable invoked on match or a constant to return.
            guard: An optional predicate that must also hold for the match.

        Returns:
            Match: This builder, for chaining further cases.
        """
        self._cases.append(_Case(pattern, handler, guard))
        return self

    def case_type(
        self,
        typ: type | tuple[type, ...],
        handler: Callable[[T], R] | R | None = None,
        *,
        guard: Callable[[T], bool] | None = None,
    ) -> Match[T, R]:
        """Add a case that matches values of the given type (or tuple of types).

        Args:
            typ: A type or tuple of types to match against with ``isinstance``.
            handler: A callable invoked on match or a constant to return.
            guard: An optional predicate that must also hold for the match.

        Returns:
            Match: This builder, for chaining further cases.

        Example:
            >>> match("hi").case_type(str, lambda s: len(s)).execute()
            2
        """
        self._cases.append(_Case(typ, handler, guard))
        return self

    def case_eq(
        self,
        value: object,
        handler: Callable[[T], R] | R | None = None,
        *,
        guard: Callable[[T], bool] | None = None,
    ) -> Match[T, R]:
        """Add a case that matches by equality to the given value.

        Args:
            value (object): The value to compare with ``==``.
            handler: A callable invoked on match or a constant to return.
            guard: An optional predicate that must also hold for the match.

        Returns:
            Match: This builder, for chaining further cases.

        Example:
            >>> match(7).case_eq(7, "lucky").execute()
            'lucky'
        """
        self._cases.append(_Case(value, handler, guard))
        return self

    def case_range(
        self,
        start: int,
        end: int,
        handler: Callable[[T], R] | R | None = None,
        *,
        guard: Callable[[T], bool] | None = None,
    ) -> Match[T, R]:
        """Add a case matching values within the half-open range [start, end).

        Args:
            start (int): The inclusive lower bound of the range.
            end (int): The exclusive upper bound of the range.
            handler: A callable invoked on match or a constant to return.
            guard: An optional predicate that must also hold for the match.

        Returns:
            Match: This builder, for chaining further cases.

        Example:
            >>> match(9).case_range(1, 10, "single digit").execute()
            'single digit'
        """
        class _RangePattern:
            def __init__(self, s: int, e: int) -> None:
                self.start = s
                self.end = e
            def __eq__(self, other: object) -> bool:
                if isinstance(other, (int, float)):
                    return self.start <= other < self.end
                return NotImplemented
        self._cases.append(_Case(_RangePattern(start, end), handler, guard))
        return self

    def case_pred(
        self,
        predicate: Callable[[T], bool],
        handler: Callable[[T], R] | R | None = None,
    ) -> Match[T, R]:
        """Add a case that matches when a predicate returns True.

        Args:
            predicate (Callable[[T], bool]): Test that must return True.
            handler: A callable invoked on match or a constant to return.

        Returns:
            Match: This builder, for chaining further cases.

        Example:
            >>> match(4).case_pred(lambda n: n % 2 == 0, "even").execute()
            'even'
        """
        class _PredPattern:
            def __init__(self, pred: Callable[[T], bool]) -> None:
                self.pred = pred
            def __eq__(self, other: object) -> bool:
                return self.pred(other)  # type: ignore[arg-type]
        self._cases.append(_Case(_PredPattern(predicate), handler, None))
        return self

    def case_in(
        self,
        collection: Iterable[object],
        handler: Callable[[T], R] | R | None = None,
        *,
        guard: Callable[[T], bool] | None = None,
    ) -> Match[T, R]:
        """Add a case that matches when the value is contained in a collection.

        Args:
            collection (Iterable[object]): Container tested with ``in``.
            handler: A callable invoked on match or a constant to return.
            guard: An optional predicate that must also hold for the match.

        Returns:
            Match: This builder, for chaining further cases.

        Example:
            >>> match("b").case_in(("a", "b", "c"), "letter").execute()
            'letter'
        """
        class _InPattern:
            def __init__(self, coll: Iterable[object]) -> None:
                self.coll = coll
            def __eq__(self, other: object) -> bool:
                return other in self.coll
        self._cases.append(_Case(_InPattern(collection), handler, guard))
        return self

    def otherwise(self, handler: Callable[[T], R] | R) -> R:
        """Add a wildcard (default) case and evaluate the match.

        Args:
            handler: A callable invoked on match or a constant to return.

        Returns:
            R: The result of the first matching case (this final wildcard
            guarantees a result when reached).
        """
        self._cases.append(_Case(_, handler, None))
        return self.execute()

    def execute(self) -> R:
        """Evaluate all added cases and return the result of the first match.

        Returns:
            R: The result produced by the first matching case.

        Raises:
            MatchError: If no case matches and no wildcard was provided.
        """
        if self._executed:
            return self._result
        for case in self._cases:
            if case.matches(self._value):
                self._result = case.execute(self._value)
                self._executed = True
                return self._result
        raise MatchError(
            f"no match found for {self._value!r}"
        )

    def __repr__(self) -> str:
        """Return a string describing this match expression.

        Returns:
            str: The value and result if executed, else the value and case count.
        """
        if self._executed:
            return f"Match({self._value!r} => {self._result!r})"
        return f"Match({self._value!r}, {len(self._cases)} cases)"


class _MatchWildcard:
    """Wildcard marker matching any value for pattern matching.

    This is an internal sentinel powering the ``otherwise``/``_`` cases and is
    not intended for direct construction.
    """
    __slots__ = ()

    def __eq__(self, other: object) -> bool:
        """Match any value when used as a comparison wildcard.

        Args:
            other (object): The value being compared (ignored).

        Returns:
            bool: Always True.
        """
        return True

    def __hash__(self) -> int:
        """Return a fixed hash consistent with the wildcard's equality.

        Returns:
            int: A constant hash value.
        """
        return hash("_")

    def __repr__(self) -> str:
        """Return the wildcard symbol.

        Returns:
            str: The string ``"_"``.
        """
        return "_"


class _:
    """The wildcard sentinel, previously a built-in symbol.

    Instances of this class are exposed as the module-level ``_`` used to
    denote a catch-all case when adding a wildcard pattern (see ``_MatchWildcard``
    and ``Match``).
    """
    __slots__ = ()

    def __eq__(self, other: object) -> bool:
        """Match the wildcard sentinel against any value.

        Args:
            other (object): The value being compared (ignored).

        Returns:
            bool: Always True.
        """
        return True

    def __hash__(self) -> int:
        """Return a fixed hash consistent with the wildcard's equality.

        Returns:
            int: A constant hash value.
        """
        return hash("_")

    def __repr__(self) -> str:
        """Return the wildcard symbol.

        Returns:
            str: The string ``"_"``.
        """
        return "_"


_ = _MatchWildcard()


def match(value: T) -> Match[T, Any]:
    """Begin a pattern match over the given value.

    Returns a ``Match`` builder to which cases are added before execution.

    Args:
        value (T): The value to match against.

    Returns:
        Match: A builder for fluent pattern matching on ``value``.

    Example:
        >>> m = match("x").case_eq("x", "hit").otherwise("miss")
        >>> m
        'hit'
    """
    return Match(value)


class Variant:
    """A tagged union value consisting of a tag string and an associated payload.

    Produced by enumerating an ``Enum`` class; each ``Variant`` carries a tag
    name and a payload, and supports inspection and transformation methods.

    Example:
        >>> class Color(Enum):  # doctest: +SKIP
        ...     RED = "red"
        >>> Color.RED.tag  # doctest: +SKIP
        'red'
    """

    __slots__ = ("_tag", "_value", "_enum_cls")

    def __init__(self, tag: str, value: Any, enum_cls: type | None = None) -> None:
        """Create a variant with a tag, a payload, and an optional owning enum.

        Args:
            tag (str): The variant's tag name.
            value (Any): The payload carried by this variant.
            enum_cls (type, optional): The Enum class that produced this variant.
        """
        self._tag = tag
        self._value = value
        self._enum_cls = enum_cls

    @property
    def tag(self) -> str:
        """Return the variant's tag name.

        Returns:
            str: The tag identifying this variant.
        """
        return self._tag

    @property
    def value(self) -> Any:
        """Return the variant's inner payload.

        Returns:
            Any: The value carried by this variant.
        """
        return self._value

    def is_(self, *tags: str) -> bool:
        """Check whether this variant's tag matches any of the given tags.

        Args:
            *tags (str): One or more tag names to test against.

        Returns:
            bool: True if this variant's tag is among ``tags``, else False.

        Example:
            >>> Variant("a", 1).is_("a", "b")
            True
        """
        return self._tag in tags

    def unwrap(self) -> Any:
        """Return the inner value unconditionally.

        Returns:
            Any: The payload carried by this variant.
        """
        return self._value

    def unwrap_or(self, default: Any) -> Any:
        """Return the inner value, ignoring the default since a value is always present.

        Args:
            default (Any): Ignored; kept for Option/Result API consistency.

        Returns:
            Any: The payload carried by this variant.
        """
        return self._value

    def expect(self, message: str) -> Any:
        """Return the inner value, ignoring the message since it always succeeds.

        Args:
            message (str): Ignored; kept for Option/Result API consistency.

        Returns:
            Any: The payload carried by this variant.
        """
        return self._value

    def map(self, fn: Callable[[Any], Any]) -> Variant:
        """Apply a function to the inner value, returning a new Variant.

        Args:
            fn (Callable[[Any], Any]): Function applied to the payload.

        Returns:
            Variant: A new variant with the same tag and the transformed payload.

        Example:
            >>> Variant("n", 2).map(lambda v: v * 10).value
            20
        """
        return Variant(self._tag, fn(self._value), self._enum_cls)

    def map_or(self, default: Any, fn: Callable[[Any], Any]) -> Any:
        """Apply a function to the inner value and return its result.

        Args:
            default (Any): Ignored; kept for Option/Result API consistency.
            fn (Callable[[Any], Any]): Function applied to the payload.

        Returns:
            Any: The result of ``fn(self._value)``.
        """
        return fn(self._value)

    def and_then(self, fn: Callable[[Any], Variant]) -> Variant:
        """Chain a function that produces a new Variant from the inner value.

        Args:
            fn (Callable[[Any], Variant]): Function returning a Variant.

        Returns:
            Variant: The Variant produced by ``fn(self._value)``.
        """
        return fn(self._value)

    def or_else(self, fn: Callable[[str], Variant]) -> Variant:
        """Return self since a Variant is always present.

        Args:
            fn (Callable[[str], Variant]): Unused; kept for API consistency.

        Returns:
            Variant: This same variant.
        """
        return self

    def match(self, *cases: tuple[str, Callable[[Any], Any]]) -> Any:
        """Match this variant against tag-handler pairs and return the result.

        Cases are ``(tag, handler)`` tuples, optionally wrapping ``(tag, guard)``
        with a two-element pattern tuple, or a wildcard ``_`` as a catch-all.

        Args:
            *cases (tuple): ``(tag, handler)`` pairs or guarded/wildcard cases.

        Returns:
            Any: The result of the first matching handler.

        Raises:
            MatchError: If no case matches this variant.

        Example:
            >>> Variant("b", 3).match(("a", lambda v: v), ("b", lambda v: v * 2))
            6
        """
        for case in cases:
            pattern, handler = case[0], case[1]
            if isinstance(pattern, _MatchWildcard):
                return handler(self._value)
            if isinstance(pattern, tuple) and len(pattern) == 2:
                t, guard = pattern
                if t == self._tag and guard(self._value):
                    return handler(self._value)
            elif pattern == self._tag:
                return handler(self._value)
        raise MatchError(f"no match for {self!r}")

    def __eq__(self, other: object) -> bool:
        """Return True if another Variant has the same tag and value.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: True if tags and values are equal, else NotImplemented.
        """
        if isinstance(other, Variant):
            return self._tag == other._tag and self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        """Return a hash based on the tag and value.

        Returns:
            int: The hash of the ``(tag, value)`` pair.
        """
        return hash((self._tag, self._value))

    def __repr__(self) -> str:
        """Return a compact string representation of this variant.

        Returns:
            str: The tag alone if the value is None, else ``tag(value)``.
        """
        if self._value is None:
            return self._tag
        return f"{self._tag}({self._value!r})"


class _EnumMeta(type):
    """Metaclass that intercepts attribute access to create Variant instances.

    Collects declared variants from the class namespace during class creation
    and exposes each as an attribute returning a fresh ``Variant``.
    """

    def __new__(cls, name, bases, namespace) -> type:
        """Extract variant declarations from the namespace when the class is created.

        Args:
            name (str): The name of the new class.
            bases (tuple): The base classes of the new class.
            namespace (dict): The class body namespace.

        Returns:
            type: The newly created enum class with ``_variants`` attached.
        """
        variants = {}
        for key, val in list(namespace.items()):
            if key.startswith("_") or callable(val):
                continue
            if isinstance(val, tuple) and len(val) >= 1 and isinstance(val[0], str):
                variants[key] = val[1:]
            elif isinstance(val, str):
                variants[key] = (val,)
        namespace["_variants"] = variants
        for key in list(variants.keys()):
            if key in namespace:
                del namespace[key]
        obj = super().__new__(cls, name, bases, namespace)
        return obj

    def __getattr__(cls, name: str) -> Variant:
        """Return a Variant for the named attribute or raise AttributeError.

        Args:
            name (str): The variant tag being accessed.

        Returns:
            Variant: A variant instance for the requested tag.

        Raises:
            AttributeError: If the tag is private or not a defined variant.
        """
        if name.startswith("_"):
            raise AttributeError(name)
        variants = cls.__dict__.get("_variants", {})
        if name in variants:
            val = variants[name]
            return Variant(name, val[0] if len(val) == 1 else val, cls)
        raise AttributeError(f"enum {cls.__name__} has no variant '{name}'")


class Enum(metaclass=_EnumMeta):
    """Base class for defining tagged union enums with variant access via attributes.

    Subclass ``Enum`` and declare each variant as a string (or tuple) class
    attribute; attributes resolve to ``Variant`` instances at access time.

    Example:
        >>> class Status(Enum):
        ...     OK = "ok"
        ...     ERROR = "error", 500
        >>> Status.OK.tag
        'OK'
        >>> Status.OK.value
        'ok'
        >>> Status.ERROR.value
        500
    """

    @classmethod
    def variants(cls) -> list[str]:
        """Return the list of variant tag names defined on this enum.

        Returns:
            list[str]: The declared variant tag names in definition order.

        Example:
            >>> class Status(Enum):
            ...     OK = "ok"
            ...     ERROR = "error", 500
            >>> Status.variants()
            ['OK', 'ERROR']
        """
        return list(cls._variants.keys())  # type: ignore

    @classmethod
    def is_valid(cls, tag: str) -> bool:
        """Check whether the given tag is a valid variant of this enum.

        Args:
            tag (str): The tag name to check.

        Returns:
            bool: True if ``tag`` is a declared variant, else False.

        Example:
            >>> class Status(Enum):
            ...     OK = "ok"
            >>> Status.is_valid("OK")
            True
            >>> Status.is_valid("MISSING")
            False
        """
        return tag in cls._variants  # type: ignore

    def __repr__(self) -> str:
        """Return a string describing this enum instance.

        Returns:
            str: The class name and its instance dictionary.
        """
        return f"{type(self).__name__}({self.__dict__})"
