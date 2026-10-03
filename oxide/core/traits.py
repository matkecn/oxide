"""Trait protocols — Rust-style traits as Python protocols.

Defines 17 trait protocols (Clone, Debug, Display, Default, From, Into, etc.)
and corresponding helper functions for polymorphic behavior.
"""

from __future__ import annotations

from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

from .result import Result, Ok, Err


T = TypeVar("T")


@runtime_checkable
class CloneTrait(Protocol[T]):
    """Protocol for types that support explicit cloning.

    A type that implements ``CloneTrait`` provides a ``clone()`` method that
    returns a deep independent copy of the instance. Use the module-level
    ``clone()`` helper to call it polymorphically.

    Example:
        >>> class Box(CloneTrait):
        ...     def __init__(self, v): self.v = v
        ...     def clone(self): return Box(self.v)
        >>> b = Box(1)
        >>> b.clone().v
        1
        >>> b.clone() is b
        False
    """
    def clone(self) -> T:
        """Return an independent copy of this value.

        Returns:
            T: A deep clone of the instance.
        """


@runtime_checkable
class CopyTrait(Protocol[T]):
    """Protocol for types that support cheap copy semantics.

    A type that implements ``CopyTrait`` provides a ``copy()`` method returning
    a copy of the instance. Distinct from ``CloneTrait`` in that copying is
    typically inexpensive and the original remains usable.
    """
    def copy(self) -> T:
        """Return a copy of this value.

        Returns:
            T: A copy of the instance.
        """


@runtime_checkable
class DebugTrait(Protocol):
    """Protocol for types that produce a debug-friendly string representation.

    A type that implements ``DebugTrait`` provides a ``debug()`` method used for
    logging and debugging. Use the module-level ``debug()`` helper to call it.
    """
    def debug(self) -> str:
        """Return a debug-friendly representation of this value.

        Returns:
            str: A string useful for debugging.
        """


@runtime_checkable
class DisplayTrait(Protocol):
    """Protocol for types that produce a user-facing string representation.

    A type that implements ``DisplayTrait`` provides a ``fmt()`` method used for
    human-facing output. Use the module-level ``display()`` helper to call it.
    """
    def fmt(self) -> str:
        """Return a user-facing representation of this value.

        Returns:
            str: A human-readable string.
        """


@runtime_checkable
class DefaultTrait(Protocol[T]):
    """Protocol for types that have a default value.

    A type that implements ``DefaultTrait`` provides a classmethod ``default()``
    returning a canonical empty or zero instance. Use ``default_of()`` to call it.
    """
    @classmethod
    def default(cls) -> T:
        """Return the default instance of this type.

        Returns:
            T: A default-valued instance of the type.
        """


@runtime_checkable
class EqTrait(Protocol):
    """Protocol for types supporting equality comparison.

    A type that implements ``EqTrait`` provides ``eq()`` and ``ne()`` methods
    for structural equality checks.
    """
    def eq(self, other: object) -> bool:
        """Return True if this value is equal to ``other``.

        Args:
            other (object): The value to compare against.

        Returns:
            bool: True if values are equal.
        """
    def ne(self, other: object) -> bool:
        """Return True if this value is not equal to ``other``.

        Args:
            other (object): The value to compare against.

        Returns:
            bool: True if values are not equal.
        """


@runtime_checkable
class OrdTrait(Protocol):
    """Protocol for types supporting total ordering.

    A type that implements ``OrdTrait`` provides comparison methods returning a
    result consistent with a total order over its values.
    """
    def cmp(self, other: object) -> int:
        """Compare this value with ``other``, returning an ordering integer.

        Args:
            other (object): The value to compare against.

        Returns:
            int: Negative if less, zero if equal, positive if greater.
        """
    def lt(self, other: object) -> bool:
        """Return True if this value is less than ``other``.

        Args:
            other (object): The value to compare against.

        Returns:
            bool: True if this value sorts before ``other``.
        """
    def le(self, other: object) -> bool:
        """Return True if this value is less than or equal to ``other``.

        Args:
            other (object): The value to compare against.

        Returns:
            bool: True if this value sorts at or before ``other``.
        """
    def gt(self, other: object) -> bool:
        """Return True if this value is greater than ``other``.

        Args:
            other (object): The value to compare against.

        Returns:
            bool: True if this value sorts after ``other``.
        """
    def ge(self, other: object) -> bool:
        """Return True if this value is greater than or equal to ``other``.

        Args:
            other (object): The value to compare against.

        Returns:
            bool: True if this value sorts at or after ``other``.
        """


@runtime_checkable
class HashTrait(Protocol):
    """Protocol for types that support hashing.

    A type that implements ``HashTrait`` provides a ``hash()`` method returning
    an integer suitable for hashing the value.
    """
    def hash(self) -> int:
        """Return a hash of this value.

        Returns:
            int: An integer hash of the value.
        """


