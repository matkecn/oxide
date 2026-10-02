"""The ``oxide`` library — Rust-inspired data structures and utilities.

A Python re-imagining of common Rust standard-library types and macros,
including ``Option``/``Result``, iterators, collections, smart pointers,
synchronization primitives, time, I/O, filesystem, networking, process, and
async facilities.

The package re-exports the full public API for convenient import, e.g.
``from oxide import Option, Vec, HashMap``. A curated subset is also available
from :mod:`oxide.prelude`.

Example:
    >>> from oxide import Some, Vec
    >>> Some(5).unwrap()
    5
"""

from __future__ import annotations

from .core.option import Option, Some, NoneOption, None_, none
from .core.result import Result, Ok, Err, PropagateError, propagate, ask, try_ask
from .core.enum import Enum, Variant, match, _, Match, MatchError
from .core.traits import (
    CloneTrait, CopyTrait, DebugTrait, DisplayTrait, DefaultTrait,
    EqTrait, OrdTrait, HashTrait, DropTrait,
    FromTrait, IntoTrait, TryFromTrait, TryIntoTrait,
    AsRefTrait, AsMutTrait, DerefTrait, DerefMutTrait,
    clone, debug, display, default_of, from_, into,
    try_from, try_into, as_ref, as_mut, deref, deref_mut, drop,
)
from .core.convert import (
    Range, RangeInclusive, RangeFrom, RangeTo, RangeToInclusive, RangeFull,
    range_, range_inclusive, range_from, range_to, range_to_inclusive,
)
from .core.error import Error, Backtrace, Location, context

from ._collections.vec import Vec
from ._collections.hashmap import HashMap, Entry, OccupiedEntry, VacantEntry
from ._collections.hashset import HashSet
from ._collections.btreemap import BTreeMap
from ._collections.btreeset import BTreeSet
from ._collections.vecdeque import VecDeque
from ._collections.binary_heap import BinaryHeap
from ._collections.linked_list import LinkedList
from ._collections.extra import Drain, IntoIter, Slice

from .iter.iterator import Iter
from .iter.adapters import (
    Enumerate, Zip, Map, Filter, FilterMap, FlatMap, Flatten,
    Peekable, PeekMut, Fuse, Chain, Cycle, Take, Skip, Rev,
    Inspect, Copied, Cloned, Partition,
)

from .memory.box import Box
from .memory.rc import Rc, Weak
from .memory.arc import Arc
from .memory.cell import Cell
from .memory.refcell import RefCell, Ref, RefMut, BorrowError, BorrowMutError
from .memory.oncecell import OnceCell
from .memory.lazy import Lazy
from .memory.cow import Cow
from .memory.pin import (
    Pin, ManuallyDrop, MaybeUninit, NonNull, PhantomData,
    Borrow, BorrowMut,
)

from .sync.atomic import Atomic, AtomicBool, AtomicInt
from .sync.mutex import Mutex, MutexGuard
from .sync.rwlock import RwLock, RwLockReadGuard, RwLockWriteGuard
from .sync.barrier import Barrier
from .sync.condvar import Condvar
from .sync.channel import Channel, Sender, Receiver
from .sync.once import Once
from .sync.semaphore import Semaphore

from ._time.duration import Duration, UNIX_EPOCH, Elapsed
from ._time.instant import Instant
from ._time.system_time import SystemTime

from ._io.read import Read, BufRead
from ._io.write import Write
from ._io.buffered import BufReader, BufWriter
from ._io.cursor import Cursor, SeekFrom

from .fs.path import Path, PathBuf
from .fs.file import OpenOptions, File
from .fs.metadata import (
    FileType, Permissions, Metadata, DirEntry, ReadDir,
)

from .net.address import Ipv4Addr, Ipv6Addr, IpAddr, SocketAddr, Shutdown
from .net.tcp import TcpStream, TcpListener, Incoming
from .net.udp import UdpSocket

from .process.command import Command
from .process.child import Child, Stdio
from .process.output import (
    ExitStatus, Output, ExitCode,
    args, env, current_dir, current_exe, home_dir, temp_dir,
)

from .async_.future import Future, Poll, Waker, JoinHandle, Stream, spawn, join_all

