"""Text rendering for :class:`~oxide.help.Help`.

Kept separate from the catalog and the :class:`~oxide.help.Help` class so the
formatting can change without touching either the index or the query API.

Every function returns plain text ending in a newline-free string, so callers
can print it directly or slice it.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from .catalog import Catalog, Entry, MethodEntry

#: Width of the label column in rendered output.
LABEL_WIDTH = 14

#: Maximum methods listed for one class before the list is truncated.
METHOD_LIMIT = 40

_RULE = "-" * 72


def _wrap(text: str, width: int = 72, indent: str = "  ") -> list[str]:
    """Wrap prose to a column width, prefixing every line.

    Blank input yields no lines, so an absent docstring leaves no gap.
    """
    import textwrap

    if not text.strip():
        return []
    return textwrap.wrap(text, width=width - len(indent),
                         initial_indent=indent, subsequent_indent=indent)


def _render_doc(text: str, width: int = 72) -> list[str]:
    """Render a docstring, wrapping prose but preserving indented code blocks.

    A docstring mixes paragraphs with doctest blocks. Running the whole thing
    through a wrapper mangles the doctests, so indented lines pass through
    untouched and only the prose between them is reflowed.

    Args:
        text: The docstring to render.
        width: The column width for prose.

    Returns:
        list: Rendered lines, blank line between blocks.
    """
    if not text.strip():
        return []

    out: list[str] = []
    for block in text.split("\n\n"):
        block = block.strip("\n")
        if not block.strip():
            continue
        if any(line.startswith(("    ", "\t")) for line in block.splitlines()):
            out.extend(f"  {line}" if line.strip() else "" for line in block.splitlines())
        else:
            out.extend(_wrap(" ".join(block.split()), width=width))
        out.append("")
    while out and not out[-1]:
        out.pop()
    return out


def _field(label: str, value: str) -> str:
    """Render one ``label  value`` line with a padded label."""
    return f"  {label + ':':<{LABEL_WIDTH}}{value}"


def render_entry(entry: Entry, catalog: Catalog) -> str:
    """Render the full help page for one symbol.

    Args:
        entry: The symbol to document.
        catalog: The catalog, used to find related symbols.

    Returns:
        str: Rendered help text.

    Example:
        >>> from oxide.help.catalog import Catalog
        >>> text = render_entry(Catalog.build().lookup("Option"), Catalog.build())
        >>> text.splitlines()[0]
        'Option'
    """
    out: list[str] = [entry.name, _RULE]

    if entry.kind == "class":
        header = f"class {entry.name}{entry.signature}"
    elif entry.kind == "type":
        header = f"enum {entry.name}{entry.signature}"
    elif entry.kind == "function":
        header = f"def {entry.name}{entry.signature}"
    else:
        header = entry.name
    out.append(_field("signature", header))
    out.append(_field("module", f"oxide.{entry.module}"))

    if entry.bases:
        out.append(_field("inherits", ", ".join(_short(name) for name in entry.bases)))

    if entry.summary:
        out.append("")
        out.extend(_wrap(entry.summary))

    if entry.fields:
        out.append("")
        out.append(_field("fields", ", ".join(entry.fields)))

    if entry.methods:
        out.append("")
        out.append(f"  methods ({len(entry.methods)}):")
        out.extend(_render_methods(entry.methods))

    if entry.examples:
        out.append("")
        out.append("  examples:")
        out.extend(f"    {item}" for item in entry.examples)

    related = catalog.related(entry)
    if related:
        names = ", ".join(item.name for item in related[:12])
        more = f", +{len(related) - 12} more" if len(related) > 12 else ""
        out.append("")
        out.append(_field("related", f"{names}{more}"))

    return "\n".join(out)


def _render_methods(methods: Sequence[MethodEntry]) -> list[str]:
    """Render a class's methods as a padded, aligned listing."""
    out: list[str] = []
    shown = methods[:METHOD_LIMIT]
    width = max((len(method.name) for method in shown), default=0)
    for method in shown:
        label = f"    {method.name}:".ljust(width + 8)
        if method.signature:
            label += f"{method.signature}"
            if method.summary:
                label += f"  {method.summary}"
        elif method.summary:
            label += method.summary
        out.append(label.rstrip())
    if len(methods) > len(shown):
        out.append(f"    ... and {len(methods) - len(shown)} more")
    return out


