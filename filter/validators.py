"""Low-level validation predicates used by :mod:`oxide.filter`.

Every public predicate follows the same contract: it returns ``None`` when the
value is acceptable, or a human-readable failure reason when it is not. This
mirrors the ``Option[str]`` idiom used throughout ``oxide`` and lets the
``Filter`` class compose an error code with a message without re-inspecting
the value.

Predicates never raise for malformed input. A value of the wrong Python type is
simply reported as invalid rather than blowing up with a ``TypeError``.
"""

from __future__ import annotations

import ipaddress
import json
import re
import uuid
from datetime import date, datetime
from typing import Any
from urllib.parse import urlsplit


EMAIL_LOCAL = r"[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
EMAIL_LABEL = r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
EMAIL_RE = re.compile(
    r"\A" + EMAIL_LOCAL + r"@" + EMAIL_LABEL + r"(?:\." + EMAIL_LABEL + r")+\Z"
)
EMAIL_UNICODE_LOCAL = (
    r"[\w!#$%&'*+\-/=?^`{|}~¡-￿]+"
)
EMAIL_UNICODE_RE = re.compile(
    r"\A" + EMAIL_UNICODE_LOCAL + r"@" + EMAIL_LABEL + r"(?:\." + EMAIL_LABEL + r")+\Z"
)
LOCAL_PART_MAX = 64
DOMAIN_MAX = 253

SCHEME_RE = re.compile(r"\A[A-Za-z][A-Za-z0-9+.-]*\Z")
OPAQUE_SCHEMES = frozenset({"mailto", "urn", "data", "tel", "news", "sip", "magnet"})
PORT_RE = re.compile(r"\A\d{1,5}\Z")
HOSTNAME_LABEL_RE = re.compile(r"\A[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?\Z")
MAC_RE = re.compile(r"\A(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\Z")
MAC_RE_DASH = re.compile(r"\A(?:[0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}\Z")
MAC_RE_EUI48 = re.compile(r"\A(?:[0-9A-Fa-f]{2}-){7}[0-9A-Fa-f]{2}\Z")
HEX_RE = re.compile(r"\A(?:0[xX])?[0-9A-Fa-f]+\Z")
HEX_ODD_RE = re.compile(r"\A(?:0[xX])?[0-9A-Fa-f]*\Z")
SLUG_RE = re.compile(r"\A[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\Z")
ALPHA_RE = re.compile(r"\A[A-Za-z]+\Z")
ALPHA_NUM_RE = re.compile(r"\A[A-Za-z0-9]+\Z")
NUMERIC_RE = re.compile(r"\A[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?\Z")
INT_RE = re.compile(r"\A[+-]?\d+\Z")
FLOAT_RE = re.compile(r"\A[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z")
BOOLEAN_TRUE = frozenset({"1", "true", "on", "yes"})
BOOLEAN_FALSE = frozenset({"0", "false", "off", "no", ""})

FLAG_EMAIL_UNICODE = 1 << 0
FLAG_ALLOW_FRACTION = 1 << 1


def is_string(value: Any) -> str | None:
    """Return None if value is a string, else the failure reason."""
    if isinstance(value, str):
        return None
    return "a string"


def is_boolean(value: Any) -> str | None:
    """Return None if value is a PHP-acceptable boolean, else the reason."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value in (0, 1):
        return None
    if isinstance(value, str) and value.strip().lower() in BOOLEAN_TRUE | BOOLEAN_FALSE:
        return None
    return "a boolean"


def boolean(value: Any) -> bool | None:
    """Coerce value to a bool, or return None when not boolean-like.

    Args:
        value: The value to coerce.

    Returns:
        bool | None: The coerced boolean, or None if uncoercible.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        text = value.strip().lower()
        if text in BOOLEAN_TRUE:
            return True
        if text in BOOLEAN_FALSE:
            return False
    return None


