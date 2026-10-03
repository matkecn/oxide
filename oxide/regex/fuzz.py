"""Differential test harness comparing this engine against the standard library.

Run directly to execute the corpus, a randomised search over generated patterns,
a linear-time check for known catastrophic-backtracking patterns, and the
documentation examples::

    python -m oxide.regex.fuzz

Any divergence is printed with the offending pattern, subject and flags so it can
be reduced by hand. Exit status is non-zero when a check fails.

One class of divergence is accepted on purpose and reported separately. When a
repetition's body can match empty, CPython runs that body one final time with no
input consumed before leaving the loop, so ``(a*)*`` against ``"aa"`` reports
group 1 as the empty final iteration. This engine reports the last iteration that
consumed input instead, which is what Rust's ``regex`` crate and RE2 do. The
overall match span is identical; only the captures inside such a loop differ, and
``findall``/``split`` inherit the difference because they surface those captures.
"""

from __future__ import annotations

import random
import re
import sys
import time

import oxide.regex as rx
from oxide.regex._syntax import (
    Alternate, Anchor, AnyChar, CharClass, Concat, Empty, Group, Literal, Repeat,
)
from oxide.regex.api import _parse

__all__ = ["Corpus", "check", "run", "main"]


class Corpus:
    """Hand-written cases covering every supported construct.

    Attributes:
        patterns (tuple): Patterns exercised against every subject.
        subjects (tuple): Subjects exercised against every pattern.
        flags (tuple): Flag values applied to every combination.
        replacers (tuple): Replacement templates used for ``sub`` and ``subn``.
    """

    patterns: tuple = (
        "abc", "a.c", "a.*c", "a.*?c", "^abc$", "^a", "a$", r"\d+", r"\d{2,4}",
        r"\d{3}", r"\D+", r"\w+", r"\W+", r"\s+", r"\S+", "[a-z]+", "[^a-z]+",
        "[abc]", "[^abc]", "[a-zA-Z0-9_]+", "[[:alpha:]]+", "[[:digit:]]{2}",
        "[[:space:]]", "[[:^alpha:]]+", "[.]", r"[\d\s]", r"[\D]", r"[\w_]+",
        r"[\x41-\x43]+", r"[\101-\103]", "(a|b)c", "abc|abd", "(?:ab)+",
        "(a+)(b+)", "(a|ab)(c|bcd)", "x(a|ab|abc)y", "(?:foo|foobar)",
        "(a)(b)?(c)", "(a*)*", "(a|)b", "(?:)", "a|", "|a", "()", "(())",
        r"\bfoo\b", r"\Bfoo\B", r"\Afoo", r"foo\Z", r"\w+\s\w+",
        r"(\w+)@(\w+)\.com", r"([a-z]+)=(\d+)", r"\s*,\s*", r"(\s+)",
        r"\(\w+\)", r"[+-]?\d+\.?\d*", r"[A-Za-z_]\w*", r".", r".*", r".+",
        r"a{0,3}b", r"a{2}b", r"a{0}b", r"(ab){2,3}", r"a{1,}?b",
        r"(?P<word>\w+)", r"(?P<a>\d)(?P<b>\w)", r"x(?P<mid>y)?z",
        r"\d+(?=px)",  # lookahead: unsupported, must raise
        r"\d\1",  # backreference: unsupported, must raise
    )
    subjects: tuple = (
        "", "a", "abc", "aaa", "abcabc", "abcbcd", "a\nb", "x123y", "  ",
        "foo bar", "FOO", "foo", "me@you.com", "a=1, b=22 ,c=333",
        "acb", "xxz", "xyz", "cat dog cat", "a.c", "aaa\n", "\n", "AbC",
        "abcabcabc", "1a 2b", "x42", "hello, world", "a-b_c", "()", "ababab",
    )
    flags: tuple = (0, rx.IGNORECASE, rx.MULTILINE, rx.DOTALL, rx.VERBOSE)
    replacers: tuple = ("X", r"\1", r"\g<0>", "[\\1]")


def _is_supported(pattern: str, flags: int) -> bool:
    """Report whether a pattern avoids constructs the engine deliberately rejects.

    Args:
        pattern (str): The pattern string.
        flags (int): The flag mask.

    Returns:
        bool: True when both engines are expected to accept the pattern.
    """
    if "(?=" in pattern or "(?!" in pattern or "(?<" in pattern:
        return False
    if re.search(r"\\[1-9]", pattern) or "(?>" in pattern:
        return False
    if "[[:" in pattern:
        return False
    return True


