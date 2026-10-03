"""Atomic types — lock-free AtomicBool, AtomicInt, and generic Atomic."""

from __future__ import annotations

import threading
from typing import Generic, TypeVar

T = TypeVar("T")


class Atomic(Generic[T]):
    """Thread-safe atomic container for arbitrary types using a lock.

    Provides atomic load, store, and swap operations on values of any type.
    An internal lock serializes all access, making the container safe to share
    across threads.

    Examples:
        >>> from oxide.sync import Atomic
        >>> count = Atomic.new([0])
        >>> count.store([1])
        >>> count.load()
        [1]
    """

    __slots__ = ("_value", "_lock")

    def __init__(self, value: T) -> None:
        self._value = value
        self._lock = threading.Lock()

    @classmethod
    def new(cls, value: T) -> Atomic[T]:
        """Create a new Atomic wrapping the given value.

        Args:
            value: The value to store atomically.

        Returns:
            A new Atomic container.
        """
        return cls(value)

    def load(self) -> T:
        """Return the current value atomically.

        Returns:
            The value currently held in the container.
        """
        with self._lock:
            return self._value

    def store(self, value: T) -> None:
        """Set the value atomically.

        Args:
            value: The new value to store.
        """
        with self._lock:
            self._value = value

    def swap(self, value: T) -> T:
        """Atomically replace the value and return the old one.

        Args:
            value: The value to store.

        Returns:
            The value that was previously held.
        """
        with self._lock:
            old = self._value
            self._value = value
            return old

    def into_inner(self) -> T:
        """Return the held value without changing the container.

        Note:
            This does not empty the container; it simply exposes the current value.

        Returns:
            The value currently held in the container.
        """
        return self._value

    def __repr__(self) -> str:
        return f"Atomic({self._value!r})"


class AtomicBool:
    """Thread-safe atomic boolean with bitwise and compare-and-set operations.

    All operations are serialized by an internal lock, making the value safe to
    read and modify concurrently from multiple threads.

    Examples:
        >>> from oxide.sync import AtomicBool
        >>> flag = AtomicBool.new(True)
        >>> flag.compare_and_set(True, False)
        True
        >>> flag.load()
        False
    """

    __slots__ = ("_value", "_lock")

    def __init__(self, value: bool = False) -> None:
        self._value = value
        self._lock = threading.Lock()

    @classmethod
    def new(cls, value: bool = False) -> AtomicBool:
        """Create a new AtomicBool with the given value.

        Args:
            value: The initial boolean value (default False).

        Returns:
            A new AtomicBool.
        """
        return cls(value)

    def load(self) -> bool:
        """Return the current boolean value atomically.

        Returns:
            The boolean value currently held.
        """
        with self._lock:
            return self._value

    def store(self, value: bool) -> None:
        """Set the boolean value atomically.

        Args:
            value: The new boolean value.
        """
        with self._lock:
            self._value = value

    def swap(self, value: bool) -> bool:
        """Atomically replace the value and return the old one.

        Args:
            value: The value to store.

        Returns:
            The boolean value that was previously held.
        """
        with self._lock:
            old = self._value
            self._value = value
            return old

    def compare_and_set(self, current: bool, new: bool) -> bool:
        """Set to new if the current value equals current.

        If the held value equals ``current``, it is replaced with ``new`` and
        True is returned. Otherwise nothing changes and False is returned.

        Args:
            current: The value to compare against.
            new: The value to store on success.

        Returns:
            True if the swap succeeded, False otherwise.
        """
        with self._lock:
            if self._value == current:
                self._value = new
                return True
            return False

    def fetch_and(self, value: bool) -> bool:
        """Atomically compute the logical AND with value and return the old value.

        Args:
            value: The operand to AND with.

        Returns:
            The boolean value that was previously held.
        """
        with self._lock:
            old = self._value
            self._value = self._value and value
            return old

    def fetch_or(self, value: bool) -> bool:
        """Atomically compute the logical OR with value and return the old value.

        Args:
            value: The operand to OR with.

        Returns:
            The boolean value that was previously held.
        """
        with self._lock:
            old = self._value
            self._value = self._value or value
            return old

    def fetch_xor(self, value: bool) -> bool:
        """Atomically compute the logical XOR with value and return the old value.

        Args:
            value: The operand to XOR with.

        Returns:
            The boolean value that was previously held.
        """
        with self._lock:
            old = self._value
            self._value = self._value != value
            return old

    def into_inner(self) -> bool:
        """Return the held boolean value without changing the container.

        Returns:
            The boolean value currently held.
        """
        return self._value

    def __repr__(self) -> str:
        return f"AtomicBool({self._value!r})"

    def __bool__(self) -> bool:
        """Return the current boolean value, enabling truth testing."""
        return self.load()


