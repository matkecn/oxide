"""NFA compiler and Pike VM for the ``oxide.regex`` engine.

The engine compiles a pattern's syntax tree into a Thompson NFA program and
executes it with a Pike-style virtual machine that advances a *set* of live
states in lockstep across the input.

Because every state is visited at most once per input position, matching costs
``O(len(text) * len(program))`` in the worst case for any pattern whatsoever.
There is no backtracking and therefore no catastrophic-backtracking failure
mode; a pattern such as ``(a+)+b`` against a long run of ``a`` terminates in
linear time instead of hanging.

Alternation follows leftmost-first (Perl-style) priority, which is what Python's
``re`` and Rust's ``regex`` both specify, rather than POSIX leftmost-longest.
Captures are threaded through the state set, so greedy and lazy quantifiers
interact with each other exactly as they do in ``re``.
"""

from __future__ import annotations

from ._syntax import (
    Alternate, Anchor, AnyChar, CharAtom, CharClass, Concat, Empty, Group, IGNORECASE,
    Literal, MULTILINE, Node, RangeSet, RegexError, Repeat,
)

CHAR = 0
CLASS = 1
SPLIT = 2
JMP = 3
SAVE = 4
MATCH = 5
ASSERT = 6

MAX_CODEPOINT = 0x10FFFF

HOLE_X = 1
HOLE_Y = 2
HOLE_TARGET = 1


class Program:
    """A compiled regular expression ready for execution.

    Holds the instruction list, the pool of character classes it references, and
    the capture-group metadata reported by :class:`~oxide.regex.api.Match`.
    """

    __slots__ = ("ops", "classes", "ngroups", "groupnames", "flags", "pattern")

    def __init__(
        self,
        ops: list[list],
        classes: list[CharClass],
        ngroups: int,
        groupnames: dict[str, int],
        flags: int,
        pattern: str,
    ) -> None:
        """Create a compiled program.

        Args:
            ops (list): The instruction list.
            classes (list): The pool of character classes.
            ngroups (int): The number of capturing groups.
            groupnames (dict): A mapping of group name to capture index.
            flags (int): The effective flag set.
            pattern (str): The source pattern.
        """
        self.ops = ops
        self.classes = classes
        self.ngroups = ngroups
        self.groupnames = groupnames
        self.flags = flags
        self.pattern = pattern

    def slot_count(self) -> int:
        """Return the number of capture slots, including the whole match."""
        return 2 * (self.ngroups + 1)

    def __repr__(self) -> str:
        return (
            f"Program({self.pattern!r}, groups={self.ngroups}, "
            f"instructions={len(self.ops)})"
        )


