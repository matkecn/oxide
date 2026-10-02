"""Pattern syntax for the ``oxide.regex`` engine.

Contains the abstract syntax tree, the recursive-descent parser that produces
it, and the character-class machinery shared with the compiler.

The accepted syntax is a deliberate subset of Python's ``re`` that matches the
capability set of Rust's ``regex`` crate. In particular the following are
rejected with a clear error rather than silently accepted, because supporting
them would require backtracking and would forfeit the engine's linear-time
guarantee:

- backreferences, both ``\\1`` and ``(?P=name)``
- lookaround, both ``(?=...)``/``(?!)`` and lookbehind
- possessive quantifiers such as ``a*+``
- atomic groups ``(?>...)``

Numeric flag values are chosen to match :mod:`re` exactly so patterns and flags
can be shared between the two engines without translation.
"""

from __future__ import annotations

import unicodedata
from typing import Any, Callable

ASCII = 256
IGNORECASE = 2
MULTILINE = 8
DOTALL = 16
UNICODE = 32
VERBOSE = 64

_FOLD_SCAN_LIMIT = 0x1000
_FOLD_REVERSE_LIMIT = 0x3000
_FOLD_REVERSE: dict[int, tuple[int, ...]] | None = None

META = frozenset("\\^$.[]|()?*+{}")

ESCAPE_CHARS = frozenset("()[]{}?*+-|^$\\.&~# \t\n\r\v\f")

DIGIT_RANGES = ((0x30, 0x39),)
ASCII_WORD_RANGES = ((0x30, 0x39), (0x41, 0x5A), (0x5F, 0x5F), (0x61, 0x7A))
ASCII_SPACE_RANGES = ((0x09, 0x0D), (0x20, 0x20))
WORD_RANGES = ASCII_WORD_RANGES

SIMPLE_ESCAPES = {
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "f": "\f",
    "v": "\v",
    "a": "\a",
    "0": "\0",
}

CLASS_ESCAPE_KINDS = frozenset("dDwWsS")

POSIX_RANGES: dict[str, tuple[tuple[int, int], ...]] = {
    "alpha": ((0x41, 0x5A), (0x61, 0x7A)),
    "digit": ((0x30, 0x39),),
    "alnum": ((0x30, 0x39), (0x41, 0x5A), (0x61, 0x7A)),
    "upper": ((0x41, 0x5A),),
    "lower": ((0x61, 0x7A),),
    "space": ((0x09, 0x0D), (0x20, 0x20)),
    "blank": ((0x09, 0x09), (0x20, 0x20)),
    "punct": (
        (0x21, 0x2F), (0x3A, 0x40), (0x5B, 0x60), (0x7B, 0x7E),
    ),
    "xdigit": ((0x30, 0x39), (0x41, 0x46), (0x61, 0x66)),
    "word": ((0x30, 0x39), (0x41, 0x5A), (0x5F, 0x5F), (0x61, 0x7A)),
    "graph": ((0x21, 0x7E),),
    "print": ((0x20, 0x7E),),
    "cntrl": ((0x00, 0x1F), (0x7F, 0x7F)),
}

POSIX_PREDICATES: dict[str, Callable[[str], bool]] = {
    "alpha": lambda ch: ch.isalpha(),
    "alnum": lambda ch: ch.isalnum(),
    "space": lambda ch: ch.isspace(),
    "punct": lambda ch: not ch.isalnum() and not ch.isspace() and ch.isprintable(),
    "word": lambda ch: ch.isalnum() or ch == "_",
    "blank": lambda ch: ch in " \t",
    "graph": lambda ch: ch.isprintable() and not ch.isspace(),
    "print": lambda ch: ch.isprintable(),
    "cntrl": lambda ch: ord(ch) < 0x20 or ord(ch) == 0x7F,
    "upper": lambda ch: ch.isupper(),
    "lower": lambda ch: ch.islower(),
    "digit": lambda ch: ch.isdigit(),
    "xdigit": lambda ch: ch in "0123456789abcdefABCDEF",
}

FLAG_LETTERS = {
    "i": IGNORECASE,
    "m": MULTILINE,
    "s": DOTALL,
    "x": VERBOSE,
    "a": ASCII,
    "u": UNICODE,
}

ANCHOR_KINDS = frozenset(
    ("start", "end", "text_start", "text_end", "word", "not_word")
)


