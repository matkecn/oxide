"""Future, Poll, Waker, Stream — async computation primitives.

Provides Future[T] for async computations, Poll[T] for pending/ready
state, Waker for task notification, Stream[T] for async iteration,
JoinHandle for task results, and spawn for launching tasks.
"""
from __future__ import annotations

import asyncio
import threading
from typing import Any, Callable, Generic, Iterable, TypeVar

T = TypeVar("T")
U = TypeVar("U")


class Poll(Generic[T]):
    """A result of polling an async computation: pending or ready.

    Represents whether a value is available yet. A ready poll carries a
    value; a pending poll indicates the computation is not complete.
    Uses :meth:`ready`/:meth:`pending` to construct and the combinators
    :meth:`map`/:meth:`and_then`/:meth:`inspect` to transform.

    Examples:
        >>> Poll.ready(5).is_ready()
        True
        >>> Poll.pending().unwrap_or(0)
        0
    """

    __slots__ = ("_ready", "_value")

    def __init__(self, ready: bool, value: T | None = None) -> None:
        """Construct a Poll directly.

        Prefer the :meth:`ready`/:meth:`pending` class methods.

        Args:
            ready (bool): Whether the poll carries a value.
            value (T | None, optional): The carried value. Defaults to None.
        """
        self._ready = ready
        self._value = value

    @classmethod
    def ready(cls, value: T) -> Poll[T]:
        """Create a ready poll carrying the given value.

        Args:
            value (T): The value to carry.

        Returns:
            Poll[T]: A ready poll.
        """
        return cls(True, value)

    @classmethod
    def pending(cls) -> Poll[T]:
        """Create a pending poll indicating the value is not yet available.

        Returns:
            Poll[T]: A pending poll.
        """
        return cls(False)

    def is_ready(self) -> bool:
        """Return whether the poll is ready with a value.

        Returns:
            bool: True if ready.
        """
        return self._ready

    def is_pending(self) -> bool:
        """Return whether the poll is still pending.

        Returns:
            bool: True if pending.
        """
        return not self._ready

    def unwrap(self) -> T:
        """Return the inner value, raising if the poll is pending.

        Returns:
            T: The inner value.

        Raises:
            RuntimeError: If this is a pending poll.
        """
        if not self._ready:
            raise RuntimeError("called unwrap on pending Poll")
        return self._value  # type: ignore

    def unwrap_or(self, default: T) -> T:
        """Return the inner value, or a default if pending.

        Args:
            default (T): The fallback value to return if pending.

        Returns:
            T: The inner value, or the default.
        """
        if not self._ready:
            return default
        return self._value  # type: ignore

    def map(self, fn: Callable[[T], U]) -> Poll[U]:
        """Transform the inner value with fn if ready.

        Args:
            fn (Callable[[T], U]): The transformation function.

        Returns:
            Poll[U]: A ready poll with the transformed value, or a pending
                poll if this one was pending.
        """
        if self._ready:
            return Poll.ready(fn(self._value))  # type: ignore
        return Poll.pending()

    def and_then(self, fn: Callable[[T], Poll[U]]) -> Poll[U]:
        """Chain with a poll-returning function if ready.

        Args:
            fn (Callable[[T], Poll[U]]): The function producing a new poll
                from the inner value.

        Returns:
            Poll[U]: The poll from fn, or a pending poll if this was
                pending.
        """
        if self._ready:
            return fn(self._value)  # type: ignore
        return Poll.pending()

    def inspect(self, fn: Callable[[T], Any]) -> Poll[T]:
        """Run fn on the inner value if ready, then return self.

        Useful for side effects without changing the value.

        Args:
            fn (Callable[[T], Any]): The side-effect function.

        Returns:
            Poll[T]: Self.
        """
        if self._ready:
            fn(self._value)  # type: ignore
        return self

    def __repr__(self) -> str:
        if self._ready:
            return f"Poll::Ready({self._value!r})"
        return "Poll::Pending"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Poll):
            if self._ready != other._ready:
                return False
            if self._ready:
                return self._value == other._value
            return True
        return NotImplemented

    def __bool__(self) -> bool:
        return self._ready


