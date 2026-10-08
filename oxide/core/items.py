"""Rust item attributes that :mod:`oxide.derive` does not already cover.

:mod:`oxide.derive` emulates the attributes that shape a *type's* generated
code — ``#[derive]``, the lint levels, ``#[cfg]``, ``#[deprecated]``. This module
adds the attributes Rust attaches to *items* (functions, modules, crates) and the
test-harness attributes, giving one place to look for the whole set.

Most are metadata. Rust's ``#[no_mangle]``, ``#[used]``, and ``#[cold]`` steer
code generation, which Python has no equivalent for, so they are recorded and
readable through :func:`~oxide.derive.attributes.attributes_of` — the same
treatment :func:`~oxide.derive.attributes.inline` already gets. Three have real
behaviour here: :func:`repr_`, :func:`track_caller`, and :func:`main`.

The test attributes are the exception worth calling out. ``#[test]``, ``#[bench]``,
``#[ignore]``, ``#[should_panic]``, and ``#[serial]`` are emulated for real:
marked functions are collected into registries that :func:`run_tests` executes,
honouring each attribute.

Example:
    >>> from oxide.core import no_mangle, repr_, repr_kinds_of, test, run_tests
    >>> @no_mangle
    ... def entry_point():
    ...     return 1
    >>> entry_point()
    1
    >>> @repr_("transparent")
    ... class Handle:
    ...     __slots__ = ("raw",)
    ...     def __init__(self, raw):
    ...         self.raw = raw
    >>> repr_kinds_of(Handle)
    ('transparent',)
    >>> @test
    ... def test_always_passes():
    ...     return None
    >>> result = run_tests()
    >>> result.passed, result.failed
    (('test_always_passes',), ())
"""

from __future__ import annotations

import asyncio
import functools
import inspect
from typing import Any, Callable, NamedTuple, TypeVar

from ..core.error import Location
from ..derive.attributes import _record

F = TypeVar("F", bound=Callable[..., Any])

__all__ = [
    "TestResult",
    "caller_location",
    "cold",
    "crate_name",
    "crate_type",
    "ignored_reason",
    "ignore",
    "is_ignored",
    "is_serial",
    "is_test",
    "link",
    "link_name",
    "main",
    "naked",
    "no_mangle",
    "path",
    "repr_",
    "repr_kinds_of",
    "benches",
    "run_tests",
    "serial",
    "should_panic",
    "should_panic_of",
    "test",
    "track_caller",
    "tests",
    "used",
]


# --------------------------------------------------------------------------
# Symbol and code-generation attributes
# --------------------------------------------------------------------------


def no_mangle(target: F) -> F:
    """Record Rust's ``#[no_mangle]``, suppressing symbol name mangling.

    Python names are already stable, so this is metadata that documents the
    intent of an exported entry point.

    Args:
        target: The function to mark.

    Returns:
        The function, unchanged.

    Example:
        >>> from oxide.core import no_mangle
        >>> from oxide.derive.attributes import find_attribute
        >>> @no_mangle
        ... def exported():
        ...     return 1
        >>> find_attribute(exported, "no_mangle")["enabled"]
        True
    """
    _record(target, "no_mangle", {"enabled": True})
    return target


def used(target: F) -> F:
    """Record Rust's ``#[used]``, keeping an otherwise unreferenced item alive.

    Args:
        target: The function or value to mark.

    Returns:
        The target, unchanged.

    Example:
        >>> from oxide.core import used
        >>> from oxide.derive.attributes import find_attribute
        >>> @used
        ... def vtable_entry():
        ...     return None
        >>> find_attribute(vtable_entry, "used")["kept"]
        True
    """
    _record(target, "used", {"kept": True})
    return target