class RegexError(Exception):
    """Raised when a pattern cannot be parsed.

    Carries the offending pattern, the failure message, and the character offset
    at which parsing stopped.

    Example:
        >>> try:
        ...     _parse("(unclosed", 0)
        ... except RegexError as e:
        ...     e.msg()
        'missing ), unterminated subpattern'
    """

    __slots__ = ("_msg", "_pattern", "_pos")

    def __init__(self, msg: str, pattern: str = "", pos: int = 0) -> None:
        """Create a parse failure.

        Args:
            msg (str): A description of the failure.
            pattern (str): The pattern being parsed.
            pos (int): The character offset at which parsing stopped.
        """
        super().__init__(msg if not pattern else f"{msg} at position {pos}")
        self._msg = msg
        self._pattern = pattern
        self._pos = pos

    def msg(self) -> str:
        """Return the failure message without position context.

        Returns:
            str: The error message.
        """
        return self._msg

    def pattern(self) -> str:
        """Return the pattern that failed to parse.

        Returns:
            str: The offending pattern.
        """
        return self._pattern

    def pos(self) -> int:
        """Return the offset at which parsing failed.

        Returns:
            int: The character offset.
        """
        return self._pos


class Node:
    """Base class for every abstract syntax tree node."""

    __slots__ = ()


class Empty(Node):
    """A node that matches the empty string."""

    __slots__ = ()


class Literal(Node):
    """A node matching one literal character."""

    __slots__ = ("char",)

    def __init__(self, char: str) -> None:
        """Create a literal node.

        Args:
            char (str): The character to match.
        """
        self.char = char


class CharAtom:
    """One union term of a character class, with its own optional inversion.

    Keeping terms separate is what lets ``[\\D]`` mean "not a digit" instead of
    collapsing to the digit ranges, which a single flattened range set cannot
    express.

    Attributes:
        ranges (tuple): Inclusive code-point ranges in the term.
        predicates (tuple): Predicate functions matched in addition.
        negated (bool): Whether the term is inverted.
    """

    __slots__ = ("ranges", "predicates", "negated")

    def __init__(
        self,
        ranges: tuple[tuple[int, int], ...] = (),
        predicates: tuple[Callable[[str], bool], ...] = (),
        negated: bool = False,
    ) -> None:
        """Create a class term.

        Args:
            ranges (tuple): Inclusive code-point ranges, already normalised.
            predicates (tuple): Predicate functions matched in addition.
            negated (bool): Whether the term is inverted.
        """
        self.ranges = ranges
        self.predicates = predicates
        self.negated = negated

    def matches(self, char: str) -> bool:
        """Return whether a character belongs to this term.

        Args:
            char (str): The character to test.

        Returns:
            bool: True when the character is in the term.
        """
        hit = _in_ranges(self.ranges, char)
        if not hit:
            for predicate in self.predicates:
                if predicate(char):
                    hit = True
                    break
        return hit != self.negated


class CharClass(Node):
    """A node matching one character from a set.

    A class is the union of its atoms, optionally inverted as a whole.
    """

    __slots__ = ("atoms", "negated")

    def __init__(self, atoms: tuple[CharAtom, ...], negated: bool = False) -> None:
        """Create a character class node.

        Args:
            atoms (tuple): The union terms of the class.
            negated (bool): Whether the whole class is inverted.
        """
        self.atoms = atoms
        self.negated = negated

    def matches(self, char: str) -> bool:
        """Return whether a character belongs to this class.

        Args:
            char (str): The character to test.

        Returns:
            bool: True when the character is in the class.
        """
        for atom in self.atoms:
            if atom.matches(char):
                return not self.negated
        return self.negated


class AnyChar(Node):
    """A node matching any character, honouring the DOTALL flag."""

    __slots__ = ("dotall",)

    def __init__(self, dotall: bool) -> None:
        """Create a wildcard node.

        Args:
            dotall (bool): When True, newline characters also match.
        """
        self.dotall = dotall


class Anchor(Node):
    """A zero-width assertion such as ``^``, ``$``, or ``\\b``."""

    __slots__ = ("kind",)

    def __init__(self, kind: str) -> None:
        """Create an anchor node.

        Args:
            kind (str): One of the values in :data:`ANCHOR_KINDS`.
        """
        self.kind = kind


class Concat(Node):
    """A node matching each of its items in sequence."""

    __slots__ = ("items",)

    def __init__(self, items: tuple[Node, ...]) -> None:
        """Create a concatenation node.

        Args:
            items (tuple): The child nodes, in order.
        """
        self.items = items


class Alternate(Node):
    """A node matching any one of its branches."""

    __slots__ = ("branches",)

    def __init__(self, branches: tuple[Node, ...]) -> None:
        """Create an alternation node.

        Args:
            branches (tuple): The alternative branches, in priority order.
        """
        self.branches = branches


