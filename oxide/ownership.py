"""Ownership and borrowing — Rust's ownership model for Python.

Implements the ownership-side concepts of Rust:

* Ownership (1): :class:`Owner` is the sole owner of a value.
* Borrowing (2): :meth:`Owner.borrow` and :meth:`Owner.borrow_mut`.
* ``&T`` (3): :class:`Borrowed`, an immutable borrow guard.
* ``&mut T`` (4): :class:`BorrowedMut`, an exclusive mutable borrow.
* Move (5): :class:`Move` and :func:`move_` transfer ownership.
* Lifetimes (8): :class:`Lifetime` scopes borrows to a region.
* RAII (9): :class:`RAII` ties a resource to a guard's lifetime.

Rust's RAII guards and scoped resources are already implemented by
:class:`~oxide.macros.panic.ScopeGuard` and
:func:`~oxide.macros.panic.defer`, which are re-exported from
:mod:`oxide` as ``ScopeGuard`` and ``defer``; this module does not
duplicate them.
"""

from __future__ import annotations

from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")

__all__ = [
    "Owner", "own", "Move", "move_", "MovedError",
    "Borrowed", "BorrowedMut",
    "Lifetime", "LifetimeRef", "LifetimeError",
    "RAII", "raii",
]


class MovedError(RuntimeError):
    """Raised when a moved-from :class:`Owner` or spent :class:`Move` is used."""


class Owner(Generic[T]):
    """The sole owner of a value.

    An ``Owner`` tracks who controls a value: while it is not moved,
    it is the only handle to that value. Borrow it read-only with
    :meth:`borrow`, exclusively with :meth:`borrow_mut`, or transfer
    ownership out entirely with :meth:`move_`.

    Examples:
        >>> from oxide import Owner
        >>> owner = Owner([1, 2, 3])
        >>> owner.borrow().get()
        [1, 2, 3]
        >>> with owner.borrow_mut() as b:
        ...     b.set([4, 5])
        >>> owner.get()
        [4, 5]
        >>> owner.move_()
        [4, 5]
        >>> owner.is_moved()
        True
    """

    __slots__ = ("_value", "_moved")

    def __init__(self, value: T) -> None:
        """Create an owner for a value.

        Args:
            value (T): The value to own.
        """
        self._value = value
        self._moved = False

    def get(self) -> T:
        """Return the owned value.

        Returns:
            T: The owned value.

        Raises:
            MovedError: If ownership has already been transferred.
        """
        self._check()
        return self._value

    def borrow(self) -> Borrowed[T]:
        """Borrow the value read-only.

        Returns:
            Borrowed[T]: An immutable borrow guard.

        Raises:
            MovedError: If ownership has already been transferred.
        """
        self._check()
        return Borrowed(self)

    def borrow_mut(self) -> BorrowedMut[T]:
        """Borrow the value exclusively for mutation.

        Returns:
            BorrowedMut[T]: A mutable borrow guard.

        Raises:
            MovedError: If ownership has already been transferred.
        """
        self._check()
        return BorrowedMut(self)

    def move_(self) -> T:
        """Transfer ownership of the value out of this owner.

        Returns:
            T: The value. The owner is empty afterwards.

        Raises:
            MovedError: If ownership has already been transferred.
        """
        self._check()
        self._moved = True
        return self._value

    def is_moved(self) -> bool:
        """Return True if ownership has been transferred.

        Returns:
            bool: True once :meth:`move_` has been called.
        """
        return self._moved

    def _check(self) -> None:
        if self._moved:
            raise MovedError("value moved out of its owner")

    def __repr__(self) -> str:
        if self._moved:
            return f"{type(self).__name__}(moved)"
        return f"{type(self).__name__}({self._value!r})"


class Borrowed(Generic[T]):
    """An immutable borrow (``&T``) of an owned value.

    Examples:
        >>> from oxide import Owner
        >>> owner = Owner("shared")
        >>> with owner.borrow() as b:
        ...     b.get()
        'shared'
    """

    __slots__ = ("_owner",)

    def __init__(self, owner: Owner[T]) -> None:
        """Borrow from an owner.

        Args:
            owner (Owner[T]): The owner to borrow from.
        """
        self._owner = owner

    def get(self) -> T:
        """Return the borrowed value.

        Returns:
            T: The value behind the borrow.

        Raises:
            MovedError: If the owner was moved while borrowed.
        """
        return self._owner.get()

    def __enter__(self) -> Borrowed[T]:
        return self

    def __exit__(self, *_: Any) -> None:
        return None

    def __repr__(self) -> str:
        try:
            return f"Borrowed({self._owner.get()!r})"
        except MovedError:
            return "Borrowed(moved)"


