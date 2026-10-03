"""Memory management — Box, Rc, Arc, Cell, RefCell, Cow, Pin, and smart pointers.

This package provides Rust-inspired ownership, reference counting, interior
mutability, lazy initialization, and low-level memory primitives: ``Box``,
``Rc``/``Weak``, ``Arc``, ``Cell``, ``RefCell``, ``OnceCell``, ``Lazy``,
``Cow``, ``Pin``, ``ManuallyDrop``, ``MaybeUninit``, ``NonNull``,
``PhantomData``, and the ``Borrow``/``BorrowMut`` borrow guards.
"""

from __future__ import annotations

from .box import Box
from .rc import Rc, Weak
from .cell import Cell
from .refcell import RefCell, Ref, RefMut, BorrowError, BorrowMutError
from .oncecell import OnceCell
from .lazy import Lazy
from .cow import Cow, CowBorrowed, CowOwned
from .pin import Pin, ManuallyDrop, MaybeUninit, NonNull, PhantomData, Borrow, BorrowMut
from .arc import Arc

__all__ = [
    "Box",
    "Rc",
    "Weak",
    "Cell",
    "RefCell",
    "Ref",
    "RefMut",
    "OnceCell",
    "Lazy",
    "Cow",
    "CowBorrowed",
    "CowOwned",
    "Pin",
    "ManuallyDrop",
    "MaybeUninit",
    "NonNull",
    "PhantomData",
    "Borrow",
    "BorrowMut",
    "BorrowError",
    "BorrowMutError",
    "Arc",
]