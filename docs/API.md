# oxide API Reference

Complete API documentation for all classes, functions, and types in the oxide library.

---

## Table of Contents

- [Core Types](#core-types)
  - [Option](#option)
  - [Result](#result)
  - [Enum](#enum)
  - [Traits](#traits)
  - [Ranges](#ranges)
  - [Error](#error)
- [Collections](#collections)
  - [Vec](#vec)
  - [HashMap](#hashmap)
  - [HashSet](#hashset)
  - [BTreeMap](#btreemap)
  - [BTreeSet](#btreeset)
  - [VecDeque](#vecdeque)
  - [BinaryHeap](#binaryheap)
  - [LinkedList](#linkedlist)
- [Iterators](#iterators)
  - [Iter](#iter)
  - [Iterator Adapters](#iterator-adapters)
  - [Iterator Consumers](#iterator-consumers)
- [Memory Management](#memory-management)
  - [Box](#box)
  - [Rc](#rc)
  - [Arc](#arc)
  - [Cell](#cell)
  - [RefCell](#refcell)
  - [OnceCell](#oncecell)
  - [Lazy](#lazy)
  - [Cow](#cow)
  - [Pin](#pin)
- [Concurrency](#concurrency)
  - [Mutex](#mutex)
  - [RwLock](#rwlock)
  - [Channel](#channel)
  - [Atomic](#atomic)
  - [Barrier](#barrier)
  - [Condvar](#condvar)
  - [Once](#once)
  - [Semaphore](#semaphore)
- [Time](#time)
  - [Duration](#duration)
  - [Instant](#instant)
  - [SystemTime](#systemtime)
- [I/O](#io)
  - [Read](#read)
  - [Write](#write)
  - [BufReader](#bufreader)
  - [BufWriter](#bufwriter)
  - [Cursor](#cursor)
- [Filesystem](#filesystem)
  - [Path](#path)
  - [PathBuf](#pathbuf)
  - [File](#file)
  - [Metadata](#metadata)
- [Networking](#networking)
  - [TcpStream](#tcpstream)
  - [TcpListener](#tcplistener)
  - [UdpSocket](#udpsocket)
  - [Address Types](#address-types)
- [Process](#process)
  - [Command](#command)
  - [Child](#child)
  - [ExitStatus](#exitstatus)
- [Async](#async)
  - [Future](#future)
  - [Poll](#poll)
  - [Stream](#stream)
  - [JoinHandle](#joinhandle)
- [Macros](#macros)
  - [Assertions](#assertions)
  - [Debugging](#debugging)
  - [Panic](#panic)
- [Miscellaneous](#miscellaneous)
- [Regular Expressions](#regular-expressions)
- [Validation & Sanitization](#validation--sanitization)
- [Prelude](#prelude)
- [Logging](#logging)
  - [Log levels](#log-levels)
  - [Loggers and sinks](#loggers-and-sinks)
  - [Console and streams](#console-and-streams)
- [Derive and Attribute Macros](#derive-and-attribute-macros)
  - [Supported derives](#supported-derives)
  - [Lints](#lints)
- [Decorators](#decorators)
  - [One namespace for Rust attributes](#one-namespace-for-rust-attributes)
  - [Item attributes](#item-attributes)
  - [Test attributes](#test-attributes)
  - [masterclass](#masterclass)
- [Help](#help)

---

## Core Types

### Option

`Option[T]` represents an optional value. Every `Option` is either `Some(value)` or `None_`.

```python
from oxide import Option, Some, None_
```

#### Classes

**`Option[T]`** — Abstract base class for optional values.

| Method | Signature | Description |
|--------|-----------|-------------|
| `is_some()` | `-> bool` | Returns `True` if the option is `Some` |
| `is_none()` | `-> bool` | Returns `True` if the option is `None_` |
| `unwrap()` | `-> T` | Returns the contained value or raises `RuntimeError` |
| `expect(message)` | `-> T` | Returns the contained value or raises with custom message |
| `unwrap_or(default)` | `-> T` | Returns the contained value or `default` |
| `unwrap_or_else(fn)` | `-> T` | Returns the contained value or computes from `fn` |
| `map(fn)` | `-> Option[U]` | Transforms `Some(v)` to `Some(fn(v))` |
| `map_or(default, fn)` | `-> U` | Maps or returns `default` |
| `map_or_else(default_fn, fn)` | `-> U` | Maps, or calls the zero-argument `default_fn()` for the fallback |
| `and_(other)` | `-> Option[U]` | Returns `other` if `Some`, else `None_` |
| `and_then(fn)` | `-> Option[U]` | Chains operations on `Some` values |
| `or_(other)` | `-> Option[T]` | Returns `self` if `Some`, else `other` |
| `or_else(fn)` | `-> Option[T]` | Returns `self` if `Some`, else computes from `fn` |
| `filter(predicate)` | `-> Option[T]` | Returns `None_` if `Some` but predicate fails |
| `inspect(fn)` | `-> Option[T]` | Calls `fn` with value if `Some`, returns self |

**`Some(value)`** — Frozen dataclass wrapper for a present value, subclassing `Option`.

```python
from dataclasses import dataclass
from typing import Generic, TypeVar

from oxide import Option

T = TypeVar("T")

@dataclass(frozen=True)
class Some(Option[T], Generic[T]):   # Option is Generic[T]
    value: T
```

**`NoneOption`** — Singleton subclass of `Option` representing absence of a
value. `repr()` is `None`. Do not instantiate it directly: use the `None_`
constant, or the `none` alias.

```python
from oxide import NoneOption, None_, none

NoneOption() is None_   # True — NoneOption() returns the singleton
none is None_           # True — `none` is an alias for `None_`
```

#### Usage Examples

```python
from oxide import Option, Some, None_, match, _

# Creating options
x: Option[int] = Some(5)
y: Option[int] = None_

# Pattern matching with match
result = match(x).case(Some(_), "some").otherwise("none")   # 'some'
result = match(y).case(Some(_), "some").otherwise("none")   # 'none'

# Functional transformations
doubled = x.map(lambda v: v * 2)  # Some(10)
default_val = y.unwrap_or(0)      # 0
```

---

### Result

`Result[T, E]` represents success or failure. Every `Result` is either `Ok(value)` or `Err(error)`.

```python
from oxide import Result, Ok, Err
```

#### Classes

**`Result[T, E]`** — Abstract base class for success/error values.

| Method | Signature | Description |
|--------|-----------|-------------|
| `is_ok()` | `-> bool` | Returns `True` if `Ok` |
| `is_err()` | `-> bool` | Returns `True` if `Err` |
| `unwrap()` | `-> T` | Returns value or raises `RuntimeError` |
| `expect(message)` | `-> T` | Returns value or raises with custom message |
| `unwrap_err()` | `-> E` | Returns error or raises `RuntimeError` |
| `expect_err(message)` | `-> E` | Returns error or raises with custom message |
| `unwrap_or(default)` | `-> T` | Returns value or `default` |
| `unwrap_or_else(fn)` | `-> T` | Returns value or computes from error |
| `map(fn)` | `-> Result[U, E]` | Transforms `Ok(v)` to `Ok(fn(v))` |
| `map_err(fn)` | `-> Result[T, U]` | Transforms `Err(e)` to `Err(fn(e))` |
| `map_or(default, fn)` | `-> U` | Maps or returns `default` |
| `map_or_else(default, fn)` | `-> U` | Maps or computes default |
| `and_(other)` | `-> Result[U, E]` | Returns `other` if `Ok` |
| `and_then(fn)` | `-> Result[U, E]` | Chains operations on `Ok` values |
| `or_(other)` | `-> Result[T, U]` | Returns `self` if `Ok`, else `other` |
| `or_else(fn)` | `-> Result[T, U]` | Returns `self` if `Ok`, else computes from error |
| `ok()` | `-> Option[T]` | Converts to `Some` if `Ok` |
| `err()` | `-> Option[E]` | Converts to `Some` if `Err` |
| `inspect(fn)` | `-> Result[T, E]` | Calls `fn` with value if `Ok` |
| `inspect_err(fn)` | `-> Result[T, E]` | Calls `fn` with error if `Err` |

**`Ok(value)`** — Wrapper for successful values.

**`Err(error)`** — Wrapper for error values.

#### Error Propagation

```python
from oxide import Result, Ok, Err, propagate, ask, try_ask

# propagate decorator enables ?-like syntax
@propagate
def divide(a: float, b: float) -> Result[float, str]:
    if b == 0:
        return Err("division by zero")
    return Ok(a / b)

@propagate
def process() -> Result[float, str]:
    return ask(divide(10, 3)) * 2  # Propagates Err automatically

# try_ask wraps exceptions into Err
@try_ask
def dangerous_operation() -> int:
    return int("not a number")  # Returns Err instead of raising
```

---

### Enum

`Enum` provides tagged unions with pattern matching.

```python
from oxide import Enum, Variant, match, None_, Some, _
```

#### Classes

**`Enum`** — Base class for defining algebraic data types.

```python
from oxide import Enum
class Color(Enum):
    RED = "red"              # tag 'RED', payload 'red'
    GREEN = "green"
    RGB = "rgb", "payload"   # tag 'RGB', payload 'payload'
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `variants()` | `-> list[str]` | Class method; variant names in declaration order |
| `is_valid(name)` | `-> bool` | Class method; True if `name` is a declared variant |

Only `str` values and `str`-leading tuples are collected as variants; attributes
declared with any other type are left alone as ordinary class attributes.

**`Variant`** — Instance of an enum variant. Created by attribute access on an
`Enum` subclass, or directly via `Variant(tag, value)`.

```python
from oxide import Enum

class Color(Enum):
    RED = "red"
    RGB = "rgb", "payload"

Color.RED.tag        # 'RED'  — the declaration name, not the payload
Color.RED.value      # 'red'
Color.RGB.value      # 'payload'
repr(Color.RED)      # "RED('red')"
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `tag` | Property | The variant tag name (the declaration name) |
| `value` | Property | The variant payload |
| `is_(*tags)` | `-> bool` | True if the tag is any of `tags` — compares against `'RED'`, not `'red'` |
| `unwrap()` | `-> Any` | Returns the payload |
| `unwrap_or(default)` | `-> Any` | Returns the payload; `default` is ignored (a Variant always has a value) |
| `expect(message)` | `-> Any` | Returns the payload; `message` is ignored, for Option/Result API parity |
| `map(fn)` | `-> Variant` | Applies `fn` to the payload, keeping the tag |
| `map_or(default, fn)` | `-> Any` | Returns `fn(payload)`; `default` is ignored |
| `and_then(fn)` | `-> Variant` | Chains a function that returns a `Variant` |
| `or_else(fn)` | `-> Variant` | Returns this same variant; `fn` is unused, for Option/Result API parity |
| `match(*cases)` | `-> Any` | `(tag, handler)` pairs; raises `MatchError` if none match |

```python
from oxide import Enum, _

class Color(Enum):
    RED = "red"

Color.RED.match(("RED", lambda v: f"warm: {v}"), ("BLUE", lambda v: "cold"))
# 'warm: red'

Color.RED.match((_, lambda v: "anything"))                       # 'anything'
Color.RED.match((("RED", lambda v: v == "red"), lambda v: "guarded"),
                ("RED", lambda v: "plain"))
# 'guarded'  — ((tag, guard), handler) checks the guard first
```

**`match(value)`** — Creates a `Match` builder for ordered pattern matching over
any value. Cases are evaluated in declaration order and the first hit wins.

```python
from oxide import None_, Some, _, match

match(Some("Alice")).case(Some(_), "found").otherwise("missing")   # 'found'
match(None_).case(Some(_), "found").otherwise("missing")          # 'missing'
match(5).case_eq(0, "zero").case_range(1, 10, "small").otherwise("large")
# 'small'
```

#### Match Builder

`Match` lives in `oxide.core.enum`, next to `Enum` and `Variant`. It is a
different class from `RegexMatch`, which is the regex engine's match object.
`Match` is single-use: `execute()` and `otherwise()` each consume it, so call
one or the other exactly once.

| Method | Description |
|--------|-------------|
| `case(pattern, handler, guard=)` | `value == pattern`, or `isinstance` for a type or tuple of types; `guard=` is an optional predicate |
| `case_type(typ, handler, guard=)` | `isinstance(value, typ)` |
| `case_eq(expected, handler, guard=)` | `value == expected` |
| `case_range(start, end, handler, guard=)` | `start <= value < end` (half-open) |
| `case_in(collection, handler, guard=)` | `value in collection` |
| `case_pred(pred, handler, guard=)` | `pred(value)` is truthy |
| `otherwise(handler)` | Catch-all; **evaluates and returns the result** |
| `execute()` | Evaluates the cases; raises `MatchError` if none match |

Handlers may be constants or callables; a callable receives the matched value.

```python
from oxide import match
match("hi").case_type(str, lambda s: len(s)).execute()          # 2
match(5).case(5, "five", guard=lambda n: n % 2 == 1).otherwise("other")
# 'five'
match(3.5).case_type(int, "int").case_type(str, "str").otherwise("float")
# 'float'
```

---

### Traits

17 trait protocols for Rust-style polymorphism.

```python
from oxide import (
    CloneTrait, CopyTrait, DebugTrait, DisplayTrait, DefaultTrait,
    EqTrait, OrdTrait, HashTrait, DropTrait,
    FromTrait, IntoTrait, TryFromTrait, TryIntoTrait,
    AsRefTrait, AsMutTrait, DerefTrait, DerefMutTrait,
)
```

#### Trait Protocols

| Protocol | Methods | Description |
|----------|---------|-------------|
| `CloneTrait` | `clone() -> T` | Deep copy semantics |
| `CopyTrait` | `copy() -> T` | Bitwise copy semantics |
| `DebugTrait` | `debug() -> str` | Debug string representation |
| `DisplayTrait` | `fmt() -> str` | User-facing display |
| `DefaultTrait` | `default() -> T` | Default instance creation |
| `EqTrait` | `eq()`, `ne()` | Equality comparison |
| `OrdTrait` | `cmp()`, `lt()`, `le()`, `gt()`, `ge()` | Total ordering |
| `HashTrait` | `hash() -> int` | Hash computation |
| `DropTrait` | `drop()` | Cleanup on deletion |
| `FromTrait` | `from_(value) -> T` | Conversion from other type |
| `IntoTrait` | `into() -> T` | Conversion to other type |
| `TryFromTrait` | `try_from(value) -> Result[T, str]` | Fallible conversion |
| `TryIntoTrait` | `try_into() -> Result[T, str]` | Fallible conversion |
| `AsRefTrait` | `as_ref() -> T` | Borrowed reference |
| `AsMutTrait` | `as_mut() -> T` | Mutable reference |
| `DerefTrait` | `deref() -> T` | Dereference |
| `DerefMutTrait` | `deref_mut() -> T` | Mutable dereference |

#### Helper Functions

```python
from oxide import (
    Vec, as_mut, as_ref, clone, debug, default_of, deref, deref_mut, display,
    drop, from_, into, try_from, try_into,
)

value = Vec([1, 2, 3])

clone(value)                  # Vec([1, 2, 3])
debug(value)                  # Debug representation
display(value)                # Display representation
default_of(list)              # Get default instance
from_(list, [1, 2])           # cls first
into("42", int)               # value first, then the target type
try_from(int, "42")           # Ok(value=42)
try_into("42", int)           # Ok(value=42)
as_ref(value)                 # Borrow reference
as_mut(value)                 # Borrow mutable reference
deref(value)                  # Dereference
deref_mut(value)              # Mutable dereference
drop(value)                   # Explicit drop
```

---

### Ranges

Rust-style range types.

```python
from oxide import Range, RangeInclusive, RangeFrom, RangeTo, RangeToInclusive, RangeFull
```

| Class | Syntax | Description |
|-------|--------|-------------|
| `Range(start, end)` | `start..end` | Half-open range |
| `RangeInclusive(start, end)` | `start..=end` | Closed range |
| `RangeFrom(start)` | `start..` | Open-ended start |
| `RangeTo(end)` | `..end` | Open-ended end |
| `RangeToInclusive(end)` | `..=end` | Open-ended end inclusive |
| `RangeFull` | `..` | Full range (everything) |

| Method | Description |
|--------|-------------|
| `contains(value)` | Check if value is in range |
| `is_empty()` | Check if range is empty |
| `iter()` | Get iterator over range |
| `__len__()` | Number of elements |

---

### Error

Rich error handling infrastructure.

```python
from oxide import Error, Backtrace, Location, context
```

**`Error`** — Enhanced exception with source chaining.

| Method | Signature | Description |
|--------|-----------|-------------|
| `new(message)` | Class method | Create new error |
| `from_source(source)` | Class method | Wrap existing exception |
| `message()` | `-> str` | Get error message |
| `source()` | `-> Exception \| None` | Get source exception |
| `backtrace()` | `-> Backtrace` | Get stack trace |
| `location()` | `-> Location \| None` | Get source location |
| `with_context(ctx)` | `-> Error` | Add context string |
| `with_source(source)` | `-> Error` | Chain source exception |

**`Backtrace`** — Captured stack trace.

**`Location`** — Source file location (file, line, column).

```python
from oxide import Error, context

original_error = Error("bad token")
context("during parsing", original_error).message()   # 'bad token'
context("during parsing", original_error).context()   # 'during parsing'
```

---

## Collections

### Vec

`Vec[T]` — Growable array with Rust-style API.

```python
from oxide import Vec
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new()` | Class method | Create empty vec |
| `with_capacity(capacity)` | Class method | Pre-allocate capacity |
| `from_iter(values)` | Class method | Create from iterable |
| `repeat(value, n)` | Class method | Create with repeated value |
| `len()` | `-> int` | Number of elements |
| `is_empty()` | `-> bool` | Check if empty |
| `capacity()` | `-> int` | Current capacity |
| `reserve(additional)` | `-> None` | Reserve additional space |
| `shrink_to_fit()` | `-> None` | Reduce to fit |
| `push(value)` | `-> None` | Append element |
| `pop()` | `-> Option[T]` | Remove and return last element |
| `insert(index, value)` | `-> None` | Insert at index |
| `remove(index)` | `-> T` | Remove and return at index |
| `swap_remove(index)` | `-> T` | Remove by swapping with last |
| `clear()` | `-> None` | Remove all elements |
| `truncate(length)` | `-> None` | Truncate to length |
| `get(index)` | `-> Option[T]` | Get element by index |
| `first()` | `-> Option[T]` | Get first element |
| `last()` | `-> Option[T]` | Get last element |
| `contains(value)` | `-> bool` | Check membership |
| `position(predicate)` | `-> Option[int]` | Find index of first match |
| `find(predicate)` | `-> Option[T]` | Find first match |
| `reverse()` | `-> None` | Reverse elements |
| `sort(key, reverse)` | `-> None` | Sort elements |
| `retain(predicate)` | `-> None` | Keep matching elements |
| `dedup()` | `-> None` | Remove consecutive duplicates |
| `append(other)` | `-> None` | Append another vec |
| `extend(values)` | `-> None` | Extend with iterable |
| `split_off(at)` | `-> Vec[T]` | Split at index |
| `iter()` | `-> Iterator[T]` | Get iterator |
| `into_iter()` | `-> Iterator[T]` | Consume into iterator |
| `to_list()` | `-> list[T]` | Convert to Python list |

---

### HashMap

`HashMap[K, V]` — Hash-based key-value map with Entry API.

```python
from oxide import HashMap, Entry, OccupiedEntry, VacantEntry
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new()` | Class method | Create empty map |
| `with_capacity(capacity)` | Class method | Pre-allocate capacity |
| `from_dict(values)` | Class method | Create from dict |
| `len()` | `-> int` | Number of entries |
| `is_empty()` | `-> bool` | Check if empty |
| `insert(key, value)` | `-> Option[V]` | Insert key-value pair |
| `get(key)` | `-> Option[V]` | Get value by key |
| `get_value(key)` | `-> V \| None` | Get raw value (no Option) |
| `get_mut(key)` | `-> Option[MutableValue]` | Get mutable value reference |
| `contains_key(key)` | `-> bool` | Check if key exists |
| `remove(key)` | `-> Option[V]` | Remove and return value |
| `entry(key)` | `-> Entry[K, V]` | Get entry for key |
| `or_insert(key, value)` | `-> V` | Insert if absent |
| `extend(values)` | `-> None` | Extend with pairs |
| `iter()` | `-> Iterator[tuple[K, V]]` | Iterate over pairs |
| `keys()` | `-> Iterator[K]` | Iterate over keys |
| `values()` | `-> Iterator[V]` | Iterate over values |
| `drain()` | `-> Iterator[tuple[K, V]]` | Remove and iterate |
| `clone()` | `-> HashMap[K, V]` | Deep clone |
| `to_dict()` | `-> dict[K, V]` | Convert to Python dict |

#### Entry API

`entry(key)` returns an `OccupiedEntry` when the key exists and a `VacantEntry`
when it does not. Both expose `key()`, `is_occupied()` and `is_vacant()`, and
their mutating methods all return the entry, so calls chain. Handlers receive a
`MutableValue` — use `.get()` and `.set()` rather than plain operators.

```python
from oxide import HashMap

table = HashMap.new()
table.insert("key", 1)

# Efficient in-place manipulation
entry = table.entry("key")
entry.is_occupied()                      # True if the key was already present
entry.and_modify(lambda v: v.set(v.get() + 10))   # occupied only
entry.get_mut().set(99)                  # occupied only

# One-liner insert-or-default
table.or_insert("missing", 0)                  # returns the effective value
table.or_insert_with("other", lambda: 2)
table.or_insert_with_key("key", lambda k: len(k))
table.insert_entry("fresh", 3)                 # insert, then an OccupiedEntry
table.remove_entry("fresh")                    # -> Option[(K, V)]
```

| Entry method | Availability | Description |
|--------------|--------------|-------------|
| `key()` | both | The entry's key |
| `is_occupied()` / `is_vacant()` | both | Which kind of entry this is |
| `get()` / `get_mut()` | occupied | The value, or a `MutableValue` handle for in-place mutation |
| `insert(value)` | both | Insert (occupied overwrites) |
| `remove_entry()` | both | Remove and return `(key, value)` |
| `or_insert(value)` | both | Insert `value` only if vacant; returns the effective value |
| `or_insert_with(fn)` / `or_insert_with_key(fn)` | both | As above, computed lazily |
| `and_modify(fn)` | occupied | Apply `fn(MutableValue)` in place |

---

### HashSet

`HashSet[T]` — Hash-based set with set operations.

```python
from oxide import HashSet
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new()` | Class method | Create empty set |
| `from_iter(values)` | Class method | Create from iterable |
| `insert(value)` | `-> bool` | Insert value (returns `True` if new) |
| `remove(value)` | `-> T \| None` | Remove and return value |
| `contains(value)` | `-> bool` | Check membership |
| `len()` | `-> int` | Number of elements |
| `is_empty()` | `-> bool` | Check if empty |
| `union(other)` | `-> HashSet[T]` | Set union |
| `intersection(other)` | `-> HashSet[T]` | Set intersection |
| `difference(other)` | `-> HashSet[T]` | Set difference |
| `symmetric_difference(other)` | `-> HashSet[T]` | Symmetric difference |
| `is_disjoint(other)` | `-> bool` | Check if disjoint |
| `is_subset(other)` | `-> bool` | Check if subset |
| `is_superset(other)` | `-> bool` | Check if superset |
| `iter()` | `-> Iterator[T]` | Iterate over elements |
| `drain()` | `-> Iterator[T]` | Remove and iterate |

---

### BTreeMap

`BTreeMap[K, V]` — Ordered map with sorted key iteration.

```python
from oxide import BTreeMap
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new()` | Class method | Create empty map |
| `from_dict(values)` | Class method | Create from dict |
| `insert(key, value)` | `-> V \| None` | Insert key-value pair |
| `get(key)` | `-> V \| None` | Get value by key |
| `remove(key)` | `-> V \| None` | Remove and return value |
| `contains_key(key)` | `-> bool` | Check if key exists |
| `first_key_value()` | `-> tuple[K, V] \| None` | Get smallest key-value |
| `last_key_value()` | `-> tuple[K, V] \| None` | Get largest key-value |
| `keys()` | `-> Iterator[K]` | Iterate keys in sorted order |
| `values()` | `-> Iterator[V]` | Iterate values in sorted order |
| `iter()` | `-> Iterator[tuple[K, V]]` | Iterate pairs in sorted order |
| `range_(start, end)` | `-> Iterator[tuple[K, V]]` | Range query |
| `to_dict()` | `-> dict[K, V]` | Convert to dict |

---

### BTreeSet

`BTreeSet[T]` — Ordered set with sorted iteration.

```python
from oxide import BTreeSet
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new()` | Class method | Create empty set |
| `from_iter(values)` | Class method | Create from iterable |
| `insert(value)` | `-> bool` | Insert value |
| `remove(value)` | `-> bool` | Remove value |
| `contains(value)` | `-> bool` | Check membership |
| `first()` | `-> T \| None` | Get smallest element |
| `last()` | `-> T \| None` | Get largest element |
| `range_(start, end)` | `-> Iterator[T]` | Range query |
| `union(other)` | `-> BTreeSet[T]` | Set union |
| `intersection(other)` | `-> BTreeSet[T]` | Set intersection |
| `difference(other)` | `-> BTreeSet[T]` | Set difference |

---

### VecDeque

`VecDeque[T]` — Double-ended queue with O(1) push/pop at both ends.

```python
from oxide import VecDeque
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new()` | Class method | Create empty deque |
| `from_iter(values)` | Class method | Create from iterable |
| `push_back(value)` | `-> None` | Add to back |
| `push_front(value)` | `-> None` | Add to front |
| `pop_back()` | `-> T \| None` | Remove from back |
| `pop_front()` | `-> T \| None` | Remove from front |
| `front()` | `-> T \| None` | Peek at front |
| `back()` | `-> T \| None` | Peek at back |
| `get(index)` | `-> T \| None` | Get by index |
| `insert(index, value)` | `-> None` | Insert at index |
| `remove(index)` | `-> T \| None` | Remove at index |
| `contains(value)` | `-> bool` | Check membership |
| `rotate_left(k)` | `-> None` | Rotate left by k |
| `rotate_right(k)` | `-> None` | Rotate right by k |
| `drain()` | `-> Drain[T]` | Remove and iterate |

---

### BinaryHeap

`BinaryHeap[T]` — Max-heap priority queue.

```python
from oxide import BinaryHeap
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new()` | Class method | Create empty heap |
| `from_iter(values, reverse)` | Class method | Create from iterable |
| `push(value)` | `-> None` | Add element |
| `pop()` | `-> T \| None` | Remove and return maximum |
| `peek()` | `-> T \| None` | Peek at maximum |
| `push_pop(value)` | `-> T` | Push then pop maximum |
| `contains(value)` | `-> bool` | Check membership |
| `drain()` | `-> Iterator[T]` | Remove and iterate in order |
| `to_list()` | `-> list[T]` | Get sorted list |

---

### LinkedList

`LinkedList[T]` — Doubly-linked list.

```python
from oxide import LinkedList
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new()` | Class method | Create empty list |
| `from_iter(values)` | Class method | Create from iterable |
| `push_front(value)` | `-> None` | Add to front |
| `push_back(value)` | `-> None` | Add to back |
| `pop_front()` | `-> T \| None` | Remove from front |
| `pop_back()` | `-> T \| None` | Remove from back |
| `front()` | `-> T \| None` | Peek at front |
| `back()` | `-> T \| None` | Peek at back |
| `contains(value)` | `-> bool` | Check membership |
| `reverse()` | `-> None` | Reverse list |
| `iter()` | `-> Iterator[T]` | Forward iteration |
| `iter_rev()` | `-> Iterator[T]` | Reverse iteration |
| `drain()` | `-> Drain[T]` | Remove and iterate |

---

## Iterators

### Iter

`Iter[T]` — Chainable iterator with built-in adapters and consumers.

```python
from oxide import Iter
```

#### Creating Iterators

```python
from oxide import Iter

Iter([1, 2, 3])                          # From any iterable
Iter.from_fn(lambda i: i * 2, start=0).take(4).collect()   # [0, 2, 4, 6]
Iter.repeat([1, 2]).take(5).collect()    # cycles the iterable FOREVER
Iter.chain([1, 2], [3]).collect()        # [1, 2, 3]
Iter.zip([1, 2], ["a", "b"]).collect()   # [(1, 'a'), (2, 'b')]
```

> `from_fn`, `repeat`, `chain` and `zip` are callable directly on the `Iter`
> class; `repeat` cycles forever, so always bound it with `take(...)`.
> There is no `Iter.range(...)` — use `Iter(range_(1, 5))`.
> Beware `count`: `Iter([1, 2, 3]).count()` is a *consumer* returning the number
> of remaining items, and there is no infinite-counter classmethod.

#### Adapter Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `map(fn)` | `-> Iter[U]` | Transform each element |
| `filter(predicate)` | `-> Iter[T]` | Keep matching elements |
| `filter_map(fn)` | `-> Iter[U]` | Filter and transform |
| `enumerate(start)` | `-> Iter[tuple[int, T]]` | Add index |
| `take(n)` | `-> Iter[T]` | Take first n elements |
| `take_while(predicate)` | `-> Iter[T]` | Take while condition |
| `skip(n)` | `-> Iter[T]` | Skip first n elements |
| `skip_while(predicate)` | `-> Iter[T]` | Skip while condition |
| `flat_map(fn)` | `-> Iter[U]` | Map and flatten |
| `flatten()` | `-> Iter[Any]` | Flatten nested iterables |
| `inspect(fn)` | `-> Iter[T]` | Side effect per element |
| `step_by(step)` | `-> Iter[T]` | Take every nth element |
| `zip_with(other, fn)` | `-> Iter[V]` | Zip with combining function |
| `fuse()` | `-> Iter[T]` | Stop after first None |

#### Consumer Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `fold(init, fn)` | `-> U` | Accumulate with function |
| `reduce(fn)` | `-> T \| None` | Reduce to single value |
| `collect()` | `-> list[T]` | Collect into list |
| `count()` | `-> int` | Count elements |
| `sum()` | `-> T` | Sum elements |
| `product()` | `-> T` | Product of elements |
| `min()` | `-> T \| None` | Find minimum |
| `max()` | `-> T \| None` | Find maximum |
| `all(predicate)` | `-> bool` | Check all match |
| `any(predicate)` | `-> bool` | Check any match |
| `position(predicate)` | `-> int \| None` | Find index of first match |
| `nth(n)` | `-> T \| None` | Get nth element |
| `last()` | `-> T \| None` | Get last element |
| `for_each(fn)` | `-> None` | Apply function to each |
| `partition(predicate)` | `-> tuple[list, list]` | Split into two lists |

---

### Iterator Adapters

18 standalone adapter types for lazy evaluation.

```python
from oxide import (
    Enumerate, Zip, Map, FilterIter, FilterMap, FlatMap, Flatten,
    Peekable, Fuse, Chain, Cycle, Take, Skip, Rev, Inspect,
    Copied, Cloned, Partition,
)
```

| Adapter | Description |
|---------|-------------|
| `Enumerate(iterable, start)` | Add index to each element |
| `Zip(a, b)` | Pair elements from two iterables |
| `Map(iterable, fn)` | Transform each element |
| `FilterIter(iterable, pred)` | Keep matching elements |
| `FilterMap(iterable, fn)` | Filter and transform in one pass |
| `FlatMap(iterable, fn)` | Map and flatten |
| `Flatten(iterable)` | Flatten nested iterables |
| `Peekable(iterable)` | Look ahead without consuming |
| `Fuse(iterable)` | Stop after first None |
| `Chain(a, b)` | Concatenate two iterables |
| `Cycle(iterable)` | Repeat indefinitely |
| `Take(iterable, n)` | Take first n elements |
| `Skip(iterable, n)` | Skip first n elements |
| `Rev(iterable)` | Reverse iteration |
| `Inspect(iterable, fn)` | Side effect per element |
| `Copied(iterable)` | Copy elements |
| `Cloned(iterable)` | Clone elements |
| `Partition(iterable, pred)` | Partition into two collections |

---

### Iterator Consumer Functions

Standalone functions that consume iterables.

```python
from oxide.iter.consumers import (
    collect, fold, for_each, count, sum, min, max, any, all,
    find, position, zip, enumerate, chain, peek, step_by,
    skip, take, rev, inspect, copied, cloned, filter, filter_map,
    flat_map, flatten, map,
)
```

---

## Memory Management

### Box

`Box[T]` — Heap-allocated value with automatic cleanup.

```python
from oxide import Box
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new(value)` | Class method | Allocate on heap |
| `from_fn(fn)` | Class method | Allocate with lazy computation |
| `into_inner()` | `-> T` | Unwrap and return value |
| `as_ref()` | `-> T` | Borrow reference |
| `as_mut()` | `-> T` | Borrow mutable reference |
| `leak()` | `-> T` | Leak value (no cleanup) |
| `pin()` | `-> Pin[T]` | Pin the value |

```python
from oxide import Box

b = Box.new(42)
b.as_ref()                 # 42
b.into_inner()             # 42
Box.from_fn(lambda: [1, 2]).as_ref()   # Allocate with lazy computation
Box.new([1, 2, 3]).leak()  # Leak — the value is never freed
Box.new([1]).pin()         # Pin the value

with Box.new([1, 2, 3]) as owned:
    owned.as_ref()         # [1, 2, 3] — dropped at the end of the block
```

---

### Rc

`Rc[T]` — Single-threaded reference-counted shared ownership.

```python
from oxide import Rc, Weak
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new(value)` | Class method | Create new reference |
| `clone()` | `-> Rc[T]` | Increment reference count |
| `downgrade()` | `-> Weak[T]` | Create weak reference |
| `strong_count()` | `-> int` | Get strong reference count |
| `weak_count()` | `-> int` | Get weak reference count |
| `try_unwrap()` | `-> T \| None` | Try to unwrap (if sole owner) |
| `as_ptr()` | `-> int` | Get pointer identity |
| `into_inner()` | `-> T` | Unwrap value |

**`Weak[T]`** — Non-owning reference that doesn't prevent cleanup.

| Method | Signature | Description |
|--------|-----------|-------------|
| `upgrade()` | `-> Rc[T] \| None` | Upgrade to strong reference |
| `strong_count()` | `-> int` | Get strong count |
| `is_alive()` | `-> bool` | Check if value is alive |

---

### Arc

`Arc[T]` — Thread-safe reference-counted shared ownership.

```python
from oxide import Arc
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new(value)` | Class method | Create new reference |
| `clone()` | `-> Arc[T]` | Thread-safe increment |
| `strong_count()` | `-> int` | Get strong count |
| `try_unwrap()` | `-> T \| None` | Try to unwrap |
| `as_ptr()` | `-> int` | Get pointer identity |
| `into_inner()` | `-> T` | Unwrap value |
| `make_mut()` | `-> T` | Get mutable reference |

---

### Cell

`Cell[T]` — Interior mutability for Copy types.

```python
from oxide import Cell
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new(value)` | Class method | Create new cell |
| `get()` | `-> T` | Get value (Copy semantics) |
| `set(value)` | `-> None` | Set value |
| `replace(value)` | `-> T` | Replace and return old value |
| `swap(other)` | `-> None` | Swap with another cell |
| `take()` | `-> T` | Take value (leaves None) |
| `into_inner()` | `-> T` | Unwrap value |

```python
from oxide import Cell
c = Cell.new(5)
c.set(10)
print(c.get())  # 10
```

---

### RefCell

`RefCell[T]` — Runtime borrow-checked interior mutability.

```python
from oxide import RefCell, Ref, RefMut
```

**`RefCell[T]`**

| Method | Signature | Description |
|--------|-----------|-------------|
| `new(value)` | Class method | Create new ref cell |
| `borrow()` | `-> Ref[T]` | Immutably borrow (panics if mutably borrowed) |
| `try_borrow()` | `-> Ref[T] \| None` | Try immutable borrow |
| `borrow_mut()` | `-> RefMut[T]` | Mutably borrow (panics if borrowed) |
| `try_borrow_mut()` | `-> RefMut[T] \| None` | Try mutable borrow |
| `replace(value)` | `-> T` | Replace value |
| `swap(other)` | `-> None` | Swap with another RefCell |
| `into_inner()` | `-> T` | Unwrap value |

**`Ref[T]`** — Immutable borrow guard.

- `value` property: Access the borrowed value
- Supports comparison operators (`==`, `<`, etc.)
- Context manager protocol supported

**`RefMut[T]`** — Mutable borrow guard.

- `value` property (read/write): Access and modify the value
- `replace(v)`: Replace the value
- Context manager protocol supported

```python
from oxide import BorrowMutError, RefCell
cell = RefCell.new(42)

# Multiple immutable borrows
with cell.borrow() as r:
    print(r.value)  # 42

# Single mutable borrow
with cell.borrow_mut() as mut:
    mut.value = 100

# Runtime borrow checking
try:
    r1 = cell.borrow()
    r2 = cell.borrow_mut()  # Raises BorrowMutError
except BorrowMutError:
    pass
```

---

### OnceCell

`OnceCell[T]` — Cell that can be initialized exactly once.

```python
from oxide import OnceCell
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new()` | Class method | Create uninitialized cell |
| `with_value(value)` | Class method | Create pre-initialized cell |
| `get()` | `-> T \| None` | Get value if initialized |
| `set(value)` | `-> bool` | Initialize (returns `False` if already set) |
| `get_or_init(fn)` | `-> T` | Get or initialize with function |
| `try_into_inner()` | `-> T \| None` | Try to unwrap |
| `is_initialized()` | `-> bool` | Check if initialized |

```python
from oxide import OnceCell

cell = OnceCell.new()
cell.get()                          # None before initialisation
cell.get_or_init(lambda: {"config": "loaded"})
print(cell.get())                   # {'config': 'loaded'}
cell.set({"config": "replaced"})    # False — already initialised
```

---

### Lazy

`Lazy[T]` — Deferred computation, evaluated on first access.

```python
from oxide import Lazy
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new(fn)` | Constructor | Create lazy value |
| `force()` | `-> T` | Compute and return value |
| `is_forced()` | `-> bool` | Check if computed |
| `try_into_inner()` | `-> T \| None` | Try to get if computed |

```python
from oxide import Lazy

lazy = Lazy.new(lambda: sum(range(1000)))
lazy.is_forced()              # False — not computed yet
lazy.force()                  # 499500 — computed on the first call
lazy.force()                  # 499500 — cached from then on
lazy.is_forced()              # True
```

---

### Cow

`Cow[T]` — Copy-on-write abstraction.

```python
from oxide import Cow, CowBorrowed, CowOwned
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `is_borrowed()` | `-> bool` | Check if borrowed |
| `is_owned()` | `-> bool` | Check if owned |
| `as_ref()` | `-> T` | Borrow reference |
| `into_owned()` | `-> T` | Get owned copy (clones if borrowed) |
| `to_owned()` | `-> T` | Alias for `into_owned` |
| `map(fn)` | `-> Cow[U]` | Transform value |
| `unwrap()` | `-> T` | Unwrap value |

```python
from oxide import Cow, CowBorrowed, CowOwned

# Efficient: no copy while only reading
data = CowBorrowed([1, 2, 3])
data.is_borrowed()            # True
data.as_ref()                 # [1, 2, 3] — no copy
data.into_owned()             # [1, 2, 3] — a detached copy, `data` unchanged
data.map(lambda v: v + [4])   # a new Cow of the *same* variant
CowOwned([1, 2]).is_owned()   # True
```

---

### Pin

`Pin[T]` — Pinned reference preventing moves.

```python
from oxide import Pin, ManuallyDrop, MaybeUninit, NonNull, PhantomData
```

**`Pin[T]`** — Prevents value from being moved.

| Method | Signature | Description |
|--------|-----------|-------------|
| `new(value)` | Class method | Pin a value |
| `as_ref()` | `-> T` | Get reference |
| `as_mut()` | `-> T` | Get mutable reference |
| `into_inner()` | `-> T` | Unpin and return |
| `is_pinned()` | `-> bool` | Check if pinned |

**`ManuallyDrop[T]`** — Control when value is dropped.

| Method | Signature | Description |
|--------|-----------|-------------|
| `new(value)` | Class method | Wrap value |
| `drop()` | `-> None` | Explicitly drop |
| `is_dropped()` | `-> bool` | Check if dropped |

**`MaybeUninit[T]`** — Handle uninitialized memory.

| Method | Signature | Description |
|--------|-----------|-------------|
| `new()` | Class method | Create uninitialized |
| `init(value)` | Class method | Create initialized |
| `assume_init()` | `-> T` | Get value (must be initialized) |
| `write(value)` | `-> T` | Initialize and return |
| `is_initialized()` | `-> bool` | Check if initialized |

**`NonNull[T]`** — Non-null pointer wrapper.

| Method | Signature | Description |
|--------|-----------|-------------|
| `new(value)` | Class method | Create (raises if `None`) |
| `as_ref()` | `-> T` | Get reference |
| `as_mut()` | `-> T` | Get mutable reference |
| `replace(value)` | `-> T` | Replace and return old |
| `is_null()` | `-> bool` | Always returns `False` |

**`PhantomData[T]`** — Zero-sized type marker.

**`Borrow[T]`** / **`BorrowMut[T]`** — Borrowing trait implementations.

---

## Concurrency

### Mutex

`Mutex[T]` — Mutual exclusion lock with `MutexGuard`.

```python
from oxide import Mutex, MutexGuard
```

**`Mutex[T]`**

| Method | Signature | Description |
|--------|-----------|-------------|
| `new(value)` | Class method | Create mutex-protected value |
| `lock()` | `-> MutexGuard` | Acquire lock |
| `try_lock()` | `-> MutexGuard \| None` | Try to acquire lock |
| `into_inner()` | `-> T` | Unwrap value |
| `is_poisoned()` | `-> bool` | Check if poisoned |
| `poison()` | `-> None` | Poison the mutex |
| `clear_poison()` | `-> None` | Clear poison state |

**`MutexGuard`** — RAII lock guard.

- `value` property: Access protected value
- `replace(v)`: Replace value
- `release()`: Release lock early

```python
from oxide import Mutex
counter = Mutex.new(0)

def increment():
    with counter:
        counter._value += 1

# Or explicit locking
guard = counter.lock()
guard.value += 1
guard.release()
```

---

### RwLock

`RwLock[T]` — Readers-writer lock for concurrent reads with exclusive writes.

```python
from oxide import RwLock, RwLockReadGuard, RwLockWriteGuard
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new(value)` | Class method | Create lock-protected value |
| `read()` | `-> RwLockReadGuard` | Acquire read lock |
| `write()` | `-> RwLockWriteGuard` | Acquire write lock |
| `try_read()` | `-> RwLockReadGuard \| None` | Try to acquire read lock |
| `try_write()` | `-> RwLockWriteGuard \| None` | Try to acquire write lock |
| `into_inner()` | `-> T` | Unwrap value |

```python
from oxide import RwLock

data = RwLock.new([1, 2, 3])

# Multiple readers can hold locks simultaneously
with data.read() as r:
    print(r.value)

# Writers get exclusive access
with data.write() as w:
    w.value.append(4)
print(data.into_inner())   # [1, 2, 3, 4]
```

---

### Channel

`Channel[T]` — Multi-producer single-consumer message passing.

```python
from oxide import Channel, Sender, Receiver
```

**`Channel[T]`**

| Method | Signature | Description |
|--------|-----------|-------------|
| `unbounded()` | Class method | Create unbounded channel |
| `bounded(capacity)` | Class method | Create bounded channel |
| `sender` | Property | Get sender handle |
| `receiver` | Property | Get receiver handle |
| `send(value)` | `-> bool` | Send a value |
| `recv()` | `-> T \| None` | Receive a value |

**`Sender[T]`**

| Method | Signature | Description |
|--------|-----------|-------------|
| `send(value)` | `-> bool` | Send a value |
| `is_closed()` | `-> bool` | Check if closed |
| `close()` | `-> None` | Close sender |

**`Receiver[T]`**

| Method | Signature | Description |
|--------|-----------|-------------|
| `recv()` | `-> T \| None` | Non-blocking receive |
| `recv_blocking(timeout)` | `-> T \| None` | Blocking receive |
| `try_recv()` | `-> T \| None` | Try to receive |
| `is_empty()` | `-> bool` | Check if empty |

```python
from oxide import Channel
ch = Channel.bounded(10)
sender, receiver = ch.sender, ch.receiver

# Send from any thread
sender.send("hello")

# Receive (blocking or non-blocking)
msg = receiver.recv()
msg = receiver.recv_blocking(timeout=5.0)
```

---

### Atomic

`Atomic[T]`, `AtomicBool`, `AtomicInt` — Lock-free thread-safe primitives.

```python
from oxide import Atomic, AtomicBool, AtomicInt
```

**`AtomicBool`**

| Method | Signature | Description |
|--------|-----------|-------------|
| `new(value)` | Class method | Create with initial value |
| `load()` | `-> bool` | Load value |
| `store(value)` | `-> None` | Store value |
| `swap(value)` | `-> bool` | Swap and return old |
| `compare_and_set(current, new)` | `-> bool` | CAS operation |
| `fetch_and(value)` | `-> bool` | AND and return old |
| `fetch_or(value)` | `-> bool` | OR and return old |
| `fetch_xor(value)` | `-> bool` | XOR and return old |

**`AtomicInt`**

| Method | Signature | Description |
|--------|-----------|-------------|
| `new(value)` | Class method | Create with initial value |
| `load()` | `-> int` | Load value |
| `store(value)` | `-> None` | Store value |
| `swap(value)` | `-> int` | Swap and return old |
| `fetch_add(value)` | `-> int` | Add and return old |
| `fetch_sub(value)` | `-> int` | Subtract and return old |
| `fetch_and(value)` | `-> int` | AND and return old |
| `fetch_or(value)` | `-> int` | OR and return old |
| `fetch_xor(value)` | `-> int` | XOR and return old |
| `compare_and_set(current, new)` | `-> bool` | CAS operation |

```python
from oxide import AtomicInt
counter = AtomicInt.new(0)

def increment():
    counter.fetch_add(1)

# Thread-safe operations
print(counter.load())  # Atomic read
counter.store(42)       # Atomic write
```

---

### Barrier

`Barrier` — Blocks until N threads arrive.

```python
from oxide import Barrier
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new(count)` | Constructor | Create barrier for N threads |
| `wait()` | `-> int` | Wait for all threads (returns 0 for last) |

```python
from oxide import Barrier
barrier = Barrier(3)

def worker():
    do_work()
    barrier.wait()  # Blocks until all 3 threads arrive
    do_more_work()
```

---

### Condvar

`Condvar` — Condition variable for thread coordination.

```python
from oxide import Condvar
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new()` | Class method | Create condition variable |
| `wait(lock)` | `-> None` | Wait on condition |
| `wait_while(predicate, lock)` | `-> None` | Wait while condition is true |
| `notify_one()` | `-> None` | Wake one waiting thread |
| `notify_all()` | `-> None` | Wake all waiting threads |

```python
from oxide import Condvar
cond = Condvar.new()
ready = False

def producer():
    global ready
    ready = True
    cond.notify_one()

def consumer():
    with cond:
        cond.wait_while(lambda: not ready)
        process()
```

---

### Once

`Once` — Execute a function exactly once across threads.

```python
from oxide import Once
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new()` | Class method | Create new Once |
| `call_once(fn)` | `-> T` | Execute function (only first call) |
| `is_completed()` | `-> bool` | Check if executed |

```python
from oxide import Once
init_once = Once.new()

def initialize():
    init_once.call_once(expensive_setup)
```

---

### Semaphore

`Semaphore` — Counting semaphore for concurrency limiting.

```python
from oxide import Semaphore
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new(max_permits)` | Class method | Create with max concurrent |
| `acquire(blocking, timeout)` | `-> bool` | Acquire permit |
| `release()` | `-> None` | Release permit |
| `available()` | `-> int` | Get available permits |

```python
from oxide import Semaphore
sem = Semaphore.new(5)  # Max 5 concurrent

def task():
    with sem:
        limited_resource()
```

---

## Time

### Duration

`Duration` — A span of time with arithmetic operations.

```python
from oxide import Duration, UNIX_EPOCH
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `from_secs(secs)` | Class method | Create from seconds |
| `from_millis(millis)` | Class method | Create from milliseconds |
| `from_micros(micros)` | Class method | Create from microseconds |
| `from_nanos(nanos)` | Class method | Create from nanoseconds |
| `from_minutes(minutes)` | Class method | Create from minutes |
| `from_hours(hours)` | Class method | Create from hours |
| `from_days(days)` | Class method | Create from days |
| `zero()` | Class method | Zero duration |
| `as_secs()` | `-> int` | Get seconds |
| `as_millis()` | `-> int` | Get milliseconds |
| `as_nanos()` | `-> int` | Get nanoseconds |
| `secs_f64()` | `-> float` | Get seconds as float |
| `is_zero()` | `-> bool` | Check if zero |
| `checked_add(other)` | `-> Duration \| None` | Checked addition |
| `checked_sub(other)` | `-> Duration \| None` | Checked subtraction |
| `saturating_add(other)` | `-> Duration` | Saturating addition |
| `saturating_sub(other)` | `-> Duration` | Saturating subtraction |
| `mul(rhs)` | `-> Duration` | Multiply by scalar |
| `div(rhs)` | `-> Duration` | Divide by scalar |

```python
from oxide import Duration
d = Duration.from_secs(5) + Duration.from_millis(500)
print(d.as_millis())  # 5500
```

---

### Instant

`Instant` — Monotonic timestamp for measuring elapsed time.

```python
from oxide import Instant
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `now()` | Class method | Get current instant |
| `elapsed()` | `-> Duration` | Time since this instant |
| `checked_elapsed()` | `-> Duration \| None` | Checked elapsed time |
| `duration_since(earlier)` | `-> Duration` | Duration between instants |
| `checked_duration_since(earlier)` | `-> Duration \| None` | Checked duration |
| `saturating_duration_since(earlier)` | `-> Duration` | Saturating duration |
| `add_duration(duration)` | `-> Instant` | Add duration |
| `as_secs()` | `-> float` | Get as seconds |
| `as_millis()` | `-> int` | Get as milliseconds |

```python
from oxide import Instant

start = Instant.now()
elapsed = start.elapsed()      # 0.0 ms — measured against now
print(f"Took {elapsed.as_millis()}ms")
```

---

### SystemTime

`SystemTime` — Wall-clock time with datetime conversion.

```python
from oxide import SystemTime
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `now()` | Class method | Get current time |
| `from_secs(secs, nanos)` | Class method | Create from epoch seconds |
| `duration_since(earlier)` | `-> Duration` | Duration between times |
| `checked_duration_since(earlier)` | `-> Duration \| None` | Checked duration |
| `saturating_duration_since(earlier)` | `-> Duration` | Saturating duration |
| `add_duration(duration)` | `-> SystemTime` | Add duration |
| `from_epoch()` | `-> Duration` | Time since epoch |
| `to_datetime()` | `-> datetime` | Convert to Python datetime |

---

## I/O

### Read

`Read` — Byte reading trait.

```python
from oxide import Read, BufRead
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `read(buf)` | `-> int` | Read into buffer |
| `read_exact(buf)` | `-> None` | Read exactly len(buf) bytes |
| `read_to_end()` | `-> bytes` | Read all remaining bytes |
| `read_to_string()` | `-> str` | Read all as UTF-8 string |

**`BufRead`** — Buffered reading trait.

| Method | Signature | Description |
|--------|-----------|-------------|
| `fill_buf()` | `-> bytes` | Fill internal buffer |
| `consume(amt)` | `-> None` | Consume bytes from buffer |
| `read_until(byte)` | `-> bytes` | Read until byte |
| `read_line()` | `-> str` | Read until newline |
| `split(byte)` | `-> BufSplitIter` | Split on byte |
| `lines()` | `-> LinesIter` | Iterate over lines |

---

### Write

`Write` — Byte and string writing trait.

```python
from oxide import Write
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `write(data)` | `-> int` | Write data |
| `write_all(data)` | `-> None` | Write all data |
| `flush()` | `-> None` | Flush buffer |

---

### BufReader

`BufReader` — Buffered reader with configurable capacity.

```python
from oxide import BufReader
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `with_capacity(capacity, inner)` | Class method | Create with custom capacity |
| `inner()` | `-> Any` | Get inner reader |
| `into_inner()` | `-> Any` | Consume and get inner |
| `buffer()` | `-> bytes` | Get buffered data |
| `capacity()` | `-> int` | Get buffer capacity |
| `fill_buf()` | `-> bytes` | Fill and return buffer |
| `consume(amt)` | `-> None` | Consume bytes |
| `read(buf)` | `-> int` | Read into buffer |
| `seek(style)` | `-> int` | Seek position |

---

### BufWriter

`BufWriter` — Buffered writer with automatic flushing.

```python
from oxide import BufWriter
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `with_capacity(capacity, inner)` | Class method | Create with custom capacity |
| `inner()` | `-> Any` | Get inner writer |
| `into_inner()` | `-> Any` | Flush and consume |
| `write(data)` | `-> int` | Write data |
| `write_all(data)` | `-> None` | Write all data |
| `flush()` | `-> None` | Flush buffer |

---

### Cursor

`Cursor[T]` — In-memory Read+Write+Seek operations.

```python
from oxide import Cursor, SeekFrom
```

**`Cursor[T]`**

| Method | Signature | Description |
|--------|-----------|-------------|
| `new(data)` | Class method | Create from data |
| `position()` | `-> int` | Get current position |
| `set_position(pos)` | `-> None` | Set position |
| `read(buf)` | `-> int` | Read from cursor |
| `write(data)` | `-> int` | Write at position |
| `seek(style)` | `-> int` | Seek position |
| `remaining()` | `-> int` | Bytes remaining |
| `is_empty()` | `-> bool` | Check if empty |

**`SeekFrom`** — Seek position specification.

```python
from oxide import SeekFrom
SeekFrom.start(0)      # From beginning
SeekFrom.current(0)    # From current position
SeekFrom.end(0)        # From end
```

---

## Filesystem

### Path

`Path` — Immutable filesystem path.

```python
from oxide import Path
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new(path)` | Class method | Create from string |
| `as_str()` | `-> str` | Get as string |
| `to_path_buf()` | `-> PathBuf` | Convert to mutable PathBuf |
| `is_absolute()` | `-> bool` | Check if absolute |
| `is_relative()` | `-> bool` | Check if relative |
| `parent()` | `-> Path \| None` | Get parent directory |
| `file_name()` | `-> str \| None` | Get file name |
| `extension()` | `-> str \| None` | Get extension |
| `file_stem()` | `-> str \| None` | Get file name without extension |
| `with_extension(ext)` | `-> Path` | Change extension |
| `join(other)` | `-> Path` | Join paths |
| `exists()` | `-> bool` | Check if exists |
| `is_file()` | `-> bool` | Check if file |
| `is_dir()` | `-> bool` | Check if directory |
| `metadata()` | `-> Metadata` | Get metadata |
| `canonicalize()` | `-> Path` | Resolve symlinks |
| `read_to_string()` | `-> str` | Read file as string |
| `read_to_bytes()` | `-> bytes` | Read file as bytes |
| `write_str(data)` | `-> None` | Write string to file |
| `write_bytes(data)` | `-> None` | Write bytes to file |
| `create_dir()` | `-> None` | Create directory |
| `create_dir_all()` | `-> None` | Create directory recursively |
| `remove_file()` | `-> None` | Remove file |
| `remove_dir()` | `-> None` | Remove directory |
| `remove_dir_all()` | `-> None` | Remove directory recursively |
| `rename(to)` | `-> None` | Rename/move |
| `copy(to)` | `-> None` | Copy file |
| `read_dir()` | `-> ReadDir` | Read directory contents |

```python
from oxide import Path
p = Path("/tmp/data")
p.create_dir_all()
(p / "file.txt").write_str("hello")
print((p / "file.txt").read_to_string())
```

---

### PathBuf

`PathBuf` — Mutable filesystem path.

```python
from oxide import PathBuf
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `new()` | Class method | Create empty path |
| `from_str(s)` | Class method | Create from string |
| `as_path()` | `-> Path` | Convert to immutable Path |
| `as_str()` | `-> str` | Get as string |
| `push(path)` | `-> None` | Append path component |
| `push_str(s)` | `-> None` | Append string component |
| `pop()` | `-> bool` | Remove last component |
| `set_extension(ext)` | `-> bool` | Set extension |
| `clear()` | `-> None` | Clear path |

---

### File

`File` — File I/O with configurable open modes.

```python
from oxide import File, OpenOptions
```

**`File`**

| Method | Signature | Description |
|--------|-----------|-------------|
| `create(path)` | Class method | Create/truncate file |
| `create_new(path)` | Class method | Create new (error if exists) |
| `open(path)` | Class method | Open for reading |
| `options()` | Class method | Get OpenOptions builder |
| `read()` | `-> bytes` | Read all bytes |
| `read_exact(buf)` | `-> int` | Read into buffer |
| `read_to_string()` | `-> str` | Read as string |
| `write(data)` | `-> int` | Write data |
| `write_all(data)` | `-> None` | Write all data |
| `flush()` | `-> None` | Flush to disk |
| `seek(pos)` | `-> int` | Seek to position |
| `stream_position()` | `-> int` | Get current position |
| `metadata()` | `-> Metadata` | Get file metadata |
| `path()` | `-> Path` | Get file path |
| `try_clone()` | `-> File` | Duplicate file handle |

**`OpenOptions`** — Builder for file open modes.

```python
from oxide import OpenOptions
file = (OpenOptions.new()
    .read(True)
    .write(True)
    .create(True)
    .open("data.txt"))
```

---

### Metadata

`Metadata`, `Permissions`, `FileType`, `DirEntry`, `ReadDir` — Filesystem information.

| Class | Description |
|-------|-------------|
| `Metadata` | File type, size, timestamps |
| `Permissions` | Read-only status |
| `FileType` | File, directory, or symlink |
| `DirEntry` | Directory entry with lazy metadata |
| `ReadDir` | Iterator over directory contents |

---

## Networking

### TcpStream

`TcpStream` — TCP client connection.

```python
from oxide import TcpStream
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `connect(addr)` | Class method | Connect to address |
| `connect_timeout(addr, timeout)` | Class method | Connect with timeout |
| `peer_addr()` | `-> SocketAddr \| None` | Get peer address |
| `local_addr()` | `-> SocketAddr \| None` | Get local address |
| `shutdown(how)` | `-> None` | Shutdown connection |
| `set_nodelay(nodelay)` | `-> None` | Set TCP_NODELAY |
| `set_nonblocking(nonblocking)` | `-> None` | Set non-blocking mode |
| `read(buf)` | `-> int` | Read into buffer |
| `write(data)` | `-> int` | Write data |
| `write_all(data)` | `-> None` | Write all data |
| `try_clone()` | `-> TcpStream` | Duplicate socket |

---

### TcpListener

`TcpListener` — TCP server socket.

```python
from oxide import TcpListener
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `bind(addr)` | Class method | Bind and listen |
| `accept()` | `-> tuple[TcpStream, SocketAddr]` | Accept connection |
| `accept_timeout(timeout)` | `-> tuple[TcpStream, SocketAddr] \| None` | Accept with timeout |
| `incoming()` | `-> Incoming` | Iterator of connections |
| `local_addr()` | `-> SocketAddr \| None` | Get local address |

```python
from oxide import SocketAddr, TcpListener

# bind() needs a SocketAddr, not a string
listener = TcpListener.bind(SocketAddr.from_str("127.0.0.1:0"))
print(listener.local_addr())
```

---

### UdpSocket

`UdpSocket` — UDP datagram socket.

```python
from oxide import UdpSocket
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `bind(addr)` | Class method | Bind to address |
| `local_addr()` | `-> SocketAddr \| None` | Get local address |
| `send_to(buf, target)` | `-> int` | Send datagram |
| `recv_from(buf_size)` | `-> tuple[bytes, SocketAddr]` | Receive datagram |
| `connect(addr)` | `-> None` | Connect to address |
| `set_broadcast(on)` | `-> None` | Enable broadcast |
| `set_ttl(ttl)` | `-> None` | Set time-to-live |

---

### Address Types

```python
from oxide import Ipv4Addr, Ipv6Addr, IpAddr, SocketAddr, Shutdown
```

**`Ipv4Addr`**

```python
from oxide import Ipv4Addr
addr = Ipv4Addr(127, 0, 0, 1)  # or
addr = Ipv4Addr.from_str("127.0.0.1")
addr = Ipv4Addr.localhost()
```

| Method | Description |
|--------|-------------|
| `octets()` | Get octets tuple |
| `to_str()` | Get string representation |
| `to_bytes()` | Get bytes |
| `is_loopback()` | Check if loopback |
| `is_private()` | Check if private network |
| `is_multicast()` | Check if multicast |

**`Ipv6Addr`** — Similar API for IPv6.

**`IpAddr`** — Union of IPv4 and IPv6.

```python
from oxide import IpAddr, Ipv4Addr, Ipv6Addr

IpAddr.v4(Ipv4Addr(127, 0, 0, 1))   # 127.0.0.1
IpAddr.v6(Ipv6Addr.localhost())     # ::1
```

**`SocketAddr`** — IP address with port.

```python
from oxide import Ipv4Addr, SocketAddr

SocketAddr.new_v4(Ipv4Addr(127, 0, 0, 1), 8080)   # 127.0.0.1:8080
SocketAddr.from_str("127.0.0.1:8080")              # 127.0.0.1:8080
```

---

## Process

### Command

`Command` — Build and spawn child processes.

```python
from oxide import Command, Stdio
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `Command(program)` | Constructor | Create command |
| `arg(arg)` | `-> Command` | Add argument |
| `args(args)` | `-> Command` | Add multiple arguments |
| `env(key, val)` | `-> Command` | Set environment variable |
| `envs(envs)` | `-> Command` | Set multiple env vars |
| `current_dir(dir)` | `-> Command` | Set working directory |
| `stdin(cfg)` | `-> Command` | Configure stdin |
| `stdout(cfg)` | `-> Command` | Configure stdout |
| `stderr(cfg)` | `-> Command` | Configure stderr |
| `spawn()` | `-> Child` | Spawn process |
| `output()` | `-> Output` | Run and capture output |
| `status()` | `-> ExitStatus` | Run and get status |

```python
from oxide import Command

output = Command("ls").arg("-la").current_dir("/tmp").output()
print(output.stdout_str())
```

---

### Child

`Child` — Handle to a running process.

```python
from oxide import Child, Stdio
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `id()` | `-> int` | Get process ID |
| `kill()` | `-> None` | Kill process |
| `wait()` | `-> ExitStatus` | Wait for completion |
| `wait_with_output()` | `-> Output` | Wait and get output |
| `try_wait()` | `-> ExitStatus \| None` | Non-blocking wait |
| `wait_timeout(secs)` | `-> ExitStatus \| None` | Wait with timeout |

**`Stdio`** — Standard stream configuration.

```python
from oxide import Stdio
Stdio.inherit()    # Inherit from parent
Stdio.piped()      # Create pipe
Stdio.null()       # Discard output
Stdio.from_path("out.txt")  # Redirect to a file
```

---

### ExitStatus

`ExitStatus`, `Output`, `ExitCode` — Process output types.

**`ExitStatus`**

| Method | Description |
|--------|-------------|
| `code()` | Get exit code |
| `success()` | Check if successful |
| `signal()` | Get signal if killed |

**`Output`**

| Method | Description |
|--------|-------------|
| `status()` | Get exit status |
| `stdout()` | Get stdout bytes |
| `stderr()` | Get stderr bytes |
| `stdout_str()` | Get stdout as string |
| `stderr_str()` | Get stderr as string |

#### OS Utility Functions

```python
from oxide import args, env, current_dir, current_exe, home_dir, temp_dir

args()           # Get command line arguments
env("KEY")       # Get environment variable
current_dir()    # Get current working directory
current_exe()    # Get executable path
home_dir()       # Get home directory
temp_dir()       # Get temporary directory
```

---

## Async

### Future

`Future[T]` — Async computation.

```python
from oxide import Future, Poll, Waker, spawn
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `ready(value)` | Class method | Create completed future |
| `pending()` | Class method | Create pending future |
| `poll(waker)` | `-> Poll[T]` | Check completion status |
| `is_done()` | `-> bool` | Check if completed |
| `result()` | `-> T \| None` | Get result if done |
| `add_done_callback(fn)` | `-> None` | Add completion callback |
| `set_result(value)` | `-> None` | Complete with value |
| `set_exception(exc)` | `-> None` | Complete with error |
| `map(fn)` | `-> Future[U]` | Transform result |
| `and_then(fn)` | `-> Future[U]` | Chain futures |

```python
import asyncio
from oxide import Future

async def fetch_data() -> str:
    return "data"

async def main() -> None:
    print(await Future(fetch_data()))     # 'data'
    print(Future.ready(7).result())      # 7 — already resolved
    pending = Future.pending()
    print(pending.result(), pending.is_done())   # None False
    print(pending.poll())                # Poll::Pending

asyncio.run(main())
```

> `Future.map()` and `Future.and_then()` build a *new coroutine*, not a resolved
> `Future`, so call `.result()` on them and you get `None` — `await` the mapped
> future (or drive it through an event loop) instead.

---

### Poll

`Poll[T]` — Pending/Ready state for async operations.

```python
from oxide import Poll
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `ready(value)` | Class method | Ready with value |
| `pending()` | Class method | Not ready |
| `is_ready()` | `-> bool` | Check if ready |
| `is_pending()` | `-> bool` | Check if pending |
| `unwrap()` | `-> T` | Get value (panics if pending) |
| `unwrap_or(default)` | `-> T` | Get value or default |
| `map(fn)` | `-> Poll[U]` | Transform if ready |
| `and_then(fn)` | `-> Poll[U]` | Chain if ready |

---

### Stream

`Stream[T]` — Async iterator.

```python
from oxide import Stream
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `from_iter(iterable)` | Class method | Create from sync iterable |
| `from_async_iter(async_iter)` | Class method | Create from async iterable |
| `empty()` | Class method | Empty stream |
| `once(value)` | Class method | Single value stream |
| `repeat(value)` | Class method | Infinite repetition |
| `chain(*streams)` | Class method | Chain streams |
| `next()` | `-> T \| None` | Get next value |
| `map(fn)` | `-> Stream[U]` | Transform elements |
| `filter(predicate)` | `-> Stream[T]` | Filter elements |
| `take(n)` | `-> Stream[T]` | Take first n |
| `collect()` | `-> list[T]` | Collect all values |
| `fold(init, fn)` | `-> U` | Fold to single value |
| `for_each(fn)` | `-> None` | Apply to all |
| `count()` | `-> int` | Count elements |

---

### JoinHandle

`JoinHandle[T]` — Handle to a spawned task.

```python
from oxide import JoinHandle, spawn
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `run()` | `-> None` | Run synchronously |
| `start()` | `-> None` | Run in background thread |
| `is_finished()` | `-> bool` | Check if done |
| `is_running()` | `-> bool` | Check if running |
| `abort()` | `-> bool` | Try to abort |
| `get_result(timeout)` | `-> T \| None` | Get result |
| `join(timeout)` | `-> T \| None` | Wait for completion |

```python
import asyncio
from oxide import spawn

async def fetch_data() -> str:
    return "data"

handle = spawn(fetch_data())     # Runs on a daemon thread
print(handle.join())             # 'data' — blocks until done
print(handle.get_result())       # 'data'
```

---

## Macros

### Assertions

```python
from oxide import assert_eq, assert_ne, assert_, debug_assert, debug_assert_eq, debug_assert_ne
```

| Function | Description |
|----------|-------------|
| `assert_(condition, message)` | Assert condition is true |
| `assert_eq(a, b, message)` | Assert equality |
| `assert_ne(a, b, message)` | Assert inequality |
| `debug_assert(condition, message)` | Debug-only assert |
| `debug_assert_eq(a, b, message)` | Debug-only equality assert |
| `debug_assert_ne(a, b, message)` | Debug-only inequality assert |

---

### Debugging

```python
from oxide import Formatter, format_, write_, writeln_, dbg_, dbg, cfg, matches
```

| Function | Description |
|----------|-------------|
| `dbg(value)` | Print debug info with location |
| `dbg_(*args)` | Print debug info (alternate) |
| `format_(template, *args)` | String formatting |
| `write_(buf, template, *args)` | Write formatted to buffer |
| `writeln_(buf, template, *args)` | Write with newline |
| `cfg(key)` | Get config from environment |
| `matches(value, pattern)` | Pattern matching |
| `option_env(key)` | Get env var or None |
| `include_str(path)` | Include file as string |
| `include_bytes(path)` | Include file as bytes |

**`Formatter`** — Buffer for building formatted strings.

```python
from oxide import Formatter
f = Formatter()
f.write_str("Hello")
f.write_char(" ")
f.write_fmt("World")
print(f.finish())  # "Hello World"
```

---

### Panic

```python
from oxide import panic, todo, unimplemented, ScopeGuard, defer
```

| Function | Description |
|----------|-------------|
| `panic(message)` | Raise `PanicError` with backtrace |
| `todo(message)` | Raise `UnimplementedError` |
| `unimplemented(message)` | Raise `UnimplementedError` |
| `defer(fn)` | RAII cleanup guard |

**`ScopeGuard`** — RAII-style cleanup.

```python
from oxide import ScopeGuard, defer

def cleanup() -> None:
    print("cleaned up")

def do_work() -> None:
    print("working")

with defer(cleanup):
    do_work()          # 'working' then 'cleaned up' on exit

guard = ScopeGuard(cleanup)
guard.cancel()         # Prevent execution
```

---

## Miscellaneous

### Ordering

`Ordering` — Comparison result.

```python
from oxide import Ordering
```

| Constant | Value | Description |
|----------|-------|-------------|
| `Ordering.less()` | -1 | Less than |
| `Ordering.equal()` | 0 | Equal |
| `Ordering.greater()` | 1 | Greater than |

| Method | Description |
|--------|-------------|
| `from_cmp(a, b)` | Create from comparison |
| `reverse()` | Get opposite ordering |
| `then(other)` | Chain comparisons |
| `then_with(f)` | Chain with function |
| `is_less()` | Check if less |
| `is_equal()` | Check if equal |
| `is_greater()` | Check if greater |

---

### ControlFlow

`ControlFlow` — Break/Continue control flow.

```python
from oxide import ControlFlow
```

| Method | Description |
|--------|-------------|
| `cont(value)` | Continue with value |
| `brk(value)` | Break with value |
| `is_break()` | Check if break |
| `is_continue()` | Check if continue |
| `break_value()` | Get break value |
| `continue_value()` | Get continue value |
| `map_break(f)` | Transform break value |
| `map_continue(f)` | Transform continue value |

---

### Arithmetic Wrappers

**`Reverse[T]`** — Reversed ordering wrapper.

**`Wrapping[T]`** — Wrapping arithmetic (overflow wraps).

```python
from oxide import Wrapping
w = Wrapping(255) + 1  # Wrapping(0)
```

| Method | Description |
|--------|-------------|
| `wrapping_add(other)` | Wrapping addition |
| `wrapping_sub(other)` | Wrapping subtraction |
| `wrapping_mul(other)` | Wrapping multiplication |
| `wrapping_div(other)` | Wrapping division |
| `wrapping_neg()` | Wrapping negation |

**`Saturating[T]`** — Saturating arithmetic (clamps at bounds).

```python
from oxide import Saturating
s = Saturating(2**31 - 1) + 1  # Saturating(2**31 - 1)
```

| Method | Description |
|--------|-------------|
| `saturating_add(other)` | Saturating addition |
| `saturating_sub(other)` | Saturating subtraction |
| `saturating_mul(other)` | Saturating multiplication |

**`NonZero[T]`** — Non-zero numeric wrapper.

```python
from oxide import NonZero
nz = NonZero.new(5)      # Create (raises if 0)
nz = NonZero.try_new(0)  # Returns None if 0
```

---

### Specialized Vectors

**`SmallVec[T]`** — Stack-optimized small vector.

```python
from oxide import SmallVec
sv = SmallVec([1, 2, 3], stack_limit=8)
```

**`ArrayVec[T]`** — Fixed-capacity vector.

```python
from oxide import ArrayVec
av = ArrayVec.with_capacity(10)
av.push(42)  # Raises OverflowError if full
```

**`TinyVec[T]`** — Inline-to-heap vector.

```python
from oxide import TinyVec
tv = TinyVec()
for i in range(100):
    tv.push(i)  # Moves to heap when inline limit exceeded
```

**`BitVec`** — Bit vector.

```python
from oxide import BitVec
bv = BitVec()
bv.push(True)
bv.push(False)
print(bv.to_bytes())  # b'\x01'
```

---

### CreateMeta

`CreateMeta` — Library metadata (for internal use).

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class CreateMeta:
    libname: str
    libversion: tuple[int, int]
    pyversion: tuple[int, int]
    author: str
    clone: str
    description: str
    license: str
    homepage: str
    keywords: tuple[str, ...]
    python_requires: str
    timestamp: str
```

---

## Regular Expressions

`oxide.regex` is a linear-time engine: patterns compile to a Thompson NFA
simulated by a Pike VM, so matching costs `O(len(text) * len(program))` and
catastrophic backtracking cannot occur. Backreferences, lookaround, atomic and
possessive groups, and unicode property escapes raise `RegexError`, matching
what Rust's `regex` crate rejects.

```python
from oxide import Regex, RegexMatch, RegexError, IGNORECASE
from oxide import regex          # the functions, namespaced

pattern = Regex(r"[a-z]+@[a-z]+\.[a-z]+", IGNORECASE)
match = pattern.search("Ann@Example.COM")   # RegexMatch
match.span(), match.group(), match.groups()
```

### Names

| Name | Description |
|------|-------------|
| `Regex(pattern, flags=0)` | Compiled pattern with `search`/`match`/`fullmatch`/`findall`/`finditer`/`split`/`sub`/`subn` |
| `RegexMatch` | The match object, exported under this name because `Match` at the top level is the enum `match` macro's result |
| `RegexError` | Raised for malformed patterns and unsupported constructs |

### Functions

Available in the `oxide.regex` namespace rather than at the top level, so they
cannot shadow `oxide.match`.

```python
from oxide import regex

pattern = r"(?P<user>[a-z]+)"
string = "ann@example"
repl = r"\g<user>"

regex.compile(pattern, flags=0)     # -> Regex
regex.match(pattern, string, flags=0)
regex.fullmatch(pattern, string, flags=0)
regex.search(pattern, string, flags=0)
regex.findall(pattern, string, flags=0)
regex.finditer(pattern, string, flags=0)
regex.split(pattern, string, maxsplit=0, flags=0)
regex.sub(pattern, repl, string, count=0, flags=0)
regex.subn(pattern, repl, string, count=0, flags=0)
regex.escape(string)
regex.purge()
```

### Flags

| Flag | Alias | Description |
|------|-------|-------------|
| `ASCII` | `A` | `\w`, `\d`, `\s` and `\b` are ASCII-only |
| `IGNORECASE` | `I` | Case-insensitive, folded with simple case mappings |
| `MULTILINE` | `M` | `^` and `$` match at line boundaries |
| `DOTALL` | `S` | `.` also matches newline |
| `UNICODE` | `U` | Unicode semantics (the default) |
| `VERBOSE` | `X` | Ignore whitespace and allow `#` comments |

---

## Validation & Sanitization

`oxide.filter` is a PHP `filter_var()`-style port that returns `Result` values
instead of PHP's `false`/`null` sentinel.

```python
from oxide import Filter, FilterError

Filter.validate("a@b.com", Filter.EMAIL)   # Ok(value='a@b.com')
Filter.validate("nope", Filter.EMAIL)       # Err(FilterError)
Filter.is_valid("https://example.com", Filter.URL)
Filter.sanitize("<b>hi</b>", Filter.SANITIZE_SPECIAL_CHARS)
```

| Method | Description |
|--------|-------------|
| `Filter.validate(value, name, flags=0, options=None)` | Validate, returning `Ok` with the coerced value or `Err` with a reason |
| `Filter.is_valid(value, name, flags=0, options=None)` | `bool` form of `validate` |
| `Filter.var(value, name, flags=0, options=None)` | The coerced value on success, `None` on failure |
| `Filter.sanitize(value, name, flags=0)` | Sanitize and return the value |
| `Filter.register(name, validator=..., sanitizer=...)` | Register a custom filter at runtime |
| `Filter.unregister(name)` | Remove a previously registered filter |
| `Filter.is_validator(name)` / `Filter.is_sanitizer(name)` | Whether a name is registered, and of which kind |

There are no module-level `validate_var`/`filter_var`/`is_valid`/`sanitize_var`
pass-throughs. Everything lives on the class; the low-level predicates and
sanitizers are available from `oxide.filter.validators` and
`oxide.filter.sanitizers`.

### Validators

`BOOLEAN`, `INT`, `FLOAT`, `NUMERIC`, `EMAIL`, `URL`, `IP`, `IPV4`, `IPV6`,
`DOMAIN`, `REGEXP`, `MAC`, `HEX`, `UUID`, `ALPHA`, `ALPHA_NUMERIC`, `SLUG`,
`JSON`, `DATE`

### Sanitizers

`SANITIZE_EMAIL`, `SANITIZE_URL`, `SANITIZE_URL_RAW`, `SANITIZE_NUMBER_INT`,
`SANITIZE_NUMBER_FLOAT`, `SANITIZE_SPECIAL_CHARS`, `SANITIZE_STRING`,
`SANITIZE_STRIPPED`, `SANITIZE_ENCODED`

`Filter` at the top level is this validation class; the iterator adapter that
used to hold the name is now `FilterIter`.

---

## Prelude

Import common types with a single import:

```python
from oxide.prelude import *
```

Includes: `Option`, `Some`, `None_`, `Result`, `Ok`, `Err`, `Enum`, `match`, `_`, `Vec`, `HashMap`, `HashSet`, `Box`, `Rc`, `Arc`, `Cell`, `RefCell`, `OnceCell`, `Lazy`, `Cow`, `Mutex`, `RwLock`, `Channel`, `Duration`, `Instant`, `SystemTime`, `Path`, `File`, `TcpStream`, `TcpListener`, `UdpSocket`, `Command`, `Child`, `Future`, `Poll`, `Stream`, `Regex`, `Filter`, `Logger`, `derive_`, `masterclass`, `run_tests`, `Help`, and more.

---

## Logging

`oxide.logging` layers console output, the standard streams, and structured
loggers. It is exported at the top level with `log_`-prefixed level helpers so
that `info`, `debug`, and `warn` stay unambiguous.

```python
from oxide.logging import Logger, MemorySink, log_info, println

sink = MemorySink()
logger = Logger("worker", sink=sink, level="info")
logger.info("listening on {port}", port=8080)
sink.messages()                  # ['listening on 8080']

println("to stdout")             # console output, like Rust's println!
log_info("to the default logger")  # routed to a Logger, which writes to stderr
```

### Log levels

`LogLevel` is a `str` subclass, so it compares equal to its own name
(`LogLevel.WARN == "WARN"`) while ordering by verbosity rather than
alphabetically (`LogLevel.ERROR < LogLevel.TRACE`).

| Level | Short | Meaning |
|-------|-------|---------|
| `LogLevel.ERROR` | `ERR` | Something failed and the caller must know |
| `LogLevel.WARN` | `WARN` | Something is suspicious but recoverable |
| `LogLevel.INFO` | `INFO` | Normal, expected progress |
| `LogLevel.DEBUG` | `DBG` | Detail useful while diagnosing a problem |
| `LogLevel.TRACE` | `TRACE` | Everything, including per-iteration detail |

The short forms are the `LogLevel.short` attribute, not separate class
attributes — `LogLevel.WARN.short` is `"WARN"`, `LogLevel.ERROR.short` is
`"ERR"`. Each level also carries `name`, `rank` (0 for ERROR through 4 for
TRACE), `color`, `is_verbose`, and `is_severe`.

| Function | Description |
|----------|-------------|
| `resolve_level(level)` | Normalise a name or alias (`"warning"`) to a canonical level |
| `level_rank(level)` | Verbosity rank, `0` for ERROR through `4` for TRACE |
| `levels()` | Every level name, least to most verbose |
| `enabled_levels(level=None)` | The level names a threshold admits |

### Loggers and sinks

| Name | Signature | Description |
|------|-----------|-------------|
| `Logger` | `Logger(target, *, level=..., parent=None, sink=None, enabled=True)` | A named logger with a level threshold and a sink |
| `Logger.child` | `child(target, **kwargs)` | A nested logger inheriting the parent's level and sink |
| `Logger.log` | `log(level, message, *args, **kwargs) -> bool` | Emit at any level; `args`/`kwargs` fill a format template |
| `Logger.enabled_for` | `enabled_for(level) -> bool` | Whether a record at that level would be emitted |
| `Logger.records` | `records() -> list[LogRecord]` | Captured records, when the sink is a `MemorySink` |
| `LogRecord` | `LogRecord(level, target, message)` | One captured event, with `.level`, `.target`, `.message`, `.timestamp` |
| `MemorySink` | `MemorySink()` | Keeps records in memory for tests |
| `console_sink` | `console_sink(stream=None, *, color=None, format_=...)` | Writes formatted lines, defaulting to stderr |
| `set_default_logger` | `set_default_logger(logger \| None)` | Replace the logger the `log_*` functions route to |
| `default_logger` | `default_logger() -> Logger` | The current default logger |

Module-level shortcuts — `log_trace`, `log_debug`, `log_info`, `log_warn`,
`log_error`, and `log(level, message, ...)` — route to the default logger and
return `True` when the record was emitted.

### Console and streams

Rust's `println!`/`eprint!` and the `std::io` handles, with every name also
available as a plain function.

| Name | Description |
|------|-------------|
| `println(*values)` / `print_(*values)` | Write to stdout, with or without a trailing newline |
| `eprintln(*values)` / `eprint_(*values)` | The same for stderr |
| `stdin()` / `stdout()` / `stderr()` | Handles on the standard streams |
| `Stdin.read_line()` | One line, keeping its newline; `None` at end of input |
| `Stdin.read_line_or(fallback)` | One line, or `fallback` at end of input |
| `Stdin.read_all()` | The rest of the stream |
| `Stdout.write(text) -> int` | Writes and returns the character count |
| `set_stdin/set_stdout/set_stderr(stream)` | Redirect a stream; `None` restores the default |
| `capture() -> (out, err)` | Redirect both output streams into `StringIO` buffers |
| `style(text, *names)` | Wrap text in ANSI codes; a no-op when colour is off |
| `set_color(enabled)` | Force colour on or off; `None` restores detection |
| `color_enabled() -> bool` | Honouring `NO_COLOR` and `FORCE_COLOR` |

---

## Derive and Attribute Macros

`oxide.derive` provides Rust's `#[derive(...)]` and `#[warn]`-style attributes.
Because Python has no compile step, derives are applied by a class decorator and
lints are resolved when the decorated function is called.

```python
from oxide.derive import derive, memoize, lint_warn

@derive("Debug", "Clone", "Default")
class Config:
    __slots__ = ("host", "port")
    def __init__(self, host="localhost", port=8080):
        self.host = host
        self.port = port

Config.default()                  # Config { host: 'localhost', port: 8080 }
Config.default(port=9090)         # per-field overrides win
```

### Supported derives

`Debug`, `Display`, `Clone`, `Copy`, `PartialEq`, `Eq`, `PartialOrd`, `Ord`,
`Hash`, `Default`, `Error`.

Aliases are accepted: `repr` → `Debug`, `fmt` → `Display`, `eq` → `Eq`, and so
on. `derive(*names, fields=None, defaults=None, pretty=False, overwrite=False)`
installs the generated attributes and records what it made in
`cls.derive`. Hand-written implementations are never replaced unless
`overwrite=True`. `Default` resolves each field from, in order: an override
passed to `default()`, the `defaults` mapping, a `default_<field>` class
attribute, then the matching `__init__` parameter default — and raises
`DeriveError` when a field has no default anywhere, exactly as Rust refuses to
compile.

| Function | Description |
|----------|-------------|
| `derive_fields(cls)` | The field names a derive would use |
| `derives_of(cls)` / `is_derived(cls, name)` | What was generated for a class |
| `memoize(maxsize=None, *, key=None)` | Cache results, falling back to `repr` for unhashable arguments |
| `once()` | Run the function at most once |
| `pure(message=None, *, lint=...)` | Memoize, and record a side-effect-free contract |
| `timed(label=None, *, printer=None, scale=1.0, unit="ms")` | Report elapsed time |
| `log_calls(*, level=..., logger=None, ...)` | Log every call through `oxide.logging` |
| `must_use(message=None, *, lint=..., level=None, check=False)` | Lint an ignored return value |
| `deprecated(note='', *, since=None, version=None, ...)` | Warn on use |
| `inline(always=False, *, reason=None)` / `export_name(name)` | Marking attributes |
| `non_exhaustive(target)` | Mark an `Enum` as open to future variants |

### Lints

Levels follow Rust: `allow`, `warn`, `deny`, `forbid`. Because a configured level
raises the floor, `set_lint_level` and `lint_scope` can turn a `warn` into an
error globally or within a block, and a decorator's `level=` argument can raise
it for one use.

| Name | Description |
|------|-------------|
| `warn`, `allow`, `deny`, `forbid` | Attribute decorators; also exported as `lint_*` |
| `set_lint_level(lint, level)` | Set a lint's level for the process |
| `get_lint_level(lint)` / `lint_levels()` | Read configured levels |
| `lint_scope(**levels)` | Context manager applying levels for a block |
| `cap_lint(lint)` | The highest level a lint may reach |
| `reset_lints()` | Forget every level and cap |
| `LintLevel` | A `str` subclass ordering levels; `LintLevel.DENY.is_at_least("warn")` |
| `LintError` | Raised at `deny`/`forbid`; `LintWarning` at `warn` |

`cfg(feature, *, not_feature=None, test=None)` skips a definition unless the
named features are enabled, matching `#[cfg(feature = "...")]`. Features are
turned on with `enable_feature("nightly")`.

---

## Decorators

### One namespace for Rust attributes

Rust spreads its attributes across the language, the standard library, and a pile
of proc-macro crates, so knowing what `#[inline(always)]` does means knowing
which crate it came from. `oxide.decor` gathers them behind one import. It is a
facade, not a reimplementation: `oxide.decor.derive is oxide.derive.derive`.

```python
from oxide.decor import derive, inline, cfg, warn, test, run_tests, masterclass
```

Inside this namespace the plain Rust spellings work, because nothing here
collides with a builtin. At the top level of the `oxide` package the colliding
names are disambiguated instead — `derive_`, `cfg_`, `lint_warn` — so
`oxide.derive` keeps naming the subpackage.

`oxide.decor` re-exports everything from `oxide.derive` (see
[Derive and Attribute Macros](#derive-and-attribute-macros)) and adds the item
attributes, the test harness, and `masterclass`.

### Item attributes

`#[no_mangle]`, `#[used]`, `#[cold]`, and `#[naked]` steer code generation, which
CPython offers no equivalent for, so they are recorded as metadata and read back
through `attributes_of` — the same treatment `inline` already gets.

```python
from oxide.decor import no_mangle, repr_, repr_kinds_of, attributes_of

@no_mangle
def entry_point():
    return 1

attributes_of(entry_point)
# {'no_mangle': {'enabled': True}}

@repr_("transparent")
class Handle:
    __slots__ = ("raw",)

repr_kinds_of(Handle)
# ('transparent',)
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

serve()
# 'done'
```

`track_caller` and `caller_location` together reproduce Rust's
`Location::caller()`: a tracked function that reports `caller_location()` names
the code that called it, not its own line.

### Test attributes

`#[test]`, `#[bench]`, `#[ignore]`, `#[should_panic]`, and `#[serial]` are emulated
for real. Marked functions are collected into registries and executed by
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
result.passed, result.failed, result.ignored, result.errors
# (('test_ok', 'test_expected_failure'), (), ('test_skipped',), ())
```

Tests are collected per module the way Rust collects them per crate: `test` and
`bench` register the function, and `tests()` and `benches()` filter the registry
down to the module that asks, so one module's run never picks up another's.

```python
from oxide.decor import test, tests

@test
def test_in_this_module():
    return None

tests()
# (<function test_in_this_module at ...>,)
```

Pass `module=` to target another module's suite, which is what a driver or a test
runner wants: `run_tests(module=mod_a)`.

`run_tests(include_ignored=True)` runs the ignored ones too and reports them as
ordinary tests.

### masterclass

`masterclass` has no Rust spelling. It combines `classmethod` and `staticmethod`:
the class is always bound, and the instance is bound when one is reachable. A
method written as `(cls, self, ...)` works when called on the class *and* on an
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

Config(7).describe()
# 'Config holds 7'

Config.describe()
# 'Config describes itself'
```

Calling through the class passes `self=None`; calling through an instance passes
that instance. `MasterMethod` is the descriptor itself, and `is_master` reports
whether a value is one.

```python
from oxide.decor import is_master

class Builder:
    @masterclass
    def size(cls, self):
        return 0

is_master(Builder.__dict__["size"])
# True
```

---

## Help

`oxide.help` indexes the library by importing it and reading `__all__`, the
docstrings, and the signatures. It answers the question the README cannot: what
does this symbol actually do?

```python
from oxide.help import Help

Help("Vec").summary            # 'A growable array type with push, pop, ...'
Help("Vec").reference          # 'oxide._collections.Vec'
Help("Vec").fields             # ('_data', '_capacity')
Help("Vec").methods            # MethodEntry objects, sorted by name
Help.module("iter").exports()  # every symbol the module exports
Help.search("range", limit=3).matches
Help.overview().usage()        # rendered text for the whole library
```

Scanning happens once, on first use, and is cached.

| Member | Description |
|--------|-------------|
| `Help(topic)` | Describe a symbol, module, or search term |
| `Help.overview()` | The library as a whole |
| `Help.module(name)` | Describe a whole module |
| `Help.search(query, limit=25, in_methods=False)` | Scored search over names and summaries |
All of the first group are attributes; everything else is a method.

| Member | Kind | Description |
|--------|------|-------------|
| `.name` | attribute | The symbol's name |
| `.kind` | attribute | `symbol`, `module`, or `search` |
| `.module` | attribute | The module it came from |
| `.reference` | attribute | Fully qualified path, e.g. `oxide._collections.Vec` |
| `.summary` / `.description` | attribute | First line, and the whole docstring |
| `.signature` | attribute | The call signature |
| `.methods` / `.fields` / `.bases` / `.examples` | attribute | Structure, from docstrings and `__slots__` |
| `.related` | attribute | Neighbours in the same module |
| `.siblings()` | method | The rest of the module, sorted |
| `.exports()` | method | Every symbol this module exports |
| `.in_module(name)` | method | Every symbol exported by module `name` |
| `.find(query, limit=25, in_methods=False)` | method | The raw matching entries |
| `.usage()` | method | Rendered plain text |
| `.print(stream=None)` | method | Write the rendered help to a stream |
| `.to_dict()` | method | The same data as JSON-serialisable plain types |
| `.exists` | attribute | Whether the topic resolved |
| `Help.module()` / `Help.modules()` / `Help.names()` | classmethod / staticmethod | Module views and the full name index |

| Function | Description |
|----------|-------------|
| `Catalog.build(max_methods=200)` | Scan the package and index every public symbol |
| `catalog(rebuild=False)` | The shared catalog, built on first use |
| `render_entry` / `render_module` / `render_overview` / `render_search` | Renderers used by `Help` |
