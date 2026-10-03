"""The :class:`Help` class — self-documenting help for the whole library.

Instantiate it to get an answer:

    >>> from oxide.help import Help
    >>> help_all = Help()                      # everything, grouped by package
    >>> option = Help("Option")                # one symbol
    >>> ranges = Help.module("core.convert")   # one module
    >>> hits = Help.search("range")            # free-text search

Every instance answers the same questions — what is it, where does it live, what
can I do with it, and what else is nearby — and renders them either as text
(:meth:`Help.usage`) or as a dictionary (:meth:`Help.to_dict`).

Constructing a :class:`Help` is cheap. The underlying index is built once per
process and shared, so ``Help("Vec")`` in a loop costs a dictionary lookup after
the first call.
"""

from __future__ import annotations

from typing import Any, Iterator

from .catalog import Catalog, Entry, MethodEntry, catalog
from .render import render_entry, render_module, render_overview, render_search

#: Width of the label column in rendered output.
LABEL_WIDTH = 14

#: Maximum methods listed in rendered class output.
METHOD_LIMIT = 40


class Help:
    """Documentation for any part of the ``oxide`` library.

    The class is a view over a shared :class:`~oxide.help.catalog.Catalog`. The
    constructor accepts a symbol name, a module name, or a dotted path, and the
    instance reports which it resolved to through :attr:`kind`.

    Unlike the library's value types, this class does not declare ``__slots__``.
    It has both a ``module`` classmethod and a ``module`` attribute, and a
    documentation view is not on any hot path, so the flexibility is worth more
    than the few bytes.

    Attributes:
        query (str): The text originally passed in.
        kind (str): ``"symbol"``, ``"module"``, ``"search"``, or ``"unknown"``.
        entry (Entry | None): The resolved symbol entry, if any.
        module (str): The resolved module name, if any.
        matches (tuple): Search results, when constructed with :meth:`search`.

    Example:
        >>> entry = Help("Option")
        >>> entry.kind
        'symbol'
        >>> entry.name
        'Option'
        >>> entry.module
        'core.option'
        >>> entry.summary[:7]
        'A conta'
        >>> "and_then" in [m.name for m in entry.methods]
        True
        >>> entry.methods[0].name
        'and_'
    """

    def __init__(
        self,
        topic: Any = None,
        *,
        catalog_: Catalog | None = None,
    ) -> None:
        """Resolve a topic to a symbol, a module, or nothing.

        Args:
            topic: A symbol name (``"Option"``), a module name
                (``"core.convert"`` or ``"oxide.core.convert"``), a live class
                or function, or None for an overview of the whole library.
            catalog_: An explicit catalog to query. Defaults to the shared one.
        """
        self._catalog = catalog_ if catalog_ is not None else catalog()
        self.query = "" if topic is None else str(topic)
        self.entry: Entry | None = None
        self.module: str = ""
        self.matches: tuple[Entry, ...] = ()
        self.kind = "unknown"

        if topic is None:
            self.kind = "overview"
            return

        if not isinstance(topic, str) and not callable(topic):
            topic = type(topic).__name__

        name = getattr(topic, "__name__", topic)
        if not isinstance(name, str):
            self.kind = "unknown"
            return

        resolved = self._catalog.lookup(name)
        if resolved is not None:
            self.entry = resolved
            self.module = resolved.module
            self.kind = "symbol"
            return

        stripped = name[len("oxide."):] if name.startswith("oxide.") else name
        if stripped in self._catalog.module_names() or stripped == "oxide":
            self.module = stripped
            self.kind = "module"
            return

        self.matches = self._catalog.search(name, limit=10)
        self.kind = "search" if self.matches else "unknown"

    # -- construction variants -------------------------------------------------

    @classmethod
    def module(cls, module: str, *, catalog_: Catalog | None = None) -> "Help":
        """Return help for one module.

        Skips symbol lookup entirely, so :meth:`module` resolves the name as a
        module even when a symbol of the same name exists — ``Help.module("filter")``
        documents the ``filter`` package, while ``Help("filter")`` documents the
        iterator adapter function.

        Args:
            module: The module name, with or without the ``oxide.`` prefix.
            catalog_: An explicit catalog to query.

        Returns:
            Help: A help instance of kind ``"module"``.

        Example:
            >>> Help.module("oxide.filter").name
            'filter'
        """
        source = catalog_ if catalog_ is not None else catalog()
        name = str(module)
        stripped = name[len("oxide."):] if name.startswith("oxide.") else name
        instance = cls.__new__(cls)
        instance._catalog = source
        instance.query = name
        instance.entry = None
        instance.module = stripped if stripped in source.module_names() else ""
        instance.matches = ()
        instance.kind = "module" if instance.module else "unknown"
        if not instance.module:
            instance.matches = source.search(stripped, limit=10)
            instance.kind = "search" if instance.matches else "unknown"
        return instance

    @classmethod
    def search(
        cls,
        query: str,
        *,
        limit: int = 25,
        in_methods: bool = False,
        catalog_: Catalog | None = None,
    ) -> "Help":
        """Return help for a free-text query.

        Args:
            query: The search term.
            limit: Maximum number of results.
            in_methods: Also match against method names and summaries.
            catalog_: An explicit catalog to query.

        Returns:
            Help: A help instance of kind ``"search"`` carrying the matches.

        Example:
            >>> [entry.name for entry in Help.search("range", limit=2).matches]
            ['Range', 'RangeFrom']
        """
        instance = cls.__new__(cls)
        instance._catalog = catalog_ if catalog_ is not None else catalog()
        instance.query = str(query)
        instance.entry = None
        instance.module = ""
        instance.matches = instance._catalog.search(query, limit=limit, in_methods=in_methods)
        instance.kind = "search" if instance.matches else "unknown"
        return instance

    # -- identity --------------------------------------------------------------

    @property
    def name(self) -> str:
        """Return the primary name this help entry describes.

        Returns:
            str: The symbol name, the module name, or the search query.

        Example:
            >>> Help("Vec").name
            'Vec'
            >>> Help.module("core").name
            'core'
        """
        if self.entry is not None:
            return self.entry.name
        if self.module:
            return self.module
        return self.query

    @property
    def reference(self) -> str:
        """Return the fully-qualified dotted path.

        Returns:
            str: A path such as ``"oxide.core.option.Option"``, or the module
            name when this entry describes a module.
        """
        if self.entry is not None:
            return f"oxide.{self.entry.reference}"
        return f"oxide.{self.module}" if self.module else ""

    @property
    def exists(self) -> bool:
        """Return whether the topic resolved to anything.

        Returns:
            bool: True for a symbol, module, overview, or non-empty search.

        Example:
            >>> Help("Vec").exists, Help("nope_not_here").exists
            (True, False)
        """
        return self.kind != "unknown"

    # -- symbol properties -----------------------------------------------------

    @property
    def summary(self) -> str:
        """Return the one-line summary of the topic.

        Returns:
            str: The first paragraph of the docstring, or the module summary.

        Example:
            >>> Help("Result").summary
            'A container for either a success value or a failure error.'
        """
        if self.entry is not None:
            return self.entry.summary
        if self.module:
            return self._catalog.module_summary(self.module)
        return ""

    @property
    def description(self) -> str:
        """Return the full documentation text of the topic.

        Returns:
            str: The complete docstring, or the module docstring.

        Example:
            >>> "unwrap" in Help("Option").description
            True
        """
        if self.entry is not None:
            return self.entry.description
        if self.module:
            return self._catalog.module_doc(self.module)
        return ""

    @property
    def signature(self) -> str:
        """Return the rendered signature of the topic.

        Returns:
            str: The signature, or an empty string when the topic is a module.

        Example:
            >>> Help("Some").signature.startswith("(value")
            True
        """
        return self.entry.signature if self.entry is not None else ""

    @property
    def methods(self) -> tuple[MethodEntry, ...]:
        """Return the documented methods of the topic.

        Returns:
            tuple: One :class:`~oxide.help.catalog.MethodEntry` per method,
            sorted by name. Empty for functions, constants, and modules.

        Example:
            >>> "and_then" in [method.name for method in Help("Result").methods]
            True
        """
        return self.entry.methods if self.entry is not None else ()

    @property
    def fields(self) -> tuple[str, ...]:
        """Return the topic's field names.

        Returns:
            tuple: ``__slots__`` or annotated field names. Empty when the topic
            has no declared fields.

        Example:
            >>> Help("Vec").fields
            ('_data', '_capacity')
        """
        return self.entry.fields if self.entry is not None else ()

    @property
    def bases(self) -> tuple[str, ...]:
        """Return the topic's base classes.

        Returns:
            tuple: Dotted base class names. Empty for functions and modules.

        Example:
            >>> Help("MemorySink").bases
            ()
        """
        return self.entry.bases if self.entry is not None else ()

    @property
    def examples(self) -> tuple[str, ...]:
        """Return the doctest lines found in the topic's docstring.

        Returns:
            tuple: The example lines, with prompts included.

        Example:
            >>> Help("Option").examples[0]
            '>>> x: Option[int] = Some(5)'
        """
        return self.entry.examples if self.entry is not None else ()

    @property
    def related(self) -> tuple[Entry, ...]:
        """Return symbols in the same module or that reference this one.

        Returns:
            tuple: Neighbour entries, sorted by name.

        Example:
            >>> "Some" in [item.name for item in Help("Option").related]
            True
        """
        if self.entry is None:
            return ()
        return self._catalog.related(self.entry)

    # -- catalog-wide queries --------------------------------------------------

    def siblings(self) -> tuple[Entry, ...]:
        """Return the other symbols defined in the same module.

        Returns:
            tuple: Entries from the same module, excluding the topic itself.

        Example:
            >>> "None_" in [item.name for item in Help("Some").siblings()]
            True
        """
        if self.entry is None:
            return ()
        return tuple(
            item for item in self._catalog.in_module(self.entry.module)
            if item.name != self.entry.name
        )

    def exports(self) -> tuple[Entry, ...]:
        """Return the symbols of a module.

        Returns:
            tuple: Entries for a module topic. Empty for a symbol topic.

        Example:
            >>> "Filter" in [item.name for item in Help.module("filter").exports()]
            True
        """
        if self.module and not (self.entry is not None):
            return self._catalog.in_module(self.module)
        return ()

    def in_module(self, module: str) -> tuple[Entry, ...]:
        """Return the symbols of any module, whatever this instance describes.

        Args:
            module: The module name, with or without the ``oxide.`` prefix.

        Returns:
            tuple: Entries defined by that module.

        Example:
            >>> "Range" in [item.name for item in Help().in_module("iter")]
            True
        """
        return self._catalog.in_module(module)

    def find(self, query: str, *, limit: int = 25, in_methods: bool = False) -> tuple[Entry, ...]:
        """Search the library from any instance.

        Named ``find`` rather than ``search`` so it does not shadow the
        :meth:`search` classmethod, which is the documented entry point for
        running a query.

        Args:
            query: The search term.
            limit: Maximum number of results.
            in_methods: Also match against method names and summaries.

        Returns:
            tuple: Scored entries, best first.

        Example:
            >>> [item.name for item in Help().find("mutex", limit=1)]
            ['Mutex']
        """
        return self._catalog.search(query, limit=limit, in_methods=in_methods)

    @staticmethod
    def modules() -> tuple[str, ...]:
        """Return every module in the library.

        Returns:
            tuple: Subpackage names, sorted, without the ``oxide.`` prefix.

        Example:
            >>> "core" in Help.modules()
            True
        """
        return catalog().module_names()

    @staticmethod
    def names() -> tuple[str, ...]:
        """Return every public symbol in the library.

        Returns:
            tuple: Symbol names, sorted.

        Example:
            >>> "Filter" in Help.names()
            True
        """
        return catalog().names()

    @classmethod
    def overview(cls) -> "Help":
        """Return help describing the library as a whole.

        Returns:
            Help: An instance of kind ``"overview"``.

        Example:
            >>> Help.overview().kind
            'overview'
        """
        return cls()

    # -- rendering -------------------------------------------------------------

    def usage(self) -> str:
        """Return rendered help text for this topic.

        Returns:
            str: Plain text. A symbol gets a header, summary, signature, fields,
            methods, and examples; a module gets its docstring and export list;
            a search gets a ranked result list; an overview lists every package.

        Example:
            >>> text = Help("Vec").usage()
            >>> text.splitlines()[0]
            'Vec'
        """
        if self.kind == "overview":
            return render_overview(self._catalog)
        if self.kind == "symbol" and self.entry is not None:
            return render_entry(self.entry, self._catalog)
        if self.kind == "module":
            return render_module(self.module, self._catalog)
        if self.kind == "search":
            return render_search(self.query, self.matches)
        return (
            f"No documentation found for {self.query!r}.\n\n"
            f"Try {self.__class__.__name__}.search(...) or "
            f"{self.__class__.__name__}.modules()."
        )

    def print(self, stream: Any = None) -> None:
        """Print the rendered help text.

        Args:
            stream: Where to write. Defaults to :func:`oxide.logging.println`'s
                stream, standard output.

        Example:
            >>> import io
            >>> buffer = io.StringIO()
            >>> Help("Vec").print(buffer)
            >>> buffer.getvalue().splitlines()[0]
            'Vec'
        """
        text = self.usage()
        if stream is None:
            from ..logging import println

            println(text)
            return
        if hasattr(stream, "write"):
            stream.write(text + "\n")
            return
        stream(text)

    def to_dict(self) -> dict[str, Any]:
        """Return this help entry as plain data.

        Returns:
            dict: A JSON-serialisable dictionary with the topic's identity,
            documentation, signature, fields, methods, and related symbols.

        Example:
            >>> data = Help("Vec").to_dict()
            >>> data["name"], data["kind"]
            ('Vec', 'symbol')
        """
        if self.kind == "symbol" and self.entry is not None:
            entry = self.entry
            return {
                "kind": self.kind,
                "name": entry.name,
                "module": entry.module,
                "reference": f"oxide.{entry.reference}",
                "entry_kind": entry.kind,
                "signature": entry.signature,
                "summary": entry.summary,
                "description": entry.description,
                "bases": list(entry.bases),
                "fields": list(entry.fields),
                "methods": [
                    {"name": method.name, "signature": method.signature,
                     "kind": method.kind, "summary": method.summary}
                    for method in entry.methods
                ],
                "examples": list(entry.examples),
                "related": [item.name for item in self._catalog.related(entry)],
            }
        if self.kind == "module":
            return {
                "kind": self.kind,
                "name": self.module,
                "module": self.module,
                "reference": f"oxide.{self.module}",
                "summary": self.summary,
                "description": self.description,
                "exports": [item.name for item in self._catalog.in_module(self.module)],
            }
        if self.kind == "search":
            return {
                "kind": self.kind,
                "query": self.query,
                "matches": [
                    {"name": entry.name, "module": entry.module, "summary": entry.summary}
                    for entry in self.matches
                ],
            }
        return {"kind": self.kind, "query": self.query}

    # -- dunders ---------------------------------------------------------------

    def __str__(self) -> str:
        return self.usage()

    def __repr__(self) -> str:
        return f"Help({self.name!r}, kind={self.kind!r})"

    def __contains__(self, item: object) -> bool:
        return isinstance(item, str) and item in self.description

    def __iter__(self) -> Iterator[str]:
        return iter(self.description.split())

    def __len__(self) -> int:
        return len(self.description)

    def __bool__(self) -> bool:
        return self.exists


__all__ = [
    "LABEL_WIDTH",
    "METHOD_LIMIT",
    "Help",
]
