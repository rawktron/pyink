from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Generic, Optional, TypeVar

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


@dataclass
class TryGetResult(Generic[T]):
    result: T
    exists: bool


def try_get_value_from_map(map_obj: Optional[Dict[K, V]], key: K, value: V):
    if map_obj is None:
        return TryGetResult(value, False)
    if key not in map_obj:
        return TryGetResult(value, False)
    return TryGetResult(map_obj[key], True)


def try_parse_int(value, default_value: int = 0):
    try:
        return TryGetResult(int(value), True)
    except (TypeError, ValueError):
        return TryGetResult(default_value, False)


def try_parse_float(value, default_value: float = 0.0):
    try:
        return TryGetResult(float(value), True)
    except (TypeError, ValueError):
        return TryGetResult(default_value, False)
