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
| `map_or_else(default, fn)` | `-> U` | Maps or computes default from function |
| `and_(other)` | `-> Option[U]` | Returns `other` if `Some`, else `None_` |
| `and_then(fn)` | `-> Option[U]` | Chains operations on `Some` values |
| `or_(other)` | `-> Option[T]` | Returns `self` if `Some`, else `other` |
| `or_else(fn)` | `-> Option[T]` | Returns `self` if `Some`, else computes from `fn` |
| `filter(predicate)` | `-> Option[T]` | Returns `None_` if `Some` but predicate fails |
| `inspect(fn)` | `-> Option[T]` | Calls `fn` with value if `Some`, returns self |

**`Some(value)`** — Wrapper for present values.

```python
@dataclass(frozen=True)
class Some(Option[T]):
    value: T
```

**`NoneOption`** — Singleton representing absence of value. Use `None_` or `none` constants.

```python
None_ = NoneOption()  # Recommended
none = None_          # Alias
```

#### Usage Examples

```python
from oxide import Option, Some, None_, _

# Creating options
x: Option[int] = Some(5)
y: Option[int] = None_

# Pattern matching with match
result = match(x, {
    Some(v): f"Value is {v}",
    None_:  "No value",
})

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
from oxide import Enum, match, _
```

#### Classes

**`Enum`** — Base class for defining algebraic data types.

```python
class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    RGB = ("rgb", int, int, int)  # Variant with payload
```

**`Variant`** — Instance of an enum variant.

| Method | Signature | Description |
|--------|-----------|-------------|
| `tag` | Property | The variant tag name |
| `value` | Property | The variant payload |
| `is_(*tags)` | `-> bool` | Checks if variant matches any tag |
| `unwrap()` | `-> Any` | Returns the payload |
| `expect(message)` | `-> Any` | Returns payload or raises with message |
| `map(fn)` | `-> Variant` | Transforms the payload |
| `and_then(fn)` | `-> Variant` | Chains operations on payload |
| `match(*cases)` | `-> Any` | Pattern matches on tag |

**`match(value)`** — Creates a `Match` builder for exhaustive pattern matching.

```python
result = match(Color.RED, {
    Color.RED:   "Red color",
    Color.GREEN: "Green color",
    _:           "Unknown",
})
```

#### Match Builder

The `Match` class provides a fluent API for pattern matching:

| Method | Description |
|--------|-------------|
| `case(pattern, handler)` | Add exact value match |
| `case_type(typ, handler)` | Add type match |
| `case_range(start, end, handler)` | Add range match |
| `case_pred(predicate, handler)` | Add predicate match |
| `case_in(collection, handler)` | Add membership match |
| `otherwise(handler)` | Add catch-all and execute |

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
clone(value)           # Clone with fallback to deepcopy
debug(value)           # Debug representation
display(value)         # Display representation
default_of(cls)        # Get default instance
from_(cls, value)      # Convert to type
into(value, target)    # Convert to target type
try_from(cls, value)   # Fallible conversion
try_into(value, target) # Fallible conversion
as_ref(value)          # Borrow reference
as_mut(value)          # Borrow mutable reference
deref(value)           # Dereference
deref_mut(value)       # Mutable dereference
drop(value)            # Explicit drop
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
context("during parsing", original_error)  # Create error with context
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

```python
# Efficient in-place manipulation
entry = map.entry("key")
match entry:
    case OccupiedEntry():
        # Key exists, can modify value
        entry.insert(new_value)
    case VacantEntry():
        # Key missing, can insert
        entry.insert(default_value)

# One-liner insert-or-default
map.or_insert("key", default_value)
map.or_insert_with("key", lambda: expensive_computation())
```

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
Iter.from_fn(lambda i: i * 2, start=0)  # Infinite iterator from function
Iter.repeat(value)                       # Infinite repetition
Iter.count(start=0, step=1)              # Infinite counter
Iter.zip(a, b)                           # Zipped iterators
Iter.chain(a, b, c)                      # Chained iterators
```

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
    Enumerate, Zip, Map, Filter, FilterMap, FlatMap, Flatten,
    Peekable, Fuse, Chain, Cycle, Take, Skip, Rev, Inspect,
    Copied, Cloned, Partition,
)
```

