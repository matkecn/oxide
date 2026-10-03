<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/logo.svg">
    <img alt="oxide" src="assets/logo.svg" width="380">
  </picture>
</p>

<p align="center">
  <b>Rust-inspired types and utilities for Python — without the compiler.</b><br>
  <sub>Algebraic data types · linear-time regex · runtime-checked ownership · channels, locks &amp; async primitives · PHP-style validation · zero dependencies</sub>
</p>

<p align="center">
  <a href="https://github.com/matkecn/oxide"><img alt="GitHub" src="https://img.shields.io/badge/github-matkecn%2Foxide-181717?logo=github&logoColor=white"></a>
  <img alt="Python versions" src="https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white">
  <img alt="Dependencies" src="https://img.shields.io/badge/dependencies-0-success">
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/matkecn/oxide"></a>
</p>

---

**oxide** is a pure-Python library that ports the parts of the Rust standard library
that make Rust programs hard to get wrong: `Option`/`Result`, pattern matching,
ownership wrappers (`Box`, `Rc`, `Arc`), interior mutability (`Cell`, `RefCell`),
collections with predictable semantics, iterator adapters, concurrency primitives,
time and filesystem types, plus five batteries-included higher-level packages —
a **linear-time regular expression engine**, a **PHP `filter_var()`-style
validator**, a **structured logger** with console and stream helpers, a
**`#[derive]`-style decorator toolkit**, and a **self-documenting `Help` index**
that introspects the whole library.

Nothing here is compiled, there are no runtime dependencies, and nothing shadows
the standard library unless you explicitly ask for it.

```python
from oxide import Option, Some, None_, Ok, Err, Result, match, _, Vec, Regex, Filter

def half(n: int) -> Option[int]:
    return None_ if n % 2 else Some(n // 2)

def parse_port(raw: str) -> Result[int, str]:
    match = Filter.validate(raw, Filter.INT)
    return match.map(lambda v: v) if match.is_ok() else Err("port must be an integer")

print(half(10), half(7))          # Some(5) None_
print(parse_port("8080"))         # Ok(value=8080)
print(parse_port("http"))         # Err(error=FilterError('int', 'an integer'))
```

---

## Contents