class AtomicInt:
    """Thread-safe atomic integer with arithmetic, bitwise, and compare-and-set operations.

    All operations are serialized by an internal lock, making the integer safe to
    modify concurrently from multiple threads without race conditions.

    Examples:
        >>> from oxide.sync import AtomicInt
        >>> a = AtomicInt.new(10)
        >>> a.fetch_add(5)
        10
        >>> a.load()
        15
    """

    __slots__ = ("_value", "_lock")

    def __init__(self, value: int = 0) -> None:
        self._value = value
        self._lock = threading.Lock()

    @classmethod
    def new(cls, value: int = 0) -> AtomicInt:
        """Create a new AtomicInt with the given value.

        Args:
            value: The initial integer value (default 0).

        Returns:
            A new AtomicInt.
        """
        return cls(value)

    def load(self) -> int:
        """Return the current integer value atomically.

        Returns:
            The integer value currently held.
        """
        with self._lock:
            return self._value

    def store(self, value: int) -> None:
        """Set the integer value atomically.

        Args:
            value: The new integer value.
        """
        with self._lock:
            self._value = value

    def swap(self, value: int) -> int:
        """Atomically replace the value and return the old one.

        Args:
            value: The value to store.

        Returns:
            The integer value that was previously held.
        """
        with self._lock:
            old = self._value
            self._value = value
            return old

    def fetch_add(self, value: int) -> int:
        """Atomically add value and return the old value.

        Args:
            value: The amount to add.

        Returns:
            The integer value that was previously held.
        """
        with self._lock:
            old = self._value
            self._value += value
            return old

    def fetch_sub(self, value: int) -> int:
        """Atomically subtract value and return the old value.

        Args:
            value: The amount to subtract.

        Returns:
            The integer value that was previously held.
        """
        with self._lock:
            old = self._value
            self._value -= value
            return old

    def fetch_and(self, value: int) -> int:
        """Atomically compute the bitwise AND with value and return the old value.

        Args:
            value: The operand to AND with.

        Returns:
            The integer value that was previously held.
        """
        with self._lock:
            old = self._value
            self._value &= value
            return old

    def fetch_or(self, value: int) -> int:
        """Atomically compute the bitwise OR with value and return the old value.

        Args:
            value: The operand to OR with.

        Returns:
            The integer value that was previously held.
        """
        with self._lock:
            old = self._value
            self._value |= value
            return old

    def fetch_xor(self, value: int) -> int:
        """Atomically compute the bitwise XOR with value and return the old value.

        Args:
            value: The operand to XOR with.

        Returns:
            The integer value that was previously held.
        """
        with self._lock:
            old = self._value
            self._value ^= value
            return old

    def compare_and_set(self, current: int, new: int) -> bool:
        """Set to new if the current value equals current.

        If the held value equals ``current``, it is replaced with ``new`` and
        True is returned. Otherwise nothing changes and False is returned.

        Args:
            current: The value to compare against.
            new: The value to store on success.

        Returns:
            True if the swap succeeded, False otherwise.
        """
        with self._lock:
            if self._value == current:
                self._value = new
                return True
            return False

    def into_inner(self) -> int:
        """Return the held integer value without changing the container.

        Returns:
            The integer value currently held.
        """
        return self._value

    def __repr__(self) -> str:
        return f"AtomicInt({self._value!r})"

    def __int__(self) -> int:
        """Return the current value as an int."""
        return self.load()

    def __add__(self, other: int) -> int:
        """Return the sum of the current value and other."""
        return self.load() + other

    def __sub__(self, other: int) -> int:
        """Return the difference between the current value and other."""
        return self.load() - other

    def __iadd__(self, other: int) -> AtomicInt:
        """Atomically add other to the current value in place."""
        self.fetch_add(other)
        return self

    def __isub__(self, other: int) -> AtomicInt:
        """Atomically subtract other from the current value in place."""
        self.fetch_sub(other)
        return self
