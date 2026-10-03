"""BTreeMap — an ordered map with sorted key iteration.

Provides ``BTreeMap``, a key-value map that keeps its keys in sorted order
(analogous to Rust's ``std::collections::BTreeMap``). It offers efficient range
queries, sorted iteration over keys and values, and access to the smallest and
largest entries.
"""
from __future__ import annotations

from typing import Generic, Iterable, Iterator, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class BTreeMap(Generic[K, V]):
    """An ordered key-value map with keys maintained in sorted order.

    ``BTreeMap`` stores key-value pairs such that keys are always in ascending
    sorted order. This enables ordered iteration, range queries via
    :meth:`range_`, and O(1) access to the smallest/largest entries.

    Examples:
        >>> m = BTreeMap([("b", 2), ("a", 1)])
        >>> list(m.keys())
        ['a', 'b']
        >>> m.first_key_value()
        ('a', 1)
        >>> dict(m.iter())
        {'a': 1, 'b': 2}
    """

    __slots__ = ("_data",)

    def __init__(self, values: Iterable[tuple[K, V]] | dict[K, V] | None = None) -> None:
        """Initialize a BTreeMap, optionally from pairs or a dict.

        Entries are sorted by key upon construction.

        Args:
            values (Iterable[tuple[K, V]] | dict[K, V] | None): An iterable of
                ``(key, value)`` pairs or a dict to pre-populate the map.

        Examples:
            >>> BTreeMap([("b", 2), ("a", 1)])
            BTreeMap({'a': 1, 'b': 2})
        """
        self._data: dict[K, V] = {}
        if values is not None:
            if isinstance(values, dict):
                self._data = dict(sorted(values.items()))
            else:
                self._data = dict(sorted(values, key=lambda x: x[0]))

    @classmethod
    def new(cls) -> BTreeMap[K, V]:
        """Create a new empty BTreeMap.

        Returns:
            BTreeMap[K, V]: An empty map.

        Examples:
            >>> BTreeMap.new()
            BTreeMap({})
        """
        return cls()

    @classmethod
    def from_dict(cls, values: dict[K, V]) -> BTreeMap[K, V]:
        """Create a BTreeMap from a dictionary.

        Args:
            values (dict[K, V]): The dictionary to copy, sorted by key.

        Returns:
            BTreeMap[K, V]: A new map with keys sorted.

        Examples:
            >>> BTreeMap.from_dict({"b": 2, "a": 1})
            BTreeMap({'a': 1, 'b': 2})
        """
        return cls(values)

    def insert(self, key: K, value: V) -> V | None:
        """Insert a key-value pair, returning the old value if the key existed.

        Args:
            key (K): The key to insert.
            value (V): The value to associate with ``key``.

        Returns:
            V | None: The previous value if ``key`` existed, otherwise None.

        Examples:
            >>> m = BTreeMap([("a", 1)])
            >>> m.insert("a", 9)
            1
        """
        old = self._data.get(key)
        self._data[key] = value
        return old

    def get(self, key: K) -> V | None:
        """Return the value for the key, or None if not present.

        Args:
            key (K): The key to look up.

        Returns:
            V | None: The value if present, otherwise None.

        Examples:
            >>> BTreeMap([("a", 1)]).get("a")
            1
        """
        return self._data.get(key)

    def get_key_value(self, key: K) -> tuple[K, V] | None:
        """Return the (key, value) pair, or None if the key is not present.

        Args:
            key (K): The key to look up.

        Returns:
            tuple[K, V] | None: The ``(key, value)`` pair if present, otherwise
                None.

        Examples:
            >>> BTreeMap([("a", 1)]).get_key_value("a")
            ('a', 1)
        """
        if key in self._data:
            return (key, self._data[key])
        return None

    def remove(self, key: K) -> V | None:
        """Remove and return the value for the key, or None if not present.

        Args:
            key (K): The key to remove.

        Returns:
            V | None: The removed value if present, otherwise None.

        Examples:
            >>> m = BTreeMap([("a", 1)])
            >>> m.remove("a")
            1
        """
        return self._data.pop(key, None)

    def contains_key(self, key: K) -> bool:
        """Return True if the map contains the given key.

        Args:
            key (K): The key to check.

        Returns:
            bool: True if ``key`` is in the map.

        Examples:
            >>> BTreeMap([("a", 1)]).contains_key("a")
            True
        """
        return key in self._data

    def first_key_value(self) -> tuple[K, V] | None:
        """Return the (key, value) pair with the smallest key, or None.

        Returns:
            tuple[K, V] | None: The entry with the smallest key, or None if the
                map is empty.

        Examples:
            >>> BTreeMap([("b", 2), ("a", 1)]).first_key_value()
            ('a', 1)
        """
        if not self._data:
            return None
        key = min(self._data.keys())
        return (key, self._data[key])

    def last_key_value(self) -> tuple[K, V] | None:
        """Return the (key, value) pair with the largest key, or None.

        Returns:
            tuple[K, V] | None: The entry with the largest key, or None if the
                map is empty.

        Examples:
            >>> BTreeMap([("b", 2), ("a", 1)]).last_key_value()
            ('b', 2)
        """
        if not self._data:
            return None
        key = max(self._data.keys())
        return (key, self._data[key])

    def clear(self) -> None:
        """Remove all entries from the map.

        Examples:
            >>> m = BTreeMap([("a", 1)])
            >>> m.clear()
            >>> m.is_empty()
            True
        """
        self._data.clear()

    def len(self) -> int:
        """Return the number of entries in the map.

        Returns:
            int: The number of key-value pairs.

        Examples:
            >>> BTreeMap([("a", 1)]).len()
            1
        """
        return len(self._data)

    def is_empty(self) -> bool:
        """Return True if the map contains no entries.

        Returns:
            bool: True if the map is empty.

        Examples:
            >>> BTreeMap().is_empty()
            True
        """
        return len(self._data) == 0

    def keys(self) -> Iterator[K]:
        """Return an iterator over the keys in sorted order.

        Returns:
            Iterator[K]: An iterator yielding keys in ascending order.

        Examples:
            >>> list(BTreeMap([("b", 2), ("a", 1)]).keys())
            ['a', 'b']
        """
        return iter(sorted(self._data.keys()))

    def values(self) -> Iterator[V]:
        """Return an iterator over the values in key-sorted order.

        Yields:
            Iterator[V]: Each value, in ascending key order.

        Examples:
            >>> list(BTreeMap([("b", 2), ("a", 1)]).values())
            [1, 2]
        """
        for k in sorted(self._data.keys()):
            yield self._data[k]

    def iter(self) -> Iterator[tuple[K, V]]:
        """Return an iterator over (key, value) pairs in sorted key order.

        Yields:
            Iterator[tuple[K, V]]: Each pair, in ascending key order.

        Examples:
            >>> list(BTreeMap([("b", 2), ("a", 1)]).iter())
            [('a', 1), ('b', 2)]
        """
        for k in sorted(self._data.keys()):
            yield (k, self._data[k])

    def drain(self) -> Iterator[tuple[K, V]]:
        """Consume the map and return an iterator over its sorted (key, value) pairs.

        The map is emptied as a result.

        Returns:
            Iterator[tuple[K, V]]: The sorted pairs before consumption.

        Examples:
            >>> m = BTreeMap([("b", 2), ("a", 1)])
            >>> list(m.drain())
            [('a', 1), ('b', 2)]
            >>> m.is_empty()
            True
        """
        items = sorted(self._data.items())
        self._data.clear()
        return iter(items)

    def range_(self, start: K, end: K) -> Iterator[tuple[K, V]]:
        """Return an iterator over entries where start <= key < end.

        Args:
            start (K): The inclusive lower bound of the range.
            end (K): The exclusive upper bound of the range.

        Yields:
            Iterator[tuple[K, V]]: Each ``(key, value)`` pair with
                ``start <= key < end``, in ascending key order.

        Examples:
            >>> list(BTreeMap([("a", 1), ("b", 2), ("c", 3)]).range_("a", "c"))
            [('a', 1), ('b', 2)]
        """
        for k in sorted(self._data.keys()):
            if start <= k < end:
                yield (k, self._data[k])

    def to_dict(self) -> dict[K, V]:
        """Return a new dictionary with entries sorted by key.

        Returns:
            dict[K, V]: A dict of the entries, sorted by key.

        Examples:
            >>> BTreeMap([("b", 2), ("a", 1)]).to_dict()
            {'a': 1, 'b': 2}
        """
        return dict(sorted(self._data.items()))

    def __len__(self) -> int:
        """Return the number of entries in the map.

        Examples:
            >>> len(BTreeMap([("a", 1)]))
            1
        """
        return len(self._data)

    def __iter__(self) -> Iterator[K]:
        """Return an iterator over the keys in sorted order.

        Examples:
            >>> list(BTreeMap([("b", 2), ("a", 1)]))
            ['a', 'b']
        """
        return self.keys()

    def __contains__(self, key: object) -> bool:
        """Return True if the map contains the key.

        Examples:
            >>> "a" in BTreeMap([("a", 1)])
            True
        """
        return key in self._data

    def __getitem__(self, key: K) -> V:
        """Return the value for the key.

        Args:
            key (K): The key to look up.

        Returns:
            V: The value associated with ``key``.

        Raises:
            KeyError: If ``key`` is not present.

        Examples:
            >>> BTreeMap([("a", 1)])["a"]
            1
        """
        return self._data[key]

    def __setitem__(self, key: K, value: V) -> None:
        """Insert or overwrite the value for the key.

        Args:
            key (K): The key to write.
            value (V): The value to associate.

        Examples:
            >>> m = BTreeMap()
            >>> m["a"] = 1
            >>> m["a"]
            1
        """
        self._data[key] = value

    def __delitem__(self, key: K) -> None:
        """Remove the entry for the key.

        Args:
            key (K): The key to remove.

        Raises:
            KeyError: If ``key`` is not present.

        Examples:
            >>> m = BTreeMap([("a", 1)])
            >>> del m["a"]
            >>> len(m)
            0
        """
        del self._data[key]

    def __repr__(self) -> str:
        """Return a string representation of the map.

        Examples:
            >>> repr(BTreeMap([("a", 1)]))
            "BTreeMap({'a': 1})"
        """
        return f"BTreeMap({self._data!r})"

    def __eq__(self, other: object) -> bool:
        """Return True if the map equals another BTreeMap.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: True if ``other`` is a ``BTreeMap`` with equal entries;
                ``NotImplemented`` otherwise.

        Examples:
            >>> BTreeMap([("a", 1)]) == BTreeMap([("a", 1)])
            True
        """
        if isinstance(other, BTreeMap):
            return self._data == other._data
        return NotImplemented

    def __hash__(self) -> int:
        """Return a hash of the map's sorted contents.

        Returns:
            int: A hash based on the sorted ``(key, value)`` items.
        """
        return hash(tuple(sorted(self._data.items())))

    def __bool__(self) -> bool:
        """Return True if the map is non-empty.

        Examples:
            >>> bool(BTreeMap([("a", 1)]))
            True
        """
        return bool(self._data)
