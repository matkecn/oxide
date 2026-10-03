"""Duration: a span of time with arithmetic and comparisons.

Provides the ``Duration`` type with constructors such as ``from_secs`` and
``from_nanos``, conversion accessors such as ``as_millis``, checked and
saturating arithmetic, and ordering comparisons. Also defines the
``UNIX_EPOCH`` constant and the ``Elapsed`` exception.
"""
from __future__ import annotations


class Elapsed(Exception):
    """Raised when a timer operation fails due to expiration.

    For example, computing a duration with ``Instant.duration_since`` or
    ``SystemTime.duration_since`` raises this when the clock went backwards
    or the start time lies in the future.

    Examples:
        >>> try:
        ...     raise Elapsed()
        ... except Elapsed as e:
        ...     str(e)
        'timer expiration error'
    """

    __slots__ = ()

    def __init__(self) -> None:
        """Initialize the exception with a fixed timer expiration message."""
        super().__init__("timer expiration error")


class Duration:
    """A span of time with nanosecond precision, supporting arithmetic and comparisons.

    The internal representation keeps whole seconds and a sub-second
    nanoseconds component. Construct via the ``from_*`` constructors or the
    plain constructor, then convert with the ``as_*`` accessors or combine
    with arithmetic operators.

    Examples:
        >>> d = Duration.from_secs(1.5)
        >>> d.as_millis()
        1500
        >>> d + Duration.from_millis(500)
        Duration(secs=2)
        >>> Duration.from_secs(2) > d
        True
    """

    __slots__ = ("_secs", "_nanos")

    def __init__(self, secs: int = 0, nanos: int = 0) -> None:
        """Create a Duration from seconds and nanoseconds components.

        The nanoseconds component is normalized into the seconds field, so
        values greater than or equal to 1 billion nanoseconds are carried
        over into whole seconds.

        Args:
            secs: The whole seconds component. Must be non-negative.
            nanos: The fractional nanoseconds component. Must be non-negative and less than 1,000,000,000.

        Raises:
            ValueError: If secs or nanos is negative.
        """
        if secs < 0 or nanos < 0:
            raise ValueError("duration values must be non-negative")
        self._secs = secs + nanos // 1_000_000_000
        self._nanos = nanos % 1_000_000_000

    @classmethod
    def from_secs(cls, secs: int | float) -> Duration:
        """Create a Duration from a number of seconds.

        Args:
            secs: Number of seconds (integer or floating-point).

        Returns:
            A new Duration representing the given time span.

        Examples:
            >>> Duration.from_secs(1.5).as_secs()
            1
            >>> Duration.from_secs(90).as_secs()
            90
        """
        s = int(secs)
        ns = int((secs - s) * 1_000_000_000)
        return cls(s, ns)

    @classmethod
    def from_millis(cls, millis: int | float) -> Duration:
        """Create a Duration from a number of milliseconds.

        Args:
            millis: Number of milliseconds.

        Returns:
            A new Duration representing the given time span.

        Examples:
            >>> Duration.from_millis(1500).as_millis()
            1500
        """
        s = int(millis) // 1000
        ns = (int(millis) % 1000) * 1_000_000
        return cls(s, ns)

    @classmethod
    def from_micros(cls, micros: int | float) -> Duration:
        """Create a Duration from a number of microseconds.

        Args:
            micros: Number of microseconds.

        Returns:
            A new Duration representing the given time span.

        Examples:
            >>> Duration.from_micros(1_500_000).as_micros()
            1500000
        """
        s = int(micros) // 1_000_000
        ns = (int(micros) % 1_000_000) * 1_000
        return cls(s, ns)

    @classmethod
    def from_nanos(cls, nanos: int) -> Duration:
        """Create a Duration from a number of nanoseconds.

        Args:
            nanos: Number of nanoseconds.

        Returns:
            A new Duration representing the given time span.

        Examples:
            >>> Duration.from_nanos(1_000_000_001).as_nanos()
            1000000001
        """
        return cls(0, nanos)

    @classmethod
    def from_minutes(cls, minutes: int | float) -> Duration:
        """Create a Duration from a number of minutes.

        Args:
            minutes: Number of minutes.

        Returns:
            A new Duration representing the given time span.

        Examples:
            >>> Duration.from_minutes(1).as_secs()
            60
        """
        return cls.from_secs(minutes * 60)

    @classmethod
    def from_hours(cls, hours: int | float) -> Duration:
        """Create a Duration from a number of hours.

        Args:
            hours: Number of hours.

        Returns:
            A new Duration representing the given time span.

        Examples:
            >>> Duration.from_hours(1).as_secs()
            3600
        """
        return cls.from_secs(hours * 3600)

    @classmethod
    def from_days(cls, days: int | float) -> Duration:
        """Create a Duration from a number of days.

        Args:
            days: Number of days.

        Returns:
            A new Duration representing the given time span.

        Examples:
            >>> Duration.from_days(1).as_secs()
            86400
        """
        return cls.from_secs(days * 86400)

    @classmethod
    def zero(cls) -> Duration:
        """Create a zero-length Duration.

        Returns:
            A Duration representing zero time.

        Examples:
            >>> Duration.zero().is_zero()
            True
        """
        return cls(0, 0)

    def as_secs(self) -> int:
        """Return the whole seconds component of this Duration.

        Sub-second precision is discarded.

        Returns:
            The number of whole seconds.

        Examples:
            >>> Duration.from_millis(1500).as_secs()
            1
        """
        return self._secs

    def as_millis(self) -> int:
        """Return the total duration as an integer number of milliseconds.

        Sub-millisecond precision is truncated towards zero.

        Returns:
            The duration converted to milliseconds.

        Examples:
            >>> Duration.from_secs(1.5).as_millis()
            1500
        """
        return self._secs * 1000 + self._nanos // 1_000_000

    def as_micros(self) -> int:
        """Return the total duration as an integer number of microseconds.

        Sub-microsecond precision is truncated towards zero.

        Returns:
            The duration converted to microseconds.

        Examples:
            >>> Duration.from_secs(1.5).as_micros()
            1500000
        """
        return self._secs * 1_000_000 + self._nanos // 1_000

    def as_nanos(self) -> int:
        """Return the total duration as an integer number of nanoseconds.

        Returns:
            The duration converted to nanoseconds.

        Examples:
            >>> Duration.from_secs(1.5).as_nanos()
            1500000000
        """
        return self._secs * 1_000_000_000 + self._nanos

    def secs_f64(self) -> float:
        """Return the duration as a floating-point number of seconds.

        Returns:
            The duration converted to seconds as a float.

        Examples:
            >>> Duration.from_millis(500).secs_f64()
            0.5
        """
        return self._secs + self._nanos / 1_000_000_000

    def is_zero(self) -> bool:
        """Check if this Duration represents zero time.

        Returns:
            True if both seconds and nanoseconds are zero, False otherwise.

        Examples:
            >>> Duration.zero().is_zero()
            True
        """
        return self._secs == 0 and self._nanos == 0

    def checked_add(self, other: Duration) -> Duration | None:
        """Try to add another Duration to this one, returning None on overflow.

        Args:
            other: The Duration to add.

        Returns:
            The sum of both Durations, or None if overflow occurs.

        Examples:
            >>> Duration.from_secs(1).checked_add(Duration.from_secs(2)).as_secs()
            3
        """
        try:
            return Duration(self._secs + other._secs, self._nanos + other._nanos)
        except (ValueError, OverflowError):
            return None

    def checked_sub(self, other: Duration) -> Duration | None:
        """Try to subtract another Duration from this one, returning None on underflow.

        Args:
            other: The Duration to subtract.

        Returns:
            The difference of the Durations, or None if the result would be negative.

        Examples:
            >>> Duration.from_secs(1).checked_sub(Duration.from_millis(500)).as_millis()
            500
        """
        total_self = self.as_nanos()
        total_other = other.as_nanos()
        if total_self < total_other:
            return None
        return Duration.from_nanos(total_self - total_other)

    def saturating_add(self, other: Duration) -> Duration:
        """Add another Duration, saturating at infinity on overflow.

        Args:
            other: The Duration to add.

        Returns:
            The sum of both Durations, or infinity if overflow occurs.

        Examples:
            >>> Duration.from_secs(1).saturating_add(Duration.zero()).as_secs()
            1
        """
        result = self.checked_add(other)
        return result if result else Duration.from_secs(float('inf'))

    def saturating_sub(self, other: Duration) -> Duration:
        """Subtract another Duration, saturating at zero on underflow.

        Args:
            other: The Duration to subtract.

        Returns:
            The difference of the Durations, or zero if underflow occurs.

        Examples:
            >>> Duration.from_secs(1).saturating_sub(Duration.from_secs(99)).is_zero()
            True
        """
        result = self.checked_sub(other)
        return result if result else Duration.zero()

    def mul(self, rhs: int) -> Duration:
        """Multiply this Duration by a scalar integer.

        Args:
            rhs: The integer multiplier.

        Returns:
            A new Duration representing the product.

        Examples:
            >>> (Duration.from_millis(500) * 3).as_millis()
            1500
        """
        return Duration.from_nanos(self.as_nanos() * rhs)

    def div(self, rhs: int) -> Duration:
        """Divide this Duration by a scalar integer, truncating towards zero.

        Args:
            rhs: The integer divisor.

        Returns:
            A new Duration representing the quotient.

        Raises:
            ZeroDivisionError: If rhs is zero.

        Examples:
            >>> (Duration.from_secs(7) // 2).as_secs()
            3
        """
        if rhs == 0:
            raise ZeroDivisionError("division by zero")
        return Duration.from_nanos(self.as_nanos() // rhs)

    def __add__(self, other: Duration) -> Duration:
        """Return the sum of this Duration and another."""
        return Duration(self._secs + other._secs, self._nanos + other._nanos)

    def __sub__(self, other: Duration) -> Duration:
        """Return the difference, raising on negative results."""
        result = self.checked_sub(other)
        if result is None:
            raise ValueError("underflow in duration subtraction")
        return result

    def __mul__(self, rhs: int) -> Duration:
        """Return this Duration multiplied by an integer scalar."""
        return self.mul(rhs)

    def __rmul__(self, lhs: int) -> Duration:
        """Return this Duration multiplied by an integer scalar (reversed)."""
        return self.mul(lhs)

    def __floordiv__(self, rhs: int) -> Duration:
        """Return this Duration divided by an integer scalar."""
        return self.div(rhs)

    def __mod__(self, other: Duration) -> Duration:
        """Return the remainder of dividing this Duration by another."""
        nanos = self.as_nanos() % other.as_nanos()
        return Duration.from_nanos(nanos)

    def __eq__(self, other: object) -> bool:
        """Return True if other is a Duration with the same length."""
        if isinstance(other, Duration):
            return self._secs == other._secs and self._nanos == other._nanos
        return NotImplemented

    def __ne__(self, other: object) -> bool:
        """Return True if other is not an equal Duration."""
        if isinstance(other, Duration):
            return self._secs != other._secs or self._nanos != other._nanos
        return NotImplemented

    def __lt__(self, other: Duration) -> bool:
        """Return True if this Duration is shorter than other."""
        if isinstance(other, Duration):
            return self.as_nanos() < other.as_nanos()
        return NotImplemented

    def __le__(self, other: Duration) -> bool:
        """Return True if this Duration is shorter than or equal to other."""
        if isinstance(other, Duration):
            return self.as_nanos() <= other.as_nanos()
        return NotImplemented

    def __gt__(self, other: Duration) -> bool:
        """Return True if this Duration is longer than other."""
        if isinstance(other, Duration):
            return self.as_nanos() > other.as_nanos()
        return NotImplemented

    def __ge__(self, other: Duration) -> bool:
        """Return True if this Duration is longer than or equal to other."""
        if isinstance(other, Duration):
            return self.as_nanos() >= other.as_nanos()
        return NotImplemented

    def __hash__(self) -> int:
        """Return a hash based on this Duration's components."""
        return hash((self._secs, self._nanos))

    def __repr__(self) -> str:
        """Return a concise representation like ``Duration(secs=1)``."""
        if self._nanos == 0:
            return f"Duration(secs={self._secs})"
        return f"Duration(secs={self._secs}, nanos={self._nanos})"

    def __bool__(self) -> bool:
        """Return True if this Duration is non-zero."""
        return not self.is_zero()


UNIX_EPOCH = Duration(0, 0)