"""Low-level sanitizers used by :mod:`oxide.filter`.

Each sanitizer coerces a value to a string and then strips every character that
is not part of its allowed character set. Sanitizing never raises: values that
are not string-like are coerced with ``str()`` first, mirroring PHP's behaviour
of operating on the scalar cast of the input.

The allowed character sets are documented per function so the behaviour can be
audited without reading the implementation.
"""

from __future__ import annotations

import html
import re
from typing import Any

URL_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    "-_.~!*'()%&#?="
)

URL_RAW_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    "-_.~!*'()%&#?=;:@+$,[]/"
)

EMAIL_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    "-_.!#$%&'*+/=?^`{|}~@"
)

NUMBER_TRIM_RE = re.compile(r"\s+|[\x00-\x1f\x7f]")
FLOAT_RE = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")
TAG_RE = re.compile(r"<[^>]*>")


def _as_text(value: Any) -> str:
    """Coerce value to a string for sanitizing."""
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else ""
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", "replace")
    if isinstance(value, (list, tuple, dict, set)):
        return ""
    return str(value)


def sanitize_email(value: Any) -> str:
    """Strip every character not legal in an email address.

    Keeps ASCII letters, digits, and ``-_.!#$%&'*+/=?^`{|}~@``. Note that the
    local part may retain characters that are illegal in a position, so the
    result is not guaranteed to pass validation.

    Args:
        value: The value to sanitize.

    Returns:
        str: The sanitized string.
    """
    return "".join(ch for ch in _as_text(value) if ch in EMAIL_CHARS)


def sanitize_url(value: Any) -> str:
    """Strip every character not legal in a URL.

    Keeps ASCII letters, digits, and ``-_.~!*'()%&#?=``. Characters such as
    ``<``, ``>``, ``"``, backtick, and whitespace are removed.

    Args:
        value: The value to sanitize.

    Returns:
        str: The sanitized string.
    """
    return "".join(ch for ch in _as_text(value) if ch in URL_CHARS)


def sanitize_url_raw(value: Any) -> str:
    """Strip unsafe characters from a URL while preserving its separators.

    Behaves like :func:`sanitize_url` but additionally keeps ``; : @ + $ , [ ]``
    so that ports, userinfo, and query separators survive.

    Args:
        value: The value to sanitize.

    Returns:
        str: The sanitized string.
    """
    return "".join(ch for ch in _as_text(value) if ch in URL_RAW_CHARS)


def sanitize_number_int(value: Any) -> str:
    """Extract an integer from a value by discarding non-numeric characters.

    Every character that is not a digit is removed, except a ``+`` or ``-`` that
    appears at position zero. This mirrors PHP's ``FILTER_SANITIZE_NUMBER_INT``,
    so ``"$1,234.56"`` sanitizes to ``"1234"``. Returns "" when no digit remains.

    Args:
        value: The value to sanitize.

    Returns:
        str: The integer substring, or "" when none is present.
    """
    text = _as_text(value)
    sign = ""
    if text[:1] in ("+", "-"):
        sign = text[0]
        text = text[1:]
    digits = "".join(ch for ch in text if ch.isdigit() and ch.isascii())
    if not digits:
        return ""
    return sign + digits


def sanitize_number_float(value: Any) -> str:
    """Extract a float from a value by discarding non-numeric characters.

    Keeps digits, a single decimal point, a leading sign, and scientific
    notation in exponent position. Returns "" when the remaining characters do
    not form a valid number.

    Args:
        value: The value to sanitize.

    Returns:
        str: The numeric substring, or "" when none is present.

    Example:
        >>> sanitize_number_float(" 1,234.56abc")
        '1234.56'
    """
    text = _as_text(value)
    sign = ""
    if text[:1] in ("+", "-"):
        sign = text[0]
        text = text[1:]
    out: list[str] = []
    seen_point = False
    seen_exponent = False
    for index, ch in enumerate(text):
        if ch.isascii() and ch.isdigit():
            out.append(ch)
        elif ch == "." and not seen_point and not seen_exponent:
            seen_point = True
            out.append(ch)
        elif ch in "eE" and not seen_exponent and out and out[-1].isdigit():
            seen_exponent = True
            out.append(ch)
        elif ch in "+-" and seen_exponent and out and out[-1] in "eE":
            out.append(ch)
    number = sign + "".join(out)
    if not number or FLOAT_RE.fullmatch(number) is None:
        return ""
    return number


def sanitize_string(value: Any) -> str:
    """Escape HTML special characters.

    Encodes ``&``, ``<``, ``>``, ``"``, and ``'`` as HTML entities so the value
    can be embedded in markup safely. Equivalent to PHP's
    ``FILTER_SANITIZE_SPECIAL_CHARS``.

    Args:
        value: The value to sanitize.

    Returns:
        str: The HTML-escaped string.
    """
    return html.escape(_as_text(value), quote=True)


def sanitize_stripped(value: Any) -> str:
    """Remove HTML tags and leading/trailing whitespace.

    Equivalent to PHP's ``FILTER_SANITIZE_STRIPPED``.

    Args:
        value: The value to sanitize.

    Returns:
        str: The stripped string.
    """
    return TAG_RE.sub("", _as_text(value)).strip()


def sanitize_encoded(value: Any) -> str:
    """Decode HTML entities back to their literal characters.

    Args:
        value: The value to sanitize.

    Returns:
        str: The decoded string.
    """
    return html.unescape(_as_text(value))