from .macros.assertions import assert_eq, assert_ne, assert_, debug_assert, debug_assert_eq, debug_assert_ne
from .macros.debugging import Formatter, format_, write_, writeln_, dbg_, dbg, cfg, option_env, include_str, include_bytes, matches
from .macros.panic import panic, todo, unimplemented, ScopeGuard, defer

from .other import (
    Ordering, ControlFlow, Reverse, Wrapping, Saturating, NonZero,
    SmallVec, ArrayVec, TinyVec, BitVec, CreateMeta,
)

__all__ = [
    # core.option
    "Option", "Some", "NoneOption", "None_", "none",
    # core.result
    "Result", "Ok", "Err", "PropagateError", "propagate", "ask", "try_ask",
    # core.enum
    "Enum", "Variant", "match", "_", "Match", "MatchError",
    # core.traits
    "CloneTrait", "CopyTrait", "DebugTrait", "DisplayTrait", "DefaultTrait",
    "EqTrait", "OrdTrait", "HashTrait", "DropTrait",
    "FromTrait", "IntoTrait", "TryFromTrait", "TryIntoTrait",
    "AsRefTrait", "AsMutTrait", "DerefTrait", "DerefMutTrait",
    "clone", "debug", "display", "default_of", "from_", "into",
    "try_from", "try_into", "as_ref", "as_mut", "deref", "deref_mut", "drop",
    # core.convert
    "Range", "RangeInclusive", "RangeFrom", "RangeTo", "RangeToInclusive", "RangeFull",
    "range_", "range_inclusive", "range_from", "range_to", "range_to_inclusive",
    # core.error
    "Error", "Backtrace", "Location", "context",
    # collections
    "Vec", "HashMap", "Entry", "OccupiedEntry", "VacantEntry",
    "HashSet", "BTreeMap", "BTreeSet", "VecDeque", "BinaryHeap",
    "LinkedList", "Drain", "IntoIter", "Slice",
    # iter
    "Iter", "Enumerate", "Zip", "Map", "Filter", "FilterMap", "FlatMap", "Flatten",
    "Peekable", "PeekMut", "Fuse", "Chain", "Cycle", "Take", "Skip", "Rev",
    "Inspect", "Copied", "Cloned", "Partition",
    # memory
    "Box", "Rc", "Weak", "Arc", "Cell", "RefCell", "Ref", "RefMut",
    "BorrowError", "BorrowMutError", "OnceCell", "Lazy", "Cow",
    "Pin", "ManuallyDrop", "MaybeUninit", "NonNull", "PhantomData",
    "Borrow", "BorrowMut",
    # sync
    "Atomic", "AtomicBool", "AtomicInt",
    "Mutex", "MutexGuard", "RwLock", "RwLockReadGuard", "RwLockWriteGuard",
    "Barrier", "Condvar", "Channel", "Sender", "Receiver",
    "Once", "Semaphore",
    # time
    "Duration", "UNIX_EPOCH", "Elapsed", "Instant", "SystemTime",
    # io
    "Read", "Write", "BufRead", "BufReader", "BufWriter", "Cursor", "SeekFrom",
    # fs
    "Path", "PathBuf", "OpenOptions", "File",
    "FileType", "Permissions", "Metadata", "DirEntry", "ReadDir",
    # net
    "Ipv4Addr", "Ipv6Addr", "IpAddr", "SocketAddr", "Shutdown",
    "TcpStream", "TcpListener", "Incoming", "UdpSocket",
    # process
    "Command", "Child", "Stdio", "ExitStatus", "Output", "ExitCode",
    "args", "env", "current_dir", "current_exe", "home_dir", "temp_dir",
    # async_
    "Future", "Poll", "Waker", "JoinHandle", "Stream", "spawn", "join_all",
    # macros
    "assert_eq", "assert_ne", "assert_", "debug_assert", "debug_assert_eq", "debug_assert_ne",
    "Formatter", "format_", "write_", "writeln_", "dbg_", "dbg", "cfg",
    "option_env", "include_str", "include_bytes", "matches",
    "panic", "todo", "unimplemented", "ScopeGuard", "defer",
    # other
    "Ordering", "ControlFlow", "Reverse", "Wrapping", "Saturating", "NonZero",
    "SmallVec", "ArrayVec", "TinyVec", "BitVec", "CreateMeta",
]
