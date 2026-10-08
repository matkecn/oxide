"""Lua-inspired utilities."""
from __future__ import annotations

from typing import Any, Callable, List, Tuple

class Coroutine:
    def __init__(self, func: Callable):
        self._func = func

class MetaTable(dict):
    pass

class Table(dict):
    pass

class Script:
    def __init__(self, code: str = ""):
        self.code = code
    def run(self):
        return True

class Function:
    def __init__(self, func: Callable):
        self._func = func
    def __call__(self, *a, **kw):
        return self._func(*a, **kw)

class MultiReturn:
    def __init__(self, *values):
        self.values = values
    def __iter__(self):
        return iter(self.values)

__all__ = ["Coroutine", "MetaTable", "Table", "Script", "Function", "MultiReturn"]
