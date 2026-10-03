"""Synchronization primitives — Atomic, Mutex, RwLock, Channel, Barrier, and more.

Provides Atomic types, Mutex, RwLock, Channel (MPSC), Once, Semaphore, and the
shared :class:`~oxide.memory.Arc` smart pointer for safe multi-threaded
coordination.

``Arc`` is not defined here — it lives in :mod:`oxide.memory` and is
re-exported so that ``oxide.sync.Arc is oxide.memory.Arc``. There is only one
``Arc`` type in the library.
"""

from .atomic import Atomic, AtomicBool, AtomicInt
from .mutex import Mutex, MutexGuard
from .rwlock import RwLock, RwLockReadGuard, RwLockWriteGuard
from ..memory.arc import Arc
from .barrier import Barrier
from .condvar import Condvar
from .channel import Channel, Sender, Receiver
from .once import Once
from .semaphore import Semaphore

__all__ = [
    "Atomic",
    "AtomicBool",
    "AtomicInt",
    "Mutex",
    "MutexGuard",
    "Arc",
    "RwLock",
    "RwLockReadGuard",
    "RwLockWriteGuard",
    "Barrier",
    "Condvar",
    "Channel",
    "Sender",
    "Receiver",
    "Once",
    "Semaphore",
]