def render_module(module: str, catalog: Catalog) -> str:
    """Render the full help page for one module.

    Args:
        module: The module name, without the ``oxide.`` prefix.
        catalog: The catalog, used to list the module's exports.

    Returns:
        str: Rendered help text.

    Example:
        >>> from oxide.help.catalog import Catalog
        >>> text = render_module("core", Catalog.build())
        >>> text.splitlines()[0]
        'oxide.core'
    """
    out: list[str] = [f"oxide.{module}", _RULE]
    doc = catalog.module_doc(module)
    if doc:
        out.append("")
        out.extend(_render_doc(doc))
    entries = catalog.in_module(module)
    if entries:
        out.append("")
        out.append(f"  exports ({len(entries)}):")
        width = max(len(entry.name) for entry in entries)
        for entry in entries:
            label = f"    {entry.name}:".ljust(width + 6)
            if entry.summary:
                label += entry.summary
            out.append(label.rstrip())
    return "\n".join(out)


def render_overview(catalog: Catalog) -> str:
    """Render an overview of every module in the library.

    Args:
        catalog: The catalog to summarise.

    Returns:
        str: Rendered help text.

    Example:
        >>> from oxide.help.catalog import Catalog
        >>> text = render_overview(Catalog.build())
        >>> text.splitlines()[0]
        'oxide'
    """
    out: list[str] = [
        "oxide",
        _RULE,
        "  Rust-inspired types and utilities for Python.",
        "",
        f"  {catalog.module_count()} modules, {catalog.count()} documented symbols.",
        "",
        "  modules:",
    ]
    width = max(len(name) for name in catalog.module_names())
    for name, summary in catalog.iter_modules():
        label = f"    {name}:".ljust(width + 6)
        if summary:
            label += _one_line(summary)
        out.append(label.rstrip())
    out.append("")
    out.append("  Usage:")
    out.append("    Help('Option')            help for one symbol")
    out.append("    Help.module('core')       help for one module")
    out.append("    Help.search('range')      free-text search")
    out.append("    Help.names()              every public symbol")
    out.append("    Help('Vec').print()       print the rendered page")
    return "\n".join(out)


def render_search(query: str, matches: Iterable[Entry]) -> str:
    """Render the results of a free-text search.

    Args:
        query: The search term that was used.
        matches: The scored entries to list.

    Returns:
        str: Rendered help text.

    Example:
        >>> from oxide.help.catalog import Catalog
        >>> catalog = Catalog.build()
        >>> text = render_search("Vec", catalog.search("Vec", limit=2))
        >>> text.splitlines()[0]
        "matches for 'Vec':"
    """
    entries = tuple(matches)
    out = [f"matches for {query!r}:", _RULE]
    if not entries:
        out.append("  (nothing found)")
        return "\n".join(out)
    width = max(len(entry.name) for entry in entries)
    for entry in entries:
        out.append(f"  {entry.name}:{entry.module}".ljust(width + 6).rstrip())
        for text in _wrap(entry.summary, indent="      "):
            out.append(text)
    return "\n".join(out)


def _one_line(text: str, limit: int = 88) -> str:
    """Collapse text to a single line, truncated to ``limit`` characters."""
    flat = " ".join(text.split())
    if len(flat) <= limit:
        return flat
    return flat[: limit - 1].rstrip() + "…"


def _short(dotted: str) -> str:
    """Reduce a dotted path to its final component."""
    return dotted.rsplit(".", 1)[-1]


__all__ = [
    "LABEL_WIDTH",
    "METHOD_LIMIT",
    "render_entry",
    "render_module",
    "render_overview",
    "render_search",
]
