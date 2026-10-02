"""Filter subpackage — PHP ``filter_var()``-style validation and sanitization.

Exposes :class:`Filter` with the familiar ``FILTER_VALIDATE_*`` and
``FILTER_SANITIZE_*`` constants, plus the module-level ``validate_var``,
``filter_var``, ``is_valid``, and ``sanitize_var`` helpers.

Example:
    >>> from oxide.filter import Filter
    >>> Filter.validate("user@example.com", Filter.EMAIL).is_ok()
    True
    >>> Filter.sanitize(" hi <b>there</b> ", Filter.SANITIZE_STRIPPED)
    'hi there'
"""

from __future__ import annotations

from .filter import (
    Filter, FilterError, validate_var, filter_var, is_valid, sanitize_var,
)

__all__ = [
    "Filter",
    "FilterError",
    "validate_var",
    "filter_var",
    "is_valid",
    "sanitize_var",
]