def cold(target: F) -> F:
    """Record Rust's ``#[cold]``, marking a function as unlikely to be called.

    Args:
        target: The function to mark.

    Returns:
        The function, unchanged.

    Example:
        >>> from oxide.core import cold
        >>> from oxide.derive.attributes import find_attribute
        >>> @cold
        ... def unreachable_default():
        ...     raise AssertionError
        >>> find_attribute(unreachable_default, "cold")["unlikely"]
        True
    """
    _record(target, "cold", {"unlikely": True})
    return target


def naked(target: F) -> F:
    """Record Rust's ``#[naked]``, prohibiting prologue and epilogue generation.

    Args:
        target: The function to mark.

    Returns:
        The function, unchanged.

    Example:
        >>> from oxide.core import naked
        >>> from oxide.derive.attributes import find_attribute
        >>> @naked
        ... def entry():
        ...     return None
        >>> find_attribute(entry, "naked")["bare"]
        True
    """
    _record(target, "naked", {"bare": True})
    return target


def link(name: str, *, kind: str = "static") -> Callable[[Any], Any]:
    """Record Rust's ``#[link(name = "...", kind = "...")]`` native linkage.

    Args:
        name: The library to link against.
        kind: The linkage kind, such as ``"static"``, ``"dylib"``, or
            ``"framework"``.

    Returns:
        Callable: A decorator returning the target unchanged.

    Example:
        >>> from oxide.core import link
        >>> from oxide.derive.attributes import find_attribute
        >>> @link("m", kind="static")
        ... def call_libm(x):
        ...     return x
        >>> find_attribute(call_libm, "link")["name"]
        'm'
    """

    def decorate(target: Any) -> Any:
        """Record the linkage request and return the target unchanged.

        Args:
            target: The function to mark.

        Returns:
            The target, unchanged.
        """
        _record(target, "link", {"name": name, "kind": kind})
        return target

    return decorate


def link_name(name: str) -> Callable[[Any], Any]:
    """Record Rust's ``#[link_name = "..."]`` explicit symbol name.

    Args:
        name: The symbol name to link.

    Returns:
        Callable: A decorator returning the target unchanged.

    Example:
        >>> from oxide.core import link_name
        >>> from oxide.derive.attributes import find_attribute
        >>> @link_name("memcpy")
        ... def copy_bytes():
        ...     return None
        >>> find_attribute(copy_bytes, "link_name")["name"]
        'memcpy'
    """

    def decorate(target: Any) -> Any:
        """Record the link name and return the target unchanged.

        Args:
            target: The function to mark.

        Returns:
            The target, unchanged.
        """
        _record(target, "link_name", {"name": name})
        return target

    return decorate


def crate_type(name: str) -> Callable[[Any], Any]:
    """Record Rust's ``#[crate_type = "..."]`` output artifact kind.

    Args:
        name: The artifact kind, such as ``"lib"``, ``"cdylib"``, or ``"bin"``.

    Returns:
        Callable: A decorator returning the target unchanged.

    Example:
        >>> from oxide.core import crate_type
        >>> from oxide.derive.attributes import find_attribute
        >>> @crate_type("cdylib")
        ... class Plugin:
        ...     pass
        >>> find_attribute(Plugin, "crate_type")["name"]
        'cdylib'
    """

    def decorate(target: Any) -> Any:
        """Record the crate type and return the target unchanged.

        Args:
            target: The item to mark.

        Returns:
            The target, unchanged.
        """
        _record(target, "crate_type", {"name": name})
        return target

    return decorate


def crate_name(name: str) -> Callable[[Any], Any]:
    """Record Rust's ``#[crate_name = "..."]``.

    Args:
        name: The crate name to record.

    Returns:
        Callable: A decorator returning the target unchanged.

    Example:
        >>> from oxide.core import crate_name
        >>> from oxide.derive.attributes import find_attribute
        >>> @crate_name("oxide_core")
        ... class Root:
        ...     pass
        >>> find_attribute(Root, "crate_name")["name"]
        'oxide_core'
    """

    def decorate(target: Any) -> Any:
        """Record the crate name and return the target unchanged.

        Args:
            target: The item to mark.

        Returns:
            The target, unchanged.
        """
        _record(target, "crate_name", {"name": name})
        return target

    return decorate