class Compiler:
    """Translates a syntax tree into a Thompson NFA instruction list.

    Args:
        pattern (str): The source pattern, retained for diagnostics.
        ngroups (int): The number of capturing groups.
        groupnames (dict): A mapping of group name to capture index.
        flags (int): The effective flag set.
    """

    __slots__ = ("pattern", "ngroups", "groupnames", "flags", "ops", "classes", "_index")

    def __init__(
        self,
        pattern: str,
        ngroups: int,
        groupnames: dict[str, int],
        flags: int,
    ) -> None:
        """Create a compiler for a parsed pattern.

        Args:
            pattern (str): The source pattern.
            ngroups (int): The number of capturing groups.
            groupnames (dict): A mapping of group name to capture index.
            flags (int): The effective flag set.
        """
        self.pattern = pattern
        self.ngroups = ngroups
        self.groupnames = groupnames
        self.flags = flags
        self.ops: list[list] = []
        self.classes: list[CharClass] = []
        self._index: dict[tuple, int] = {}

    def _emit(self, op: list) -> int:
        """Append an instruction and return its index.

        Args:
            op (list): The instruction to append.

        Returns:
            int: The instruction's index.
        """
        self.ops.append(op)
        return len(self.ops) - 1

    def _add_class(self, node: CharClass) -> int:
        """Intern a character class and return its pool index.

        Args:
            node (CharClass): The class to intern.

        Returns:
            int: The index of the class in the pool.
        """
        key = tuple(
            (atom.ranges, atom.predicates, atom.negated) for atom in node.atoms
        ) + (node.negated,)
        cached = self._index.get(key)
        if cached is not None:
            return cached
        index = len(self.classes)
        self.classes.append(node)
        self._index[key] = index
        return index

    def _here(self) -> int:
        """Return the index the next emitted instruction will occupy."""
        return len(self.ops)

    def _patch(self, holes: list[tuple[int, int]]) -> None:
        """Point every hole at the next instruction to be emitted.

        Args:
            holes (list): Pairs of instruction index and the slot to fill.
        """
        target = self._here()
        for pc, slot in holes:
            self.ops[pc][slot] = target

    def compile(self, node: Node) -> list[tuple[int, int]]:
        """Compile a node, returning holes to patch to the continuation.

        Args:
            node (Node): The syntax tree node to compile.

        Returns:
            list: Pairs of instruction index and slot index, to be patched once
            the continuation's address is known.
        """
        if isinstance(node, Empty):
            return []
        if isinstance(node, Literal):
            if self.flags & IGNORECASE:
                ranges = RangeSet()
                ranges.add_char(node.char)
                ranges.add_ignorecase()
                self._emit([CLASS, self._add_class(CharClass((CharAtom(ranges.normalized()),)))])
            else:
                self._emit([CHAR, ord(node.char)])
            return []
        if isinstance(node, CharClass):
            self._emit([CLASS, self._add_class(node)])
            return []
        if isinstance(node, AnyChar):
            if node.dotall:
                ranges: tuple[tuple[int, int], ...] = ((0, MAX_CODEPOINT),)
            else:
                ranges = ((0, 9), (11, MAX_CODEPOINT))
            self._emit([CLASS, self._add_class(CharClass((CharAtom(ranges),)))])
            return []
        if isinstance(node, Anchor):
            self._emit([ASSERT, node.kind])
            return []
        if isinstance(node, Group):
            if node.index is None:
                return self.compile(node.node)
            self._emit([SAVE, 2 * node.index])
            inner = self.compile(node.node)
            self._patch(inner)
            self._emit([SAVE, 2 * node.index + 1])
            return []
        if isinstance(node, Concat):
            holes = []
            for item in node.items:
                self._patch(holes)
                holes = self.compile(item)
            return holes
        if isinstance(node, Alternate):
            return self._compile_alternate(node)
        if isinstance(node, Repeat):
            return self._compile_repeat(node)
        raise RegexError(f"unsupported node {type(node).__name__}", self.pattern, 0)

    def _compile_alternate(self, node: Alternate) -> list[tuple[int, int]]:
        """Compile an alternation into a chain of two-way splits.

        Args:
            node (Alternate): The alternation node.

        Returns:
            list: Holes to patch to the continuation.
        """
        count = len(node.branches)
        if count == 1:
            return self.compile(node.branches[0])
        splits = [self._emit([SPLIT, None, None]) for _ in range(count - 1)]
        for index in range(count - 2):
            self.ops[splits[index]][HOLE_Y] = splits[index + 1]
        jmps: list[int] = []
        holes: list[tuple[int, int]] = []
        for index, branch in enumerate(node.branches):
            if index < count - 1:
                self.ops[splits[index]][HOLE_X] = self._here()
            else:
                self.ops[splits[index - 1]][HOLE_Y] = self._here()
            branch_holes = self.compile(branch)
            if index < count - 1:
                self._patch(branch_holes)
                jmps.append(self._emit([JMP, None]))
            else:
                holes = branch_holes
        target = self._here()
        for pc in jmps:
            self.ops[pc][HOLE_TARGET] = target
        return holes

    def _compile_repeat(self, node: Repeat) -> list[tuple[int, int]]:
        """Compile a repetition node.

        Args:
            node (Repeat): The repetition node.

        Returns:
            list: Holes to patch to the continuation.
        """
        if node.max == 0:
            return []
        for _ in range(node.min):
            self._patch(self.compile(node.node))
        if node.max is None:
            split = self._emit([SPLIT, None, None])
            self.ops[split][HOLE_X if node.greedy else HOLE_Y] = self._here()
            self._patch(self.compile(node.node))
            self._emit([JMP, split])
            return [(split, HOLE_Y if node.greedy else HOLE_X)]
        optionals = node.max - node.min
        if optionals <= 0:
            return []
        splits: list[int] = []
        for _ in range(optionals):
            split = self._emit([SPLIT, None, None])
            self.ops[split][HOLE_X if node.greedy else HOLE_Y] = self._here()
            splits.append(split)
            self._patch(self.compile(node.node))
        return [(pc, HOLE_Y if node.greedy else HOLE_X) for pc in splits]


