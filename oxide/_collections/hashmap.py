"""HashMap — a hash-based key-value map with an Entry API.

Provides ``HashMap``, a hash table mapping keys to values (analogous to Rust's
``std::collections::HashMap``). It supports insertion, lookup, removal, capacity
management, iteration, and an Entry API (``Entry``, ``OccupiedEntry``,
``VacantEntry``) for efficient in-place manipulation of entries. A
``MutableValue`` wrapper provides mutable references to stored values.
"""
from __future__ import annotations

from typing import Callable, Generic, Iterable, Iterator, TypeVar

from ..core.option import Option, Some, None_

K = TypeVar("K")
V = TypeVar("V")
U = TypeVar("U")


class _Missing:
    """Sentinel type used to distinguish missing keys from None values."""

    __slots__ = ()


_MISSING = _Missing()


class HashMap(Generic[K, V]):
    """A hash-based key-value map with Entry API for efficient in-place manipulation.

    ``HashMap`` stores key-value pairs with average O(1) lookup, insertion, and
    removal. Keys must be hashable. Use :meth:`entry` to obtain an
    :class:`Entry` for efficient conditional insertion, or wrap values in
    :class:`MutableValue` for in-place mutation.

    Examples:
        >>> m = HashMap([("a", 1)])
        >>> m.insert("b", 2)
        None_
        >>> m.get("a")
        Some(1)
        >>> dict(m.iter())
        {'a': 1, 'b': 2}
    """

    __slots__ = ("_data", "_capacity")

    def __init__(
        self,
        values: Iterable[tuple[K, V]] | dict[K, V] | None = None,
        *,
        capacity: int = 0,
    ) -> None:
        """Initialize a HashMap, optionally from pairs and with a capacity hint.

        Args:
            values (Iterable[tuple[K, V]] | dict[K, V] | None): An iterable of
                ``(key, value)`` pairs or a dict to pre-populate the map.
            capacity (int): The initial capacity. Defaults to 0.

        Raises:
            ValueError: If ``capacity`` is negative.

        Examples:
            >>> HashMap()
            HashMap({})
            >>> HashMap([("a", 1), ("b", 2)])
            HashMap({'a': 1, 'b': 2})
        """
        if capacity < 0:
            raise ValueError("capacity must be non-negative")

        self._data: dict[K, V] = {}
        self._capacity = max(capacity, 0)

        if values is not None:
            if isinstance(values, dict):
                self.extend(values.items())
            else:
                self.extend(values)

    @classmethod
    def new(cls) -> HashMap[K, V]:
        """Create a new empty HashMap.

        Returns:
            HashMap[K, V]: An empty map.

        Examples:
            >>> HashMap.new()
            HashMap({})
        """
        return cls()

    @classmethod
    def with_capacity(cls, capacity: int) -> HashMap[K, V]:
        """Create a new HashMap with pre-allocated capacity.

        Args:
            capacity (int): The number of entries to allocate space for.

        Returns:
            HashMap[K, V]: An empty map with the given capacity.

        Examples:
            >>> HashMap.with_capacity(10)
            HashMap({})
        """
        return cls(capacity=capacity)

    @classmethod
    def from_iter(
        cls,
        values: Iterable[tuple[K, V]],
    ) -> HashMap[K, V]:
        """Create a HashMap from an iterable of (key, value) pairs.

        Args:
            values (Iterable[tuple[K, V]]): Pairs to insert into the map.

        Returns:
            HashMap[K, V]: A new map containing all the pairs.

        Examples:
            >>> HashMap.from_iter([("a", 1), ("b", 2)])
            HashMap({'a': 1, 'b': 2})
        """
        return cls(values)

    @classmethod
    def from_dict(
        cls,
        values: dict[K, V],
    ) -> HashMap[K, V]:
        """Create a HashMap from a dictionary.

        Args:
            values (dict[K, V]): The dictionary to copy into the map.

        Returns:
            HashMap[K, V]: A new map with the same entries as ``values``.

        Examples:
            >>> HashMap.from_dict({"a": 1})
            HashMap({'a': 1})
        """
        return cls(values.items())

    def len(self) -> int:
        """Return the number of entries in the map.

        Returns:
            int: The number of key-value pairs.

        Examples:
            >>> HashMap([("a", 1)]).len()
            1
        """
        return len(self._data)

    def is_empty(self) -> bool:
        """Return True if the map contains no entries.

        Returns:
            bool: True if the map has no entries.

        Examples:
            >>> HashMap().is_empty()
            True
        """
        return not self._data

    def capacity(self) -> int:
        """Return the total capacity of the map.

        Returns:
            int: The current capacity, at least the number of entries.

        Examples:
            >>> HashMap([("a", 1)], capacity=10).capacity()
            10
        """
        return max(self._capacity, len(self._data))

    def reserve(self, additional: int) -> None:
        """Reserve capacity for at least `additional` more entries.

        Args:
            additional (int): The desired number of additional entries. Must be
                non-negative.

        Raises:
            ValueError: If ``additional`` is negative.

        Examples:
            >>> m = HashMap()
            >>> m.reserve(10)
            >>> m.capacity() >= 10
            True
        """
        if additional < 0:
            raise ValueError("additional must be non-negative")

        required = self.len() + additional

        if required > self._capacity:
            self._capacity = max(
                required,
                max(1, self._capacity * 2),
            )

    def reserve_exact(self, additional: int) -> None:
        """Reserve capacity for exactly `additional` more entries if needed.

        Args:
            additional (int): The number of additional entries to reserve room
                for. Must be non-negative.

        Raises:
            ValueError: If ``additional`` is negative.

        Examples:
            >>> m = HashMap()
            >>> m.reserve_exact(5)
            >>> m.capacity()
            5
        """
        if additional < 0:
            raise ValueError("additional must be non-negative")

        required = self.len() + additional

        if required > self._capacity:
            self._capacity = required

    def try_reserve(self, additional: int) -> bool:
        """Attempt to reserve capacity; return True on success, False on overflow.

        Args:
            additional (int): The desired number of additional entries.

        Returns:
            bool: True if capacity was reserved, False on memory error or
                overflow.

        Examples:
            >>> m = HashMap()
            >>> m.try_reserve(10)
            True
        """
        try:
            self.reserve(additional)
            return True
        except (MemoryError, OverflowError):
            return False

    def shrink_to_fit(self) -> None:
        """Shrink the capacity to match the current length.

        Examples:
            >>> m = HashMap([("a", 1)], capacity=100)
            >>> m.shrink_to_fit()
            >>> m.capacity()
            1
        """
        self._capacity = self.len()

    def shrink_to(self, min_capacity: int) -> None:
        """Shrink the capacity to at most `min_capacity`.

        The resulting capacity is no smaller than the current length.

        Args:
            min_capacity (int): The desired upper bound on capacity. Must be
                non-negative.

        Raises:
            ValueError: If ``min_capacity`` is negative.

        Examples:
            >>> m = HashMap([("a", 1)], capacity=100)
            >>> m.shrink_to(5)
            >>> m.capacity()
            5
        """
        if min_capacity < 0:
            raise ValueError("min_capacity must be non-negative")

        self._capacity = max(
            self.len(),
            min_capacity,
        )

    def insert(self, key: K, value: V) -> Option[V]:
        """Insert a key-value pair, returning the old value if the key existed.

        Args:
            key (K): The key to insert.
            value (V): The value to associate with ``key``.

        Returns:
            Option[V]: ``Some`` containing the previous value if ``key`` already
                existed, otherwise ``None_``.

        Examples:
            >>> m = HashMap([("a", 1)])
            >>> m.insert("a", 9)
            Some(1)
            >>> m.insert("b", 2)
            None_
        """
        old = self._data.get(key, _MISSING)

        if old is _MISSING:
            self.reserve(1)
            self._data[key] = value
            return None_

        self._data[key] = value
        return Some(old)

    def insert_entry(self, key: K, value: V) -> OccupiedEntry[K, V]:
        """Insert a key-value pair and return an OccupiedEntry for it.

        Args:
            key (K): The key to insert.
            value (V): The value to associate with ``key``.

        Returns:
            OccupiedEntry[K, V]: An occupied entry referencing the freshly
                inserted pair.

        Examples:
            >>> m = HashMap()
            >>> e = m.insert_entry("a", 1)
            >>> m.get("a")
            Some(1)
        """
        self.insert(key, value)
        return OccupiedEntry(self, key)

    def get(self, key: K) -> Option[V]:
        """Return the value for the key, or None_ if not present.

        Args:
            key (K): The key to look up.

        Returns:
            Option[V]: ``Some`` with the value if present, otherwise ``None_``.

        Examples:
            >>> m = HashMap([("a", 1)])
            >>> m.get("a")
            Some(1)
            >>> m.get("z")
            None_
        """
        value = self._data.get(key, _MISSING)

        if value is _MISSING:
            return None_

        return Some(value)

    def get_value(self, key: K) -> V | None:
        """Return the value for the key, or None if not present.

        Unlike :meth:`get`, this returns a plain Python value (``None``) rather
        than an ``Option``.

        Args:
            key (K): The key to look up.

        Returns:
            V | None: The value if present, otherwise None.

        Examples:
            >>> m = HashMap([("a", 1)])
            >>> m.get_value("a")
            1
        """
        return self._data.get(key)

    def get_mut(self, key: K) -> Option[MutableValue[K, V]]:
        """Return a mutable reference to the value, or None_ if not present.

        Args:
            key (K): The key to look up.

        Returns:
            Option[MutableValue[K, V]]: ``Some`` with a mutable reference if the
                key is present, otherwise ``None_``.

        Examples:
            >>> m = HashMap([("a", 1)])
            >>> m.get_mut("a").unwrap().set(5)
            >>> m.get_value("a")
            5
        """
        if key not in self._data:
            return None_

        return Some(MutableValue(self, key))

    def get_key_value(self, key: K) -> Option[tuple[K, V]]:
        """Return the (key, value) pair, or None_ if the key is not present.

        Args:
            key (K): The key to look up.

        Returns:
            Option[tuple[K, V]]: ``Some`` with the ``(key, value)`` pair if
                present, otherwise ``None_``.

        Examples:
            >>> m = HashMap([("a", 1)])
            >>> m.get_key_value("a")
            Some(('a', 1))
        """
        if key not in self._data:
            return None_

        return Some((key, self._data[key]))

    def contains_key(self, key: K) -> bool:
        """Return True if the map contains the given key.

        Args:
            key (K): The key to check.

        Returns:
            bool: True if ``key`` is in the map.

        Examples:
            >>> HashMap([("a", 1)]).contains_key("a")
            True
        """
        return key in self._data

    def remove(self, key: K) -> Option[V]:
        """Remove and return the value for the key, or None_ if not present.

        Args:
            key (K): The key to remove.

        Returns:
            Option[V]: ``Some`` with the removed value if present, otherwise
                ``None_``.

        Examples:
            >>> m = HashMap([("a", 1)])
            >>> m.remove("a")
            Some(1)
            >>> m.remove("a")
            None_
        """
        value = self._data.pop(key, _MISSING)

        if value is _MISSING:
            return None_

        return Some(value)

    def remove_entry(self, key: K) -> Option[tuple[K, V]]:
        """Remove and return the (key, value) pair, or None_ if not present.

        Args:
            key (K): The key to remove.

        Returns:
            Option[tuple[K, V]]: ``Some`` with the removed ``(key, value)`` pair
                if present, otherwise ``None_``.

        Examples:
            >>> m = HashMap([("a", 1)])
            >>> m.remove_entry("a")
            Some(('a', 1))
        """
        if key not in self._data:
            return None_

        return Some((key, self._data.pop(key)))

    def clear(self) -> None:
        """Remove all entries from the map.

        Examples:
            >>> m = HashMap([("a", 1)])
            >>> m.clear()
            >>> m.is_empty()
            True
        """
        self._data.clear()

    def retain(self, predicate: Callable[[K, V], bool]) -> None:
        """Keep only entries for which the predicate returns True.

        Args:
            predicate (Callable[[K, V], bool]): A function called with each
                ``(key, value)`` pair; entries for which it returns True are kept.

        Examples:
            >>> m = HashMap({"a": 1, "b": 2, "c": 3})
            >>> m.retain(lambda k, v: v % 2 == 1)
            >>> dict(m.iter())
            {'a': 1, 'c': 3}
        """
        keys = [
            key
            for key, value in self._data.items()
            if not predicate(key, value)
        ]

        for key in keys:
            del self._data[key]

    def entry(self, key: K) -> Entry[K, V]:
        """Return an Entry for the key, enabling in-place manipulation.

        Args:
            key (K): The key to build an entry for.

        Returns:
            Entry[K, V]: An ``OccupiedEntry`` if the key is present, otherwise a
                ``VacantEntry``.

        Examples:
            >>> m = HashMap()
            >>> m.entry("a").or_insert(1)
            1
            >>> m.entry("a").or_insert(99)
            1
        """
        if key in self._data:
            return OccupiedEntry(self, key)

        return VacantEntry(self, key)

    def or_insert(self, key: K, value: V) -> V:
        """Insert the value if the key is absent, then return the value.

        Args:
            key (K): The key to insert.
            value (V): The value to insert if ``key`` is absent.

        Returns:
            V: The existing value if present, otherwise the inserted value.

        Examples:
            >>> m = HashMap()
            >>> m.or_insert("a", 1)
            1
            >>> m.or_insert("a", 9)
            1
        """
        entry = self.entry(key)
        return entry.or_insert(value)

    def or_insert_with(
        self,
        key: K,
        fn: Callable[[], V],
    ) -> V:
        """Insert the value from `fn` if the key is absent, then return the value.

        Args:
            key (K): The key to insert.
            fn (Callable[[], V]): A function producing the value, called lazily
                only when ``key`` is absent.

        Returns:
            V: The existing value if present, otherwise the value from ``fn``.

        Examples:
            >>> m = HashMap()
            >>> m.or_insert_with("a", lambda: 42)
            42
        """
        entry = self.entry(key)
        return entry.or_insert_with(fn)

    def or_insert_with_key(
        self,
        key: K,
        fn: Callable[[K], V],
    ) -> V:
        """Insert the value from `fn(key)` if the key is absent, then return the value.

        Args:
            key (K): The key to insert; passed to ``fn`` when computing the new
                value.
            fn (Callable[[K], V]): A function producing the value, called lazily
                only when ``key`` is absent.

        Returns:
            V: The existing value if present, otherwise the value from ``fn``.

        Examples:
            >>> m = HashMap()
            >>> m.or_insert_with_key("a", lambda k: len(k))
            1
        """
        entry = self.entry(key)
        return entry.or_insert_with_key(fn)

    def extend(
        self,
        values: Iterable[tuple[K, V]],
    ) -> None:
        """Insert all (key, value) pairs from an iterable into the map.

        Existing values associated with the same keys are overwritten.

        Args:
            values (Iterable[tuple[K, V]]): An iterable of ``(key, value)`` pairs.

        Examples:
            >>> m = HashMap()
            >>> m.extend([("a", 1), ("b", 2)])
            >>> len(m)
            2
        """
        values = list(values)
        self.reserve(len(values))

        for key, value in values:
            self._data[key] = value

    def extend_one(self, key: K, value: V) -> None:
        """Insert a single key-value pair into the map.

        Args:
            key (K): The key to insert.
            value (V): The value to associate.

        Examples:
            >>> m = HashMap()
            >>> m.extend_one("a", 1)
            >>> len(m)
            1
        """
        self.insert(key, value)

    def iter(self) -> Iterator[tuple[K, V]]:
        """Return an iterator over (key, value) pairs.

        Returns:
            Iterator[tuple[K, V]]: An iterator yielding the map's pairs.

        Examples:
            >>> dict(HashMap([("a", 1)]).iter())
            {'a': 1}
        """
        return iter(self._data.items())

    def iter_mut(self) -> Iterator[MutableValue[K, V]]:
        """Return an iterator of mutable value references.

        Yields:
            Iterator[MutableValue[K, V]]: A mutable reference to each value.

        Examples:
            >>> m = HashMap({"a": 1, "b": 2})
            >>> for mv in m.iter_mut():
            ...     mv.set(mv.get() * 10)
        """
        for key in self._data:
            yield MutableValue(self, key)

    def keys(self) -> Iterator[K]:
        """Return an iterator over the keys.

        Returns:
            Iterator[K]: An iterator yielding each key.

        Examples:
            >>> list(HashMap([("a", 1)]).keys())
            ['a']
        """
        return iter(self._data.keys())

    def values(self) -> Iterator[V]:
        """Return an iterator over the values.

        Returns:
            Iterator[V]: An iterator yielding each value.

        Examples:
            >>> list(HashMap([("a", 1)]).values())
            [1]
        """
        return iter(self._data.values())

    def values_mut(self) -> Iterator[MutableValue[K, V]]:
        """Return an iterator of mutable value references.

        Alias of :meth:`iter_mut`.

        Yields:
            Iterator[MutableValue[K, V]]: A mutable reference to each value.
        """
        return self.iter_mut()

    def into_iter(self) -> Iterator[tuple[K, V]]:
        """Consume the map and return an iterator over its (key, value) pairs.

        The map is emptied and its capacity reset.

        Returns:
            Iterator[tuple[K, V]]: An iterator over the pairs before consumption.

        Examples:
            >>> m = HashMap([("a", 1)])
            >>> list(m.into_iter())
            [('a', 1)]
            >>> m.is_empty()
            True
        """
        data = self._data

        self._data = {}
        self._capacity = 0

        return iter(data.items())

    def drain(self) -> Iterator[tuple[K, V]]:
        """Consume the map and return an iterator over its (key, value) pairs.

        The map is emptied and its capacity reset.

        Returns:
            Iterator[tuple[K, V]]: An iterator over the pairs before consumption.

        Examples:
            >>> m = HashMap([("a", 1)])
            >>> list(m.drain())
            [('a', 1)]
            >>> len(m)
            0
        """
        data = self._data

        self._data = {}
        self._capacity = 0

        return iter(data.items())

    def is_disjoint(self, other: HashMap[K, V]) -> bool:
        """Return True if the two maps share no common keys.

        Args:
            other (HashMap[K, V]): The map to compare against.

        Returns:
            bool: True if the two maps have no keys in common.

        Examples:
            >>> HashMap([("a", 1)]).is_disjoint(HashMap([("b", 2)]))
            True
        """
        return not any(
            key in other._data
            for key in self._data
        )

    def len_common(self, other: HashMap[K, U]) -> int:
        """Return the number of keys shared between this map and another.

        Args:
            other (HashMap[K, U]): The map to compare against.

        Returns:
            int: The count of keys present in both maps.

        Examples:
            >>> HashMap([("a", 1), ("b", 2)]).len_common(HashMap([("b", 3)]))
            1
        """
        return sum(
            key in other._data
            for key in self._data
        )

    def clone(self) -> HashMap[K, V]:
        """Return a deep copy of this map.

        Returns:
            HashMap[K, V]: A new map with the same entries and capacity.

        Examples:
            >>> m = HashMap([("a", 1)])
            >>> m.clone() == m
            True
        """
        result = HashMap[K, V]()
        result._data = self._data.copy()
        result._capacity = self._capacity
        return result

    def to_dict(self) -> dict[K, V]:
        """Return a new dictionary containing a copy of all entries.

        Returns:
            dict[K, V]: A shallow copy of the underlying entries.

        Examples:
            >>> HashMap([("a", 1)]).to_dict()
            {'a': 1}
        """
        return self._data.copy()

    def __getitem__(self, key: K) -> V:
        """Return the value for the key.

        Args:
            key (K): The key to look up.

        Returns:
            V: The value associated with ``key``.

        Raises:
            KeyError: If ``key`` is not present.

        Examples:
            >>> HashMap([("a", 1)])["a"]
            1
        """
        return self._data[key]

    def __setitem__(self, key: K, value: V) -> None:
        """Insert or overwrite the value for the key.

        Args:
            key (K): The key to write.
            value (V): The value to associate.

        Examples:
            >>> m = HashMap()
            >>> m["a"] = 1
            >>> m["a"]
            1
        """
        self.insert(key, value)

    def __delitem__(self, key: K) -> None:
        """Remove the entry for the key.

        Args:
            key (K): The key to remove.

        Raises:
            KeyError: If ``key`` is not present.

        Examples:
            >>> m = HashMap([("a", 1)])
            >>> del m["a"]
            >>> len(m)
            0
        """
        del self._data[key]

    def __contains__(self, key: object) -> bool:
        """Return True if the map contains the key.

        Examples:
            >>> "a" in HashMap([("a", 1)])
            True
        """
        return key in self._data

    def __iter__(self) -> Iterator[K]:
        """Return an iterator over the keys.

        Examples:
            >>> list(HashMap([("a", 1)]))
            ['a']
        """
        return iter(self._data)

    def __len__(self) -> int:
        """Return the number of entries in the map.

        Examples:
            >>> len(HashMap([("a", 1)]))
            1
        """
        return len(self._data)

    def __bool__(self) -> bool:
        """Return True if the map is non-empty.

        Examples:
            >>> bool(HashMap([("a", 1)]))
            True
        """
        return bool(self._data)

    def __repr__(self) -> str:
        """Return a string representation of the map.

        Examples:
            >>> repr(HashMap([("a", 1)]))
            "HashMap({'a': 1})"
        """
        return f"HashMap({self._data!r})"

    def __eq__(self, other: object) -> bool:
        """Return True if the map equals another map or dict.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: True if ``other`` is a ``HashMap`` or ``dict`` with equal
                entries; ``NotImplemented`` otherwise.

        Examples:
            >>> HashMap([("a", 1)]) == {"a": 1}
            True
        """
        if isinstance(other, HashMap):
            return self._data == other._data

        if isinstance(other, dict):
            return self._data == other

        return NotImplemented


