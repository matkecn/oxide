"""Public interface for the ``oxide.regex`` engine.

Mirrors the surface of :mod:`re` closely enough that a pattern compiled by one
module can be used with the other, with the deliberate exception of
backreferences, lookaround, and possessive quantifiers, which are rejected at
parse time because they would require backtracking.

Example:
    >>> import oxide.regex as regex
    >>> match = regex.match(r"(\\w+)@(\\w+)", "user@example")
    >>> match.group(1)
    'user'
"""

from __future__ import annotations

from typing import Any, Callable, Iterator

from ._syntax import (
    ASCII, DOTALL, IGNORECASE, MULTILINE, UNICODE, VERBOSE, RegexError,
    compile_pattern as _parse, escape as _escape,
)
from .engine import PikeVM, compile_pattern as _compile

error = RegexError

A = ASCII
I = IGNORECASE
M = MULTILINE
S = DOTALL
U = UNICODE
X = VERBOSE


class Match:
    """The result of a successful match.

    Exposes the matched span, the captured group text, and the group names
    declared in the pattern. Capture slots that did not participate in the
    match report ``None`` unless a default is supplied.
    """

    __slots__ = ("_caps", "_re", "_string", "_pos", "_endpos")

    def __init__(
        self,
        caps: tuple,
        regex: Regex,
        string: str,
        pos: int,
        endpos: int,
    ) -> None:
        """Create a match result.

        Args:
            caps (tuple): The capture slot tuple.
            regex (Regex): The pattern that produced the match.
            string (str): The subject text.
            pos (int): The offset matching began at.
            endpos (int): The effective end of the subject.
        """
        self._caps = caps
        self._re = regex
        self._string = string
        self._pos = pos
        self._endpos = endpos

    def group(self, *groups: Any) -> Any:
        """Return one or more captured groups.

        Args:
            *groups: Group indices or names. With no arguments, returns the
                whole match.

        Returns:
            Any: The captured text, or None when the group did not participate.
            When several groups are requested, a tuple is returned.

        Raises:
            IndexError: If a group index is out of range.
            KeyError: If a group name is not in the pattern.
        """
        if not groups:
            return self._string[self._caps[0]:self._caps[1]]
        values = tuple(self._resolve(group) for group in groups)
        return values[0] if len(values) == 1 else values

    def _resolve(self, group: Any) -> str | None:
        """Resolve a group index or name to its captured text.

        Args:
            group (Any): A group index or name.

        Returns:
            str | None: The captured text, or None if unset.
        """
        index = self._re.groupindex.get(group, -1) if isinstance(group, str) else group
        if not isinstance(index, int) or isinstance(index, bool):
            raise KeyError(f"unknown group name {group!r}")
        if index < 0 or index > self._re.groups:
            raise IndexError(f"no such group: {index}")
        start, end = self._caps[2 * index], self._caps[2 * index + 1]
        if start is None or end is None:
            return None
        return self._string[start:end]

    def groups(self, default: Any = None) -> tuple:
        """Return every captured group as a tuple.

        Args:
            default (Any): The value substituted for groups that did not
                participate in the match.

        Returns:
            tuple: One entry per capturing group, in index order.
        """
        return tuple(
            default if self._caps[2 * i] is None else self._string[
                self._caps[2 * i]:self._caps[2 * i + 1]
            ]
            for i in range(1, self._re.groups + 1)
        )

    def groupdict(self, default: Any = None) -> dict:
        """Return the named capture groups as a dictionary.

        Args:
            default (Any): The value substituted for named groups that did not
                participate in the match.

        Returns:
            dict: A mapping of group name to captured text.
        """
        return {
            name: self._resolve(name) if default is None else (
                self._resolve(name) or default
            )
            for name in self._re.groupindex
        }

    def start(self, group: Any = 0) -> int:
        """Return the start offset of a group.

        Args:
            group (Any): The group index or name, defaulting to the whole match.

        Returns:
            int: The start offset, or -1 when the group did not participate.
        """
        index = self._index_of(group)
        value = self._caps[2 * index]
        return -1 if value is None else value

    def end(self, group: Any = 0) -> int:
        """Return the end offset of a group.

        Args:
            group (Any): The group index or name, defaulting to the whole match.

        Returns:
            int: The end offset, or -1 when the group did not participate.
        """
        index = self._index_of(group)
        value = self._caps[2 * index + 1]
        return -1 if value is None else value

    def span(self, group: Any = 0) -> tuple[int, int]:
        """Return the start and end offsets of a group.

        Args:
            group (Any): The group index or name, defaulting to the whole match.

        Returns:
            tuple: A ``(start, end)`` pair.
        """
        index = self._index_of(group)
        return self.start(index), self.end(index)

    def _index_of(self, group: Any) -> int:
        """Convert a group index or name to a validated integer index.

        Args:
            group (Any): The group index or name.

        Returns:
            int: The capture index.
        """
        if isinstance(group, str):
            index = self._re.groupindex.get(group, -1)
            if index < 0:
                raise KeyError(f"unknown group name {group!r}")
            return index
        if not isinstance(group, int) or isinstance(group, bool):
            raise IndexError(f"no such group: {group!r}")
        if group < 0 or group > self._re.groups:
            raise IndexError(f"no such group: {group}")
        return group

    def expand(self, template: str) -> str:
        """Expand a replacement template against this match.

        Supports ``\\1``-style group references and ``\\g<name>``-style named
        references, plus the standard ``\\n``, ``\\t``, and ``\\\\`` escapes.

        Args:
            template (str): The replacement template.

        Returns:
            str: The expanded string.

        Raises:
            KeyError: If the template names a group that does not exist.
        """
        return self._re._expand(self, template)

    def __getitem__(self, group: Any) -> Any:
        """Return a captured group, so ``match[1]`` works like ``group(1)``."""
        return self.group(group)

    def __repr__(self) -> str:
        return (
            f"<Match span=({self._caps[0]}, {self._caps[1]}) "
            f"match={self.group()!r}>"
        )


