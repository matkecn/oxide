"""Instant: a monotonic timestamp for measuring elapsed time.

Provides ``Instant`` for measuring elapsed time and computing durations
between two points. Instants are captured on a monotonic clock so elapsed
measurements are reliable, while a wall-clock snapshot is retained for
``as_secs``/``as_millis`` conversions.
"""
from __future__ import annotations

import time

from .duration import Duration, Elapsed


class Instant:
    """A monotonic timestamp for measuring elapsed time between two points.

    Create one with ``Instant.now()``, then measure the gap to a later
    moment with :meth:`elapsed` or :meth:`duration_since`. Instants support
    ordering, equality, and arithmetic with Durations.

    Examples:
        >>> start = Instant.now()
        >>> end = Instant.now()
        >>> end.duration_since(start).as_nanos() >= 0
        True
    """

    __slots__ = ("_monotonic", "_wall")

    def __init__(self) -> None:
        """Capture the current instant using both monotonic and wall clocks."""
        self._monotonic = time.monotonic()
        self._wall = time.time()

    @classmethod
    def now(cls) -> Instant:
        """Capture the current instant.

        Returns:
            A new Instant representing the current moment.

        Examples:
            >>> isinstance(Instant.now(), Instant)
            True
        """
        return cls()

    @classmethod
    def from_secs(cls, secs: float) -> Instant:
        """Create an Instant from a wall-clock timestamp in seconds.

        The monotonic component is taken from the current time and only the
        wall-clock component is replaced.

        Args:
            secs: Wall-clock time as seconds since the Unix epoch.

        Returns:
            A new Instant with the specified wall-clock time.

        Examples:
            >>> Instant.from_secs(1_000_000_000).as_secs()
            1000000000
        """
        inst = cls()
        inst._wall = secs
        return inst

    def elapsed(self) -> Duration:
        """Compute the Duration elapsed since this Instant was created.

        Returns:
            A Duration representing the time elapsed.

        Examples:
            >>> Instant.now().elapsed().as_nanos() >= 0
            True
        """
        return Duration.from_secs(time.monotonic() - self._monotonic)

    def checked_elapsed(self) -> Duration | None:
        """Try to compute the elapsed Duration, returning None if the clock went backwards.

        Returns:
            A Duration representing the time elapsed, or None on clock regression.
        """
        diff = time.monotonic() - self._monotonic
        if diff < 0:
            return None
        return Duration.from_secs(diff)

    def checked_duration_since(self, earlier: Instant) -> Duration | None:
        """Try to compute the Duration between this Instant and an earlier one.

        Args:
            earlier: The Instant to measure from.

        Returns:
            The Duration from earlier to self, or None if the clock went backwards.

        Examples:
            >>> a = Instant.now()
            >>> b = Instant.now()
            >>> isinstance(b.checked_duration_since(a), Duration)
            True
        """
        diff = self._monotonic - earlier._monotonic
        if diff < 0:
            return None
        return Duration.from_secs(diff)

    def duration_since(self, earlier: Instant) -> Duration:
        """Compute the Duration between this Instant and an earlier one.

        Args:
            earlier: The Instant to measure from.

        Returns:
            The Duration from earlier to self.

        Raises:
            Elapsed: If the clock went backwards between the two Instants.

        Examples:
            >>> a = Instant.now()
            >>> b = Instant.now()
            >>> b.duration_since(a).as_nanos() >= 0
            True
        """
        diff = self._monotonic - earlier._monotonic
        if diff < 0:
            raise Elapsed()
        return Duration.from_secs(diff)

    def checked_since(self, earlier: Instant) -> Instant | None:
        """Check that an earlier Instant occurred before this one.

        Args:
            earlier: The Instant to check against.

        Returns:
            This Instant if it is at or after earlier, or None otherwise.

        Examples:
            >>> a = Instant.now()
            >>> b = Instant.now()
            >>> b.checked_since(a) is b
            True
        """
        diff = self._monotonic - earlier._monotonic
        if diff < 0:
            return None
        return self

    def saturating_duration_since(self, earlier: Instant) -> Duration:
        """Compute the Duration since an earlier Instant, saturating at zero on clock regression.

        Args:
            earlier: The Instant to measure from.

        Returns:
            The Duration from earlier to self, or zero if the clock went backwards.

        Examples:
            >>> a = Instant.now()
            >>> b = Instant.now()
            >>> b.saturating_duration_since(a).as_nanos() >= 0
            True
        """
        diff = self._monotonic - earlier._monotonic
        if diff < 0:
            return Duration.zero()
        return Duration.from_secs(diff)

    def add_duration(self, duration: Duration) -> Instant:
        """Add a Duration to this Instant, producing a new Instant in the future.

        Args:
            duration: The Duration to add.

        Returns:
            A new Instant offset from this one by the given duration.

        Examples:
            >>> a = Instant.now()
            >>> b = a.add_duration(Duration.from_secs(1))
            >>> b > a
            True
        """
        inst = Instant()
        inst._monotonic = self._monotonic + duration.secs_f64()
        inst._wall = self._wall + duration.secs_f64()
        return inst

    def checked_add_duration(self, duration: Duration) -> Instant | None:
        """Try to add a Duration to this Instant, returning None on overflow.

        Args:
            duration: The Duration to add.

        Returns:
            A new Instant offset from this one, or None on overflow.

        Examples:
            >>> isinstance(Instant.now().checked_add_duration(Duration.from_secs(1)), Instant)
            True
        """
        try:
            return self.add_duration(duration)
        except (ValueError, OverflowError):
            return None

    def as_secs(self) -> float:
        """Return the wall-clock timestamp as seconds since the Unix epoch.

        Returns:
            The wall-clock time in seconds as a float.

        Examples:
            >>> Instant.from_secs(1.5).as_secs()
            1.5
        """
        return self._wall

    def as_millis(self) -> int:
        """Return the wall-clock timestamp as milliseconds since the Unix epoch.

        Returns:
            The wall-clock time in milliseconds as an integer.

        Examples:
            >>> Instant.from_secs(1.5).as_millis()
            1500
        """
        return int(self._wall * 1000)

    def __sub__(self, other: Instant) -> Duration:
        """Return the Duration from other to this Instant."""
        return self.duration_since(other)

    def __add__(self, duration: Duration) -> Instant:
        """Return a new Instant offset by the given Duration."""
        return self.add_duration(duration)

    def __radd__(self, duration: Duration) -> Instant:
        """Return a new Instant offset by the given Duration (reversed)."""
        return self.add_duration(duration)

    def __eq__(self, other: object) -> bool:
        """Return True if other is an Instant at the same monotonic time."""
        if isinstance(other, Instant):
            return self._monotonic == other._monotonic
        return NotImplemented

    def __ne__(self, other: object) -> bool:
        """Return True if other is not an Instant at the same monotonic time."""
        if isinstance(other, Instant):
            return self._monotonic != other._monotonic
        return NotImplemented

    def __lt__(self, other: Instant) -> bool:
        """Return True if this Instant occurred before other."""
        if isinstance(other, Instant):
            return self._monotonic < other._monotonic
        return NotImplemented

    def __le__(self, other: Instant) -> bool:
        """Return True if this Instant occurred at or before other."""
        if isinstance(other, Instant):
            return self._monotonic <= other._monotonic
        return NotImplemented

    def __gt__(self, other: Instant) -> bool:
        """Return True if this Instant occurred after other."""
        if isinstance(other, Instant):
            return self._monotonic > other._monotonic
        return NotImplemented

    def __ge__(self, other: Instant) -> bool:
        """Return True if this Instant occurred at or after other."""
        if isinstance(other, Instant):
            return self._monotonic >= other._monotonic
        return NotImplemented

    def __hash__(self) -> int:
        """Return a hash based on the monotonic time."""
        return hash(self._monotonic)

    def __repr__(self) -> str:
        """Return a concise representation of this Instant."""
        return f"Instant({self._wall:.6f})"