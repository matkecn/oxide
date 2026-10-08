"""Extended JS utilities."""
from __future__ import annotations

import asyncio
import queue
from typing import Any, Callable

# Reuse from js
from ..js import Promise, all, race

class EventEmitter:
    def __init__(self):
        self._listeners = {}
    def on(self, event: str, listener: Callable):
        self._listeners.setdefault(event, []).append(listener)
        return self
    def emit(self, event: str, *args):
        for l in self._listeners.get(event, []):
            l(*args)
        return True

class EventLoop:
    def run_until_complete(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

class Proxy:
    def __init__(self, target, handler=None):
        self._target = target
        self._handler = handler

class Symbol:
    def __init__(self, name: str = ""):
        self.name = name
    def __repr__(self):
        return f"Symbol({self.name})"

class Uint8Array(list):
    pass

class Float32Array(list):
    pass

class ArrayBuffer:
    def __init__(self, size: int = 0):
        self._data = bytearray(size)
    def __len__(self):
        return len(self._data)

class WeakMap(dict):
    pass

class WeakSet(set):
    pass

def load_module(name: str):
    import importlib
    return importlib.import_module(name)

class Generator:
    def __init__(self, gen):
        self._gen = gen
    def __iter__(self):
        return iter(self._gen)
    def __next__(self):
        return next(self._gen)

class AsyncIterator:
    def __init__(self, agen):
        self._agen = agen
    def __aiter__(self):
        return self
    async def __anext__(self):
        try:
            return await self._agen.__anext__()
        except StopAsyncIteration:
            raise

__all__ = ["Promise", "all", "race", "EventEmitter", "EventLoop", "Proxy", "Symbol", "Uint8Array", "Float32Array", "ArrayBuffer", "WeakMap", "WeakSet", "load_module", "Generator", "AsyncIterator"]