| Adapter | Description |
|---------|-------------|
| `Enumerate(iterable, start)` | Add index to each element |
| `Zip(a, b)` | Pair elements from two iterables |
| `Map(iterable, fn)` | Transform each element |
| `Filter(iterable, pred)` | Keep matching elements |
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
b = Box.new(42)
with Box.new(expensive_value()) as b:
    use(b.as_ref())
# Automatically cleaned up
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
cell = OnceCell.new()
cell.get_or_init(lambda: expensive_computation())
print(cell.get())  # Computed value
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
lazy = Lazy(lambda: expensive_computation())
# Not computed yet
result = lazy.force()  # Computed on first call
# Subsequent calls return cached value
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
# Efficient: no copy if not modified
data = CowBorrowed("hello")
owned = data.into_owned()  # Copies here
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
data = RwLock.new(vec)

# Multiple readers can hold locks simultaneously
with data.read() as r:
    print(r.value)

# Writers get exclusive access
with data.write() as w:
    w.value.push(42)
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
start = Instant.now()
do_work()
elapsed = start.elapsed()
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
listener = TcpListener.bind(addr)
for conn in listener.incoming():
    handle_connection(conn)
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
addr = IpAddr.v4(Ipv4Addr(127, 0, 0, 1))
addr = IpAddr.v6(Ipv6Addr.localhost())
```

**`SocketAddr`** — IP address with port.

```python
addr = SocketAddr.new_v4(Ipv4Addr(127, 0, 0, 1), 8080)
addr = SocketAddr.from_str("127.0.0.1:8080")
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
| `new(program)` | Constructor | Create command |
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
output = (Command.new("ls")
    .arg("-la")
    .current_dir("/tmp")
    .output())

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
Stdio.inherit()    # Inherit from parent
Stdio.piped()      # Create pipe
Stdio.null()       # Discard output
Stdio.from_path()  # Redirect to file
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
async def fetch_data() -> str:
    return "data"

future = Future(fetch_data())
result = await future
```

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
handle = spawn(fetch_data())
result = handle.get_result()  # Blocks until done
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
with defer(lambda: cleanup()):
    do_work()
# cleanup() called on exit

guard = ScopeGuard(lambda: cleanup())
guard.cancel()  # Prevent execution
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
s = Saturating(2**31 - 1) + 1  # Saturating(2**31 - 1)
```

| Method | Description |
|--------|-------------|
| `saturating_add(other)` | Saturating addition |
| `saturating_sub(other)` | Saturating subtraction |
| `saturating_mul(other)` | Saturating multiplication |

**`NonZero[T]`** — Non-zero numeric wrapper.

```python
nz = NonZero.new(5)      # Create (raises if 0)
nz = NonZero.try_new(0)  # Returns None if 0
```

---

### Specialized Vectors

**`SmallVec[T]`** — Stack-optimized small vector.

```python
sv = SmallVec([1, 2, 3], stack_limit=8)
```

**`ArrayVec[T]`** — Fixed-capacity vector.

```python
av = ArrayVec.with_capacity(10)
av.push(42)  # Raises OverflowError if full
```

**`TinyVec[T]`** — Inline-to-heap vector.

```python
tv = TinyVec()
for i in range(100):
    tv.push(i)  # Moves to heap when inline limit exceeded
```

**`BitVec`** — Bit vector.

```python
bv = BitVec()
bv.push(True)
bv.push(False)
print(bv.to_bytes())  # b'\x01'
```

---

### CreateMeta

`CreateMeta` — Library metadata (for internal use).

```python
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

## Prelude

Import common types with a single import:

```python
from oxide.prelude import *
```

Includes: `Option`, `Some`, `None_`, `Result`, `Ok`, `Err`, `Enum`, `match`, `_`, `Vec`, `HashMap`, `HashSet`, `Box`, `Rc`, `Arc`, `Cell`, `RefCell`, `OnceCell`, `Lazy`, `Cow`, `Mutex`, `RwLock`, `Channel`, `Duration`, `Instant`, `SystemTime`, `Path`, `File`, `TcpStream`, `TcpListener`, `UdpSocket`, `Command`, `Child`, `Future`, `Poll`, `Stream`, and more.
