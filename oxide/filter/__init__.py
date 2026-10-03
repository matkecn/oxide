"""Filter subpackage — PHP ``filter_var()``-style validation and sanitization.

Exposes :class:`Filter` with the familiar ``FILTER_VALIDATE_*`` and
``FILTER_SANITIZE_*`` constants, plus the :class:`FilterError` error type.

All operations live on the :class:`Filter` class: ``Filter.validate``,
``Filter.is_valid``, ``Filter.var``, and ``Filter.sanitize``. There are no
module-level ``validate_var``/``filter_var``/``is_valid``/``sanitize_var``
pass-throughs — use the class, or call the low-level predicates and sanitizers
directly from :mod:`oxide.filter.validators` and
:mod:`oxide.filter.sanitizers`.

Example:
    >>> from oxide.filter import Filter
    >>> Filter.validate("user@example.com", Filter.EMAIL).is_ok()
    True
    >>> Filter.sanitize(" hi <b>there</b> ", Filter.SANITIZE_STRIPPED)
    'hi there'
"""

from __future__ import annotations

from .filter import Filter, FilterError

__all__ = [
    "Filter",
    "FilterError",
]