class Regex:
    """A compiled regular expression.

    Compiled patterns are immutable and safe to share between threads, since
    matching never mutates the program.
    """

    __slots__ = ("pattern", "flags", "groups", "groupindex", "_vm", "_cache")

    def __init__(self, pattern: str, flags: int = 0) -> None:
        """Compile a pattern.

        Args:
            pattern (str): The pattern source.
            flags (int): Any combination of IGNORECASE, MULTILINE, DOTALL,
                ASCII, UNICODE, and VERBOSE.

        Raises:
            RegexError: If the pattern is malformed or uses an unsupported
                construct.

        Example:
            >>> Regex(r"\\d+").search("abc 123").group()
            '123'
        """
        node, ngroups, groupnames, effective = _parse(pattern, flags)
        self.pattern = pattern
        self.flags = effective
        self.groups = ngroups
        self.groupindex = dict(groupnames)
        self._vm = PikeVM(_compile(node, ngroups, groupnames, effective, pattern))
        self._cache: dict[Any, Any] = {}

    def match(self, string: str, pos: int = 0, endpos: int | None = None) -> Match | None:
        """Match the pattern at the start of the string.

        Args:
            string (str): The subject text.
            pos (int): The offset matching begins at.
            endpos (int, optional): The effective end of the subject.

        Returns:
            Match | None: The match, or None if the pattern does not match at
            ``pos``.
        """
        return self._exec(string, pos, endpos, anchored=True, anchored_end=False)

    def fullmatch(
        self, string: str, pos: int = 0, endpos: int | None = None
    ) -> Match | None:
        """Match the pattern against the entire subject region.

        Args:
            string (str): The subject text.
            pos (int): The offset matching begins at.
            endpos (int, optional): The effective end of the subject.

        Returns:
            Match | None: The match, or None if the pattern does not consume the
            whole region.
        """
        return self._exec(string, pos, endpos, anchored=True, anchored_end=True)

    def search(
        self, string: str, pos: int = 0, endpos: int | None = None
    ) -> Match | None:
        """Search for the first match anywhere in the subject.

        Args:
            string (str): The subject text.
            pos (int): The offset searching begins at.
            endpos (int, optional): The effective end of the subject.

        Returns:
            Match | None: The leftmost match, or None.
        """
        return self._exec(string, pos, endpos, anchored=False, anchored_end=False)

    def finditer(
        self, string: str, pos: int = 0, endpos: int | None = None
    ) -> Iterator[Match]:
        """Yield successive non-overlapping matches.

        After a zero-length match the same position is retried while requiring
        a match that consumed input, so a pattern such as ``|a`` reports the
        empty match and the longer one that follows it at the same offset, the
        way the standard library does.

        Args:
            string (str): The subject text.
            pos (int): The offset searching begins at.
            endpos (int, optional): The effective end of the subject.

        Yields:
            Match: Each match in order. Iteration always terminates.
        """
        end = len(string) if endpos is None else min(endpos, len(string))
        cursor = max(pos, 0)
        while cursor <= end:
            found = self.search(string, cursor, end)
            if found is None:
                return
            start, stop = found.span()
            yield found
            if stop != start:
                cursor = stop
                continue
            longer = self._exec(string, start, end, True, False, progress=True)
            if longer is not None:
                yield longer
                cursor = longer.span()[1]
                if cursor > end:
                    return
            elif start >= end:
                return
            else:
                cursor = start + 1

    def findall(
        self, string: str, pos: int = 0, endpos: int | None = None
    ) -> list:
        """Return every non-overlapping match as a list of strings or tuples.

        Mirrors :func:`re.findall`: a pattern with no groups yields whole-match
        strings, a pattern with one group yields that group's text, and a
        pattern with several groups yields tuples. A group that did not take
        part in the match is reported as ``""`` here, whereas :meth:`split`
        reports ``None``, again following the standard library.

        Args:
            string (str): The subject text.
            pos (int): The offset searching begins at.
            endpos (int, optional): The effective end of the subject.

        Returns:
            list: The collected matches.
        """
        results: list = []
        for found in self.finditer(string, pos, endpos):
            if self.groups == 0:
                results.append(found.group())
            elif self.groups == 1:
                results.append(found.group(1) or "")
            else:
                results.append(tuple(text or "" for text in found.groups()))
        return results

    def split(
        self,
        string: str,
        maxsplit: int = 0,
        flags: int = 0,
    ) -> list:
        """Split the subject on matches of the pattern.

        Capturing groups are included in the result between the pieces, and
        empty matches split just as they do in the standard library.

        Args:
            string (str): The subject text.
            maxsplit (int): The maximum number of splits, or 0 for no limit.
            flags (int): Extra flags applied on top of those used to compile.

        Returns:
            list: The substrings between matches, interleaved with captures.
        """
        source = self if not flags else compile(self.pattern, self.flags | flags)
        pieces: list = []
        cursor = 0
        count = 0
        for found in source.finditer(string):
            if maxsplit and count >= maxsplit:
                break
            start, stop = found.span()
            pieces.append(string[cursor:start])
            for group in range(1, source.groups + 1):
                pieces.append(found.group(group))
            cursor = stop
            count += 1
        pieces.append(string[cursor:])
        return pieces

    def sub(
        self, repl: str | Callable[[Match], str], string: str, count: int = 0
    ) -> str:
        """Replace matches of the pattern in the subject.

        Args:
            repl (str | Callable): A replacement template or a callable taking a
                match and returning the replacement.
            string (str): The subject text.
            count (int): The maximum number of replacements, or 0 for all.

        Returns:
            str: The subject with matches replaced.

        Raises:
            TypeError: If ``repl`` is neither a string nor a callable.
        """
        return self.subn(repl, string, count)[0]

    def subn(
        self, repl: str | Callable[[Match], str], string: str, count: int = 0
    ) -> tuple[str, int]:
        """Replace matches of the pattern, reporting how many were replaced.

        Args:
            repl (str | Callable): A replacement template or a callable taking a
                match and returning the replacement.
            string (str): The subject text.
            count (int): The maximum number of replacements, or 0 for all.

        Returns:
            tuple: The resulting string and the number of replacements.

        Raises:
            TypeError: If ``repl`` is neither a string nor a callable.
        """
        if not isinstance(repl, str) and not callable(repl):
            raise TypeError(
                f"expected string or callable, got {type(repl).__name__}"
            )
        out: list[str] = []
        cursor = 0
        done = 0
        for found in self.finditer(string):
            if count and done >= count:
                break
            start, stop = found.span()
            out.append(string[cursor:start])
            out.append(repl(found) if callable(repl) else self._expand(found, repl))
            cursor = stop
            done += 1
        out.append(string[cursor:])
        return "".join(out), done

    def _expand(self, found: Match, template: str) -> str:
        """Expand a replacement template against a match.

        Args:
            found (Match): The match being replaced.
            template (str): The replacement template.

        Returns:
            str: The expanded replacement.
        """
        out: list[str] = []
        index = 0
        size = len(template)
        while index < size:
            char = template[index]
            if char != "\\":
                out.append(char)
                index += 1
                continue
            index += 1
            if index >= size:
                raise RegexError("bad escape (end of pattern)", template, index)
            marker = template[index]
            if marker == "g" and index + 1 < size and template[index + 1] == "<":
                close = template.find(">", index + 2)
                if close < 0:
                    raise RegexError("missing >, unterminated name", template, index)
                out.append(self._group_text(found, template[index + 2:close]))
                index = close + 1
                continue
            if marker.isdigit():
                digits = marker
                while (
                    index + 1 < size
                    and template[index + 1].isdigit()
                    and len(digits) < 2
                ):
                    digits += template[index + 1]
                    index += 1
                index += 1
                out.append(self._group_text(found, int(digits)))
                continue
            index += 1
            out.append({"n": "\n", "t": "\t", "r": "\r", "f": "\f", "v": "\v", "0": "\0", "\\": "\\"}.get(marker, "\\" + marker))
        return "".join(out)

    def _group_text(self, found: Match, group: Any) -> str:
        """Return a group's text for replacement, treating None as empty.

        Args:
            found (Match): The match being replaced.
            group (Any): A group index or name.

        Returns:
            str: The group's text, or "" when it did not participate.
        """
        if isinstance(group, str) and group.isdigit():
            group = int(group)
        try:
            text = found.group(group)
        except (IndexError, KeyError):
            raise RegexError(
                f"invalid group reference {group!r}", self.pattern, 0
            ) from None
        return text or ""

    def _exec(
        self,
        string: str,
        pos: int,
        endpos: int | None,
        anchored: bool,
        anchored_end: bool,
        progress: bool = False,
    ) -> Match | None:
        """Run the virtual machine and wrap the result.

        Args:
            string (str): The subject text.
            pos (int): The offset to begin at.
            endpos (int, optional): The effective end of the subject.
            anchored (bool): Whether to anchor the match start.
            anchored_end (bool): Whether the match must reach the end.
            progress (bool): When True, reject zero-length matches.

        Returns:
            Match | None: The match, or None.
        """
        if not isinstance(string, str):
            raise TypeError(f"expected string, got {type(string).__name__}")
        end = len(string) if endpos is None else min(endpos, len(string))
        begin = max(pos, 0)
        caps = self._vm.search(string, begin, end, anchored, anchored_end, progress)
        if caps is None:
            return None
        return Match(caps, self, string, begin, end)

    def __repr__(self) -> str:
        return f"Regex({self.pattern!r}, flags={self.flags})"


