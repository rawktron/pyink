from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .null_exception import throw_null_exception
from .object import InkObject
from .path import Path

if TYPE_CHECKING:
    from .call_stack import CallStack


class Choice(InkObject):
    def __init__(self):
        super().__init__()
        self.text = ""
        self.index = 0
        self.threadAtGeneration: Optional["CallStack.Thread"] = None
        self.sourcePath = ""
        self.targetPath: Optional[Path] = None
        self.isInvisibleDefault = False
        self.tags: Optional[list[str]] = None
        self.originalThreadIndex = 0

    @property
    def pathStringOnChoice(self) -> str:
        if self.targetPath is None:
            return throw_null_exception("Choice.targetPath")
        return str(self.targetPath)

    @pathStringOnChoice.setter
    def pathStringOnChoice(self, value: str):
        self.targetPath = Path(value)

    def Clone(self):
        copy = Choice()
        copy.text = self.text
        copy.sourcePath = self.sourcePath
        copy.index = self.index
        copy.targetPath = self.targetPath
        copy.originalThreadIndex = self.originalThreadIndex
        copy.isInvisibleDefault = self.isInvisibleDefault
        if self.threadAtGeneration is not None:
            copy.threadAtGeneration = self.threadAtGeneration.Copy()
        return copy
