# oxide

A comprehensive Rust-inspired type system and utility library for Python.

`oxide` brings Rust's powerful abstractions — algebraic types, ownership semantics, trait protocols, concurrency primitives, and more — to Python, giving you expressive, type-safe patterns without leaving the Python ecosystem.

## Installation

```bash
pip install oxide
```

Or copy the `oxide/` directory into your project.

## Quick Start

```python
from oxide import Option, Some, None_, Result, Ok, Err

def divide(a: float, b: float) -> Result[float, str]:
    if b == 0:
        return Err("division by zero")
    return Ok(a / b)

result = divide(10, 3)
match result:
    case Ok(value):
        print(f"Result: {value}")
    case Err(msg):
        print(f"Error: {msg}")
```

## Import Styles

```python
# Import everything
from oxide import *

# Import specific types
from oxide import Option, Some, Vec, HashMap, Duration, Path

# Import from submodules
from oxide.core.option import Some
from oxide.collections.vec import Vec
from oxide.sync.mutex import Mutex

# Use the prelude for a curated set of common types
from oxide.prelude import *
```

## Module Overview

### `oxide.core` — Foundational Types

| Module | Contents |
|--------|----------|
| `option` | `Option`, `Some`, `None_` — nullable value abstraction |
| `result` | `Result`, `Ok`, `Err` — error handling with `?` propagation |
| `enum` | `Enum`, `Variant`, `match` — tagged unions and pattern matching |
| `traits` | `CloneTrait`, `DebugTrait`, `DisplayTrait`, `FromTrait`, `IntoTrait`, and 13 more trait protocols with helper functions |
| `convert` | `Range`, `RangeInclusive`, `RangeFrom`, and other range types |
| `error` | `Error`, `Backtrace`, `Location`, `context` — error chaining infrastructure |

### `oxide.collections` — Data Structures

| Module | Contents |
|--------|----------|
| `vec` | `Vec` — growable array |
| `hashmap` | `HashMap` with `Entry` API |
| `hashset` | `HashSet` |
| `btreemap` | `BTreeMap` — ordered map |
| `btreeset` | `BTreeSet` — ordered set |
| `vecdeque` | `VecDeque` — double-ended queue |
| `binary_heap` | `BinaryHeap` — priority queue |
| `linked_list` | `LinkedList` |
| `extra` | `Drain`, `IntoIter`, `Slice` |

### `oxide.iter` — Iterator Adapters

| Module | Contents |
|--------|----------|
| `iterator` | `Iter`, `PeekableIter` |
| `adapters` | `Enumerate`, `Zip`, `Map`, `Filter`, `FilterMap`, `FlatMap`, `Flatten`, `Peekable`, `Fuse`, `Chain`, `Cycle`, `Take`, `Skip`, `Rev`, `Inspect`, `Copied`, `Cloned`, `Partition` |
| `consumers` | `collect`, `fold`, `for_each`, `count`, `sum`, `min`, `max`, `any`, `all`, `find`, `position` |

### `oxide.memory` — Ownership and Interior Mutability

| Module | Contents |
|--------|----------|
| `box` | `Box` — heap-allocated value |
| `rc` | `Rc`, `Weak` — reference-counted shared ownership |
| `arc` | `Arc` — atomic reference-counted shared ownership |
| `cell` | `Cell` — interior mutability (Copy types) |
| `refcell` | `RefCell`, `Ref`, `RefMut` — runtime borrow checking |
| `oncecell` | `OnceCell` — one-time initialization |
| `lazy` | `Lazy` — deferred computation |
| `cow` | `Cow` — copy-on-write |
| `pin` | `Pin`, `ManuallyDrop`, `MaybeUninit`, `NonNull`, `PhantomData`, `Borrow`, `BorrowMut` |

### `oxide.sync` — Concurrency Primitives

| Module | Contents |
|--------|----------|
| `atomic` | `Atomic`, `AtomicBool`, `AtomicInt` |
| `mutex` | `Mutex`, `MutexGuard` |
| `rwlock` | `RwLock`, `RwLockReadGuard`, `RwLockWriteGuard` |
| `barrier` | `Barrier` |
| `condvar` | `Condvar` |
| `channel` | `Channel`, `Sender`, `Receiver` — MPSC channels |
| `once` | `Once` — one-time execution |
| `semaphore` | `Semaphore` |

### `oxide.time` — Time Utilities

| Module | Contents |
|--------|----------|
| `duration` | `Duration`, `UNIX_EPOCH`, `Elapsed` |
| `instant` | `Instant` — monotonic timestamps |
| `system_time` | `SystemTime` — wall-clock time |

### `oxide.io` — I/O Abstractions

