"""Pin and related types — pinned references and low-level memory primitives.

Provides ``Pin`` for preventing a value from being moved, ``ManuallyDrop``
for controlling when a value is dropped, ``MaybeUninit`` for uninitialized
slots, ``NonNull`` for guaranteed non-null values, ``PhantomData`` as a
zero-sized type-level marker, and the ``Borrow``/``BorrowMut`` borrow guards.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

T = TypeVar("T")


class Pin(Generic[T]):
    """A pinned reference that prevents the contained value from being moved.

    Analogous to Rust's ``Pin``, wrapping a value in a ``Pin`` marks it as
    immovable while the pin lives. The value is handed back (and the pin
    released) via :meth:`into_inner`.

    Examples:
        >>> pin = Pin.new([1, 2])
        >>> pin.is_pinned()
        True
        >>> pin.as_ref()
        [1, 2]
    """

    __slots__ = ("_value", "_pinned")

    def __init__(self, value: T) -> None:
        """Construct a new pinned reference around the given value.

        Args:
            value (T): The value to pin in place.
        """
        self._value = value
        self._pinned = True

    @classmethod
    def new(cls, value: T) -> Pin[T]:
        """Create a new pinned value.

        Args:
            value (T): The value to pin.

        Returns:
            Pin[T]: A new pin guarding the value.

        Examples:
            >>> Pin.new(5).is_pinned()
            True
        """
        return cls(value)

    @classmethod
    def into_pin(cls, value: T) -> Pin[T]:
        """Pin the given value.

        Args:
            value (T): The value to pin.

        Returns:
            Pin[T]: A new pin guarding the value.
        """
        return cls(value)

    def as_ref(self) -> T:
        """Return a reference to the pinned value.

        Returns:
            T: The pinned value; the pin remains active.
        """
        return self._value

    def as_mut(self) -> T:
        """Return a mutable reference to the pinned value.

        Returns:
            T: The pinned value viewed as mutable.
        """
        return self._value

    def into_inner(self) -> T:
        """Unpin and consume the value, returning the contained data.

        The pin is released and the value is handed back to the caller.

        Returns:
            T: The previously pinned value.

        Examples:
            >>> Pin.new(5).into_inner()
            5
        """
        self._pinned = False
        return self._value

    def is_pinned(self) -> bool:
        """Return True if the value is currently pinned.

        Returns:
            bool: ``True`` if the value is still pinned, ``False`` if the pin
                has been released by :meth:`into_inner`.
        """
        return self._pinned

    def __repr__(self) -> str:
        """Return a string representation of the Pin.

        Returns:
            str: A repr of the form ``Pin(<value>)``.
        """
        return f"Pin({self._value!r})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another Pin by comparing the contained values.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: ``True`` if ``other`` is a ``Pin`` wrapping an equal value,
                otherwise ``NotImplemented``.
        """
        if isinstance(other, Pin):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        """Return the hash of the contained value.

        Returns:
            int: The hash of the pinned value.
        """
        return hash(self._value)

    def __enter__(self) -> Pin[T]:
        """Enter the context manager, returning self.

        Returns:
            Pin[T]: The Pin itself, ready for use inside the ``with`` block.
        """
        return self

    def __exit__(self, *_: Any) -> None:
        """Exit the context manager, performing no extra cleanup.

        Args:
            *_ (Any): The exception type, value, and traceback (if any), which
                are ignored.
        """
        pass


