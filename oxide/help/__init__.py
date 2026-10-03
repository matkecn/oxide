"""Help subpackage — documentation lookup for the whole ``oxide`` library.

Rather than making you read the README to remember whether it was ``Filter.var``
or ``Filter.validate``, this package introspects the library itself and answers.

    >>> from oxide.help import Help
    >>> Help("Option").summary
    'A container for an optional value that is either Some(value) or None_.'
    >>> Help.module("core").name
    'core'
    >>> [entry.name for entry in Help.search("filter", limit=2).matches]
    ['Filter', 'filter']

The class is named ``Help`` rather than ``help`` so that
``from oxide import *`` does not shadow the builtin. The module is still
``oxide.help``, and ``oxide.help.Help`` is the only entry point you need.

Everything is driven by :class:`~oxide.help.catalog.Catalog`, a lazily built
index of every public symbol. Building that index imports each subpackage once,
so the first query is slower than every query after it.

Example:
    >>> Help().usage().splitlines()[0]
    'oxide'
"""

from __future__ import annotations

from .catalog import Catalog, Entry, MethodEntry, catalog
from .help import Help
from .render import render_entry, render_module, render_overview, render_search

__all__ = [
    "Catalog",
    "Entry",
    "Help",
    "MethodEntry",
    "catalog",
    "render_entry",
    "render_module",
    "render_overview",
    "render_search",
]
