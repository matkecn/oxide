"""Design by contract utilities."""
from __future__ import annotations

from typing import Any, Callable


class ContractError(AssertionError):
    """Raised when a contract is violated."""
    pass


def requires(condition: bool, message: str = "precondition failed") -> None:
    if not condition:
        raise ContractError(message)


def ensures(condition: bool, message: str = "postcondition failed") -> None:
    if not condition:
        raise ContractError(message)


def invariant(condition: bool, message: str = "invariant failed") -> None:
    if not condition:
        raise ContractError(message)