class BorrowedMut(Generic[T]):
    """An exclusive mutable borrow (``&mut T``) of an owned value.

    Examples:
        >>> from oxide import Owner
        >>> owner = Owner([1])
        >>> with owner.borrow_mut() as b:
        ...     b.set([1, 2])
        ...     b.get()
        [1, 2]
        >>> owner.get()
        [1, 2]
    """

    __slots__ = ("_owner",)

    def __init__(self, owner: Owner[T]) -> None:
        """Borrow exclusively from an owner.

        Args:
            owner (Owner[T]): The owner to borrow from.
        """
        self._owner = owner

    def get(self) -> T:
        """Return the borrowed value.

        Returns:
            T: The value behind the borrow.

        Raises:
            MovedError: If the owner was moved while borrowed.
        """
        return self._owner.get()

    def set(self, value: T) -> None:
        """Replace the owned value through this borrow.

        Args:
            value (T): The new value to write through the borrow.

        Raises:
            MovedError: If the owner was moved while borrowed.
        """
        self._owner._check()
        self._owner._value = value

    def __enter__(self) -> BorrowedMut[T]:
        return self

    def __exit__(self, *_: Any) -> None:
        return None

    def __repr__(self) -> str:
        try:
            return f"BorrowedMut({self._owner.get()!r})"
        except MovedError:
            return "BorrowedMut(moved)"


class Move(Generic[T]):
    """A value in transit — its ownership has been transferred.

    ``Move`` marks Rust's ``move`` semantics: once a value is wrapped,
    the original binding should no longer be used. Extract the value
    exactly once with :meth:`take`.

    Examples:
        >>> from oxide import Move
        >>> moved = Move([1, 2, 3])
        >>> moved.take()
        [1, 2, 3]
        >>> moved.is_taken()
        True
        >>> moved.take()
        Traceback (most recent call last):
            ...
        oxide.ownership.MovedError: value already taken from Move
    """

    __slots__ = ("_value", "_taken")

    def __init__(self, value: T) -> None:
        """Wrap a value as moved.

        Args:
            value (T): The value being transferred.
        """
        self._value = value
        self._taken = False

    def take(self) -> T:
        """Take the value, consuming the move.

        Returns:
            T: The transferred value.

        Raises:
            MovedError: If the value has already been taken.
        """
        if self._taken:
            raise MovedError("value already taken from Move")
        self._taken = True
        return self._value

    def is_taken(self) -> bool:
        """Return True if the value has been taken.

        Returns:
            bool: True once :meth:`take` succeeds.
        """
        return self._taken

    def __repr__(self) -> str:
        if self._taken:
            return "Move(taken)"
        return f"Move({self._value!r})"


def own(value: T) -> Owner[T]:
    """Create an :class:`Owner` for a value.

    Args:
        value (T): The value to take ownership of.

    Returns:
        Owner[T]: The sole owner of ``value``.

    Examples:
        >>> from oxide import own
        >>> own(42).get()
        42
    """
    return Owner(value)


def move_(value: T) -> Move[T]:
    """Mark a value as moved, transferring its ownership.

    Args:
        value (T): The value whose ownership transfers.

    Returns:
        Move[T]: A move marker wrapping ``value``.

    Examples:
        >>> from oxide import move_
        >>> move_("data").take()
        'data'
    """
    return Move(value)


class LifetimeError(RuntimeError):
    """Raised when a borrow outlives its :class:`Lifetime`."""


