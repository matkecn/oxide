"""Concurrent execution utilities."""
from __future__ import annotations

import concurrent.futures
from typing import Any, Callable, Iterable, TypeVar

T = TypeVar("T")


def map_parallel(func: Callable[..., T], iterable: Iterable[Any], max_workers: int | None = None) -> list[T]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(func, iterable))


def submit_parallel(*callables: Callable[[], Any], max_workers: int | None = None) -> list[Any]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(c) for c in callables]
        return [f.result() for f in futures]


__all__ = ["map_parallel", "submit_parallel"]
