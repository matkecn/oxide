"""The ``classmethod`` + ``staticmethod`` combination, as one descriptor.

Python gives a method exactly two binding modes. ``classmethod`` always binds
the class and never the instance; ``staticmethod`` binds neither. Nothing binds
both, which forces the usual workaround: define the method twice, or branch on
``isinstance(self, type)``.

``masterclass`` fills that gap. It binds the class **always**, and the instance
**when one is reachable**. Reaching the method through the class passes ``None``
for the instance, so one definition serves both call styles::

    class Session:
        def __init__(self, name):
            self.name = name

        @masterclass
        def describe(cls, self):
            if self is None:
                return f"{cls.__name__} (no instance bound)"
            return f"{cls.__name__}(name={self.name!r})"

    Session.describe()
    # 'Session (no instance bound)'
    Session("db").describe()
    # "Session(name='db')"

Because the class is always passed, the body can reach ``cls`` for alternate
constructors and shared tables, and ``self`` for per-instance state, without
duplicating the signature. That is the same reach Rust gives an associated
function and a method separately, folded into one callable.

Example:
    >>> from oxide.decor import masterclass
    >>> class Counter:
    ...     total = 0
    ...     def __init__(self, step):
    ...         self.step = step
    ...         Counter.total += 1
    ...     @masterclass
    ...     def report(cls, self):
    ...         if self is None:
    ...             return f"{cls.__name__}: {cls.total} built"
    ...         return f"{cls.__name__}: {cls.total} built, step={self.step}"
    >>> Counter(5).report()
    'Counter: 1 built, step=5'
    >>> Counter.report()
    'Counter: 1 built'
"""

from __future__ import annotations

import functools
from typing import Any, Callable, Generic, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

__all__ = ["MasterMethod", "is_master", "masterclass"]