class Lifetime:
    """A lexical scope that invalidates its borrows when it ends.

    ``Lifetime`` models Rust's lifetime system: references handed out
    by a lifetime are valid only while the lifetime is alive.

    Examples:
        >>> from oxide import Lifetime
        >>> with Lifetime() as lifetime:
        ...     ref = lifetime.borrow(42)
        ...     ref.get()
        42
        >>> ref.get()
        Traceback (most recent call last):
            ...
        oxide.ownership.LifetimeError: borrow expired: lifetime has ended
    """

    __slots__ = ("_alive",)

    def __init__(self) -> None:
        """Create a live lifetime scope."""
        self._alive = True

    @property
    def alive(self) -> bool:
        """Whether borrows from this lifetime are still valid.

        Returns:
            bool: True until the lifetime scope exits.
        """
        return self._alive

    def borrow(self, value: T) -> LifetimeRef[T]:
        """Borrow a value for the duration of this lifetime.

        Args:
            value (T): The value to borrow.

        Returns:
            LifetimeRef[T]: A reference valid only while the lifetime lives.

        Raises:
            LifetimeError: If the lifetime has already ended.
        """
        if not self._alive:
            raise LifetimeError("borrow expired: lifetime has ended")
        return LifetimeRef(self, value)

    def __enter__(self) -> Lifetime:
        return self

    def __exit__(self, *_: Any) -> None:
        self._alive = False
        return None

    def __repr__(self) -> str:
        return f"Lifetime({'alive' if self._alive else 'ended'})"


class LifetimeRef(Generic[T]):
    """A reference valid only within its :class:`Lifetime`.

    Examples:
        >>> from oxide import Lifetime
        >>> with Lifetime() as lifetime:
        ...     ref = lifetime.borrow("temp")
        ...     ref
        LifetimeRef('temp')
    """

    __slots__ = ("_lifetime", "_value")

    def __init__(self, lifetime: Lifetime, value: T) -> None:
        """Borrow a value for a lifetime's duration.

        Args:
            lifetime (Lifetime): The scope the borrow belongs to.
            value (T): The value to borrow.
        """
        self._lifetime = lifetime
        self._value = value

    def get(self) -> T:
        """Return the referenced value.

        Returns:
            T: The value, if the lifetime is still alive.

        Raises:
            LifetimeError: If the lifetime has ended.
        """
        if not self._lifetime.alive:
            raise LifetimeError("borrow expired: lifetime has ended")
        return self._value

    def __repr__(self) -> str:
        return f"LifetimeRef({self._value!r})"


class RAII(Generic[T]):
    """A resource acquired on construction and released on cleanup.

    RAII ties a resource's lifetime to a guard: the resource is
    acquired immediately and released when the guard leaves its scope
    or is garbage collected. Prefer the ``with`` statement;
    ``__del__`` is a safety net, not a guarantee.

    Examples:
        >>> from oxide import RAII
        >>> events = []
        >>> resource = RAII(lambda: "open", events.append)
        >>> resource.resource
        'open'
        >>> resource.release()
        >>> events
        ['open']
    """

    __slots__ = ("_resource", "_release", "_released")

    def __init__(self, acquire: Callable[[], T], release: Callable[[T], None]) -> None:
        """Acquire a resource to be released later.

        Args:
            acquire (Callable[[], T]): Acquires the resource.
            release (Callable[[T], None]): Releases the resource.
        """
        self._resource = acquire()
        self._release = release
        self._released = False

    @property
    def resource(self) -> T:
        """The acquired resource.

        Returns:
            T: The resource, or None once released.
        """
        return self._resource

    def release(self) -> None:
        """Release the resource. Calling this twice is a no-op."""
        if self._released:
            return
        self._released = True
        resource, self._resource = self._resource, None
        self._release(resource)

    def __enter__(self) -> RAII[T]:
        return self

    def __exit__(self, *_: Any) -> None:
        self.release()
        return None

    def __del__(self) -> None:
        try:
            self.release()
        except Exception:  # pragma: no cover - best-effort cleanup
            pass

    def __repr__(self) -> str:
        if self._released:
            return f"{type(self).__name__}(released)"
        return f"{type(self).__name__}({self._resource!r})"


def raii(acquire: Callable[[], T], release: Callable[[T], None]) -> RAII[T]:
    """Acquire a resource and release it when the guard ends.

    Args:
        acquire (Callable[[], T]): Acquires the resource.
        release (Callable[[T], None]): Releases the resource.

    Returns:
        RAII[T]: A guard holding the acquired resource.

    Examples:
        >>> from oxide import raii
        >>> log = []
        >>> with raii(lambda: 1, lambda v: log.append(v)) as guard:
        ...     guard.resource
        1
        >>> log
        [1]
    """
    return RAII(acquire, release)
