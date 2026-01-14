from __future__ import annotations

from typing import Optional

from .object import InkObject
from .path import Path


class VariableReference(InkObject):
    def __init__(self, name: Optional[str] = None):
        super().__init__()
        self.name = name
        self.pathForCount: Optional[Path] = None

    @property
    def containerForCount(self):
        if self.pathForCount is None:
            return None
        return self.ResolvePath(self.pathForCount).container

    @property
    def pathStringForCount(self):
        if self.pathForCount is None:
            return None
        return self.CompactPathString(self.pathForCount)

    @pathStringForCount.setter
    def pathStringForCount(self, value: Optional[str]):
        if value is None:
            self.pathForCount = None
        else:
            self.pathForCount = Path(value)

    def __str__(self):
        if self.name is not None:
            return "var(" + self.name + ")"
        return "read_count(" + str(self.pathStringForCount) + ")"
