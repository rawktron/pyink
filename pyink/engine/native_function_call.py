from __future__ import annotations

from typing import Callable, Dict, List

from .ink_list import InkList, InkListItem
from .null_exception import throw_null_exception
from .object import InkObject
from .path import Path
from .story_exception import StoryException
from .type_assertion import as_boolean_or_throws, as_or_null, as_or_throws
from .value import BoolValue, IntValue, ListValue, Value, ValueType
from .void import Void

BinaryOp = Callable[[object, object], object]
UnaryOp = Callable[[object], object]


class NativeFunctionCall(InkObject):
    Add = "+"
    Subtract = "-"
    Divide = "/"
    Multiply = "*"
    Mod = "%"
    Negate = "_"
    Equal = "=="
    Greater = ">"
    Less = "<"
    GreaterThanOrEquals = ">="
    LessThanOrEquals = "<="
    NotEquals = "!="
    Not = "!"
    And = "&&"
    Or = "||"
    Min = "MIN"
    Max = "MAX"
    Pow = "POW"
    Floor = "FLOOR"
    Ceiling = "CEILING"
    Int = "INT"
    Float = "FLOAT"
    Has = "?"
    Hasnt = "!?"
    Intersect = "^"
    ListMin = "LIST_MIN"
    ListMax = "LIST_MAX"
    All = "LIST_ALL"
    Count = "LIST_COUNT"
    ValueOfList = "LIST_VALUE"
    Invert = "LIST_INVERT"

    _nativeFunctions: Dict[str, "NativeFunctionCall"] | None = None

    @staticmethod
    def CallWithName(function_name: str):
        return NativeFunctionCall(function_name)

    @staticmethod
    def CallExistsWithName(function_name: str):
        NativeFunctionCall.GenerateNativeFunctionsIfNecessary()
        return NativeFunctionCall._nativeFunctions.get(function_name)

    def __init__(self, name: str | None = None, number_of_parameters: int | None = None):
        super().__init__()
        self._name = None
        self._numberOfParameters = 0
        self._prototype: NativeFunctionCall | None = None
        self._isPrototype = False
        self._operationFuncs: Dict[int, BinaryOp | UnaryOp] | None = None

        if name is None and number_of_parameters is None:
            NativeFunctionCall.GenerateNativeFunctionsIfNecessary()
        elif name is not None and number_of_parameters is None:
            NativeFunctionCall.GenerateNativeFunctionsIfNecessary()
            self.name = name
        else:
            self._isPrototype = True
            self.name = name
            self.numberOfParameters = number_of_parameters

    @property
    def name(self):
        if self._name is None:
            return throw_null_exception("NativeFunctionCall._name")
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value
        if not self._isPrototype:
            if NativeFunctionCall._nativeFunctions is None:
                return throw_null_exception("NativeFunctionCall._nativeFunctions")
            self._prototype = NativeFunctionCall._nativeFunctions.get(self._name)

    @property
    def numberOfParameters(self):
        if self._prototype:
            return self._prototype.numberOfParameters
        return self._numberOfParameters

    @numberOfParameters.setter
    def numberOfParameters(self, value: int):
        self._numberOfParameters = value

    def Call(self, parameters: List[InkObject]):
        if self._prototype:
            return self._prototype.Call(parameters)

        if self.numberOfParameters != len(parameters):
            raise ValueError("Unexpected number of parameters")

        has_list = False
        for p in parameters:
            if isinstance(p, Void):
                raise StoryException(
                    "Attempting to perform "
                    + self.name
                    + ' on a void value. Did you forget to "return" a value from a function you called here?'
                )
            if isinstance(p, ListValue):
                has_list = True

        if len(parameters) == 2 and has_list:
            return self.CallBinaryListOperation(parameters)

        coerced_params = self.CoerceValuesToSingleType(parameters)
        coerced_type = coerced_params[0].valueType

        if coerced_type in (ValueType.Int, ValueType.Float, ValueType.String, ValueType.DivertTarget, ValueType.List):
            return self.CallType(coerced_params)
        return None

    def CallType(self, parameters_of_single_type: List[Value]):
        param1 = as_or_throws(parameters_of_single_type[0], Value)
        val_type = param1.valueType
        val1 = param1
        param_count = len(parameters_of_single_type)

        if param_count in (1, 2):
            if self._operationFuncs is None:
                return throw_null_exception("NativeFunctionCall._operationFuncs")
            op_for_type_obj = self._operationFuncs.get(val_type)
            if not op_for_type_obj:
                raise StoryException("Cannot perform operation " + self.name + " on " + str(val_type))

            if param_count == 2:
                param2 = as_or_throws(parameters_of_single_type[1], Value)
                val2 = param2
                op_for_type = op_for_type_obj
                if val1.value is None or val2.value is None:
                    return throw_null_exception("NativeFunctionCall.Call BinaryOp values")
                result_val = op_for_type(val1.value, val2.value)
                return Value.Create(result_val)
            op_for_type = op_for_type_obj
            if val1.value is None:
                return throw_null_exception("NativeFunctionCall.Call UnaryOp value")
            result_val = op_for_type(val1.value)
            if self.name == NativeFunctionCall.Int:
                return Value.Create(result_val, ValueType.Int)
            if self.name == NativeFunctionCall.Float:
                return Value.Create(result_val, ValueType.Float)
            return Value.Create(result_val, param1.valueType)

        raise ValueError(
            "Unexpected number of parameters to NativeFunctionCall: " + str(len(parameters_of_single_type))
        )

    def CallBinaryListOperation(self, parameters: List[InkObject]):
        if self.name in (NativeFunctionCall.Add, NativeFunctionCall.Subtract) and isinstance(
            parameters[0], ListValue
        ) and isinstance(parameters[1], IntValue):
            return self.CallListIncrementOperation(parameters)

        v1 = as_or_throws(parameters[0], Value)
        v2 = as_or_throws(parameters[1], Value)

        if self.name in (NativeFunctionCall.And, NativeFunctionCall.Or) and (
            v1.valueType != ValueType.List or v2.valueType != ValueType.List
        ):
            if self._operationFuncs is None:
                return throw_null_exception("NativeFunctionCall._operationFuncs")
            op = self._operationFuncs.get(ValueType.Int)
            if op is None:
                return throw_null_exception("NativeFunctionCall.CallBinaryListOperation op")
            result = as_boolean_or_throws(op(1 if v1.isTruthy else 0, 1 if v2.isTruthy else 0))
            return BoolValue(result)

        if v1.valueType == ValueType.List and v2.valueType == ValueType.List:
            return self.CallType([v1, v2])

        raise StoryException(
            "Can not call use "
            + self.name
            + " operation on "
            + str(v1.valueType)
            + " and "
            + str(v2.valueType)
        )

    def CallListIncrementOperation(self, list_int_params: List[InkObject]):
        list_val = as_or_throws(list_int_params[0], ListValue)
        int_val = as_or_throws(list_int_params[1], IntValue)

        result_ink_list = InkList()

        if list_val.value is None:
            return throw_null_exception("NativeFunctionCall.CallListIncrementOperation listVal.value")
        for list_item_key, list_item_value in list_val.value.items():
            list_item = InkListItem.fromSerializedKey(list_item_key)

            if self._operationFuncs is None:
                return throw_null_exception("NativeFunctionCall._operationFuncs")
            int_op = self._operationFuncs.get(ValueType.Int)

            if int_val.value is None:
                return throw_null_exception("NativeFunctionCall.CallListIncrementOperation intVal.value")
            target_int = int_op(list_item_value, int_val.value)

            item_origin = None
            if list_val.value.origins is None:
                return throw_null_exception("NativeFunctionCall.CallListIncrementOperation listVal.value.origins")
            for origin in list_val.value.origins:
                if origin.name == list_item.originName:
                    item_origin = origin
                    break
            if item_origin is not None:
                incremented_item = item_origin.TryGetItemWithValue(target_int, InkListItem.Null())
                if incremented_item.exists:
                    result_ink_list.Add(incremented_item.result, target_int)

        return ListValue(result_ink_list)

    def CoerceValuesToSingleType(self, parameters_in: List[InkObject]):
        val_type = ValueType.Int
        special_case_list: ListValue | None = None

        for obj in parameters_in:
            val = as_or_throws(obj, Value)
            if val.valueType > val_type:
                val_type = val.valueType
            if val.valueType == ValueType.List:
                special_case_list = as_or_null(val, ListValue)

        parameters_out: List[Value] = []

        if val_type == ValueType.List:
            for ink_object_val in parameters_in:
                val = as_or_throws(ink_object_val, Value)
                if val.valueType == ValueType.List:
                    parameters_out.append(val)
                elif val.valueType == ValueType.Int:
                    int_val = int(val.valueObject)
                    special_case_list = as_or_throws(special_case_list, ListValue)
                    if special_case_list.value is None:
                        return throw_null_exception(
                            "NativeFunctionCall.CoerceValuesToSingleType specialCaseList.value"
                        )
                    list_def = special_case_list.value.originOfMaxItem
                    if list_def is None:
                        return throw_null_exception("NativeFunctionCall.CoerceValuesToSingleType list")
                    item = list_def.TryGetItemWithValue(int_val, InkListItem.Null())
                    if item.exists:
                        casted_value = ListValue(item.result, int_val)
                        parameters_out.append(casted_value)
                    else:
                        raise StoryException(
                            "Could not find List item with the value " + str(int_val) + " in " + list_def.name
                        )
                else:
                    raise StoryException("Cannot mix Lists and " + str(val.valueType) + " values in this operation")
        else:
            for ink_object_val in parameters_in:
                val = as_or_throws(ink_object_val, Value)
                casted_value = val.Cast(val_type)
                parameters_out.append(casted_value)

        return parameters_out

    @staticmethod
    def Identity(t):
        return t

    @staticmethod
    def GenerateNativeFunctionsIfNecessary():
        if NativeFunctionCall._nativeFunctions is None:
            NativeFunctionCall._nativeFunctions = {}

            NativeFunctionCall.AddIntBinaryOp(NativeFunctionCall.Add, lambda x, y: x + y)
            NativeFunctionCall.AddIntBinaryOp(NativeFunctionCall.Subtract, lambda x, y: x - y)
            NativeFunctionCall.AddIntBinaryOp(NativeFunctionCall.Multiply, lambda x, y: x * y)
            NativeFunctionCall.AddIntBinaryOp(NativeFunctionCall.Divide, lambda x, y: x // y)
            NativeFunctionCall.AddIntBinaryOp(NativeFunctionCall.Mod, lambda x, y: x % y)
            NativeFunctionCall.AddIntUnaryOp(NativeFunctionCall.Negate, lambda x: -x)

            NativeFunctionCall.AddIntBinaryOp(NativeFunctionCall.Equal, lambda x, y: x == y)
            NativeFunctionCall.AddIntBinaryOp(NativeFunctionCall.Greater, lambda x, y: x > y)
            NativeFunctionCall.AddIntBinaryOp(NativeFunctionCall.Less, lambda x, y: x < y)
            NativeFunctionCall.AddIntBinaryOp(NativeFunctionCall.GreaterThanOrEquals, lambda x, y: x >= y)
            NativeFunctionCall.AddIntBinaryOp(NativeFunctionCall.LessThanOrEquals, lambda x, y: x <= y)
            NativeFunctionCall.AddIntBinaryOp(NativeFunctionCall.NotEquals, lambda x, y: x != y)
            NativeFunctionCall.AddIntUnaryOp(NativeFunctionCall.Not, lambda x: x == 0)

            NativeFunctionCall.AddIntBinaryOp(NativeFunctionCall.And, lambda x, y: x != 0 and y != 0)
            NativeFunctionCall.AddIntBinaryOp(NativeFunctionCall.Or, lambda x, y: x != 0 or y != 0)

            NativeFunctionCall.AddIntBinaryOp(NativeFunctionCall.Max, lambda x, y: max(x, y))
            NativeFunctionCall.AddIntBinaryOp(NativeFunctionCall.Min, lambda x, y: min(x, y))

            NativeFunctionCall.AddIntBinaryOp(NativeFunctionCall.Pow, lambda x, y: pow(x, y))
            NativeFunctionCall.AddIntUnaryOp(NativeFunctionCall.Floor, NativeFunctionCall.Identity)
            NativeFunctionCall.AddIntUnaryOp(NativeFunctionCall.Ceiling, NativeFunctionCall.Identity)
            NativeFunctionCall.AddIntUnaryOp(NativeFunctionCall.Int, NativeFunctionCall.Identity)
            NativeFunctionCall.AddIntUnaryOp(NativeFunctionCall.Float, lambda x: x)

            NativeFunctionCall.AddFloatBinaryOp(NativeFunctionCall.Add, lambda x, y: x + y)
            NativeFunctionCall.AddFloatBinaryOp(NativeFunctionCall.Subtract, lambda x, y: x - y)
            NativeFunctionCall.AddFloatBinaryOp(NativeFunctionCall.Multiply, lambda x, y: x * y)
            NativeFunctionCall.AddFloatBinaryOp(NativeFunctionCall.Divide, lambda x, y: x / y)
            NativeFunctionCall.AddFloatBinaryOp(NativeFunctionCall.Mod, lambda x, y: x % y)
            NativeFunctionCall.AddFloatUnaryOp(NativeFunctionCall.Negate, lambda x: -x)

            NativeFunctionCall.AddFloatBinaryOp(NativeFunctionCall.Equal, lambda x, y: x == y)
            NativeFunctionCall.AddFloatBinaryOp(NativeFunctionCall.Greater, lambda x, y: x > y)
            NativeFunctionCall.AddFloatBinaryOp(NativeFunctionCall.Less, lambda x, y: x < y)
            NativeFunctionCall.AddFloatBinaryOp(NativeFunctionCall.GreaterThanOrEquals, lambda x, y: x >= y)
            NativeFunctionCall.AddFloatBinaryOp(NativeFunctionCall.LessThanOrEquals, lambda x, y: x <= y)
            NativeFunctionCall.AddFloatBinaryOp(NativeFunctionCall.NotEquals, lambda x, y: x != y)
            NativeFunctionCall.AddFloatUnaryOp(NativeFunctionCall.Not, lambda x: x == 0.0)

            NativeFunctionCall.AddFloatBinaryOp(NativeFunctionCall.And, lambda x, y: x != 0.0 and y != 0.0)
            NativeFunctionCall.AddFloatBinaryOp(NativeFunctionCall.Or, lambda x, y: x != 0.0 or y != 0.0)

            NativeFunctionCall.AddFloatBinaryOp(NativeFunctionCall.Max, lambda x, y: max(x, y))
            NativeFunctionCall.AddFloatBinaryOp(NativeFunctionCall.Min, lambda x, y: min(x, y))

            NativeFunctionCall.AddFloatBinaryOp(NativeFunctionCall.Pow, lambda x, y: pow(x, y))
            import math

            NativeFunctionCall.AddFloatUnaryOp(NativeFunctionCall.Floor, lambda x: math.floor(x))
            NativeFunctionCall.AddFloatUnaryOp(NativeFunctionCall.Ceiling, lambda x: math.ceil(x))
            NativeFunctionCall.AddFloatUnaryOp(NativeFunctionCall.Int, lambda x: math.floor(x))
            NativeFunctionCall.AddFloatUnaryOp(NativeFunctionCall.Float, NativeFunctionCall.Identity)

            NativeFunctionCall.AddStringBinaryOp(NativeFunctionCall.Add, lambda x, y: x + y)
            NativeFunctionCall.AddStringBinaryOp(NativeFunctionCall.Equal, lambda x, y: x == y)
            NativeFunctionCall.AddStringBinaryOp(NativeFunctionCall.NotEquals, lambda x, y: not (x == y))
            NativeFunctionCall.AddStringBinaryOp(NativeFunctionCall.Has, lambda x, y: y in x)
            NativeFunctionCall.AddStringBinaryOp(NativeFunctionCall.Hasnt, lambda x, y: y not in x)

            NativeFunctionCall.AddListBinaryOp(NativeFunctionCall.Add, lambda x, y: x.Union(y))
            NativeFunctionCall.AddListBinaryOp(NativeFunctionCall.Subtract, lambda x, y: x.Without(y))
            NativeFunctionCall.AddListBinaryOp(NativeFunctionCall.Has, lambda x, y: x.Contains(y))
            NativeFunctionCall.AddListBinaryOp(NativeFunctionCall.Hasnt, lambda x, y: not x.Contains(y))
            NativeFunctionCall.AddListBinaryOp(NativeFunctionCall.Intersect, lambda x, y: x.Intersect(y))

            NativeFunctionCall.AddListBinaryOp(NativeFunctionCall.Equal, lambda x, y: x.Equals(y))
            NativeFunctionCall.AddListBinaryOp(NativeFunctionCall.Greater, lambda x, y: x.GreaterThan(y))
            NativeFunctionCall.AddListBinaryOp(NativeFunctionCall.Less, lambda x, y: x.LessThan(y))
            NativeFunctionCall.AddListBinaryOp(NativeFunctionCall.GreaterThanOrEquals, lambda x, y: x.GreaterThanOrEquals(y))
            NativeFunctionCall.AddListBinaryOp(NativeFunctionCall.LessThanOrEquals, lambda x, y: x.LessThanOrEquals(y))
            NativeFunctionCall.AddListBinaryOp(NativeFunctionCall.NotEquals, lambda x, y: not x.Equals(y))

            NativeFunctionCall.AddListBinaryOp(NativeFunctionCall.And, lambda x, y: x.Count > 0 and y.Count > 0)
            NativeFunctionCall.AddListBinaryOp(NativeFunctionCall.Or, lambda x, y: x.Count > 0 or y.Count > 0)
            NativeFunctionCall.AddListUnaryOp(NativeFunctionCall.Not, lambda x: 1 if x.Count == 0 else 0)

            NativeFunctionCall.AddListUnaryOp(NativeFunctionCall.Invert, lambda x: x.inverse)
            NativeFunctionCall.AddListUnaryOp(NativeFunctionCall.All, lambda x: x.all)
            NativeFunctionCall.AddListUnaryOp(NativeFunctionCall.ListMin, lambda x: x.MinAsList())
            NativeFunctionCall.AddListUnaryOp(NativeFunctionCall.ListMax, lambda x: x.MaxAsList())
            NativeFunctionCall.AddListUnaryOp(NativeFunctionCall.Count, lambda x: x.Count)
            NativeFunctionCall.AddListUnaryOp(NativeFunctionCall.ValueOfList, lambda x: x.maxItem.Value)

            NativeFunctionCall.AddOpToNativeFunc(
                NativeFunctionCall.Equal, 2, ValueType.DivertTarget, lambda d1, d2: d1.Equals(d2)
            )
            NativeFunctionCall.AddOpToNativeFunc(
                NativeFunctionCall.NotEquals, 2, ValueType.DivertTarget, lambda d1, d2: not d1.Equals(d2)
            )

    def AddOpFuncForType(self, val_type: int, op: BinaryOp | UnaryOp):
        if self._operationFuncs is None:
            self._operationFuncs = {}
        self._operationFuncs[val_type] = op

    @staticmethod
    def AddOpToNativeFunc(name: str, args: int, val_type: int, op: BinaryOp | UnaryOp):
        if NativeFunctionCall._nativeFunctions is None:
            return throw_null_exception("NativeFunctionCall._nativeFunctions")
        native_func = NativeFunctionCall._nativeFunctions.get(name)
        if native_func is None:
            native_func = NativeFunctionCall(name, args)
            NativeFunctionCall._nativeFunctions[name] = native_func
        native_func.AddOpFuncForType(val_type, op)

    @staticmethod
    def AddIntBinaryOp(name: str, op: BinaryOp):
        NativeFunctionCall.AddOpToNativeFunc(name, 2, ValueType.Int, op)

    @staticmethod
    def AddIntUnaryOp(name: str, op: UnaryOp):
        NativeFunctionCall.AddOpToNativeFunc(name, 1, ValueType.Int, op)

    @staticmethod
    def AddFloatBinaryOp(name: str, op: BinaryOp):
        NativeFunctionCall.AddOpToNativeFunc(name, 2, ValueType.Float, op)

    @staticmethod
    def AddFloatUnaryOp(name: str, op: UnaryOp):
        NativeFunctionCall.AddOpToNativeFunc(name, 1, ValueType.Float, op)

    @staticmethod
    def AddStringBinaryOp(name: str, op: BinaryOp):
        NativeFunctionCall.AddOpToNativeFunc(name, 2, ValueType.String, op)

    @staticmethod
    def AddListBinaryOp(name: str, op: BinaryOp):
        NativeFunctionCall.AddOpToNativeFunc(name, 2, ValueType.List, op)

    @staticmethod
    def AddListUnaryOp(name: str, op: UnaryOp):
        NativeFunctionCall.AddOpToNativeFunc(name, 1, ValueType.List, op)

    def __str__(self):
        return 'Native "' + self.name + '"'
