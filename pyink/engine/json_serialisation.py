from __future__ import annotations

import json
import re
from typing import Dict, List

from .choice import Choice
from .choice_point import ChoicePoint
from .container import Container
from .control_command import ControlCommand
from .divert import Divert
from .glue import Glue
from .ink_list import InkList, InkListItem
from .list_definition import ListDefinition
from .list_definitions_origin import ListDefinitionsOrigin
from .native_function_call import NativeFunctionCall
from .null_exception import throw_null_exception
from .object import InkObject
from .path import Path
from .push_pop import PushPopType
from .simple_json import SimpleJson
from .tag import Tag
from .type_assertion import as_or_null
from .value import (
    BoolValue,
    DivertTargetValue,
    FloatValue,
    IntValue,
    ListValue,
    StringValue,
    Value,
    VariablePointerValue,
)
from .variable_assignment import VariableAssignment
from .variable_reference import VariableReference
from .void import Void


class JsonSerialisation:
    _controlCommandNames = [
        "ev",
        "out",
        "/ev",
        "du",
        "pop",
        "~ret",
        "->->",
        "str",
        "/str",
        "nop",
        "choiceCnt",
        "turn",
        "turns",
        "readc",
        "rnd",
        "srnd",
        "visit",
        "seq",
        "thread",
        "done",
        "end",
        "listInt",
        "range",
        "lrnd",
        "#",
        "/#",
    ]

    @staticmethod
    def JArrayToRuntimeObjList(j_array: List, skip_last: bool = False):
        count = len(j_array)
        if skip_last:
            count -= 1
        result_list: List[InkObject] = []
        for i in range(count):
            j_tok = j_array[i]
            runtime_obj = JsonSerialisation.JTokenToRuntimeObject(j_tok)
            if runtime_obj is None:
                return throw_null_exception("runtimeObj")
            result_list.append(runtime_obj)
        return result_list

    @staticmethod
    def WriteDictionaryRuntimeObjs(writer: SimpleJson.Writer, dictionary: Dict[str, InkObject]):
        writer.WriteObjectStart()
        for key, value in dictionary.items():
            writer.WritePropertyStart(key)
            JsonSerialisation.WriteRuntimeObject(writer, value)
            writer.WritePropertyEnd()
        writer.WriteObjectEnd()

    @staticmethod
    def WriteListRuntimeObjs(writer: SimpleJson.Writer, list_value: List[InkObject]):
        writer.WriteArrayStart()
        for value in list_value:
            JsonSerialisation.WriteRuntimeObject(writer, value)
        writer.WriteArrayEnd()

    @staticmethod
    def WriteIntDictionary(writer: SimpleJson.Writer, dict_value: Dict[str, int]):
        writer.WriteObjectStart()
        for key, value in dict_value.items():
            writer.WriteIntProperty(key, value)
        writer.WriteObjectEnd()

    @staticmethod
    def WriteRuntimeObject(writer: SimpleJson.Writer, obj: InkObject):
        container = as_or_null(obj, Container)
        if container:
            JsonSerialisation.WriteRuntimeContainer(writer, container)
            return

        divert = as_or_null(obj, Divert)
        if divert:
            div_type_key = "->"
            if divert.isExternal:
                div_type_key = "x()"
            elif divert.pushesToStack:
                if divert.stackPushType == PushPopType.Function:
                    div_type_key = "f()"
                elif divert.stackPushType == PushPopType.Tunnel:
                    div_type_key = "->t->"

            if divert.hasVariableTarget:
                target_str = divert.variableDivertName
            else:
                target_str = divert.targetPathString

            writer.WriteObjectStart()
            writer.WriteProperty(div_type_key, target_str)

            if divert.hasVariableTarget:
                writer.WriteProperty("var", True)
            if divert.isConditional:
                writer.WriteProperty("c", True)
            if divert.externalArgs > 0:
                writer.WriteIntProperty("exArgs", divert.externalArgs)
            writer.WriteObjectEnd()
            return

        choice_point = as_or_null(obj, ChoicePoint)
        if choice_point:
            writer.WriteObjectStart()
            writer.WriteProperty("*", choice_point.pathStringOnChoice)
            writer.WriteIntProperty("flg", choice_point.flags)
            writer.WriteObjectEnd()
            return

        bool_val = as_or_null(obj, BoolValue)
        if bool_val:
            writer.WriteBool(bool_val.value)
            return

        int_val = as_or_null(obj, IntValue)
        if int_val:
            writer.WriteInt(int_val.value)
            return

        float_val = as_or_null(obj, FloatValue)
        if float_val:
            writer.WriteFloat(float_val.value)
            return

        str_val = as_or_null(obj, StringValue)
        if str_val:
            if str_val.isNewline:
                writer.Write("\n", False)
            else:
                writer.WriteStringStart()
                writer.WriteStringInner("^")
                writer.WriteStringInner(str_val.value)
                writer.WriteStringEnd()
            return

        list_val = as_or_null(obj, ListValue)
        if list_val:
            JsonSerialisation.WriteInkList(writer, list_val)
            return

        div_target_val = as_or_null(obj, DivertTargetValue)
        if div_target_val:
            writer.WriteObjectStart()
            if div_target_val.value is None:
                return throw_null_exception("divTargetVal.value")
            writer.WriteProperty("^->", div_target_val.value.componentsString)
            writer.WriteObjectEnd()
            return

        var_ptr_val = as_or_null(obj, VariablePointerValue)
        if var_ptr_val:
            writer.WriteObjectStart()
            writer.WriteProperty("^var", var_ptr_val.value)
            writer.WriteIntProperty("ci", var_ptr_val.contextIndex)
            writer.WriteObjectEnd()
            return

        glue = as_or_null(obj, Glue)
        if glue:
            writer.Write("<>")
            return

        control_cmd = as_or_null(obj, ControlCommand)
        if control_cmd:
            writer.Write(JsonSerialisation._controlCommandNames[control_cmd.commandType])
            return

        native_func = as_or_null(obj, NativeFunctionCall)
        if native_func:
            name = native_func.name
            if name == "^":
                name = "L^"
            writer.Write(name)
            return

        var_ref = as_or_null(obj, VariableReference)
        if var_ref:
            writer.WriteObjectStart()
            read_count_path = var_ref.pathStringForCount
            if read_count_path is not None:
                writer.WriteProperty("CNT?", read_count_path)
            else:
                writer.WriteProperty("VAR?", var_ref.name)
            writer.WriteObjectEnd()
            return

        var_ass = as_or_null(obj, VariableAssignment)
        if var_ass:
            writer.WriteObjectStart()
            if var_ass.isGlobal:
                writer.WriteProperty("VAR=", var_ass.variableName)
            else:
                writer.WriteProperty("temp=", var_ass.variableName)
            if var_ass.isNewDeclaration is False:
                writer.WriteProperty("re", True)
            writer.WriteObjectEnd()
            return

        tag = as_or_null(obj, Tag)
        if tag:
            writer.WriteObjectStart()
            writer.WriteProperty("#", tag.text)
            writer.WriteObjectEnd()
            return

        if isinstance(obj, Choice):
            JsonSerialisation.WriteChoice(writer, obj)
            return

        if isinstance(obj, Void):
            writer.Write("void")
            return

        raise ValueError("Failed to convert runtime object to json: " + str(obj))

    @staticmethod
    def WriteInkList(writer: SimpleJson.Writer, list_val: ListValue):
        raw_list = list_val.value
        if raw_list is None:
            return throw_null_exception("rawList")

        writer.WriteObjectStart()
        writer.WritePropertyStart("list")
        writer.WriteObjectStart()
        for key, value in raw_list.items():
            item = InkListItem.fromSerializedKey(key)
            if item.itemName is None:
                return throw_null_exception("item.itemName")
            writer.WritePropertyNameStart()
            writer.WritePropertyNameInner(item.originName if item.originName else "?")
            writer.WritePropertyNameInner(".")
            writer.WritePropertyNameInner(item.itemName)
            writer.WritePropertyNameEnd()
            writer.Write(value)
            writer.WritePropertyEnd()
        writer.WriteObjectEnd()
        writer.WritePropertyEnd()

        if raw_list.Count == 0 and raw_list.originNames and len(raw_list.originNames) > 0:
            writer.WritePropertyStart("origins")
            writer.WriteArrayStart()
            for name in raw_list.originNames:
                writer.Write(name)
            writer.WriteArrayEnd()
            writer.WritePropertyEnd()

        writer.WriteObjectEnd()

    @staticmethod
    def WriteChoice(writer: SimpleJson.Writer, choice: Choice):
        writer.WriteObjectStart()
        writer.WriteProperty("text", choice.text)
        writer.WriteProperty("index", choice.index)
        writer.WriteProperty("originalChoicePath", choice.sourcePath)
        writer.WriteIntProperty("originalThreadIndex", choice.originalThreadIndex)
        writer.WriteProperty("targetPath", choice.pathStringOnChoice)
        writer.WriteProperty("isInvisibleDefault", choice.isInvisibleDefault)
        if choice.tags is not None and len(choice.tags) > 0:
            writer.WritePropertyStart("tags")
            writer.WriteArrayStart()
            for t in choice.tags:
                writer.Write(t)
            writer.WriteArrayEnd()
            writer.WritePropertyEnd()
        writer.WriteObjectEnd()

    @staticmethod
    def JTokenToRuntimeObject(token):
        if isinstance(token, (int, float, bool)):
            return Value.Create(token)

        if isinstance(token, str):
            str_value = str(token)
            float_repr = re.match(r"^([0-9]+\.[0-9]+)f$", str_value)
            if float_repr:
                return FloatValue(float(float_repr.group(1)))

            first_char = str_value[0] if str_value else ""
            if first_char == "^":
                return StringValue(str_value[1:])
            if first_char == "\n" and len(str_value) == 1:
                return StringValue("\n")

            if str_value == "<>":
                return Glue()

            for i, cmd_name in enumerate(JsonSerialisation._controlCommandNames):
                if str_value == cmd_name:
                    return ControlCommand(ControlCommand.CommandType(i))

            if str_value == "L^":
                str_value = "^"
            if NativeFunctionCall.CallExistsWithName(str_value):
                return NativeFunctionCall.CallWithName(str_value)

            if str_value == "->->":
                return ControlCommand.PopTunnel()
            if str_value == "~ret":
                return ControlCommand.PopFunction()
            if str_value == "void":
                return Void()

        if isinstance(token, dict):
            obj = token
            if "^->" in obj:
                prop_value = obj["^->"]
                return DivertTargetValue(Path(str(prop_value)))

            if "^var" in obj:
                prop_value = obj["^var"]
                var_ptr = VariablePointerValue(str(prop_value))
                if "ci" in obj:
                    var_ptr.contextIndex = int(obj["ci"])
                return var_ptr

            is_divert = False
            pushes_to_stack = False
            div_push_type = PushPopType.Function
            external = False
            prop_value = None
            if "->" in obj:
                prop_value = obj["->"]
                is_divert = True
            elif "f()" in obj:
                prop_value = obj["f()"]
                is_divert = True
                pushes_to_stack = True
                div_push_type = PushPopType.Function
            elif "->t->" in obj:
                prop_value = obj["->t->"]
                is_divert = True
                pushes_to_stack = True
                div_push_type = PushPopType.Tunnel
            elif "x()" in obj:
                prop_value = obj["x()"]
                is_divert = True
                external = True

            if is_divert:
                divert = Divert()
                divert.pushesToStack = pushes_to_stack
                divert.stackPushType = div_push_type
                divert.isExternal = external
                target = str(prop_value)
                if "var" in obj:
                    divert.variableDivertName = target
                else:
                    divert.targetPathString = target
                divert.isConditional = bool(obj.get("c"))
                if external and "exArgs" in obj:
                    divert.externalArgs = int(obj["exArgs"])
                return divert

            if "*" in obj:
                choice = ChoicePoint()
                choice.pathStringOnChoice = str(obj["*"])
                if "flg" in obj:
                    choice.flags = int(obj["flg"])
                return choice

            if "VAR?" in obj:
                return VariableReference(str(obj["VAR?"]))
            if "CNT?" in obj:
                read_count_var_ref = VariableReference()
                read_count_var_ref.pathStringForCount = str(obj["CNT?"])
                return read_count_var_ref

            is_var_ass = False
            is_global_var = False
            if "VAR=" in obj:
                prop_value = obj["VAR="]
                is_var_ass = True
                is_global_var = True
            elif "temp=" in obj:
                prop_value = obj["temp="]
                is_var_ass = True
                is_global_var = False
            if is_var_ass:
                var_name = str(prop_value)
                is_new_decl = not obj.get("re")
                var_ass = VariableAssignment(var_name, is_new_decl)
                var_ass.isGlobal = is_global_var
                return var_ass

            if "#" in obj:
                return Tag(str(obj["#"]))

            if "list" in obj:
                list_content = obj["list"]
                raw_list = InkList()
                if "origins" in obj:
                    raw_list.SetInitialOriginNames(obj["origins"])
                for key, name_to_val in list_content.items():
                    item = InkListItem(str(key))
                    val = int(name_to_val)
                    raw_list.Add(item, val)
                return ListValue(raw_list)

            if obj.get("originalChoicePath") is not None:
                return JsonSerialisation.JObjectToChoice(obj)

        if isinstance(token, list):
            return JsonSerialisation.JArrayToContainer(token)

        if token is None:
            return None

        raise ValueError("Failed to convert token to runtime object: " + json.dumps(token))

    @staticmethod
    def JObjectToDictionaryRuntimeObjs(j_object: Dict):
        result = {}
        for key, value in j_object.items():
            ink_object = JsonSerialisation.JTokenToRuntimeObject(value)
            if ink_object is None:
                return throw_null_exception("inkObject")
            result[key] = ink_object
        return result

    @staticmethod
    def JObjectToIntDictionary(j_object: Dict):
        result = {}
        for key, value in j_object.items():
            result[key] = int(value)
        return result

    @staticmethod
    def JObjectToChoice(obj: Dict):
        choice = Choice()
        choice.text = obj.get("text", "")
        choice.index = int(obj.get("index", 0))
        choice.sourcePath = str(obj.get("originalChoicePath", ""))
        choice.originalThreadIndex = int(obj.get("originalThreadIndex", 0))
        choice.pathStringOnChoice = str(obj.get("targetPath", ""))
        choice.tags = obj.get("tags") if obj.get("tags") is not None else None
        choice.isInvisibleDefault = bool(obj.get("isInvisibleDefault"))
        return choice

    @staticmethod
    def JArrayToContainer(j_array: List):
        container = Container()
        container.content = JsonSerialisation.JArrayToRuntimeObjList(j_array, True)
        terminating_obj = j_array[-1] if j_array else None
        if terminating_obj is not None and isinstance(terminating_obj, dict):
            named_only_content = {}
            for key, value in terminating_obj.items():
                if key == "#f":
                    container.countFlags = int(value)
                elif key == "#n":
                    container.name = str(value)
                else:
                    named_content_item = JsonSerialisation.JTokenToRuntimeObject(value)
                    named_sub_container = as_or_null(named_content_item, Container)
                    if named_sub_container:
                        named_sub_container.name = key
                    named_only_content[key] = named_content_item
            container.namedOnlyContent = named_only_content
        return container

    @staticmethod
    def WriteRuntimeContainer(writer: SimpleJson.Writer, container: Container, without_name: bool = False):
        writer.WriteArrayStart()
        if container is None:
            return throw_null_exception("container")
        for content in container.content:
            JsonSerialisation.WriteRuntimeObject(writer, content)

        named_only_content = container.namedOnlyContent
        count_flags = container.countFlags
        has_name_property = container.name is not None and not without_name

        has_terminator = named_only_content is not None or count_flags > 0 or has_name_property
        if has_terminator:
            writer.WriteObjectStart()

        if named_only_content is not None:
            for key, value in named_only_content.items():
                writer.WritePropertyStart(key)
                JsonSerialisation.WriteRuntimeContainer(writer, as_or_null(value, Container), True)
                writer.WritePropertyEnd()

        if count_flags > 0:
            writer.WriteIntProperty("#f", count_flags)
        if has_name_property:
            writer.WriteProperty("#n", container.name)

        if has_terminator:
            writer.WriteObjectEnd()
        else:
            writer.WriteNull()

        writer.WriteArrayEnd()

    @staticmethod
    def toJson(me, removes=None, space=None):
        def remove_keys(obj):
            if not removes:
                return obj
            if isinstance(obj, dict):
                return {k: remove_keys(v) for k, v in obj.items() if k not in removes}
            if isinstance(obj, list):
                return [remove_keys(v) for v in obj]
            return obj

        return json.dumps(remove_keys(me), indent=space)

    @staticmethod
    def ListDefinitionsToJToken(origin: ListDefinitionsOrigin):
        list_defs: Dict[str, Dict[str, int]] = {}
        for list_def in origin.lists:
            list_items = {}
            for key, val in list_def.items.items():
                item = InkListItem.fromSerializedKey(key)
                if item.itemName is None:
                    return throw_null_exception("item.itemName")
                list_items[item.itemName] = val
            list_defs[list_def.name] = list_items
        return list_defs

    @staticmethod
    def JTokenToListDefinitions(obj: Dict):
        definitions: List[ListDefinition] = []
        for key, val in obj.items():
            list_def = ListDefinition(key, val)
            definitions.append(list_def)
        return ListDefinitionsOrigin(definitions)
