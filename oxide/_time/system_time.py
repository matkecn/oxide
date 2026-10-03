"""SystemTime: wall-clock time with datetime conversion.

Provides ``SystemTime`` for calendar-based time operations, conversion to and
from ``datetime``, computing durations since the Unix epoch or between two
points, and arithmetic with Durations.
"""
from __future__ import annotations

import datetime as _dt_module

from .duration import Duration, Elapsed


class SystemTime:
    """Wall-clock time with nanosecond precision for calendar-based time operations.

    Create one with ``SystemTime.now()`` or ``SystemTime.from_secs``, then
    measure gaps with :meth:`duration_since`, shift it with Durations, or
    convert it to a ``datetime`` with :meth:`to_datetime`.

    Examples:
        >>> t = SystemTime.now()
        >>> t.as_secs() > 1_600_000_000
        True
    """

    __slots__ = ("_seconds", "_nanos", "_tz")

    def __init__(self) -> None:
        """Capture the current wall-clock time."""
        now = _dt_module.datetime.now()
        epoch = _dt_module.datetime(1970, 1, 1)
        delta = now - epoch
        self._seconds = int(delta.total_seconds())
        self._nanos = delta.microseconds * 1000
        self._tz = now.tzinfo

    @classmethod
    def now(cls) -> SystemTime:
        """Capture the current wall-clock time.

        Returns:
            A new SystemTime representing the current moment.

        Examples:
            >>> isinstance(SystemTime.now(), SystemTime)
            True
        """
        return cls()

    @classmethod
    def from_secs(cls, secs: int, nanos: int = 0) -> SystemTime:
        """Create a SystemTime from seconds and nanoseconds since the Unix epoch.

        Args:
            secs: Whole seconds since the epoch.
            nanos: Fractional nanoseconds. Defaults to 0.

        Returns:
            A new SystemTime representing the specified point in time.

        Examples:
            >>> SystemTime.from_secs(1_000_000_000).as_secs()
            1000000000
        """
        t = cls.__new__(cls)
        t._seconds = secs
        t._nanos = nanos
        t._tz = None
        return t

    def duration_since(self, earlier: SystemTime) -> Duration:
        """Compute the Duration between this SystemTime and an earlier one.

        Args:
            earlier: The SystemTime to measure from.

        Returns:
            The Duration from earlier to self.

        Raises:
            Elapsed: If earlier is in the future relative to self.

        Examples:
            >>> later = SystemTime.from_secs(5)
            >>> earlier = SystemTime.from_secs(3)
            >>> later.duration_since(earlier).as_secs()
            2
        """
        diff_secs = self._seconds - earlier._seconds
        diff_nanos = self._nanos - earlier._nanos
        if diff_nanos < 0:
            diff_secs -= 1
            diff_nanos += 1_000_000_000
        if diff_secs < 0:
            raise Elapsed()
        return Duration(diff_secs, diff_nanos)

    def checked_duration_since(self, earlier: SystemTime) -> Duration | None:
        """Try to compute the Duration since an earlier SystemTime, returning None on failure.

        Args:
            earlier: The SystemTime to measure from.

        Returns:
            The Duration from earlier to self, or None if earlier is in the future.

        Examples:
            >>> SystemTime.from_secs(3).checked_duration_since(SystemTime.from_secs(5))
        """
        diff_secs = self._seconds - earlier._seconds
        diff_nanos = self._nanos - earlier._nanos
        if diff_nanos < 0:
            diff_secs -= 1
            diff_nanos += 1_000_000_000
        if diff_secs < 0:
            return None
        return Duration(diff_secs, diff_nanos)

    def saturating_duration_since(self, earlier: SystemTime) -> Duration:
        """Compute the Duration since an earlier SystemTime, saturating at zero on failure.

        Args:
            earlier: The SystemTime to measure from.

        Returns:
            The Duration from earlier to self, or zero if earlier is in the future.

        Examples:
            >>> SystemTime.from_secs(3).saturating_duration_since(SystemTime.from_secs(5)).is_zero()
            True
        """
        result = self.checked_duration_since(earlier)
        return result if result else Duration.zero()

    def add_duration(self, duration: Duration) -> SystemTime:
        """Add a Duration to this SystemTime, producing a new point in the future.

        Args:
            duration: The Duration to add.

        Returns:
            A new SystemTime offset from this one by the given duration.

        Examples:
            >>> SystemTime.from_secs(10).add_duration(Duration.from_secs(5)).as_secs()
            15
        """
        new_secs = self._seconds + duration._secs
        new_nanos = self._nanos + duration._nanos
        if new_nanos >= 1_000_000_000:
            new_secs += 1
            new_nanos -= 1_000_000_000
        t = SystemTime.__new__(SystemTime)
        t._seconds = new_secs
        t._nanos = new_nanos
        t._tz = None
        return t

    def checked_add_duration(self, duration: Duration) -> SystemTime | None:
        """Try to add a Duration to this SystemTime, returning None on overflow.

        Args:
            duration: The Duration to add.

        Returns:
            A new SystemTime offset from this one, or None on overflow.

        Examples:
            >>> SystemTime.from_secs(1).checked_add_duration(Duration.from_secs(1)).as_secs()
            2
        """
        try:
            return self.add_duration(duration)
        except (ValueError, OverflowError):
            return None

    def checked_sub_duration(self, duration: Duration) -> SystemTime | None:
        """Try to subtract a Duration from this SystemTime, returning None on underflow.

        Args:
            duration: The Duration to subtract.

        Returns:
            A new SystemTime offset from this one, or None if the result would be before the epoch.

        Examples:
            >>> SystemTime.from_secs(5).checked_sub_duration(Duration.from_secs(3)).as_secs()
            2
            >>> SystemTime.from_secs(5).checked_sub_duration(Duration.from_secs(99))
        """
        new_secs = self._seconds - duration._secs
        new_nanos = self._nanos - duration._nanos
        if new_nanos < 0:
            new_secs -= 1
            new_nanos += 1_000_000_000
        if new_secs < 0:
            return None
        t = SystemTime.__new__(SystemTime)
        t._seconds = new_secs
        t._nanos = new_nanos
        t._tz = None
        return t

    def sub(self, other: SystemTime) -> Duration:
        """Compute the Duration between this SystemTime and another.

        Entry point for the ``-`` operator; see :meth:`duration_since`.

        Args:
            other: The SystemTime to subtract.

        Returns:
            The Duration from other to self.

        Examples:
            >>> SystemTime.from_secs(5).sub(SystemTime.from_secs(3)).as_secs()
            2
        """
        return self.duration_since(other)

    def as_secs(self) -> int:
        """Return the whole seconds component since the Unix epoch.

        Returns:
            The number of whole seconds since the epoch.

        Examples:
            >>> SystemTime.from_secs(123).as_secs()
            123
        """
        return self._seconds

    def from_epoch(self) -> Duration:
        """Return the Duration since the Unix epoch to this SystemTime.

        Returns:
            A Duration representing the time elapsed since the epoch.

        Examples:
            >>> SystemTime.from_secs(1, 500_000_000).from_epoch().as_nanos()
            1500000000
        """
        return Duration(self._seconds, self._nanos)

    def to_datetime(self) -> _dt_module.datetime:
        """Convert this SystemTime to a datetime object.

        Returns:
            A datetime representing the same point in time.

        Examples:
            >>> SystemTime.from_secs(0).to_datetime().year
            1970
        """
        return _dt_module.datetime.fromtimestamp(self._seconds, tz=self._tz)

    def __sub__(self, other: SystemTime) -> Duration:
        """Return the Duration from other to this SystemTime."""
        return self.duration_since(other)

    def __add__(self, duration: Duration) -> SystemTime:
        """Return a new SystemTime offset by the given Duration."""
        return self.add_duration(duration)

    def __radd__(self, duration: Duration) -> SystemTime:
        """Return a new SystemTime offset by the given Duration (reversed)."""
        return self.add_duration(duration)

    def __eq__(self, other: object) -> bool:
        """Return True if other is a SystemTime with the same timestamp."""
        if isinstance(other, SystemTime):
            return self._seconds == other._seconds and self._nanos == other._nanos
        return NotImplemented

    def __ne__(self, other: object) -> bool:
        """Return True if other is not an equal SystemTime."""
        if isinstance(other, SystemTime):
            return self._seconds != other._seconds or self._nanos != other._nanos
        return NotImplemented

    def __lt__(self, other: SystemTime) -> bool:
        """Return True if this SystemTime is before other."""
        if isinstance(other, SystemTime):
            return (self._seconds, self._nanos) < (other._seconds, other._nanos)
        return NotImplemented

    def __le__(self, other: SystemTime) -> bool:
        """Return True if this SystemTime is at or before other."""
        if isinstance(other, SystemTime):
            return (self._seconds, self._nanos) <= (other._seconds, other._nanos)
        return NotImplemented

    def __gt__(self, other: SystemTime) -> bool:
        """Return True if this SystemTime is after other."""
        if isinstance(other, SystemTime):
            return (self._seconds, self._nanos) > (other._seconds, other._nanos)
        return NotImplemented

    def __ge__(self, other: SystemTime) -> bool:
        """Return True if this SystemTime is at or after other."""
        if isinstance(other, SystemTime):
            return (self._seconds, self._nanos) >= (other._seconds, other._nanos)
        return NotImplemented

    def __hash__(self) -> int:
        """Return a hash based on the timestamp components."""
        return hash((self._seconds, self._nanos))

    def __repr__(self) -> str:
        """Return a concise representation of this SystemTime."""
        return f"SystemTime({self._seconds}.{self._nanos:09d})"