"""The catalog: a lazily-built index of everything the library exports.

:mod:`oxide.help` answers questions about the whole library, which means it has
to know what the whole library contains. That index lives here.

Scanning is **lazy and cached**. Building it walks the ``oxide`` package with
:mod:`pkgutil`, imports each subpackage, and reads ``__all__``, the docstrings,
and the signatures. That costs real work, so it happens once, on first use, and
only for subpackages that have not been imported yet.

Example:
    >>> from oxide.help.catalog import Catalog
    >>> catalog = Catalog.build()
    >>> names = catalog.module_names()
    >>> "filter" in names and "logging" in names
    True
    >>> entry = catalog.lookup("Option")
    >>> entry is not None
    True
    >>> entry.module
    'core.option'
"""

from __future__ import annotations

import enum
import importlib
import inspect
import pkgutil
import textwrap
from typing import Any, Iterator, NamedTuple

#: Top-level subpackages to index. Every one of these is scanned, including the
#: ``_``-prefixed ones: ``_collections``, ``_io``, and ``_time`` are named after
#: their Rust modules but hold public types such as ``Vec`` and ``Duration``.
PUBLIC_PACKAGES: tuple[str, ...] = (
    "core",
    "_collections",
    "iter",
    "memory",
    "sync",
    "_time",
    "_io",
    "fs",
    "net",
    "process",
    "async_",
    "macros",
    "regex",
    "filter",
    "derive",
    "decor",
    "logging",
    "help",
)


class MethodEntry(NamedTuple):
    """One method or function belonging to a catalog entry.

    Attributes:
        name (str): The method name, such as ``"unwrap"``.
        signature (str): Rendered signature, or an empty string.
        summary (str): The first line of the docstring.
        kind (str): ``"method"``, ``"classmethod"``, ``"staticmethod"``,
            ``"property"``, ``"function"``, or ``"dunder"``.
    """

    name: str
    signature: str
    summary: str
    kind: str


class Entry(NamedTuple):
    """One documented symbol in the library.

    Attributes:
        name (str): The symbol's public name, such as ``"Option"``.
        module (str): The dotted module that defines it.
        kind (str): ``"class"``, ``"function"``, ``"type"``, or ``"constant"``.
        signature (str): Rendered signature, or an empty string.
        summary (str): The first paragraph of the docstring.
        description (str): The full docstring, or an empty string.
        bases (tuple): Base classes as ``"module.Name"`` strings.
        methods (tuple): Nested :class:`MethodEntry` values.
        fields (tuple): ``__slots__`` or annotated field names.
        examples (tuple): Doctest lines found in the docstring.
        tags (tuple): Lowercased keywords used for search.
    """

    name: str
    module: str
    kind: str
    signature: str
    summary: str
    description: str
    bases: tuple[str, ...]
    methods: tuple[MethodEntry, ...]
    fields: tuple[str, ...]
    examples: tuple[str, ...]
    tags: tuple[str, ...]

    @property
    def is_callable(self) -> bool:
        """Return whether the entry can be constructed or called directly.

        Returns:
            bool: True for classes and functions.
        """
        return self.kind in ("class", "function")

    @property
    def reference(self) -> str:
        """Return the fully-qualified dotted path.

        Returns:
            str: A path such as ``"oxide.core.option.Option"``.
        """
        return f"{self.module}.{self.name}"


def _clean_doc(doc: str | None) -> str:
    """Dedent and normalise a docstring, dropping trailing whitespace."""
    if not doc:
        return ""
    return textwrap.dedent(doc).strip()


def _summary_of(doc: str) -> str:
    """Return the first sentence or paragraph of a docstring."""
    if not doc:
        return ""
    for block in doc.split("\n\n"):
        text = " ".join(block.split())
        if text and not text.startswith(("Args:", "Returns:", "Example", "Raises:", "Yields:")):
            return text
    return " ".join(doc.split("\n\n")[0].split())


