"""Filter — PHP ``filter_var()``-style validation and sanitization.

The :class:`Filter` class is a dependency-free port of PHP's filter extension.
It exposes the familiar ``FILTER_VALIDATE_*`` and ``FILTER_SANITIZE_*``
constants, the same flag bits, and the same ``options`` dictionary, but returns
``oxide`` :class:`Result` values instead of PHP's ``false``/``null`` sentinel.

Example:
    >>> Filter.validate("a@b.com", Filter.EMAIL).is_ok()
    True
    >>> Filter.sanitize("<b>hi</b>", Filter.SANITIZE_SPECIAL_CHARS)
    '&lt;b&gt;hi&lt;/b&gt;'
    >>> Filter.is_valid("nope", Filter.URL)
    False
"""

from __future__ import annotations

from typing import Any, Callable

from ..core.result import Result, Ok, Err
from . import sanitizers as _san
from . import validators as _val


class FilterError(Exception):
    """Raised or returned when a value fails a filter.

    Carries the filter that rejected the value and a human-readable reason, so
    callers can report exactly what was wrong instead of a bare ``False``.

    Example:
        >>> Filter.validate("x", Filter.EMAIL).unwrap_err().reason()
        'an email address'
    """

    __slots__ = ("_filter", "_reason")

    def __init__(self, filter_name: str, reason: str) -> None:
        """Create a filter failure for a specific filter.

        Args:
            filter_name (str): The name of the filter that rejected the value.
            reason (str): A human-readable description of the failure.
        """
        super().__init__(f"{filter_name}: {reason}")
        self._filter = filter_name
        self._reason = reason

    def filter(self) -> str:
        """Return the name of the filter that rejected the value.

        Returns:
            str: The filter name.
        """
        return self._filter

    def reason(self) -> str:
        """Return the human-readable failure reason.

        Returns:
            str: The reason the value was rejected.
        """
        return self._reason

    def __repr__(self) -> str:
        return f"FilterError({self._filter!r}, {self._reason!r})"


