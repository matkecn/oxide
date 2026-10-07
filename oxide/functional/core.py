"""Core functional utilities."""
from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

T = TypeVar("T")
U = TypeVar("U")


def identity(x: T) -> T:
    return x


def constant(x: T) -> Callable[..., T]:
    def _const(*args: Any, **kwargs: Any) -> T:
        return x
    return _const


def flip(f: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(f)
    def flipped(*args: Any) -> Any:
        if len(args) >= 2:
            return f(args[1], args[0], *args[2:])
        return f(*args)
    return flipped


def partial(f: Callable[..., Any], *args: Any, **kwargs: Any) -> Callable[..., Any]:
    @wraps(f)
    def _partial(*more_args: Any, **more_kwargs: Any) -> Any:
        return f(*args, *more_args, **{**kwargs, **more_kwargs})
    return _partial


def pipe(*funcs: Callable[..., Any]) -> Callable[..., Any]:
    def pipeline(x: Any) -> Any:
        result = x
        for f in funcs:
            result = f(result)
        return result
    return pipeline


def compose(*funcs: Callable[..., Any]) -> Callable[..., Any]:
    def composed(x: Any) -> Any:
        result = x
        for f in reversed(funcs):
            result = f(result)
        return result
    return composed


def curry(f: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(f)
    def curried(*args: Any) -> Any:
        if len(args) >= f.__code__.co_argcount:
            return f(*args)
        return lambda *more: curried(*(args + more))
    return curried


def memoize(f: Callable[..., Any]) -> Callable[..., Any]:
    cache: dict = {}

    @wraps(f)
    def memoized(*args: Any, **kwargs: Any) -> Any:
        key = (args, frozenset(kwargs.items()))
        if key not in cache:
            cache[key] = f(*args, **kwargs)
        return cache[key]
    return memoized


def once(f: Callable[..., Any]) -> Callable[..., Any]:
    called = False
    result = None

    @wraps(f)
    def onced(*args: Any, **kwargs: Any) -> Any:
        nonlocal called, result
        if not called:
            result = f(*args, **kwargs)
            called = True
        return result
    return onced