class ManuallyDrop(Generic[T]):
    """A wrapper that gives explicit control over when a value is dropped.

    The wrapped value is kept intact until :meth:`drop`, :meth:`into_inner`,
    or the destruction of the wrapper. Useful when the default cleanup would
    happen too early.

    Examples:
        >>> m = ManuallyDrop.new(1)
        >>> m.is_dropped()
        False
        >>> m.drop()
        >>> m.is_dropped()
        True
    """

    __slots__ = ("_value", "_dropped")

    def __init__(self, value: T) -> None:
        """Construct a new ManuallyDrop wrapping the given value.

        Args:
            value (T): The value to wrap.
        """
        self._value = value
        self._dropped = False

    @classmethod
    def new(cls, value: T) -> ManuallyDrop[T]:
        """Create a new ManuallyDrop wrapping the given value.

        Args:
            value (T): The value to wrap.

        Returns:
            ManuallyDrop[T]: A new wrapper holding ``value``.

        Examples:
            >>> ManuallyDrop.new(3).as_ref()
            3
        """
        return cls(value)

    def as_ref(self) -> T:
        """Return a reference to the contained value.

        Returns:
            T: The wrapped value.
        """
        return self._value

    def as_mut(self) -> T:
        """Return a mutable reference to the contained value.

        Returns:
            T: The wrapped value viewed as mutable.
        """
        return self._value

    def into_inner(self) -> T:
        """Take ownership of the value, marking it as dropped.

        Returns:
            T: The contained value; the wrapper is afterwards considered
                dropped.

        Examples:
            >>> m = ManuallyDrop.new(5)
            >>> m.into_inner()
            5
            >>> m.is_dropped()
            True
        """
        self._dropped = True
        return self._value

    def drop(self) -> None:
        """Explicitly drop the contained value.

        Marks the value as dropped and clears it out, so it can no longer be
        read afterwards.

        Examples:
            >>> m = ManuallyDrop.new(5)
            >>> m.drop()
            >>> m.is_dropped()
            True
        """
        self._dropped = True
        self._value = None  # type: ignore[assignment]

    def is_dropped(self) -> bool:
        """Return True if the value has been dropped.

        Returns:
            bool: ``True`` if the value was dropped or taken via
                :meth:`into_inner`.
        """
        return self._dropped

    def __repr__(self) -> str:
        """Return a string representation of the ManuallyDrop.

        Returns:
            str: A repr of the form ``ManuallyDrop(<value>)``.
        """
        return f"ManuallyDrop({self._value!r})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another ManuallyDrop by comparing the values.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: ``True`` if ``other`` is a ``ManuallyDrop`` wrapping an equal
                value, otherwise ``NotImplemented``.
        """
        if isinstance(other, ManuallyDrop):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        """Return the hash of the contained value.

        Returns:
            int: The hash of the wrapped value.
        """
        return hash(self._value)

    def __del__(self) -> None:
        """Mark the value as dropped on destruction."""
        if not self._dropped:
            self._dropped = True


class MaybeUninit(Generic[T]):
    """A container that may or may not hold an initialized value.

    Analogous to Rust's ``MaybeUninit``, the slot starts uninitialized. Use
    :meth:`write` to store a value and :meth:`assume_init` to read it back
    out, asserting that it has been initialized.

    Examples:
        >>> u = MaybeUninit.uninit()
        >>> u.is_initialized()
        False
        >>> u.write(100)
        100
        >>> u.assume_init()
        100
    """

    __slots__ = ("_value", "_initialized")

    def __init__(self) -> None:
        """Construct an uninitialized MaybeUninit slot."""
        self._value: T = None  # type: ignore[assignment]
        self._initialized = False

    @classmethod
    def new(cls) -> MaybeUninit[T]:
        """Create a new uninitialized MaybeUninit.

        Returns:
            MaybeUninit[T]: An empty slot.
        """
        return cls()

    @classmethod
    def uninit(cls) -> MaybeUninit[T]:
        """Create a new uninitialized MaybeUninit.

        Returns:
            MaybeUninit[T]: An empty slot.

        Examples:
            >>> MaybeUninit.uninit().is_initialized()
            False
        """
        return cls()

    @classmethod
    def init(cls, value: T) -> MaybeUninit[T]:
        """Create a new MaybeUninit already initialized with the given value.

        Args:
            value (T): The value to store as initialized.

        Returns:
            MaybeUninit[T]: An initialized slot.
        """
        cell = cls()
        cell._value = value
        cell._initialized = True
        return cell

    def assume_init(self) -> T:
        """Return the contained value, raising if the slot is uninitialized.

        Returns:
            T: The stored value.

        Raises:
            ValueError: If the slot has not been initialized yet.

        Examples:
            >>> MaybeUninit.init(7).assume_init()
            7
        """
        if not self._initialized:
            raise ValueError("MaybeUninit is not initialized")
        return self._value

    def write(self, value: T) -> T:
        """Write a value into the slot, marking it as initialized.

        Args:
            value (T): The value to store.

        Returns:
            T: The value that was written.

        Examples:
            >>> u = MaybeUninit.uninit()
            >>> u.write(3)
            3
        """
        self._value = value
        self._initialized = True
        return value

    def as_ptr(self) -> int:
        """Return the identity of the contained value.

        Returns:
            int: The identity of the stored value.
        """
        return id(self._value)

    def is_initialized(self) -> bool:
        """Return True if the cell holds an initialized value.

        Returns:
            bool: ``True`` if a value has been written to the slot.
        """
        return self._initialized

    def __repr__(self) -> str:
        """Return a string representation of the MaybeUninit.

        Returns:
            str: A repr of the form ``MaybeUninit(<value>)``, or
                ``MaybeUninit(<uninitialized>)`` while the slot is empty.
        """
        if self._initialized:
            return f"MaybeUninit({self._value!r})"
        return "MaybeUninit(<uninitialized>)"

    def __bool__(self) -> bool:
        """Return True if the cell is initialized.

        Returns:
            bool: ``True`` if a value has been written to the slot.
        """
        return self._initialized

    def __eq__(self, other: object) -> bool:
        """Check equality with another MaybeUninit.

        Uninitialized slots are never equal to anything.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: ``True`` if ``other`` is an initialized ``MaybeUninit``
                holding an equal value, otherwise ``NotImplemented``.
        """
        if isinstance(other, MaybeUninit):
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


class NonNull(Generic[T]):
    """A wrapper that guarantees the contained value is never None.

    Construction, :meth:`new`, and :meth:`replace` reject ``None`` by raising
    ``ValueError``, so the stored value can safely be assumed non-null.

    Examples:
        >>> n = NonNull.new(5)
        >>> n.as_ref()
        5
        >>> n.replace(6)
        5
        >>> n.as_ref()
        6
    """

    __slots__ = ("_value",)

    def __init__(self, value: T) -> None:
        """Construct a new NonNull, rejecting ``None``.

        Args:
            value (T): The value to hold.

        Raises:
            ValueError: If ``value`` is ``None``.
        """
        if value is None:
            raise ValueError("NonNull cannot hold None")
        self._value = value

    @classmethod
    def new(cls, value: T) -> NonNull[T]:
        """Create a new NonNull, raising ValueError if the value is None.

        Args:
            value (T): The value to hold.

        Returns:
            NonNull[T]: A new non-null wrapper.

        Raises:
            ValueError: If ``value`` is ``None``.

        Examples:
            >>> NonNull.new(10).as_ref()
            10
        """
        return cls(value)

    def as_ref(self) -> T:
        """Return a reference to the non-null value.

        Returns:
            T: The contained value.
        """
        return self._value

    def as_mut(self) -> T:
        """Return a mutable reference to the non-null value.

        Returns:
            T: The contained value viewed as mutable.
        """
        return self._value

    def replace(self, value: T) -> T:
        """Replace the contained value, returning the old value.

        Args:
            value (T): The new value to store.

        Returns:
            T: The previous contained value.

        Raises:
            ValueError: If ``value`` is ``None``.

        Examples:
            >>> n = NonNull.new(1)
            >>> n.replace(2)
            1
        """
        if value is None:
            raise ValueError("NonNull cannot hold None")
        old = self._value
        self._value = value
        return old

    def into_inner(self) -> T:
        """Consume the NonNull and return the contained value.

        Returns:
            T: The contained value.
        """
        return self._value

    def is_null(self) -> bool:
        """Return whether the contained value is null.

        A ``NonNull`` can never hold ``None``, so this always returns
        ``False``.

        Returns:
            bool: Always ``False``.
        """
        return False

    def as_ptr(self) -> int:
        """Return the identity of the contained value.

        Returns:
            int: The identity of the stored value.
        """
        return id(self._value)

    def __repr__(self) -> str:
        """Return a string representation of the NonNull.

        Returns:
            str: A repr of the form ``NonNull(<value>)``.
        """
        return f"NonNull({self._value!r})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another NonNull by comparing the contained values.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: ``True`` if ``other`` is a ``NonNull`` wrapping an equal
                value, otherwise ``NotImplemented``.
        """
        if isinstance(other, NonNull):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        """Return the hash of the contained value.

        Returns:
            int: The hash of the stored value.
        """
        return hash(self._value)

    def __bool__(self) -> bool:
        """Return whether the NonNull is truthy.

        A ``NonNull`` is always truthy.

        Returns:
            bool: Always ``True``.
        """
        return True