_CACHE: dict[tuple[str, int], Regex] = {}


def compile(pattern: str, flags: int = 0) -> Regex:  # noqa: A001
    """Compile a pattern, caching the result.

    Args:
        pattern (str): The pattern source.
        flags (int): Any combination of flag constants.

    Returns:
        Regex: The compiled pattern.

    Raises:
        RegexError: If the pattern is malformed.

    Example:
        >>> compile(r"a+") is compile(r"a+")
        True
    """
    key = (pattern, flags)
    cached = _CACHE.get(key)
    if cached is None:
        cached = Regex(pattern, flags)
        if len(_CACHE) > 512:
            _CACHE.clear()
        _CACHE[key] = cached
    return cached


def purge() -> None:
    """Empty the compiled-pattern cache."""
    _CACHE.clear()


def match(pattern: str, string: str, flags: int = 0) -> Match | None:
    """Match a pattern at the start of a string.

    Args:
        pattern (str): The pattern source.
        string (str): The subject text.
        flags (int): Any combination of flag constants.

    Returns:
        Match | None: The match, or None.
    """
    return compile(pattern, flags).match(string)


def fullmatch(pattern: str, string: str, flags: int = 0) -> Match | None:
    """Match a pattern against the whole of a string.

    Args:
        pattern (str): The pattern source.
        string (str): The subject text.
        flags (int): Any combination of flag constants.

    Returns:
        Match | None: The match, or None.
    """
    return compile(pattern, flags).fullmatch(string)


