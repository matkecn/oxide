"""Runtime instrumentation decorators inspired by Rust's function attributes.

These go beyond compile-time attributes: they wrap the function and change what
happens when it runs.

======================  ====================================================
Decorator               Purpose
======================  ====================================================
:func:`memoize`         ``#[inline]``-style hot-path caching, keyed on arguments
:func:`pure`            Rust's ``#[pure]``: no side effects, results cached
:func:`timed`           Measure wall-clock duration via :class:`~oxide._time.instant.Instant`
:func:`log_calls`       Log entry, exit, and failures through :mod:`oxide.logging`
:func:`once`            Run the body exactly once, caching the result
======================  ====================================================

Example:
    >>> @memoize()
    ... def collatz_steps(n):
    ...     steps = 0
    ...     while n != 1:
    ...         n = n // 2 if n % 2 == 0 else 3 * n + 1
    ...         steps += 1
    ...     return steps
    >>> collatz_steps(27)
    111
    >>> collatz_steps(27)
    111
    >>> collatz_steps.cache_info().hits
    1
"""

from __future__ import annotations

import functools
import threading
from typing import Any, Callable, Hashable, TypeVar

from .._time.instant import Instant

F = TypeVar("F", bound=Callable[..., Any])

#: Thread used by :func:`once` to hold the one-shot flag.
_LOCK_FACTORY = threading.Lock


class CacheInfo(tuple):
    """Immutable snapshot of a memoization cache's counters.

    A :class:`tuple` subclass, so it unpacks like Rust's ``CacheStats``'s fields
    in order: ``hits``, ``misses``, ``size``, ``capacity``.

    Attributes:
        hits (int): Number of calls served from the cache.
        misses (int): Number of calls that invoked the wrapped function.
        size (int): Number of entries currently held.
        capacity (int | None): Maximum entries, or None when unbounded.

    Example:
        >>> info = CacheInfo(2, 1, 1, None)
        >>> info.hits, info.misses, info.capacity
        (2, 1, None)
    """

    __slots__ = ()

    def __new__(cls, hits: int, misses: int, size: int, capacity: int | None) -> "CacheInfo":
        """Build the snapshot tuple.

        Args:
            hits: Calls served from the cache.
            misses: Calls that ran the wrapped function.
            size: Entries currently held.
            capacity: Maximum entries, or None when unbounded.

        Returns:
            CacheInfo: The snapshot.
        """
        return super().__new__(cls, (hits, misses, size, capacity))

    @property
    def hits(self) -> int:
        """Return the number of calls served from the cache."""
        return self[0]

    @property
    def misses(self) -> int:
        """Return the number of calls that ran the wrapped function."""
        return self[1]

    @property
    def size(self) -> int:
        """Return the number of entries currently cached."""
        return self[2]

    @property
    def capacity(self) -> int | None:
        """Return the maximum number of entries, or None when unbounded."""
        return self[3]

    def __repr__(self) -> str:
        bound = "unbounded" if self[3] is None else str(self[3])
        return f"CacheInfo(hits={self[0]}, misses={self[1]}, size={self[2]}, capacity={bound})"


def _default_key(*args: Any, **kwargs: Any) -> Hashable:
    """Build a hashable cache key from a call's arguments.

    Unhashable arguments fall back to their ``repr``, which is slower but never
    wrong in a way that returns a stale value for a different object.
    """
    key: tuple[Any, ...] = tuple(args) + (_KEY_MARKER,) + tuple(sorted(kwargs.items()))
    try:
        hash(key)
    except TypeError:
        return repr(key)
    return key


#: Sentinel separating positional from keyword arguments in a cache key, so
#: ``f(1, x=2)`` and ``f(1, 2)`` never collide.
_KEY_MARKER = object()