def path(value: str) -> Callable[[Any], Any]:
    """Record Rust's ``#[path = "..."]``, remapping where a module is loaded from.

    Args:
        value: The filesystem path the module should come from.

    Returns:
        Callable: A decorator returning the target unchanged.

    Example:
        >>> from oxide.core import path
        >>> from oxide.derive.attributes import find_attribute
        >>> @path("vendor/extra.rs")
        ... class Extra:
        ...     pass
        >>> find_attribute(Extra, "path")["value"]
        'vendor/extra.rs'
    """

    def decorate(target: Any) -> Any:
        """Record the path remap and return the target unchanged.

        Args:
            target: The module to mark.

        Returns:
            The target, unchanged.
        """
        _record(target, "path", {"value": value})
        return target

    return decorate


def repr_(*kinds: str) -> Callable[[Any], Any]:
    """Record Rust's ``#[repr(...)]`` layout hint, which has behaviour here.

    Rust's ``#[repr(transparent)]`` promises a type has exactly one
    non-zero-sized field and may be transmuted to it. That is a real guarantee,
    so :meth:`~oxide.derive.attributes.is_transparent` reports it, and
    :func:`repr_kinds_of` reads back whatever was recorded.

    Args:
        *kinds: Layout kinds, such as ``"transparent"``, ``"C"``, or ``"u8"``.

    Returns:
        Callable: A decorator returning the target unchanged.

    Raises:
        ValueError: If no kind is given.

    Example:
        >>> from oxide.core import repr_
        >>> from oxide.derive.attributes import find_attribute
        >>> @repr_("transparent")
        ... class Wrapper:
        ...     __slots__ = ("inner",)
        >>> find_attribute(Wrapper, "repr")["kinds"]
        ('transparent',)
        >>> repr_()
        Traceback (most recent call last):
            ...
        ValueError: repr_ requires at least one layout kind
    """
    if not kinds:
        raise ValueError("repr_ requires at least one layout kind")
    normalized = tuple(kinds)

    def decorate(target: Any) -> Any:
        """Record the layout hint and return the target unchanged.

        Args:
            target: The class to mark.

        Returns:
            The target, unchanged.
        """
        _record(target, "repr", {"kinds": normalized})
        return target

    return decorate


def repr_kinds_of(target: Any) -> tuple[str, ...]:
    """Return the layout kinds recorded by :func:`repr_`.

    Args:
        target: A class decorated with ``repr_``.

    Returns:
        tuple: The recorded kinds, or an empty tuple when none were recorded.

    Example:
        >>> from oxide.core import repr_, repr_kinds_of
        >>> @repr_("C", "u64")
        ... class Raw:
        ...     pass
        >>> repr_kinds_of(Raw)
        ('C', 'u64')
        >>> repr_kinds_of(object())
        ()
    """
    from ..derive.attributes import find_attribute

    payload = find_attribute(target, "repr")
    if payload is None:
        return ()
    return tuple(payload.get("kinds", ()))


# --------------------------------------------------------------------------
# Caller tracking
# --------------------------------------------------------------------------


def caller_location(depth: int = 1) -> Location:
    """Return the source location of a frame up the call stack.

    Paired with :func:`track_caller`, this reproduces Rust's
    ``Location::caller()``: a function marked ``#[track_caller]`` that reports
    :func:`caller_location` names the code that *called* it rather than its own
    line.

    Args:
        depth: How many frames to walk back. 0 is the caller's own frame, 1 its
            caller, and so on.

    Returns:
        Location: The resolved location, with empty fields when the stack is
        shallower than ``depth``.

    Example:
        >>> from oxide.core import caller_location
        >>> def report():
        ...     return caller_location()
        >>> def outer():
        ...     return report()
        >>> mine = caller_location()
        >>> theirs = outer()
        >>> mine.line() > 0, theirs.line() > 0
        (True, True)
        >>> theirs.line() != mine.line()
        True
    """
    frame = inspect.currentframe()
    for _ in range(depth + 1):
        if frame is None:
            return Location()
        frame = frame.f_back
    if frame is None:
        return Location()
    return Location(frame.f_code.co_filename, frame.f_lineno)


