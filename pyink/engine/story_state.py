from __future__ import annotations

from typing import Dict, List, Optional

from .call_stack import CallStack
from .choice import Choice
from .container import Container
from .control_command import ControlCommand
from .glue import Glue
from .ink_list import InkList
from .json_serialisation import JsonSerialisation
from .null_exception import throw_null_exception
from .path import Path
from .pointer import Pointer
from .prng import PRNG
from .push_pop import PushPopType
from .simple_json import SimpleJson
from .state_patch import StatePatch
from .string_builder import StringBuilder
from .tag import Tag
from .try_get_result import try_get_value_from_map
from .type_assertion import as_or_null, as_or_throws, null_if_undefined
from .value import ListValue, StringValue, Value, ValueType
from .variables_state import VariablesState
from .void import Void
from .flow import Flow


class StoryState:
    kInkSaveStateVersion = 10
    kMinCompatibleLoadVersion = 8

    def __init__(self, story):
        self.onDidLoadState = None
        self.story = story

        self._currentFlow = Flow(self.kDefaultFlowName, story)
        self.OutputStreamDirty()

        self._aliveFlowNamesDirty = True
        self._evaluationStack: List = []

        self._variablesState = VariablesState(self.callStack, story.listDefinitions)

        self._visitCounts: Dict[str, int] = {}
        self._turnIndices: Dict[str, int] = {}
        self._currentTurnIndex = -1

        time_seed = PRNG(int(__import__("time").time() * 1000)).next() % 100
        self.storySeed = time_seed
        self.previousRandom = 0
        self.didSafeExit = False

        self.divertedPointer = Pointer.Null()
        self._currentErrors: Optional[List[str]] = None
        self._currentWarnings: Optional[List[str]] = None
        self._currentText = None
        self._currentTags = None
        self._outputStreamTextDirty = True
        self._outputStreamTagsDirty = True
        self._patch: Optional[StatePatch] = None
        self._aliveFlowNames = None
        self._namedFlows = None

        self.GoToStart()

    def ToJson(self, indented: bool = False):
        writer = SimpleJson.Writer()
        self.WriteJson(writer)
        return writer.toString()

    def toJson(self, indented: bool = False):
        return self.ToJson(indented)

    def LoadJson(self, json_text: str):
        j_object = SimpleJson.TextToDictionary(json_text)
        self.LoadJsonObj(j_object)
        if self.onDidLoadState is not None:
            self.onDidLoadState()

    def VisitCountAtPathString(self, path_string: str):
        if self._patch is not None:
            container = self.story.ContentAtPath(Path(path_string)).container
            if container is None:
                raise ValueError("Content at path not found: " + path_string)
            visit_count_out = self._patch.TryGetVisitCount(container, 0)
            if visit_count_out.exists:
                return visit_count_out.result

        visit_count_out = try_get_value_from_map(self._visitCounts, path_string, None)
        if visit_count_out.exists:
            return visit_count_out.result
        return 0

    def VisitCountForContainer(self, container: Container):
        if container is None:
            return throw_null_exception("container")
        if not container.visitsShouldBeCounted:
            self.story.Error(
                "Read count for target ("
                + str(container.name)
                + " - on "
                + str(container.debugMetadata)
                + ") unknown. The story may need to be compiled with countAllVisits flag (-c)."
            )
            return 0

        if self._patch is not None:
            count = self._patch.TryGetVisitCount(container, 0)
            if count.exists:
                return count.result

        container_path_str = container.path.toString()
        count2 = try_get_value_from_map(self._visitCounts, container_path_str, None)
        if count2.exists:
            return count2.result
        return 0

    def IncrementVisitCountForContainer(self, container: Container):
        if self._patch is not None:
            curr_count = self.VisitCountForContainer(container)
            curr_count += 1
            self._patch.SetVisitCount(container, curr_count)
            return

        container_path_str = container.path.toString()
        count = try_get_value_from_map(self._visitCounts, container_path_str, None)
        if count.exists:
            self._visitCounts[container_path_str] = count.result + 1
        else:
            self._visitCounts[container_path_str] = 1

    def RecordTurnIndexVisitToContainer(self, container: Container):
        if self._patch is not None:
            self._patch.SetTurnIndex(container, self.currentTurnIndex)
            return
        container_path_str = container.path.toString()
        self._turnIndices[container_path_str] = self.currentTurnIndex

    def TurnsSinceForContainer(self, container: Container):
        if not container.turnIndexShouldBeCounted:
            self.story.Error(
                "TURNS_SINCE() for target ("
                + str(container.name)
                + " - on "
                + str(container.debugMetadata)
                + ") unknown. The story may need to be compiled with countAllVisits flag (-c)."
            )
        if self._patch is not None:
            index = self._patch.TryGetTurnIndex(container, 0)
            if index.exists:
                return self.currentTurnIndex - index.result
        container_path_str = container.path.toString()
        index2 = try_get_value_from_map(self._turnIndices, container_path_str, 0)
        if index2.exists:
            return self.currentTurnIndex - index2.result
        return -1

    @property
    def callstackDepth(self):
        return self.callStack.depth

    @property
    def outputStream(self):
        return self._currentFlow.outputStream

    @property
    def currentChoices(self):
        if self.canContinue:
            return []
        return self._currentFlow.currentChoices

    @property
    def generatedChoices(self):
        return self._currentFlow.currentChoices

    @property
    def currentErrors(self):
        return self._currentErrors

    @property
    def currentWarnings(self):
        return self._currentWarnings

    @property
    def variablesState(self):
        return self._variablesState

    @variablesState.setter
    def variablesState(self, value):
        self._variablesState = value

    @property
    def callStack(self):
        return self._currentFlow.callStack

    @property
    def evaluationStack(self):
        return self._evaluationStack

    @property
    def currentTurnIndex(self):
        return self._currentTurnIndex

    @currentTurnIndex.setter
    def currentTurnIndex(self, value):
        self._currentTurnIndex = value

    @property
    def currentPathString(self):
        pointer = self.currentPointer
        if pointer.isNull:
            return None
        if pointer.path is None:
            return throw_null_exception("pointer.path")
        return pointer.path.toString()

    @property
    def previousPathString(self):
        pointer = self.previousPointer
        if pointer.isNull:
            return None
        if pointer.path is None:
            return throw_null_exception("previousPointer.path")
        return pointer.path.toString()

    @property
    def currentPointer(self):
        return self.callStack.currentElement.currentPointer.copy()

    @currentPointer.setter
    def currentPointer(self, value: Pointer):
        self.callStack.currentElement.currentPointer = value.copy()

    @property
    def previousPointer(self):
        return self.callStack.currentThread.previousPointer.copy()

    @previousPointer.setter
    def previousPointer(self, value: Pointer):
        self.callStack.currentThread.previousPointer = value.copy()

    @property
    def canContinue(self):
        return not self.currentPointer.isNull and not self.hasError

    @property
    def hasError(self):
        return self.currentErrors is not None and len(self.currentErrors) > 0

    @property
    def hasWarning(self):
        return self.currentWarnings is not None and len(self.currentWarnings) > 0

    @property
    def currentText(self):
        if self._outputStreamTextDirty:
            sb = StringBuilder()
            in_tag = False
            for output_obj in self.outputStream:
                text_content = as_or_null(output_obj, StringValue)
                if not in_tag and text_content is not None:
                    sb.Append(text_content.value)
                else:
                    control_command = as_or_null(output_obj, ControlCommand)
                    if control_command is not None:
                        if control_command.commandType == ControlCommand.CommandType.BeginTag:
                            in_tag = True
                        elif control_command.commandType == ControlCommand.CommandType.EndTag:
                            in_tag = False
            self._currentText = self.CleanOutputWhitespace(str(sb))
            self._outputStreamTextDirty = False
        return self._currentText

    def CleanOutputWhitespace(self, text: str):
        sb = StringBuilder()
        current_whitespace_start = -1
        start_of_line = 0
        for i, char in enumerate(text):
            is_inline_whitespace = char in (" ", "\t")
            if is_inline_whitespace and current_whitespace_start == -1:
                current_whitespace_start = i
            if not is_inline_whitespace:
                if char != "\n" and current_whitespace_start > 0 and current_whitespace_start != start_of_line:
                    sb.Append(" ")
                current_whitespace_start = -1
            if char == "\n":
                start_of_line = i + 1
            if not is_inline_whitespace:
                sb.Append(char)
        return str(sb)

    @property
    def currentTags(self):
        if self._outputStreamTagsDirty:
            self._currentTags = []
            in_tag = False
            sb = StringBuilder()
            for output_obj in self.outputStream:
                control_command = as_or_null(output_obj, ControlCommand)
                if control_command is not None:
                    if control_command.commandType == ControlCommand.CommandType.BeginTag:
                        if in_tag and sb.Length > 0:
                            txt = self.CleanOutputWhitespace(str(sb))
                            self._currentTags.append(txt)
                            sb.Clear()
                        in_tag = True
                    elif control_command.commandType == ControlCommand.CommandType.EndTag:
                        if sb.Length > 0:
                            txt = self.CleanOutputWhitespace(str(sb))
                            self._currentTags.append(txt)
                            sb.Clear()
                        in_tag = False
                elif in_tag:
                    str_val = as_or_null(output_obj, StringValue)
                    if str_val is not None:
                        sb.Append(str_val.value)
                else:
                    tag = as_or_null(output_obj, Tag)
                    if tag is not None and tag.text is not None and len(tag.text) > 0:
                        self._currentTags.append(tag.text)

            if sb.Length > 0:
                txt = self.CleanOutputWhitespace(str(sb))
                self._currentTags.append(txt)
                sb.Clear()

            self._outputStreamTagsDirty = False
        return self._currentTags

    @property
    def currentFlowName(self):
        return self._currentFlow.name

    @property
    def currentFlowIsDefaultFlow(self):
        return self._currentFlow.name == self.kDefaultFlowName

    @property
    def aliveFlowNames(self):
        if self._aliveFlowNamesDirty:
            self._aliveFlowNames = []
            if self._namedFlows is not None:
                for flow_name in self._namedFlows.keys():
                    if flow_name != self.kDefaultFlowName:
                        self._aliveFlowNames.append(flow_name)
            self._aliveFlowNamesDirty = False
        return self._aliveFlowNames

    @property
    def inExpressionEvaluation(self):
        return self.callStack.currentElement.inExpressionEvaluation

    @inExpressionEvaluation.setter
    def inExpressionEvaluation(self, value: bool):
        self.callStack.currentElement.inExpressionEvaluation = value

    def GoToStart(self):
        self.callStack.currentElement.currentPointer = Pointer.StartOf(self.story.mainContentContainer)

    def SwitchFlow_Internal(self, flow_name: str):
        if flow_name is None:
            raise ValueError("Must pass a non-null string to Story.SwitchFlow")
        if self._namedFlows is None:
            self._namedFlows = {self.kDefaultFlowName: self._currentFlow}
        if flow_name == self._currentFlow.name:
            return
        flow = self._namedFlows.get(flow_name)
        if flow is None:
            flow = Flow(flow_name, self.story)
            self._namedFlows[flow_name] = flow
            self._aliveFlowNamesDirty = True
        self._currentFlow = flow
        self.variablesState.callStack = self._currentFlow.callStack
        self.OutputStreamDirty()

    def SwitchToDefaultFlow_Internal(self):
        if self._namedFlows is None:
            return
        self.SwitchFlow_Internal(self.kDefaultFlowName)

    def RemoveFlow_Internal(self, flow_name: str):
        if flow_name is None:
            raise ValueError("Must pass a non-null string to Story.DestroyFlow")
        if flow_name == self.kDefaultFlowName:
            raise ValueError("Cannot destroy default flow")
        if self._currentFlow.name == flow_name:
            self.SwitchToDefaultFlow_Internal()
        if self._namedFlows is None:
            return throw_null_exception("this._namedFlows")
        if flow_name in self._namedFlows:
            del self._namedFlows[flow_name]
            self._aliveFlowNamesDirty = True

    def CopyAndStartPatching(self, for_background_save: bool):
        copy = StoryState(self.story)
        copy._patch = StatePatch(self._patch)

        copy._currentFlow.name = self._currentFlow.name
        copy._currentFlow.callStack = CallStack(to_copy=self._currentFlow.callStack)
        copy._currentFlow.outputStream.extend(self._currentFlow.outputStream)
        copy.OutputStreamDirty()

        if for_background_save:
            for choice in self._currentFlow.currentChoices:
                copy._currentFlow.currentChoices.append(choice.Clone())
        else:
            copy._currentFlow.currentChoices.extend(self._currentFlow.currentChoices)

        if self._namedFlows is not None:
            copy._namedFlows = {}
            for named_flow_key, named_flow_value in self._namedFlows.items():
                copy._namedFlows[named_flow_key] = named_flow_value
                copy._aliveFlowNamesDirty = True
            copy._namedFlows[self._currentFlow.name] = copy._currentFlow

        if self.hasError:
            copy._currentErrors = []
            copy._currentErrors.extend(self.currentErrors or [])

        if self.hasWarning:
            copy._currentWarnings = []
            copy._currentWarnings.extend(self.currentWarnings or [])

        copy.variablesState = self.variablesState
        copy.variablesState.callStack = copy.callStack
        copy.variablesState.patch = copy._patch

        copy.evaluationStack.extend(self.evaluationStack)

        if not self.divertedPointer.isNull:
            copy.divertedPointer = self.divertedPointer.copy()

        copy.previousPointer = self.previousPointer.copy()

        copy._visitCounts = self._visitCounts
        copy._turnIndices = self._turnIndices
        copy.currentTurnIndex = self.currentTurnIndex
        copy.storySeed = self.storySeed
        copy.previousRandom = self.previousRandom
        copy.didSafeExit = self.didSafeExit
        return copy

    def RestoreAfterPatch(self):
        self.variablesState.callStack = self.callStack
        self.variablesState.patch = self._patch

    def ApplyAnyPatch(self):
        if self._patch is None:
            return
        self.variablesState.ApplyPatch()
        for key, value in self._patch.visitCounts.items():
            self.ApplyCountChanges(key, value, True)
        for key, value in self._patch.turnIndices.items():
            self.ApplyCountChanges(key, value, False)
        self._patch = None

    def ApplyCountChanges(self, container: Container, new_count: int, is_visit: bool):
        counts = self._visitCounts if is_visit else self._turnIndices
        counts[container.path.toString()] = new_count

    def WriteJson(self, writer: SimpleJson.Writer):
        writer.WriteObjectStart()

        writer.WritePropertyStart("flows")
        writer.WriteObjectStart()

        if self._namedFlows is not None:
            for named_flow_key, named_flow_value in self._namedFlows.items():
                writer.WriteProperty(named_flow_key, lambda w, f=named_flow_value: f.WriteJson(w))
        else:
            writer.WriteProperty(self._currentFlow.name, lambda w: self._currentFlow.WriteJson(w))

        writer.WriteObjectEnd()
        writer.WritePropertyEnd()

        writer.WriteProperty("currentFlowName", self._currentFlow.name)
        writer.WriteProperty("variablesState", lambda w: self.variablesState.WriteJson(w))
        writer.WriteProperty("evalStack", lambda w: JsonSerialisation.WriteListRuntimeObjs(w, self.evaluationStack))

        if not self.divertedPointer.isNull:
            if self.divertedPointer.path is None:
                return throw_null_exception("divertedPointer")
            writer.WriteProperty("currentDivertTarget", self.divertedPointer.path.componentsString)

        writer.WriteProperty("visitCounts", lambda w: JsonSerialisation.WriteIntDictionary(w, self._visitCounts))
        writer.WriteProperty("turnIndices", lambda w: JsonSerialisation.WriteIntDictionary(w, self._turnIndices))

        writer.WriteIntProperty("turnIdx", self.currentTurnIndex)
        writer.WriteIntProperty("storySeed", self.storySeed)
        writer.WriteIntProperty("previousRandom", self.previousRandom)

        writer.WriteIntProperty("inkSaveVersion", self.kInkSaveStateVersion)
        writer.WriteIntProperty("inkFormatVersion", self.story.inkVersionCurrent)
        writer.WriteObjectEnd()

    def LoadJsonObj(self, value: Dict):
        j_object = value
        j_save_version = j_object.get("inkSaveVersion")
        if j_save_version is None:
            raise ValueError("ink save format incorrect, can't load.")
        if int(j_save_version) < self.kMinCompatibleLoadVersion:
            raise ValueError(
                "Ink save format isn't compatible with the current version (saw '"
                + str(j_save_version)
                + "', but minimum is "
                + str(self.kMinCompatibleLoadVersion)
                + "), so can't load."
            )

        flows_obj = j_object.get("flows")
        if flows_obj is not None:
            flows_obj_dict = flows_obj
            if len(flows_obj_dict.keys()) == 1:
                self._namedFlows = None
            elif self._namedFlows is None:
                self._namedFlows = {}
            else:
                self._namedFlows.clear()

            for named_flow_obj_key, named_flow_obj_value in flows_obj_dict.items():
                name = named_flow_obj_key
                flow_obj = named_flow_obj_value
                flow = Flow(name, self.story, flow_obj)
                if len(flows_obj_dict.keys()) == 1:
                    self._currentFlow = Flow(name, self.story, flow_obj)
                else:
                    self._namedFlows[name] = flow

            if self._namedFlows is not None and len(self._namedFlows) > 1:
                curr_flow_name = j_object.get("currentFlowName")
                self._currentFlow = self._namedFlows.get(curr_flow_name)
        else:
            self._namedFlows = None
            self._currentFlow.name = self.kDefaultFlowName
            self._currentFlow.callStack.SetJsonToken(j_object.get("callstackThreads"), self.story)
            self._currentFlow.outputStream = JsonSerialisation.JArrayToRuntimeObjList(j_object.get("outputStream", []))
            self._currentFlow.currentChoices = JsonSerialisation.JArrayToRuntimeObjList(
                j_object.get("currentChoices", [])
            )
            j_choice_threads_obj = j_object.get("choiceThreads")
            self._currentFlow.LoadFlowChoiceThreads(j_choice_threads_obj, self.story)

        self.OutputStreamDirty()
        self._aliveFlowNamesDirty = True

        self.variablesState.SetJsonToken(j_object.get("variablesState"))
        self.variablesState.callStack = self._currentFlow.callStack

        self._evaluationStack = JsonSerialisation.JArrayToRuntimeObjList(j_object.get("evalStack"))

        current_divert_target_path = j_object.get("currentDivertTarget")
        if current_divert_target_path is not None:
            divert_path = Path(str(current_divert_target_path))
            self.divertedPointer = self.story.PointerAtPath(divert_path)

        self._visitCounts = JsonSerialisation.JObjectToIntDictionary(j_object.get("visitCounts"))
        self._turnIndices = JsonSerialisation.JObjectToIntDictionary(j_object.get("turnIndices"))
        self.currentTurnIndex = int(j_object.get("turnIdx"))
        self.storySeed = int(j_object.get("storySeed"))
        self.previousRandom = int(j_object.get("previousRandom"))

    def ResetErrors(self):
        self._currentErrors = None
        self._currentWarnings = None

    def ResetOutput(self, objs: Optional[List] = None):
        self.outputStream.clear()
        if objs is not None:
            self.outputStream.extend(objs)
        self.OutputStreamDirty()

    def PushToOutputStream(self, obj):
        text = as_or_null(obj, StringValue)
        if text is not None:
            list_text = self.TrySplittingHeadTailWhitespace(text)
            if list_text is not None:
                for text_obj in list_text:
                    self.PushToOutputStreamIndividual(text_obj)
                self.OutputStreamDirty()
                return
        self.PushToOutputStreamIndividual(obj)
        self.OutputStreamDirty()

    def PopFromOutputStream(self, count: int):
        del self.outputStream[-count:]
        self.OutputStreamDirty()

    def TrySplittingHeadTailWhitespace(self, single: StringValue):
        str_val = single.value
        if str_val is None:
            return throw_null_exception("single.value")

        head_first_newline_idx = -1
        head_last_newline_idx = -1
        for i, c in enumerate(str_val):
            if c == "\n":
                if head_first_newline_idx == -1:
                    head_first_newline_idx = i
                head_last_newline_idx = i
            elif c in (" ", "\t"):
                continue
            else:
                break

        tail_last_newline_idx = -1
        tail_first_newline_idx = -1
        for i in range(len(str_val) - 1, -1, -1):
            c = str_val[i]
            if c == "\n":
                if tail_last_newline_idx == -1:
                    tail_last_newline_idx = i
                tail_first_newline_idx = i
            elif c in (" ", "\t"):
                continue
            else:
                break

        if head_first_newline_idx == -1 and tail_last_newline_idx == -1:
            return None

        list_texts: List[StringValue] = []
        inner_str_start = 0
        inner_str_end = len(str_val)

        if head_first_newline_idx != -1:
            if head_first_newline_idx > 0:
                leading_spaces = StringValue(str_val[:head_first_newline_idx])
                list_texts.append(leading_spaces)
            list_texts.append(StringValue("\n"))
            inner_str_start = head_last_newline_idx + 1

        if tail_last_newline_idx != -1:
            inner_str_end = tail_first_newline_idx

        if inner_str_end > inner_str_start:
            inner_str_text = str_val[inner_str_start:inner_str_end]
            list_texts.append(StringValue(inner_str_text))

        if tail_last_newline_idx != -1 and tail_first_newline_idx > head_last_newline_idx:
            list_texts.append(StringValue("\n"))
            if tail_last_newline_idx < len(str_val) - 1:
                trailing_spaces = StringValue(str_val[tail_last_newline_idx + 1 :])
                list_texts.append(trailing_spaces)

        return list_texts

    def PushToOutputStreamIndividual(self, obj):
        glue = as_or_null(obj, Glue)
        text = as_or_null(obj, StringValue)

        include_in_output = True
        if glue:
            self.TrimNewlinesFromOutputStream()
            include_in_output = True
        elif text:
            function_trim_index = -1
            curr_el = self.callStack.currentElement
            if curr_el.type == PushPopType.Function:
                function_trim_index = curr_el.functionStartInOutputStream

            glue_trim_index = -1
            for i in range(len(self.outputStream) - 1, -1, -1):
                o = self.outputStream[i]
                c = o if isinstance(o, ControlCommand) else None
                g = o if isinstance(o, Glue) else None
                if g is not None:
                    glue_trim_index = i
                    break
                if c is not None and c.commandType == ControlCommand.CommandType.BeginString:
                    if i >= function_trim_index:
                        function_trim_index = -1
                    break

            trim_index = -1
            if glue_trim_index != -1 and function_trim_index != -1:
                trim_index = min(function_trim_index, glue_trim_index)
            elif glue_trim_index != -1:
                trim_index = glue_trim_index
            else:
                trim_index = function_trim_index

            if trim_index != -1:
                if text.isNewline:
                    include_in_output = False
                elif text.isNonWhitespace:
                    if glue_trim_index > -1:
                        self.RemoveExistingGlue()
                    if function_trim_index > -1:
                        call_stack_elements = self.callStack.elements
                        for i in range(len(call_stack_elements) - 1, -1, -1):
                            el = call_stack_elements[i]
                            if el.type == PushPopType.Function:
                                el.functionStartInOutputStream = -1
                            else:
                                break
            elif text.isNewline:
                if self.outputStreamEndsInNewline or not self.outputStreamContainsContent:
                    include_in_output = False

        if include_in_output:
            if obj is None:
                return throw_null_exception("obj")
            self.outputStream.append(obj)
            self.OutputStreamDirty()

    def TrimNewlinesFromOutputStream(self):
        remove_whitespace_from = -1
        i = len(self.outputStream) - 1
        while i >= 0:
            obj = self.outputStream[i]
            cmd = as_or_null(obj, ControlCommand)
            txt = as_or_null(obj, StringValue)
            if cmd is not None or (txt is not None and txt.isNonWhitespace):
                break
            if txt is not None and txt.isNewline:
                remove_whitespace_from = i
            i -= 1

        if remove_whitespace_from >= 0:
            i = remove_whitespace_from
            while i < len(self.outputStream):
                text = as_or_null(self.outputStream[i], StringValue)
                if text is not None:
                    self.outputStream.pop(i)
                else:
                    i += 1
        self.OutputStreamDirty()

    def RemoveExistingGlue(self):
        for i in range(len(self.outputStream) - 1, -1, -1):
            c = self.outputStream[i]
            if isinstance(c, Glue):
                self.outputStream.pop(i)
            elif isinstance(c, ControlCommand):
                break
        self.OutputStreamDirty()

    @property
    def outputStreamEndsInNewline(self):
        if len(self.outputStream) > 0:
            for i in range(len(self.outputStream) - 1, -1, -1):
                obj = self.outputStream[i]
                if isinstance(obj, ControlCommand):
                    break
                if isinstance(obj, StringValue):
                    if obj.isNewline:
                        return True
                    if obj.isNonWhitespace:
                        break
        return False

    @property
    def outputStreamContainsContent(self):
        return any(isinstance(content, StringValue) for content in self.outputStream)

    @property
    def inStringEvaluation(self):
        for i in range(len(self.outputStream) - 1, -1, -1):
            cmd = as_or_null(self.outputStream[i], ControlCommand)
            if cmd is not None and cmd.commandType == ControlCommand.CommandType.BeginString:
                return True
        return False

    def PushEvaluationStack(self, obj):
        list_value = as_or_null(obj, ListValue)
        if list_value:
            raw_list = list_value.value
            if raw_list is None:
                return throw_null_exception("rawList")
            if raw_list.originNames is not None:
                if not raw_list.origins:
                    raw_list.origins = []
                raw_list.origins.clear()
                for n in raw_list.originNames:
                    if self.story.listDefinitions is None:
                        return throw_null_exception("StoryState.story.listDefinitions")
                    definition = self.story.listDefinitions.TryListGetDefinition(n, None)
                    if definition.result is None:
                        return throw_null_exception("StoryState def.result")
                    if definition.result not in raw_list.origins:
                        raw_list.origins.append(definition.result)

        if obj is None:
            return throw_null_exception("obj")
        self.evaluationStack.append(obj)

    def PopEvaluationStack(self, number_of_objects: Optional[int] = None):
        if number_of_objects is None:
            obj = self.evaluationStack.pop() if self.evaluationStack else None
            return null_if_undefined(obj)
        if number_of_objects > len(self.evaluationStack):
            raise ValueError("trying to pop too many objects")
        popped = self.evaluationStack[-number_of_objects:]
        del self.evaluationStack[-number_of_objects:]
        return null_if_undefined(popped)

    def PeekEvaluationStack(self):
        return self.evaluationStack[-1]

    def ForceEnd(self):
        self.callStack.Reset()
        self._currentFlow.currentChoices.clear()
        self.currentPointer = Pointer.Null()
        self.previousPointer = Pointer.Null()
        self.didSafeExit = True

    def TrimWhitespaceFromFunctionEnd(self):
        if self.callStack.currentElement.type != PushPopType.Function:
            return
        function_start_point = self.callStack.currentElement.functionStartInOutputStream
        if function_start_point == -1:
            function_start_point = 0
        for i in range(len(self.outputStream) - 1, function_start_point - 1, -1):
            obj = self.outputStream[i]
            txt = as_or_null(obj, StringValue)
            cmd = as_or_null(obj, ControlCommand)
            if txt is None:
                continue
            if cmd:
                break
            if txt.isNewline or txt.isInlineWhitespace:
                self.outputStream.pop(i)
                self.OutputStreamDirty()
            else:
                break

    def PopCallStack(self, pop_type: Optional[PushPopType] = None):
        if self.callStack.currentElement.type == PushPopType.Function:
            self.TrimWhitespaceFromFunctionEnd()
        self.callStack.Pop(pop_type)

    def SetChosenPath(self, path: Path, incrementing_turn_index: bool):
        self._currentFlow.currentChoices.clear()
        new_pointer = self.story.PointerAtPath(path)
        if not new_pointer.isNull and new_pointer.index == -1:
            new_pointer.index = 0
        self.currentPointer = new_pointer
        if incrementing_turn_index:
            self.currentTurnIndex += 1

    def StartFunctionEvaluationFromGame(self, func_container: Container, args: List):
        self.callStack.Push(PushPopType.FunctionEvaluationFromGame, len(self.evaluationStack))
        self.callStack.currentElement.currentPointer = Pointer.StartOf(func_container)
        self.PassArgumentsToEvaluationStack(args)

    def PassArgumentsToEvaluationStack(self, args: Optional[List]):
        if args is not None:
            for arg in args:
                if not isinstance(arg, (int, float, str, bool, InkList)):
                    raise ValueError(
                        "ink arguments when calling EvaluateFunction / ChoosePathStringWithParameters must be"
                        + "number, string, bool or InkList. Argument was "
                        + ("null" if arg is None else arg.__class__.__name__)
                    )
                self.PushEvaluationStack(Value.Create(arg))

    def TryExitFunctionEvaluationFromGame(self):
        if self.callStack.currentElement.type == PushPopType.FunctionEvaluationFromGame:
            self.currentPointer = Pointer.Null()
            self.didSafeExit = True
            return True
        return False

    def CompleteFunctionEvaluationFromGame(self):
        if self.callStack.currentElement.type != PushPopType.FunctionEvaluationFromGame:
            raise ValueError(
                "Expected external function evaluation to be complete. Stack trace: " + self.callStack.callStackTrace
            )

        original_evaluation_stack_height = self.callStack.currentElement.evaluationStackHeightWhenPushed
        returned_obj = None
        while len(self.evaluationStack) > original_evaluation_stack_height:
            popped_obj = self.PopEvaluationStack()
            if returned_obj is None:
                returned_obj = popped_obj
        self.PopCallStack(PushPopType.FunctionEvaluationFromGame)

        if returned_obj:
            if isinstance(returned_obj, Void):
                return None
            return_val = as_or_throws(returned_obj, Value)
            if return_val.valueType == ValueType.DivertTarget:
                return "-> " + str(return_val.valueObject)
            return return_val.valueObject
        return None

    def AddError(self, message: str, is_warning: bool):
        if not is_warning:
            if self._currentErrors is None:
                self._currentErrors = []
            self._currentErrors.append(message)
        else:
            if self._currentWarnings is None:
                self._currentWarnings = []
            self._currentWarnings.append(message)

    def OutputStreamDirty(self):
        self._outputStreamTextDirty = True
        self._outputStreamTagsDirty = True

    kDefaultFlowName = "DEFAULT_FLOW"
