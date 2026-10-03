"""OnceCell — a cell that can be initialized exactly once.

``OnceCell[T]`` starts uninitialized and can be written at most once. It is
useful for lazy one-time initialization: :meth:`OnceCell.get_or_init`
computes the value on first access, while ``get`` returns ``None`` until
the cell has been set.
"""

from __future__ import annotations

from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class OnceCell(Generic[T]):
    """A cell that can be initialized at most once.

    Analogous to Rust's ``OnceCell``, this type is empty until it is set or
    initialized. Once written it can never be reset, which makes it ideal
    for lazy one-time initialization with shared access.

    Examples:
        >>> cell = OnceCell.new()
        >>> cell.set(5)
        True
        >>> cell.set(6)
        False
        >>> cell.get()
        5
    """

    __slots__ = ("_value", "_initialized")

    def __init__(self) -> None:
        """Construct an empty, uninitialized OnceCell."""
        self._value: T = None  # type: ignore[assignment]
        self._initialized = False

    @classmethod
    def new(cls) -> OnceCell[T]:
        """Create a new uninitialized OnceCell.

        Returns:
            OnceCell[T]: An empty cell.

        Examples:
            >>> OnceCell.new().is_initialized()
            False
        """
        return cls()

    @classmethod
    def with_value(cls, value: T) -> OnceCell[T]:
        """Create a new OnceCell already initialized with the given value.

        Args:
            value (T): The value with which the cell starts initialized.

        Returns:
            OnceCell[T]: An initialized cell containing ``value``.

        Examples:
            >>> OnceCell.with_value(10).get()
            10
        """
        cell = cls()
        cell._value = value
        cell._initialized = True
        return cell

    def get(self) -> T | None:
        """Return the value if initialized, otherwise None.

        Returns:
            T | None: The stored value, or ``None`` if the cell is empty.

        Examples:
            >>> cell = OnceCell.new()
            >>> cell.get() is None
            True
            >>> cell.set(7)
            True
            >>> cell.get()
            7
        """
        if not self._initialized:
            return None
        return self._value

    def set(self, value: T) -> bool:
        """Set the value if the cell is not yet initialized.

        Args:
            value (T): The value to store.

        Returns:
            bool: ``True`` if the value was stored, ``False`` if the cell was
                already initialized (in which case it is left unchanged).

        Examples:
            >>> cell = OnceCell.new()
            >>> cell.set(1)
            True
            >>> cell.set(2)
            False
        """
        if self._initialized:
            return False
        self._value = value
        self._initialized = True
        return True

    def get_or_init(self, fn: Callable[[], T]) -> T:
        """Return the value, initializing it on first access if needed.

        If the cell is empty, ``fn`` is called and its result stored; on
        subsequent calls the cached value is returned without re-invoking
        ``fn``.

        Args:
            fn (Callable[[], T]): A zero-argument callable producing the value
                when the cell is first accessed.

        Returns:
            T: The stored value.

        Examples:
            >>> cell = OnceCell.new()
            >>> cell.get_or_init(lambda: 2 + 3)
            5
            >>> cell.get_or_init(lambda: 99)
            5
        """
        if self._initialized:
            return self._value
        self._value = fn()
        self._initialized = True
        return self._value

    def try_into_inner(self) -> T | None:
        """Consume the cell and return the value if initialized.

        Returns:
            T | None: The stored value, or ``None`` if the cell was empty.
        """
        if not self._initialized:
            return None
        return self._value

    def is_initialized(self) -> bool:
        """Return True if the cell has been initialized.

        Returns:
            bool: ``True`` if a value has been stored in the cell.
        """
        return self._initialized

    def __repr__(self) -> str:
        """Return a string representation of the OnceCell.

        Returns:
            str: A repr of the form ``OnceCell(<value>)``, or
                ``OnceCell(<uninitialized>)`` while the cell is empty.
        """
        if self._initialized:
            return f"OnceCell({self._value!r})"
        return "OnceCell(<uninitialized>)"

    def __bool__(self) -> bool:
        """Return True if the cell has been initialized.

        Returns:
            bool: ``True`` if a value has been stored in the cell.
        """
        return self._initialized

    def __eq__(self, other: object) -> bool:
        """Check equality with another OnceCell.

        Uninitialized cells are never equal to anything.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: ``True`` if ``other`` is an initialized ``OnceCell`` holding
                an equal value, otherwise ``NotImplemented``.
        """
        if isinstance(other, OnceCell):
            if not self._initialized or not other._initialized:
                return False
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        """Return the hash of the contained value, or hash(None) if uninitialized.

        Returns:
            int: The hash of the stored value, or ``hash(None)`` while empty.
        """
        if self._initialized:
            return hash(self._value)
        return hash(None)