class Entry(Generic[K, V]):
    """Represents a map entry that is either occupied or vacant.

    Returned by :meth:`HashMap.entry`, this base class provides a uniform
    interface over both an existing key (``OccupiedEntry``) and a missing key
    (``VacantEntry``) so entries can be inserted or modified efficiently in
    place.

    Examples:
        >>> m = HashMap()
        >>> m.entry("a").or_insert(1)
        1
        >>> m.entry("a").is_occupied()
        True
    """

    __slots__ = ()

    def is_occupied(self) -> bool:
        """Return True if this entry corresponds to an occupied slot.

        Returns:
            bool: True if this is an ``OccupiedEntry``.

        Examples:
            >>> HashMap([("a", 1)]).entry("a").is_occupied()
            True
        """
        return isinstance(self, OccupiedEntry)

    def is_vacant(self) -> bool:
        """Return True if this entry corresponds to a vacant slot.

        Returns:
            bool: True if this is a ``VacantEntry``.

        Examples:
            >>> HashMap().entry("a").is_vacant()
            True
        """
        return isinstance(self, VacantEntry)

    def key(self) -> K:
        """Return the key associated with this entry.

        Returns:
            K: The key of the entry.

        Raises:
            NotImplementedError: Always, in the abstract base class. Concrete
                subclasses implement this.
        """
        raise NotImplementedError

    def or_insert(self, value: V) -> V:
        """Return the existing value or insert and return the provided value.

        Args:
            value (V): The value to insert if the key is vacant.

        Returns:
            V: The existing value if occupied, otherwise the inserted value.

        Raises:
            NotImplementedError: Always, in the abstract base class. Concrete
                subclasses implement this.
        """
        raise NotImplementedError

    def or_insert_with(self, fn: Callable[[], V]) -> V:
        """Return the existing value or insert the value from `fn`.

        Args:
            fn (Callable[[], V]): A function producing the value to insert if
                vacant.

        Returns:
            V: The existing value if occupied, otherwise the value from ``fn``.

        Raises:
            NotImplementedError: Always, in the abstract base class. Concrete
                subclasses implement this.
        """
        raise NotImplementedError

    def or_insert_with_key(
        self,
        fn: Callable[[K], V],
    ) -> V:
        """Return the existing value or insert the value from `fn(key)`.

        Args:
            fn (Callable[[K], V]): A function producing the value to insert if
                vacant; receives the entry's key.

        Returns:
            V: The existing value if occupied, otherwise the value from ``fn``.

        Raises:
            NotImplementedError: Always, in the abstract base class. Concrete
                subclasses implement this.
        """
        raise NotImplementedError

    def and_modify(
        self,
        fn: Callable[[MutableValue[K, V]], None],
    ) -> Entry[K, V]:
        """If occupied, call `fn` with a mutable reference; return self.

        Args:
            fn (Callable[[MutableValue[K, V]], None]): A callback receiving a
                mutable reference to the value when the entry is occupied.

        Returns:
            Entry[K, V]: ``self``, for chaining.

        Examples:
            >>> m = HashMap({"a": 1})
            >>> m.entry("a").and_modify(lambda mv: mv.set(9)).or_insert(0)
            9
        """
        if isinstance(self, OccupiedEntry):
            fn(MutableValue(self._map, self._key))

        return self


