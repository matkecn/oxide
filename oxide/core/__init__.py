"""Core foundational types for the oxide library.

Provides algebraic types (Option, Result), tagged unions (Enum, Variant),
trait protocols for duck-typed polymorphism, range types, and error infrastructure.
"""

from __future__ import annotations

from .error import Location, Backtrace, Error, context
from .convert import (
    Range, RangeInclusive, RangeFrom, RangeTo, RangeToInclusive, RangeFull,
    range_, range_inclusive, range_from, range_to, range_to_inclusive,
)
from .option import Option, Some, NoneOption, None_, none
from .result import (
    Result, Ok, Err, PropagateError, Propagate, propagate, ask, try_ask,
)
from .enum import (
    MatchError, _Case, Match, _MatchWildcard, _, match, Variant, _EnumMeta, Enum,
)
from .traits import (
    CloneTrait, CopyTrait, DebugTrait, DisplayTrait, DefaultTrait,
    EqTrait, OrdTrait, HashTrait, FromTrait, IntoTrait,
    TryFromTrait, TryIntoTrait, AsRefTrait, AsMutTrait,
    DerefTrait, DerefMutTrait, DropTrait,
    clone, debug, display, default_of, from_, into,
    try_from, try_into, as_ref, as_mut, deref, deref_mut, drop,
)

from .masterclass import (
    masterclass, mastermethod, MasterMethod, is_master,
)
from .items import (

    path, no_mangle, used, cold, naked, link, link_name, crate_type, crate_name,
    repr_, repr_kinds_of, track_caller, caller_location,
    main, TestResult, test, bench, tests, benches, run_tests,
    ignore, ignored_reason, is_ignored, is_test, is_bench,
    serial, is_serial, should_panic, should_panic_of,
)