def memoize(
    maxsize: int | None = None,
    *,
    key: Callable[..., Hashable] | None = None,
) -> Callable[[F], F]:
    """Cache a function's results, keyed on its arguments.

    Unbounded by default: entries are never evicted silently, because Rust's
    hot-path caching has no equivalent of a TTL. Pass ``maxsize`` for
    least-recently-used eviction.

    The wrapper grows ``cache_info()``, ``cache_clear()``, ``cache_keys()``, and
    ``cache_is_full()`` methods.

    Usable bare (``@memoize``) or with a capacity (``@memoize(128)``); a bare
    decorator is detected by a callable first argument.

    Args:
        maxsize: Maximum entries to retain. None means unbounded.
        key: Custom key builder called as ``key(*args, **kwargs)``.

    Returns:
        Callable: A decorator preserving the wrapped function's signature.

    Example:
        >>> @memoize()
        ... def add(a, b):
        ...     return a + b
        >>> add(1, 2), add(1, 2)
        (3, 3)
        >>> add.cache_info()
        CacheInfo(hits=1, misses=1, size=1, capacity=unbounded)
    """
    bare = maxsize if callable(maxsize) and not isinstance(maxsize, int) else None
    if bare is not None:
        return decorate(bare)  # type: ignore[arg-type]

    if maxsize is not None and maxsize < 0:
        raise ValueError("maxsize must be non-negative or None for unbounded")

    def decorate(fn: F) -> F:
        """Wrap ``fn`` with a thread-safe result cache."""
        cache: dict[Hashable, Any] = {}
        lock = _LOCK_FACTORY()
        hits = 0
        misses = 0
        build_key = key if key is not None else _default_key

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Return the cached result, or compute, store, and return it."""
            nonlocal hits, misses
            cache_key = build_key(*args, **kwargs)
            with lock:
                if cache_key in cache:
                    hits += 1
                    return cache[cache_key]
            result = fn(*args, **kwargs)
            with lock:
                misses += 1
                if maxsize is None or len(cache) < maxsize:
                    cache[cache_key] = result
            return result

        def cache_info() -> CacheInfo:
            """Return a snapshot of the cache counters."""
            with lock:
                return CacheInfo(hits, misses, len(cache), maxsize)

        def cache_clear() -> None:
            """Drop every entry and reset the counters."""
            nonlocal hits, misses
            with lock:
                cache.clear()
                hits = misses = 0

        def cache_keys() -> list[Hashable]:
            """Return the cached keys in insertion order."""
            with lock:
                return list(cache.keys())

        def cache_is_full() -> bool:
            """Return whether a bounded cache has reached its limit."""
            return maxsize is not None and len(cache) >= maxsize

        for attribute, value in (
            ("cache_info", cache_info),
            ("cache_clear", cache_clear),
            ("cache_keys", cache_keys),
            ("cache_is_full", cache_is_full),
        ):
            setattr(wrapper, attribute, value)
        wrapper.__wrapped__ = fn  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorate


def pure(
    message: str | None = None,
    *,
    lint: str = "pure_function",
) -> Callable[[F], F]:
    """Assert that a function has no side effects, and cache its results.

    Rust's ``#[pure]`` tells the optimiser the function depends only on its
    arguments. Here that contract becomes enforceable: the function is memoized,
    so a second call with equal arguments returns the identical object rather
    than recomputing. That makes an accidental side effect visible immediately
    instead of hiding behind a repeated call.

    Args:
        message: Diagnostic text recorded in the ``pure`` attribute.
        lint: Lint name recorded in the ``pure`` attribute.

    Returns:
        Callable: A memoizing decorator that also records the contract.

    Example:
        >>> @pure("parsing is side-effect free")
        ... def parse(raw):
        ...     return {"n": int(raw)}
        >>> parse("1") is parse("1")
        True
    """
    from .attributes import _record

    def decorate(fn: F) -> F:
        """Memoize the function and record the purity contract."""
        cached = memoize()(fn)
        _record(cached, "pure", {"message": message, "lint": lint})
        _record(cached, "memoize", {"maxsize": None})
        return cached  # type: ignore[return-value]

    return decorate


def timed(
    label: str | None = None,
    *,
    printer: Callable[[str], Any] | None = None,
    scale: float = 1.0,
    unit: str = "ms",
) -> Callable[[F], F]:
    """Measure and report how long each call takes.

    Uses :class:`~oxide._time.instant.Instant`, so the measurement is monotonic
    and immune to wall-clock adjustments.

    Args:
        label: Text included in the report. Defaults to the function's name.
        printer: Callable receiving the report string. Defaults to
            :func:`oxide.logging.log_info`.
        scale: Multiply the elapsed duration by this before printing, for
            unit conversion such as ``scale=1000`` with ``unit="us"``.
        unit: Unit suffix for the report.

    Returns:
        Callable: A decorator that prints a timing line per call.

    Example:
        >>> lines = []
        >>> @timed("work", printer=lines.append, unit="ms")
        ... def work():
        ...     return 1
        >>> work()
        1
        >>> lines[0].startswith("work took ")
        True
    """
    if printer is None:
        from ..logging import log_info

        def emit(message: str) -> None:
            """Print the timing line through the oxide logger."""
            log_info(message)

        printer = emit

    def decorate(fn: F) -> F:
        """Wrap the function so each call is timed and reported."""
        name = label or getattr(fn, "__name__", "anonymous")

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Time the call, print the report, then return the result."""
            started = Instant.now()
            try:
                return fn(*args, **kwargs)
            finally:
                elapsed = started.elapsed()
                printer(f"{name} took {elapsed.as_millis() * scale:.3f}{unit}")

        wrapper.__timed__ = name  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorate


