"""Async utilities - Promise-like helpers."""
from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Iterable, TypeVar

T = TypeVar("T")
U = TypeVar("U")


async def gather(*aws: Awaitable[Any]) -> list[Any]:
    return await asyncio.gather(*aws)


async def all_settled(*aws: Awaitable[Any]) -> list[Any]:
    return await asyncio.gather(*aws, return_exceptions=True)


async def race(*aws: Awaitable[Any]) -> Any:
    done, pending = await asyncio.wait(
        [asyncio.ensure_future(a) for a in aws], return_when=asyncio.FIRST_COMPLETED
    )
    for p in pending:
        p.cancel()
    return done.pop().result()


async def sleep(seconds: float) -> None:
    await asyncio.sleep(seconds)


__all__ = ["gather", "all_settled", "race", "sleep"]