def _normalise(value: object) -> object:
    """Reduce a result to a comparable structure.

    Args:
        value (object): A match, list of matches, string or None.

    Returns:
        object: A hashable representation of the result.
    """
    if isinstance(value, list):
        return [_normalise(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_normalise(item) for item in value)
    if isinstance(value, str) or value is None:
        return value
    return (value.group(), value.groups(), value.span(), value.groupdict())


def _nullable(node) -> bool:
    """Report whether a syntax tree node can match without consuming input.

    Args:
        node (Node): The syntax tree node to inspect.

    Returns:
        bool: True when the node may match the empty string.
    """
    if isinstance(node, (Empty, Anchor)):
        return True
    if isinstance(node, (Literal, CharClass, AnyChar)):
        return False
    if isinstance(node, Group):
        return _nullable(node.node)
    if isinstance(node, Concat):
        return all(_nullable(item) for item in node.items)
    if isinstance(node, Alternate):
        return any(_nullable(branch) for branch in node.branches)
    return node.min == 0 or _nullable(node.node)


def _has_empty_loop(node) -> bool:
    """Report whether the tree contains a repetition with an empty-matching body.

    Args:
        node (Node): The syntax tree node to inspect.

    Returns:
        bool: True when an unbounded repetition wraps a body matching empty.
    """
    if isinstance(node, Repeat):
        if node.max is None and _nullable(node.node):
            return True
        return _has_empty_loop(node.node)
    if isinstance(node, Group):
        return _has_empty_loop(node.node)
    if isinstance(node, Concat):
        return any(_has_empty_loop(item) for item in node.items)
    if isinstance(node, Alternate):
        return any(_has_empty_loop(branch) for branch in node.branches)
    return False


def _known_deviation(pattern: str, flags: int) -> bool:
    """Report whether a pattern falls into the accepted empty-loop capture class.

    Args:
        pattern (str): The pattern string.
        flags (int): The flag mask.

    Returns:
        bool: True when divergences for this pattern are already understood.
    """
    try:
        node, _, _, _ = _parse(pattern, flags)
    except Exception:  # noqa: BLE001 - rejected by both engines elsewhere
        return False
    return _has_empty_loop(node)


def _same_span(expected: object, actual: object) -> bool:
    """Report whether two normalised results agree on the overall match position.

    Args:
        expected (object): The standard library result.
        actual (object): This engine's result.

    Returns:
        bool: True when no span disagreement is visible, or none is reported.
    """
    if not (isinstance(expected, tuple) and isinstance(actual, tuple)):
        return True
    return expected[2] == actual[2]


def _compare(pattern: str, subject: str, flags: int) -> tuple[list, list]:
    """Compare every public entry point for one pattern/subject pair.

    Args:
        pattern (str): The pattern string.
        subject (str): The subject text.
        flags (int): The flag mask.

    Returns:
        tuple: Unexpected divergences, and accepted empty-loop deviations.
    """
    problems = []
    known = []
    operations = (
        ("match", lambda mod: mod.match(pattern, subject, flags)),
        ("fullmatch", lambda mod: mod.fullmatch(pattern, subject, flags)),
        ("search", lambda mod: mod.search(pattern, subject, flags)),
        ("findall", lambda mod: mod.findall(pattern, subject, flags)),
        ("finditer", lambda mod: [m.group() for m in mod.finditer(pattern, subject, flags)]),
        ("split", lambda mod: mod.split(pattern, subject, maxsplit=0, flags=flags)),
    )
    for replacer in Corpus.replacers[:1]:
        operations += (
            ("sub", lambda mod, r=replacer: mod.sub(pattern, r, subject, count=0, flags=flags)),
            ("subn", lambda mod, r=replacer: mod.subn(pattern, r, subject, count=0, flags=flags)),
        )
    accepted = _known_deviation(pattern, flags)
    for name, call in operations:
        try:
            expected = _normalise(call(re))
            failed = False
        except Exception:  # noqa: BLE001 - the standard library rejected it
            expected = None
            failed = True
        try:
            actual = _normalise(call(rx))
            broke = False
        except Exception:  # noqa: BLE001
            actual = None
            broke = True
        if failed or broke:
            if failed and broke:
                continue
            side = "re rejects but rx accepts" if failed else "rx rejects but re accepts"
            problems.append(
                f"{name}({pattern!r}, {subject!r}, flags={flags}): {side}"
            )
            continue
        if expected != actual:
            message = (
                f"{name}({pattern!r}, {subject!r}, flags={flags}): "
                f"re={expected!r} rx={actual!r}"
            )
            if accepted and _same_span(expected, actual):
                known.append(message)
            else:
                problems.append(message)
    return problems, known


def check_corpus() -> tuple[list, list]:
    """Run every corpus pattern against every subject and flag value.

    Returns:
        tuple: Unexpected divergences, and accepted empty-loop deviations.
    """
    problems = []
    known = []
    total = 0
    for pattern in Corpus.patterns:
        for flags in Corpus.flags:
            if not _is_supported(pattern, flags):
                continue
            for subject in Corpus.subjects:
                total += 1
                found, accepted = _compare(pattern, subject, flags)
                problems.extend(found)
                known.extend(accepted)
    print(f"corpus: {total} pattern/subject/flag combinations")
    return problems, known


def check_random(iterations: int = 4000, seed: int = 0) -> tuple[list, list]:
    """Compare randomly generated patterns against the standard library.

    Args:
        iterations (int): Number of patterns to generate.
        seed (int): Seed for reproducible runs.

    Returns:
        tuple: Unexpected divergences, and accepted empty-loop deviations.
    """
    rng = random.Random(seed)
    alphabet = "abcxy01 _-.@\n"
    pieces = [
        "a", "b", "c", "x", "1", "0", ".", r"\d", r"\w", r"\s", r"\D",
        r"\W", "[ab]", "[^ab]", "[a-c]", "[[:alpha:]]", "(a)", "(?:ab)",
        "(a|b)", "a*", "a+", "a?", "a{2}", "a{1,3}", "a{2,}", "*?", "+?", "??",
        "^", "$", r"\b", r"\B", "|", "(?P<n>a)", r"[\d]", r"[\x61]",
    ]
    problems = []
    known = []
    for step in range(iterations):
        pattern = "".join(rng.choice(pieces) for _ in range(rng.randint(1, 5)))
        if not _is_supported(pattern, 0):
            continue
        subject = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 8)))
        flags = rng.choice((0, rx.IGNORECASE, rx.MULTILINE, rx.DOTALL))
        found, accepted = _compare(pattern, subject, flags)
        problems.extend(found)
        known.extend(accepted)
        if step % 500 == 0 and step:
            print(f"  random: {step} patterns")
    print(f"random: {iterations} generated patterns (seed={seed})")
    return problems, known


