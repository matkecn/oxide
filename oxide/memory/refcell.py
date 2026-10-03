"""RefCell — runtime borrow-checked interior mutability with Ref/RefMut guards.

``RefCell[T]`` allows modifying a value even through an immutable view,
enforcing the usual borrow rules at runtime instead of at compile time.
Immutable borrows yield ``Ref`` guards and mutable borrows yield ``RefMut``
guards; violating the rules raises ``BorrowError`` or ``BorrowMutError``.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

T = TypeVar("T")


class BorrowError(Exception):
    """Raised when immutably borrowing a value that is already mutably borrowed."""

    __slots__ = ()

    def __init__(self) -> None:
        """Construct a BorrowError with a fixed message."""
        super().__init__("already mutably borrowed")


class BorrowMutError(Exception):
    """Raised when mutably borrowing a value that is already borrowed in any form."""

    __slots__ = ()

    def __init__(self) -> None:
        """Construct a BorrowMutError with a fixed message."""
        super().__init__("already borrowed")


class RefCell(Generic[T]):
    """Runtime borrow-checked interior mutability for single-threaded contexts.

    Provides interior mutability with borrow checking performed at runtime:
    at most one mutable borrow or any number of immutable borrows may be
    active at once. Prefer the ``try_`` variants when you want to check
    instead of raising.

    Examples:
        >>> cell = RefCell.new([1, 2, 3])
        >>> with cell.borrow() as value:
        ...     len(value.value)
        3
        >>> with cell.borrow_mut() as value:
        ...     value.value.append(4)
        >>> cell.borrow().value
        [1, 2, 3, 4]
    """

    __slots__ = ("_value", "_borrow_count")

    def __init__(self, value: T) -> None:
        """Construct a new RefCell with no active borrows.

        Args:
            value (T): The value to store in the cell.
        """
        self._value = value
        self._borrow_count = 0

    @classmethod
    def new(cls, value: T) -> RefCell[T]:
        """Create a new RefCell containing the given value.

        Args:
            value (T): The value to store in the cell.

        Returns:
            RefCell[T]: A new RefCell holding ``value``.

        Examples:
            >>> cell = RefCell.new(10)
            >>> cell.borrow().value
            10
        """
        return cls(value)

    def borrow(self) -> Ref[T]:
        """Immutably borrow the value, raising if it is mutably borrowed.

        Multiple immutable borrows may be active simultaneously.

        Returns:
            Ref[T]: A ``Ref`` guard holding the borrowed value.

        Raises:
            BorrowError: If the value is currently mutably borrowed.

        Examples:
            >>> cell = RefCell.new([1, 2])
            >>> with cell.borrow() as value:
            ...     value.value
            [1, 2]
        """
        if self._borrow_count < 0:
            raise BorrowError()
        self._borrow_count += 1
        return Ref(self)

    def try_borrow(self) -> Ref[T] | None:
        """Try to immutably borrow the value without raising.

        Returns:
            Ref[T] | None: A ``Ref`` guard if the value is not mutably
                borrowed, otherwise ``None``.

        Examples:
            >>> cell = RefCell.new(1)
            >>> cell.try_borrow().value
            1
        """
        if self._borrow_count < 0:
            return None
        self._borrow_count += 1
        return Ref(self)

    def borrow_mut(self) -> RefMut[T]:
        """Mutably borrow the value, raising if it is already borrowed.

        A mutable borrow excludes all other borrows, including other mutable
        ones, until the guard is released.

        Returns:
            RefMut[T]: A ``RefMut`` guard granting mutable access.

        Raises:
            BorrowMutError: If the value is already borrowed in any form.

        Examples:
            >>> cell = RefCell.new(1)
            >>> with cell.borrow_mut() as value:
            ...     value.value = 2
            >>> cell.borrow().value
            2
        """
        if self._borrow_count != 0:
            raise BorrowMutError()
        self._borrow_count = -1
        return RefMut(self)

    def try_borrow_mut(self) -> RefMut[T] | None:
        """Try to mutably borrow the value without raising.

        Returns:
            RefMut[T] | None: A ``RefMut`` guard if the value is not currently
                borrowed, otherwise ``None``.

        Examples:
            >>> cell = RefCell.new(1)
            >>> cell.try_borrow_mut().value
            1
        """
        if self._borrow_count != 0:
            return None
        self._borrow_count = -1
        return RefMut(self)

    def replace(self, value: T) -> T:
        """Replace the contained value and return the previous value.

        Args:
            value (T): The new value to store.

        Returns:
            T: The value previously held by the cell.

        Examples:
            >>> cell = RefCell.new(1)
            >>> cell.replace(2)
            1
        """
        old = self._value
        self._value = value
        return old

    def swap(self, other: RefCell[T]) -> None:
        """Swap the contained values with another RefCell.

        Args:
            other (RefCell[T]): Another RefCell whose value will be exchanged
                with this one.
        """
        self._value, other._value = other._value, self._value

    def into_inner(self) -> T:
        """Consume the RefCell and return the contained value.

        Returns:
            T: The value held by the cell.
        """
        return self._value

    def _release_borrow(self) -> None:
        if self._borrow_count == -1:
            self._borrow_count = 0
        elif self._borrow_count > 0:
            self._borrow_count -= 1

    def __repr__(self) -> str:
        """Return a string representation of the RefCell.

        Returns:
            str: A repr of the form ``RefCell(<value>)``.
        """
        return f"RefCell({self._value!r})"


class Ref(Generic[T]):
    """An immutable reference guard returned by :meth:`RefCell.borrow`.

    The guard keeps the cell immutably borrowed until :meth:`release` is
    called or the guard is dropped. It behaves like the borrowed value for
    comparisons, arithmetic conversions, and string formatting.

    Examples:
        >>> cell = RefCell.new([1, 2])
        >>> with cell.borrow() as value:
        ...     value.value
        [1, 2]
    """

    __slots__ = ("_cell",)

    def __init__(self, cell: RefCell) -> None:
        """Construct a Ref guard around the given cell.

        Args:
            cell (RefCell): The RefCell being borrow-guarded.
        """
        self._cell = cell

    @property
    def value(self) -> Any:
        """Return the borrowed value.

        Returns:
            Any: The value held by the underlying cell.
        """
        return self._cell._value

    def release(self) -> None:
        """Release the borrow, decrementing the borrow count.

        After this call the underlying cell may again be mutably borrowed.
        """
        self._cell._release_borrow()

    def __enter__(self) -> Ref[T]:
        """Enter the context manager, returning self.

        Returns:
            Ref[T]: The guard itself.
        """
        return self

    def __exit__(self, *_: Any) -> None:
        """Exit the context manager, releasing the borrow.

        Args:
            *_ (Any): The exception type, value, and traceback (if any), which
                are ignored.
        """
        self.release()

    def __eq__(self, other: Any) -> bool:
        """Compare the borrowed value to another value for equality.

        Args:
            other (Any): The value to compare against.

        Returns:
            bool: Whether the borrowed value equals ``other``.
        """
        return self._cell._value == other

    def __ne__(self, other: Any) -> bool:
        """Compare the borrowed value to another value for inequality.

        Args:
            other (Any): The value to compare against.

        Returns:
            bool: Whether the borrowed value differs from ``other``.
        """
        return self._cell._value != other

    def __lt__(self, other: Any) -> bool:
        """Return whether the borrowed value is less than another value.

        Args:
            other (Any): The value to compare against.

        Returns:
            bool: Whether the borrowed value is less than ``other``.
        """
        return self._cell._value < other

    def __le__(self, other: Any) -> bool:
        """Return whether the borrowed value is at most another value.

        Args:
            other (Any): The value to compare against.

        Returns:
            bool: Whether the borrowed value is less than or equal to ``other``.
        """
        return self._cell._value <= other

    def __gt__(self, other: Any) -> bool:
        """Return whether the borrowed value is greater than another value.

        Args:
            other (Any): The value to compare against.

        Returns:
            bool: Whether the borrowed value is greater than ``other``.
        """
        return self._cell._value > other

    def __ge__(self, other: Any) -> bool:
        """Return whether the borrowed value is at least another value.

        Args:
            other (Any): The value to compare against.

        Returns:
            bool: Whether the borrowed value is greater than or equal to
                ``other``.
        """
        return self._cell._value >= other

    def __hash__(self) -> int:
        """Return the hash of the borrowed value.

        Returns:
            int: The hash of the borrowed value.
        """
        return hash(self._cell._value)

    def __bool__(self) -> bool:
        """Return the truthiness of the borrowed value.

        Returns:
            bool: Whether the borrowed value is truthy.
        """
        return bool(self._cell._value)

    def __int__(self) -> int:
        """Convert the borrowed value to an int.

        Returns:
            int: The borrowed value as an ``int``.
        """
        return int(self._cell._value)

    def __float__(self) -> float:
        """Convert the borrowed value to a float.

        Returns:
            float: The borrowed value as a ``float``.
        """
        return float(self._cell._value)

    def __str__(self) -> str:
        """Convert the borrowed value to a string.

        Returns:
            str: The borrowed value as a ``str``.
        """
        return str(self._cell._value)

    def __repr__(self) -> str:
        """Return a string representation of the guard.

        Returns:
            str: A repr of the form ``Ref(<value>)``.
        """
        return f"Ref({self._cell._value!r})"


class RefMut(Generic[T]):
    """A mutable reference guard returned by :meth:`RefCell.borrow_mut`.

    The guard keeps the cell mutably borrowed until :meth:`release` is called
    or the guard is dropped. The borrowed value can be read, written, or
    replaced through the guard.

    Examples:
        >>> cell = RefCell.new(0)
        >>> with cell.borrow_mut() as value:
        ...     value.value = 5
        >>> cell.borrow().value
        5
    """

    __slots__ = ("_cell",)

    def __init__(self, cell: RefCell) -> None:
        """Construct a RefMut guard around the given cell.

        Args:
            cell (RefCell): The RefCell being mutably borrow-guarded.
        """
        self._cell = cell

    @property
    def value(self) -> Any:
        """Return the borrowed value.

        Returns:
            Any: The value held by the underlying cell.
        """
        return self._cell._value

    @value.setter
    def value(self, v: Any) -> None:
        """Set the contained value through the mutable reference.

        Args:
            v (Any): The new value to store in the cell.
        """
        self._cell._value = v

    def replace(self, v: Any) -> Any:
        """Replace the contained value and return the previous value.

        Args:
            v (Any): The new value to store.

        Returns:
            Any: The value previously held by the cell.
        """
        old = self._cell._value
        self._cell._value = v
        return old

    def release(self) -> None:
        """Release the mutable borrow, resetting the borrow count.

        After this call the cell may be borrowed again by anyone.
        """
        self._cell._release_borrow()

    def __enter__(self) -> RefMut[T]:
        """Enter the context manager, returning self.

        Returns:
            RefMut[T]: The guard itself.
        """
        return self

    def __exit__(self, *_: Any) -> None:
        """Exit the context manager, releasing the mutable borrow.

        Args:
            *_ (Any): The exception type, value, and traceback (if any), which
                are ignored.
        """
        self.release()

    def __eq__(self, other: Any) -> bool:
        """Compare the borrowed value to another value for equality.

        Args:
            other (Any): The value to compare against.

        Returns:
            bool: Whether the borrowed value equals ``other``.
        """
        return self._cell._value == other

    def __ne__(self, other: Any) -> bool:
        """Compare the borrowed value to another value for inequality.

        Args:
            other (Any): The value to compare against.

        Returns:
            bool: Whether the borrowed value differs from ``other``.
        """
        return self._cell._value != other

    def __lt__(self, other: Any) -> bool:
        """Return whether the borrowed value is less than another value.

        Args:
            other (Any): The value to compare against.

        Returns:
            bool: Whether the borrowed value is less than ``other``.
        """
        return self._cell._value < other

    def __le__(self, other: Any) -> bool:
        """Return whether the borrowed value is at most another value.

        Args:
            other (Any): The value to compare against.

        Returns:
            bool: Whether the borrowed value is less than or equal to ``other``.
        """
        return self._cell._value <= other

    def __gt__(self, other: Any) -> bool:
        """Return whether the borrowed value is greater than another value.

        Args:
            other (Any): The value to compare against.

        Returns:
            bool: Whether the borrowed value is greater than ``other``.
        """
        return self._cell._value > other

    def __ge__(self, other: Any) -> bool:
        """Return whether the borrowed value is at least another value.

        Args:
            other (Any): The value to compare against.

        Returns:
            bool: Whether the borrowed value is greater than or equal to
                ``other``.
        """
        return self._cell._value >= other

    def __hash__(self) -> int:
        """Return the hash of the borrowed value.

        Returns:
            int: The hash of the borrowed value.
        """
        return hash(self._cell._value)

    def __bool__(self) -> bool:
        """Return the truthiness of the borrowed value.

        Returns:
            bool: Whether the borrowed value is truthy.
        """
        return bool(self._cell._value)

    def __int__(self) -> int:
        """Convert the borrowed value to an int.

        Returns:
            int: The borrowed value as an ``int``.
        """
        return int(self._cell._value)

    def __float__(self) -> float:
        """Convert the borrowed value to a float.

        Returns:
            float: The borrowed value as a ``float``.
        """
        return float(self._cell._value)

    def __str__(self) -> str:
        """Convert the borrowed value to a string.

        Returns:
            str: The borrowed value as a ``str``.
        """
        return str(self._cell._value)

    def __repr__(self) -> str:
        """Return a string representation of the guard.

        Returns:
            str: A repr of the form ``RefMut(<value>)``.
        """
        return f"RefMut({self._cell._value!r})"