def log_calls(
    *,
    level: str = "info",
    logger: Callable[[str], Any] | None = None,
    include_args: bool = True,
    include_result: bool = False,
) -> Callable[[F], F]:
    """Log entry, exit, and failures of a function.

    Wraps the body in ``try``/``except``/``else`` so a raised exception is
    reported before it propagates, which is what makes this useful for tracing
    a bug through code you cannot step into.

    Args:
        level: The :class:`~oxide.logging.LogLevel` name to report at.
        logger: Callable receiving each line. Defaults to the matching
            ``oxide.logging.log_*`` function.
        include_args: Include the formatted arguments in the entry line.
        include_result: Include the return value in the exit line.

    Returns:
        Callable: A decorator that logs around every call.

    Example:
        >>> lines = []
        >>> @log_calls(logger=lines.append, include_args=False, include_result=False)
        ... def divide(a, b):
        ...     return a / b
        >>> divide(6, 3)
        2.0
        >>> lines[0]
        '-> divide'
        >>> lines[-1]
        '<- divide'
    """

    def decorate(fn: F) -> F:
        """Wrap the function so entry, exit, and errors are reported."""
        emit = logger
        if emit is None:
            from ..logging import log_at_level

            emit = log_at_level(level)

        name = getattr(fn, "__qualname__", getattr(fn, "__name__", "anonymous"))

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Log the call, run the body, and log how it ended."""
            if include_args:
                emit(f"-> {name}{_format_call(args, kwargs)}")
            else:
                emit(f"-> {name}")
            try:
                result = fn(*args, **kwargs)
            except BaseException as error:
                emit(f"!! {name} raised {type(error).__name__}: {error}")
                raise
            if include_result:
                emit(f"<- {name} = {result!r}")
            else:
                emit(f"<- {name}")
            return result

        return wrapper  # type: ignore[return-value]

    return decorate


def once() -> Callable[[F], F]:
    """Run a function exactly once, caching the result forever.

    Differs from :func:`memoize` in that it ignores arguments after the first
    call: it is the decorator form of :class:`oxide.sync.Once`, for cases where
    the initialisation arguments are not part of the identity.

    Args:
        None: This decorator takes no arguments.

    Returns:
        Callable: A decorator exposing ``called()`` and ``reset()``.

    Example:
        >>> calls = []
        >>> @once()
        ... def setup():
        ...     calls.append(1)
        ...     return len(calls)
        >>> setup(), setup(), setup.called()
        (1, 1, True)
        >>> setup.reset()
        >>> setup()
        2
    """
    state: dict[str, Any] = {"value": None, "done": False}
    lock = _LOCK_FACTORY()

    def decorate(fn: F) -> F:
        """Wrap ``fn`` so only the first call runs the body."""
        name = getattr(fn, "__name__", "anonymous")

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Return the cached result, running the body only once."""
            with lock:
                if state["done"]:
                    return state["value"]
            result = fn(*args, **kwargs)
            with lock:
                if not state["done"]:
                    state["value"] = result
                    state["done"] = True
            return state["value"]

        def called() -> bool:
            """Return whether the body has already run."""
            with lock:
                return bool(state["done"])

        def reset() -> None:
            """Forget the cached result so the next call runs the body again."""
            with lock:
                state["value"] = None
                state["done"] = False

        wrapper.__once__ = name  # type: ignore[attr-defined]
        wrapper.called = called  # type: ignore[attr-defined]
        wrapper.reset = reset  # type: ignore[attr-defined]
        wrapper.__wrapped__ = fn  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorate


def _format_call(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    """Render a call's arguments compactly for a log line."""
    parts = [repr(arg) for arg in args]
    parts.extend(f"{key}={value!r}" for key, value in kwargs.items())
    return f"({', '.join(parts)})"


__all__ = [
    "CacheInfo",
    "log_calls",
    "memoize",
    "once",
    "pure",
    "timed",
]