def _examples_of(doc: str) -> tuple[str, ...]:
    """Extract the doctest lines from a docstring."""
    if not doc:
        return ()
    lines = doc.splitlines()
    examples: list[str] = []
    collecting = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(">>>"):
            collecting = True
            examples.append(stripped)
        elif collecting:
            if stripped.startswith("..."):
                examples.append(stripped)
            elif stripped:
                examples.append(stripped)
                collecting = False
            else:
                examples.append("")
    while examples and not examples[-1]:
        examples.pop()
    return tuple(examples)


def _signature_of(obj: Any) -> str:
    """Render a callable's signature, tolerating builtins and C functions."""
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "(...)"


def _classify(target: Any) -> str:
    """Classify a symbol into a coarse kind for display purposes."""
    if inspect.isclass(target):
        return "type" if issubclass(target, enum.Enum) else "class"
    if inspect.isroutine(target):
        return "function"
    return "constant"


def _method_entries(cls: type, *, include_dunders: bool = True) -> tuple[MethodEntry, ...]:
    """Collect the documented public methods defined on a class.

    Private helpers are skipped: a reference page should describe the API, not
    the implementation.
    """
    entries: list[MethodEntry] = []
    seen: set[str] = set()
    for name, member in sorted(vars(cls).items()):
        if name.startswith("_"):
            continue
        if name in seen:
            continue
        seen.add(name)
        if isinstance(member, property):
            entries.append(MethodEntry(name, "", _summary_of(_clean_doc(member.__doc__)), "property"))
            continue
        if isinstance(member, staticmethod):
            kind, target = "staticmethod", member.__func__
        elif isinstance(member, classmethod):
            kind, target = "classmethod", member.__func__
        elif inspect.isroutine(member):
            kind, target = ("dunder" if name.startswith("__") else "method"), member
        else:
            continue
        entries.append(MethodEntry(name, _signature_of(target),
                                   _summary_of(_clean_doc(target.__doc__)), kind))
    return tuple(entries)


def _fields_of(cls: type) -> tuple[str, ...]:
    """Collect a class's field names from ``__slots__`` or its annotations.

    Names are reported exactly as declared, so a private ``_data`` slot shows
    up as ``_data`` rather than being silently renamed.

    Args:
        cls: The class to inspect.

    Returns:
        tuple: The field names, in declaration order.
    """
    slots = cls.__dict__.get("__slots__")
    if isinstance(slots, str):
        slots = (slots,)
    if slots:
        return tuple(str(name) for name in slots)
    annotations = cls.__dict__.get("__annotations__") or {}
    return tuple(name for name in annotations if not str(annotations[name]).startswith("ClassVar"))


def _bases_of(cls: type) -> tuple[str, ...]:
    """Collect a class's base classes, omitting the implicit ``object``.

    Args:
        cls: The class to inspect.

    Returns:
        tuple: Dotted base class names, excluding ``builtins.object``.
    """
    return tuple(
        f"{base.__module__}.{base.__name__}"
        for base in getattr(cls, "__bases__", ())
        if base is not object
    )