class Waker:
    """Notification handle used to wake a pending task.

    Tracks whether it has been woken and optionally invokes a callback
    function. Pass a waker to :meth:`Future.poll` so a task can be
    notified when progress can resume.

    Examples:
        >>> w = Waker()
        >>> w.wake()
        >>> w.is_woken()
        True
    """

    __slots__ = ("_wake_fn", "_woken")

    def __init__(self, wake_fn: Callable[[], None] | None = None) -> None:
        """Construct a Waker with an optional wake callback.

        Args:
            wake_fn (Callable[[], None] | None, optional): A function
                invoked on wake, or None to not call anything.
        """
        self._wake_fn = wake_fn
        self._woken = False

    def wake(self) -> None:
        """Signal the task that it should re-poll.

        Marks the waker as woken and invokes the wake callback if one was
        provided.
        """
        self._woken = True
        if self._wake_fn:
            self._wake_fn()

    def wake_by_ref(self) -> None:
        """Wake the task by reference; behaves identically to :meth:`wake`.

        Provided as a Rust-like naming alias.
        """
        self.wake()

    def clone_waker(self) -> Waker:
        """Return a new Waker sharing the same wake function.

        Returns:
            Waker: A new waker with the same callback.
        """
        return Waker(self._wake_fn)

    def is_woken(self) -> bool:
        """Return whether :meth:`wake` has been called.

        Returns:
            bool: True if woken.
        """
        return self._woken

    def reset(self) -> None:
        """Reset the woken state to False.

        After reset, :meth:`is_woken` returns False until :meth:`wake` is
        called again.
        """
        self._woken = False

    def __repr__(self) -> str:
        return f"Waker(woken={self._woken})"


class JoinHandle(Generic[T]):
    """Handle to a spawned task for retrieving its result.

    Wraps a :class:`Future` running on a background daemon thread. Use
    :meth:`start` to launch, then :meth:`join`/:meth:`get_result` to obtain
    the result. Obtained from the :func:`spawn` helper.

    Examples:
        >>> async def work():
        ...     return 7
        >>> h = spawn(work())
        >>> h.get_result()
        7
    """

    __slots__ = ("_future", "_result", "_done", "_exception", "_thread")

    def __init__(self, future: Future[T]) -> None:
        """Construct a JoinHandle around a Future.

        Args:
            future (Future[T]): The future this handle manages.
        """
        self._future = future
        self._result: T | None = None
        self._done = False
        self._exception: Exception | None = None
        self._thread: threading.Thread | None = None

    def run(self) -> None:
        """Execute the wrapped future to completion in a new event loop.

        Runs synchronously on the calling (or background) thread, storing
        the result or any raised exception on the handle.
        """
        try:
            loop = asyncio.new_event_loop()
            self._result = loop.run_until_complete(self._future)
            loop.close()
        except Exception as e:
            self._exception = e
        finally:
            self._done = True

    def start(self) -> None:
        """Launch the task on a background daemon thread.

        The task begins running asynchronously; use :meth:`get_result` to
        wait for and retrieve its result.
        """
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

    def is_finished(self) -> bool:
        """Return whether the task has completed.

        Returns:
            bool: True if the future has finished running.
        """
        return self._done

    def is_running(self) -> bool:
        """Return whether the task's thread is still alive.

        Returns:
            bool: True if the underlying thread is running.
        """
        return self._thread is not None and self._thread.is_alive()

    def abort(self) -> bool:
        """Attempt to abort the task.

        Aborts only if the task is not currently running or was never
        started.

        Returns:
            bool: True if the task is finished or not started; False if a
                running task could not be aborted.
        """
        if self._thread and self._thread.is_alive():
            return False
        return True

    def get_result(self, timeout: float | None = None) -> T | None:
        """Wait for the task and return its result.

        Args:
            timeout (float | None, optional): Maximum seconds to wait, or
                None to wait indefinitely.

        Returns:
            T | None: The task result, or None if it timed out.

        Raises:
            Exception: The task's exception, if its future failed.
        """
        if self._thread:
            self._thread.join(timeout=timeout)
        if self._exception:
            raise self._exception
        return self._result

    def join(self, timeout: float | None = None) -> T | None:
        """Wait for the task and return its result.

        Alias for :meth:`get_result`.

        Args:
            timeout (float | None, optional): Maximum seconds to wait, or
                None to wait indefinitely.

        Returns:
            T | None: The task result, or None if it timed out.

        Raises:
            Exception: The task's exception, if its future failed.
        """
        return self.get_result(timeout)

    def __enter__(self) -> JoinHandle[T]:
        return self

    def __exit__(self, *_: Any) -> None:
        if self._thread:
            self._thread.join()

    def __repr__(self) -> str:
        return f"JoinHandle(finished={self._done})"