class PhantomData(Generic[T]):
    """A zero-sized type-level marker that carries no data.

    Used to attach a type parameter to a class without storing a value of
    that type.

    Examples:
        >>> repr(PhantomData.new())
        'PhantomData'
    """

    __slots__ = ()

    def __init__(self) -> None:
        """Construct an empty PhantomData marker."""
        pass

    @classmethod
    def new(cls) -> PhantomData[T]:
        """Create a new PhantomData instance.

        Returns:
            PhantomData[T]: A new type-level marker.
        """
        return cls()

    def __repr__(self) -> str:
        """Return a string representation of the PhantomData.

        Returns:
            str: Always ``'PhantomData'``.
        """
        return "PhantomData"

    def __bool__(self) -> bool:
        """Return whether PhantomData is truthy.

        A ``PhantomData`` holds no data and is always falsy.

        Returns:
            bool: Always ``False``.
        """
        return False

    def __eq__(self, other: object) -> bool:
        """Check equality with another PhantomData.

        All ``PhantomData`` instances, regardless of type argument, are
        considered equal because they carry no data.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: ``True`` if ``other`` is a ``PhantomData`` instance.
        """
        return isinstance(other, PhantomData)

    def __hash__(self) -> int:
        """Return a constant hash for all PhantomData instances.

        Returns:
            int: Always ``0``.
        """
        return 0


