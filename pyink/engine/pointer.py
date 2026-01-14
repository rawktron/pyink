from __future__ import annotations

from typing import Optional

from .path import Path


class Pointer:
    def __init__(self, container=None, index: int = -1):
        self.container = container
        self.index = index

    def Resolve(self):
        if self.index < 0:
            return self.container
        if self.container is None:
            return None
        if len(self.container.content) == 0:
            return self.container
        if self.index >= len(self.container.content):
            return None
        return self.container.content[self.index]

    @property
    def isNull(self) -> bool:
        return self.container is None

    @property
    def path(self) -> Optional[Path]:
        if self.isNull:
            return None
        if self.index >= 0:
            return self.container.path.PathByAppendingComponent(Path.Component(self.index))
        return self.container.path

    def __str__(self):
        if not self.container:
            return "Ink Pointer (null)"
        return f"Ink Pointer -> {self.container.path} -- index {self.index}"

    def copy(self):
        return Pointer(self.container, self.index)

    @staticmethod
    def StartOf(container):
        return Pointer(container, 0)

    @staticmethod
    def Null():
        return Pointer(None, -1)