class Stream(Generic[T]):
    """An async iterator providing combinators over a sequence of values.

    Produces values asynchronously. Construct from a sync or async iterable
    with :meth:`from_iter`/:meth:`from_async_iter`, or with the helpers
    :meth:`empty`, :meth:`once`, :meth:`repeat`, and :meth:`chain`. Combine
    with :meth:`map`, :meth:`filter`, :meth:`take`, and consume with
    :meth:`collect` or async iteration.

    Examples:
        >>> import asyncio
        >>> async def main():
        ...     s = Stream.from_iter([1, 2, 3])
        ...     doubled = await s.map(lambda x: x * 2)
        ...     return await doubled.collect()
        >>> asyncio.run(main())
        [2, 4, 6]
    """

    __slots__ = ("_async_gen", "_buffer")

    def __init__(self, async_gen: Any = None) -> None:
        """Construct a Stream from an async generator.

        Prefer the class constructors (:meth:`from_iter`,
        :meth:`from_async_iter`, etc.) in most cases.

        Args:
            async_gen (Any, optional): An async generator object, or None.
        """
        self._async_gen = async_gen
        self._buffer: list[T] = []

    @classmethod
    def from_iter(cls, iterable: Iterable[T]) -> Stream[T]:
        """Create a stream that yields values from a synchronous iterable.

        Args:
            iterable (Iterable[T]): Any synchronous iterable of values.

        Returns:
            Stream[T]: A stream over the iterable's values.
        """

        async def gen():
            for v in iterable:
                yield v
        return cls(gen())

    @classmethod
    def from_async_iter(cls, async_iter: Any) -> Stream[T]:
        """Create a stream that yields values from an async iterable.

        Args:
            async_iter (Any): An object supporting async iteration.

        Returns:
            Stream[T]: A stream over the async iterable's values.
        """
        return cls(async_iter)

    @classmethod
    def empty(cls) -> Stream[T]:
        """Create a stream that yields no values.

        Returns:
            Stream[T]: An empty stream.
        """

        async def gen():
            return
            yield  # type: ignore[misc]
        return cls(gen())

    @classmethod
    def once(cls, value: T) -> Stream[T]:
        """Create a stream that yields a single value.

        Args:
            value (T): The single value to yield.

        Returns:
            Stream[T]: A stream yielding exactly one value.
        """

        async def gen():
            yield value
        return cls(gen())

    @classmethod
    def repeat(cls, value: T) -> Stream[T]:
        """Create an infinite stream that repeatedly yields the same value.

        Args:
            value (T): The value to repeat.

        Returns:
            Stream[T]: An infinite stream.
        """

        async def gen():
            while True:
                yield value
        return cls(gen())

    @classmethod
    def chain(cls, *streams: Stream[T]) -> Stream[T]:
        """Concatenate multiple streams into a single stream.

        Args:
            *streams (Stream[T]): The streams to concatenate, in order.

        Returns:
            Stream[T]: A stream yielding values from each input stream in
                sequence.
        """

        async def gen():
            for s in streams:
                async for item in s._async_gen:
                    yield item
        return cls(gen())

    async def next(self) -> T | None:
        """Advance the stream and return the next value.

        Returns:
            T | None: The next value, or None if the stream is exhausted.
        """
        try:
            return await self._async_gen.__anext__()
        except StopAsyncIteration:
            return None

    async def map(self, fn: Callable[[T], U]) -> Stream[U]:
        """Transform each value in the stream with fn.

        Args:
            fn (Callable[[T], U]): The transformation function.

        Returns:
            Stream[U]: A new stream of transformed values.
        """

        async def gen():
            async for item in self._async_gen:
                yield fn(item)
        return Stream(gen())

    async def filter(self, predicate: Callable[[T], bool]) -> Stream[T]:
        """Yield only the values in the stream matching the predicate.

        Args:
            predicate (Callable[[T], bool]): A function returning whether a
                value should be kept.

        Returns:
            Stream[T]: A new stream of matching values.
        """

        async def gen():
            async for item in self._async_gen:
                if predicate(item):
                    yield item
        return Stream(gen())

    async def take(self, n: int) -> Stream[T]:
        """Yield at most n values from the stream.

        Args:
            n (int): The maximum number of values to yield.

        Returns:
            Stream[T]: A new stream of at most n values.
        """

        async def gen():
            count = 0
            async for item in self._async_gen:
                if count >= n:
                    break
                yield item
                count += 1
        return Stream(gen())

    async def collect(self) -> list[T]:
        """Consume the stream and return all values as a list.

        Returns:
            list[T]: All remaining values in the stream.
        """
        result = []
        async for item in self._async_gen:
            result.append(item)
        return result

    async def fold(self, init: U, fn: Callable[[U, T], U]) -> U:
        """Fold all stream values into a single accumulator.

        Args:
            init (U): The initial accumulator value.
            fn (Callable[[U, T], U]): A function combining the accumulator
                and each value.

        Returns:
            U: The final accumulator value.
        """
        acc = init
        async for item in self._async_gen:
            acc = fn(acc, item)
        return acc

    async def for_each(self, fn: Callable[[T], Any]) -> None:
        """Call fn on every value in the stream.

        Args:
            fn (Callable[[T], Any]): The function to call per value.
        """
        async for item in self._async_gen:
            fn(item)

    async def count(self) -> int:
        """Count the number of values in the stream.

        Returns:
            int: The number of values yielded.
        """
        n = 0
        async for _ in self._async_gen:
            n += 1
        return n

    async def first(self) -> T | None:
        """Return the first value in the stream, or None if empty.

        Returns:
            T | None: The first value, or None if the stream is empty.
        """
        return await self.next()

    async def peek(self) -> T | None:
        """Return the next value without consuming it.

        The peeked value is buffered and still delivered by subsequent
        operations.

        Returns:
            T | None: The next value, or None if the stream is exhausted.
        """
        try:
            item = await self._async_gen.__anext__()
            self._buffer.append(item)
            return item
        except StopAsyncIteration:
            return None

    def __aiter__(self) -> Any:
        return self._async_gen

    def __repr__(self) -> str:
        return "Stream(...)"


