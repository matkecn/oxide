"""Core types inspired by C++/Rust."""
from __future__ import annotations

# Reuse existing
from ..core.option import Option, Some, None_
from ..core.result import Result, Ok, Err

# Aliases for C++ style names
Optional = Option
Variant = None  # placeholder
Expected = Result
Span = None  # placeholder

__all__ = [
    "Option", "Some", "None_", "Optional",
    "Result", "Ok", "Err", "Expected",
    "Variant", "Span",
]