class MasterMethod(Generic[F]):
    """Descriptor binding a function to its class and, when present, its instance.

    The wrapped function receives ``(cls, self, *args, **kwargs)``. ``self`` is
    ``None`` when the method was reached through the class rather than an
    instance, so a single definition covers both call styles.

    Attributes:
        func (Callable): The undecorated function, kept for introspection.

    Example:
        >>> from oxide.decor.masterclass import MasterMethod
        >>> class Greeter:
        ...     def __init__(self, who):
        ...         self.who = who
        ...     @MasterMethod
        ...     def greet(cls, self, name):
        ...         return f"{cls.__name__} -> {name} (self={self is not None})"
        >>> Greeter("a").greet("world")
        'Greeter -> world (self=True)'
        >>> Greeter.greet("world")
        'Greeter -> world (self=False)'
    """

    __slots__ = ("func", "__wrapped__", "__dict__")

    def __init__(self, func: F, _kind: str = "masterclass") -> None:
        """Wrap a function as a combined class/instance method.

        Args:
            func: The function to wrap. Its first parameter receives the class
                and its second receives the instance, or ``None`` when reached
                through the class.

        Raises:
            TypeError: If ``func`` is not callable.
        """
        if not callable(func):
            raise TypeError(f"masterclass expects a callable, got {type(func).__name__}")
        self.func = func
        self._kind = _kind
        self.__wrapped__ = func
        self.__name__ = getattr(func, "__name__", _kind)
        self.__qualname__ = getattr(func, "__qualname__", self.__name__)
        self.__module__ = getattr(func, "__module__", None)
        self.__doc__ = getattr(func, "__doc__", None)

    def __set_name__(self, owner: type, name: str) -> None:
        """Record the attribute name the descriptor was assigned to.

        Args:
            owner: The class the descriptor was defined in.
            name: The attribute name it was assigned to.

        Returns:
            None.
        """
        if not self.__name__ or self.__name__ == "masterclass":
            self.__name__ = name

    def __get__(self, instance: Any, owner: type | None = None) -> Callable[..., Any]:
        """Bind the class and the instance, whichever is available.

        Args:
            instance: The instance the method was reached through, or ``None``
                when it was reached through the class.
            owner: The owning class, which becomes ``cls``.

        Returns:
            Callable: A partial that prepends ``cls``, then ``self``.
        """
        if owner is None:
            owner = type(instance)
        if instance is None:
            return functools.partial(self.func, owner, None)
        return functools.partial(self.func, owner, instance)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call the wrapped function without binding anything.

        This keeps the descriptor usable when it is not attached to a class.

        Args:
            *args: Positional arguments for the wrapped function.
            **kwargs: Keyword arguments for the wrapped function.

        Returns:
            Any: Whatever the wrapped function returns.
        """
        return self.func(*args, **kwargs)

    def __repr__(self) -> str:
        """Return a readable representation naming the wrapped function.

        Returns:
            str: For example ``<masterclass Counter.report>``.
        """
        try:
            name = self.__qualname__
        except Exception:
            name = getattr(self.func, "__name__", repr(self.func))
        kind = getattr(self, "_kind", "masterclass")
        return f"<{kind} {name}>"


def masterclass(target: F | None = None) -> Any:
    """Combine ``classmethod`` and ``staticmethod`` into one method.

    The wrapped function is called with the class first and the instance second.
    When the method is reached through the class rather than an instance, the
    instance argument is ``None``.

    Usable bare or called, so ``@masterclass`` and ``@masterclass()`` both work.

    Args:
        target: The function to decorate, or ``None`` when used as
            ``@masterclass()``.

    Returns:
        MasterMethod: The descriptor, or a decorator producing one.

    Raises:
        TypeError: If ``target`` is given and is not callable, or if it is
            already a ``staticmethod`` or ``classmethod``, whose binding would
            be silently discarded.

    Example:
        >>> from oxide.decor import masterclass
        >>> class Builder:
        ...     def __init__(self, parts):
        ...         self.parts = parts
        ...     @masterclass
        ...     def size(cls, self):
        ...         return 0 if self is None else len(self.parts)
        >>> Builder(["a", "b"]).size()
        2
        >>> Builder.size()
        0
        >>> Builder.__dict__["size"].__doc__ is None
        True
        >>> repr(Builder.__dict__["size"])
        '<masterclass Builder.size>'
    """

    def decorate(func: F) -> MasterMethod[F]:
        """Wrap one function in a MasterMethod.

        Args:
            func: The function to wrap.

        Returns:
            MasterMethod: The descriptor for it.
        """
        if isinstance(func, (staticmethod, classmethod)):
            raise TypeError(
                "masterclass cannot wrap a staticmethod or classmethod; "
                f"unwrap it first, got {type(func).__name__}"
            )
        return MasterMethod(func, _kind="masterclass")

    if target is None:
        return decorate
    return decorate(target)


def mastermethod(target: F | None = None) -> Any:
    """Combine ``classmethod`` and ``staticmethod`` into one method.

    The wrapped function is called with the class first and the instance second.
    When the method is reached through the class rather than an instance, the
    instance argument is ``None``.

    Usable bare or called, so ``@mastermethod`` and ``@mastermethod()`` both work.

    Args:
        target: The function to decorate, or ``None`` when used as
            ``@mastermethod()``.

    Returns:
        MasterMethod: The descriptor, or a decorator producing one.

    Raises:
        TypeError: If ``target`` is given and is not callable, or if it is
            already a ``staticmethod`` or ``classmethod``, whose binding would
            be silently discarded.

    Example:
        >>> from oxide.decor import mastermethod
        >>> class Builder:
        ...     def __init__(self, parts):
        ...         self.parts = parts
        ...     @mastermethod
        ...     def size(cls, self):
        ...         return 0 if self is None else len(self.parts)
        >>> Builder(["a", "b"]).size()
        2
        >>> Builder.size()
        0
        >>> Builder.__dict__["size"].__doc__ is None
        True
        >>> repr(Builder.__dict__["size"])
        '<mastermethod Builder.size>'
    """

    def decorate(func: F) -> MasterMethod[F]:
        """Wrap one function in a MasterMethod.

        Args:
            func: The function to wrap.

        Returns:
            MasterMethod: The descriptor for it.
        """
        if isinstance(func, (staticmethod, classmethod)):
            raise TypeError(
                "masterclass cannot wrap a staticmethod or classmethod; "
                f"unwrap it first, got {type(func).__name__}"
            )
        return MasterMethod(func, _kind="mastermethod")

    if target is None:
        return decorate
    return decorate(target)


def is_master(target: Any) -> bool:
    """Return whether a value is a combined class/instance method.

    Args:
        target: Any object, typically a class attribute.

    Returns:
        bool: True when ``target`` is a :class:`MasterMethod`.

    Example:
        >>> from oxide.decor import is_master
        >>> class Thing:
        ...     @masterclass()
        ...     def go(cls, self):
        ...         return None
        >>> is_master(Thing.__dict__["go"])
        True
        >>> is_master(Thing.__dict__.get("__init__"))
        False
    """
    return isinstance(target, MasterMethod)