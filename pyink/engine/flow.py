from __future__ import annotations

from .call_stack import CallStack
from .choice import Choice
from .json_serialisation import JsonSerialisation
from .null_exception import throw_null_exception
from .simple_json import SimpleJson


class Flow:
    def __init__(self, name: str, story, j_object=None):
        self.name = name
        self.callStack = CallStack(story_context=story)
        if j_object is not None:
            self.callStack.SetJsonToken(j_object["callstack"], story)
            self.outputStream = JsonSerialisation.JArrayToRuntimeObjList(j_object["outputStream"])
            self.currentChoices = JsonSerialisation.JArrayToRuntimeObjList(j_object["currentChoices"])
            j_choice_threads_obj = j_object.get("choiceThreads")
            if j_choice_threads_obj is not None:
                self.LoadFlowChoiceThreads(j_choice_threads_obj, story)
        else:
            self.outputStream = []
            self.currentChoices = []

    def WriteJson(self, writer: SimpleJson.Writer):
        writer.WriteObjectStart()
        writer.WriteProperty("callstack", lambda w: self.callStack.WriteJson(w))
        writer.WriteProperty("outputStream", lambda w: JsonSerialisation.WriteListRuntimeObjs(w, self.outputStream))

        has_choice_threads = False
        for c in self.currentChoices:
            if c.threadAtGeneration is None:
                return throw_null_exception("c.threadAtGeneration")
            c.originalThreadIndex = c.threadAtGeneration.threadIndex
            if self.callStack.ThreadWithIndex(c.originalThreadIndex) is None:
                if not has_choice_threads:
                    has_choice_threads = True
                    writer.WritePropertyStart("choiceThreads")
                    writer.WriteObjectStart()
                writer.WritePropertyStart(c.originalThreadIndex)
                c.threadAtGeneration.WriteJson(writer)
                writer.WritePropertyEnd()

        if has_choice_threads:
            writer.WriteObjectEnd()
            writer.WritePropertyEnd()

        def write_choices(w):
            w.WriteArrayStart()
            for c in self.currentChoices:
                JsonSerialisation.WriteChoice(w, c)
            w.WriteArrayEnd()

        writer.WriteProperty("currentChoices", write_choices)
        writer.WriteObjectEnd()

    def LoadFlowChoiceThreads(self, j_choice_threads, story):
        for choice in self.currentChoices:
            found_active_thread = self.callStack.ThreadWithIndex(choice.originalThreadIndex)
            if found_active_thread is not None:
                choice.threadAtGeneration = found_active_thread.Copy()
            else:
                j_saved_choice_thread = j_choice_threads.get(str(choice.originalThreadIndex))
                choice.threadAtGeneration = CallStack.Thread(j_saved_choice_thread, story)