class Repeat(Node):
    """A node matching its child a bounded or unbounded number of times."""

    __slots__ = ("node", "min", "max", "greedy")

    def __init__(
        self, node: Node, minimum: int, maximum: int | None, greedy: bool
    ) -> None:
        """Create a repetition node.

        Args:
            node (Node): The repeated subexpression.
            minimum (int): The minimum number of repetitions.
            maximum (int | None): The maximum, or None for unbounded.
            greedy (bool): True for greedy, False for lazy.
        """
        self.node = node
        self.min = minimum
        self.max = maximum
        self.greedy = greedy


class Group(Node):
    """A node wrapping a subexpression, capturing it when indexed."""

    __slots__ = ("node", "index")

    def __init__(self, node: Node, index: int | None) -> None:
        """Create a group node.

        Args:
            node (Node): The grouped subexpression.
            index (int | None): The capture index, or None when non-capturing.
        """
        self.node = node
        self.index = index


def _case_shift(value: int, shift: int) -> int | None:
    """Return a case-shifted code point when the shift stays a single character.

    Args:
        value (int): The code point to shift.
        shift (int): ``32`` to reach the opposite ASCII letter case, else ``0``.

    Returns:
        int | None: The shifted code point, or None when the shift is not
        expressible as a simple code-point adjustment.
    """
    if shift == 0:
        return value
    if 65 <= value <= 90 or 97 <= value <= 122:
        return value + shift
    return None


def _simple_lower(value: int) -> int:
    """Return the simple lowercase mapping of a code point.

    Simple mappings never expand to several characters, so ``ß`` maps to itself
    while ``İ`` maps to ``i``. A full lowercase result keeps only its first
    character when the remainder is combining marks, which is how simple
    mappings treat characters such as ``ΐ``.

    Args:
        value (int): The code point to map.

    Returns:
        int: The simple lowercase code point.
    """
    char = chr(value)
    lower = char.lower()
    if len(lower) == 1:
        return ord(lower)
    if all(unicodedata.category(part) == "Mn" for part in lower[1:]):
        return ord(lower[0])
    return value


def _simple_upper(value: int) -> int:
    """Return the simple uppercase mapping of a code point.

    Args:
        value (int): The code point to map.

    Returns:
        int: The simple uppercase code point.
    """
    upper = chr(value).upper()
    return ord(upper) if len(upper) == 1 else value


def _fold_reverse() -> dict[int, tuple[int, ...]]:
    """Return code points that fold onto others, keyed by the folded code point.

    The reference engine also matches the reverse direction of a simple mapping,
    so ``σ`` matches ``ς`` and ``i`` matches ``İ``. Reverse pairs inside the
    scripts that carry case are all found below the window; rarer supplementary
    scripts are not scanned.

    Returns:
        dict: Mapping from a folded code point to the code points folding onto it.
    """
    global _FOLD_REVERSE
    if _FOLD_REVERSE is None:
        reverse: dict[int, list[int]] = {}
        for point in range(_FOLD_REVERSE_LIMIT):
            for key in (_simple_lower(point), _simple_upper(point)):
                if key != point:
                    reverse.setdefault(key, []).append(point)
        _FOLD_REVERSE = {key: tuple(value) for key, value in reverse.items()}
    return _FOLD_REVERSE


def _case_variants(value: int) -> tuple[int, ...]:
    """Return every code point that IGNORECASE should treat as ``value``.

    Mirrors the reference engine, which folds a literal against its lower and
    its upper form plus the code points that fold back onto those, so ``é``
    matches ``É``, ``σ`` matches ``ς``, and ``ẛ`` matches ``ṡ``.

    Args:
        value (int): The code point to fold.

    Returns:
        tuple: Code points equivalent to ``value`` under IGNORECASE.
    """
    lower = _simple_lower(value)
    upper = _simple_upper(value)
    seeds = tuple(dict.fromkeys((value, lower, upper)))
    reverse = _fold_reverse()
    targets = list(seeds)
    for seed in (lower, upper):
        targets.extend(reverse.get(seed, ()))
    return tuple(dict.fromkeys(targets))


