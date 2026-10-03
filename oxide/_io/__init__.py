"""I/O abstractions — Read, Write, BufRead, BufReader, BufWriter, Cursor.

Provides Read, Write, BufRead traits, BufReader, BufWriter, Cursor,
and SeekFrom for in-memory and stream I/O.
"""
from __future__ import annotations

from .read import Read, BufRead, BufSplitIter, LinesIter
from .write import Write
from .buffered import BufReader, BufWriter
from .cursor import Cursor, SeekFrom

__all__ = [
    "Read",
    "BufRead",
    "BufSplitIter",
    "LinesIter",
    "Write",
    "BufReader",
    "BufWriter",
    "Cursor",
    "SeekFrom",
]
