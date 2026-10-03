"""Curated imports of the most commonly used ``oxide`` types.

Provides a convenient ``from oxide.prelude import *``-style entry point that
re-exports the most frequently used types and functions, so code can avoid
long import lists.

Example:
    >>> from oxide.prelude import Option, Vec, Result
    >>> v = Vec([1, 2, 3])
    >>> len(v)
    3
"""

from __future__ import annotations

from .core.option import Option, Some, NoneOption, None_, none
from .core.result import Result, Ok, Err
from .core.enum import Enum, Variant, match, _
from .core.traits import (
    CloneTrait, DebugTrait, DisplayTrait, DefaultTrait,
    FromTrait, IntoTrait,
    clone, debug, display, default_of, from_, into,
)
from .core.convert import Range, RangeInclusive, range_
from .core.error import Error, Backtrace, Location, context

from ._collections.vec import Vec
from ._collections.hashmap import HashMap
from ._collections.hashset import HashSet

from .iter.iterator import Iter
from .iter.adapters import (
    Enumerate, Zip, Map, FilterIter, Peekable, Chain, Take, Skip, Rev,
)

from .memory.box import Box
from .memory.rc import Rc, Weak
from .memory.arc import Arc
from .memory.cell import Cell
from .memory.refcell import RefCell
from .memory.oncecell import OnceCell
from .memory.lazy import Lazy
from .memory.cow import Cow

from .sync.atomic import Atomic, AtomicBool, AtomicInt
from .sync.mutex import Mutex
from .sync.rwlock import RwLock
from .sync.channel import Channel, Sender, Receiver
from .sync.once import Once
from .sync.semaphore import Semaphore

from ._time.duration import Duration, UNIX_EPOCH
from ._time.instant import Instant
from ._time.system_time import SystemTime

from ._io.read import Read, BufRead
from ._io.write import Write
from ._io.buffered import BufReader, BufWriter
from ._io.cursor import Cursor, SeekFrom

from .fs.path import Path, PathBuf
from .fs.file import OpenOptions, File

from .net.address import Ipv4Addr, Ipv6Addr, IpAddr, SocketAddr
from .net.tcp import TcpStream, TcpListener
from .net.udp import UdpSocket

from .process.command import Command
from .process.child import Child, Stdio
from .process.output import ExitStatus, Output, ExitCode

from .async_.future import Future, Poll, Waker, JoinHandle, Stream, spawn

from .macros.assertions import assert_eq, assert_ne
from .macros.debugging import dbg_, dbg, format_
from .macros.panic import panic, todo, unimplemented, ScopeGuard, defer

from .other import Ordering, ControlFlow, Reverse, Wrapping, Saturating, NonZero

from .filter import Filter, FilterError
from .regex import Regex, RegexError, RegexMatch

from .derive import (
    derive as derive_, DeriveError, memoize, pure,
    LintError, LintLevel,
    lint_warn, lint_allow, lint_deny, lint_forbid,
)

from .decor import (
    masterclass, MasterMethod, is_master, mastermethod,
    TestResult, test, bench, tests, run_tests,
)

from .logging import (
    Logger, LogLevel, LogRecord, MemorySink, console_sink,
    log_trace, log_debug, log_info, log_warn, log_error,
    println, print_, eprintln, eprint_,
)

from .help import Help