class Catalog:
    """An index of every public symbol the library exports.

    Built once by :meth:`build` and then queried in memory. Every query method
    returns plain tuples, so a catalog is safe to hand around and cheap to keep.

    Attributes:
        entries (tuple): Every :class:`Entry` found, sorted by name.

    Example:
        >>> catalog = Catalog.build()
        >>> "Vec" in catalog.names()
        True
        >>> catalog.count() == len(catalog.names())
        True
        >>> catalog.count() > 100
        True
        >>> entry = catalog.lookup("Vec")
        >>> entry.kind
        'class'
        >>> any(m.name == "push" for m in entry.methods)
        True
    """

    __slots__ = ("_by_name", "_by_module", "_modules", "_module_docs")

    def __init__(
        self,
        entries: tuple[Entry, ...],
        modules: dict[str, str],
        module_docs: dict[str, str] | None = None,
    ) -> None:
        """Create a catalog from pre-built entries.

        Args:
            entries: Every documented symbol.
            modules: Mapping of module name to its summary line.
            module_docs: Mapping of module name to its full docstring.
        """
        self._by_name: dict[str, Entry] = {}
        for entry in entries:
            self._by_name.setdefault(entry.name, entry)
        self._by_module = dict(modules)
        self._modules = tuple(sorted(modules))
        self._module_docs = dict(module_docs or {})

    @classmethod
    def build(
        cls,
        *,
        max_methods: int = 200,
    ) -> "Catalog":
        """Scan the ``oxide`` package and index everything public.

        Args:
            max_methods: Cap on methods recorded per class, to keep a base class
                with hundreds of members from bloating the index.

        Returns:
            Catalog: The populated index.
        """
        import oxide

        entries: list[Entry] = []
        modules: dict[str, str] = {}
        module_docs: dict[str, str] = {}

        for package_name in PUBLIC_PACKAGES:
            package = _import(package_name)
            if package is None:
                continue
            doc = _clean_doc(getattr(package, "__doc__", ""))
            modules[package_name] = _summary_of(doc)
            module_docs[package_name] = doc
            entries.extend(_scan_module(package_name, package, max_methods))

        for name in getattr(oxide, "__all__", ()):
            if name in {entry.name for entry in entries}:
                continue
            target = getattr(oxide, name, None)
            if target is None:
                continue
            # Reuse the package introspector so top-level re-exports carry the
            # same methods, bases, and fields as their defining module's entry.
            entries.append(
                _entry_for(
                    name,
                    getattr(target, "__module__", "oxide"),
                    target,
                    max_methods,
                )
            )

        entries.sort(key=lambda entry: entry.name)
        return cls(tuple(entries), modules, module_docs)

    def names(self) -> tuple[str, ...]:
        """Return every indexed symbol name, sorted.

        Returns:
            tuple: The names.

        Example:
            >>> catalog = Catalog.build()
            >>> "Option" in catalog.names()
            True
        """
        return tuple(sorted(self._by_name))

    def module_names(self) -> tuple[str, ...]:
        """Return every indexed subpackage name, sorted.

        Returns:
            tuple: The subpackage names, with the ``oxide.`` prefix stripped.
        """
        return self._modules

    def count(self) -> int:
        """Return how many symbols are indexed.

        Returns:
            int: The number of entries.
        """
        return len(self._by_name)

    def module_count(self) -> int:
        """Return how many subpackages are indexed.

        Returns:
            int: The number of subpackages.
        """
        return len(self._modules)

    def lookup(self, name: str) -> Entry | None:
        """Return the entry for one symbol.

        Args:
            name: The symbol name, matched case-insensitively.

        Returns:
            Entry | None: The entry, or None when the symbol is not indexed.

        Example:
            >>> catalog = Catalog.build()
            >>> catalog.lookup("option").module
            'core.option'
            >>> catalog.lookup("not_a_symbol") is None
            True
        """
        if name in self._by_name:
            return self._by_name[name]
        lowered = name.lower()
        for key, entry in self._by_name.items():
            if key.lower() == lowered:
                return entry
        return None

    def module_summary(self, module: str) -> str:
        """Return the summary line of a subpackage's docstring.

        Args:
            module: The module name, with or without the ``oxide.`` prefix.

        Returns:
            str: The summary, or an empty string when the module is unknown.

        Example:
            >>> Catalog.build().module_summary("oxide.filter")
            'Filter subpackage — PHP ``filter_var()``-style validation and sanitization.'
        """
        return _summary_of(self._module_docs.get(_normalize_module(module), ""))

    def module_doc(self, module: str) -> str:
        """Return a subpackage's full docstring.

        Args:
            module: The module name, with or without the ``oxide.`` prefix.

        Returns:
            str: The docstring, or an empty string when the module is unknown.
        """
        return self._module_docs.get(_normalize_module(module), "")

    def in_module(self, module: str) -> tuple[Entry, ...]:
        """Return every entry defined by one module.

        Args:
            module: The module name, with or without the ``oxide.`` prefix.

        Returns:
            tuple: Matching entries, sorted by name. Empty when none match.

        Example:
            >>> entries = Catalog.build().in_module("oxide.core.option")
            >>> "Option" in [entry.name for entry in entries]
            True
        """
        needle = _normalize_module(module)
        return tuple(entry for entry in self._by_name.values() if entry.module == needle)

    def of_kind(self, kind: str) -> tuple[Entry, ...]:
        """Return every entry of one kind.

        Args:
            kind: ``"class"``, ``"function"``, ``"type"``, or ``"constant"``.

        Returns:
            tuple: Matching entries, sorted by name.

        Example:
            >>> all(entry.kind == "class" for entry in Catalog.build().of_kind("class"))
            True
        """
        return tuple(entry for entry in self._by_name.values() if entry.kind == kind)

    def search(self, query: str, *, limit: int = 25, in_methods: bool = False) -> tuple[Entry, ...]:
        """Find entries matching a free-text query.

        Scores matches by where the term appears: the name scores highest, then
        the summary, then tags, then the full description. A substring match
        beats a tag match, and a prefix match beats a substring.

        Args:
            query: The search term. Empty or whitespace returns nothing.
            limit: Maximum number of results.
            in_methods: Also match against method names and summaries.

        Returns:
            tuple: Scored entries, best first.

        Example:
            >>> [entry.name for entry in Catalog.build().search("range", limit=3)]
            ['Range', 'RangeFrom', 'RangeFull']
        """
        term = query.strip().lower()
        if not term:
            return ()

        scored: list[tuple[int, str, Entry]] = []
        for entry in self._by_name.values():
            score = _score(entry, term, in_methods)
            if score:
                scored.append((score, entry.name, entry))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return tuple(entry for _, _, entry in scored[:limit])

    def related(self, entry: Entry) -> tuple[Entry, ...]:
        """Return entries that share a module or reference each other.

        Args:
            entry: The entry to find neighbours for.

        Returns:
            tuple: Neighbouring entries, excluding ``entry`` itself, sorted by
            name.

        Example:
            >>> catalog = Catalog.build()
            >>> names = [e.name for e in catalog.related(catalog.lookup("Option"))]
            >>> "Option" not in names
            True
            >>> "Some" in names
            True
        """
        seen: dict[str, Entry] = {}
        for candidate in self._by_name.values():
            if candidate.name == entry.name:
                continue
            if candidate.module == entry.module:
                seen[candidate.name] = candidate
                continue
            haystack = f"{candidate.bases} {candidate.summary}".lower()
            if entry.name.lower() in haystack:
                seen[candidate.name] = candidate
        return tuple(sorted(seen.values(), key=lambda item: item.name))

    def iter_modules(self) -> Iterator[tuple[str, str]]:
        """Iterate over subpackages and their summaries.

        Yields:
            tuple: ``(module_name, summary)`` pairs, sorted by module name.
        """
        for name in self._modules:
            yield name, self._module_docs.get(name, "")

    def __len__(self) -> int:
        return len(self._by_name)

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and self.lookup(name) is not None

    def __repr__(self) -> str:
        return f"Catalog({len(self._by_name)} symbols across {len(self._modules)} modules)"


