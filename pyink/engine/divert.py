from __future__ import annotations

from typing import Optional

from .container import Container
from .null_exception import throw_null_exception
from .object import InkObject
from .path import Path
from .pointer import Pointer
from .push_pop import PushPopType
from .string_builder import StringBuilder


class Divert(InkObject):
    def __init__(self, stack_push_type: Optional[PushPopType] = None):
        super().__init__()
        self._targetPath: Optional[Path] = None
        self._targetPointer: Pointer = Pointer.Null()
        self.variableDivertName: Optional[str] = None
        self.pushesToStack = False
        self.stackPushType: PushPopType = PushPopType.Tunnel
        self.isExternal = False
        self.externalArgs = 0
        self.isConditional = False
        if stack_push_type is not None:
            self.pushesToStack = True
            self.stackPushType = stack_push_type

    @property
    def targetPath(self):
        if self._targetPath is not None and self._targetPath.isRelative:
            target_obj = self.targetPointer.Resolve()
            if target_obj:
                self._targetPath = target_obj.path
        return self._targetPath

    @targetPath.setter
    def targetPath(self, value: Optional[Path]):
        self._targetPath = value
        self._targetPointer = Pointer.Null()

    @property
    def targetPointer(self):
        if self._targetPointer.isNull:
            target_obj = self.ResolvePath(self._targetPath).obj
            if self._targetPath is None:
                return throw_null_exception("this._targetPath")
            if self._targetPath.lastComponent is None:
                return throw_null_exception("this._targetPath.lastComponent")
            if self._targetPath.lastComponent.isIndex:
                if target_obj is None:
                    return throw_null_exception("targetObj")
                self._targetPointer.container = target_obj.parent if isinstance(target_obj.parent, Container) else None
                self._targetPointer.index = self._targetPath.lastComponent.index
            else:
                self._targetPointer = Pointer.StartOf(target_obj if isinstance(target_obj, Container) else None)
        return self._targetPointer.copy()

    @property
    def targetPathString(self):
        if self.targetPath is None:
            return None
        return self.CompactPathString(self.targetPath)

    @targetPathString.setter
    def targetPathString(self, value: Optional[str]):
        if value is None:
            self.targetPath = None
        else:
            self.targetPath = Path(value)

    @property
    def hasVariableTarget(self):
        return self.variableDivertName is not None

    def Equals(self, obj: Optional["Divert"]):
        other_divert = obj
        if isinstance(other_divert, Divert):
            if self.hasVariableTarget == other_divert.hasVariableTarget:
                if self.hasVariableTarget:
                    return self.variableDivertName == other_divert.variableDivertName
                if self.targetPath is None:
                    return throw_null_exception("this.targetPath")
                return self.targetPath.Equals(other_divert.targetPath)
        return False

    def __str__(self):
        if self.hasVariableTarget:
            return "Divert(variable: " + str(self.variableDivertName) + ")"
        if self.targetPath is None:
            return "Divert(null)"
        sb = StringBuilder()
        target_str = str(self.targetPath)
        target_line_num = None
        if target_line_num is not None:
            target_str = "line " + str(target_line_num)

        sb.Append("Divert")
        if self.isConditional:
            sb.Append("?")
        if self.pushesToStack:
            if self.stackPushType == PushPopType.Function:
                sb.Append(" function")
            else:
                sb.Append(" tunnel")
        sb.Append(" -> ")
        sb.Append(self.targetPathString)
        sb.Append(" (")
        sb.Append(target_str)
        sb.Append(")")
        return str(sb)