class OccupiedEntry(Entry[K, V]):
    """An entry in the map that corresponds to an existing key-value pair.

    Returned by :meth:`HashMap.entry` when the key is already present. Provides
    read and mutate access to the stored value, as well as removal.

    Examples:
        >>> m = HashMap({"a": 1})
        >>> e = m.entry("a")
        >>> e.get()
        1
    """

    __slots__ = ("_map", "_key")

    def __init__(
        self,
        map_: HashMap[K, V],
        key: K,
    ) -> None:
        """Initialize an occupied entry bound to a map and key.

        Args:
            map_ (HashMap[K, V]): The map the entry belongs to.
            key (K): The key of the occupied entry.
        """
        self._map = map_
        self._key = key

    def key(self) -> K:
        """Return the key of this occupied entry.

        Returns:
            K: The entry's key.
        """
        return self._key

    def get(self) -> V:
        """Return a reference to the value in this entry.

        Returns:
            V: The current value.

        Examples:
            >>> HashMap({"a": 1}).entry("a").get()
            1
        """
        return self._map._data[self._key]

    def get_mut(self) -> MutableValue[K, V]:
        """Return a mutable reference to the value in this entry.

        Returns:
            MutableValue[K, V]: A wrapper enabling in-place value mutation.

        Examples:
            >>> e = HashMap({"a": 1}).entry("a")
            >>> e.get_mut().set(5)
            >>> e.get()
            5
        """
        return MutableValue(self._map, self._key)

    def insert(self, value: V) -> V:
        """Replace the value and return the old one.

        Args:
            value (V): The new value.

        Returns:
            V: The value that was previously stored.

        Examples:
            >>> e = HashMap({"a": 1}).entry("a")
            >>> e.insert(9)
            1
        """
        old = self._map._data[self._key]
        self._map._data[self._key] = value
        return old

    def remove(self) -> V:
        """Remove this entry from the map and return the value.

        Returns:
            V: The value that was removed.

        Examples:
            >>> m = HashMap({"a": 1})
            >>> m.entry("a").remove()
            1
            >>> "a" in m
            False
        """
        return self._map._data.pop(self._key)

    def remove_entry(self) -> tuple[K, V]:
        """Remove this entry from the map and return the (key, value) pair.

        Returns:
            tuple[K, V]: The removed key and value.

        Examples:
            >>> m = HashMap({"a": 1})
            >>> m.entry("a").remove_entry()
            ('a', 1)
        """
        return self._key, self._map._data.pop(self._key)

    def or_insert(self, value: V) -> V:
        """Return the existing value since the key is already present.

        Args:
            value (V): Ignored; provided only to satisfy the entry interface.

        Returns:
            V: The existing value.
        """
        return self.get()

    def or_insert_with(self, fn: Callable[[], V]) -> V:
        """Return the existing value since the key is already present.

        Args:
            fn (Callable[[], V]): Ignored; provided only to satisfy the entry
                interface.

        Returns:
            V: The existing value.
        """
        return self.get()

    def or_insert_with_key(
        self,
        fn: Callable[[K], V],
    ) -> V:
        """Return the existing value since the key is already present.

        Args:
            fn (Callable[[K], V]): Ignored; provided only to satisfy the entry
                interface.

        Returns:
            V: The existing value.
        """
        return self.get()