def track_caller(target: F) -> F:
    """Record Rust's ``#[track_caller]``.

    Combined with :func:`caller_location`, the marked function reports its
    caller's source location instead of its own — the behaviour Rust needs for
    ``unwrap`` and ``expect``.

    Args:
        target: The function to mark.

    Returns:
        The function, unchanged.

    Example:
        >>> from oxide.core import caller_location, track_caller
        >>> @track_caller
        ... def fail(message):
        ...     return f"{message} at {caller_location().file()}"
        >>> fail("boom").endswith("masterclass.py")
        False
        >>> fail("boom").startswith("boom at ")
        True
    """
    _record(target, "track_caller", {"propagates": True})
    return target


def main(target: F | None = None, *, runner: str = "asyncio") -> Any:
    """Emulate ``#[tokio::main]``, running a coroutine function as the entry point.

    The decorated coroutine function is wrapped so that calling it runs the
    event loop to completion and returns the result, matching how an async Rust
    ``main`` returns before the process exits.

    Usable bare or called.

    Args:
        target: The coroutine function, or ``None`` when used as ``@main()``.
        runner: The event loop to drive. Only ``"asyncio"`` is supported.

    Returns:
        The wrapper, or a decorator producing one.

    Raises:
        ValueError: If ``runner`` names an unsupported loop.
        TypeError: If the target is not a coroutine function.

    Example:
        >>> from oxide.core import main
        >>> @main
        ... async def serve():
        ...     return "served"
        >>> serve()
        'served'
        >>> main(runner="trio")
        Traceback (most recent call last):
            ...
        ValueError: unsupported event loop: 'trio'
        >>> main(lambda: None)
        Traceback (most recent call last):
            ...
        TypeError: #[main] expects a coroutine function, got function
    """
    if runner != "asyncio":
        raise ValueError(f"unsupported event loop: {runner!r}")

    def decorate(func: F) -> F:
        """Wrap one coroutine function so calling it drives the event loop.

        Args:
            func: The coroutine function to wrap.

        Returns:
            Callable: A synchronous entry point returning the coroutine's result.

        Raises:
            TypeError: If ``func`` is not a coroutine function.
        """
        if not inspect.iscoroutinefunction(func):
            raise TypeError(
                f"#[main] expects a coroutine function, got {type(func).__name__}"
            )

        @functools.wraps(func)
        def entry(*args: Any, **kwargs: Any) -> Any:
            """Run the wrapped coroutine on a fresh event loop.

            Args:
                *args: Positional arguments for the coroutine function.
                **kwargs: Keyword arguments for the coroutine function.

            Returns:
                Any: The coroutine's result.
            """
            return asyncio.run(func(*args, **kwargs))

        _record(entry, "main", {"runner": runner})
        return entry  # type: ignore[return-value]

    if target is None:
        return decorate
    return decorate(target)


# --------------------------------------------------------------------------
# Test-harness attributes
# --------------------------------------------------------------------------


#: Every function marked ``#[test]``, in decoration order. Modules are told
#: apart by each function's ``__globals__``, so one module's run never picks up
#: another module's tests.
_TESTS: list[Any] = []

#: Every function marked ``#[bench]``, in decoration order.
_BENCHES: list[Any] = []


def _register(function: F, registry: list[Any]) -> F:
    """Add a function to a registry.

    Args:
        function: The function that was just decorated.
        registry: The registry to add it to.

    Returns:
        The function, unchanged, so this can stand in for ``return target``.
    """
    if function not in registry:
        registry.append(function)
    return function


