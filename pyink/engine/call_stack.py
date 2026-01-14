from __future__ import annotations

from typing import List, Optional

from .debug import Debug
from .json_serialisation import JsonSerialisation
from .null_exception import throw_null_exception
from .path import Path
from .pointer import Pointer
from .push_pop import PushPopType
from .simple_json import SimpleJson
from .string_builder import StringBuilder
from .try_get_result import try_get_value_from_map
from .value import ListValue


class CallStack:
    class Element:
        def __init__(self, stack_type: PushPopType, pointer: Pointer, in_expression_evaluation: bool = False):
            self.currentPointer = pointer.copy()
            self.inExpressionEvaluation = in_expression_evaluation
            self.temporaryVariables = {}
            self.type = stack_type
            self.evaluationStackHeightWhenPushed = 0
            self.functionStartInOutputStream = 0

        def Copy(self):
            copy = CallStack.Element(self.type, self.currentPointer, self.inExpressionEvaluation)
            copy.temporaryVariables = dict(self.temporaryVariables)
            copy.evaluationStackHeightWhenPushed = self.evaluationStackHeightWhenPushed
            copy.functionStartInOutputStream = self.functionStartInOutputStream
            return copy

    class Thread:
        def __init__(self, j_thread_obj=None, story_context=None):
            self.callstack: List[CallStack.Element] = []
            self.threadIndex = 0
            self.previousPointer = Pointer.Null()

            if j_thread_obj is not None and story_context is not None:
                self.threadIndex = int(j_thread_obj.get("threadIndex", 0))
                j_thread_callstack = j_thread_obj.get("callstack", [])

                for j_el_tok in j_thread_callstack:
                    j_element_obj = j_el_tok
                    push_pop_type = PushPopType(int(j_element_obj.get("type")))
                    pointer = Pointer.Null()
                    current_container_path_str_token = j_element_obj.get("cPath")
                    if current_container_path_str_token is not None:
                        current_container_path_str = str(current_container_path_str_token)
                        thread_pointer_result = story_context.ContentAtPath(Path(current_container_path_str))
                        pointer.container = thread_pointer_result.container
                        pointer.index = int(j_element_obj.get("idx"))

                        if thread_pointer_result.obj is None:
                            raise ValueError(
                                "When loading state, internal story location couldn't be found: "
                                + current_container_path_str
                                + ". Has the story changed since this save data was created?"
                            )
                        if thread_pointer_result.approximate:
                            if pointer.container is not None:
                                story_context.Warning(
                                    "When loading state, exact internal story location couldn't be found: '"
                                    + current_container_path_str
                                    + "', so it was approximated to '"
                                    + pointer.container.path.componentsString
                                    + "' to recover. Has the story changed since this save data was created?"
                                )
                            else:
                                story_context.Warning(
                                    "When loading state, exact internal story location couldn't be found: '"
                                    + current_container_path_str
                                    + "' and it may not be recoverable. Has the story changed since this save data was created?"
                                )

                    in_expression_evaluation = bool(j_element_obj.get("exp"))
                    el = CallStack.Element(push_pop_type, pointer, in_expression_evaluation)
                    temps = j_element_obj.get("temp")
                    if temps is not None:
                        el.temporaryVariables = JsonSerialisation.JObjectToDictionaryRuntimeObjs(temps)
                    else:
                        el.temporaryVariables = {}
                    self.callstack.append(el)

                prev_content_obj_path = j_thread_obj.get("previousContentObject")
                if prev_content_obj_path is not None:
                    prev_path = Path(str(prev_content_obj_path))
                    self.previousPointer = story_context.PointerAtPath(prev_path)

        def Copy(self):
            copy = CallStack.Thread()
            copy.threadIndex = self.threadIndex
            for element in self.callstack:
                copy.callstack.append(element.Copy())
            copy.previousPointer = self.previousPointer.copy()
            return copy

        def WriteJson(self, writer: SimpleJson.Writer):
            writer.WriteObjectStart()

            writer.WritePropertyStart("callstack")
            writer.WriteArrayStart()
            for el in self.callstack:
                writer.WriteObjectStart()
                if not el.currentPointer.isNull:
                    if el.currentPointer.container is None:
                        return throw_null_exception("el.currentPointer.container")
                    writer.WriteProperty("cPath", el.currentPointer.container.path.componentsString)
                    writer.WriteIntProperty("idx", el.currentPointer.index)
                writer.WriteProperty("exp", el.inExpressionEvaluation)
                writer.WriteIntProperty("type", el.type)
                if len(el.temporaryVariables) > 0:
                    writer.WritePropertyStart("temp")
                    JsonSerialisation.WriteDictionaryRuntimeObjs(writer, el.temporaryVariables)
                    writer.WritePropertyEnd()
                writer.WriteObjectEnd()
            writer.WriteArrayEnd()
            writer.WritePropertyEnd()

            writer.WriteIntProperty("threadIndex", self.threadIndex)

            if not self.previousPointer.isNull:
                resolved_pointer = self.previousPointer.Resolve()
                if resolved_pointer is None:
                    return throw_null_exception("this.previousPointer.Resolve()")
                writer.WriteProperty("previousContentObject", resolved_pointer.path.toString())
            writer.WriteObjectEnd()

    def __init__(self, story_context=None, to_copy=None):
        self._threadCounter = 0
        if story_context is not None:
            self._startOfRoot = Pointer.StartOf(story_context.rootContentContainer)
            self.Reset()
        elif to_copy is not None:
            self._threads = [thread.Copy() for thread in to_copy._threads]
            self._threadCounter = to_copy._threadCounter
            self._startOfRoot = to_copy._startOfRoot.copy()
        else:
            self._startOfRoot = Pointer.Null()
            self._threads = []
            self._threadCounter = 0

    @property
    def elements(self):
        return self.callStack

    @property
    def depth(self):
        return len(self.elements)

    @property
    def currentElement(self):
        thread = self._threads[-1]
        cs = thread.callstack
        return cs[-1]

    @property
    def currentElementIndex(self):
        return len(self.callStack) - 1

    @property
    def currentThread(self):
        return self._threads[-1]

    @currentThread.setter
    def currentThread(self, value):
        Debug.Assert(len(self._threads) == 1, "Shouldn't be directly setting the current thread when we have a stack of them")
        self._threads = [value]

    @property
    def canPop(self):
        return len(self.callStack) > 1

    def Reset(self):
        self._threads = [CallStack.Thread()]
        self._threads[0].callstack.append(CallStack.Element(PushPopType.Tunnel, self._startOfRoot))

    def SetJsonToken(self, j_object, story_context):
        self._threads = []
        j_threads = j_object.get("threads", [])
        for j_thread_tok in j_threads:
            thread = CallStack.Thread(j_thread_tok, story_context)
            self._threads.append(thread)
        self._threadCounter = int(j_object.get("threadCounter", 0))
        self._startOfRoot = Pointer.StartOf(story_context.rootContentContainer)

    def WriteJson(self, writer: SimpleJson.Writer):
        writer.WriteObject(lambda w: self._write_json_inner(w))

    def _write_json_inner(self, writer: SimpleJson.Writer):
        writer.WritePropertyStart("threads")
        writer.WriteArrayStart()
        for thread in self._threads:
            thread.WriteJson(writer)
        writer.WriteArrayEnd()
        writer.WritePropertyEnd()

        writer.WritePropertyStart("threadCounter")
        writer.WriteInt(self._threadCounter)
        writer.WritePropertyEnd()

    def PushThread(self):
        new_thread = self.currentThread.Copy()
        self._threadCounter += 1
        new_thread.threadIndex = self._threadCounter
        self._threads.append(new_thread)

    def ForkThread(self):
        forked_thread = self.currentThread.Copy()
        self._threadCounter += 1
        forked_thread.threadIndex = self._threadCounter
        return forked_thread

    def PopThread(self):
        if self.canPopThread:
            self._threads.pop()
        else:
            raise ValueError("Can't pop thread")

    @property
    def canPopThread(self):
        return len(self._threads) > 1 and not self.elementIsEvaluateFromGame

    @property
    def elementIsEvaluateFromGame(self):
        return self.currentElement.type == PushPopType.FunctionEvaluationFromGame

    def Push(self, stack_type: PushPopType, external_evaluation_stack_height: int = 0, output_stream_length_with_pushed: int = 0):
        element = CallStack.Element(stack_type, self.currentElement.currentPointer, False)
        element.evaluationStackHeightWhenPushed = external_evaluation_stack_height
        element.functionStartInOutputStream = output_stream_length_with_pushed
        self.callStack.append(element)

    def CanPop(self, stack_type: PushPopType | None = None):
        if not self.canPop:
            return False
        if stack_type is None:
            return True
        return self.currentElement.type == stack_type

    def Pop(self, stack_type: PushPopType | None = None):
        if self.CanPop(stack_type):
            self.callStack.pop()
        else:
            raise ValueError("Mismatched push/pop in Callstack")

    def GetTemporaryVariableWithName(self, name: str | None, context_index: int = -1):
        if context_index == -1:
            context_index = self.currentElementIndex + 1
        context_element = self.callStack[context_index - 1]
        var_value = try_get_value_from_map(context_element.temporaryVariables, name, None)
        return var_value.result if var_value.exists else None

    def SetTemporaryVariable(self, name: str, value, declare_new: bool, context_index: int = -1):
        if context_index == -1:
            context_index = self.currentElementIndex + 1
        context_element = self.callStack[context_index - 1]
        if not declare_new and name not in context_element.temporaryVariables:
            raise ValueError("Could not find temporary variable to set: " + name)
        old_value = try_get_value_from_map(context_element.temporaryVariables, name, None)
        if old_value.exists:
            ListValue.RetainListOriginsForAssignment(old_value.result, value)
        context_element.temporaryVariables[name] = value

    def ContextForVariableNamed(self, name: str):
        if name in self.currentElement.temporaryVariables:
            return self.currentElementIndex + 1
        return 0

    def ThreadWithIndex(self, index: int):
        for t in self._threads:
            if t.threadIndex == index:
                return t
        return None

    @property
    def callStack(self):
        return self.currentThread.callstack

    @property
    def callStackTrace(self):
        sb = StringBuilder()
        for t, thread in enumerate(self._threads):
            is_current = t == len(self._threads) - 1
            sb.AppendFormat(
                "=== THREAD {0}/{1} {2}===\n", t + 1, len(self._threads), "(current) " if is_current else ""
            )
            for i, element in enumerate(thread.callstack):
                if element.type == PushPopType.Function:
                    sb.Append("  [FUNCTION] ")
                else:
                    sb.Append("  [TUNNEL] ")
                pointer = element.currentPointer
                if not pointer.isNull:
                    sb.Append("<SOMEWHERE IN ")
                    if pointer.container is None:
                        return throw_null_exception("pointer.container")
                    sb.Append(pointer.container.path.componentsString)
                    sb.AppendLine(">")
        return str(sb)