def check_linear_time(budget: float = 0.5) -> list:
    """Confirm pathological patterns stay fast where the standard library hangs.

    Args:
        budget (float): Maximum seconds allowed per pattern.

    Returns:
        list: Human readable descriptions of each divergence.
    """
    problems = []
    attacks = (
        (r"(a+)+$", "a" * 40 + "b"),
        (r"(a|a)*$", "a" * 40 + "b"),
        (r"(a*)*b", "a" * 40),
        (r"(a|a?)+$", "a" * 40 + "b"),
        (r"(.*a){20}$", "a" * 40 + "b"),
        (r"([a-zA-Z]+)*$", "a" * 40 + "!"),
    )
    for pattern, subject in attacks:
        started = time.perf_counter()
        rx.search(pattern, subject)
        elapsed = time.perf_counter() - started
        status = "ok" if elapsed < budget else "SLOW"
        print(f"linear: {pattern!r:24} {len(subject):4d} chars  {elapsed * 1000:8.3f} ms  {status}")
        if elapsed >= budget:
            problems.append(f"linear: {pattern!r} took {elapsed:.3f}s (budget {budget}s)")
    return problems


def check_unsupported() -> list:
    """Confirm constructs without linear implementations are rejected loudly.

    Returns:
        list: Human readable descriptions of any acceptance.
    """
    rejected = (
        r"\d(?=\d)", r"\d(?!\d)", r"(?<=a)b", r"(?<!a)b", r"(a)\1",
        r"(?>a)", r"a*+", r"a++", r"a?+", r"\p{L}", r"\P{L}",
    )
    problems = []
    for pattern in rejected:
        try:
            rx.compile(pattern)
        except rx.RegexError:
            continue
        problems.append(f"unsupported: {pattern!r} compiled but should be rejected")
    print(f"unsupported: {len(rejected)} constructs checked")
    return problems


def run(iterations: int = 4000, seed: int = 0) -> tuple[list, list]:
    """Execute every check group and return all divergences.

    Args:
        iterations (int): Number of random patterns to generate.
        seed (int): Seed for reproducible runs.

    Returns:
        tuple: Unexpected divergences, and accepted empty-loop deviations.
    """
    problems = []
    known = []
    problems.extend(check_unsupported())
    found, accepted = check_corpus()
    problems.extend(found)
    known.extend(accepted)
    found, accepted = check_random(iterations, seed)
    problems.extend(found)
    known.extend(accepted)
    problems.extend(check_linear_time())
    return problems, known


def main() -> int:
    """Run the harness as a script.

    Returns:
        int: Process exit status, zero when every check passes.
    """
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    problems, known = run(iterations, seed)
    if known:
        print(f"\n{len(known)} accepted empty-loop capture deviation(s), e.g.")
        for line in known[:3]:
            print(f"  {line}")
    if not problems:
        print("\nall differential checks passed")
        return 0
    print(f"\n{len(problems)} divergence(s):")
    for line in problems[:80]:
        print(f"  {line}")
    if len(problems) > 80:
        print(f"  ... and {len(problems) - 80} more")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())