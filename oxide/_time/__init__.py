"""Time utilities: Duration, Instant, SystemTime, and UNIX_EPOCH.

Re-exports ``Duration`` (spans of time with arithmetic), ``Instant``
(monotonic timestamps for elapsed measurement), ``SystemTime`` (wall-clock
time with datetime conversion), the ``UNIX_EPOCH`` constant, and the
``Elapsed`` exception raised on timer/clock failures.
"""
from __future__ import annotations

from .duration import Duration, UNIX_EPOCH, Elapsed
from .instant import Instant
from .system_time import SystemTime

__all__ = [
    "Duration",
    "UNIX_EPOCH",
    "Elapsed",
    "Instant",
    "SystemTime",
]