class VacantEntry(Entry[K, V]):
    """An entry in the map that corresponds to a key with no value.

    Returned by :meth:`HashMap.entry` when the key is not present. Provides a
    way to insert a value at the vacant key.

    Examples:
        >>> m = HashMap()
        >>> m.entry("a").insert(1)
        1
    """

    __slots__ = ("_map", "_key")

    def __init__(
        self,
        map_: HashMap[K, V],
        key: K,
    ) -> None:
        """Initialize a vacant entry bound to a map and key.

        Args:
            map_ (HashMap[K, V]): The map the entry belongs to.
            key (K): The key of the vacant entry.
        """
        self._map = map_
        self._key = key

    def key(self) -> K:
        """Return the key of this vacant entry.

        Returns:
            K: The entry's key.
        """
        return self._key

    def insert(self, value: V) -> V:
        """Insert the value into the map and return it.

        Args:
            value (V): The value to insert.

        Returns:
            V: The inserted value.

        Examples:
            >>> m = HashMap()
            >>> m.entry("a").insert(1)
            1
            >>> m.get_value("a")
            1
        """
        self._map.insert(self._key, value)
        return value

    def or_insert(self, value: V) -> V:
        """Insert and return the provided value since the key is vacant.

        Args:
            value (V): The value to insert.

        Returns:
            V: The inserted value.
        """
        return self.insert(value)

    def or_insert_with(self, fn: Callable[[], V]) -> V:
        """Insert the value from `fn` and return it since the key is vacant.

        Args:
            fn (Callable[[], V]): A function producing the value to insert.

        Returns:
            V: The inserted value.
        """
        return self.insert(fn())

    def or_insert_with_key(
        self,
        fn: Callable[[K], V],
    ) -> V:
        """Insert the value from `fn(key)` and return it since the key is vacant.

        Args:
            fn (Callable[[K], V]): A function producing the value to insert;
                receives the entry's key.

        Returns:
            V: The inserted value.
        """
        return self.insert(fn(self._key))


