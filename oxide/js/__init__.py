"""JavaScript-inspired utilities."""
from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Iterable

class Promise:
    """Simple Promise-like wrapper."""
    def __init__(self, coro: Awaitable[Any] | None = None):
        self._coro = coro
        self._result: Any = None
        self._error: Exception | None = None
        self._done = False

    @classmethod
    def resolve(cls, value: Any) -> 'Promise':
        p = cls()
        p._result = value
        p._done = True
        return p

    @classmethod
    def reject(cls, error: Exception) -> 'Promise':
        p = cls()
        p._error = error
        p._done = True
        return p

    async def _run(self):
        if self._coro is not None:
            try:
                self._result = await self._coro
            except Exception as e:
                self._error = e
            self._done = True
            return self._result
        return self._result

    def __await__(self):
        return self._run().__await__()

async def all(promises: Iterable[Any]) -> list[Any]:
    return await asyncio.gather(*promises)

async def race(promises: Iterable[Any]) -> Any:
    done, pending = await asyncio.wait(
        [asyncio.ensure_future(p) if hasattr(p, '__await__') else asyncio.ensure_future(asyncio.sleep(0, result=p)) for p in promises],
        return_when=asyncio.FIRST_COMPLETED
    )
    for p in pending:
        p.cancel()
    return done.pop().result()

__all__ = ["Promise", "all", "race"]