class Borrow(Generic[T]):
    """An immutable borrow guard that tracks the borrowed value and its owner.

    Keeps a reference to the borrowed value along with an optional owner;
    useful as a lightweight guard when sharing an immutable view.

    Examples:
        >>> b = Borrow.new([1, 2])
        >>> b.as_ref()
        [1, 2]
    """

    __slots__ = ("_value", "_owner")

    def __init__(self, value: T, owner: Any = None) -> None:
        """Construct a new immutable borrow.

        Args:
            value (T): The value being borrowed.
            owner (Any, optional): An optional owner or borrower token.
        """
        self._value = value
        self._owner = owner

    @classmethod
    def new(cls, value: T, owner: Any = None) -> Borrow[T]:
        """Create a new immutable borrow of the given value.

        Args:
            value (T): The value being borrowed.
            owner (Any, optional): An optional owner or borrower token.

        Returns:
            Borrow[T]: A new immutable borrow.
        """
        return cls(value, owner)

    def as_ref(self) -> T:
        """Return a reference to the borrowed value.

        Returns:
            T: The borrowed value.
        """
        return self._value

    def into_inner(self) -> T:
        """Consume the borrow and return the contained value.

        Returns:
            T: The borrowed value.
        """
        return self._value

    def __repr__(self) -> str:
        """Return a string representation of the Borrow.

        Returns:
            str: A repr of the form ``Borrow(<value>)``.
        """
        return f"Borrow({self._value!r})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another Borrow by comparing the contained values.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: ``True`` if ``other`` is a ``Borrow`` wrapping an equal
                value, otherwise ``NotImplemented``.
        """
        if isinstance(other, Borrow):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        """Return the hash of the borrowed value.

        Returns:
            int: The hash of the borrowed value.
        """
        return hash(self._value)

    def __enter__(self) -> Borrow[T]:
        """Enter the context manager, returning self.

        Returns:
            Borrow[T]: The guard itself.
        """
        return self

    def __exit__(self, *_: Any) -> None:
        """Exit the context manager, performing no extra cleanup.

        Args:
            *_ (Any): The exception type, value, and traceback (if any), which
                are ignored.
        """
        pass


class BorrowMut(Generic[T]):
    """A mutable borrow guard that tracks the borrowed value, owner, and release state.

    Grants mutable access to a borrowed value, tracks an optional owner, and
    records whether the borrow has been released.

    Examples:
        >>> bm = BorrowMut.new(0)
        >>> bm.value
        0
        >>> bm.value = 5
        >>> bm.is_released()
        False
        >>> bm.release()
        >>> bm.is_released()
        True
    """

    __slots__ = ("_value", "_owner", "_released")

    def __init__(self, value: T, owner: Any = None) -> None:
        """Construct a new mutable borrow.

        Args:
            value (T): The value being borrowed.
            owner (Any, optional): An optional owner or borrower token.
        """
        self._value = value
        self._owner = owner
        self._released = False

    @classmethod
    def new(cls, value: T, owner: Any = None) -> BorrowMut[T]:
        """Create a new mutable borrow of the given value.

        Args:
            value (T): The value being borrowed.
            owner (Any, optional): An optional owner or borrower token.

        Returns:
            BorrowMut[T]: A new mutable borrow.
        """
        return cls(value, owner)

    @property
    def value(self) -> T:
        """Return the borrowed value.

        Returns:
            T: The borrowed value.
        """
        return self._value

    @value.setter
    def value(self, v: T) -> None:
        """Set the borrowed value through the mutable borrow.

        Args:
            v (T): The new value to store.
        """
        self._value = v

    def replace(self, v: T) -> T:
        """Replace the borrowed value and return the previous value.

        Args:
            v (T): The new value to store.

        Returns:
            T: The value previously held by the borrow.
        """
        old = self._value
        self._value = v
        return old

    def into_inner(self) -> T:
        """Consume the borrow, marking it as released, and return the value.

        Returns:
            T: The borrowed value.
        """
        self._released = True
        return self._value

    def release(self) -> None:
        """Release the mutable borrow.

        Records that the borrow is no longer active.
        """
        self._released = True

    def is_released(self) -> bool:
        """Return True if the borrow has been released.

        Returns:
            bool: ``True`` if the borrow was released or consumed.
        """
        return self._released

    def __enter__(self) -> BorrowMut[T]:
        """Enter the context manager, returning self.

        Returns:
            BorrowMut[T]: The guard itself.
        """
        return self

    def __exit__(self, *_: Any) -> None:
        """Exit the context manager, releasing the borrow.

        Args:
            *_ (Any): The exception type, value, and traceback (if any), which
                are ignored.
        """
        self.release()

    def __repr__(self) -> str:
        """Return a string representation of the BorrowMut.

        Returns:
            str: A repr of the form ``BorrowMut(<value>)``.
        """
        return f"BorrowMut({self._value!r})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another BorrowMut by comparing the values.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: ``True`` if ``other`` is a ``BorrowMut`` wrapping an equal
                value, otherwise ``NotImplemented``.
        """
        if isinstance(other, BorrowMut):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        """Return the hash of the borrowed value.

        Returns:
            int: The hash of the borrowed value.
        """
        return hash(self._value)