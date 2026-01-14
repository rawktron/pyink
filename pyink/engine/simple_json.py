from __future__ import annotations

import json
import re


class SimpleJson:
    @staticmethod
    def TextToDictionary(text: str):
        return SimpleJson.Reader(text).ToDictionary()

    @staticmethod
    def TextToArray(text: str):
        return SimpleJson.Reader(text).ToArray()

    class Reader:
        def __init__(self, text: str):
            if text.startswith("\ufeff"):
                text = text.lstrip("\ufeff")
            # Preserve "123.0" float intent by tagging as "123.0f" before parsing.
            json_with_explicit_float = re.sub(
                r'([,\[\s:])([0-9]+\.[0]+)([,\]\s}])',
                r'\1"\2f"\3',
                text,
            )
            self._root_object = json.loads(json_with_explicit_float)

        def ToDictionary(self):
            return self._root_object

        def ToArray(self):
            return self._root_object

    class Writer:
        class State:
            NoneState = 0
            Object = 1
            Array = 2
            Property = 3
            PropertyName = 4
            String = 5

        class StateElement:
            def __init__(self, state: int):
                self.state = state
                self.childCount = 0

        def __init__(self):
            self._jsonObject = None
            self._collectionStack = []
            self._stateStack = []
            self._propertyNameStack = []
            self._currentPropertyName = None
            self._currentString = None

        @property
        def state(self):
            if not self._stateStack:
                return SimpleJson.Writer.State.NoneState
            return self._stateStack[-1].state

        @property
        def childCount(self):
            if not self._stateStack:
                return 0
            return self._stateStack[-1].childCount

        @property
        def currentCollection(self):
            return self._collectionStack[-1] if self._collectionStack else None

        @property
        def currentPropertyName(self):
            return self._propertyNameStack[-1] if self._propertyNameStack else None

        def Assert(self, condition: bool):
            if not condition:
                raise AssertionError("JSON writer state invalid")

        def IncrementChildCount(self):
            if self._stateStack:
                self._stateStack[-1].childCount += 1

        def WriteObject(self, inner):
            self.WriteObjectStart()
            inner(self)
            self.WriteObjectEnd()

        def WriteObjectStart(self):
            self.StartNewObject(True)
            new_object = {}

            if self.state == SimpleJson.Writer.State.Property:
                self.Assert(self.currentCollection is not None)
                self.Assert(self.currentPropertyName is not None)
                property_name = self._propertyNameStack.pop()
                self.currentCollection[property_name] = new_object
                self._collectionStack.append(new_object)
            elif self.state == SimpleJson.Writer.State.Array:
                self.Assert(self.currentCollection is not None)
                self.currentCollection.append(new_object)
                self._collectionStack.append(new_object)
            else:
                self.Assert(self.state == SimpleJson.Writer.State.NoneState)
                self._jsonObject = new_object
                self._collectionStack.append(new_object)

            self._stateStack.append(SimpleJson.Writer.StateElement(SimpleJson.Writer.State.Object))

        def WriteObjectEnd(self):
            self.Assert(self.state == SimpleJson.Writer.State.Object)
            self._collectionStack.pop()
            self._stateStack.pop()

        def WriteProperty(self, name, inner_or_content):
            self.WritePropertyStart(name)
            if callable(inner_or_content):
                inner_or_content(self)
            else:
                self.Write(inner_or_content)
            self.WritePropertyEnd()

        def WriteIntProperty(self, name, content: int):
            self.WritePropertyStart(name)
            self.WriteInt(content)
            self.WritePropertyEnd()

        def WriteFloatProperty(self, name, content: float):
            self.WritePropertyStart(name)
            self.WriteFloat(content)
            self.WritePropertyEnd()

        def WritePropertyStart(self, name):
            self.Assert(self.state == SimpleJson.Writer.State.Object)
            self._propertyNameStack.append(name)
            self.IncrementChildCount()
            self._stateStack.append(SimpleJson.Writer.StateElement(SimpleJson.Writer.State.Property))

        def WritePropertyEnd(self):
            self.Assert(self.state == SimpleJson.Writer.State.Property)
            self.Assert(self.childCount == 1)
            self._stateStack.pop()

        def WritePropertyNameStart(self):
            self.Assert(self.state == SimpleJson.Writer.State.Object)
            self.IncrementChildCount()
            self._currentPropertyName = ""
            self._stateStack.append(SimpleJson.Writer.StateElement(SimpleJson.Writer.State.Property))
            self._stateStack.append(SimpleJson.Writer.StateElement(SimpleJson.Writer.State.PropertyName))

        def WritePropertyNameEnd(self):
            self.Assert(self.state == SimpleJson.Writer.State.PropertyName)
            self.Assert(self._currentPropertyName is not None)
            self._propertyNameStack.append(self._currentPropertyName)
            self._currentPropertyName = None
            self._stateStack.pop()

        def WritePropertyNameInner(self, str_value: str):
            self.Assert(self.state == SimpleJson.Writer.State.PropertyName)
            self.Assert(self._currentPropertyName is not None)
            self._currentPropertyName += str_value

        def WriteArrayStart(self):
            self.StartNewObject(True)
            new_object = []
            if self.state == SimpleJson.Writer.State.Property:
                self.Assert(self.currentCollection is not None)
                self.Assert(self.currentPropertyName is not None)
                property_name = self._propertyNameStack.pop()
                self.currentCollection[property_name] = new_object
                self._collectionStack.append(new_object)
            elif self.state == SimpleJson.Writer.State.Array:
                self.Assert(self.currentCollection is not None)
                self.currentCollection.append(new_object)
                self._collectionStack.append(new_object)
            else:
                self.Assert(self.state == SimpleJson.Writer.State.NoneState)
                self._jsonObject = new_object
                self._collectionStack.append(new_object)
            self._stateStack.append(SimpleJson.Writer.StateElement(SimpleJson.Writer.State.Array))

        def WriteArrayEnd(self):
            self.Assert(self.state == SimpleJson.Writer.State.Array)
            self._collectionStack.pop()
            self._stateStack.pop()

        def Write(self, value, escape: bool = True):
            if value is None:
                return
            self.StartNewObject(False)
            self._addToCurrentObject(value)

        def WriteBool(self, value):
            if value is None:
                return
            self.StartNewObject(False)
            self._addToCurrentObject(bool(value))

        def WriteInt(self, value):
            if value is None:
                return
            self.StartNewObject(False)
            self._addToCurrentObject(int(value))

        def WriteFloat(self, value):
            if value is None:
                return
            self.StartNewObject(False)
            if value == float("inf"):
                self._addToCurrentObject(3.4e38)
            elif value == float("-inf"):
                self._addToCurrentObject(-3.4e38)
            elif value != value:
                self._addToCurrentObject(0)
            else:
                num = float(value)
                if num.is_integer():
                    self._addToCurrentObject(int(num))
                else:
                    self._addToCurrentObject(num)

        def WriteNull(self):
            self.StartNewObject(False)
            self._addToCurrentObject(None)

        def WriteStringStart(self):
            self.StartNewObject(False)
            self._currentString = ""
            self._stateStack.append(SimpleJson.Writer.StateElement(SimpleJson.Writer.State.String))

        def WriteStringEnd(self):
            self.Assert(self.state == SimpleJson.Writer.State.String)
            self._stateStack.pop()
            self._addToCurrentObject(self._currentString)
            self._currentString = None

        def WriteStringInner(self, str_value, escape: bool = True):
            self.Assert(self.state == SimpleJson.Writer.State.String)
            if str_value is None:
                return
            self._currentString += str_value

        def toString(self):
            if self._jsonObject is None:
                return ""
            return json.dumps(self._jsonObject, separators=(",", ":"))

        def StartNewObject(self, container: bool):
            if container:
                self.Assert(
                    self.state in (SimpleJson.Writer.State.NoneState, SimpleJson.Writer.State.Property, SimpleJson.Writer.State.Array)
                )
            else:
                self.Assert(self.state in (SimpleJson.Writer.State.Property, SimpleJson.Writer.State.Array))
            if self.state == SimpleJson.Writer.State.Property:
                self.Assert(self.childCount == 0)
            if self.state in (SimpleJson.Writer.State.Array, SimpleJson.Writer.State.Property):
                self.IncrementChildCount()

        def _addToCurrentObject(self, obj):
            if self.state == SimpleJson.Writer.State.Property:
                property_name = self._propertyNameStack.pop()
                self.currentCollection[property_name] = obj
            elif self.state == SimpleJson.Writer.State.Array:
                self.currentCollection.append(obj)