def _expand_ignorecase(ranges: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    """Widen a set of ranges with its IGNORECASE equivalents.

    Args:
        ranges (tuple): Inclusive code-point ranges.

    Returns:
        tuple: The widened, normalised ranges.
    """
    widened = RangeSet()
    for low, high in ranges:
        widened.add(low, high)
        shifted = (_case_shift(low, 32), _case_shift(high, 32))
        if shifted[0] is not None and shifted[1] is not None:
            widened.add(shifted[0], shifted[1])
        if high - low <= _FOLD_SCAN_LIMIT:
            for point in range(low, high + 1):
                for variant in _case_variants(point):
                    widened.add(variant, variant)
    return widened.normalized()


class RangeSet:
    """An accumulator for character ranges that keeps them sorted and merged.

    Ranges are inclusive code-point pairs. Adding overlapping or adjacent
    ranges coalesces them, so callers can add freely without sorting later.
    """

    __slots__ = ("_ranges",)

    def __init__(self, ranges: tuple[tuple[int, int], ...] = ()) -> None:
        """Create an accumulator seeded with the given ranges.

        Args:
            ranges (tuple): Initial inclusive code-point ranges.
        """
        self._ranges = [tuple(pair) for pair in ranges]

    def add(self, low: int, high: int) -> None:
        """Add an inclusive range to the set.

        Args:
            low (int): The first code point in the range.
            high (int): The last code point in the range.
        """
        if low > high:
            low, high = high, low
        self._ranges.append((low, high))

    def add_char(self, char: str) -> None:
        """Add a single character to the set.

        Args:
            char (str): The character to add.
        """
        point = ord(char)
        self._ranges.append((point, point))

    def extend(self, ranges: tuple[tuple[int, int], ...]) -> None:
        """Add every range from another collection.

        Args:
            ranges (tuple): Inclusive code-point ranges to merge in.
        """
        for low, high in ranges:
            self.add(low, high)

    def add_ignorecase(self) -> None:
        """Add the IGNORECASE equivalent of every code point in the set."""
        for low, high in _expand_ignorecase(self.normalized()):
            self._ranges.append((low, high))

    def negate_as_range(self) -> tuple[tuple[int, int], ...]:
        """Return the complement of this set across the whole code-point space.

        Returns:
            tuple: Inclusive ranges covering everything not in the set.
        """
        merged = self.normalized()
        result: list[tuple[int, int]] = []
        cursor = 0
        for low, high in merged:
            if low > cursor:
                result.append((cursor, low - 1))
            cursor = max(cursor, high + 1)
        if cursor <= 0x10FFFF:
            result.append((cursor, 0x10FFFF))
        return tuple(result)

    def normalized(self) -> tuple[tuple[int, int], ...]:
        """Return the ranges sorted and merged.

        Returns:
            tuple: Inclusive ranges with no overlaps or adjacency.
        """
        if not self._ranges:
            return ()
        ordered = sorted(self._ranges)
        merged: list[tuple[int, int]] = [ordered[0]]
        for low, high in ordered[1:]:
            last_low, last_high = merged[-1]
            if low <= last_high + 1:
                if high > last_high:
                    merged[-1] = (last_low, high)
            else:
                merged.append((low, high))
        return tuple(merged)

    def is_empty(self) -> bool:
        """Return whether the set contains no ranges."""
        return not self._ranges

    def __len__(self) -> int:
        """Return the number of ranges held before normalisation."""
        return len(self._ranges)


def _in_ranges(ranges: tuple[tuple[int, int], ...], char: str) -> bool:
    """Return whether a code point falls inside a sorted range list."""
    point = ord(char)
    low_index = 0
    high_index = len(ranges) - 1
    while low_index <= high_index:
        middle = (low_index + high_index) // 2
        low, high = ranges[middle]
        if point < low:
            high_index = middle - 1
        elif point > high:
            low_index = middle + 1
        else:
            return True
    return False


class _Parser:
    """Recursive-descent parser producing an abstract syntax tree.

    Args:
        pattern (str): The pattern to parse.
        flags (int): The initial flag set, which inline groups may modify.
    """

    __slots__ = ("pattern", "flags", "pos", "ngroups", "groupnames", "scoped_depth")

    def __init__(self, pattern: str, flags: int = 0) -> None:
        """Create a parser positioned at the start of a pattern.

        Args:
            pattern (str): The pattern source.
            flags (int): The initial flag set.
        """
        self.pattern = pattern
        self.flags = flags
        self.pos = 0
        self.ngroups = 0
        self.groupnames: dict[str, int] = {}
        self.scoped_depth = 0

    def error(self, msg: str, pos: int | None = None) -> RegexError:
        """Build a RegexError anchored at the given offset.

        Args:
            msg (str): The failure message.
            pos (int, optional): The offset, defaulting to the current one.

        Returns:
            RegexError: The error to raise.
        """
        return RegexError(msg, self.pattern, self.pos if pos is None else pos)

    def parse(self) -> Node:
        """Parse the whole pattern.

        Returns:
            Node: The root of the syntax tree.
        """
        node = self._parse_alternation()
        if self.pos < len(self.pattern):
            raise self.error("unbalanced )")
        return node

    def _at_end(self) -> bool:
        """Return whether the parser has consumed the whole pattern."""
        return self.pos >= len(self.pattern)

    def _peek(self, offset: int = 0) -> str:
        """Return the character at an offset, or "" past the end."""
        index = self.pos + offset
        if index < len(self.pattern):
            return self.pattern[index]
        return ""

    def _skip_verbose(self) -> None:
        """Skip whitespace and comments when VERBOSE is active."""
        if not self.flags & VERBOSE:
            return
        while self.pos < len(self.pattern):
            char = self.pattern[self.pos]
            if char in " \t\n\r\f\v":
                self.pos += 1
            elif char == "#":
                while self.pos < len(self.pattern) and self.pattern[self.pos] != "\n":
                    self.pos += 1
            else:
                return

    def _parse_alternation(self) -> Node:
        """Parse a sequence of ``|``-separated branches."""
        branches = [self._parse_concatenation()]
        while not self._at_end() and self._peek() == "|":
            self.pos += 1
            branches.append(self._parse_concatenation())
        if len(branches) == 1:
            return branches[0]
        return Alternate(tuple(branches))

    def _parse_concatenation(self) -> Node:
        """Parse a sequence of atoms until ``|``, ``)``, or end of pattern."""
        items: list[Node] = []
        while True:
            self._skip_verbose()
            if self._at_end() or self._peek() in "|)":
                break
            atom = self._parse_quantified()
            if atom is not None:
                items.append(atom)
        if not items:
            return Empty()
        if len(items) == 1:
            return items[0]
        return Concat(tuple(items))

    def _parse_quantified(self) -> Node | None:
        """Parse an atom followed by any quantifiers applied to it."""
        atom = self._parse_atom()
        if atom is None:
            return None
        while True:
            self._skip_verbose()
            char = self._peek()
            minimum: int
            maximum: int | None
            if char == "*":
                self.pos += 1
                minimum, maximum = 0, None
            elif char == "+":
                self.pos += 1
                minimum, maximum = 1, None
            elif char == "?":
                self.pos += 1
                minimum, maximum = 0, 1
            elif char == "{" and self._is_repeat_brace():
                minimum, maximum = self._parse_braced_repeat(atom)
            else:
                break
            greedy = True
            if self._peek() == "?":
                self.pos += 1
                greedy = False
            elif self._peek() == "+":
                raise self.error("possessive quantifiers are not supported")
            if isinstance(atom, Anchor):
                raise self.error("nothing to repeat")
            if maximum is not None and maximum < minimum:
                raise self.error("min repeat greater than max repeat")
            atom = Repeat(atom, minimum, maximum, greedy)
            following = self._peek()
            if following and (
                following in "*+?" or (following == "{" and self._is_repeat_brace())
            ):
                raise self.error("multiple repeat", self.pos)
        return atom

    def _parse_braced_repeat(self, atom: Node) -> tuple[int, int | None]:
        """Parse a ``{n}``, ``{n,}``, or ``{n,m}`` quantifier.

        Args:
            atom (Node): The repeated subexpression, checked for zero-width
                bodies.

        Returns:
            tuple: The minimum and maximum repetition counts.

        Raises:
            RegexError: If the braces are unterminated or inverted.
        """
        if isinstance(atom, Anchor):
            raise self.error("nothing to repeat")
        start = self.pos
        self.pos += 1
        low_digits = ""
        while not self._at_end() and self._peek().isdigit():
            low_digits += self._peek()
            self.pos += 1
        minimum = int(low_digits)
        maximum: int | None = minimum
        if self._peek() == ",":
            self.pos += 1
            high_digits = ""
            while not self._at_end() and self._peek().isdigit():
                high_digits += self._peek()
                self.pos += 1
            maximum = int(high_digits) if high_digits else None
        if self._peek() != "}":
            raise self.error("unterminated quantifier", start)
        self.pos += 1
        return minimum, maximum

    def _is_repeat_brace(self) -> bool:
        """Return whether ``{`` at the cursor opens a quantifier."""
        index = self.pos + 1
        if index < len(self.pattern) and self.pattern[index] == ",":
            index += 1
        digits = 0
        while index < len(self.pattern) and self.pattern[index].isdigit():
            index += 1
            digits += 1
        if digits == 0:
            return False
        if index < len(self.pattern) and self.pattern[index] == ",":
            index += 1
            while index < len(self.pattern) and self.pattern[index].isdigit():
                index += 1
        if index >= len(self.pattern) or self.pattern[index] != "}":
            return False
        return True

    def _parse_atom(self) -> Node | None:
        """Parse a single atom, or return None for an ignorable position."""
        char = self._peek()
        if char == "(":
            return self._parse_group()
        if char == "[":
            return self._parse_class()
        if char == ".":
            self.pos += 1
            return AnyChar(bool(self.flags & DOTALL))
        if char == "^":
            self.pos += 1
            return Anchor("start")
        if char == "$":
            self.pos += 1
            return Anchor("end")
        if char == "\\":
            return self._parse_escape_atom()
        if char in "*+?":
            raise self.error("nothing to repeat")
        self.pos += 1
        return Literal(char)

    def _parse_escape_atom(self) -> Node:
        """Parse a backslash escape appearing outside a character class."""
        start = self.pos
        self.pos += 1
        if self._at_end():
            raise self.error("bad escape (end of pattern)", start)
        char = self._peek()
        if char in "bBAZ":
            self.pos += 1
            if char == "b":
                return Anchor("word")
            if char == "B":
                return Anchor("not_word")
            if char == "A":
                return Anchor("text_start")
            return Anchor("text_end")
        if char in CLASS_ESCAPE_KINDS:
            self.pos += 1
            return CharClass((self._class_from_escape(char),))
        if char in "01234567" and self._octal_run(start) is not None:
            return Literal(self._parse_octal_escape(start))
        if char.isdigit() and char != "0":
            raise self.error("backreferences are not supported", start)
        if char == "p" or char == "P":
            raise self.error("unicode property escapes are not supported", start)
        if char in "g" and self._peek(1) in "<0123456789":
            raise self.error("backreferences are not supported", start)
        return Literal(self._parse_literal_escape(start))

    def _octal_run(self, start: int) -> str | None:
        """Return the octal digits of a digit escape, or None if it is a group ref.

        ``re`` only reads a digit escape as octal when the run is exactly three
        digits long, or when it begins with ``0``. Shorter runs such as ``\\1``
        are group references instead.

        Args:
            start (int): The offset of the backslash.

        Returns:
            str | None: The consumed octal digits, or None for a group reference.
        """
        digits = ""
        index = start + 1
        while index < len(self.pattern) and self.pattern[index] in "01234567" and len(digits) < 3:
            digits += self.pattern[index]
            index += 1
        if len(digits) == 3 or digits.startswith("0"):
            return digits or None
        return None

    def _parse_octal_escape(self, start: int) -> str:
        """Parse an octal digit escape into the character it denotes.

        Args:
            start (int): The offset of the backslash, used for errors.

        Returns:
            str: The single character the escape denotes.
        """
        digits = self._octal_run(start)
        self.pos = start + 1 + len(digits)
        return chr(int(digits, 8))

    def _parse_literal_escape(self, start: int) -> str:
        """Parse an escape that denotes a single literal character.

        Args:
            start (int): The offset of the backslash, used for errors.

        Returns:
            str: The character the escape denotes.
        """
        char = self._peek()
        if char == "x":
            return self._parse_hex_escape(start, 2)
        if char == "u":
            return self._parse_hex_escape(start, 4)
        if char == "U":
            return self._parse_hex_escape(start, 8)
        if char in SIMPLE_ESCAPES:
            self.pos += 1
            return SIMPLE_ESCAPES[char]
        if char.isdigit():
            digits = ""
            while not self._at_end() and len(digits) < 3 and self._peek() in "01234567":
                digits += self._peek()
                self.pos += 1
            point = int(digits, 8)
            if point > 0x10FFFF:
                raise self.error("octal escape value out of range", start)
            return chr(point)
        self.pos += 1
        return char

    def _parse_hex_escape(self, start: int, width: int) -> str:
        """Parse a ``\\xNN``-style escape of a fixed digit width.

        Args:
            start (int): The offset of the backslash.
            width (int): The number of hexadecimal digits expected.

        Returns:
            str: The character the escape denotes.
        """
        self.pos += 1
        digits = self.pattern[self.pos:self.pos + width]
        if len(digits) != width or any(d not in "0123456789abcdefABCDEF" for d in digits):
            raise self.error("incomplete escape", start)
        self.pos += width
        point = int(digits, 16)
        if point > 0x10FFFF:
            raise self.error("escaped character is out of range", start)
        return chr(point)

    def _parse_group(self) -> Node:
        """Parse a parenthesised group and any inline flag modifiers."""
        self.pos += 1
        capturing = True
        index: int | None = None
        name: str | None = None
        saved_flags = self.flags
        scoped = False
        if self._peek() == "?":
            self.pos += 1
            kind = self._peek()
            if kind == ":":
                self.pos += 1
                capturing = False
            elif kind == "P":
                self.pos += 1
                if self._peek() == "<":
                    self.pos += 1
                    name = self._read_group_name()
                elif self._peek() == "=":
                    raise self.error("backreferences are not supported")
                else:
                    raise self.error("unknown extension")
            elif kind == "=" or kind == "!":
                raise self.error("lookahead is not supported")
            elif kind == "<":
                self.pos += 1
                follower = self._peek()
                if follower == "=" or follower == "!":
                    raise self.error("lookbehind is not supported")
                raise self.error("unknown extension")
            elif kind == ">":
                raise self.error("atomic groups are not supported")
            elif kind == "#":
                self.pos += 1
                close = self.pattern.find(")", self.pos)
                if close < 0:
                    raise self.error("missing ), unterminated comment")
                self.pos = close + 1
                return Empty()
            elif kind in FLAG_LETTERS or kind == "-":
                self._parse_inline_flags()
                scoped = True
                capturing = False
                if self._peek() == ")":
                    self.pos += 1
                    if scoped:
                        self.flags = saved_flags
                    return Empty()
            else:
                raise self.error("unknown extension")
        if capturing:
            self.ngroups += 1
            index = self.ngroups
            if name is not None:
                if name in self.groupnames:
                    raise self.error(f"redefinition of group name {name!r}")
                self.groupnames[name] = index
        inner = self._parse_alternation()
        if self._peek() != ")":
            raise self.error("missing ), unterminated subpattern")
        self.pos += 1
        if scoped:
            self.flags = saved_flags
        return Group(inner, index)

    def _read_group_name(self) -> str:
        """Read a group name up to the closing ``>``.

        Returns:
            str: The group name.
        """
        close = self.pattern.find(">", self.pos)
        if close < 0:
            raise self.error("missing >, unterminated name")
        if close == self.pos:
            raise self.error("missing group name")
        name = self.pattern[self.pos:close]
        self.pos = close + 1
        return name

    def _parse_inline_flags(self) -> None:
        """Parse a ``(?flags)`` or ``(?flags:...)`` modifier."""
        start = self.pos
        self.pos += 1
        enabling = True
        if self._peek() == "-":
            enabling = False
            self.pos += 1
        new_flags = 0
        while not self._at_end() and self._peek() in FLAG_LETTERS:
            new_flags |= FLAG_LETTERS[self._peek()]
            self.pos += 1
        if not self._at_end() and self._peek() == ")":
            self.pos += 1
            if enabling:
                self.flags |= new_flags
            else:
                self.flags &= ~new_flags
            return
        if self._peek() != ":":
            raise self.error("missing ), unterminated subpattern", start)
        self.pos += 1
        if enabling:
            self.flags |= new_flags
        else:
            self.flags &= ~new_flags

    def _parse_class(self) -> CharClass:
        """Parse a bracketed character class, including POSIX names."""
        self.pos += 1
        negated = False
        if self._peek() == "^":
            self.pos += 1
            negated = True
        atoms: list[CharAtom] = []
        first = True
        while True:
            if self._at_end():
                raise self.error("unterminated character set")
            char = self._peek()
            if char == "]" and not first:
                self.pos += 1
                break
            first = False
            start = self.pos
            if char == "[" and self._peek(1) == ":":
                atoms.append(self._parse_posix_class())
                continue
            if char == "\\":
                low, low_atom = self._parse_class_escape()
            else:
                low = ord(self._read_class_char())
                low_atom = None
            if low_atom is not None:
                if self._peek() == "-" and self._peek(1) not in ("]", ""):
                    raise self.error("bad character range", start)
                atoms.append(low_atom)
                continue
            ranges = RangeSet()
            if self._peek() == "-" and self._peek(1) not in ("]", ""):
                self.pos += 1
                high, high_atom = self._parse_class_escape() if self._peek() == "\\" else (
                    ord(self._read_class_char()),
                    None,
                )
                if high_atom is not None or high < low:
                    raise self.error("bad character range", start)
                ranges.add(low, high)
            else:
                ranges.add(low, low)
            atoms.append(self._finish_atom(ranges))
        return CharClass(tuple(atoms), negated)

    def _finish_atom(self, ranges: RangeSet) -> CharAtom:
        """Normalise a range accumulator into a class term, folding case if asked.

        Args:
            ranges (RangeSet): The accumulated ranges for one term.

        Returns:
            CharAtom: The finished, case-folded term.
        """
        if self.flags & IGNORECASE:
            ranges.add_ignorecase()
        return CharAtom(ranges.normalized())

    def _read_class_char(self) -> str:
        """Read a single literal character inside a character class.

        Returns:
            str: The character read.
        """
        char = self._peek()
        self.pos += 1
        return char

    def _parse_posix_class(self) -> CharAtom:
        """Parse a ``[:name:]`` POSIX class into its own term."""
        close = self.pattern.find(":]", self.pos)
        if close < 0:
            raise self.error("unterminated POSIX class")
        name = self.pattern[self.pos + 2:close]
        negated = name.startswith("^")
        if negated:
            name = name[1:]
        if name not in POSIX_RANGES:
            raise self.error(f"unknown POSIX class {name!r}")
        self.pos = close + 2
        ascii_names = ("alpha", "digit", "alnum", "upper", "lower", "xdigit")
        if bool(self.flags & ASCII) or name in ascii_names:
            ranges = RangeSet(POSIX_RANGES[name])
            return CharAtom(self._fold(ranges), (), negated)
        return CharAtom((), (POSIX_PREDICATES[name],), negated)

    def _fold(self, ranges: RangeSet) -> tuple[tuple[int, int], ...]:
        """Add case-swapped variants when IGNORECASE is active and normalise.

        Args:
            ranges (RangeSet): The ranges to fold.

        Returns:
            tuple: The normalised ranges.
        """
        if self.flags & IGNORECASE:
            ranges.add_ignorecase()
        return ranges.normalized()

    def _parse_class_escape(self) -> tuple[int | None, CharAtom | None]:
        """Parse a backslash escape appearing inside a character class.

        Args:
            None: No arguments beyond ``self``.

        Returns:
            tuple: The code point the escape denotes and ``None`` for a class
            term, or ``None`` and the term for a ``\\d``-style escape.
        """
        start = self.pos
        self.pos += 1
        if self._at_end():
            raise self.error("bad escape (end of pattern)", start)
        char = self._peek()
        if char == "b":
            self.pos += 1
            return 8, None
        if char in CLASS_ESCAPE_KINDS:
            self.pos += 1
            return None, self._class_from_escape(char)
        if char in "01234567" and self._octal_run(start) is not None:
            return ord(self._parse_octal_escape(start)), None
        if char.isdigit() and char != "0":
            raise self.error("backreferences are not supported", start)
        return ord(self._parse_literal_escape(start)), None

    def _class_from_escape(self, kind: str) -> CharAtom:
        """Build the character class denoted by a ``\\d``-style escape.

        Args:
            kind (str): One of ``d D w W s S``.

        Returns:
            CharAtom: The matching class term.
        """
        base = kind.lower()
        negated = kind.isupper()
        ascii_only = bool(self.flags & ASCII)
        if base == "d":
            ranges = RangeSet(DIGIT_RANGES)
            predicates: tuple = () if ascii_only else (str.isdecimal,)
        elif base == "w":
            ranges = RangeSet(WORD_RANGES)
            predicates = () if ascii_only else (lambda ch: ch.isalnum() or ch == "_",)
        else:
            ranges = RangeSet(ASCII_SPACE_RANGES)
            predicates = () if ascii_only else (str.isspace,)
        return CharAtom(self._fold(ranges), predicates, negated)


def _parse(pattern: str, flags: int = 0) -> tuple[Node, int, dict[str, int]]:
    """Parse a pattern into a syntax tree.

    Args:
        pattern (str): The pattern source.
        flags (int): The flag set.

    Returns:
        tuple: The root node, the capture-group count, and the group name map.

    Raises:
        RegexError: If the pattern is malformed.

    Example:
        >>> _parse("a|b", 0)[1]
        0
    """
    if not isinstance(pattern, str):
        raise RegexError("pattern must be a string", repr(pattern), 0)
    parser = _Parser(pattern, flags)
    node = parser.parse()
    return node, parser.ngroups, parser.groupnames


def escape(text: str) -> str:
    """Escape a literal string so it matches itself in a pattern.

    Matches the reference implementation, which leaves characters that carry no
    special meaning alone and backslash-escapes the rest, so ``"a-b"`` becomes
    ``"a\\-b"`` while ``"aé"`` is unchanged.

    Args:
        text (str): The literal text to escape.

    Returns:
        str: The escaped pattern source.

    Example:
        >>> escape("a.b*c")
        'a\\\\.b\\\\*c'
    """
    if not isinstance(text, str):
        raise TypeError(f"expected string, got {type(text).__name__}")
    out: list[str] = []
    for char in text:
        if char in ESCAPE_CHARS:
            out.append("\\")
            out.append(char)
        else:
            out.append(char)
    return "".join(out)


def compile_pattern(pattern: str, flags: int = 0) -> tuple[Node, int, dict[str, int], int]:
    """Parse a pattern and report the flags in force at its end.

    Args:
        pattern (str): The pattern source.
        flags (int): The initial flag set.

    Returns:
        tuple: The root node, capture count, group names, and effective flags.
    """
    parser = _Parser(pattern, flags)
    node = parser.parse()
    return node, parser.ngroups, parser.groupnames, parser.flags