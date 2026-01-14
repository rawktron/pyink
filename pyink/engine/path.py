from __future__ import annotations

import re
from typing import List, Optional


class Path:
    parentId = "^"

    class Component:
        def __init__(self, index_or_name):
            self.index = -1
            self.name = None
            if isinstance(index_or_name, str):
                self.name = index_or_name
            else:
                self.index = int(index_or_name)

        @property
        def isIndex(self) -> bool:
            return self.index >= 0

        @property
        def isParent(self) -> bool:
            return self.name == Path.parentId

        @staticmethod
        def ToParent() -> "Path.Component":
            return Path.Component(Path.parentId)

        def __str__(self):
            return str(self.index) if self.isIndex else self.name

        def Equals(self, other_comp: "Path.Component") -> bool:
            if other_comp is not None and other_comp.isIndex == self.isIndex:
                if self.isIndex:
                    return self.index == other_comp.index
                return self.name == other_comp.name
            return False

    def __init__(self, *args):
        self._components: List[Path.Component] = []
        self._componentsString: Optional[str] = None
        self._isRelative = False

        if len(args) == 1 and isinstance(args[0], str):
            self.componentsString = args[0]
        elif len(args) == 2 and isinstance(args[0], Path.Component) and isinstance(args[1], Path):
            head = args[0]
            tail = args[1]
            self._components.append(head)
            self._components.extend(tail._components)
        elif len(args) >= 1 and isinstance(args[0], list):
            head = args[0]
            relative = bool(args[1]) if len(args) > 1 else False
            self._components.extend(head)
            self._isRelative = relative

    @property
    def isRelative(self):
        return self._isRelative

    @property
    def componentCount(self) -> int:
        return len(self._components)

    @property
    def head(self) -> Optional["Path.Component"]:
        return self._components[0] if self._components else None

    @property
    def tail(self) -> "Path":
        if len(self._components) >= 2:
            return Path(self._components[1:])
        return Path.self()

    @property
    def length(self) -> int:
        return len(self._components)

    @property
    def lastComponent(self) -> Optional["Path.Component"]:
        if not self._components:
            return None
        return self._components[-1]

    @property
    def containsNamedComponent(self) -> bool:
        return any(not comp.isIndex for comp in self._components)

    @staticmethod
    def self() -> "Path":
        path = Path()
        path._isRelative = True
        return path

    def GetComponent(self, index: int) -> "Path.Component":
        return self._components[index]

    def PathByAppendingPath(self, path_to_append: "Path") -> "Path":
        p = Path()
        upward_moves = 0
        for comp in path_to_append._components:
            if comp.isParent:
                upward_moves += 1
            else:
                break

        for i in range(len(self._components) - upward_moves):
            p._components.append(self._components[i])

        for i in range(upward_moves, len(path_to_append._components)):
            p._components.append(path_to_append._components[i])

        return p

    @property
    def componentsString(self) -> str:
        if self._componentsString is None:
            self._componentsString = ".".join(str(comp) for comp in self._components)
            if self.isRelative:
                self._componentsString = "." + self._componentsString
        return self._componentsString

    @componentsString.setter
    def componentsString(self, value: str):
        self._components = []
        self._componentsString = value
        if not self._componentsString:
            return
        if self._componentsString[0] == ".":
            self._isRelative = True
            self._componentsString = self._componentsString[1:]

        component_strings = self._componentsString.split(".")
        for comp_str in component_strings:
            if re.match(r"^(\-|\+)?([0-9]+|Infinity)$", comp_str):
                self._components.append(Path.Component(int(comp_str)))
            else:
                self._components.append(Path.Component(comp_str))

    def __str__(self) -> str:
        return self.componentsString

    def toString(self) -> str:
        return self.componentsString

    def Equals(self, other_path: Optional["Path"]) -> bool:
        if other_path is None:
            return False
        if len(other_path._components) != len(self._components):
            return False
        if other_path.isRelative != self.isRelative:
            return False
        for idx, other_comp in enumerate(other_path._components):
            if not other_comp.Equals(self._components[idx]):
                return False
        return True

    def PathByAppendingComponent(self, comp: "Path.Component") -> "Path":
        p = Path()
        p._components.extend(self._components)
        p._components.append(comp)
        return p
