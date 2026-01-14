from __future__ import annotations

from typing import Any

from .ink_list import InkList, InkListItem
from .null_exception import throw_null_exception
from .object import InkObject
from .path import Path
from .story_exception import StoryException
from .try_get_result import try_parse_float, try_parse_int
from .type_assertion import as_or_null, as_or_throws


class ValueType:
    Bool = -1
    Int = 0
    Float = 1
    List = 2
    String = 3
    DivertTarget = 4
    VariablePointer = 5


class AbstractValue(InkObject):
    @property
    def valueType(self):
        raise NotImplementedError()

    @property
    def isTruthy(self):
        raise NotImplementedError()

    @property
    def valueObject(self):
        raise NotImplementedError()

    def Cast(self, new_type: int):
        raise NotImplementedError()

    @staticmethod
    def Create(val: Any, preferred_number_type: int | None = None):
        if preferred_number_type is not None:
            if preferred_number_type == ValueType.Int and isinstance(val, (int, float)) and float(val).is_integer():
                return IntValue(int(val))
            if preferred_number_type == ValueType.Float and isinstance(val, (int, float)):
                return FloatValue(float(val))

        if isinstance(val, bool):
            return BoolValue(bool(val))
        if isinstance(val, str):
            return StringValue(str(val))
        if isinstance(val, (int, float)) and float(val).is_integer():
            return IntValue(int(val))
        if isinstance(val, (int, float)):
            return FloatValue(float(val))
        if isinstance(val, Path):
            return DivertTargetValue(as_or_throws(val, Path))
        if isinstance(val, InkList):
            return ListValue(as_or_throws(val, InkList))
        return None

    def Copy(self):
        return as_or_throws(AbstractValue.Create(self.valueObject), InkObject)

    def BadCastException(self, target_type: int):
        return StoryException(
            "Can't cast " + str(self.valueObject) + " from " + str(self.valueType) + " to " + str(target_type)
        )


class Value(AbstractValue):
    def __init__(self, val):
        super().__init__()
        self.value = val

    @property
    def valueObject(self):
        return self.value

    def __str__(self):
        if self.value is None:
            return throw_null_exception("Value.value")
        return str(self.value)

    def toString(self):
        return str(self)


class BoolValue(Value):
    def __init__(self, val: bool):
        super().__init__(val or False)

    @property
    def isTruthy(self):
        return bool(self.value)

    @property
    def valueType(self):
        return ValueType.Bool

    def Cast(self, new_type: int):
        if self.value is None:
            return throw_null_exception("Value.value")
        if new_type == self.valueType:
            return self
        if new_type == ValueType.Int:
            return IntValue(1 if self.value else 0)
        if new_type == ValueType.Float:
            return FloatValue(1.0 if self.value else 0.0)
        if new_type == ValueType.String:
            return StringValue("true" if self.value else "false")
        raise self.BadCastException(new_type)

    def __str__(self):
        return "true" if self.value else "false"


class IntValue(Value):
    def __init__(self, val: int):
        super().__init__(val or 0)

    @property
    def isTruthy(self):
        return self.value != 0

    @property
    def valueType(self):
        return ValueType.Int

    def Cast(self, new_type: int):
        if self.value is None:
            return throw_null_exception("Value.value")
        if new_type == self.valueType:
            return self
        if new_type == ValueType.Bool:
            return BoolValue(False if self.value == 0 else True)
        if new_type == ValueType.Float:
            return FloatValue(self.value)
        if new_type == ValueType.String:
            return StringValue(str(self.value))
        raise self.BadCastException(new_type)


class FloatValue(Value):
    def __init__(self, val: float):
        super().__init__(val or 0.0)

    @property
    def isTruthy(self):
        return self.value != 0.0

    @property
    def valueType(self):
        return ValueType.Float

    def Cast(self, new_type: int):
        if self.value is None:
            return throw_null_exception("Value.value")
        if new_type == self.valueType:
            return self
        if new_type == ValueType.Bool:
            return BoolValue(False if self.value == 0.0 else True)
        if new_type == ValueType.Int:
            return IntValue(int(self.value))
        if new_type == ValueType.String:
            return StringValue(str(self.value))
        raise self.BadCastException(new_type)

    def __str__(self):
        if self.value is None:
            return throw_null_exception("Value.value")
        if float(self.value).is_integer():
            return str(int(self.value))
        return str(self.value)