def compile_pattern(
    node: Node, ngroups: int, groupnames: dict[str, int], flags: int, pattern: str
) -> Program:
    """Compile a syntax tree into an executable program.

    Args:
        node (Node): The root of the syntax tree.
        ngroups (int): The number of capturing groups.
        groupnames (dict): A mapping of group name to capture index.
        flags (int): The effective flag set.
        pattern (str): The source pattern.

    Returns:
        Program: The compiled program.
    """
    compiler = Compiler(pattern, ngroups, groupnames, flags)
    compiler._emit([SAVE, 0])
    holes = compiler.compile(node)
    compiler._patch(holes)
    compiler._emit([SAVE, 1])
    compiler._emit([MATCH])
    return Program(
        compiler.ops, compiler.classes, ngroups, groupnames, flags, pattern
    )


def _is_word_char(char: str) -> bool:
    """Return whether a character is alphanumeric or an underscore."""
    return char.isalnum() or char == "_"


class PikeVM:
    """Executes a compiled :class:`Program` with NFA state-set simulation.

    The machine keeps a priority-ordered list of live states. Epsilon
    transitions (splits, jumps, capture saves, and zero-width assertions) are
    resolved eagerly by :meth:`_add`, and character transitions are resolved one
    input position at a time.
    """

    __slots__ = ("program", "ops", "classes", "ngroups", "multiline")

    def __init__(self, program: Program) -> None:
        """Create a virtual machine for a compiled program.

        Args:
            program (Program): The program to execute.
        """
        self.program = program
        self.ops = program.ops
        self.classes = program.classes
        self.ngroups = program.ngroups
        self.multiline = bool(program.flags & MULTILINE)

    def _assert_ok(
        self, kind: str, text: str, pos: int, start: int, end: int, origin: int
    ) -> bool:
        """Evaluate a zero-width assertion at a position.

        ``origin`` is the offset of the real string start and is always zero;
        ``start`` is the offset the caller is searching from. ``^`` and ``\\b``
        are always measured against the real string, so ``search(string, pos)``
        does not create a sliced context for them, while ``$`` respects
        ``endpos``.

        Args:
            kind (str): The assertion kind.
            text (str): The subject text.
            pos (int): The position to evaluate at.
            start (int): The effective start of the search region.
            end (int): The effective end of the subject.
            origin (int): The offset of the real string start.

        Returns:
            bool: True when the assertion holds.
        """
        if kind == "text_start":
            return pos == origin
        if kind == "text_end":
            return pos == end
        if kind == "start":
            if pos == origin:
                return True
            return self.multiline and pos > origin and text[pos - 1] == "\n"
        if kind == "end":
            if pos == end:
                return True
            if pos == end - 1 and text[pos] == "\n" and end == len(text):
                return True
            return self.multiline and text[pos] == "\n"
        before = pos > origin and _is_word_char(text[pos - 1])
        after = pos < end and _is_word_char(text[pos])
        if kind == "word":
            return before != after
        return before == after

    def _add(
        self,
        target: list[tuple[int, tuple]],
        seen: set[int],
        pc: int,
        caps: tuple,
        text: str,
        pos: int,
        start: int,
        end: int,
    ) -> None:
        """Add a state and its epsilon closure, preserving priority order.

        Args:
            target (list): The priority-ordered state list to extend.
            seen (set): Instruction indices already present in this state set.
            pc (int): The instruction index to add.
            caps (tuple): The state at this point.
            text (str): The subject text.
            pos (int): The current input position.
            start (int): The effective start of the subject.
            end (int): The effective end of the subject.
        """
        ops = self.ops
        stack: list[tuple[int, tuple]] = [(pc, caps)]
        origin = 0
        while stack:
            pc, caps = stack.pop()
            if pc in seen:
                continue
            seen.add(pc)
            op = ops[pc]
            kind = op[0]
            if kind == JMP:
                stack.append((op[HOLE_TARGET], caps))
            elif kind == SPLIT:
                stack.append((op[HOLE_Y], caps))
                stack.append((op[HOLE_X], caps))
            elif kind == SAVE:
                updated = list(caps)
                updated[op[1]] = pos
                stack.append((pc + 1, tuple(updated)))
            elif kind == ASSERT:
                if self._assert_ok(op[1], text, pos, start, end, origin):
                    stack.append((pc + 1, caps))
            else:
                target.append((pc, caps))

    @staticmethod
    def _terminal_usable(
        caps: tuple, end: int, anchor_end: bool, progress: bool
    ) -> bool:
        """Return whether a terminal state yields an acceptable match.

        Args:
            caps (tuple): The capture slots at the terminal state.
            end (int): The effective end of the subject.
            anchor_end (bool): When True, require the match to reach ``end``.
            progress (bool): When True, reject zero-length matches.

        Returns:
            bool: True when the terminal state may be reported.
        """
        if anchor_end and caps[1] != end:
            return False
        if progress and caps[0] == caps[1]:
            return False
        return True

    def _run_from(
        self,
        text: str,
        start: int,
        end: int,
        anchor_end: bool,
        progress: bool = False,
    ) -> tuple | None:
        """Attempt a match anchored at a single start position.

        The state list is kept in priority order and the best terminal state is
        carried forward instead of being collapsed into a single fallback.
        Collapsing loses priority, which is what a regular expression engine
        actually resolves on: a greedy ``a*`` re-derives its terminal as the
        input grows and the fresh state outranks the carried one, while a lazy
        ``\\s*?`` that already reached a terminal keeps it even though longer
        matches exist further along.

        Carrying is skipped for terminals that are no longer acceptable, such
        as one that stopped short of ``end`` under ``fullmatch``. Dropping them
        lets a higher-priority thread re-derive a usable terminal later, and
        keeps the carried state list bounded to a single entry.

        Args:
            text (str): The subject text.
            start (int): The position to anchor at.
            end (int): The effective end of the subject.
            anchor_end (bool): When True, require the match to reach ``end``.
            progress (bool): When True, reject zero-length matches so a caller
                can retry a position looking for a match that consumed input.

        Returns:
            tuple | None: The capture slot tuple on success, else None.
        """
        ops = self.ops
        classes = self.classes
        slots = 2 * (self.ngroups + 1)
        clist: list[tuple[int, tuple]] = []
        seen: set[int] = set()
        self._add(clist, seen, 0, (None,) * slots, text, start, start, end)
        pos = start
        while True:
            carried: tuple | None = None
            carried_pc = -1
            carried_rank = -1
            for rank, (pc, caps) in enumerate(clist):
                if ops[pc][0] == MATCH and self._terminal_usable(
                    caps, end, anchor_end, progress
                ):
                    carried = caps
                    carried_pc = pc
                    carried_rank = rank
                    break
            if carried is not None and carried_rank == 0:
                return carried
            if pos >= end:
                return carried
            char = text[pos]
            code = ord(char)
            nlist: list[tuple[int, tuple]] = []
            nseen: set[int] = set()
            following = pos + 1
            slot = 0
            for rank, (pc, caps) in enumerate(clist):
                if rank == carried_rank:
                    slot = len(nlist)
                op = ops[pc]
                kind = op[0]
                if kind == CHAR:
                    if op[1] == code:
                        self._add(
                            nlist, nseen, pc + 1, caps, text, following, start, end
                        )
                elif kind == CLASS:
                    if classes[op[1]].matches(char):
                        self._add(
                            nlist, nseen, pc + 1, caps, text, following, start, end
                        )
            if carried is not None:
                head = nlist[:slot]
                tail = [entry for entry in nlist[slot:] if ops[entry[0]][0] != MATCH]
                nlist = head + [(carried_pc, carried)] + tail
            if not nlist:
                return carried
            clist = nlist
            pos = following

    def search(
        self,
        text: str,
        start: int,
        end: int,
        anchored: bool,
        anchored_end: bool,
        progress: bool = False,
    ) -> tuple | None:
        """Run the machine over a subject, optionally anchoring both ends.

        Args:
            text (str): The subject text.
            start (int): The offset to begin matching at.
            end (int): The effective end of the subject.
            anchored (bool): When True, only match at ``start``.
            anchored_end (bool): When True, require the match to reach ``end``.
            progress (bool): When True, reject zero-length matches.

        Returns:
            tuple | None: The capture slot tuple on success, else None.
        """
        if start > end:
            return None
        first = self._run_from(text, start, end, anchored_end, progress)
        if first is not None or anchored:
            return first
        for pos in range(start + 1, end + 1):
            found = self._run_from(text, pos, end, anchored_end, progress)
            if found is not None:
                return found
        return None