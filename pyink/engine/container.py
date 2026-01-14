from __future__ import annotations

from typing import Dict, List, Optional

from .debug import Debug
from .null_exception import throw_null_exception
from .object import InkObject
from .path import Path
from .search_result import SearchResult
from .string_builder import StringBuilder
from .try_get_result import try_get_value_from_map
from .type_assertion import as_inamed_content_or_null, as_or_null, as_or_throws
from .value import StringValue


class Container(InkObject):
    class CountFlags:
        Start = 0
        Visits = 1
        Turns = 2
        CountStartOnly = 4

    def __init__(self):
        super().__init__()
        self.name: Optional[str] = None
        self._content: List[InkObject] = []
        self.namedContent: Dict[str, object] = {}
        self.visitsShouldBeCounted = False
        self.turnIndexShouldBeCounted = False
        self.countingAtStartOnly = False
        self._pathToFirstLeafContent: Optional[Path] = None

    @property
    def hasValidName(self):
        return self.name is not None and len(self.name) > 0

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value: List[InkObject]):
        self.AddContent(value)

    @property
    def namedOnlyContent(self):
        named_only_content_dict: Optional[Dict[str, InkObject]] = {}
        for key, value in self.namedContent.items():
            ink_object = as_or_throws(value, InkObject)
            named_only_content_dict[key] = ink_object

        for content in self.content:
            named = as_inamed_content_or_null(content)
            if named is not None and named.hasValidName:
                if named.name in named_only_content_dict:
                    del named_only_content_dict[named.name]

        if not named_only_content_dict:
            named_only_content_dict = None
        return named_only_content_dict

    @namedOnlyContent.setter
    def namedOnlyContent(self, value: Optional[Dict[str, InkObject]]):
        existing_named_only = self.namedOnlyContent
        if existing_named_only:
            for key in list(existing_named_only.keys()):
                if key in self.namedContent:
                    del self.namedContent[key]
        if value is None:
            return
        for val in value.values():
            named = as_inamed_content_or_null(val)
            if named is not None:
                self.AddToNamedContentOnly(named)

    @property
    def countFlags(self):
        flags = 0
        if self.visitsShouldBeCounted:
            flags |= Container.CountFlags.Visits
        if self.turnIndexShouldBeCounted:
            flags |= Container.CountFlags.Turns
        if self.countingAtStartOnly:
            flags |= Container.CountFlags.CountStartOnly
        if flags == Container.CountFlags.CountStartOnly:
            flags = 0
        return flags

    @countFlags.setter
    def countFlags(self, value: int):
        if value & Container.CountFlags.Visits:
            self.visitsShouldBeCounted = True
        if value & Container.CountFlags.Turns:
            self.turnIndexShouldBeCounted = True
        if value & Container.CountFlags.CountStartOnly:
            self.countingAtStartOnly = True

    @property
    def pathToFirstLeafContent(self):
        if self._pathToFirstLeafContent is None:
            self._pathToFirstLeafContent = self.path.PathByAppendingPath(self.internalPathToFirstLeafContent)
        return self._pathToFirstLeafContent

    @property
    def internalPathToFirstLeafContent(self):
        components = []
        container = self
        while isinstance(container, Container):
            if container.content:
                components.append(Path.Component(0))
                container = container.content[0]
            else:
                break
        return Path(components)

    def AddContent(self, content_obj_or_list):
        if isinstance(content_obj_or_list, list):
            for content in content_obj_or_list:
                self.AddContent(content)
        else:
            content_obj = content_obj_or_list
            self._content.append(content_obj)
            if content_obj.parent:
                raise ValueError("content is already in " + str(content_obj.parent))
            content_obj.parent = self
            self.TryAddNamedContent(content_obj)

    def TryAddNamedContent(self, content_obj: InkObject):
        named_content_obj = as_inamed_content_or_null(content_obj)
        if named_content_obj is not None and named_content_obj.hasValidName:
            self.AddToNamedContentOnly(named_content_obj)

    def AddToNamedContentOnly(self, named_content_obj):
        Debug.AssertType(named_content_obj, InkObject, "Can only add Runtime.Objects to a Runtime.Container")
        runtime_obj = as_or_throws(named_content_obj, InkObject)
        runtime_obj.parent = self
        if named_content_obj.name is None:
            return throw_null_exception("namedContentObj.name")
        self.namedContent[named_content_obj.name] = named_content_obj

    def ContentAtPath(self, path: Path, partial_path_start: int = 0, partial_path_length: int = -1):
        if partial_path_length == -1:
            partial_path_length = path.length

        result = SearchResult()
        result.approximate = False

        current_container: Optional[Container] = self
        current_obj: InkObject = self

        for i in range(partial_path_start, partial_path_length):
            comp = path.GetComponent(i)
            if current_container is None:
                result.approximate = True
                break

            found_obj = current_container.ContentWithPathComponent(comp)
            if found_obj is None:
                result.approximate = True
                break

            next_container = as_or_null(found_obj, Container)
            if i < partial_path_length - 1 and next_container is None:
                result.approximate = True
                break

            current_obj = found_obj
            current_container = next_container

        result.obj = current_obj
        return result

    def InsertContent(self, content_obj: InkObject, index: int):
        self.content.insert(index, content_obj)
        if content_obj.parent:
            raise ValueError("content is already in " + str(content_obj.parent))
        content_obj.parent = self
        self.TryAddNamedContent(content_obj)

    def AddContentsOfContainer(self, other_container: "Container"):
        self.content.extend(other_container.content)
        for obj in other_container.content:
            obj.parent = self
            self.TryAddNamedContent(obj)

    def ContentWithPathComponent(self, component: Path.Component):
        if component.isIndex:
            if 0 <= component.index < len(self.content):
                return self.content[component.index]
            return None
        if component.isParent:
            return self.parent
        if component.name is None:
            return throw_null_exception("component.name")
        found_content = try_get_value_from_map(self.namedContent, component.name, None)
        if found_content.exists:
            return as_or_throws(found_content.result, InkObject)
        return None

    def BuildStringOfHierarchy(self, sb: StringBuilder | None = None, indentation: int = 0, pointed_obj=None):
        if sb is None:
            sb = StringBuilder()
            self.BuildStringOfHierarchy(sb, 0, None)
            return str(sb)

        def append_indentation():
            spaces_per_indent = 4
            sb.Append(" " * (spaces_per_indent * indentation))

        append_indentation()
        sb.Append("[")
        if self.hasValidName:
            sb.AppendFormat(" ({0})", self.name)
        if self == pointed_obj:
            sb.Append("  <---")
        sb.AppendLine()

        indentation += 1
        for i, obj in enumerate(self.content):
            if isinstance(obj, Container):
                obj.BuildStringOfHierarchy(sb, indentation, pointed_obj)
            else:
                append_indentation()
                if isinstance(obj, StringValue):
                    sb.Append('"')
                    sb.Append(str(obj).replace("\n", "\\n"))
                    sb.Append('"')
                else:
                    sb.Append(str(obj))
            if i != len(self.content) - 1:
                sb.Append(",")
            if not isinstance(obj, Container) and obj == pointed_obj:
                sb.Append("  <---")
            sb.AppendLine()

        only_named: Dict[str, object] = {}
        for key, value in self.namedContent.items():
            if as_or_throws(value, InkObject) in self.content:
                continue
            only_named[key] = value

        if only_named:
            append_indentation()
            sb.AppendLine("-- named: --")
            for value in only_named.values():
                Debug.AssertType(value, Container, "Can only print out named Containers")
                container = value
                container.BuildStringOfHierarchy(sb, indentation, pointed_obj)
                sb.AppendLine()

        indentation -= 1
        append_indentation()
        sb.Append("]")
        return str(sb)
