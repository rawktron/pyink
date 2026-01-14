from __future__ import annotations

from typing import Any, Optional, Type, TypeVar

from .inamed_content import INamedContent

T = TypeVar("T")


def as_or_null(obj: Any, expected_type: Type[T]) -> Optional[T]:
    if isinstance(obj, expected_type):
        return obj
    return None


def as_or_throws(obj: Any, expected_type: Type[T]) -> T:
    if isinstance(obj, expected_type):
        return obj
    raise TypeError(f"{obj} is not of type {expected_type}")


def as_number_or_throws(obj: Any) -> float:
    if isinstance(obj, (int, float)):
        return obj
    raise TypeError(f"{obj} is not a number")


def as_boolean_or_throws(obj: Any) -> bool:
    if isinstance(obj, bool):
        return obj
    raise TypeError(f"{obj} is not a boolean")


def as_inamed_content_or_null(obj: Any) -> Optional[INamedContent]:
    if hasattr(obj, "hasValidName") and hasattr(obj, "name"):
        if getattr(obj, "hasValidName") and getattr(obj, "name"):
            return obj
    return None


def null_if_undefined(obj: Optional[T]) -> Optional[T]:
    return obj


def is_equatable(obj: Any) -> bool:
    return hasattr(obj, "Equals") and callable(getattr(obj, "Equals"))


def filter_undef(obj: Optional[T]) -> bool:
    return obj is not None