class Filter:
    """Registry of validation and sanitization filters.

    Filter names are plain strings so custom filters can be registered at
    runtime and composed with the built-ins. Validation returns the coerced
    value on success, so ``Filter.validate("42", Filter.INT)`` yields ``Ok(42)``
    rather than the original string.

    Example:
        >>> Filter.validate(" 42 ", Filter.INT)
        Ok(value=42)
        >>> Filter.register("shout", sanitizer=lambda text, flags: text.upper())
        >>> Filter.sanitize("hi", "shout")
        'HI'
    """

    BOOLEAN = "boolean"
    INT = "int"
    FLOAT = "float"
    NUMERIC = "numeric"
    EMAIL = "email"
    URL = "url"
    IP = "ip"
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    DOMAIN = "domain"
    REGEXP = "regexp"
    MAC = "mac"
    HEX = "hex"
    UUID = "uuid"
    ALPHA = "alpha"
    ALPHA_NUMERIC = "alpha_numeric"
    SLUG = "slug"
    JSON = "json"
    DATE = "date"

    SANITIZE_EMAIL = "sanitize_email"
    SANITIZE_URL = "sanitize_url"
    SANITIZE_URL_RAW = "sanitize_url_raw"
    SANITIZE_NUMBER_INT = "sanitize_number_int"
    SANITIZE_NUMBER_FLOAT = "sanitize_number_float"
    SANITIZE_SPECIAL_CHARS = "sanitize_special_chars"
    SANITIZE_STRING = "sanitize_string"
    SANITIZE_STRIPPED = "sanitize_stripped"
    SANITIZE_ENCODED = "sanitize_encoded"

    NULL_ON_FAILURE = 1 << 0
    REQUIRE_ARRAY = 1 << 1
    EMAIL_UNICODE = 1 << 2
    ALLOW_FRACTION = 1 << 3
    PATHNAME_REQUIRED = 1 << 4
    EVEN_LENGTH = 1 << 5

    REGEXP_MATCHED = "regexp_matched"

    _validators: dict[str, Callable[[Any, int, dict], str | None]] = {}
    _sanitizers: dict[str, Callable[[Any, int], Any]] = {}

    @classmethod
    def _init_registry(cls) -> None:
        """Populate the built-in validator and sanitizer tables."""
        if cls._validators:
            return
        cls._validators = {
            cls.BOOLEAN: _bool_validator,
            cls.INT: _int_validator,
            cls.FLOAT: _float_validator,
            cls.NUMERIC: _numeric_validator,
            cls.EMAIL: _email_validator,
            cls.URL: _url_validator,
            cls.IP: _ip_validator,
            cls.IPV4: _ipv4_validator,
            cls.IPV6: _ipv6_validator,
            cls.DOMAIN: _unary(_val.is_domain),
            cls.REGEXP: _regexp_validator,
            cls.MAC: _unary(_val.is_mac),
            cls.HEX: _hex_validator,
            cls.UUID: _unary(_val.is_uuid),
            cls.ALPHA: _unary(_val.is_alpha),
            cls.ALPHA_NUMERIC: _unary(_val.is_alpha_numeric),
            cls.SLUG: _unary(_val.is_slug),
            cls.JSON: _unary(_val.is_json),
            cls.DATE: _unary(_val.is_date),
        }
        cls._sanitizers = {
            cls.SANITIZE_EMAIL: _unary(_san.sanitize_email),
            cls.SANITIZE_URL: _unary(_san.sanitize_url),
            cls.SANITIZE_URL_RAW: _unary(_san.sanitize_url_raw),
            cls.SANITIZE_NUMBER_INT: _unary(_san.sanitize_number_int),
            cls.SANITIZE_NUMBER_FLOAT: _unary(_san.sanitize_number_float),
            cls.SANITIZE_SPECIAL_CHARS: _unary(_san.sanitize_string),
            cls.SANITIZE_STRING: _unary(_san.sanitize_string),
            cls.SANITIZE_STRIPPED: _unary(_san.sanitize_stripped),
            cls.SANITIZE_ENCODED: _unary(_san.sanitize_encoded),
        }

    @classmethod
    def register(
        cls,
        name: str,
        validator: Callable[[Any, int, dict], str | None] | None = None,
        sanitizer: Callable[[Any, int], Any] | None = None,
    ) -> None:
        """Register a custom validator or sanitizer under a new name.

        Args:
            name (str): The filter name to register.
            validator (Callable, optional): Called as ``fn(value, flags,
                options)``. Return None when the value is acceptable, or a
                reason string when it is not.
            sanitizer (Callable, optional): Called as ``fn(value, flags)`` and
                returns the sanitized value.

        Raises:
            ValueError: If neither a validator nor a sanitizer is supplied.
        """
        cls._init_registry()
        if validator is None and sanitizer is None:
            raise ValueError("register() requires a validator or a sanitizer")
        if validator is not None:
            cls._validators[name] = validator
        if sanitizer is not None:
            cls._sanitizers[name] = sanitizer

    @classmethod
    def unregister(cls, name: str) -> None:
        """Remove a custom filter, ignoring built-in names.

        Args:
            name (str): The filter name to remove.
        """
        cls._init_registry()
        cls._validators.pop(name, None)
        cls._sanitizers.pop(name, None)

    @classmethod
    def filters(cls) -> list[str]:
        """Return every registered validator and sanitizer name.

        Returns:
            list[str]: Sorted filter names.
        """
        cls._init_registry()
        return sorted(set(cls._validators) | set(cls._sanitizers))

    @classmethod
    def is_validator(cls, name: str) -> bool:
        """Return whether a validator is registered under the given name."""
        cls._init_registry()
        return name in cls._validators

    @classmethod
    def is_sanitizer(cls, name: str) -> bool:
        """Return whether a sanitizer is registered under the given name."""
        cls._init_registry()
        return name in cls._sanitizers

    @classmethod
    def validate(
        cls,
        value: Any,
        filter_name: str,
        flags: int = 0,
        options: dict | None = None,
    ) -> Result:
        """Validate a value against a registered filter.

        Args:
            value (Any): The value to validate.
            filter_name (str): A validator name such as ``Filter.EMAIL``.
            flags (int): Filter flag bits, combined with ``|``.
            options (dict, optional): Filter options. ``REGEXP`` reads the
                ``"regexp"`` key; ``HEX`` reads ``"even_length"``.

        Returns:
            Result: ``Ok(coerced_value)`` when valid, otherwise
            ``Err(FilterError)`` describing the failure. When ``REQUIRE_ARRAY``
            is set and the input is a sequence, each element is validated and an
            ``Ok(list)`` of coerced values is returned.

        Raises:
            ValueError: If ``filter_name`` is not a registered validator.

        Example:
            >>> Filter.validate("2024-02-30", Filter.DATE).is_ok()
            False
            >>> Filter.validate(["1", "2"], Filter.INT, Filter.REQUIRE_ARRAY)
            Ok(value=[1, 2])
        """
        cls._init_registry()
        validator = cls._validators.get(filter_name)
        if validator is None:
            raise ValueError(f"unknown validator: {filter_name!r}")
        opts = dict(options) if options else {}
        if flags & cls.REQUIRE_ARRAY:
            if not isinstance(value, (list, tuple)):
                return Err(FilterError(filter_name, "an array"))
            coerced: list = []
            for item in value:
                if isinstance(item, (list, tuple)):
                    return Err(FilterError(filter_name, "an array"))
                reason = validator(item, flags, opts)
                if reason is not None:
                    return Err(FilterError(filter_name, reason))
                coerced.append(_coerce(filter_name, item, flags, opts))
            return Ok(coerced)
        if isinstance(value, (list, tuple, dict, set)):
            return Err(FilterError(filter_name, "a scalar value"))
        reason = validator(value, flags, opts)
        if reason is not None:
            return Err(FilterError(filter_name, reason))
        return Ok(_coerce(filter_name, value, flags, opts))

    @classmethod
    def is_valid(
        cls,
        value: Any,
        filter_name: str,
        flags: int = 0,
        options: dict | None = None,
    ) -> bool:
        """Return whether a value passes a filter, discarding the reason.

        Args:
            value (Any): The value to check.
            filter_name (str): A validator name.
            flags (int): Filter flag bits.
            options (dict, optional): Filter options.

        Returns:
            bool: True when the value validates.
        """
        return cls.validate(value, filter_name, flags, options).is_ok()

    @classmethod
    def var(
        cls,
        value: Any,
        filter_name: str,
        flags: int = 0,
        options: dict | None = None,
    ) -> Any:
        """Validate with PHP ``filter_var`` return semantics.

        Returns the coerced value on success, or ``None`` on failure. When
        ``NULL_ON_FAILURE`` is not set, failures return ``False`` instead.

        Args:
            value (Any): The value to validate.
            filter_name (str): A validator name.
            flags (int): Filter flag bits.
            options (dict, optional): Filter options.

        Returns:
            Any: The coerced value, ``None``, or ``False`` on failure.
        """
        outcome = cls.validate(value, filter_name, flags, options)
        if outcome.is_ok():
            return outcome.unwrap()
        return None if flags & cls.NULL_ON_FAILURE else False

    @classmethod
    def sanitize(cls, value: Any, filter_name: str, flags: int = 0) -> Any:
        """Sanitize a value with a registered sanitizer.

        Args:
            value (Any): The value to sanitize.
            filter_name (str): A sanitizer name such as
                ``Filter.SANITIZE_EMAIL``.
            flags (int): Reserved for flag-aware sanitizers.

        Returns:
            Any: The sanitized value.

        Raises:
            ValueError: If ``filter_name`` is not a registered sanitizer.

        Example:
            >>> Filter.sanitize("1,2.5abc", Filter.SANITIZE_NUMBER_FLOAT)
            '12.5'
        """
        cls._init_registry()
        sanitizer = cls._sanitizers.get(filter_name)
        if sanitizer is None:
            raise ValueError(f"unknown sanitizer: {filter_name!r}")
        return sanitizer(value, flags)