def search(pattern: str, string: str, flags: int = 0) -> Match | None:
    """Search for the first match of a pattern in a string.

    Args:
        pattern (str): The pattern source.
        string (str): The subject text.
        flags (int): Any combination of flag constants.

    Returns:
        Match | None: The leftmost match, or None.
    """
    return compile(pattern, flags).search(string)


def findall(pattern: str, string: str, flags: int = 0) -> list:
    """Return every non-overlapping match of a pattern in a string.

    Args:
        pattern (str): The pattern source.
        string (str): The subject text.
        flags (int): Any combination of flag constants.

    Returns:
        list: The collected matches.
    """
    return compile(pattern, flags).findall(string)


def finditer(pattern: str, string: str, flags: int = 0) -> Iterator[Match]:
    """Yield successive non-overlapping matches of a pattern in a string.

    Args:
        pattern (str): The pattern source.
        string (str): The subject text.
        flags (int): Any combination of flag constants.

    Yields:
        Match: Each match in order.
    """
    return compile(pattern, flags).finditer(string)


def split(
    pattern: str, string: str, maxsplit: int = 0, flags: int = 0
) -> list:
    """Split a string on matches of a pattern.

    Args:
        pattern (str): The pattern source.
        string (str): The subject text.
        maxsplit (int): The maximum number of splits, or 0 for no limit.
        flags (int): IGNORECASE to match case-insensitively.

    Returns:
        list: The substrings between matches.
    """
    return compile(pattern, flags).split(string, maxsplit, flags)