| Module | Contents |
|--------|----------|
| `read` | `Read`, `BufRead` traits |
| `write` | `Write` trait |
| `buffered` | `BufReader`, `BufWriter` |
| `cursor` | `Cursor` — in-memory I/O, `SeekFrom` |

### `oxide.fs` — Filesystem Operations

| Module | Contents |
|--------|----------|
| `path` | `Path`, `PathBuf` |
| `file` | `File`, `OpenOptions` |
| `metadata` | `Metadata`, `Permissions`, `FileType`, `DirEntry`, `ReadDir` |

### `oxide.net` — Networking

| Module | Contents |
|--------|----------|
| `address` | `Ipv4Addr`, `Ipv6Addr`, `IpAddr`, `SocketAddr`, `Shutdown` |
| `tcp` | `TcpStream`, `TcpListener` |
| `udp` | `UdpSocket` |

### `oxide.process` — Process Management

| Module | Contents |
|--------|----------|
| `command` | `Command` — spawn processes |
| `child` | `Child`, `Stdio` |
| `output` | `ExitStatus`, `Output`, `ExitCode`, `args`, `env`, `current_dir`, `current_exe`, `home_dir`, `temp_dir` |

### `oxide.async_` — Async Primitives

| Module | Contents |
|--------|----------|
| `future` | `Future`, `Poll`, `Waker`, `JoinHandle`, `Stream`, `spawn`, `join_all` |

### `oxide.macros` — Utility Macros

| Module | Contents |
|--------|----------|
| `assertions` | `assert_eq`, `assert_ne`, `debug_assert`, `debug_assert_eq`, `debug_assert_ne` |
| `debugging` | `dbg`, `format_`, `write_`, `writeln_`, `cfg`, `matches`, `option_env`, `include_str`, `include_bytes` |
| `panic` | `panic`, `todo`, `unimplemented`, `ScopeGuard`, `defer` |

### `oxide.other` — Miscellaneous Types

`Ordering`, `ControlFlow`, `Reverse`, `Wrapping`, `Saturating`, `NonZero`, `SmallVec`, `ArrayVec`, `TinyVec`, `BitVec`, `CreateMeta`

## Examples

### Option & Pattern Matching

```python
from oxide import Option, Some, None_, match, _

def find_user(id: int) -> Option[str]:
    users = {1: "Alice", 2: "Bob"}
    if id in users:
        return Some(users[id])
    return None_

user = find_user(1)
result = match(user, {
    Some(name): f"Found: {name}",
    None_:      "User not found",
})
print(result)  # "Found: Alice"
```

### Result & Error Handling

```python
from oxide import Result, Ok, Err, context

def parse_int(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"invalid integer: {s}")

def parse_and_double(s: str) -> Result[int, str]:
    return parse_int(s).map(lambda x: x * 2)

print(parse_and_double("5"))   # Ok(10)
print(parse_and_double("abc")) # Err("invalid integer: abc")
```

### Collections

```python
from oxide import Vec, HashMap, HashSet

v = Vec([1, 2, 3, 4, 5])
v.push(6)
print(v)  # Vec([1, 2, 3, 4, 5, 6])

m = HashMap()
m.insert("name", "Alice")
m.insert("age", "30")
print(m.get("name"))  # Some("Alice")

s = HashSet.from_iter([1, 2, 2, 3, 3])
print(list(s))  # [1, 2, 3]
```

### Concurrency

```python
from oxide import Mutex, Channel, spawn
import threading

counter = Mutex(0)

def increment():
    with counter:
        counter._value += 1

threads = [threading.Thread(target=increment) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(counter._value)  # 10
```

### Filesystem

```python
from oxide import Path

p = Path("/tmp/data")
p.create_dir_all()
(p / "file.txt").write_str("hello world")
print((p / "file.txt").read_to_string())  # "hello world"
```

### Networking

```python
from oxide import TcpListener, TcpStream, SocketAddr, Ipv4Addr

addr = SocketAddr.new_v4(Ipv4Addr(127, 0, 0, 1), 8080)
listener = TcpListener.bind(addr)
conn, peer = listener.accept()
conn.write(b"hello")
```

## API Reference

For complete documentation of every class, function, and type, see [docs/API.md](docs/API.md).

## Philosophy

`oxide` does not attempt to replicate Rust's compiler guarantees in Python — that's impossible without changing the language. Instead, it provides **idiomatic Python wrappers** around Rust's core patterns:

- **Option/Result** for explicit null and error handling
- **Enum/Variant** for tagged unions with pattern matching
- **Traits** as Python protocols for duck-typed polymorphism
- **Ownership types** (Box, Rc, Arc) for clear resource semantics
- **Sync primitives** for safe concurrent programming
- **Iterator adapters** for functional data processing

Use `oxide` to write more expressive, maintainable Python code that clearly communicates intent.

## License

MIT