def is_int(value: Any, allow_fraction: bool = False) -> str | None:
    """Return None if value is an integer, else the failure reason.

    Args:
        value: The value to test.
        allow_fraction (bool): When True, floats with no fractional part pass.
    """
    if isinstance(value, bool):
        return "an integer"
    if isinstance(value, int):
        return None
    if isinstance(value, float):
        if allow_fraction and value.is_integer():
            return None
        return "an integer"
    if isinstance(value, str):
        text = value.strip()
        if INT_RE.match(text):
            return None
        if allow_fraction and FLOAT_RE.match(text) and float(text).is_integer():
            return None
    return "an integer"


def as_int(value: Any, allow_fraction: bool = False) -> int | None:
    """Coerce value to an int, or return None when not convertible.

    Args:
        value: The value to coerce.
        allow_fraction (bool): When True, floats with no fraction are accepted.
    """
    if is_int(value, allow_fraction) is not None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if INT_RE.match(text):
        return int(text)
    return int(float(text))


def is_float(value: Any) -> str | None:
    """Return None if value is a float or float-like, else the reason."""
    if isinstance(value, bool):
        return "a float"
    if isinstance(value, float):
        return None
    if isinstance(value, int):
        return None
    if isinstance(value, str) and FLOAT_RE.match(value.strip()):
        return None
    return "a float"


def as_float(value: Any) -> float | None:
    """Coerce value to a float, or return None when not convertible."""
    if is_float(value) is not None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value).strip())


def is_email(value: Any, unicode_ok: bool = False) -> str | None:
    """Return None if value is a syntactically valid email address.

    Enforces a local part of at most 64 characters, a total length of at most
    254 characters, and a dotted domain. Label length and hyphen placement are
    validated to reject addresses that no mail transport would accept.

    Args:
        value: The candidate address.
        unicode_ok (bool): When True, allow non-ASCII characters in the local
            part, mirroring PHP's ``FILTER_FLAG_EMAIL_UNICODE``.
    """
    if not isinstance(value, str):
        return "an email address"
    if not value or len(value) > LOCAL_PART_MAX + DOMAIN_MAX + 1:
        return "an email address"
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        return "an email address"
    if value.count("@") != 1:
        return "an email address"
    local, _, domain = value.partition("@")
    if not local or len(local) > LOCAL_PART_MAX:
        return "an email address"
    if local.startswith(".") or local.endswith(".") or ".." in local:
        return "an email address"
    if local.startswith('"') and local.endswith('"') and len(local) > 1:
        pattern = EMAIL_UNICODE_RE if unicode_ok else EMAIL_RE
        return None if pattern.match(value) is None else "an email address"
    pattern = EMAIL_UNICODE_RE if unicode_ok else EMAIL_RE
    return None if pattern.match(value) is not None else "an email address"


def is_url(value: Any, require_path: bool = False) -> str | None:
    """Return None if value is a well-formed absolute URL.

    Requires a syntactically valid scheme and, for hierarchical schemes such as
    http, a host component. Ports outside 0-65535 and hosts containing illegal
    characters are rejected.

    Args:
        value: The candidate URL.
        require_path (bool): When True, a non-root path or query is mandatory,
            mirroring PHP's ``FILTER_FLAG_PATHNAME_REQUIRED``.

    Returns:
        str | None: None when valid, otherwise the failure reason.
    """
    if not isinstance(value, str):
        return "a URL"
    if not value or any(ord(ch) <= 32 or ord(ch) == 127 for ch in value):
        return "a URL"
    try:
        parts = urlsplit(value)
    except ValueError:
        return "a URL"
    if not SCHEME_RE.match(parts.scheme):
        return "a URL"
    if parts.scheme in OPAQUE_SCHEMES:
        remainder = parts.path or parts.netloc
        if not remainder:
            return "a URL"
    elif not parts.netloc:
        return "a URL"
    if parts.netloc:
        host = parts.hostname
        if host is None or not host:
            return "a URL"
        try:
            port = parts.port
        except ValueError:
            return "a URL"
        if port is not None and not 0 <= port <= 65535:
            return "a URL"
        if any(ch in host for ch in " \t\n\r"):
            return "a URL"
    if require_path and not (parts.path.strip("/") or parts.query):
        return "a URL with a path"
    return None