def test(target: F) -> F:
    """Register a function as a test, emulating Rust's ``#[test]``.

    Example:
        >>> from oxide.core import test, is_test
        >>> @test
        ... def test_added():
        ...     assert 1 + 1 == 2
        >>> is_test(test_added)
        True
    """
    _record(target, "test", {"registered": True})
    return _register(target, _TESTS)


def is_test(target: Any) -> bool:
    """Return whether a function is registered as a test.

    Args:
        target: The function to inspect.

    Returns:
        bool: True when the function carries ``#[test]``.

    Example:
        >>> from oxide.core import is_test, test
        >>> @test
        ... def test_marked():
        ...     return None
        >>> def plain():
        ...     return None
        >>> (is_test(test_marked), is_test(plain))
        (True, False)
    """
    from ..derive.attributes import find_attribute

    return find_attribute(target, "test") is not None


def _caller_namespace(skip: int = 0) -> dict[str, Any]:
    """Return the globals of a frame partway up the call stack.

    Rust collects ``#[test]`` items into a per-crate list at compile time, so
    the registry here is global too; :func:`tests` and :func:`benches` filter
    it down to the namespace that asked, which is what keeps one module's tests
    out of another module's run.

    Args:
        skip: Frames to walk past this helper's caller. Zero selects the
            calling function's own globals, one selects *its* caller.

    Returns:
        dict: The resolved frame's globals, or an empty dict when the stack is
        shallower than ``skip``.
    """
    frame = inspect.currentframe()
    for _ in range(skip + 1):
        if frame is None:
            return {}
        frame = frame.f_back
    if frame is None:
        return {}
    return frame.f_globals


def _resolve_namespace(target: Any, skip: int = 0) -> dict[str, Any]:
    """Return the globals a registry lookup should match against.

    Args:
        target: A module, a namespace dict, or None for the calling frame.
        skip: Frames to walk back when ``target`` is None.

    Returns:
        dict: The namespace to filter the registry by, empty when it cannot be
        determined.
    """
    if target is None:
        return _caller_namespace(skip=skip)
    if isinstance(target, dict):
        return target
    return vars(target)


def _registered(namespace: dict[str, Any], registry: list[Any]) -> tuple[Any, ...]:
    """Return the registry entries that belong to a namespace.

    Args:
        namespace: The globals to match against.
        registry: The registry to select from.

    Returns:
        tuple: Matching functions in definition order.
    """
    return tuple(
        function for function in registry if function.__globals__ is namespace
    )


def tests(module: Any = None) -> tuple[Any, ...]:
    """Return every ``#[test]`` function belonging to a module.

    Args:
        module: The module or namespace to select from; the calling module when
            None. Pass it explicitly when running another module's tests, as in
            ``tests(module)`` from a driver.

    Returns:
        tuple: The registered test functions, in definition order.

    Example:
        >>> from oxide.core import test, tests
        >>> @test
        ... def test_one():
        ...     return None
        >>> test_one in tests()
        True
    """
    return _registered(_resolve_namespace(module, skip=2), _TESTS)


def benches(module: Any = None) -> tuple[Any, ...]:
    """Return every ``#[bench]`` function belonging to a module.

    Args:
        module: The module or namespace to select from; the calling module when
            None.

    Returns:
        tuple: The registered benchmark functions, in definition order.

    Example:
        >>> from oxide.core import bench, benches
        >>> @bench
        ... def bench_sum():
        ...     return sum(range(100))
        >>> bench_sum in benches()
        True
    """
    return _registered(_resolve_namespace(module, skip=2), _BENCHES)


def bench(target: F) -> F:
    """Register a function as a benchmark, emulating Rust's ``#[bench]``.

    Args:
        target: The function to register.

    Returns:
        The function, unchanged.

    Example:
        >>> from oxide.core import bench, is_bench
        >>> @bench
        ... def bench_fast():
        ...     return 1
        >>> is_bench(bench_fast)
        True
    """
    _record(target, "bench", {"registered": True})
    return _register(target, _BENCHES)