def _unary(predicate: Callable[[Any], str | None]) -> Callable[..., str | None]:
    """Adapt a one-argument validator to the registry's calling convention.

    Args:
        predicate (Callable): A validator taking only the value.

    Returns:
        Callable: A validator accepting ``(value, flags, options)``.
    """
    def adapted(value: Any, flags: int = 0, options: dict | None = None) -> str | None:
        return predicate(value)
    return adapted


def _coerce(filter_name: str, value: Any, flags: int, options: dict) -> Any:
    """Convert a validated value to its native Python type."""
    if filter_name == Filter.BOOLEAN:
        return _val.boolean(value)
    if filter_name == Filter.INT:
        return _val.as_int(value, bool(flags & Filter.ALLOW_FRACTION))
    if filter_name == Filter.FLOAT:
        return _val.as_float(value)
    if filter_name == Filter.NUMERIC:
        if isinstance(value, (int, float)):
            return value
        return _val.as_number(value)
    if filter_name == Filter.REGEXP:
        matched = options.get(Filter.REGEXP_MATCHED)
        return value if matched is None else matched
    if filter_name == Filter.IP:
        return str(value).strip()
    return value


def _bool_validator(value: Any, flags: int, options: dict) -> str | None:
    """Validate a value as a PHP-acceptable boolean."""
    return _val.is_boolean(value)


