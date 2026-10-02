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
