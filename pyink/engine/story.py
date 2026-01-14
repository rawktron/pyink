from __future__ import annotations

from typing import Dict, List, Optional

from .choice import Choice
from .choice_point import ChoicePoint
from .container import Container
from .control_command import ControlCommand
from .debug_metadata import DebugMetadata
from .divert import Divert
from .error import ErrorHandler, ErrorType
from .ink_list import InkList, InkListItem
from .json_serialisation import JsonSerialisation
from .list_definition import ListDefinition
from .list_definitions_origin import ListDefinitionsOrigin
from .native_function_call import NativeFunctionCall
from .null_exception import throw_null_exception
from .object import InkObject
from .path import Path
from .pointer import Pointer
from .prng import PRNG
from .push_pop import PushPopType
from .simple_json import SimpleJson
from .stop_watch import Stopwatch
from .story_exception import StoryException
from .story_state import StoryState
from .string_builder import StringBuilder
from .tag import Tag
from .type_assertion import as_or_null, as_or_throws
from .value import (
    DivertTargetValue,
    IntValue,
    ListValue,
    StringValue,
    Value,
    ValueType,
    VariablePointerValue,
)
from .variable_assignment import VariableAssignment
from .variable_reference import VariableReference
from .void import Void


class Story(InkObject):
    inkVersionCurrent = 21

    class OutputStateChange:
        NoChange = 0
        ExtendedBeyondNewline = 1
        NewlineRemoved = 2

    def __init__(self, content_container_or_json, lists: Optional[List[ListDefinition]] = None):
        super().__init__()
        self.inkVersionMinimumCompatible = 18

        self._mainContentContainer: Container = None
        self._listDefinitions: Optional[ListDefinitionsOrigin] = None
        self._externals: Dict[str, dict] = {}
        self._variableObservers: Optional[Dict[str, list]] = None
        self._hasValidatedExternals = False
        self._temporaryEvaluationContainer: Optional[Container] = None
        self._state: StoryState = None
        self._asyncContinueActive = False
        self._stateSnapshotAtLastNewline: Optional[StoryState] = None
        self._sawLookaheadUnsafeFunctionAfterNewline = False
        self._recursiveContinueCount = 0
        self._asyncSaving = False
        self._profiler = None

        self.onError: Optional[ErrorHandler] = None
        self.onDidContinue = None
        self.onMakeChoice = None
        self.onEvaluateFunction = None
        self.onCompleteEvaluateFunction = None
        self.onChoosePathString = None

        content_container = None
        json_obj = None

        if isinstance(content_container_or_json, Container):
            content_container = content_container_or_json
            self._mainContentContainer = content_container
            if lists is not None:
                self._listDefinitions = ListDefinitionsOrigin(lists)
            else:
                self._listDefinitions = ListDefinitionsOrigin([])
        else:
            if isinstance(content_container_or_json, str):
                json_obj = SimpleJson.TextToDictionary(content_container_or_json)
            else:
                json_obj = content_container_or_json

        if json_obj is not None:
            root_object = json_obj
            version_obj = root_object.get("inkVersion")
            if version_obj is None:
                raise ValueError("ink version number not found. Are you sure it's a valid .ink.json file?")

            format_from_file = int(version_obj)
            if format_from_file > Story.inkVersionCurrent:
                raise ValueError(
                    "Version of ink used to build story was newer than the current version of the engine"
                )
            if format_from_file < self.inkVersionMinimumCompatible:
                raise ValueError(
                    "Version of ink used to build story is too old to be loaded by this version of the engine"
                )

            root_token = root_object.get("root")
            if root_token is None:
                raise ValueError("Root node for ink not found. Are you sure it's a valid .ink.json file?")

            list_defs_obj = root_object.get("listDefs")
            if list_defs_obj:
                self._listDefinitions = JsonSerialisation.JTokenToListDefinitions(list_defs_obj)
            else:
                self._listDefinitions = ListDefinitionsOrigin([])

            self._mainContentContainer = as_or_throws(JsonSerialisation.JTokenToRuntimeObject(root_token), Container)
            self.ResetState()

    @property
    def currentChoices(self):
        choices = []
        if self._state is None:
            return throw_null_exception("this._state")
        for c in self._state.currentChoices:
            if not c.isInvisibleDefault:
                c.index = len(choices)
                choices.append(c)
        return choices

    @property
    def currentText(self):
        self.IfAsyncWeCant("call currentText since it's a work in progress")
        return self.state.currentText

    @property
    def currentTags(self):
        self.IfAsyncWeCant("call currentTags since it's a work in progress")
        return self.state.currentTags

    @property
    def currentErrors(self):
        return self.state.currentErrors

    @property
    def currentWarnings(self):
        return self.state.currentWarnings

    @property
    def currentFlowName(self):
        return self.state.currentFlowName

    @property
    def currentFlowIsDefaultFlow(self):
        return self.state.currentFlowIsDefaultFlow

    @property
    def aliveFlowNames(self):
        return self.state.aliveFlowNames

    @property
    def hasError(self):
        return self.state.hasError

    @property
    def hasWarning(self):
        return self.state.hasWarning

    @property
    def variablesState(self):
        return self.state.variablesState

    @property
    def listDefinitions(self):
        return self._listDefinitions

    @property
    def state(self):
        return self._state

    def StartProfiling(self):
        pass

    def EndProfiling(self):
        pass

    def ToJson(self, writer: Optional[SimpleJson.Writer] = None):
        should_return = False
        if writer is None:
            should_return = True
            writer = SimpleJson.Writer()

        writer.WriteObjectStart()
        writer.WriteIntProperty("inkVersion", Story.inkVersionCurrent)
        writer.WriteProperty("root", lambda w: JsonSerialisation.WriteRuntimeContainer(w, self._mainContentContainer))

        if self._listDefinitions is not None:
            writer.WritePropertyStart("listDefs")
            writer.WriteObjectStart()
            for definition in self._listDefinitions.lists:
                writer.WritePropertyStart(definition.name)
                writer.WriteObjectStart()
                for key, value in definition.items.items():
                    item = InkListItem.fromSerializedKey(key)
                    writer.WriteIntProperty(item.itemName, value)
                writer.WriteObjectEnd()
                writer.WritePropertyEnd()
            writer.WriteObjectEnd()
            writer.WritePropertyEnd()

        writer.WriteObjectEnd()
        if should_return:
            return writer.toString()

    def ResetState(self):
        self.IfAsyncWeCant("ResetState")
        self._state = StoryState(self)
        self._state.variablesState.ObserveVariableChange(self.VariableStateDidChangeEvent)
        self.ResetGlobals()

    def ResetErrors(self):
        if self._state is None:
            return throw_null_exception("this._state")
        self._state.ResetErrors()

    def ResetCallstack(self):
        self.IfAsyncWeCant("ResetCallstack")
        if self._state is None:
            return throw_null_exception("this._state")
        self._state.ForceEnd()

    def ResetGlobals(self):
        if self._mainContentContainer.namedContent.get("global decl"):
            original_pointer = self.state.currentPointer.copy()
            self.ChoosePath(Path("global decl"), False)
            self.ContinueInternal()
            self.state.currentPointer = original_pointer
        self.state.variablesState.SnapshotDefaultGlobals()

    def SwitchFlow(self, flow_name: str):
        self.IfAsyncWeCant("switch flow")
        if self._asyncSaving:
            raise ValueError("Story is already in background saving mode, can't switch flow to " + flow_name)
        self.state.SwitchFlow_Internal(flow_name)

    def RemoveFlow(self, flow_name: str):
        self.state.RemoveFlow_Internal(flow_name)

    def SwitchToDefaultFlow(self):
        self.state.SwitchToDefaultFlow_Internal()

    def Continue(self):
        self.ContinueAsync(0)
        return self.currentText

    @property
    def canContinue(self):
        return self.state.canContinue

    @property
    def asyncContinueComplete(self):
        return not self._asyncContinueActive

    def ContinueAsync(self, millisecs_limit_async: int):
        if not self._hasValidatedExternals:
            self.ValidateExternalBindings()
        self.ContinueInternal(millisecs_limit_async)

    def ContinueInternal(self, millisecs_limit_async: int = 0):
        if self._profiler is not None:
            self._profiler.PreContinue()

        is_async_time_limited = millisecs_limit_async > 0
        self._recursiveContinueCount += 1

        if not self._asyncContinueActive:
            self._asyncContinueActive = is_async_time_limited
            if not self.canContinue:
                raise ValueError("Can't continue - should check canContinue before calling Continue")
            self._state.didSafeExit = False
            self._state.ResetOutput()
            if self._recursiveContinueCount == 1:
                self._state.variablesState.StartVariableObservation()
        elif self._asyncContinueActive and not is_async_time_limited:
            self._asyncContinueActive = False

        duration_stopwatch = Stopwatch()
        duration_stopwatch.Start()

        output_stream_ends_in_newline = False
        self._sawLookaheadUnsafeFunctionAfterNewline = False
        while True:
            try:
                output_stream_ends_in_newline = self.ContinueSingleStep()
            except StoryException as e:
                self.AddError(str(e), False, e.useEndLineNumber)
                break
            if output_stream_ends_in_newline:
                break
            if self._asyncContinueActive and duration_stopwatch.ElapsedMilliseconds > millisecs_limit_async:
                break
            if not self.canContinue:
                break

        duration_stopwatch.Stop()

        changed_variables_to_observe = None

        if output_stream_ends_in_newline or not self.canContinue:
            if self._stateSnapshotAtLastNewline is not None:
                self.RestoreStateSnapshot()

            if not self.canContinue:
                if self.state.callStack.canPopThread:
                    self.AddError(
                        "Thread available to pop, threads should always be flat by the end of evaluation?"
                    )

                if (
                    len(self.state.generatedChoices) == 0
                    and not self.state.didSafeExit
                    and self._temporaryEvaluationContainer is None
                ):
                    if self.state.callStack.CanPop(PushPopType.Tunnel):
                        self.AddError("unexpectedly reached end of content. Do you need a '->->' to return from a tunnel?")
                    elif self.state.callStack.CanPop(PushPopType.Function):
                        self.AddError("unexpectedly reached end of content. Do you need a '~ return'?")
                    elif not self.state.callStack.canPop:
                        self.AddError("ran out of content. Do you need a '-> DONE' or '-> END'?")
                    else:
                        self.AddError(
                            "unexpectedly reached end of content for unknown reason. Please debug compiler!"
                        )

            self.state.didSafeExit = False
            self._sawLookaheadUnsafeFunctionAfterNewline = False

            if self._recursiveContinueCount == 1:
                changed_variables_to_observe = self._state.variablesState.CompleteVariableObservation()

            self._asyncContinueActive = False
            if self.onDidContinue is not None:
                self.onDidContinue()

        self._recursiveContinueCount -= 1

        if self._profiler is not None:
            self._profiler.PostContinue()

        if self.state.hasError or self.state.hasWarning:
            if self.onError is not None:
                if self.state.hasError:
                    for err in self.state.currentErrors:
                        self.onError(err, ErrorType.Error)
                if self.state.hasWarning:
                    for err in self.state.currentWarnings:
                        self.onError(err, ErrorType.Warning)
                self.ResetErrors()
            else:
                sb = StringBuilder()
                sb.Append("Ink had ")
                if self.state.hasError:
                    sb.Append(str(len(self.state.currentErrors)))
                    sb.Append(" error" if len(self.state.currentErrors) == 1 else " errors")
                    if self.state.hasWarning:
                        sb.Append(" and ")
                if self.state.hasWarning:
                    sb.Append(str(len(self.state.currentWarnings)))
                    sb.Append(" warning" if len(self.state.currentWarnings) == 1 else " warnings")
                    if self.state.hasWarning:
                        sb.Append(" and ")
                sb.Append(
                    ". It is strongly suggested that you assign an error handler to story.onError. The first issue was: "
                )
                sb.Append(
                    self.state.currentErrors[0] if self.state.hasError else self.state.currentWarnings[0]
                )
                raise StoryException(str(sb))

        if changed_variables_to_observe is not None and len(changed_variables_to_observe) > 0:
            self._state.variablesState.NotifyObservers(changed_variables_to_observe)

    def ContinueSingleStep(self):
        if self._profiler is not None:
            self._profiler.PreStep()
        self.Step()
        if self._profiler is not None:
            self._profiler.PostStep()

        if not self.canContinue and not self.state.callStack.elementIsEvaluateFromGame:
            self.TryFollowDefaultInvisibleChoice()

        if self._profiler is not None:
            self._profiler.PreSnapshot()

        if not self.state.inStringEvaluation:
            if self._stateSnapshotAtLastNewline is not None:
                change = self.CalculateNewlineOutputStateChange(
                    self._stateSnapshotAtLastNewline.currentText,
                    self.state.currentText,
                    len(self._stateSnapshotAtLastNewline.currentTags or []),
                    len(self.state.currentTags or []),
                )
                if change == Story.OutputStateChange.ExtendedBeyondNewline or self._sawLookaheadUnsafeFunctionAfterNewline:
                    self.RestoreStateSnapshot()
                    return True
                if change == Story.OutputStateChange.NewlineRemoved:
                    self.DiscardSnapshot()

            if self.state.outputStreamEndsInNewline:
                if self.canContinue:
                    if self._stateSnapshotAtLastNewline is None:
                        self.StateSnapshot()
                else:
                    self.DiscardSnapshot()

        if self._profiler is not None:
            self._profiler.PostSnapshot()
        return False

    def CalculateNewlineOutputStateChange(self, prev_text, curr_text, prev_tag_count, curr_tag_count):
        if prev_text is None:
            return throw_null_exception("prevText")
        if curr_text is None:
            return throw_null_exception("currText")

        newline_still_exists = (
            len(curr_text) >= len(prev_text)
            and len(prev_text) > 0
            and curr_text[len(prev_text) - 1] == "\n"
        )
        if prev_tag_count == curr_tag_count and len(prev_text) == len(curr_text) and newline_still_exists:
            return Story.OutputStateChange.NoChange

        if not newline_still_exists:
            return Story.OutputStateChange.NewlineRemoved

        if curr_tag_count > prev_tag_count:
            return Story.OutputStateChange.ExtendedBeyondNewline

        for c in curr_text[len(prev_text) :]:
            if c not in (" ", "\t"):
                return Story.OutputStateChange.ExtendedBeyondNewline
        return Story.OutputStateChange.NoChange

    def ContinueMaximally(self):
        self.IfAsyncWeCant("ContinueMaximally")
        sb = StringBuilder()
        while self.canContinue:
            sb.Append(self.Continue())
        return str(sb)

    def ContentAtPath(self, path: Path):
        return self.mainContentContainer.ContentAtPath(path)

    def KnotContainerWithName(self, name: str):
        named_container = self.mainContentContainer.namedContent.get(name)
        return named_container if isinstance(named_container, Container) else None

    def PointerAtPath(self, path: Path):
        if path.length == 0:
            return Pointer.Null()

        p = Pointer()
        path_length_to_use = path.length
        result = None

        if path.lastComponent is None:
            return throw_null_exception("path.lastComponent")

        if path.lastComponent.isIndex:
            path_length_to_use = path.length - 1
            result = self.mainContentContainer.ContentAtPath(path, 0, path_length_to_use)
            p.container = result.container
            p.index = path.lastComponent.index
        else:
            result = self.mainContentContainer.ContentAtPath(path)
            p.container = result.container
            p.index = -1

        if result.obj is None or (result.obj == self.mainContentContainer and path_length_to_use > 0):
            self.Error("Failed to find content at path '" + str(path) + "', and no approximation of it was possible.")
        elif result.approximate:
            self.Warning("Failed to find content at path '" + str(path) + "', so it was approximated to: '" + str(result.obj.path) + "'.")

        return p

    def StateSnapshot(self):
        self._stateSnapshotAtLastNewline = self._state
        self._state = self._state.CopyAndStartPatching(False)

    def RestoreStateSnapshot(self):
        if self._stateSnapshotAtLastNewline is None:
            return throw_null_exception("_stateSnapshotAtLastNewline")
        self._stateSnapshotAtLastNewline.RestoreAfterPatch()
        self._state = self._stateSnapshotAtLastNewline
        self._stateSnapshotAtLastNewline = None
        if not self._asyncSaving:
            self._state.ApplyAnyPatch()

    def DiscardSnapshot(self):
        if not self._asyncSaving:
            self._state.ApplyAnyPatch()
        self._stateSnapshotAtLastNewline = None

    def CopyStateForBackgroundThreadSave(self):
        self.IfAsyncWeCant("start saving on a background thread")
        if self._asyncSaving:
            raise ValueError("Story is already in background saving mode, can't call CopyStateForBackgroundThreadSave again!")
        state_to_save = self._state
        self._state = self._state.CopyAndStartPatching(True)
        self._asyncSaving = True
        return state_to_save

    def BackgroundSaveComplete(self):
        if self._stateSnapshotAtLastNewline is None:
            self._state.ApplyAnyPatch()
        self._asyncSaving = False

    def Step(self):
        should_add_to_stream = True
        pointer = self.state.currentPointer.copy()
        if pointer.isNull:
            return

        container_to_enter = as_or_null(pointer.Resolve(), Container)
        while container_to_enter:
            self.VisitContainer(container_to_enter, True)
            if len(container_to_enter.content) == 0:
                break
            pointer = Pointer.StartOf(container_to_enter)
            container_to_enter = as_or_null(pointer.Resolve(), Container)

        self.state.currentPointer = pointer.copy()
        if self._profiler is not None:
            self._profiler.Step(self.state.callStack)

        current_content_obj = pointer.Resolve()
        is_logic_or_flow_control = self.PerformLogicAndFlowControl(current_content_obj)
        if self.state.currentPointer.isNull:
            return
        if is_logic_or_flow_control:
            should_add_to_stream = False

        choice_point = as_or_null(current_content_obj, ChoicePoint)
        if choice_point:
            choice = self.ProcessChoice(choice_point)
            if choice:
                self.state.generatedChoices.append(choice)
            current_content_obj = None
            should_add_to_stream = False

        if isinstance(current_content_obj, Container):
            should_add_to_stream = False

        if should_add_to_stream:
            var_pointer = as_or_null(current_content_obj, VariablePointerValue)
            if var_pointer and var_pointer.contextIndex == -1:
                context_idx = self.state.callStack.ContextForVariableNamed(var_pointer.variableName)
                current_content_obj = VariablePointerValue(var_pointer.variableName, context_idx)

            if self.state.inExpressionEvaluation:
                self.state.PushEvaluationStack(current_content_obj)
            else:
                self.state.PushToOutputStream(current_content_obj)

        self.NextContent()

        control_cmd = as_or_null(current_content_obj, ControlCommand)
        if control_cmd and control_cmd.commandType == ControlCommand.CommandType.StartThread:
            self.state.callStack.PushThread()

    def VisitContainer(self, container: Container, at_start: bool):
        if not container.countingAtStartOnly or at_start:
            if container.visitsShouldBeCounted:
                self.state.IncrementVisitCountForContainer(container)
            if container.turnIndexShouldBeCounted:
                self.state.RecordTurnIndexVisitToContainer(container)

    _prevContainers: List[Container] = []

    def VisitChangedContainersDueToDivert(self):
        previous_pointer = self.state.previousPointer.copy()
        pointer = self.state.currentPointer.copy()
        if pointer.isNull or pointer.index == -1:
            return

        self._prevContainers = []
        if not previous_pointer.isNull:
            resolved_previous_ancestor = previous_pointer.Resolve()
            prev_ancestor = as_or_null(resolved_previous_ancestor, Container) or as_or_null(previous_pointer.container, Container)
            while prev_ancestor:
                self._prevContainers.append(prev_ancestor)
                prev_ancestor = as_or_null(prev_ancestor.parent, Container)

        current_child_of_container = pointer.Resolve()
        if current_child_of_container is None:
            return

        current_container_ancestor = as_or_null(current_child_of_container.parent, Container)
        all_children_entered_at_start = True
        while current_container_ancestor and (
            current_container_ancestor not in self._prevContainers or current_container_ancestor.countingAtStartOnly
        ):
            entering_at_start = (
                len(current_container_ancestor.content) > 0
                and current_child_of_container == current_container_ancestor.content[0]
                and all_children_entered_at_start
            )
            if not entering_at_start:
                all_children_entered_at_start = False

            self.VisitContainer(current_container_ancestor, entering_at_start)
            current_child_of_container = current_container_ancestor
            current_container_ancestor = as_or_null(current_container_ancestor.parent, Container)

    def PopChoiceStringAndTags(self, tags: List[str]):
        choice_only_str_val = as_or_throws(self.state.PopEvaluationStack(), StringValue)
        while self.state.evaluationStack and as_or_null(self.state.PeekEvaluationStack(), Tag) is not None:
            tag = as_or_null(self.state.PopEvaluationStack(), Tag)
            if tag:
                tags.append(tag.text)
        return choice_only_str_val.value

    def ProcessChoice(self, choice_point: ChoicePoint):
        show_choice = True
        if choice_point.hasCondition:
            condition_value = self.state.PopEvaluationStack()
            if not self.IsTruthy(condition_value):
                show_choice = False

        start_text = ""
        choice_only_text = ""
        tags: List[str] = []

        if choice_point.hasChoiceOnlyContent:
            choice_only_text = self.PopChoiceStringAndTags(tags) or ""
        if choice_point.hasStartContent:
            start_text = self.PopChoiceStringAndTags(tags) or ""

        if choice_point.onceOnly:
            visit_count = self.state.VisitCountForContainer(choice_point.choiceTarget)
            if visit_count > 0:
                show_choice = False

        if not show_choice:
            return None

        choice = Choice()
        choice.targetPath = choice_point.pathOnChoice
        choice.sourcePath = choice_point.path.toString()
        choice.isInvisibleDefault = choice_point.isInvisibleDefault
        choice.threadAtGeneration = self.state.callStack.ForkThread()
        choice.tags = list(reversed(tags))
        choice.text = (start_text + choice_only_text).strip(" \t")
        return choice

    def IsTruthy(self, obj):
        if isinstance(obj, Value):
            if isinstance(obj, DivertTargetValue):
                self.Error(
                    "Shouldn't use a divert target (to "
                    + str(obj.targetPath)
                    + ") as a conditional value. Did you intend a function call 'likeThis()' or a read count check 'likeThis'? (no arrows)"
                )
                return False
            return obj.isTruthy
        return False

    def PerformLogicAndFlowControl(self, content_obj: Optional[InkObject]):
        if content_obj is None:
            return False

        if isinstance(content_obj, Divert):
            current_divert = content_obj
            if current_divert.isConditional:
                condition_value = self.state.PopEvaluationStack()
                if not self.IsTruthy(condition_value):
                    return True

            if current_divert.hasVariableTarget:
                var_name = current_divert.variableDivertName
                var_contents = self.state.variablesState.GetVariableWithName(var_name)
                if var_contents is None:
                    self.Error(
                        "Tried to divert using a target from a variable that could not be found (" + var_name + ")"
                    )
                elif not isinstance(var_contents, DivertTargetValue):
                    int_content = as_or_null(var_contents, IntValue)
                    error_message = (
                        "Tried to divert to a target from a variable, but the variable ("
                        + var_name
                        + ") didn't contain a divert target, it "
                    )
                    if isinstance(int_content, IntValue) and int_content.value == 0:
                        error_message += "was empty/null (the value 0)."
                    else:
                        error_message += "contained '" + str(var_contents) + "'."
                    self.Error(error_message)
                target = as_or_throws(var_contents, DivertTargetValue)
                self.state.divertedPointer = self.PointerAtPath(target.targetPath)
            elif current_divert.isExternal:
                self.CallExternalFunction(current_divert.targetPathString, current_divert.externalArgs)
                return True
            else:
                self.state.divertedPointer = current_divert.targetPointer.copy()

            if current_divert.pushesToStack:
                self.state.callStack.Push(
                    current_divert.stackPushType, 0, len(self.state.outputStream)
                )

            if self.state.divertedPointer.isNull and not current_divert.isExternal:
                if current_divert.debugMetadata and current_divert.debugMetadata.sourceName is not None:
                    self.Error("Divert target doesn't exist: " + current_divert.debugMetadata.sourceName)
                else:
                    self.Error("Divert resolution failed: " + str(current_divert))
            return True

        if isinstance(content_obj, ControlCommand):
            eval_command = content_obj
            cmd = eval_command.commandType

            if cmd == ControlCommand.CommandType.EvalStart:
                self.Assert(self.state.inExpressionEvaluation is False, "Already in expression evaluation?")
                self.state.inExpressionEvaluation = True
            elif cmd == ControlCommand.CommandType.EvalEnd:
                self.Assert(self.state.inExpressionEvaluation is True, "Not in expression evaluation mode")
                self.state.inExpressionEvaluation = False
            elif cmd == ControlCommand.CommandType.EvalOutput:
                if len(self.state.evaluationStack) > 0:
                    output = self.state.PopEvaluationStack()
                    if not isinstance(output, Void):
                        text = StringValue(str(output))
                        self.state.PushToOutputStream(text)
            elif cmd == ControlCommand.CommandType.NoOp:
                pass
            elif cmd == ControlCommand.CommandType.Duplicate:
                self.state.PushEvaluationStack(self.state.PeekEvaluationStack())
            elif cmd == ControlCommand.CommandType.PopEvaluatedValue:
                self.state.PopEvaluationStack()
            elif cmd in (ControlCommand.CommandType.PopFunction, ControlCommand.CommandType.PopTunnel):
                pop_type = PushPopType.Function if cmd == ControlCommand.CommandType.PopFunction else PushPopType.Tunnel
                override_tunnel_return_target = None
                if pop_type == PushPopType.Tunnel:
                    popped = self.state.PopEvaluationStack()
                    override_tunnel_return_target = as_or_null(popped, DivertTargetValue)
                    if override_tunnel_return_target is None:
                        self.Assert(isinstance(popped, Void), "Expected void if ->-> doesn't override target")

                if self.state.TryExitFunctionEvaluationFromGame():
                    pass
                elif self.state.callStack.currentElement.type != pop_type or not self.state.callStack.canPop:
                    names = {
                        PushPopType.Function: "function return statement (~ return)",
                        PushPopType.Tunnel: "tunnel onwards statement (->->)",
                    }
                    expected = names.get(self.state.callStack.currentElement.type)
                    if not self.state.callStack.canPop:
                        expected = "end of flow (-> END or choice)"
                    error_msg = "Found " + names.get(pop_type) + ", when expected " + str(expected)
                    self.Error(error_msg)
                else:
                    self.state.PopCallStack()
                    if override_tunnel_return_target:
                        self.state.divertedPointer = self.PointerAtPath(override_tunnel_return_target.targetPath)
            elif cmd == ControlCommand.CommandType.BeginString:
                self.state.PushToOutputStream(eval_command)
                self.Assert(self.state.inExpressionEvaluation is True, "Expected to be in an expression when evaluating a string")
                self.state.inExpressionEvaluation = False
            elif cmd == ControlCommand.CommandType.BeginTag:
                self.state.PushToOutputStream(eval_command)
            elif cmd == ControlCommand.CommandType.EndTag:
                if self.state.inStringEvaluation:
                    content_stack_for_tag = []
                    output_count_consumed = 0
                    for i in range(len(self.state.outputStream) - 1, -1, -1):
                        obj = self.state.outputStream[i]
                        output_count_consumed += 1
                        command = as_or_null(obj, ControlCommand)
                        if command is not None:
                            if command.commandType == ControlCommand.CommandType.BeginTag:
                                break
                            self.Error("Unexpected ControlCommand while extracting tag from choice")
                            break
                        if isinstance(obj, StringValue):
                            content_stack_for_tag.append(obj)
                    self.state.PopFromOutputStream(output_count_consumed)
                    sb = StringBuilder()
                    for str_val in reversed(content_stack_for_tag):
                        sb.Append(str_val.toString())
                    choice_tag = Tag(self.state.CleanOutputWhitespace(str(sb)))
                    self.state.PushEvaluationStack(choice_tag)
                else:
                    self.state.PushToOutputStream(eval_command)
            elif cmd == ControlCommand.CommandType.EndString:
                content_stack_for_string = []
                content_to_retain = []
                output_count_consumed = 0
                for i in range(len(self.state.outputStream) - 1, -1, -1):
                    obj = self.state.outputStream[i]
                    output_count_consumed += 1
                    command = as_or_null(obj, ControlCommand)
                    if command and command.commandType == ControlCommand.CommandType.BeginString:
                        break
                    if isinstance(obj, Tag):
                        content_to_retain.append(obj)
                    if isinstance(obj, StringValue):
                        content_stack_for_string.append(obj)
                self.state.PopFromOutputStream(output_count_consumed)
                for rescued_tag in content_to_retain:
                    self.state.PushToOutputStream(rescued_tag)
                content_stack_for_string = list(reversed(content_stack_for_string))
                sb = StringBuilder()
                for c in content_stack_for_string:
                    sb.Append(c.toString())
                self.state.inExpressionEvaluation = True
                self.state.PushEvaluationStack(StringValue(str(sb)))
            elif cmd == ControlCommand.CommandType.ChoiceCount:
                choice_count = len(self.state.generatedChoices)
                self.state.PushEvaluationStack(IntValue(choice_count))
            elif cmd == ControlCommand.CommandType.Turns:
                self.state.PushEvaluationStack(IntValue(self.state.currentTurnIndex + 1))
            elif cmd in (ControlCommand.CommandType.TurnsSince, ControlCommand.CommandType.ReadCount):
                target = self.state.PopEvaluationStack()
                if not isinstance(target, DivertTargetValue):
                    extra_note = ""
                    if isinstance(target, IntValue):
                        extra_note = ". Did you accidentally pass a read count ('knot_name') instead of a target ('-> knot_name')?"
                    self.Error(
                        "TURNS_SINCE / READ_COUNT expected a divert target (knot, stitch, label name), but saw "
                        + str(target)
                        + extra_note
                    )
                    return True
                divert_target = as_or_throws(target, DivertTargetValue)
                container = as_or_null(self.ContentAtPath(divert_target.targetPath).correctObj, Container)
                if container is not None:
                    if cmd == ControlCommand.CommandType.TurnsSince:
                        either_count = self.state.TurnsSinceForContainer(container)
                    else:
                        either_count = self.state.VisitCountForContainer(container)
                else:
                    either_count = -1 if cmd == ControlCommand.CommandType.TurnsSince else 0
                    self.Warning(
                        "Failed to find container for " + str(eval_command) + " lookup at " + str(divert_target.targetPath)
                    )
                self.state.PushEvaluationStack(IntValue(either_count))
            elif cmd == ControlCommand.CommandType.Random:
                max_int = as_or_null(self.state.PopEvaluationStack(), IntValue)
                min_int = as_or_null(self.state.PopEvaluationStack(), IntValue)
                if not isinstance(min_int, IntValue):
                    return self.Error("Invalid value for minimum parameter of RANDOM(min, max)")
                if not isinstance(max_int, IntValue):
                    return self.Error("Invalid value for maximum parameter of RANDOM(min, max)")
                if max_int.value is None or min_int.value is None:
                    return throw_null_exception("minInt.value")
                random_range = max_int.value - min_int.value + 1
                if random_range <= 0:
                    self.Error(
                        "RANDOM was called with minimum as "
                        + str(min_int.value)
                        + " and maximum as "
                        + str(max_int.value)
                        + ". The maximum must be larger"
                    )
                result_seed = self.state.storySeed + self.state.previousRandom
                random = PRNG(result_seed)
                next_random = random.next()
                chosen_value = (next_random % random_range) + min_int.value
                self.state.PushEvaluationStack(IntValue(chosen_value))
                self.state.previousRandom = next_random
            elif cmd == ControlCommand.CommandType.SeedRandom:
                seed = as_or_null(self.state.PopEvaluationStack(), IntValue)
                if not isinstance(seed, IntValue):
                    return self.Error("Invalid value passed to SEED_RANDOM")
                if seed.value is None:
                    return throw_null_exception("minInt.value")
                self.state.storySeed = seed.value
                self.state.previousRandom = 0
                self.state.PushEvaluationStack(Void())
            elif cmd == ControlCommand.CommandType.VisitIndex:
                count = self.state.VisitCountForContainer(self.state.currentPointer.container) - 1
                self.state.PushEvaluationStack(IntValue(count))
            elif cmd == ControlCommand.CommandType.SequenceShuffleIndex:
                shuffle_index = self.NextSequenceShuffleIndex()
                self.state.PushEvaluationStack(IntValue(shuffle_index))
            elif cmd == ControlCommand.CommandType.StartThread:
                pass
            elif cmd == ControlCommand.CommandType.Done:
                if self.state.callStack.canPopThread:
                    self.state.callStack.PopThread()
                else:
                    self.state.didSafeExit = True
                    self.state.currentPointer = Pointer.Null()
            elif cmd == ControlCommand.CommandType.End:
                self.state.ForceEnd()
            elif cmd == ControlCommand.CommandType.ListFromInt:
                int_val = as_or_null(self.state.PopEvaluationStack(), IntValue)
                list_name_val = as_or_throws(self.state.PopEvaluationStack(), StringValue)
                if int_val is None:
                    raise StoryException("Passed non-integer when creating a list element from a numerical value.")
                generated_list_value = None
                if self.listDefinitions is None:
                    return throw_null_exception("this.listDefinitions")
                found_list_def = self.listDefinitions.TryListGetDefinition(list_name_val.value, None)
                if found_list_def.exists:
                    if int_val.value is None:
                        return throw_null_exception("minInt.value")
                    found_item = found_list_def.result.TryGetItemWithValue(int_val.value, InkListItem.Null())
                    if found_item.exists:
                        generated_list_value = ListValue(found_item.result, int_val.value)
                else:
                    raise StoryException("Failed to find LIST called " + str(list_name_val.value))
                if generated_list_value is None:
                    generated_list_value = ListValue()
                self.state.PushEvaluationStack(generated_list_value)
            elif cmd == ControlCommand.CommandType.ListRange:
                max_val = as_or_null(self.state.PopEvaluationStack(), Value)
                min_val = as_or_null(self.state.PopEvaluationStack(), Value)
                target_list = as_or_null(self.state.PopEvaluationStack(), ListValue)
                if target_list is None or min_val is None or max_val is None:
                    raise StoryException("Expected list, minimum and maximum for LIST_RANGE")
                if target_list.value is None:
                    return throw_null_exception("targetList.value")
                result = target_list.value.ListWithSubRange(min_val.valueObject, max_val.valueObject)
                self.state.PushEvaluationStack(ListValue(result))
            elif cmd == ControlCommand.CommandType.ListRandom:
                list_val = self.state.PopEvaluationStack()
                if not isinstance(list_val, ListValue):
                    raise StoryException("Expected list for LIST_RANDOM")
                list_obj = list_val.value
                new_list = None
                if list_obj is None:
                    raise throw_null_exception("list")
                if list_obj.Count == 0:
                    new_list = InkList()
                else:
                    result_seed = self.state.storySeed + self.state.previousRandom
                    random = PRNG(result_seed)
                    next_random = random.next()
                    list_item_index = next_random % list_obj.Count
                    list_entries = list(list_obj.items())
                    key, value = list_entries[list_item_index]
                    random_item = {"Key": InkListItem.fromSerializedKey(key), "Value": value}
                    if random_item["Key"].originName is None:
                        return throw_null_exception("randomItem.Key.originName")
                    new_list = InkList(random_item["Key"].originName, self)
                    new_list.Add(random_item["Key"], random_item["Value"])
                    self.state.previousRandom = next_random
                self.state.PushEvaluationStack(ListValue(new_list))
            else:
                self.Error("unhandled ControlCommand: " + str(eval_command))
            return True

        if isinstance(content_obj, VariableAssignment):
            var_ass = content_obj
            assigned_val = self.state.PopEvaluationStack()
            self.state.variablesState.Assign(var_ass, assigned_val)
            return True

        if isinstance(content_obj, VariableReference):
            var_ref = content_obj
            found_value = None
            if var_ref.pathForCount is not None:
                container = var_ref.containerForCount
                count = self.state.VisitCountForContainer(container)
                found_value = IntValue(count)
            else:
                found_value = self.state.variablesState.GetVariableWithName(var_ref.name)
                if found_value is None:
                    self.Warning(
                        "Variable not found: '"
                        + str(var_ref.name)
                        + "'. Using default value of 0 (false). This can happen with temporary variables if the declaration hasn't yet been hit. Globals are always given a default value on load if a value doesn't exist in the save state."
                    )
                    found_value = IntValue(0)
            self.state.PushEvaluationStack(found_value)
            return True

        if isinstance(content_obj, NativeFunctionCall):
            func = content_obj
            func_params = self.state.PopEvaluationStack(func.numberOfParameters)
            result = func.Call(func_params)
            self.state.PushEvaluationStack(result)
            return True

        return False

    def ChoosePathString(self, path: str, reset_callstack: bool = True, args: Optional[List] = None):
        self.IfAsyncWeCant("call ChoosePathString right now")
        if self.onChoosePathString is not None:
            self.onChoosePathString(path, args or [])

        if reset_callstack:
            self.ResetCallstack()
        else:
            if self.state.callStack.currentElement.type == PushPopType.Function:
                func_detail = ""
                container = self.state.callStack.currentElement.currentPointer.container
                if container is not None:
                    func_detail = "(" + container.path.toString() + ") "
                raise ValueError(
                    "Story was running a function "
                    + func_detail
                    + "when you called ChoosePathString("
                    + path
                    + ") - this is almost certainly not not what you want! Full stack trace: \n"
                    + self.state.callStack.callStackTrace
                )

        self.state.PassArgumentsToEvaluationStack(args or [])
        self.ChoosePath(Path(path))

    def IfAsyncWeCant(self, activity_str: str):
        if self._asyncContinueActive:
            raise ValueError(
                "Can't "
                + activity_str
                + ". Story is in the middle of a ContinueAsync(). Make more ContinueAsync() calls or a single Continue() call beforehand."
            )

    def ChoosePath(self, p: Path, incrementing_turn_index: bool = True):
        self.state.SetChosenPath(p, incrementing_turn_index)
        self.VisitChangedContainersDueToDivert()

    def ChooseChoiceIndex(self, choice_idx: int):
        choices = self.currentChoices
        self.Assert(choice_idx >= 0 and choice_idx < len(choices), "choice out of range")
        choice_to_choose = choices[choice_idx]
        if self.onMakeChoice is not None:
            self.onMakeChoice(choice_to_choose)
        if choice_to_choose.threadAtGeneration is None:
            return throw_null_exception("choiceToChoose.threadAtGeneration")
        if choice_to_choose.targetPath is None:
            return throw_null_exception("choiceToChoose.targetPath")
        self.state.callStack.currentThread = choice_to_choose.threadAtGeneration
        self.ChoosePath(choice_to_choose.targetPath)

    def HasFunction(self, function_name: str):
        try:
            return self.KnotContainerWithName(function_name) is not None
        except Exception:
            return False

    def EvaluateFunction(self, function_name: str, args: Optional[List] = None, return_text_output: bool = False):
        if self.onEvaluateFunction is not None:
            self.onEvaluateFunction(function_name, args or [])

        self.IfAsyncWeCant("evaluate a function")

        if function_name is None:
            raise ValueError("Function is null")
        if function_name.strip() == "":
            raise ValueError("Function is empty or white space.")

        func_container = self.KnotContainerWithName(function_name)
        if func_container is None:
            raise ValueError("Function doesn't exist: '" + function_name + "'")

        output_stream_before = list(self.state.outputStream)
        self._state.ResetOutput()

        self.state.StartFunctionEvaluationFromGame(func_container, args or [])

        string_output = StringBuilder()
        while self.canContinue:
            string_output.Append(self.Continue())
        text_output = str(string_output)

        self._state.ResetOutput(output_stream_before)

        result = self.state.CompleteFunctionEvaluationFromGame()
        if self.onCompleteEvaluateFunction is not None:
            self.onCompleteEvaluateFunction(function_name, args or [], text_output, result)

        if return_text_output:
            return {"returned": result, "output": text_output}
        return result

    def EvaluateExpression(self, expr_container: Container):
        start_call_stack_height = len(self.state.callStack.elements)
        self.state.callStack.Push(PushPopType.Tunnel)
        self._temporaryEvaluationContainer = expr_container
        self.state.GoToStart()
        eval_stack_height = len(self.state.evaluationStack)
        self.Continue()
        self._temporaryEvaluationContainer = None
        if len(self.state.callStack.elements) > start_call_stack_height:
            self.state.PopCallStack()
        end_stack_height = len(self.state.evaluationStack)
        if end_stack_height > eval_stack_height:
            return self.state.PopEvaluationStack()
        return None

    allowExternalFunctionFallbacks = False

    def CallExternalFunction(self, func_name: str, number_of_arguments: int):
        if func_name is None:
            return throw_null_exception("funcName")
        func_def = self._externals.get(func_name)
        fallback_function_container = None
        found_external = func_def is not None

        if found_external and not func_def["lookAheadSafe"] and self._state.inStringEvaluation:
            self.Error(
                "External function "
                + func_name
                + " could not be called because 1) it wasn't marked as lookaheadSafe when BindExternalFunction was called and 2) the story is in the middle of string generation, either because choice text is being generated, or because you have ink like \"hello {func()}\". You can work around this by generating the result of your function into a temporary variable before the string or choice gets generated: ~ temp x = "
                + func_name
                + "()"
            )

        if found_external and not func_def["lookAheadSafe"] and self._stateSnapshotAtLastNewline is not None:
            self._sawLookaheadUnsafeFunctionAfterNewline = True
            return

        if not found_external:
            if self.allowExternalFunctionFallbacks:
                fallback_function_container = self.KnotContainerWithName(func_name)
                self.Assert(
                    fallback_function_container is not None,
                    "Trying to call EXTERNAL function '"
                    + func_name
                    + "' which has not been bound, and fallback ink function could not be found.",
                )
                self.state.callStack.Push(PushPopType.Function, 0, len(self.state.outputStream))
                self.state.divertedPointer = Pointer.StartOf(fallback_function_container)
                return
            self.Assert(
                False,
                "Trying to call EXTERNAL function '"
                + func_name
                + "' which has not been bound (and ink fallbacks disabled).",
            )

        args = []
        for _ in range(number_of_arguments):
            popped_obj = as_or_throws(self.state.PopEvaluationStack(), Value)
            args.append(popped_obj.valueObject)
        args.reverse()

        func_result = func_def["function"](args)
        if func_result is not None:
            return_obj = Value.Create(func_result)
            self.Assert(
                return_obj is not None,
                "Could not create ink value from returned object of type " + str(type(func_result)),
            )
        else:
            return_obj = Void()
        self.state.PushEvaluationStack(return_obj)

    def BindExternalFunctionGeneral(self, func_name: str, func, lookahead_safe: bool = True):
        self.IfAsyncWeCant("bind an external function")
        self.Assert(func_name not in self._externals, "Function '" + func_name + "' has already been bound.")
        self._externals[func_name] = {"function": func, "lookAheadSafe": lookahead_safe}

    def TryCoerce(self, value):
        return value

    def BindExternalFunction(self, func_name: str, func, lookahead_safe: bool = False):
        self.Assert(func is not None, "Can't bind a null function")

        def wrapper(args):
            self.Assert(len(args) >= func.__code__.co_argcount, "External function expected " + str(func.__code__.co_argcount) + " arguments")
            coerced_args = [self.TryCoerce(arg) for arg in args]
            return func(*coerced_args)

        self.BindExternalFunctionGeneral(func_name, wrapper, lookahead_safe)

    def UnbindExternalFunction(self, func_name: str):
        self.IfAsyncWeCant("unbind an external a function")
        self.Assert(func_name in self._externals, "Function '" + func_name + "' has not been bound.")
        del self._externals[func_name]

    def ValidateExternalBindings(self, o=None, missing_externals=None):
        if missing_externals is None:
            missing_externals = set()

        if o is None:
            self.ValidateExternalBindings(self._mainContentContainer, missing_externals)
            self._hasValidatedExternals = True
            if len(missing_externals) == 0:
                self._hasValidatedExternals = True
            else:
                message = "Error: Missing function binding for external"
                message += "s" if len(missing_externals) > 1 else ""
                message += ": '"
                message += "', '".join(sorted(missing_externals))
                message += "' "
                message += (
                    ", and no fallback ink function found."
                    if self.allowExternalFunctionFallbacks
                    else " (ink fallbacks disabled)"
                )
                self.Error(message)
            return

        if isinstance(o, Container):
            for inner_content in o.content:
                container = inner_content if isinstance(inner_content, Container) else None
                if container is None or not container.hasValidName:
                    self.ValidateExternalBindings(inner_content, missing_externals)
            for value in o.namedContent.values():
                self.ValidateExternalBindings(as_or_null(value, InkObject), missing_externals)
            return

        divert = as_or_null(o, Divert)
        if divert and divert.isExternal:
            name = divert.targetPathString
            if name is None:
                return throw_null_exception("name")
            if name not in self._externals:
                if self.allowExternalFunctionFallbacks:
                    fallback_found = name in self.mainContentContainer.namedContent
                    if not fallback_found:
                        missing_externals.add(name)
                else:
                    missing_externals.add(name)

    def ObserveVariable(self, variable_name: str, observer):
        self.IfAsyncWeCant("observe a new variable")
        if self._variableObservers is None:
            self._variableObservers = {}
        if not self.state.variablesState.GlobalVariableExistsWithName(variable_name):
            raise ValueError(
                "Cannot observe variable '" + variable_name + "' because it wasn't declared in the ink story."
            )
        if variable_name in self._variableObservers:
            self._variableObservers[variable_name].append(observer)
        else:
            self._variableObservers[variable_name] = [observer]

    def ObserveVariables(self, variable_names: List[str], observers: List):
        for i, var_name in enumerate(variable_names):
            self.ObserveVariable(var_name, observers[i])

    def RemoveVariableObserver(self, observer=None, specific_variable_name=None):
        self.IfAsyncWeCant("remove a variable observer")
        if self._variableObservers is None:
            return
        if specific_variable_name is not None:
            if specific_variable_name in self._variableObservers:
                if observer is not None:
                    variable_observers = self._variableObservers.get(specific_variable_name)
                    if variable_observers:
                        variable_observers.remove(observer)
                        if not variable_observers:
                            del self._variableObservers[specific_variable_name]
                else:
                    del self._variableObservers[specific_variable_name]
        elif observer is not None:
            for var_name in list(self._variableObservers.keys()):
                variable_observers = self._variableObservers.get(var_name)
                if variable_observers:
                    if observer in variable_observers:
                        variable_observers.remove(observer)
                    if not variable_observers:
                        del self._variableObservers[var_name]

    def VariableStateDidChangeEvent(self, variable_name: str, new_value_obj):
        if self._variableObservers is None:
            return
        observers = self._variableObservers.get(variable_name)
        if observers is not None:
            if not isinstance(new_value_obj, Value):
                raise ValueError("Tried to get the value of a variable that isn't a standard type")
            val = as_or_throws(new_value_obj, Value)
            for observer in observers:
                observer(variable_name, val.valueObject)

    @property
    def globalTags(self):
        return self.TagsAtStartOfFlowContainerWithPathString("")

    def TagsForContentAtPath(self, path: str):
        return self.TagsAtStartOfFlowContainerWithPathString(path)

    def TagsAtStartOfFlowContainerWithPathString(self, path_string: str):
        path = Path(path_string)
        flow_container = self.ContentAtPath(path).container
        if flow_container is None:
            return throw_null_exception("flowContainer")
        while True:
            first_content = flow_container.content[0]
            if isinstance(first_content, Container):
                flow_container = first_content
            else:
                break

        in_tag = False
        tags = None
        for c in flow_container.content:
            command = as_or_null(c, ControlCommand)
            if command is not None:
                if command.commandType == ControlCommand.CommandType.BeginTag:
                    in_tag = True
                elif command.commandType == ControlCommand.CommandType.EndTag:
                    in_tag = False
            elif in_tag:
                str_val = as_or_null(c, StringValue)
                if str_val is not None:
                    if tags is None:
                        tags = []
                    if str_val.value is not None:
                        tags.append(str_val.value)
                else:
                    self.Error(
                        "Tag contained non-text content. Only plain text is allowed when using globalTags or TagsAtContentPath. If you want to evaluate dynamic content, you need to use story.Continue()."
                    )
            else:
                break
        return tags

    def BuildStringOfHierarchy(self):
        sb = StringBuilder()
        self.mainContentContainer.BuildStringOfHierarchy(sb, 0, self.state.currentPointer.Resolve())
        return str(sb)

    def BuildStringOfContainer(self, container: Container):
        sb = StringBuilder()
        container.BuildStringOfHierarchy(sb, 0, self.state.currentPointer.Resolve())
        return str(sb)

    def NextContent(self):
        self.state.previousPointer = self.state.currentPointer.copy()
        if not self.state.divertedPointer.isNull:
            self.state.currentPointer = self.state.divertedPointer.copy()
            self.state.divertedPointer = Pointer.Null()
            self.VisitChangedContainersDueToDivert()
            if not self.state.currentPointer.isNull:
                return

        successful_pointer_increment = self.IncrementContentPointer()
        if not successful_pointer_increment:
            did_pop = False
            if self.state.callStack.CanPop(PushPopType.Function):
                self.state.PopCallStack(PushPopType.Function)
                if self.state.inExpressionEvaluation:
                    self.state.PushEvaluationStack(Void())
                did_pop = True
            elif self.state.callStack.canPopThread:
                self.state.callStack.PopThread()
                did_pop = True
            else:
                self.state.TryExitFunctionEvaluationFromGame()
            if did_pop and not self.state.currentPointer.isNull:
                self.NextContent()

    def IncrementContentPointer(self):
        successful_increment = True
        pointer = self.state.callStack.currentElement.currentPointer.copy()
        pointer.index += 1
        if pointer.container is None:
            return throw_null_exception("pointer.container")
        while pointer.index >= len(pointer.container.content):
            successful_increment = False
            next_ancestor = as_or_null(pointer.container.parent, Container)
            if not isinstance(next_ancestor, Container):
                break
            try:
                index_in_ancestor = next_ancestor.content.index(pointer.container)
            except ValueError:
                break
            if index_in_ancestor == -1:
                break
            pointer = Pointer(next_ancestor, index_in_ancestor)
            pointer.index += 1
            successful_increment = True
            if pointer.container is None:
                return throw_null_exception("pointer.container")
        if not successful_increment:
            pointer = Pointer.Null()
        self.state.callStack.currentElement.currentPointer = pointer.copy()
        return successful_increment

    def TryFollowDefaultInvisibleChoice(self):
        all_choices = self._state.currentChoices
        invisible_choices = [c for c in all_choices if c.isInvisibleDefault]
        if len(invisible_choices) == 0 or len(all_choices) > len(invisible_choices):
            return False
        choice = invisible_choices[0]
        if choice.targetPath is None:
            return throw_null_exception("choice.targetPath")
        if choice.threadAtGeneration is None:
            return throw_null_exception("choice.threadAtGeneration")
        self.state.callStack.currentThread = choice.threadAtGeneration
        if self._stateSnapshotAtLastNewline is not None:
            self.state.callStack.currentThread = self.state.callStack.ForkThread()
        self.ChoosePath(choice.targetPath, False)
        return True

    def NextSequenceShuffleIndex(self):
        num_elements_int_val = as_or_null(self.state.PopEvaluationStack(), IntValue)
        if not isinstance(num_elements_int_val, IntValue):
            self.Error("expected number of elements in sequence for shuffle index")
            return 0
        seq_container = self.state.currentPointer.container
        if seq_container is None:
            return throw_null_exception("seqContainer")
        if num_elements_int_val.value is None:
            return throw_null_exception("numElementsIntVal.value")
        num_elements = num_elements_int_val.value
        seq_count_val = as_or_throws(self.state.PopEvaluationStack(), IntValue)
        seq_count = seq_count_val.value
        if seq_count is None:
            return throw_null_exception("seqCount")
        loop_index = seq_count // num_elements
        iteration_index = seq_count % num_elements
        seq_path_str = seq_container.path.toString()
        sequence_hash = sum(ord(ch) for ch in seq_path_str)
        random_seed = sequence_hash + loop_index + self.state.storySeed
        random = PRNG(int(random_seed))
        unpicked_indices = list(range(num_elements))
        for i in range(iteration_index + 1):
            chosen = random.next() % len(unpicked_indices)
            chosen_index = unpicked_indices.pop(chosen)
            if i == iteration_index:
                return chosen_index
        raise ValueError("Should never reach here")

    def Error(self, message: str, use_end_line_number: bool = False):
        e = StoryException(message)
        e.useEndLineNumber = use_end_line_number
        raise e

    def Warning(self, message: str):
        self.AddError(message, True)

    def AddError(self, message: str, is_warning: bool = False, use_end_line_number: bool = False):
        dm = self.currentDebugMetadata
        error_type_str = "WARNING" if is_warning else "ERROR"
        if dm is not None:
            line_num = dm.endLineNumber if use_end_line_number else dm.startLineNumber
            message = "RUNTIME " + error_type_str + ": '" + str(dm.fileName) + "' line " + str(line_num) + ": " + message
        elif not self.state.currentPointer.isNull:
            message = "RUNTIME " + error_type_str + ": (" + str(self.state.currentPointer) + "): " + message
        else:
            message = "RUNTIME " + error_type_str + ": " + message

        self.state.AddError(message, is_warning)
        if not is_warning:
            self.state.ForceEnd()

    def Assert(self, condition: bool, message: Optional[str] = None):
        if condition is False:
            if message is None:
                message = "Story assert"
            raise ValueError(message + " " + str(self.currentDebugMetadata))

    @property
    def currentDebugMetadata(self) -> Optional[DebugMetadata]:
        pointer = self.state.currentPointer
        if not pointer.isNull and pointer.Resolve() is not None:
            dm = pointer.Resolve().debugMetadata
            if dm is not None:
                return dm
        for element in reversed(self.state.callStack.elements):
            pointer = element.currentPointer
            if not pointer.isNull and pointer.Resolve() is not None:
                dm = pointer.Resolve().debugMetadata
                if dm is not None:
                    return dm
        for output_obj in reversed(self.state.outputStream):
            dm = output_obj.debugMetadata
            if dm is not None:
                return dm
        return None

    @property
    def mainContentContainer(self):
        if self._temporaryEvaluationContainer:
            return self._temporaryEvaluationContainer
        return self._mainContentContainer