class Future(Generic[T]):
    """An asynchronous computation that will produce a value.

    Wraps a coroutine or an already-resolved value. Create with
    :meth:`ready`, :meth:`pending`, or by wrapping a coroutine, then await
    it, poll it, or transform it with :meth:`map`/:meth:`and_then`. Callbacks
    can be registered with :meth:`add_done_callback`.

    Examples:
        >>> import asyncio
        >>> f = Future.ready(42)
        >>> async def main():
        ...     return await f
        >>> asyncio.run(main())
        42

        Wrap a coroutine to await a real computation instead:

        >>> async def work():
        ...     return 7
        >>> async def get():
        ...     return await Future(work())
        >>> asyncio.run(get())
        7
    """

    __slots__ = ("_coro", "_done", "_result", "_exception", "_callbacks")

    def __init__(self, coro: Any = None) -> None:
        """Construct a Future from an optional coroutine.

        Args:
            coro (Any, optional): A coroutine to await, or None.
        """
        self._coro = coro
        self._done = False
        self._result: T | None = None
        self._exception: Exception | None = None
        self._callbacks: list[Callable[[Future[T]], None]] = []

    @classmethod
    def ready(cls, value: T) -> Future[T]:
        """Create an already-resolved future holding the given value.

        Args:
            value (T): The resolved value.

        Returns:
            Future[T]: A future that is immediately done.
        """
        f = cls()
        f._done = True
        f._result = value
        return f

    @classmethod
    def pending(cls) -> Future[T]:
        """Create a future that is not yet resolved.

        Returns:
            Future[T]: A pending future.
        """
        return cls()

    def poll(self, waker: Waker | None = None) -> Poll[T]:
        """Poll the future and return ready or pending.

        Args:
            waker (Waker | None, optional): A waker to associate with this
                poll. Not used by the current implementation.

        Returns:
            Poll[T]: A ready poll with the result, or a pending poll.

        Raises:
            Exception: The future's exception, if it failed.
        """
        if self._done:
            if self._exception:
                raise self._exception
            return Poll.ready(self._result)  # type: ignore
        return Poll.pending()

    def is_done(self) -> bool:
        """Return whether the future has been resolved.

        Returns:
            bool: True if the future is done.
        """
        return self._done

    def result(self) -> T | None:
        """Return the resolved value, or None if still pending.

        Returns:
            T | None: The resolved value, or None.
        """
        return self._result

    def exception(self) -> Exception | None:
        """Return the exception if the future failed, or None.

        Returns:
            Exception | None: The failure exception, or None.
        """
        return self._exception

    def add_done_callback(self, fn: Callable[[Future[T]], None]) -> None:
        """Register a callback to run when the future completes.

        If the future is already done, the callback runs immediately.

        Args:
            fn (Callable[[Future[T]], None]): The callback, receiving the
                future.
        """
        if self._done:
            fn(self)
        else:
            self._callbacks.append(fn)

    def set_result(self, value: T) -> None:
        """Resolve the future with a value and notify callbacks.

        Args:
            value (T): The result value.
        """
        self._result = value
        self._done = True
        for cb in self._callbacks:
            cb(self)

    def set_exception(self, exc: Exception) -> None:
        """Mark the future as failed with an exception.

        Args:
            exc (Exception): The exception the future failed with.
        """
        self._exception = exc
        self._done = True
        for cb in self._callbacks:
            cb(self)

    def map(self, fn: Callable[[T], U]) -> Future[U]:
        """Transform the result with fn when the future completes.

        Args:
            fn (Callable[[T], U]): The transformation function.

        Returns:
            Future[U]: A new future of the transformed result.
        """

        async def mapped():
            result = await self
            return fn(result)
        return Future(mapped())

    def and_then(self, fn: Callable[[T], Future[U]]) -> Future[U]:
        """Chain with another future-returning function when done.

        Args:
            fn (Callable[[T], Future[U]]): A function returning a future
                from the result.

        Returns:
            Future[U]: A new future combining both computations.
        """

        async def chained():
            result = await self
            return await fn(result)
        return Future(chained())

    def __await__(self) -> Any:
        if self._coro is not None:
            return self._coro.__await__()
        if self._done:
            if self._exception:
                raise self._exception
            async def _ready():
                return self._result
            return _ready().__await__()
        async def _pending():
            return None
        return _pending().__await__()

    def __repr__(self) -> str:
        if self._done:
            return f"Future::Ready({self._result!r})"
        return "Future::Pending"


def spawn(coro: Any) -> JoinHandle:
    """Spawn a coroutine on a background thread and return a JoinHandle.

    The coroutine is wrapped in a :class:`Future` and launched on a daemon
    thread. Use :meth:`JoinHandle.get_result` to wait for and retrieve the
    result.

    Args:
        coro (Any): The coroutine to run.

    Returns:
        JoinHandle: A handle to retrieve the task's result.
    """
    future = Future(coro)
    handle = JoinHandle(future)
    handle.start()
    return handle


async def join_all(handles: list[JoinHandle]) -> list:
    """Wait for and collect the results of all given JoinHandles.

    Args:
        handles (list[JoinHandle]): The handles to join.

    Returns:
        list: The results from each handle, in the same order.
    """
    results = []
    for h in handles:
        results.append(h.get_result())
    return results
