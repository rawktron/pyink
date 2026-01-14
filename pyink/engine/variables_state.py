from __future__ import annotations

from typing import Dict, Optional, Set

from .call_stack import CallStack
from .list_definitions_origin import ListDefinitionsOrigin
from .null_exception import throw_null_exception
from .story_exception import StoryException
from .type_assertion import as_or_null, as_or_throws, is_equatable
from .value import (
    AbstractValue,
    BoolValue,
    FloatValue,
    IntValue,
    ListValue,
    Value,
    VariablePointerValue,
)
from .variable_assignment import VariableAssignment
from .json_serialisation import JsonSerialisation
from .simple_json import SimpleJson
from .try_get_result import try_get_value_from_map


class VariablesState:
    dontSaveDefaultValues = True

    def __init__(self, call_stack: CallStack, list_defs_origin: Optional[ListDefinitionsOrigin]):
        self.variableChangedEventCallbacks = []
        self.patch = None
        self._globalVariables: Dict[str, Value] = {}
        self._defaultGlobalVariables: Dict[str, Value] = {}
        self._callStack = call_stack
        self._listDefsOrigin = list_defs_origin
        self._batchObservingVariableChanges = False
        self._changedVariablesForBatchObs: Optional[Set[str]] = set()

    def variableChangedEvent(self, variable_name: str, new_value):
        for callback in self.variableChangedEventCallbacks:
            callback(variable_name, new_value)

    def StartVariableObservation(self):
        self._batchObservingVariableChanges = True
        self._changedVariablesForBatchObs = set()

    def CompleteVariableObservation(self):
        self._batchObservingVariableChanges = False
        changed_vars = {}
        if self._changedVariablesForBatchObs is not None:
            for variable_name in self._changedVariablesForBatchObs:
                current_value = self._globalVariables.get(variable_name)
                self.variableChangedEvent(variable_name, current_value)
        if self.patch is not None:
            for variable_name in self.patch.changedVariables:
                patched_val = self.patch.TryGetGlobal(variable_name, None)
                if patched_val.exists:
                    changed_vars[variable_name] = patched_val
        self._changedVariablesForBatchObs = None
        return changed_vars

    def NotifyObservers(self, changed_vars):
        for key, value in changed_vars.items():
            self.variableChangedEvent(key, value)

    @property
    def callStack(self):
        return self._callStack

    @callStack.setter
    def callStack(self, call_stack):
        self._callStack = call_stack

    def get(self, variable_name: str):
        var_contents = None
        if self.patch is not None:
            var_contents = self.patch.TryGetGlobal(variable_name, None)
            if var_contents.exists:
                return var_contents.result.valueObject
        var_contents = self._globalVariables.get(variable_name)
        if var_contents is None:
            var_contents = self._defaultGlobalVariables.get(variable_name)
        if var_contents is not None:
            return var_contents.valueObject
        return None

    def set(self, variable_name: str, value):
        if variable_name not in self._defaultGlobalVariables:
            raise StoryException(
                "Cannot assign to a variable (" + variable_name + ") that hasn't been declared in the story"
            )
        val = Value.Create(value)
        if val is None:
            if value is None:
                raise ValueError("Cannot pass null to VariableState")
            raise ValueError("Invalid value passed to VariableState: " + str(value))
        self.SetGlobal(variable_name, val)

    def __getitem__(self, variable_name: str):
        return self.get(variable_name)

    def __setitem__(self, variable_name: str, value):
        self.set(variable_name, value)

    def ApplyPatch(self):
        if self.patch is None:
            return throw_null_exception("this.patch")
        for named_var_key, named_var_value in self.patch.globals.items():
            self._globalVariables[named_var_key] = named_var_value
        if self._changedVariablesForBatchObs is not None:
            for name in self.patch.changedVariables:
                self._changedVariablesForBatchObs.add(name)
        self.patch = None

    def SetJsonToken(self, j_token: Dict):
        self._globalVariables.clear()
        for var_val_key, var_val_value in self._defaultGlobalVariables.items():
            loaded_token = j_token.get(var_val_key)
            if loaded_token is not None:
                token_ink_object = JsonSerialisation.JTokenToRuntimeObject(loaded_token)
                if token_ink_object is None:
                    return throw_null_exception("tokenInkObject")
                self._globalVariables[var_val_key] = token_ink_object
            else:
                self._globalVariables[var_val_key] = var_val_value

    def WriteJson(self, writer: SimpleJson.Writer):
        writer.WriteObjectStart()
        for name, val in self._globalVariables.items():
            if VariablesState.dontSaveDefaultValues and name in self._defaultGlobalVariables:
                default_val = self._defaultGlobalVariables.get(name)
                if self.RuntimeObjectsEqual(val, default_val):
                    continue
            writer.WritePropertyStart(name)
            JsonSerialisation.WriteRuntimeObject(writer, val)
            writer.WritePropertyEnd()
        writer.WriteObjectEnd()

    def RuntimeObjectsEqual(self, obj1, obj2) -> bool:
        if obj1 is None:
            return throw_null_exception("obj1")
        if obj2 is None:
            return throw_null_exception("obj2")
        if obj1.__class__ is not obj2.__class__:
            return False
        bool_val = as_or_null(obj1, BoolValue)
        if bool_val is not None:
            return bool_val.value == as_or_throws(obj2, BoolValue).value
        int_val = as_or_null(obj1, IntValue)
        if int_val is not None:
            return int_val.value == as_or_throws(obj2, IntValue).value
        float_val = as_or_null(obj1, FloatValue)
        if float_val is not None:
            return float_val.value == as_or_throws(obj2, FloatValue).value
        val1 = as_or_null(obj1, Value)
        val2 = as_or_null(obj2, Value)
        if val1 is not None and val2 is not None:
            if is_equatable(val1.valueObject) and is_equatable(val2.valueObject):
                return val1.valueObject.Equals(val2.valueObject)
            return val1.valueObject == val2.valueObject
        raise ValueError("FastRoughDefinitelyEquals: Unsupported runtime object type: " + obj1.__class__.__name__)

    def GetVariableWithName(self, name: Optional[str], context_index: int = -1):
        var_value = self.GetRawVariableWithName(name, context_index)
        var_pointer = as_or_null(var_value, VariablePointerValue)
        if var_pointer is not None:
            var_value = self.ValueAtVariablePointer(var_pointer)
        return var_value

    def TryGetDefaultVariableValue(self, name: Optional[str]):
        val = try_get_value_from_map(self._defaultGlobalVariables, name, None)
        return val.result if val.exists else None

    def GlobalVariableExistsWithName(self, name: str):
        return name in self._globalVariables or name in self._defaultGlobalVariables

    def GetRawVariableWithName(self, name: Optional[str], context_index: int):
        if context_index in (0, -1):
            if self.patch is not None:
                variable_value = self.patch.TryGetGlobal(name, None)
                if variable_value.exists:
                    return variable_value.result
            variable_value = try_get_value_from_map(self._globalVariables, name, None)
            if variable_value.exists:
                return variable_value.result
            variable_value = try_get_value_from_map(self._defaultGlobalVariables, name, None)
            if variable_value.exists:
                return variable_value.result
            if self._listDefsOrigin is None:
                return throw_null_exception("VariablesState._listDefsOrigin")
            list_item_value = self._listDefsOrigin.FindSingleItemListWithName(name)
            if list_item_value:
                return list_item_value

        return self._callStack.GetTemporaryVariableWithName(name, context_index)

    def ValueAtVariablePointer(self, pointer: VariablePointerValue):
        return self.GetVariableWithName(pointer.variableName, pointer.contextIndex)

    def Assign(self, var_ass: VariableAssignment, value):
        name = var_ass.variableName
        if name is None:
            return throw_null_exception("name")
        context_index = -1
        set_global = False
        if var_ass.isNewDeclaration:
            set_global = var_ass.isGlobal
        else:
            set_global = self.GlobalVariableExistsWithName(name)

        if var_ass.isNewDeclaration:
            var_pointer = as_or_null(value, VariablePointerValue)
            if var_pointer is not None:
                value = self.ResolveVariablePointer(var_pointer)
        else:
            existing_pointer = None
            while True:
                existing_pointer = as_or_null(self.GetRawVariableWithName(name, context_index), VariablePointerValue)
                if existing_pointer is not None:
                    name = existing_pointer.variableName
                    context_index = existing_pointer.contextIndex
                    set_global = context_index == 0
                else:
                    break

        if set_global:
            self.SetGlobal(name, value)
        else:
            self._callStack.SetTemporaryVariable(name, value, var_ass.isNewDeclaration, context_index)

    def SnapshotDefaultGlobals(self):
        self._defaultGlobalVariables = dict(self._globalVariables)

    def RetainListOriginsForAssignment(self, old_value, new_value):
        old_list = as_or_throws(old_value, ListValue)
        new_list = as_or_throws(new_value, ListValue)
        if old_list.value and new_list.value and new_list.value.Count == 0:
            new_list.value.SetInitialOriginNames(old_list.value.originNames)

    def SetGlobal(self, variable_name: Optional[str], value):
        old_value = None
        if self.patch is None:
            old_value = try_get_value_from_map(self._globalVariables, variable_name, None)
        if self.patch is not None:
            old_value = self.patch.TryGetGlobal(variable_name, None)
            if not old_value.exists:
                old_value = try_get_value_from_map(self._globalVariables, variable_name, None)
        ListValue.RetainListOriginsForAssignment(old_value.result, value)
        if variable_name is None:
            return throw_null_exception("variableName")
        if self.patch is not None:
            self.patch.SetGlobal(variable_name, value)
        else:
            self._globalVariables[variable_name] = value

        if old_value is not None and value is not old_value.result:
            if self._batchObservingVariableChanges:
                if self._changedVariablesForBatchObs is None:
                    return throw_null_exception("this._changedVariablesForBatchObs")
                if self.patch is not None:
                    self.patch.AddChangedVariable(variable_name)
                else:
                    self._changedVariablesForBatchObs.add(variable_name)
            else:
                self.variableChangedEvent(variable_name, value)

    def ResolveVariablePointer(self, var_pointer: VariablePointerValue):
        context_index = var_pointer.contextIndex
        if context_index == -1:
            context_index = self.GetContextIndexOfVariableNamed(var_pointer.variableName)

        value_of_variable_pointed_to = self.GetRawVariableWithName(var_pointer.variableName, context_index)
        double_redirection_pointer = as_or_null(value_of_variable_pointed_to, VariablePointerValue)
        if double_redirection_pointer is not None:
            return double_redirection_pointer
        return VariablePointerValue(var_pointer.variableName, context_index)

    def GetContextIndexOfVariableNamed(self, var_name: str):
        if self.GlobalVariableExistsWithName(var_name):
            return 0
        return self._callStack.currentElementIndex

    def ObserveVariableChange(self, callback):
        self.variableChangedEventCallbacks.append(callback)
