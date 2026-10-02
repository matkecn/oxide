"""Rust-inspired collection types — Vec, HashMap, HashSet, BTreeMap, and more.

This package provides the public collection types of the ``oxide`` library,
mirroring the standard collections of the Rust standard library: ``Vec``,
``HashMap``, ``HashSet``, ``BTreeMap``, ``BTreeSet``, ``VecDeque``,
``BinaryHeap``, and ``LinkedList``, plus supporting types ``Drain``,
``IntoIter``, and ``Slice``.
"""
from __future__ import annotations

from .vec import Vec
from .hashmap import HashMap, Entry, OccupiedEntry, VacantEntry
from .hashset import HashSet
from .btreemap import BTreeMap
from .btreeset import BTreeSet
from .vecdeque import VecDeque
from .binary_heap import BinaryHeap
from .linked_list import LinkedList
from .extra import Drain, IntoIter, Slice

__all__ = [
    "Vec",
    "HashMap",
    "HashSet",
    "BTreeMap",
    "BTreeSet",
    "VecDeque",
    "BinaryHeap",
    "LinkedList",
    "Drain",
    "IntoIter",
    "Slice",
    "Entry",
    "OccupiedEntry",
    "VacantEntry",
]