def sub(
    pattern: str,
    repl: str | Callable[[Match], str],
    string: str,
    count: int = 0,
    flags: int = 0,
) -> str:
    """Replace matches of a pattern in a string.

    Args:
        pattern (str): The pattern source.
        repl (str | Callable): A replacement template or a callable.
        string (str): The subject text.
        count (int): The maximum number of replacements, or 0 for all.
        flags (int): Any combination of flag constants.

    Returns:
        str: The resulting string.
    """
    return compile(pattern, flags).sub(repl, string, count)


def subn(
    pattern: str,
    repl: str | Callable[[Match], str],
    string: str,
    count: int = 0,
    flags: int = 0,
) -> tuple[str, int]:
    """Replace matches of a pattern, reporting how many were replaced.

    Args:
        pattern (str): The pattern source.
        repl (str | Callable): A replacement template or a callable.
        string (str): The subject text.
        count (int): The maximum number of replacements, or 0 for all.
        flags (int): Any combination of flag constants.

    Returns:
        tuple: The resulting string and the replacement count.
    """
    return compile(pattern, flags).subn(repl, string, count)


def escape(text: str) -> str:
    """Escape a literal string so it matches itself in a pattern.

    Args:
        text (str): The literal text to escape.

    Returns:
        str: The escaped pattern source.
    """
    return _escape(text)