@runtime_checkable
class FromTrait(Protocol[T]):
    """Protocol for types that can be constructed from another value.

    A type that implements ``FromTrait`` provides a classmethod ``from_()``
    performing a lossless conversion from some other value. Use ``from_()``
    helper to construct polymorphically.
    """
    @classmethod
    def from_(cls, value: Any) -> T:
        """Construct an instance of this type from ``value``.

        Args:
            value (Any): The source value to convert.

        Returns:
            T: An instance of this type built from ``value``.
        """


@runtime_checkable
class IntoTrait(Protocol[T]):
    """Protocol for types that can be converted into another type.

    A type that implements ``IntoTrait`` provides an ``into()`` method performing
    a conversion to another type. Use the ``into()`` helper to call it.
    """
    def into(self) -> T:
        """Convert this value into another type.

        Returns:
            T: The converted value.
        """


@runtime_checkable
class TryFromTrait(Protocol[T]):
    """Protocol for types that may fail when constructed from another value.

    A type that implements ``TryFromTrait`` provides a classmethod ``try_from()``
    returning a ``Result`` that is ``Ok`` on success or ``Err`` on failure.
    """
    @classmethod
    def try_from(cls, value: Any) -> Result[T, str]:
        """Attempt to construct an instance from ``value``, returning a Result.

        Args:
            value (Any): The source value to convert.

        Returns:
            Result: ``Ok(instance)`` on success, ``Err(message)`` on failure.
        """


@runtime_checkable
class TryIntoTrait(Protocol[T]):
    """Protocol for types that may fail when converting into another type.

    A type that implements ``TryIntoTrait`` provides a ``try_into()`` method
    returning a ``Result`` that is ``Ok`` on success or ``Err`` on failure.
    """
    def try_into(self) -> Result[T, str]:
        """Attempt to convert this value into another type, returning a Result.

        Returns:
            Result: ``Ok(converted)`` on success, ``Err(message)`` on failure.
        """


@runtime_checkable
class AsRefTrait(Protocol[T]):
    """Protocol for types that provide an immutable reference.

    A type that implements ``AsRefTrait`` provides an ``as_ref()`` method
    returning an immutable view or reference to an inner value.
    """
    def as_ref(self) -> T:
        """Return an immutable reference to the inner value.

        Returns:
            T: An immutable reference or view.
        """


@runtime_checkable
class AsMutTrait(Protocol[T]):
    """Protocol for types that provide a mutable reference.

    A type that implements ``AsMutTrait`` provides an ``as_mut()`` method
    returning a mutable view or reference to an inner value.
    """
    def as_mut(self) -> T:
        """Return a mutable reference to the inner value.

        Returns:
            T: A mutable reference or view.
        """


@runtime_checkable
class DerefTrait(Protocol[T]):
    """Protocol for types that dereference to an inner value.

    A type that implements ``DerefTrait`` provides a ``deref()`` method exposing
    the inner value it wraps.
    """
    def deref(self) -> T:
        """Dereference to the inner value.

        Returns:
            T: The wrapped inner value.
        """


@runtime_checkable
class DerefMutTrait(Protocol[T]):
    """Protocol for types that mutably dereference to an inner value.

    A type that implements ``DerefMutTrait`` provides a ``deref_mut()`` method
    exposing a mutable inner value.
    """
    def deref_mut(self) -> T:
        """Mutably dereference to the inner value.

        Returns:
            T: The wrapped inner value, mutable.
        """


@runtime_checkable
class DropTrait(Protocol):
    """Protocol for types that support explicit resource cleanup.

    A type that implements ``DropTrait`` provides a ``drop()`` method for
    explicitly releasing resources.
    """
    def drop(self) -> None:
        """Release resources held by this value."""



def clone(value: T) -> T:
    """Return a deep clone of the value, using ``.clone()`` if available.

    Prefers the value's own ``clone()`` method; otherwise falls back to
    ``copy.deepcopy``.

    Args:
        value (T): The value to clone.

    Returns:
        T: A deep, independent copy of ``value``.

    Example:
        >>> a = [1, [2, 3]]
        >>> b = clone(a)
        >>> b.append(4)
        >>> b
        [1, [2, 3], 4]
    """
    if hasattr(value, 'clone'):
        return value.clone()
    import copy as _copy
    return _copy.deepcopy(value)


def debug(value: Any) -> str:
    """Return a debug-friendly string for the value, using ``.debug()`` if available.

    Prefers the value's own ``debug()`` method; falls back to ``repr``.

    Args:
        value (Any): The value to format.

    Returns:
        str: A debug-oriented representation of ``value``.

    Example:
        >>> debug("hi")
        "'hi'"
    """
    if hasattr(value, 'debug'):
        return value.debug()
    return repr(value)


