from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .object import InkObject
    from .container import Container


class SearchResult:
    def __init__(self):
        self.obj: Optional["InkObject"] = None
        self.approximate = False

    @property
    def correctObj(self):
        return None if self.approximate else self.obj

    @property
    def container(self) -> Optional["Container"]:
        from .container import Container

        return self.obj if isinstance(self.obj, Container) else None

    def copy(self):
        result = SearchResult()
        result.obj = self.obj
        result.approximate = self.approximate
        return result
