"""Java-inspired utilities."""
from __future__ import annotations

import queue
import threading
from typing import Any

class ThreadPool:
    def __init__(self, max_workers: int = 4):
        self._max_workers = max_workers
        self._executor = None
    def submit(self, fn, *a, **kw):
        res = fn(*a, **kw)
        return Future(res)

class Future:
    def __init__(self, result: Any = None):
        self._result = result
        self._done = True
    def get(self, timeout=None):
        return self._result
    def is_done(self):
        return self._done

class Promise(Future):
    pass

class ConcurrentMap(dict):
    pass

class BlockingQueue:
    def __init__(self, maxsize: int = 0):
        self._q = queue.Queue(maxsize)
    def put(self, item):
        self._q.put(item)
    def get(self):
        return self._q.get()
    def task_done(self):
        self._q.task_done()
    def join(self):
        self._q.join()

class RWLock:
    def __init__(self):
        self._lock = threading.RLock()
    def read_lock(self):
        return self._lock
    def write_lock(self):
        return self._lock

class Semaphore:
    def __init__(self, value: int = 1):
        self._sem = threading.Semaphore(value)
    def acquire(self):
        self._sem.acquire()
    def release(self):
        self._sem.release()

class Latch:
    def __init__(self, count: int = 1):
        self._count = count
    def count_down(self):
        if self._count > 0:
            self._count -= 1
    def await_(self):
        pass

Immutable = dict
Record = dict

def Annotation(*a, **kw):
    def deco(f):
        return f
    return deco

class reflection:
    @staticmethod
    def get_type(obj):
        return type(obj)

__all__ = ["ThreadPool", "Future", "Promise", "ConcurrentMap", "BlockingQueue", "RWLock", "Semaphore", "Latch", "Immutable", "Record", "Annotation", "reflection"]