def is_ip(value: Any, version: int | None = None) -> str | None:
    """Return None if value is a valid IP address.

    Args:
        value: The candidate address.
        version (int, optional): 4 or 6 to restrict to one IP version.

    Returns:
        str | None: None when valid, otherwise the failure reason.
    """
    if not isinstance(value, str):
        return "an IP address"
    try:
        parsed = ipaddress.ip_address(value.strip())
    except ValueError:
        return "an IP address"
    if version == 4 and parsed.version != 4:
        return "an IPv4 address"
    if version == 6 and parsed.version != 6:
        return "an IPv6 address"
    return None


def is_domain(value: Any) -> str | None:
    """Return None if value is a valid hostname or domain name.

    Rejects empty labels, labels longer than 63 characters, leading or trailing
    hyphens, and all-numeric top-level labels, so ``1.2.3.4`` and ``-bad.com``
    both fail.
    """
    if not isinstance(value, str):
        return "a domain"
    host = value.strip()
    if not host or len(host) > DOMAIN_MAX:
        return "a domain"
    if host.endswith("."):
        host = host[:-1]
    if not host:
        return "a domain"
    labels = host.split(".")
    if any(not label for label in labels):
        return "a domain"
    if not all(HOSTNAME_LABEL_RE.match(label) for label in labels):
        return "a domain"
    if len(labels) == 1 and labels[0].isdigit():
        return "a domain"
    if len(labels) > 1 and labels[-1].isdigit():
        return "a domain"
    return None


def is_regex(value: Any) -> str | None:
    """Return None if value is a syntactically valid regular expression.

    Compiles with ``re.compile`` so an invalid pattern is reported rather than
    raising.
    """
    if not isinstance(value, str):
        return "a regular expression"
    try:
        re.compile(value)
    except re.error:
        return "a valid regular expression"
    return None


def is_mac(value: Any) -> str | None:
    """Return None if value is a valid MAC address in any common notation."""
    if not isinstance(value, str):
        return "a MAC address"
    text = value.strip()
    for pattern in (MAC_RE, MAC_RE_DASH, MAC_RE_EUI48):
        if pattern.match(text):
            return None
    return "a MAC address"


def is_hex(value: Any, even_length: bool = False) -> str | None:
    """Return None if value is a valid hexadecimal string.

    Args:
        value: The candidate string.
        even_length (bool): When True, an odd digit count is rejected.
    """
    if not isinstance(value, str):
        return "a hexadecimal string"
    text = value.strip()
    if not text:
        return "a hexadecimal string"
    if not HEX_ODD_RE.match(text):
        return "a hexadecimal string"
    digits = text[2:] if text[:2].lower() == "0x" else text
    if even_length and len(digits) % 2 != 0:
        return "a hexadecimal string of even length"
    return None


def is_uuid(value: Any) -> str | None:
    """Return None if value is a valid UUID in canonical form."""
    if not isinstance(value, str):
        return "a UUID"
    try:
        uuid.UUID(value.strip())
    except (ValueError, AttributeError, TypeError):
        return "a UUID"
    return None


def is_alpha(value: Any) -> str | None:
    """Return None if value contains only ASCII letters."""
    if not isinstance(value, str) or not ALPHA_RE.match(value):
        return "only letters"
    return None


def is_alpha_numeric(value: Any) -> str | None:
    """Return None if value contains only ASCII letters and digits."""
    if not isinstance(value, str) or not ALPHA_NUM_RE.match(value):
        return "only letters and numbers"
    return None


def is_slug(value: Any) -> str | None:
    """Return None if value is a lowercase-hyphenated slug."""
    if not isinstance(value, str) or not SLUG_RE.match(value):
        return "a valid slug"
    return None