def _int_validator(value: Any, flags: int, options: dict) -> str | None:
    """Validate a value as an integer, honouring ALLOW_FRACTION."""
    return _val.is_int(value, bool(flags & Filter.ALLOW_FRACTION))


def _float_validator(value: Any, flags: int, options: dict) -> str | None:
    """Validate a value as a float."""
    return _val.is_float(value)


def _numeric_validator(value: Any, flags: int, options: dict) -> str | None:
    """Validate a value as a number."""
    return _val.is_numeric(value)


def _email_validator(value: Any, flags: int, options: dict) -> str | None:
    """Validate a value as an email address."""
    return _val.is_email(value, bool(flags & Filter.EMAIL_UNICODE))


def _url_validator(value: Any, flags: int, options: dict) -> str | None:
    """Validate a value as a URL, honouring PATHNAME_REQUIRED."""
    return _val.is_url(value, bool(flags & Filter.PATHNAME_REQUIRED))


def _ip_validator(value: Any, flags: int, options: dict) -> str | None:
    """Validate a value as an IP address of either version."""
    return _val.is_ip(value, None)


def _ipv4_validator(value: Any, flags: int, options: dict) -> str | None:
    """Validate a value as an IPv4 address."""
    return _val.is_ip(value, 4)


def _ipv6_validator(value: Any, flags: int, options: dict) -> str | None:
    """Validate a value as an IPv6 address."""
    return _val.is_ip(value, 6)


def _regexp_validator(value: Any, flags: int, options: dict) -> str | None:
    """Validate a value against the pattern supplied in options."""
    pattern = options.get("regexp")
    if pattern is None:
        return "a regular expression option"
    return _val.matches_regex(value, pattern)


def _hex_validator(value: Any, flags: int, options: dict) -> str | None:
    """Validate a value as hexadecimal, honouring EVEN_LENGTH."""
    even = bool(flags & Filter.EVEN_LENGTH) or bool(options.get("even_length"))
    return _val.is_hex(value, even)