class MutableValue(Generic[K, V]):
    """A mutable reference to a value in a HashMap, enabling in-place updates.

    Returned by :meth:`HashMap.get_mut`, :meth:`HashMap.iter_mut`, and entry
    :meth:`OccupiedEntry.get_mut`. Use :meth:`get`/:meth:`set` or the ``value``
    property to read and update the underlying value without moving it out of the
    map.

    Examples:
        >>> m = HashMap({"a": 1})
        >>> mv = m.get_mut("a").unwrap()
        >>> mv.set(5)
        >>> m.get_value("a")
        5
    """

    __slots__ = ("_map", "_key")

    def __init__(
        self,
        map_: HashMap[K, V],
        key: K,
    ) -> None:
        """Initialize a mutable value reference bound to a map entry.

        Args:
            map_ (HashMap[K, V]): The map holding the value.
            key (K): The key of the referenced value.
        """
        self._map = map_
        self._key = key

    @property
    def value(self) -> V:
        """Return the current value.

        Returns:
            V: The value referenced by this wrapper.
        """
        return self._map._data[self._key]

    @value.setter
    def value(self, value: V) -> None:
        """Set the value in the underlying map.

        Args:
            value (V): The new value.
        """
        self._map._data[self._key] = value

    def replace(self, value: V) -> V:
        """Replace the current value and return the old one.

        Args:
            value (V): The new value.

        Returns:
            V: The value that was previously stored.
        """
        old = self.value
        self.value = value
        return old

    def get(self) -> V:
        """Return the current value.

        Returns:
            V: The value referenced by this wrapper.
        """
        return self.value

    def set(self, value: V) -> None:
        """Set the value to the given value.

        Args:
            value (V): The new value.
        """
        self.value = value