def is_numeric(value: Any) -> str | None:
    """Return None if value is a number or a numeric string."""
    if isinstance(value, bool):
        return "a number"
    if isinstance(value, (int, float)):
        return None
    if isinstance(value, str) and NUMERIC_RE.match(value.strip()):
        return None
    return "a number"


def as_number(value: Any) -> float | None:
    """Coerce value to a float for numeric comparisons, or None."""
    if is_numeric(value) is not None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value).strip())


def is_json(value: Any) -> str | None:
    """Return None if value is a string containing valid JSON."""
    if isinstance(value, (dict, list)):
        return None
    if not isinstance(value, str):
        return "a valid JSON string"
    try:
        json.loads(value)
    except (ValueError, TypeError):
        return "a valid JSON string"
    return None


def is_date(value: Any) -> str | None:
    """Return None if value parses as an ISO 8601 date or datetime.

    Accepts ``datetime``/``date`` instances directly and, for strings, the forms
    ``YYYY-MM-DD``, ``YYYY/MM/DD``, and full ISO 8601 timestamps.
    """
    if isinstance(value, (datetime, date)):
        return None
    if not isinstance(value, str):
        return "a valid date"
    text = value.strip()
    if not text:
        return "a valid date"
    normalized = text.replace("/", "-")
    for pattern, parser in (
        ("%Y-%m-%d", _parse_date_only),
        ("%Y-%m-%dT%H:%M:%S", _parse_datetime_seconds),
        ("%Y-%m-%d %H:%M:%S", _parse_datetime_seconds),
        ("%Y-%m-%dT%H:%M", _parse_datetime_minutes),
    ):
        if _matches_shape(normalized, pattern):
            if parser(normalized) is None:
                return "a valid date"
            return None
    try:
        datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        return "a valid date"
    return None


def _matches_shape(text: str, pattern: str) -> bool:
    """Return True if text's length and separator layout fit the pattern."""
    expected = pattern.replace("%Y", "4").replace("%m", "2").replace("%d", "2")
    expected = expected.replace("%H", "2").replace("%M", "2").replace("%S", "2")
    if len(text) != len(expected):
        return False
    for actual, placeholder in zip(text, expected):
        if not placeholder.isdigit():
            if actual != placeholder:
                return False
        elif not actual.isdigit():
            return False
    return True


def _parse_date_only(text: str) -> date | None:
    """Parse a YYYY-MM-DD string, returning None when invalid."""
    try:
        return date(int(text[0:4]), int(text[5:7]), int(text[8:10]))
    except ValueError:
        return None


def _parse_datetime_seconds(text: str) -> datetime | None:
    """Parse a YYYY-MM-DDTHH:MM:SS string, returning None when invalid."""
    day = text[0:10].replace("-", "/")
    try:
        return datetime(
            int(day[0:4]), int(day[5:7]), int(day[8:10]),
            int(text[11:13]), int(text[14:16]), int(text[17:19]),
        )
    except ValueError:
        return None


def _parse_datetime_minutes(text: str) -> datetime | None:
    """Parse a YYYY-MM-DDTHH:MM string, returning None when invalid."""
    day = text[0:10].replace("-", "/")
    try:
        return datetime(
            int(day[0:4]), int(day[5:7]), int(day[8:10]),
            int(text[11:13]), int(text[14:16]),
        )
    except ValueError:
        return None


def matches_regex(value: Any, pattern: str) -> str | None:
    """Return None if value fully matches pattern, else the failure reason.

    Uses ``re.fullmatch`` so the pattern must describe the entire value, which
    mirrors PHP's ``FILTER_VALIDATE_REGEXP`` semantics.
    """
    if not isinstance(value, str):
        return "a string matching the required format"
    try:
        compiled = re.compile(pattern)
    except re.error:
        return "a string matching a valid pattern"
    if compiled.fullmatch(value) is None:
        return "a string matching the required format"
    return None