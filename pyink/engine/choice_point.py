from __future__ import annotations

from typing import Optional

from .container import Container
from .null_exception import throw_null_exception
from .object import InkObject
from .path import Path


class ChoicePoint(InkObject):
    def __init__(self, once_only: bool = True):
        super().__init__()
        self._pathOnChoice: Optional[Path] = None
        self.hasCondition = False
        self.hasStartContent = False
        self.hasChoiceOnlyContent = False
        self.isInvisibleDefault = False
        self.onceOnly = once_only

    @property
    def pathOnChoice(self):
        if self._pathOnChoice is not None and self._pathOnChoice.isRelative:
            choice_target_obj = self.choiceTarget
            if choice_target_obj:
                self._pathOnChoice = choice_target_obj.path
        return self._pathOnChoice

    @pathOnChoice.setter
    def pathOnChoice(self, value: Optional[Path]):
        self._pathOnChoice = value

    @property
    def choiceTarget(self) -> Optional[Container]:
        if self._pathOnChoice is None:
            return throw_null_exception("ChoicePoint._pathOnChoice")
        return self.ResolvePath(self._pathOnChoice).container

    @property
    def pathStringOnChoice(self) -> str:
        if self.pathOnChoice is None:
            return throw_null_exception("ChoicePoint.pathOnChoice")
        return self.CompactPathString(self.pathOnChoice)

    @pathStringOnChoice.setter
    def pathStringOnChoice(self, value: str):
        self.pathOnChoice = Path(value)

    @property
    def flags(self) -> int:
        flags = 0
        if self.hasCondition:
            flags |= 1
        if self.hasStartContent:
            flags |= 2
        if self.hasChoiceOnlyContent:
            flags |= 4
        if self.isInvisibleDefault:
            flags |= 8
        if self.onceOnly:
            flags |= 16
        return flags

    @flags.setter
    def flags(self, value: int):
        self.hasCondition = (value & 1) > 0
        self.hasStartContent = (value & 2) > 0
        self.hasChoiceOnlyContent = (value & 4) > 0
        self.isInvisibleDefault = (value & 8) > 0
        self.onceOnly = (value & 16) > 0

    def __str__(self):
        if self.pathOnChoice is None:
            return throw_null_exception("ChoicePoint.pathOnChoice")
        target_line_num = None
        target_string = str(self.pathOnChoice)
        if target_line_num is not None:
            target_string = " line " + str(target_line_num) + "(" + target_string + ")"
        return "Choice: -> " + target_string