def _normalize_module(module: str) -> str:
    """Strip an ``oxide.`` prefix from a module name."""
    return module[len("oxide."):] if module.startswith("oxide.") else module


def _import(name: str) -> Any:
    """Import a subpackage, returning None when it cannot be imported."""
    try:
        return importlib.import_module(f"oxide.{name}")
    except ImportError:
        return None


def _tags(name: str, doc: str) -> tuple[str, ...]:
    """Build lowercase search keywords from a symbol name and docstring."""
    words = {word for word in _split_identifier(name) if word}
    for word in _split_identifier(_summary_of(doc)):
        if len(word) > 2:
            words.add(word)
    return tuple(sorted(words))


def _split_identifier(text: str) -> list[str]:
    """Split an identifier or sentence into lowercase words."""
    words: list[str] = []
    current = ""
    for char in text:
        if char.isalnum():
            current += char.lower()
        elif current:
            words.append(current)
            current = ""
    if current:
        words.append(current)
    return words


def _score(entry: Entry, term: str, in_methods: bool) -> int:
    """Score how well one entry matches a search term. Zero means no match."""
    name = entry.name.lower()
    score = 0
    if name == term:
        score = 1000
    elif name.startswith(term):
        score = 800
    elif term in name:
        score = 600
    elif term in entry.summary.lower():
        score = 400
    elif term in entry.tags:
        score = 300
    elif term in entry.module.lower():
        score = 200
    elif term in entry.description.lower():
        score = 100
    if in_methods and not score:
        for method in entry.methods:
            if term in method.name.lower() or term in method.summary.lower():
                score = 50
                break
    return score


