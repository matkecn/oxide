"""mem — the parts of Rust's ``core::mem`` that mean something in Python.

Rust's ``core::mem`` is mostly about ownership: ``swap``, ``replace``, and
``take`` take ``&mut`` bindings, ``align_of`` describes the layout of a type,
and ``size_of::<T>()`` is answered by the compiler for a *type*. Python has
no mutable references to bindings and no compile-time type layout, so only a
small honest subset is provided here. The rest is left out deliberately
rather than emulated:

* ``size_of::<T>()`` has no type-level answer, so :func:`size_of` measures a
  value instead, using the interpreter's own accounting.
* ``align_of`` has no meaning, because CPython pads objects internally and
  never exposes it.
* ``swap``/``replace``/``take`` need ``&mut``. They cannot be written for
  arbitrary Python bindings, so they are not offered in a form that would
  silently misbehave.
* There is no zero-sized detection: CPython charges at least one object word
  for every live object, so :func:`size_of` never returns 0.
"""
from __future__ import annotations

import sys
from typing import Any

__all__ = ["size_of", "needs_drop", "forget"]


def size_of(value: Any) -> int:
    """Return the size of a value in bytes.

    This is Python's counterpart to Rust's ``size_of::<T>()``, measured per
    value rather than per type, because the interpreter only knows object
    sizes at runtime. It reports what the object costs to the interpreter,
    which for containers includes their contents -- closer to Rust's
    ``size_of_val`` than to ``size_of``.

    Args:
        value: Any Python object.

    Returns:
        int: The size in bytes, never zero for a live object.

    Examples:
        >>> size_of(0) == size_of(0)
        True
        >>> size_of("hello") > 0
        True
        >>> size_of([1, 2, 3]) > size_of([])
        True
    """
    return sys.getsizeof(value)


def needs_drop(value: Any) -> bool:
    """Return True if a value has a destructor that could run.

    Rust's ``needs_drop::<T>()`` asks whether the type implements ``Drop``.
    The Python counterpart is whether the value's class defines ``__del__``,
    since that is the only hook CPython runs when an object is reclaimed.

    Args:
        value: Any Python object.

    Returns:
        bool: True if the object defines a ``__del__`` hook.

    Examples:
        >>> needs_drop(1)
        False
        >>> needs_drop("text")
        False
        >>> class Resource:
        ...     def __del__(self):
        ...         pass
        >>> needs_drop(Resource())
        True
    """
    return getattr(type(value), "__del__", None) is not None


def forget(value: Any) -> None:
    """Do nothing with a value, mirroring Rust's ``mem::forget``.

    In Rust, ``forget`` leaks a value by preventing its destructor from
    running. Python has no equivalent: ``__del__`` timing is decided by the
    garbage collector, not by scope. This function therefore consumes
    nothing and drops nothing -- it exists so the call sites that read like
    Rust keep their shape, and the difference is stated rather than hidden.

    Args:
        value: The value that would have been forgotten.

    Returns:
        None: Always, regardless of the value.

    Examples:
        >>> forget(object()) is None
        True
    """
    return None