def display(value: Any) -> str:
    """Return a user-facing string for the value, using ``.fmt()`` if available.

    Prefers the value's own ``fmt()`` method; falls back to ``str``.

    Args:
        value (Any): The value to format.

    Returns:
        str: A human-friendly representation of ``value``.
    """
    if hasattr(value, 'fmt'):
        return value.fmt()
    return str(value)


def default_of(cls: type[T]) -> T:
    """Return a default instance of the given class, using ``.default()`` if available.

    Tries ``cls.default()``, then ``cls.default(cls)`` to accommodate both
    instance and classmethod signatures, and finally ``cls()``.

    Args:
        cls (type[T]): The class whose default instance is desired.

    Returns:
        T: A default instance of ``cls``.

    Example:
        >>> default_of(list)
        []
    """
    if hasattr(cls, 'default'):
        try:
            return cls.default()
        except TypeError:
            return cls.default(cls)
    return cls()


def from_(cls: type[T], value: Any) -> T:
    """Construct an instance of cls from value, using ``.from_()`` if available.

    Prefers the class's own ``from_()`` classmethod; otherwise falls back to the
    class constructor ``cls(value)``.

    Args:
        cls (type[T]): The target type.
        value (Any): The value to convert.

    Returns:
        T: An instance of ``cls`` built from ``value``.
    """
    if hasattr(cls, 'from_'):
        return cls.from_(value)
    return cls(value)


def into(value: Any, target_type: type[T]) -> T:
    """Convert value into target_type, using ``.into()`` if available.

    Prefers the value's own ``into()`` method; otherwise falls back to the
    ``target_type`` constructor.

    Args:
        value (Any): The value to convert.
        target_type (type[T]): The target type.

    Returns:
        T: ``value`` converted to ``target_type``.
    """
    if hasattr(value, 'into'):
        return value.into()
    return target_type(value)


def try_from(cls: type[T], value: Any) -> Result[T, str]:
    """Attempt to construct an instance of cls from value, returning a Result.

    Prefers the class's ``try_from()`` classmethod, otherwise attempts
    ``cls(value)`` and wraps success in ``Ok`` or failure in ``Err``.

    Args:
        cls (type[T]): The target type.
        value (Any): The value to convert.

    Returns:
        Result[T, str]: ``Ok(instance)`` on success, ``Err(message)`` on failure.
    """
    if hasattr(cls, 'try_from'):
        return cls.try_from(value)
    try:
        return Ok(cls(value))
    except Exception as e:
        return Err(str(e))


def try_into(value: Any, target_type: type[T]) -> Result[T, str]:
    """Attempt to convert value into target_type, returning a Result.

    Prefers the value's ``try_into()`` method, otherwise attempts
    ``target_type(value)`` and wraps success in ``Ok`` or failure in ``Err``.

    Args:
        value (Any): The value to convert.
        target_type (type[T]): The target type.

    Returns:
        Result[T, str]: ``Ok(converted)`` on success, ``Err(message)`` on failure.
    """
    if hasattr(value, 'try_into'):
        return value.try_into()
    try:
        return Ok(target_type(value))
    except Exception as e:
        return Err(str(e))


def as_ref(value: T) -> T:
    """Return an immutable reference to the value, using ``.as_ref()`` if available.

    Prefers the value's ``as_ref()`` method; otherwise returns the value itself.

    Args:
        value (T): The value to reference.

    Returns:
        T: An immutable reference or the value itself.
    """
    if hasattr(value, 'as_ref'):
        return value.as_ref()
    return value


def as_mut(value: T) -> T:
    """Return a mutable reference to the value, using ``.as_mut()`` if available.

    Prefers the value's ``as_mut()`` method; otherwise returns the value itself.

    Args:
        value (T): The value to reference mutably.

    Returns:
        T: A mutable reference or the value itself.
    """
    if hasattr(value, 'as_mut'):
        return value.as_mut()
    return value


def deref(value: T) -> T:
    """Dereference the value, using ``.deref()`` if available.

    Prefers the value's ``deref()`` method; otherwise returns the value itself.

    Args:
        value (T): The value to dereference.

    Returns:
        T: The dereferenced inner value or the value itself.
    """
    if hasattr(value, 'deref'):
        return value.deref()
    return value


def deref_mut(value: T) -> T:
    """Mutably dereference the value, using ``.deref_mut()`` if available.

    Prefers the value's ``deref_mut()`` method; otherwise returns the value itself.

    Args:
        value (T): The value to dereference mutably.

    Returns:
        T: The mutated inner value or the value itself.
    """
    if hasattr(value, 'deref_mut'):
        return value.deref_mut()
    return value


def drop(value: Any) -> None:
    """Explicitly drop the value, calling ``.drop()`` if available.

    Invokes the value's ``drop()`` method if it has one, otherwise does nothing.

    Args:
        value (Any): The value to release resources for.
    """
    if hasattr(value, 'drop'):
        value.drop()