def is_bench(target: Any) -> bool:
    """Return whether a function is registered as a benchmark.

    Args:
        target: The function to inspect.

    Returns:
        bool: True when the function carries ``#[bench]``.

    Example:
        >>> from oxide.core import bench, is_bench
        >>> @bench
        ... def bench_marked():
        ...     return None
        >>> is_bench(bench_marked)
        True
    """
    from ..derive.attributes import find_attribute

    return find_attribute(target, "bench") is not None


def ignore(reason: str = "no reason given") -> Callable[[F], F]:
    """Emulate Rust's ``#[ignore]``, skipping a test unless explicitly requested.

    Args:
        reason: Why the test is ignored, reported by :func:`run_tests`.

    Returns:
        Callable: A decorator returning the target unchanged.

    Example:
        >>> from oxide.core import ignore, ignored_reason, is_ignored
        >>> @ignore("needs a GPU")
        ... def test_heavy():
        ...     return None
        >>> ignored_reason(test_heavy)
        'needs a GPU'
        >>> is_ignored(test_heavy)
        True
    """

    def decorate(func: F) -> F:
        """Record the ignore request and return the target unchanged.

        Args:
            func: The test to mark.

        Returns:
            The target, unchanged.
        """
        _record(func, "ignore", {"reason": reason})
        return func

    return decorate


def ignored_reason(target: Any) -> str | None:
    """Return why a test is ignored, or None when it is not.

    Args:
        target: The test to inspect.

    Returns:
        str | None: The recorded reason.

    Example:
        >>> from oxide.core import ignore, ignored_reason
        >>> @ignore("flaky")
        ... def test_flaky():
        ...     return None
        >>> ignored_reason(test_flaky)
        'flaky'
        >>> ignored_reason(test_flaky.__class__) is None
        True
    """
    from ..derive.attributes import find_attribute

    payload = find_attribute(target, "ignore")
    if payload is None:
        return None
    return payload.get("reason")


def is_ignored(target: Any) -> bool:
    """Return whether a test is ignored.

    Args:
        target: The test to inspect.

    Returns:
        bool: True when the test carries ``#[ignore]``.

    Example:
        >>> from oxide.core import ignore, is_ignored
        >>> @ignore()
        ... def test_skipped():
        ...     return None
        >>> is_ignored(test_skipped)
        True
    """
    return ignored_reason(target) is not None


def should_panic(expected: type[BaseException] | str | None = None) -> Callable[[F], F]:
    """Emulate ``#[should_panic]``, requiring a test to raise.

    Args:
        expected: The exception type, or a substring the message must contain.
            ``None`` accepts any exception.

    Returns:
        Callable: A decorator returning the target unchanged.

    Example:
        >>> from oxide.core import should_panic, should_panic_of
        >>> @should_panic(ValueError)
        ... def test_raises():
        ...     raise ValueError("bad input")
        >>> should_panic_of(test_raises)
        <class 'ValueError'>
    """

    def decorate(func: F) -> F:
        """Record the panic expectation and return the target unchanged.

        Args:
            func: The test to mark.

        Returns:
            The target, unchanged.
        """
        _record(func, "should_panic", {"expected": expected})
        return func

    return decorate


def should_panic_of(target: Any) -> type[BaseException] | str | None:
    """Return what a test is expected to raise.

    Args:
        target: The test to inspect.

    Returns:
        The expected exception type, a message substring to look for, or None
        when the test is not marked ``#[should_panic]``.

    Example:
        >>> from oxide.core import should_panic, should_panic_of
        >>> @should_panic("overflow")
        ... def test_overflow():
        ...     raise RuntimeError("integer overflow")
        >>> should_panic_of(test_overflow)
        'overflow'
    """
    from ..derive.attributes import find_attribute

    payload = find_attribute(target, "should_panic")
    if payload is None:
        return None
    return payload.get("expected")