def _scan_module(module_name: str, package: Any, max_methods: int) -> list[Entry]:
    """Collect the entries a package re-exports, recursing into its modules."""
    collected: dict[str, Entry] = {}
    package_name = f"oxide.{module_name}"

    modules: list[tuple[str, Any]] = [(package_name, package)]
    if hasattr(package, "__path__"):
        for info in pkgutil.walk_packages(package.__path__, prefix=f"{package_name}."):
            if any(part.startswith("_") and not part.startswith("__")
                   for part in info.name.split(".")[1:]):
                continue
            sub = _import_module(info.name)
            if sub is not None:
                modules.append((info.name, sub))

    for dotted, module in modules:
        for name in getattr(module, "__all__", ()) or ():
            if name.startswith("_"):
                continue
            target = getattr(module, name, None)
            if target is None or name in collected:
                continue
            collected[name] = _entry_for(name, dotted, target, max_methods)

    return list(collected.values())


def _import_module(dotted: str) -> Any:
    """Import a dotted module name, returning None when it cannot be imported."""
    try:
        return importlib.import_module(dotted)
    except ImportError:
        return None


def _entry_for(name: str, module: str, target: Any, max_methods: int) -> Entry:
    """Build an :class:`Entry` for one symbol.

    The module name is stored without its ``oxide.`` prefix so every consumer
    formats references the same way.
    """
    doc = _clean_doc(getattr(target, "__doc__", ""))
    is_class = inspect.isclass(target)
    return Entry(
        name=name,
        module=_normalize_module(module),
        kind=_classify(target),
        signature=_signature_of(target) if callable(target) else "",
        summary=_summary_of(doc),
        description=doc,
        bases=_bases_of(target) if is_class else (),
        methods=_method_entries(target, include_dunders=False)[:max_methods] if is_class else (),
        fields=_fields_of(target) if is_class else (),
        examples=_examples_of(doc),
        tags=_tags(name, doc),
    )


#: The process-wide catalog, built on first access.
_CATALOG: Catalog | None = None


def catalog(*, rebuild: bool = False) -> Catalog:
    """Return the shared catalog, building it on first use.

    Args:
        rebuild: Discard any existing catalog and scan again.

    Returns:
        Catalog: The shared catalog.

    Example:
        >>> catalog() is catalog()
        True
    """
    global _CATALOG
    if _CATALOG is None or rebuild:
        _CATALOG = Catalog.build()
    return _CATALOG


__all__ = [
    "Entry",
    "MethodEntry",
    "PUBLIC_PACKAGES",
    "Catalog",
    "catalog",
]