- [Why oxide](#why-oxide)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Import styles and naming](#import-styles-and-naming)
- [Package map](#package-map)
- [Core types](#core-types)
  - [Option](#option)
  - [Result](#result)
  - [match and Match](#match-and-match)
  - [Enum and Variant](#enum-and-variant)
  - [Traits](#traits)
  - [Errors and backtraces](#errors-and-backtraces)
  - [Ranges](#ranges)
- [Collections](#collections)
- [Iterators](#iterators)
- [Memory and ownership](#memory-and-ownership)
- [Concurrency](#concurrency)
- [Time](#time)
- [I/O](#io)
- [Filesystem](#filesystem)
- [Networking](#networking)
- [Process](#process)
- [Async](#async)
- [Macros](#macros)
- [Miscellaneous types](#miscellaneous-types)
- [Regular expressions](#regular-expressions)
  - [Complexity and guarantees](#complexity-and-guarantees)
  - [Supported syntax](#supported-syntax)
  - [Rejected syntax](#rejected-syntax)
  - [Flags](#flags)
  - [The match object](#the-match-object)
  - [Replacement templates](#replacement-templates)
- [Validation and sanitization](#validation-and-sanitization)
  - [Validators](#validators)
  - [Sanitizers](#sanitizers)
  - [Flags and options](#flags-and-options)
  - [Custom filters](#custom-filters)
- [Logging](#logging)
  - [Levels](#levels)
  - [Loggers and sinks](#loggers-and-sinks)
  - [Console and streams](#console-and-streams)
- [Derive and lints](#derive-and-lints)
  - [Supported derives](#supported-derives)
  - [Attribute macros](#attribute-macros)
  - [Lints](#lints)
- [Decorators](#decorators)
  - [Item attributes](#item-attributes)
  - [Test attributes](#test-attributes)
  - [masterclass](#masterclass)
- [Help](#help)
- [Real-world recipes](#real-world-recipes)
- [Performance notes](#performance-notes)
- [Known gaps](#known-gaps)
- [Project layout](#project-layout)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

---

## Why oxide

Python gives you `None` and exceptions, and leaves the rest to discipline. oxide
fills in the vocabulary that Rust made mainstream, and keeps it Pythonic:

| Rust | oxide | What you get |
| --- | --- | --- |
| `Option<T>` | `Option`, `Some`, `None_` | "this may be absent" as a value, not a sentinel |
| `Result<T, E>` | `Result`, `Ok`, `Err` | recoverable errors that compose with `map`/`and_then` |
| `match` | `match(value).case(...)` | ordered dispatch with predicates, guards, ranges, types |
| `enum` | `Enum`, `Variant` | tagged unions declared as class attributes |
| `Box`/`Rc`/`Arc` | `Box`, `Rc`, `Weak`, `Arc` | explicit ownership and shared ownership |
| `Cell`/`RefCell` | `Cell`, `RefCell`, `Ref`, `RefMut` | interior mutability with runtime borrow checks |
| `OnceCell`/`Lazy` | `OnceCell`, `Lazy` | thread-safe one-time initialization |
| `Mutex`/`RwLock`/`Channel` | same names | poisoning, poisoning-free locks, MPSC channels |
| `std::time` | `Duration`, `Instant`, `SystemTime` | checked and saturating arithmetic |
| `regex` crate | `oxide.regex` | same accepted language, **without catastrophic backtracking** |
| PHP `filter_var` | `oxide.filter` | 19 validators, 9 sanitizers, extensible registry |
| `log` / `tracing` | `oxide.logging` | `LogLevel`, `Logger`, sinks, `println!`-style console output |
| `#[derive(...)]` | `oxide.derive` | generate `Debug`/`Clone`/`Default`/… and declare lints |
| `rustdoc` | `oxide.help` | query every exported symbol by name at runtime |

### What oxide is not

- It is not a transpiler and it does not give you Rust's compile-time guarantees.
- It does not replace the standard library. `str`, `dict`, and `list` are still
  the right tools for most code; oxide is for the code where their semantics get
  in the way.
- It does not monkey-patch anything. `import oxide` adds no names to builtins.

---

## Installation

oxide is a pure-Python package with no dependencies. Install it from PyPI, from
GitHub, or from a local checkout:

```bash
# from PyPI
pip install oxide

# from GitHub
pip install git+https://github.com/matkecn/oxide.git

# from a local clone
git clone https://github.com/matkecn/oxide.git
pip install ./oxide
```

There is nothing to compile and no dependency to resolve. You can also vendor
the package: `oxide/` is a single self-contained directory, so dropping it into
your project root (or anywhere on `sys.path`) is enough.

**Requirements:** Python 3.10 or newer. The package uses `match` statements and
`X | Y` type syntax, and ships a `py.typed` marker so type checkers use its
inline annotations.

---

## Quick start

```python
from oxide import (
    Some, None_, Option, Ok, Err, Result,   # algebra
    match, _, Enum, Variant,                # pattern matching
    Vec, HashMap, HashSet, BTreeMap,        # collections
    Iter,                                  # iterator adapters
    Box, Rc, Arc, Cell, RefCell, OnceCell,  # ownership & interior mutability
    Mutex, RwLock, Channel, Semaphore,      # concurrency
    Duration, Instant, SystemTime,          # time
    Path, File, OpenOptions,                # filesystem
    SocketAddr, Ipv4Addr, TcpStream,        # networking
    Command, ExitStatus,                   # processes
    spawn, join_all, Stream, Future,        # async
    assert_eq, dbg, panic, defer,           # macros
    Regex, IGNORECASE, Filter,              # batteries included
)

# 1. Absence is a value
port = Some(8080)
print(port.map(lambda p: p + 1))       # Some(8081)
print(None_.unwrap_or(80))              # 80

# 2. Errors compose
def parse(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"not an integer: {s!r}")

print(parse("41").map(lambda n: n + 1))       # Ok(value=42)
print(parse("x").unwrap_or(-1))               # -1

# 3. No catastrophic backtracking
email = Regex(r"([a-z]+)@([a-z]+\.[a-z]+)", IGNORECASE)
print(email.search("Ann@Example.com").groups())
# ('Ann', 'Example.com')

# 4. Validation with a typed error
print(Filter.validate("a@b.com", Filter.EMAIL))
# Ok(value='a@b.com')
```

---

## Import styles and naming

```python
# Everything re-exported at the top level (298 names)
from oxide import *
from oxide import Option, Vec, HashMap, Mutex, Path, Regex, Filter

# Curated subset: the names you want in almost every file
from oxide.prelude import *

# Regular expressions live in their own namespace, as functions
from oxide import regex
regex.sub(r"\d+", "N", "a1b22")                 # 'aNbN'
regex.findall(r"\d+", "a1b22")                  # ['1', '22']

# Deep submodule paths (the underscore names are the internal layout)
from oxide.core.option import Some
from oxide._collections.vec import Vec
from oxide.sync.mutex import Mutex
from oxide.derive import derive
from oxide.logging import Logger
from oxide.help import Help
```

### Deliberate name collisions

Rust has no equivalents for these clashes, so oxide renames one side of each:

| You want | Import it as | Why |
| --- | --- | --- |
| The PHP-style validator class | `Filter` | it is the headline API of `oxide.filter` |
| The iterator `filter` adapter | `FilterIter` | frees `Filter` for the validator |
| A regex match object | `RegexMatch` | frees `Match` for the enum `match` builder |
| The regex functions | `oxide.regex.sub`, … | keeps `oxide.match` unambiguous |
| The derive decorator | `derive_` | keeps `oxide.derive` naming the subpackage |
| Lint levels (`warn`, `deny`, …) | `lint_warn`, `lint_deny`, … | `warn` stays with `oxide.core.traits` |
| Logging levels (`info`, `debug`) | `log_info`, `log_debug`, … | `info` stays with `oxide.core.traits` |
| The `cfg` compile-time macro | `oxide.derive.cfg` | avoids shadowing `oxide.macros.cfg` |

`RegexMatch` is the same object as `regex.Match`; it is exported under both names.
It is a *different class* from the top-level `Match`, which is the enum
`match(...)` builder — `Match.__module__` is `oxide.core.enum`, while
`RegexMatch.__module__` is `oxide.regex.api`.
Because `filter` would shadow the builtin of the same name under `import *`, the
`filter` submodule is reachable as an attribute (`from oxide import filter`) but is
deliberately left out of `__all__`.

---

## Package map

| Package | Highlights |
| --- | --- |
| `oxide.core` | `Option`, `Result`, `match`, `Enum`, traits, ranges, `Error` |
| `oxide` (collections) | `Vec`, `HashMap`, `HashSet`, `BTreeMap`, `BTreeSet`, `VecDeque`, `BinaryHeap`, `LinkedList`, `Slice`, entry API |
| `oxide.iter` | `Iter` plus 19 adapters (`Map`, `FilterIter`, `Chain`, `Peekable`, …) |
| `oxide.memory` | `Box`, `Rc`/`Weak`, `Arc`, `Cell`, `RefCell`, `OnceCell`, `Lazy`, `Cow`, `Pin`, `MaybeUninit` |
| `oxide.sync` | `Mutex`, `RwLock`, `Barrier`, `Condvar`, `Channel`, `Once`, `Semaphore`, atomics |
| `oxide` (time) | `Duration`, `Instant`, `SystemTime`, `Elapsed` |
| `oxide` (io) | `Read`/`BufRead`/`Write` protocols, `BufReader`, `BufWriter`, `Cursor`, `SeekFrom` |
| `oxide.fs` | `Path`, `PathBuf`, `File`, `OpenOptions`, `Metadata`, `Permissions`, `DirEntry` |
| `oxide.net` | `Ipv4Addr`, `Ipv6Addr`, `IpAddr`, `SocketAddr`, `TcpStream`, `TcpListener`, `UdpSocket` |
| `oxide.process` | `Command`, `Child`, `Stdio`, `ExitStatus`, `Output`, `ExitCode` |
| `oxide.async_` | `Future`, `Poll`, `Waker`, `JoinHandle`, `Stream`, `spawn`, `join_all` |
| `oxide.macros` | assertions, `dbg`, `format_`, `panic`, `todo`, `ScopeGuard`, `defer` |
| `oxide.other` | `Ordering`, `ControlFlow`, `Wrapping`, `Saturating`, `NonZero`, `SmallVec`, `ArrayVec`, `BitVec` |
| `oxide.regex` | `Regex`, `RegexMatch`, `compile`, `search`, `findall`, `sub`, `escape`, flags |
| `oxide.filter` | `Filter`, `FilterError` — all operations live on the `Filter` class |
| `oxide.logging` | `Logger`, `LogLevel`, `LogRecord`, `MemorySink`, `console_sink`, `println`, `stdin`/`stdout`/`stderr` |
| `oxide.derive` | `derive_`, `memoize`, `pure`, `lint_warn`/`allow`/`deny`/`forbid`, lint scopes |
| `oxide.help` | `Help` — the self-documenting index of every exported symbol |

`docs/API.md` documents every class and function, argument by argument.

---

## Core types

### Option

`Option` is `Some(value)` or `None_`. It is a closed enum, so a missing value can
never be confused with a valid one.

```python
from oxide import Option, Some, None_

def find_user(user_id: int) -> Option[str]:
    users = {1: "Alice", 2: "Bob"}
    return Some(users[user_id]) if user_id in users else None_

user = find_user(1)

user.is_some()                              # True
user.map(lambda name: name.upper())        # Some('ALICE')
user.filter(lambda name: len(name) > 3)    # Some('Alice')
user.and_then(lambda name: Some(len(name)))# Some(5)
user.or_else(lambda: "anonymous")          # Some('Alice')
user.unwrap_or("anonymous")                # 'Alice'
user.expect("user table is never empty")   # 'Alice'  (panics on None_)

None_.unwrap_or("anonymous")               # 'anonymous'
None_.map_or(0, len)                       # 0

# Both `expect` methods raise `RuntimeError`, not a custom error type:
#   Option.expect -> RuntimeError('boom')
#   Result.expect -> RuntimeError("boom: 'the error'")
```

`Option` combinators, in full:

| Method | Behaviour |
| --- | --- |
| `is_some()` / `is_none()` | presence test |
| `unwrap()` / `unwrap_or(x)` / `unwrap_or_else(fn)` / `expect(msg)` | extract or fail |
| `map(fn)` | transform the value, keep `None_` |
| `map_or(default, fn)` / `map_or_else(default_fn, fn)` | transform with a fallback |
| `filter(pred)` | `Some` → `None_` when the predicate fails |
| `and_then(fn)` | chain fallible transformations |
| `and_(other)` | `Some(a)` → `other`, `None_` → `None_` |
| `or_(other)` / `or_else(fn)` | keep the first value or take a fallback |
| `inspect(fn)` | side-effect on the value without consuming it |

### Result

`Result` is `Ok(value)` or `Err(error)`. Unlike `Option`, the error is a value you
can keep, inspect, and convert.

```python
from oxide import Result, Ok, Err, Filter, ask, propagate, PropagateError

def parse_port(raw: str) -> Result[int, str]:
    value = Filter.validate(raw, Filter.INT)
    if value.is_err():
        return Err("port must be an integer")
    port = value.unwrap()
    return Ok(port) if 1 <= port <= 65535 else Err(f"port out of range: {port}")

parse_port("8080")            # Ok(value=8080)
parse_port("99999")           # Err(error='port out of range: 99999')
parse_port("nope")            # Err(error='port must be an integer')

# Transformations never discard the error path
parse_port("8080").map(lambda p: p + 1)     # Ok(value=8081)
parse_port("nope").map(lambda p: p + 1)     # Err(error='port must be an integer')
parse_port("nope").map_err(str.upper)       # Err(error='PORT MUST BE AN INTEGER')
parse_port("nope").unwrap_or(80)            # 80
parse_port("nope").ok()                     # None_
parse_port("8080").ok()                     # Some(8080)

# `?` for functions that can fail
def handler(raw: str) -> Result[int, str]:
    port = parse_port(raw).and_then(
        lambda p: Ok(p * 2) if p else Err("zero")
    )
    return port.map_err(lambda e: f"[config] {e}")

handler("0")                 # Err(error='[config] zero')
```

`ask()` unwraps inside a helper and lets `PropagateError` carry the failure to the
caller:

```python
def read_port(raw: str) -> int:
    return ask(parse_port(raw))          # unwraps Ok, raises PropagateError on Err
```

### match and Match

`match(value)` builds an ordered list of cases and evaluates the first that hits.
Handlers may be constants or callables, and every `case_*` builder accepts a
`guard=` predicate. (`Match` lives in `oxide.core.enum`, next to `Enum`/`Variant`
— the builder and the tagged union share a module.)

```python
from oxide import match, _, Some, None_

# Constant handlers
match(Some("Alice")).case(Some(_), "found").otherwise("missing")   # 'found'
match(None_).case(Some(_), "found").otherwise("missing")          # 'missing'

# Callable handlers and guards
match("hi").case_type(str, lambda s: len(s)).execute()             # 2
match(5).case(5, "five", guard=lambda n: n % 2 == 1).otherwise("other")
match(9).case_range(1, 10, "single digit").otherwise("large")      # 'single digit'
match(5).case_pred(lambda n: n > 3, "big").otherwise("small")      # 'big'
match("b").case_in(["a", "b"], "letter").otherwise("symbol")       # 'letter'
match(3.5).case_type(int, "int").case_type(str, "str").otherwise("float")  # 'float'
```

| Builder | Matches when |
| --- | --- |
| `case(pattern, handler, guard=)` | `value == pattern`, or `isinstance(value, pattern)` for a type/tuple of types |
| `case_type(typ, handler)` | `isinstance(value, typ)` |
| `case_eq(expected, handler)` | `value == expected` |
| `case_range(start, end, handler)` | `start <= value < end` (half-open) |
| `case_in(collection, handler)` | `value in collection` |
| `case_pred(pred, handler)` | `pred(value)` is truthy |
| `otherwise(handler)` | fallback — required if no case hits |
| `execute()` | evaluate, raising `MatchError` when no case hits |

`Match` is single-use: `execute()` and `otherwise()` each consume it.

### Enum and Variant

Subclass `Enum` and declare variants as class attributes. Attribute access returns
a `Variant` with a `tag` and a `value`, and tuple attributes carry extra payloads.

```python
from oxide import Enum

class Status(Enum):
    OK = "ok"
    ERROR = "error", 500

Status.variants()             # ['OK', 'ERROR']
Status.OK.tag                 # 'OK'
Status.OK.value               # 'ok'
Status.ERROR.value            # 500
Status.is_valid("OK")         # True
Status.OK.is_("OK")           # True
Status.OK.map(lambda v: v.upper())   # OK('OK')
Status.OK.unwrap()            # 'ok'
```

Use `Variant(tag, value)` directly when you need a tagged union without declaring
a class.

### Traits

`oxide` exposes Rust's trait vocabulary as `typing.Protocol` classes plus
free functions, so you can require capabilities from values that do not inherit
anything.

```python
from oxide import (
    CloneTrait, DebugTrait, DisplayTrait, DefaultTrait, EqTrait, OrdTrait,
    Vec, Box,
    clone, debug, display, default_of, as_ref, deref, try_into,
)

isinstance([1, 2, 3], CloneTrait)      # True (protocol check, structural)
display(42)                            # '42'
debug(Vec([1]))                        # 'Vec([1])'
default_of(list)                       # []
clone(Vec([1, 2]))                     # Vec([1, 2])
as_ref(Box.new(5))                     # 5
try_into("42", int)                    # Ok(value=42)
```

| Trait | Helper | Note |
| --- | --- | --- |
| `CloneTrait` | `clone(value)` | deep copy for collections, shared for ref-counted types |
| `CopyTrait` | — | structural check only |
| `DebugTrait` / `DisplayTrait` | `debug(v)` / `display(v)` | two string flavours, like Rust |
| `DefaultTrait` | `default_of(cls)` | `default_of(list) == []` |
| `EqTrait` / `OrdTrait` | `eq`, `ne`, `cmp`, `lt`, `le`, `gt`, `ge` | ordering |
| `HashTrait` | — | structural |
| `FromTrait` / `IntoTrait` | `from_(cls, v)` / `into(cls, v)` | infallible conversion |
| `TryFromTrait` / `TryIntoTrait` | `try_from(cls, v)` / `try_into(cls, v)` | fallible conversion returning `Result` |
| `AsRefTrait` / `AsMutTrait` | `as_ref(v)` / `as_mut(v)` | borrow instead of move |
| `DerefTrait` / `DerefMutTrait` | `deref(v)` / `deref_mut(v)` | smart-pointer dereference |
| `DropTrait` | `drop(v)` | explicit destructor call |

### Errors and backtraces

```python
from oxide import Error, context

err = Error("could not open config file")
context("while loading /etc/app.toml", err).message()
# 'could not open config file'
context("while loading /etc/app.toml", err).context()
# 'while loading /etc/app.toml'
err.with_context("while retrying").context()
# 'while retrying'
err.backtrace()      # Backtrace; .frames() returns the captured frames
err.location()       # Location(file, line, column) or None
```

### Ranges

Rust-style range objects with `contains` and lazy `iter()`:

```python
from oxide import range_, range_inclusive, range_from, range_to, range_to_inclusive

range_(1, 4).iter()                    # [1, 2, 3]
range_inclusive(1, 4).iter()           # [1, 2, 3, 4]
range_from(1).iter(4)                  # [1, 2, 3]  (open end, explicit stop)
range_to(4).iter()                     # [0, 1, 2, 3]
range_(4, 1).is_empty()                # True
range_(1, 4).contains(3)               # True
range_(1, 4).contains_inclusive(4)     # True
```

---

## Collections

```python
from oxide import Vec, HashMap, HashSet, BTreeMap, BTreeSet, VecDeque, BinaryHeap, LinkedList, Slice

# Vec — growable array with explicit capacity control
v = Vec([3, 1, 2])
v.push(4)
v.len()                       # 4
v.get(0)                      # Some(3)
v.first()                     # Some(3)
v.last()                      # Some(4)
v.sort()                      # stable sort in place
v.to_list()                   # [1, 2, 3, 4]
Vec.repeat("ab", 3).to_list() # ['ab', 'ab', 'ab']
Vec.with_capacity(1024)       # preallocate

# HashMap — entry API for "get or insert"
m = HashMap.from_dict({"a": 1})
m.get("a")                    # Some(1)
m.get("missing")              # None_
m.remove("a")                 # Some(1)
m.or_insert("hits", 0)        # existing value, or insert and return it
m.insert("hits", 3)
m.keys(), m.values()          # list views
m.len_common(HashMap.from_dict({"hits": 0}))   # 1

counts = HashMap()
counts.entry("hits").or_insert_with(lambda: 0)  # {'hits': 0}

# HashSet — set algebra (operands are HashSets)
a, b = HashSet.from_iter([1, 2, 3]), HashSet.from_iter([3, 4])
list(a.union(b))                  # [1, 2, 3, 4]
list(a.intersection(b))           # [3]
list(a.difference(b))             # [1, 2]
list(a.symmetric_difference(b))   # [1, 2, 4]
a.is_subset(b)                    # False
a.is_superset(b)                  # False
a.is_disjoint(b)                  # False

# BTreeMap / BTreeSet — ordered, range-queryable
tree = BTreeMap.from_dict({"b": 2, "a": 1, "c": 3})
tree.keys()                        # ['a', 'b', 'c']
list(tree.range_("a", "c"))        # [('a', 1), ('b', 2)]
list(BTreeSet.from_iter([3, 1, 2]).range_(1, 3))   # [1, 2]

# Double-ended, heap, linked list
d = VecDeque([1, 2])
d.push_back(3); d.push_front(0)
list(d)                            # [0, 1, 2, 3]
d.rotate_left(1); list(d)          # [1, 2, 3, 0]

heap = BinaryHeap()
[heap.push(x) for x in (3, 9, 4)]
heap.peek()                        # 9
heap.pop()                         # 9

ll = LinkedList([1, 2])
ll.push_back(3)
(ll.front(), ll.back())            # (1, 3)
list(ll.iter_rev())                # [3, 2, 1]

# Slice — a window over a list
s = Slice.from_list([1, 2, 3])
left, right = s.split_at(1)
left.to_list(), right.to_list()    # ([1], [2, 3])
```

---

## Iterators

`Iter` wraps any iterable and gives you Rust's lazy adapter chain. Adapters are
lazy; the `collect`-family methods consume.

```python
from oxide import Iter, range_

Iter([1, 2, 3, 4]).filter(lambda n: n % 2 == 0).collect()   # [2, 4]
Iter([1, 2, 3]).map(lambda n: n * 2).collect()               # [2, 4, 6]
Iter([[1, 2], [3]]).flatten().collect()                      # [1, 2, 3]
Iter([1, 2]).flat_map(lambda n: [n, n]).collect()            # [1, 1, 2, 2]
Iter([1, 2, 3]).filter_map(lambda n: (n * 10 if n > 1 else None)).collect()  # [20, 30]
Iter(range_(1, 5)).sum()                                      # 10
Iter(range_(1, 5)).fold(1, lambda acc, n: acc * n)            # 24
Iter([1, 2, 3]).count()                                       # 3
Iter([3, 1, 2]).min(), Iter([3, 1, 2]).max()                  # (1, 3)
Iter([1, 2, 3]).nth(1)                                        # 2
Iter([1, 2, 3]).last()                                        # 3
Iter([1, 2, 3]).any(lambda n: n > 2), Iter([1]).all(lambda n: n > 0)  # (True, True)
Iter([1, 2, 3]).position(lambda n: n == 2)                    # 1

# multi-iterable adapters
Iter.chain_of([1, 2], [3], [4, 5]).collect()  # [1, 2, 3, 4, 5]
Iter([1, 2]).chain([3, 4]).collect()            # [1, 2, 3, 4]
Iter([1, 2]).zip([10, 20]).collect()             # [(1, 10), (2, 20)]
Iter([1, 2]).zip_with([10, 20], lambda a, b: a + b).collect()  # [11, 22]
Iter("ab").enumerate().collect()              # [(0, 'a'), (1, 'b')]
Iter([1, 2, 3, 4]).step_by(2).collect()       # [1, 3]
Iter([1, 2, 3]).skip(1).collect()             # [2, 3]
Iter([1, 2, 3]).take(2).collect()             # [1, 2]

# lookahead and safety
it = Iter([1, 2]).peekable()
it.peek()                                     # 1
it.next()                                     # 1

# partition returns two ready-made lists, not adapters
even, odd = Iter([1, 2, 3, 4]).partition(lambda n: n % 2 == 0)
even, odd                            # ([2, 4], [1, 3])

# lazy side effects
Iter(range_(1, 4)).inspect(lambda n: print("saw", n)).collect()
```

Adapters available as standalone classes/constructors: `Map`, `FilterIter`,
`FilterMap`, `FlatMap`, `Flatten`, `Enumerate`, `Zip`, `Chain`, `Cycle`, `Take`,
`Skip`, `Rev`, `Inspect`, `Copied`, `Cloned`, `Partition`, `Peekable`, `PeekMut`,
`Fuse`.

> `Iter.from_fn`, `Iter.repeat(iterable)`, `Iter.range(start, step)`,
> `Iter.chain_of(...)` and `Iter.zip_of(a, b)` are **classmethods** — call them on
> `Iter`, not on an instance. `repeat` cycles its argument **forever**, so always
> bound it with `take(...)`/`skip(...)`. `Iter.rev()` does not exist; use
> `oxide.iter.rev(iterable)` or `iterable[::-1]`.
>
> `chain` and `zip` are the *instance* adapters (`it.chain(other)`,
> `it.zip(other)`); the multi-argument constructors are `chain_of` and `zip_of`.
> `count` is Rust's consuming method (how many items remain), so the infinite
> counter is `range`.

> **Chains are single-use.** Terminal calls (`collect`, `count`, `sum`, `max`,
> `min`, `for_each`, …) drain the underlying iterator, so a second call on the same
> chain sees nothing: `Iter([1, 2, 3]).map(...).count()` followed by `.max()`
> returns `None`. Reuse requires rebuilding the chain from a re-iterable source,
> or `collect()`-ing once into a list. `partition` is the exception — it returns
> two ready-made lists.

---

## Memory and ownership

```python
from oxide import (
    Box, Rc, Weak, Arc, Cell, RefCell, OnceCell, Lazy,
    Cow, CowBorrowed, CowOwned,
)

# Box — explicit heap allocation, moves the value behind a pointer
b = Box.new([1, 2, 3])
b.as_ref()                    # [1, 2, 3]
b.into_inner()                # [1, 2, 3]

# Rc / Weak — shared, non-atomic ownership with weak references
shared = Rc.new({"hits": 0})
alias = shared.clone()
Rc.strong_count(shared)       # 2
weak = shared.downgrade()
weak.is_alive()               # True
weak.upgrade()                # Rc(...)
shared.try_unwrap()           # {'hits': 0} when unique; raises while aliases exist

# Arc — shared ownership across threads
config = Arc.new({"retries": 3})
config.clone().strong_count() # 2
config.make_mut()             # clone-on-write; returns a mutable handle

# Cell — interior mutability for Copy-style values
flag = Cell(0)
flag.set(1)
flag.replace(2)
flag.get()                    # 2

# RefCell — interior mutability with runtime borrow checks
cell = RefCell([1, 2])
with cell.borrow_mut() as mutable:
    mutable.value.append(3)
cell.borrow().value           # [1, 2, 3]
cell.try_borrow()             # Ref([1, 2, 3]) directly — raises while mutably borrowed

# OnceCell — write once, read many, thread safe
once = OnceCell.new()
once.get()                    # None before initialisation
once.get_or_init(lambda: {"config": "loaded"})
once.get()                    # {'config': 'loaded'}
once.is_initialized()         # True

# Lazy — compute on first access, cache forever
expensive = Lazy.new(lambda: sum(range(1000)))
expensive.force()             # 499500
expensive.is_forced()         # True

# Cow — shared value that only clones when ownership changes
shared_list = [1, 2, 3]
cow = CowBorrowed(shared_list)   # repr: _CowBorrowed(_data=[1, 2, 3])
cow.is_borrowed()               # True
cow.as_ref()                    # [1, 2, 3] — no copy
cow.into_owned()                # [1, 2, 3] — a detached copy, cow is unchanged
CowOwned([1, 2, 3]).is_owned()  # True
```

`Cow` has no public constructor of its own — use `CowBorrowed(value)` for a
value you do not want copied, or `CowOwned(value)` when you already hold a
detached copy. `map()` returns a new `Cow` of the *same* variant, `as_ref()`
never copies, and `into_owned()`/`to_owned()` always hand back a standalone
object without changing the original's borrowed/owned state.

---

## Concurrency

```python
import threading
from oxide import (
    Mutex, RwLock, AtomicInt, AtomicBool, Channel, Semaphore, Barrier, Once,
)

# Mutex — poisoning is tracked, guards are context managers
counter = Mutex(0)

def bump():
    with counter as guard:            # `with mutex.lock():` is not supported
        guard.replace(guard.value + 1)

threads = [threading.Thread(target=bump) for _ in range(4)]
[t.start() for t in threads]
[t.join() for t in threads]
counter.into_inner()                 # 4
counter.is_poisoned()                # False

# RwLock — many readers, one writer
cache = RwLock({"a": 1})
with cache.write() as guard:
    guard.replace({"a": 2})
with cache.read() as guard:
    guard.value                      # {'a': 2}

# Atomics
hits = AtomicInt(0)
hits.fetch_add(1)
hits.load()                          # 1
flag = AtomicBool(False)
flag.compare_and_set(False, True)
flag.load()                          # True

# Channels — bounded sends never block: they return False when full
ch = Channel.bounded(4)
ch.send("job")                       # True
ch.receiver.is_empty()               # False
ch.receiver.try_recv()               # 'job'
ch.receiver.try_recv()               # None once drained
ch.sender.close()                    # closes the send half
ch.sender.is_closed()                # True
ch.send("late")                      # False — closed channels refuse writes
queue = Channel.unbounded()          # unbounded queue

# One-time initialisation across threads
once = Once()
once.call_once(lambda: print("ran exactly once"))
once.is_completed()                  # True

# Semaphore — bound concurrency
sem = Semaphore(4)
sem.available()                      # 4
sem.acquire(); sem.available()       # 3
sem.release(); sem.available()       # 4

# Barrier — rendezvous point; needs one thread per party or it blocks forever
gate = Barrier(2)
peers = [threading.Thread(target=gate.wait) for _ in range(2)]
[t.start() for t in peers]
[t.join() for t in peers]
```

---

## Time

```python
from oxide import Duration, Instant, SystemTime

Duration.from_secs(2)                # Duration(secs=2)
Duration.from_millis(1500).as_millis()  # 1500
Duration.from_minutes(2).as_secs()   # 120
Duration.from_hours(1).as_secs()     # 3600
Duration.from_micros(1500).as_micros()  # 1500
Duration.zero().is_zero()            # True
Duration.from_millis(1500).secs_f64()   # 1.5 — there is no as_secs_f64()

# checked / saturating arithmetic
Duration.from_secs(1) * 3             # Duration(secs=3)
Duration.from_secs(4).div(2)          # Duration(secs=2)  — use div(), not `/`
Duration.from_secs(2).mul(3)          # Duration(secs=6)
Duration.from_secs(2).saturating_add(Duration.from_secs(1))   # no overflow panic

# monotonic clock for measuring
start = Instant.now()
elapsed = start.elapsed()
elapsed.as_millis()                  # elapsed wall time
Instant.now().checked_duration_since(start)   # Duration, None if it would go negative

# wall clock for timestamps
now = SystemTime.now()
now.as_secs()                        # unix seconds
now.to_datetime()                    # datetime.datetime(...)
SystemTime.now().from_epoch().as_secs()   # Duration method — no arguments
SystemTime.from_secs(10).duration_since(SystemTime.from_secs(4))   # Duration(secs=6)
```

`UNIX_EPOCH` is exported from `oxide`, but it is a `Duration(0, 0)` sentinel, not a
`SystemTime`, so it cannot be passed to `SystemTime.duration_since`.

---

## I/O

oxide models I/O as three protocols — `Read`, `BufRead`, `Write` — so any object
that implements them can be wrapped in `BufReader`/`BufWriter`.

```python
from oxide import BufReader, BufWriter, Cursor, SeekFrom

# `Cursor` is a BufRead: wrap it to get the read_to_* helpers
cursor = Cursor(b"hello world")
BufReader(cursor).read_to_string()   # 'hello world'

buf = BufReader(Cursor(b"line one\nline two\n"))
list(buf.lines())                    # ['line one\n', 'line two\n']

out = Cursor(bytearray())
with BufWriter(out) as writer:
    writer.write_all(b"payload")
out.into_inner()                     # bytearray(b'payload')

cursor = Cursor(b"a,b,c")
cursor.read_until(ord(","))          # 2 (bytes consumed)
cursor.position()                    # 2
cursor.seek(SeekFrom.start(0))
```

`read()` follows the buffer protocol: `read(buf: bytearray) -> int` fills `buf`
and returns the byte count. `read_to_end()`/`read_to_string()` are provided by
`BufReader`, `File`, and `Path` — a bare `Cursor` only exposes `read`,
`read_line`, `read_until`, and `fill_buf`.

---

## Filesystem

```python
from oxide import Path, PathBuf, File, OpenOptions, Metadata

path = Path("/tmp/oxide-demo")
path.create_dir_all()

file = path / "notes.txt"
file.write_str("hello from oxide")
file.read_to_string()                # 'hello from oxide'
file.exists(), file.is_file()        # (True, True)
path.is_dir()                        # True

file.file_name(), file.file_stem(), file.extension()
# ('notes.txt', 'notes', 'txt')
file.parent()                        # Path('/tmp/oxide-demo')
file.with_extension("md")            # Path('/tmp/oxide-demo/notes.md')
Path("/a/./b/../c").normalize()      # Path('/a/c')

meta: Metadata = file.metadata()
meta.size(), meta.is_file()          # (15, True)
meta.modified(), meta.created()      # SystemTime (or None when unavailable)

[entry.file_name() for entry in path.read_dir()]   # ['notes.txt']

# explicit file handles
with File.create(path / "cfg.toml") as handle:
    handle.write_all("[server]\nport = 8080\n")
with File.open(path / "cfg.toml") as handle:       # read-only handle
    handle.seek_from_start(0)
    handle.read_to_string()

# fine-grained control: OpenOptions is a mutable builder, and opens the file
options = OpenOptions.new().write().create().truncate(True)
with options.open(path / "tmp.txt") as handle:
    handle.write_all("scratch")
```

`File.open(path)` only opens an existing file for reading; there is no
`File.open_options`. To combine flags and opening, build an `OpenOptions` and call
its `.open(path)`.

`PathBuf` is the growable form: `PathBuf.new()`, `.push("child")`, `.pop()`,
`.set_extension("md")`, `.into_string()`.

---

## Networking

```python
from oxide import (
    Ipv4Addr, Ipv6Addr, IpAddr, SocketAddr, TcpListener, TcpStream, UdpSocket,
)

addr = SocketAddr.new_v4(Ipv4Addr.localhost(), 8080)
Ipv4Addr(127, 0, 0, 1).is_loopback()          # True
Ipv4Addr(192, 168, 0, 1).is_private()         # True
Ipv4Addr.from_str("10.0.0.1").to_str()         # '10.0.0.1'
Ipv6Addr.from_str("::1").is_loopback()         # True
IpAddr.from_str("::1").is_ipv6()              # True
SocketAddr.from_str("127.0.0.1:9000").port()   # 9000

# echo server + client
import threading

listener = TcpListener.bind(SocketAddr.new_v4(Ipv4Addr.localhost(), 0))
port = listener.local_addr().port()

def serve():
    stream, peer = listener.accept()
    buf = bytearray(4)                # read() fills a buffer you supply
    count = stream.read(buf)
    stream.write_all(buf[:count])     # write_all takes bytes
    stream.shutdown()
    return peer

threading.Thread(target=serve, daemon=True).start()

client = TcpStream.connect(SocketAddr.new_v4(Ipv4Addr.localhost(), port))
client.write_all(b"ping")
buf = bytearray(4)
count = client.read(buf)
buf[:count]                          # bytearray(b'ping')
```

Like `Cursor`, `TcpStream.read(buf)` fills a caller-supplied `bytearray` and
returns the byte count — there is no `read(n)` overload.

---

## Process

```python
from oxide import Command, Stdio, ExitStatus, Output, env, current_dir, temp_dir, home_dir, args

output: Output = Command("echo").arg("hello").output()
output.status().success()           # True — `status` is a method on Output
output.stdout_str()                 # 'hello\n'
output.stderr_str()                 # ''

Command("false").status().success()      # False
Command("sh").args(["-c", "echo hi; echo err 1>&2; exit 3"]).status().code()   # 3

Command("sort").stdin(Stdio.piped()).spawn()     # Child; take_stdin()/take_stdout()
Command("sort").envs({"LC_ALL": "C"}).current_dir(temp_dir())
Command("sort").stderr(Stdio.null())             # discard stderr

env("HOME")                        # str or None
current_dir(), home_dir(), temp_dir(), args()
```

---

## Async

oxide's async layer is built on `asyncio` but presents a Rust-flavoured API:
`Future`/`Poll`/`Waker` for manual futures, `JoinHandle` for spawned tasks, and
`Stream` for async sequences.

```python
from oxide import spawn, join_all, Stream, Future, Poll, Waker

# spawn a coroutine and wait for it
async def work(n: int) -> int:
    return n * 2

spawn(work(21)).join()             # 42
spawn(work(21)).get_result()       # 42

# fan out and join everything
spawn(join_all([spawn(work(i)) for i in range(3)])).join()   # [0, 2, 4]

# manually completed futures
f = Future.pending()
f.set_result("done")
f.is_done(), f.result()            # (True, 'done')

g = Future.pending()
g.set_exception(RuntimeError("nope"))
g.exception()                      # RuntimeError('nope')

# streams: each adapter link is awaited, then consumed
async def pipeline():
    doubled = await Stream.from_iter([1, 2, 3]).map(lambda n: n * 2)
    return await doubled.collect()

spawn(pipeline()).join()           # [2, 4, 6]

async def counting():
    evens = await Stream.from_iter([1, 2, 3, 4]).filter(lambda n: n % 2 == 0)
    return await evens.count()

spawn(counting()).join()           # 2

awaitable = Stream.chain(Stream.from_iter([1]), Stream.from_iter([2]))
```

| Type | Purpose |
| --- | --- |
| `Future` | a value that completes later; `await` it, or resolve it with `set_result`/`set_exception` |
| `Poll` | `Poll.pending()` / `Poll.ready(value)` — the manual poll protocol |
| `Waker` | wake callback; `wake()`, `wake_by_ref()`, `clone_waker()`, `is_woken()` |
| `JoinHandle` | a spawned task: `join()`, `get_result()`, `is_finished()`, `abort()`, usable as a context manager |
| `Stream` | lazy async sequence: `from_iter`, `from_async_iter`, `once`, `repeat`, `empty`, `next`, `map`, `filter`, `take`, `chain`, `collect`, `fold`, `count`, `first`, `peek`, `for_each` |

---

## Macros

```python
from oxide import (
    assert_, assert_eq, assert_ne, debug_assert, debug_assert_eq, debug_assert_ne,
    dbg, format_, write_, writeln_, matches, cfg, option_env, include_str, include_bytes,
    panic, todo, unimplemented, ScopeGuard, defer,
)

assert_(True, "never runs")            # no-op
assert_eq(1 + 1, 2)
assert_ne("a", "b")
assert_eq(len("abc"), 3, "length mismatch")

debug_assert(True)                     # cheap checks; strip-able

dbg(1 + 1)                             # prints "1 @ file:line", returns 2
format_("{}-{}", "a", 1)               # 'a-1'
matches("abc", r"a.c")                 # True

cfg("MY_FLAG", default="off")          # 'off' unless set in the environment
option_env("HOME")                     # str or None
include_str("README.md"), include_bytes("README.md")
```

`panic`, `todo` and `unimplemented` raise immediately — `PanicError` and
`UnimplementedError` are exported from `oxide.macros`, not the top level — so
catch them when demonstrating:

```python
from oxide import panic, todo
from oxide.macros import PanicError, UnimplementedError

for call in (lambda: panic("unreachable"), lambda: todo("finish this")):
    try:
        call()
    except (PanicError, UnimplementedError) as exc:
        print(type(exc).__name__)
```

`assert_matches` and `assert_type` also exist, but are only exported from
`oxide.macros.assertions`. `panic_fmt`, `PanicError` and `UnimplementedError`
are likewise submodule-only (`oxide.macros`); the top level exports `panic`,
`todo` and `unimplemented`. See [Known gaps](#known-gaps).

---

## Miscellaneous types

```python
from oxide import (
    Ordering, ControlFlow, Reverse, Wrapping, Saturating, NonZero,
    SmallVec, ArrayVec, BitVec,
)

Ordering.from_cmp(1, 2)               # Ordering::Less
Ordering.greater().is_greater()       # True
Ordering.less().reverse()             # Ordering::Greater

ControlFlow.brk(1).is_break()         # True
ControlFlow.cont().is_continue()      # True

Reverse([1, 2, 3]).as_ref()           # [3, 2, 1]
Wrapping(0xFFFFFFFF).wrapping_add(1)  # wraps at 32 bits -> 0
Saturating(255).saturating_add(1)     # clamps at 32 bits -> 255

NonZero.new(5).get()                  # 5 — invariant: never zero
NonZero.try_new(0)                    # None

SmallVec([1, 2]).push(3)              # inline storage, spills to the heap
ArrayVec.with_capacity(4).is_full()   # False — fixed capacity, no allocation
BitVec.from_bytes(b"\xff").count_ones()   # 8
BitVec.from_bytes(b"\xff").count_zeros()  # 0
```

---

## Regular expressions

`oxide.regex` is a from-scratch engine: patterns compile to a Thompson NFA that is
simulated by a priority-ordered Pike VM. It implements the subset of Rust's `regex`
syntax that avoids backtracking, and rejects exactly the constructs that make
backtracking necessary.

```python
from oxide import IGNORECASE, Regex, RegexError, RegexMatch
from oxide import regex

rx = Regex(r"(?P<user>[a-z0-9._%+-]+)@(?P<host>[a-z0-9.-]+)", IGNORECASE)
m = rx.search("mail Ann@Example.COM now")
m.span()             # (5, 20)
m.group("user")      # 'Ann'
m.group(1)           # 'Ann'
m.groupdict()        # {'user': 'Ann', 'host': 'Example.COM'}
m.start(2), m.end()  # (9, 20)

Regex(r"\d+").findall("a1b22")        # ['1', '22']
[m.span() for m in Regex(r"\d").finditer("a1b2")]   # [(1, 2), (3, 4)]
Regex(r"(\w+)@(\w+)").sub(r"\2 at \1", "ann@example")  # 'example at ann'
regex.split(r",\s*", "a, b,c")        # ['a', 'b', 'c']
regex.escape("a.b*c")                 # 'a\\.b\\*c'

compiled = regex.compile(r"^\d+$")    # reuse instead of recompiling
compiled.fullmatch("12345") is not None   # True
```

### Complexity and guarantees

- **No catastrophic backtracking.** There is no backtracking stack to blow up: a
  pattern cannot take exponential time on a hostile input.
- **Anchored matching** (`match`, `fullmatch`) is `O(len(text) * len(program))` —
  linear in the subject with a fixed bound from the program size.
- **Unanchored `search()`** tries the start position, then each following
  position. Each attempt is bounded as above, so total work is
  `O(len(text) * len(text) * len(program))` in the worst case.
- Matching is leftmost-first, and capture groups follow the same priority order
  as Rust's `regex`.

Nested-quantifier patterns such as `(a+)+$` and `(a|aa)+$` — the classic ReDoS
shapes — are *accepted* by the grammar and executed by the VM, so they degrade to
polynomial time instead of exploding. Anchoring them with `fullmatch` keeps even
the failing case linear:

```python
import time
from oxide import Regex

evil = "a" * 1600 + "!"

t0 = time.perf_counter()
Regex(r"(a+)+$").fullmatch(evil)      # anchored: linear, ~3 ms
time.perf_counter() - t0

t0 = time.perf_counter()
Regex(r"(a+)+$").search(evil)         # unanchored: quadratic, ~2 s
time.perf_counter() - t0
```

For long untrusted subjects prefer an anchored pattern, a literal prefix, or
`ASCII`-restricted classes. `search()` on a pattern with a literal that is *not*
present stays linear, because the first character is pre-filtered.

### Supported syntax

| Construct | Example |
| --- | --- |
| literals, `.` | `a.c` |
| character classes, negation | `[abc]`, `[^abc]`, `[a-z]`, `[[:alpha:]0-9]` |
| POSIX classes | `[[:alpha:]]`, `[[:digit:]]` (ASCII-only) |
| escapes | `\d \D \w \W \s \S \n \t \r \f \v \0` |
| hex / unicode escapes | `\x41`, `\u0041` |
| quantifiers | `*`, `+`, `?`, `{m}`, `{m,}`, `{m,n}` |
| lazy quantifiers | `*?`, `+?`, `??`, `{m,n}?` |
| groups, non-capturing, comment | `(a)`, `(?:a)`, `(?#note)a` |
| named groups | `(?P<name>a)` |
| alternation | `a|b` |
| anchors | `^`, `$`, `\A`, `\Z`, `\b`, `\B` |
| verbose mode (pass the flag) | `Regex(" a b ", VERBOSE)` |

> **Known gaps:** `\z`, `\G` and `\Q` are parsed but silently never match —
> `\Z` is the supported end-of-text anchor. Brace escapes (`\x{41}`, `\u{1F600}`)
> are rejected; use the fixed-width `\x41` / `\u0041` forms. Inline flag groups
> such as `(?i)`, `(?i:...)` and `(?x)` are **not** implemented — pass the flags
> to the constructor instead.

### Rejected syntax

These raise `RegexError` with the offending position, mirroring where Rust's
`regex` crate stops:

| Rejected | Error |
| --- | --- |
| lookahead `(?=a)`, `(?!a)` | `lookahead is not supported at position N` |
| lookbehind `(?<=a)`, `(?<!a)` | `lookbehind is not supported at position N` |
| backreference `\1`, `(?P=x)` | `backreferences are not supported at position N` |
| atomic group `(?>a)` | `atomic groups are not supported at position N` |
| possessive `a*+` | `possessive quantifiers are not supported at position N` |
| unicode property `\p{L}` | `unicode property escapes are not supported at position N` |
| conditional `(?(1)a)` | `unknown extension at position N` |
| inline flags `(?i)`, `(?i:a)`, `(?x)` | `missing ), unterminated subpattern at position N` |
| brace escapes `\u{1F600}` | `incomplete escape at position N` |

### Flags

Flags are plain `int` constants, combined with `|` and passed as the second
argument. They are *not* attributes of `Regex`:

```python
from oxide import Regex, ASCII, IGNORECASE, MULTILINE, DOTALL, UNICODE, VERBOSE

Regex(r"a", IGNORECASE).search("A")     # matches
Regex(r"^b", MULTILINE).search("a\nb")   # matches at the line start
Regex(r"a.b", DOTALL).search("a\nb")     # `.` matches the newline
Regex(" a b ", VERBOSE).fullmatch("ab")  # whitespace and # comments ignored
Regex("a  # note\n b", VERBOSE).fullmatch("ab")
Regex(r"é", IGNORECASE).search("É")      # Unicode case folding
Regex(r"\w", ASCII).search("é")          # None — ASCII-only word characters
Regex(r"\w").search("é")                 # matches — Unicode by default
Regex("abc", ASCII | IGNORECASE).flags   # the effective flag mask
```

`IGNORECASE` performs simple case folding plus reverse folding, so `É` matches
`é`, `ς` matches `σ`, and `İ` matches `i`. Reverse folding is precomputed for
U+0000–U+2FFF; the first pattern that needs it pays about 2 ms to build the table.

### The match object

`RegexMatch` (also available as `regex.Match`):

| Method | Returns |
| --- | --- |
| `group(n=0)` | the capture group, or the whole match |
| `groups()` | tuple of all captures, unmatched as `None` |
| `groupdict()` | `{name: value}` for named groups |
| `start(n=0)` / `end(n=0)` | offsets of the group |
| `span(n=0)` | `(start, end)` |
| `expand(template)` | see [below](#replacement-templates) |

Methods that return a match return `None` when nothing matched, mirroring `re`.
Out-of-range groups raise `IndexError`.

### Replacement templates

`Regex.sub` and `Regex.subn` accept a string template with `\1`, `\g<name>` and
`\g<1>` references, or a callable receiving the match object:

```python
from oxide import Regex

Regex(r"(\w+) (\w+)").sub(r"\2 \1", "hello world")   # 'world hello'
Regex(r"\d").sub(lambda m: "<>", "a1b2")             # 'a<>b<>'
Regex(r"\d").subn("#", "a1b2")                       # ('a#b#', 2)
Regex(r"(\w+)\s+(\w+)").sub(r"\g<2> \g<1>", "a b")   # 'b a'
```

> `RegexMatch.expand()` currently returns its template unexpanded — use
> `Regex.sub` for named-group substitution. See [Known gaps](#known-gaps).

`Regex.pattern`, `Regex.flags`, `Regex.groups` and `Regex.groupindex` are plain
attributes (a `str`, an `int` flag mask, an `int` group count, and a `dict`),
not methods:

```python
from oxide import IGNORECASE, Regex

rx = Regex(r"(?P<u>[a-z]+)@(?P<h>[a-z]+)", IGNORECASE)
rx.pattern              # '(?P<u>[a-z]+)@(?P<h>[a-z]+)'
rx.flags                # 2  (IGNORECASE)
rx.groups               # 2
rx.groupindex           # {'u': 1, 'h': 2}
```

---

## Validation and sanitization

`oxide.filter` mirrors PHP's `filter_var()`: validators return `Result`, and
sanitizers return the cleaned value.

Every operation lives on the `Filter` class:

```python
from oxide import Filter, FilterError

Filter.validate("ann@example.com", Filter.EMAIL)      # Ok(value='ann@example.com')
Filter.validate("not-an-email", Filter.EMAIL)         # Err(error=FilterError('email', 'an email address'))
Filter.is_valid("42", Filter.INT)                     # True
Filter.var("https://example.com/x", Filter.URL)       # 'https://example.com/x'
Filter.sanitize("<b>hi</b>", Filter.SANITIZE_SPECIAL_CHARS)   # '&lt;b&gt;hi&lt;/b&gt;'
```

Validating **coerces**: `Filter.validate("42", Filter.INT)` gives you
`Ok(value=42)` — an `int`, not a string.

> There are no module-level `validate_var`/`filter_var`/`is_valid`/`sanitize_var`
> pass-throughs; use the methods above, or the low-level predicates and sanitizers
> in `oxide.filter.validators` and `oxide.filter.sanitizers`.

A `FilterError` exposes `.filter()` (the filter that failed) and `.reason()` (a
human-readable explanation):

```python
from oxide import Filter

failure = Filter.validate("not-an-email", Filter.EMAIL).unwrap_err()
failure.filter()                                  # 'email'
failure.reason()                                  # 'an email address'
failure.add_note("while parsing signup")          # currently returns None (no-op)
```

On the `Result` itself, `.unwrap_err()` returns the `FilterError`, `.err()` returns
`Option[FilterError]`, and `.error` is the raw `Err` payload.

### Validators

`Filter.validate(value, name, flags=0, options=None)` returns
`Ok(coerced_value)` or `Err(FilterError(name, reason))`. These 19 names are
registered out of the box:

| Filter | Constant | Accepts |
| --- | --- | --- |
| `email` | `Filter.EMAIL` | `local@domain.tld` |
| `url` | `Filter.URL` | `http(s)://host[/path]`, optionally requiring a path |
| `ip` | `Filter.IP` | IPv4 or IPv6 literals |
| `ipv4` / `ipv6` | `Filter.IPV4` / `Filter.IPV6` | version-specific |
| `domain` | `Filter.DOMAIN` | DNS-style hostnames |
| `regexp` | `Filter.REGEXP` | matches the `regexp` option |
| `mac` | `Filter.MAC` | `00:1B:44:11:3A:B7` |
| `hex` | `Filter.HEX` | hexadecimal strings |
| `uuid` | `Filter.UUID` | canonical UUIDs |
| `alpha` / `alpha_numeric` | `Filter.ALPHA` / `Filter.ALPHA_NUMERIC` | letters / letters and digits |
| `slug` | `Filter.SLUG` | lowercase, dash-separated |
| `json` | `Filter.JSON` | parseable JSON |
| `date` | `Filter.DATE` | ISO dates |
| `boolean` | `Filter.BOOLEAN` | `true/false/1/0/yes/no/on/off` |
| `int` / `float` / `numeric` | `Filter.INT` / `Filter.FLOAT` / `Filter.NUMERIC` | numeric strings |

### Sanitizers

`Filter.sanitize(value, name, flags=0)` returns the cleaned value as a string.
These 9 names are registered out of the box:

| Filter | Constant | Effect |
| --- | --- | --- |
| `sanitize_email` | `Filter.SANITIZE_EMAIL` | strips characters illegal in an address |
| `sanitize_url` | `Filter.SANITIZE_URL` | keeps only URL-legal characters |
| `sanitize_url_raw` | `Filter.SANITIZE_URL_RAW` | as above, plus `; : @ + $ , [ ] /` |
| `sanitize_number_int` | `Filter.SANITIZE_NUMBER_INT` | keeps digits and a leading sign |
| `sanitize_number_float` | `Filter.SANITIZE_NUMBER_FLOAT` | as above, plus `.` and exponent |
| `sanitize_string` | `Filter.SANITIZE_STRING` | HTML-escapes `& < > " '` |
| `sanitize_special_chars` | `Filter.SANITIZE_SPECIAL_CHARS` | HTML-escapes special characters |
| `sanitize_stripped` | `Filter.SANITIZE_STRIPPED` | strips HTML tags and trims whitespace |
| `sanitize_encoded` | `Filter.SANITIZE_ENCODED` | decodes HTML entities back to literals |

> Despite the PHP-inspired names, three of these differ from PHP and are worth
> checking before you rely on them: `SANITIZE_STRING` HTML-escapes rather than
> stripping tags, `SANITIZE_STRIPPED` is the one that removes tags, and
> `SANITIZE_ENCODED` *decodes* entities instead of URL-encoding. Also note
> `SANITIZE_URL` strips `:` and `/`, so it destroys a URL's scheme and path —
> use `SANITIZE_URL_RAW` for whole URLs.

```python
from oxide import Filter

Filter.sanitize("3.14abc", Filter.SANITIZE_NUMBER_FLOAT)  # '3.14'
Filter.sanitize("$1,234.56", Filter.SANITIZE_NUMBER_INT)  # '123456' — digits only
Filter.sanitize("  <b>hi</b>  ", Filter.SANITIZE_STRIPPED)  # 'hi'
Filter.sanitize("A B@c.com", Filter.SANITIZE_EMAIL)       # 'AB@c.com'
Filter.sanitize("https://ex ample.com/x", Filter.SANITIZE_URL_RAW)  # 'https://example.com/x'
Filter.sanitize("&lt;b&gt;", Filter.SANITIZE_ENCODED)      # '<b>'
```

### Flags and options

Flags are integer bits, combined with `|`:

| Flag | Value | Effect |
| --- | --- | --- |
| `Filter.NULL_ON_FAILURE` | `1` | return `None` instead of `Err` |
| `Filter.REQUIRE_ARRAY` | `2` | require a list/tuple; validates every element |
| `Filter.EMAIL_UNICODE` | `4` | allow non-ASCII local parts |
| `Filter.ALLOW_FRACTION` | `8` | accept `4.5` for `Filter.INT` |
| `Filter.PATHNAME_REQUIRED` | `16` | require a path for `Filter.URL` |
| `Filter.EVEN_LENGTH` | `32` | require an even-length `Filter.HEX` |

Per-filter behaviour is passed through the `options` dictionary:

```python
from oxide import Filter

Filter.validate(["a@b.com", "bad"], Filter.EMAIL, Filter.REQUIRE_ARRAY)
# Err(error=FilterError('email', 'an email address'))  ← the offending element
Filter.validate("4.0", Filter.INT, Filter.ALLOW_FRACTION)
# Ok(value=4)  — a float with no fractional part coerces to int
Filter.validate("4.5", Filter.INT, Filter.ALLOW_FRACTION)
# Err(error=FilterError('int', 'an integer'))  — a real fraction is still rejected
Filter.validate("abc", Filter.HEX, Filter.EVEN_LENGTH)
# Err(error=FilterError('hex', 'a hexadecimal string of even length'))
Filter.validate("abc", Filter.REGEXP, 0, {"regexp": "^[a-z]+$"})
# Ok(value='abc')
Filter.var("nope", Filter.INT, Filter.NULL_ON_FAILURE)      # None
```

`ALLOW_FRACTION` only tolerates float *syntax* whose value is whole — `4.0`
becomes `4`, while `4.5` is rejected. Use `Filter.FLOAT` for real fractions.
`FILTER.EMAIL_UNICODE` widens the local part to non-ASCII, and
`PATHNAME_REQUIRED` rejects a URL with no path component. The `options` dict
accepts `{"regexp": ...}` for `Filter.REGEXP` and `{"even_length": bool}` for
`Filter.HEX` as an alternative to the flag bits.

Unknown filter names raise `ValueError: unknown validator: 'NOPE'`.

### Custom filters

Register a validator that returns `None` when the value is acceptable, or a
reason string when it is not. Sanitizers receive `(value, flags)` and return the
cleaned value.

```python
from oxide import Filter

def starts_with_ab(value, flags, options):
    return None if str(value).startswith("ab") else "must start with ab"

Filter.register("MY_HEX", validator=starts_with_ab)
Filter.validate("ab12", "MY_HEX")     # Ok(value='ab12')
Filter.validate("zz", "MY_HEX")       # Err(error=FilterError('MY_HEX', 'must start with ab'))
Filter.unregister("MY_HEX")

Filter.register("MY_UPPER", sanitizer=lambda value, flags: str(value).upper())
Filter.sanitize("hi", "MY_UPPER")     # 'HI'
Filter.unregister("MY_UPPER")
```

`Filter.filters()` lists every registered name; `Filter.is_validator(name)` and
`Filter.is_sanitizer(name)` classify them.

---

## Logging

`oxide.logging` is three layers: console output, the standard streams, and
structured loggers. Diagnostics go to **stderr**, keeping them out of a program's
real output — the same convention Rust follows.

```python
from oxide.logging import Logger, MemorySink, log_info, println, eprintln

# 1. Console output, like Rust's println!/eprintln!
println("listening on", 8080)          # stdout
eprintln("warning: disk almost full")  # stderr

# 2. A structured logger with an in-memory sink, for tests
sink = MemorySink()
log = Logger("worker", sink=sink, level="info")
log.info("loaded {n} rows", n=3)       # True
sink.messages()                        # ['loaded 3 rows']

# 3. The module-level helpers route to a default logger
log_info("started")                    # writes to stderr via the default logger
```

### Levels

`LogLevel` is a `str` subclass: it equals its own name (`LogLevel.WARN == "WARN"`)
but orders by **verbosity**, not alphabetically.

| Level | Short | Meaning |
| ----- | ----- | ------- |
| `ERROR` | `ERR` | Something failed and the caller must know |
| `WARN` | `WARN` | Suspicious but recoverable |
| `INFO` | `INFO` | Normal, expected progress |
| `DEBUG` | `DBG` | Detail useful while diagnosing a problem |
| `TRACE` | `TRACE` | Everything, including per-iteration detail |

Aliases are accepted everywhere: `warning`, `err`, `fatal`, `dbg`, `verbose`.

### Loggers and sinks

A sink is any callable taking `(level, target, message)`, so writing your own is
one function:

```python
def to_stdout(level, target, message):
    print(f"[{target}] {level.short} {message}")

log = Logger("api", sink=to_stdout)
log.child("db").warn("query took {ms}ms", ms=40)   # target is "api.db"
```

`console_sink()` is the built-in stderr writer, `MemorySink()` captures records
for tests, and `Logger.records()` reads them back. `Logger.child()` nests a
logger so a subsystem inherits its parent's level and sink while extending the
target name.

### Console and streams

`println`, `print_`, `eprintln`, and `eprint_` are the `println!`-style macros;
the trailing underscore on `print_` follows the library's convention for names
that would otherwise shadow a builtin, same as `assert_` and `dbg_`.
`stdin()`, `stdout()`, and `stderr()` return handles, and `capture()` redirects
both output streams into buffers so tests can assert on what was printed:

```python
from oxide.logging import capture, println, eprintln

out, err = capture()
println("x"); eprintln("y")
out.getvalue(), err.getvalue()     # ('x\n', 'y\n')
```

`set_stdout`/`set_stderr`/`set_stdin` redirect one stream, `style()` adds ANSI
colour, and `set_color()` forces colour on or off — honouring the `NO_COLOR` and
`FORCE_COLOR` conventions by default.

---

## Derive and lints

`oxide.derive` emulates Rust's attributes. Derives are applied by a class
decorator, and lints are resolved when the decorated function runs, since Python
has no compile step.

```python
from oxide.derive import derive, memoize, lint_warn

@derive("Debug", "Clone", "Default")
class Config:
    __slots__ = ("host", "port")
    def __init__(self, host="localhost", port=8080):
        self.host = host
        self.port = port

Config.default()                 # Config { host: 'localhost', port: 8080 }
Config.default(port=9090)        # Config { host: 'localhost', port: 9090 }
Config("db").clone()             # an independent copy
```

### Supported derives

`Debug`, `Display`, `Clone`, `Copy`, `PartialEq`, `Eq`, `PartialOrd`, `Ord`,
`Hash`, `Default`, `Error` — with aliases (`repr` → `Debug`, `fmt` → `Display`,
`eq` → `Eq`, …).

`Default` resolves each field in order: an override passed to `default()`, the
`defaults=` mapping, a `default_<field>` class attribute, then the matching
`__init__` parameter default. A field with no default anywhere raises
`DeriveError`, exactly as Rust refuses to compile. Generated methods never
replace a hand-written one unless you pass `overwrite=True`.

### Attribute macros

| Macro | Effect |
| ----- | ------ |
| `@memoize()` | Cache results; unhashable arguments fall back to `repr` |
| `@once()` | Run at most once |
| `@pure("...")` | Memoize and record a side-effect-free contract |
| `@timed("label")` | Report elapsed time |
| `@log_calls()` | Log every call through `oxide.logging` |
| `@must_use()` | Lint an ignored return value |
| `@deprecated("use X")` | Warn on use |
| `@non_exhaustive` | Mark an `Enum` open to future variants |
| `@cfg(feature=...)` | Define only when the feature is enabled |

### Lints

Rust's four levels — `allow`, `warn`, `deny`, `forbid` — are available as
`warn`, `deny`, and so on inside `oxide.derive`, and as `lint_warn`, `lint_deny`,
… at the top level so `warn` stays with `oxide.core.traits`.

```python
from oxide.derive import set_lint_level, lint_scope

set_lint_level("unused_result", "deny")   # process-wide
with lint_scope(deprecated="allow"):       # ...except in this block
    ...
```

A configured level raises the floor, so `deny` cannot be softened to `warn`
downstream. `warn` emits a `LintWarning`; `deny` and `forbid` raise `LintError`.

---

## Decorators

`oxide.decor` gathers every Rust decorator into one namespace, because Rust
spreads its attributes across the language, the standard library, and a pile of
proc-macro crates. It is a facade, not a reimplementation:
`oxide.decor.derive is oxide.derive.derive`.

```python
from oxide.decor import derive, inline, cfg, warn, test, run_tests, masterclass
```

It re-exports all of `oxide.derive` — the type-level attributes from
[Derive and lints](#derive-and-lints) — and adds the item attributes, the test
harness, and `masterclass`. Inside this namespace the plain Rust spellings work,
since nothing here collides with a builtin. At the top level of `oxide` the
colliding names are disambiguated (`derive_`, `cfg_`, `lint_warn`) so
`oxide.derive` keeps naming the subpackage.

### Item attributes

`#[no_mangle]`, `#[used]`, `#[cold]`, and `#[naked]` steer code generation, which
CPython offers no equivalent for, so they are recorded as metadata and read back
through `attributes_of` — the same treatment `inline` already gets.

```python
from oxide.decor import no_mangle, attributes_of

@no_mangle
def entry_point():
    return 1

attributes_of(entry_point)     # {'no_mangle': {'enabled': True}}
```

`main` is the exception with real behaviour: it runs an async function the way
`#[tokio::main]` does.

```python
import asyncio
from oxide.decor import main

@main
async def serve():
    await asyncio.sleep(0)
    return "done"

serve()                        # 'done'
```

### Test attributes

`#[test]`, `#[bench]`, `#[ignore]`, `#[should_panic]`, and `#[serial]` are emulated
for real: marked functions are collected into registries and executed by
`run_tests()`, which honours each attribute.

```python
from oxide.decor import ignore, run_tests, should_panic, test

@test
def test_ok():
    assert 1 + 1 == 2

@test
@should_panic(ValueError)
def test_expected_failure():
    raise ValueError("yes")

@test
@ignore("not ready")
def test_skipped():
    assert False

result = run_tests()
result.passed, result.ignored
# (('test_ok', 'test_expected_failure'), ('test_skipped',))
```

Tests are collected per module, the way Rust collects them per crate, so one
module's run never picks up another's. `run_tests(include_ignored=True)` runs the
ignored ones too, and `tests(module)`, `benches(module)`, and
`run_tests(module=module)` target another module's suite from a driver.

### masterclass

`masterclass` has no Rust spelling. It combines `classmethod` and `staticmethod`:
the class is always bound, and the instance is bound when one is reachable. A
method written as `(cls, self, ...)` works called on the class *and* on an
instance.

```python
from oxide.decor import masterclass

class Config:
    def __init__(self, value):
        self.value = value

    @masterclass
    def describe(cls, self):
        if self is None:
            return f"{cls.__name__} describes itself"
        return f"{cls.__name__} holds {self.value!r}"

Config(7).describe()           # 'Config holds 7'
Config.describe()              # 'Config describes itself'
```

Calling through the class passes `self=None`. `MasterMethod` is the descriptor
itself, and `is_master` reports whether a value is one.

---

## Help

`oxide.help` indexes the library by importing it and reading `__all__`, the
docstrings, and the signatures. It answers the question a README cannot: what
does this symbol actually do?

```python
from oxide.help import Help

Help("Vec").summary             # 'A growable array type with push, pop, ...'
Help("Vec").reference           # 'oxide._collections.Vec'
Help("Vec").fields              # ('_data', '_capacity')
Help("Vec").methods             # documented methods, sorted by name
Help("Vec").related             # neighbours in the same module
Help.module("iter").exports()   # everything oxide.iter exports
Help.search("range", limit=3)   # scored search; .matches holds the results
Help.overview().usage()         # rendered text for the whole library
Help("Vec").to_dict()           # the same data as plain JSON-able types
```

Scanning happens once, on first use, and is cached. `Help` accepts a symbol, a
module, or a search term, and `Help(topic).print(file)` writes the rendered page
wherever you want it.

---

## Real-world recipes

Every snippet below runs as written.

### 1. Validate an inbound webhook

```python
from oxide import Err, Filter, Ok, Result

def verify_event(payload: dict, secret_ok: bool) -> Result[dict, str]:
    if not secret_ok:
        return Err("signature mismatch")

    kind = Filter.validate(payload.get("type"), Filter.ALPHA)
    if kind.is_err():
        return Err("event type must be alphabetic")

    ident = Filter.validate(payload.get("id"), Filter.UUID)
    if ident.is_err():
        return Err(f"bad id: {ident.err().unwrap()}")

    return Ok({"type": kind.unwrap(), "id": ident.unwrap()})

verify_event({"type": "push", "id": "123e4567-e89b-12d3-a456-426614174000"}, True)
# Ok(value={'type': 'push', 'id': '123e4567-e89b-12d3-a456-426614174000'})
verify_event({"type": "push", "id": "nope"}, True)
# Err(error='bad id: a universally unique identifier (uuid)')
```

### 2. Scrub secrets out of logs without ReDoS risk

```python
from oxide import IGNORECASE, Regex

TOKEN = Regex(r"(bearer\s+)([a-z0-9._-]{8,})", IGNORECASE)
CARD = Regex(r"\b(?:\d[ -]*?){13,19}\b")

def scrub(line: str) -> str:
    line = TOKEN.sub(r"\1[REDACTED]", line)
    return CARD.sub("[CARD]", line)

scrub("Authorization: Bearer sk_live_9f8e7d6c5b4a")
# 'Authorization: Bearer [REDACTED]'
scrub("card 4111 1111 1111 1111 charged")
# 'card [CARD] charged'
```

### 3. Bounded worker pool over a channel

```python
import threading
from oxide import Channel, Mutex

def run_pool(jobs, workers=4):
    queue = Channel.bounded(64)
    results = Mutex([])

    def worker():
        while True:
            job = queue.receiver.try_recv()
            if job is None:
                break
            with results as guard:
                guard.replace(guard.value + [job.upper()])

    threads = [threading.Thread(target=worker) for _ in range(workers)]
    [t.start() for t in threads]
    for job in jobs:
        queue.send(job)          # False if the queue is full — handle that
    queue.sender.close()
    [t.join() for t in threads]
    return sorted(results.into_inner())

run_pool(["a", "b", "c"])
# ['A', 'B', 'C']
```

### 4. Retry with exponential backoff

```python
import random
import time
from oxide import Duration, Instant

def with_retry(attempts: int, base: Duration, fn):
    delay = base
    last_error = None
    for attempt in range(1, attempts + 1):
        started = Instant.now()
        try:
            return fn(attempt)
        except Exception as exc:          # noqa: BLE001 - surface after attempts
            last_error = exc
            if attempt == attempts:
                break
            print(f"attempt {attempt} failed after {started.elapsed().as_millis()}ms: {exc}")
            jitter = Duration.from_millis(random.randint(0, delay.as_millis() // 10 or 1))
            time.sleep(delay.secs_f64() + jitter.secs_f64())   # standard library
            delay = delay * 2
    raise last_error
```

### 5. A metrics registry that is safe to share

```python
import threading
from oxide import AtomicInt, Mutex, RwLock, Vec

class Metrics:
    def __init__(self):
        self._counters = Mutex({})
        self._timings = RwLock(Vec())
        self._dropped = AtomicInt(0)

    def increment(self, name: str) -> None:
        with self._counters as guard:
            current = dict(guard.value)   # plain dict: copy so we can mutate freely
            current[name] = current.get(name, 0) + 1
            guard.replace(current)

    def observe(self, millis: float) -> None:
        with self._timings.write() as guard:
            guard.value.push(millis)

    def snapshot(self):
        with self._counters as guard:
            return dict(guard.value), self._timings.read().value.to_list(), self._dropped.load()

m = Metrics()
workers = [threading.Thread(target=m.increment, args=("hits",)) for _ in range(50)]
[t.start() for t in workers]
[t.join() for t in workers]
counters, timings, dropped = m.snapshot()
counters["hits"]     # 50
```

### 6. Tokenise and summarise with a lazy pipeline

```python
from oxide import Iter

def summarise(text: str) -> dict:
    # collect once: every terminal call consumes the chain
    lengths = Iter(text.lower().split()).filter(lambda w: w.isalpha()).map(len).collect()

    return {
        "tokens": len(lengths),
        "longest": max(lengths),
        "shortest": min(lengths),
        "mean": round(sum(lengths) / max(len(lengths), 1), 2),
    }

summarise("The quick brown fox jumps over the lazy dog")
# {'tokens': 9, 'longest': 5, 'shortest': 3, 'mean': 4.11}
```

For a genuinely streaming summary, use `fold` so the data is visited exactly once:

```python
from oxide import Iter

def stats(values):
    return Iter(values).fold(
        {"n": 0, "total": 0, "max": None, "min": None},
        lambda acc, v: {
            "n": acc["n"] + 1,
            "total": acc["total"] + v,
            "max": v if acc["max"] is None else max(acc["max"], v),
            "min": v if acc["min"] is None else min(acc["min"], v),
        },
    )

stats([3, 1, 4, 1, 5])
# {'n': 5, 'total': 14, 'max': 5, 'min': 1}
```

### 7. Parse a config file and collect every problem

```python
from oxide import Filter, Vec

def load_config(text: str) -> tuple[dict, list[str]]:
    problems = []
    settings = {}

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, raw = line.partition("=")
        key, raw = key.strip(), raw.strip()

        if key == "port":
            checked = Filter.validate(raw, Filter.INT)
            if checked.is_err():
                problems.append(f"port: {raw!r} is not an integer")
            elif not 1 <= checked.unwrap() <= 65535:
                problems.append(f"port: {raw!r} out of range")
            else:
                settings["port"] = checked.unwrap()
        elif key == "host":
            checked = Filter.validate(raw, Filter.DOMAIN)
            if checked.is_err():
                problems.append(f"host: {raw!r} is not a domain")
            else:
                settings["host"] = raw
        else:
            problems.append(f"unknown key: {key!r}")

    return settings, problems

load_config("port = 8080\nhost = example.com\n")
# ({'port': 8080, 'host': 'example.com'}, [])
load_config("port = nope\nnonsense = 1\n")
# ({}, ["port: 'nope' is not an integer", "unknown key: 'nonsense'"])
```

The same shape with `Vec` if you prefer oxide collections — `Vec.push(...)`
instead of `list.append(...)`, `problems.len()` instead of `len(problems)`.

### 8. Async fan-out with a stream

```python
from oxide import join_all, spawn, Stream

async def fetch(name: str) -> str:
    return name.upper()

async def main():
    names = ["a", "b", "c"]
    handles = [spawn(fetch(n)) for n in names]
    return await join_all(handles)

spawn(main()).join()          # ['A', 'B', 'C']

async def numbers():
    for n in (1, 2, 3):
        yield n * n

async def pipeline():
    stream = Stream.from_async_iter(numbers())
    doubled = await stream.map(lambda n: n * 2)
    return await doubled.collect()

spawn(pipeline()).join()      # [2, 8, 18]
```

### 9. Deterministic cleanup on an error path

oxide ships `defer`/`ScopeGuard` for Rust-style scoping, but it does not currently
fire — use `try/finally` (or a context manager) until that is fixed:

```python
from oxide import Ok, Err, Result

def load(path: str) -> Result[str, str]:
    handle = open(path, "r")
    try:
        content = handle.read()
    except OSError as exc:
        return Err(str(exc))
    finally:
        handle.close()
    return Ok(content) if content else Err("empty file")
```

---

## Performance notes

| Operation | Complexity |
| --- | --- |
| `Vec.push` / `pop` | amortised O(1) |
| `Vec.insert` / `remove` | O(n) |
| `Vec.get` | O(1) |
| `Vec.sort` | O(n log n), stable |
| `HashMap.get` / `insert` | O(1) average |
| `BTreeMap.get` | O(log n) |
| `HashSet` membership | O(1) average |
| `BinaryHeap.push` / `pop` | O(log n) |
| `VecDeque.push_back` / `pop_front` | O(1) |
| `Iter` adapters | lazy; each element passes through the chain once |
| `Regex.match` / `fullmatch` | O(len(text) × len(program)) |
| `Regex.search` | O(len(text) × len(text) × len(program)) worst case |
| `Duration` / `Instant` arithmetic | O(1) |
| `Rc.clone` / `Arc.clone` | O(1) |

Practical advice:

- Reuse a compiled `Regex` object; compilation is cached for module-level
  patterns but a `Regex` instance is cheaper to reuse in loops.
- Prefer anchored patterns (`^…`) or `fullmatch` when you know the input shape —
  it removes the unanchored retry factor entirely.
- `Box.new(...)` allocates; use it for large or recursive values, not for small
  integers.
- `Mutex` guards are context managers — always use `with`, or you will leak the
  lock.

---

## Known gaps

oxide is a work in progress. These are the honest current limitations; the rest
of the README documents only behaviour that is verified to work.

| Area | Current state |
| --- | --- |
| `RegexMatch.expand()` | returns the template unexpanded; `Regex.sub` with `\g<name>` works correctly. |
| `try_from()` / `into()` | dispatch incorrectly and fail for plain builtin types. `try_into()` works. |
| `defer()` / `ScopeGuard` | the cleanup callable is not executed. Use `try/finally`. |
| `JoinHandle` | `run()` followed by `get_result()` re-awaits the coroutine; `is_finished()` stays `False` after `join()`. Use `spawn(coro).join()`. |
| `Stream` adapters | `map`, `filter`, `take` are coroutines, so every link in a chain must be awaited individually. |
| `MutexGuard` | has no `__enter__`/`__exit__` (unlike the `RwLock` guards). Use `with mutex as guard:`. |
| `assert_matches`, `assert_type` | not re-exported from `oxide`; import them from `oxide.macros.assertions`. |
| `Filter.REGEXP_MATCHED` | is a string, not a flag bit, unlike the other flag constants. |
| `Regex` complexity | `search()` restarts at every position, so it can be quadratic on very long subjects (still linear-time per attempt, so never exponential). |
| POSIX classes | `[[:alpha:]]`, `[[:alnum:]]`, `[[:digit:]]`, `[[:upper:]]`, `[[:lower:]]`, `[[:xdigit:]]` are ASCII-only, including under `UNICODE`. |
| `IGNORECASE` folding | reverse folding is precomputed for U+0000–U+2FFF; supplementary-plane case pairs are not folded backwards. |
| `_io` read protocol | `Read.read(buf)` fills a caller-supplied buffer, Rust-style. There is no `read(n)` convenience form, so `Cursor(b"x").read(5)` raises `TypeError`; pass a `bytearray` instead. |
| `VecDeque.get`, `HashSet.remove` | return plain `None` rather than an `Option`, unlike `Vec.get` and `HashMap.get`. `HashSet.take` is the `Option`-free counterpart that reports whether the value was present. |
| `#[no_mangle]`, `#[used]`, `#[cold]`, `#[naked]` | record metadata only — CPython has no equivalent of Rust's codegen controls, so read them back with `attributes_of`. `repr_`, `track_caller`, `main`, `test`, and `ignore`/`should_panic` do have real behaviour. |
| `#[bench]`, `#[serial]` | `benches()` collects benchmarks but there is no `run_benches()` timing loop, and `run_tests()` is sequential already, so `#[serial]` is recorded but never contended. |
| Test suite | the docstring examples are the test suite and run under `pytest --doctest-modules`; there is no separate `tests/` directory and no CI yet. |

---

## Project layout

```
.
├── oxide/                       # the package
│   ├── __init__.py              # the full public API (298 names)
│   ├── prelude.py               # curated imports
│   ├── py.typed                 # PEP 561 marker
│   ├── core/                    # option, result, enum, traits, convert, error
│   ├── _collections/            # vec, hashmap, hashset, btreemap/set, vecdeque, heap, list
│   ├── iter/                    # iterator, adapters, consumers
│   ├── memory/                  # box, rc, arc, cell, refcell, oncecell, lazy, cow, pin
│   ├── sync/                    # atomic, mutex, rwlock, barrier, condvar, channel, once, semaphore
│   ├── _time/                   # duration, instant, system_time
│   ├── _io/                     # read, write, buffered, cursor
│   ├── fs/                      # path, file, metadata
│   ├── net/                     # address, tcp, udp
│   ├── process/                 # command, child, output
│   ├── async_/                  # future, poll, waker, join handle, stream
│   ├── macros/                  # assertions, debugging, panic
│   ├── other.py                 # Ordering, ControlFlow, numeric and vector helpers
│   ├── regex/                   # api, engine, _syntax, fuzz
│   ├── filter/                  # filter, validators, sanitizers
│   ├── logging/                 # level, logger, console
│   ├── derive/                  # registry, attributes, derive, functions
│   ├── decor/                    # items, masterclass — every Rust decorator
│   └── help/                    # catalog, render, help
├── assets/                      # logo and icon artwork
├── docs/API.md                  # complete API reference
├── requirements.txt
└── pyproject.toml
```

The repository root is the *project*; `oxide/` is the package. That split is what
lets `pip install ./oxide` build a correct wheel rather than an empty one.

---

## Development

```bash
git clone https://github.com/matkecn/oxide.git
cd oxide
python3 -m pip install -e .

# import every module
python3 -c "import oxide; print(len(oxide.__all__), 'names')"

# the doctests double as the test suite
python3 -m pytest

# run one package's doctests
python3 -m pytest --doctest-modules oxide/regex

# differential fuzz the regex engine against the standard library
python3 -m oxide.regex.fuzz

# build the wheel and sdist
python3 -m build
```

`pyproject.toml` sets `addopts = "--doctest-modules"` and `testpaths = ["oxide"]`,
so a bare `python3 -m pytest` runs every docstring example in the package.

The regex engine is verified by a differential fuzzer that generates random
patterns and compares `oxide.regex` against Python's `re`, plus a corpus of
hand-written patterns. The current run is clean: 9,135 corpus combinations and
4,000 generated patterns produce zero unexpected divergences.

---

## Contributing

Issues and pull requests are welcome on
[GitHub](https://github.com/matkecn/oxide). Especially welcome:

- validators and sanitizers for `oxide.filter` (the registry is extensible)
- fixes for anything listed in [Known gaps](#known-gaps)
- tests — the project needs a real suite
- packaging and CI work

Please keep new code in the existing style: full type hints, Google-style
docstrings with runnable `>>>` examples, and doctests that pass.

---

## License

Released under the terms in [LICENSE](LICENSE).

<div align="center">
  <img alt="oxide icon" src="assets/icon.svg" width="96">
</div>