def serial(target: F) -> F:
    """Emulate ``#[serial]``, marking a test that needs exclusive access.

    The attribute is recorded, not enforced. :func:`run_tests` already executes
    every test one at a time in definition order, so a serial test never
    overlaps another; the marker only documents the requirement and survives for
    a future parallel runner to honour.

    Args:
        target: The test to mark.

    Returns:
        The target, unchanged.

    Example:
        >>> from oxide.core import serial, is_serial
        >>> @serial
        ... def test_exclusive():
        ...     return None
        >>> is_serial(test_exclusive)
        True
    """
    _record(target, "serial", {"exclusive": True})
    return target


def is_serial(target: Any) -> bool:
    """Return whether a test is marked ``#[serial]``.

    Args:
        target: The test to inspect.

    Returns:
        bool: True when the test carries ``#[serial]``.

    Example:
        >>> from oxide.core import serial, is_serial
        >>> @serial
        ... def test_one():
        ...     return None
        >>> is_serial(test_one)
        True
    """
    from ..derive.attributes import find_attribute

    return find_attribute(target, "serial") is not None


class TestResult(NamedTuple):
    """Outcome of a :func:`run_tests` sweep.

    Attributes:
        passed (tuple): Names of the tests that passed.
        failed (tuple): ``(name, message)`` pairs for the tests that failed.
        ignored (tuple): Names of the skipped tests.
        errors (tuple): ``(name, message)`` pairs for errors such as an
            unexpected ``#[should_panic]`` failure.
    """

    passed: tuple[str, ...]
    failed: tuple[tuple[str, str], ...]
    ignored: tuple[str, ...]
    errors: tuple[tuple[str, str], ...]


def run_tests(include_ignored: bool = False, module: Any = None) -> TestResult:
    """Run every test registered in a module and report the outcome.

    Honours ``#[ignore]``, ``#[should_panic]``, and ``#[serial]``.

    Args:
        include_ignored: Run ignored tests too, reporting them as ordinary.
        module: The module or namespace to run; the calling module when None.
            Pass it explicitly to run another module's tests.

    Returns:
        TestResult: The pass, failure, ignore, and error tallies.

    Example:
        >>> from oxide.core import ignore, run_tests, should_panic, test
        >>> @test
        ... def test_ok():
        ...     return 1
        >>> @test
        ... @should_panic(ValueError)
        ... def test_expected_failure():
        ...     raise ValueError("yes")
        >>> @test
        ... @ignore("later")
        ... def test_skipped():
        ...     return 2
        >>> result = run_tests()
        >>> "test_ok" in result.passed, "test_skipped" in result.ignored
        (True, True)
        >>> result.failed, result.errors
        ((), ())
        >>> run_tests(include_ignored=True).passed.count("test_skipped")
        1
    """
    passed: list[str] = []
    failed: list[tuple[str, str]] = []
    ignored: list[str] = []
    errors: list[tuple[str, str]] = []

    for func in tests(_resolve_namespace(module, skip=2)):
        name = getattr(func, "__name__", repr(func))
        if is_ignored(func) and not include_ignored:
            ignored.append(name)
            continue
        expected = should_panic_of(func)
        try:
            func()
        except BaseException as exc:  # noqa: BLE001 - a test may raise anything
            if expected is None:
                failed.append((name, f"{type(exc).__name__}: {exc}"))
            elif isinstance(expected, type) and isinstance(exc, expected):
                passed.append(name)
            elif isinstance(expected, str) and expected in str(exc):
                passed.append(name)
            else:
                errors.append((name, f"expected {expected!r}, got {exc!r}"))
            continue
        if expected is None:
            passed.append(name)
        else:
            errors.append((name, f"expected {expected!r}, but nothing was raised"))

    return TestResult(tuple(passed), tuple(failed), tuple(ignored), tuple(errors))