class StringValue(Value):
    def __init__(self, val: str):
        super().__init__(val or "")
        self._isNewline = self.value == "\n"
        self._isInlineWhitespace = True
        if self.value is None:
            return throw_null_exception("Value.value")
        if len(self.value) > 0:
            for c in self.value:
                if c != " " and c != "\t":
                    self._isInlineWhitespace = False
                    break

    @property
    def valueType(self):
        return ValueType.String

    @property
    def isTruthy(self):
        if self.value is None:
            return throw_null_exception("Value.value")
        return len(self.value) > 0

    @property
    def isNewline(self):
        return self._isNewline

    @property
    def isInlineWhitespace(self):
        return self._isInlineWhitespace

    @property
    def isNonWhitespace(self):
        return not self.isNewline and not self.isInlineWhitespace

    def Cast(self, new_type: int):
        if new_type == self.valueType:
            return self
        if new_type == ValueType.Int:
            parsed_int = try_parse_int(self.value)
            if parsed_int.exists:
                return IntValue(parsed_int.result)
            raise self.BadCastException(new_type)
        if new_type == ValueType.Float:
            parsed_float = try_parse_float(self.value)
            if parsed_float.exists:
                return FloatValue(parsed_float.result)
            raise self.BadCastException(new_type)
        raise self.BadCastException(new_type)


class DivertTargetValue(Value):
    def __init__(self, target_path: Path | None = None):
        super().__init__(target_path)

    @property
    def valueType(self):
        return ValueType.DivertTarget

    @property
    def targetPath(self):
        if self.value is None:
            return throw_null_exception("Value.value")
        return self.value

    @targetPath.setter
    def targetPath(self, value):
        self.value = value

    @property
    def isTruthy(self):
        raise ValueError("Shouldn't be checking the truthiness of a divert target")

    def Cast(self, new_type: int):
        if new_type == self.valueType:
            return self
        raise self.BadCastException(new_type)

    def __str__(self):
        return "DivertTargetValue(" + str(self.targetPath) + ")"


class VariablePointerValue(Value):
    def __init__(self, variable_name: str, context_index: int = -1):
        super().__init__(variable_name)
        self._contextIndex = context_index

    @property
    def contextIndex(self):
        return self._contextIndex

    @contextIndex.setter
    def contextIndex(self, value: int):
        self._contextIndex = value

    @property
    def variableName(self):
        if self.value is None:
            return throw_null_exception("Value.value")
        return self.value

    @variableName.setter
    def variableName(self, value: str):
        self.value = value

    @property
    def valueType(self):
        return ValueType.VariablePointer

    @property
    def isTruthy(self):
        raise ValueError("Shouldn't be checking the truthiness of a variable pointer")

    def Cast(self, new_type: int):
        if new_type == self.valueType:
            return self
        raise self.BadCastException(new_type)

    def __str__(self):
        return "VariablePointerValue(" + str(self.variableName) + ")"

    def Copy(self):
        return VariablePointerValue(self.variableName, self.contextIndex)


class ListValue(Value):
    @property
    def isTruthy(self):
        if self.value is None:
            return throw_null_exception("this.value")
        return self.value.Count > 0

    @property
    def valueType(self):
        return ValueType.List

    def Cast(self, new_type: int):
        if self.value is None:
            return throw_null_exception("Value.value")
        if new_type == ValueType.Int:
            max_item = self.value.maxItem
            if max_item.Key.isNull:
                return IntValue(0)
            return IntValue(max_item.Value)
        if new_type == ValueType.Float:
            max_item = self.value.maxItem
            if max_item.Key.isNull:
                return FloatValue(0.0)
            return FloatValue(max_item.Value)
        if new_type == ValueType.String:
            max_item = self.value.maxItem
            if max_item.Key.isNull:
                return StringValue("")
            return StringValue(str(max_item.Key))
        if new_type == self.valueType:
            return self
        raise self.BadCastException(new_type)

    def __init__(self, list_or_single_item=None, single_value: int | None = None):
        super().__init__(None)
        if list_or_single_item is None and single_value is None:
            self.value = InkList()
        elif isinstance(list_or_single_item, InkList):
            self.value = InkList(list_or_single_item)
        elif isinstance(list_or_single_item, InkListItem) and isinstance(single_value, int):
            self.value = InkList({"Key": list_or_single_item, "Value": single_value})

    @staticmethod
    def RetainListOriginsForAssignment(old_value: InkObject | None, new_value: InkObject):
        old_list = as_or_null(old_value, ListValue)
        new_list = as_or_null(new_value, ListValue)
        if new_list and new_list.value is None:
            return throw_null_exception("newList.value")
        if old_list and old_list.value is None:
            return throw_null_exception("oldList.value")
        if old_list and new_list and new_list.value.Count == 0:
            new_list.value.SetInitialOriginNames(old_list.value.originNames)
