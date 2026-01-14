from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .debug import Debug
from .null_exception import throw_null_exception
from .type_assertion import as_or_null, as_inamed_content_or_null

if TYPE_CHECKING:
    from .path import Path
    from .container import Container
    from .debug_metadata import DebugMetadata
    from .search_result import SearchResult


class InkObject:
    def __init__(self):
        self.parent: Optional["InkObject"] = None
        self._debug_metadata: Optional["DebugMetadata"] = None
        self._path: Optional["Path"] = None

    @property
    def debugMetadata(self) -> Optional["DebugMetadata"]:
        if self._debug_metadata is None and self.parent is not None:
            return self.parent.debugMetadata
        return self._debug_metadata

    @debugMetadata.setter
    def debugMetadata(self, value: Optional["DebugMetadata"]):
        self._debug_metadata = value

    @property
    def ownDebugMetadata(self) -> Optional["DebugMetadata"]:
        return self._debug_metadata

    def DebugLineNumberOfPath(self, path: "Path"):
        if path is None:
            return None
        root = self.rootContentContainer
        if root:
            target_content = root.ContentAtPath(path).obj
            if target_content:
                dm = target_content.debugMetadata
                if dm is not None:
                    return dm.startLineNumber
        return None

    @property
    def path(self):
        from .path import Path
        from .container import Container

        if self._path is None:
            if self.parent is None:
                self._path = Path()
            else:
                comps = []
                child = self
                container = as_or_null(child.parent, Container)

                while container is not None:
                    named_child = as_inamed_content_or_null(child)
                    if named_child is not None and named_child.hasValidName:
                        if named_child.name is None:
                            return throw_null_exception("namedChild.name")
                        comps.insert(0, Path.Component(named_child.name))
                    else:
                        comps.insert(0, Path.Component(container.content.index(child)))
                    child = container
                    container = as_or_null(container.parent, Container)
                self._path = Path(comps)
        return self._path

    def ResolvePath(self, path: "Path") -> "SearchResult":
        if path is None:
            return throw_null_exception("path")
        if path.isRelative:
            from .container import Container

            nearest_container = as_or_null(self, Container)
            if nearest_container is None:
                Debug.Assert(self.parent is not None, "Can't resolve relative path because we don't have a parent")
                nearest_container = as_or_null(self.parent, Container)
                Debug.Assert(nearest_container is not None, "Expected parent to be a container")
                Debug.Assert(path.GetComponent(0).isParent)
                path = path.tail
            if nearest_container is None:
                return throw_null_exception("nearest_container")
            return nearest_container.ContentAtPath(path)
        else:
            content_container = self.rootContentContainer
            if content_container is None:
                return throw_null_exception("content_container")
            return content_container.ContentAtPath(path)

    def ConvertPathToRelative(self, global_path: "Path"):
        from .path import Path

        own_path = self.path
        min_path_length = min(global_path.length, own_path.length)
        last_shared_path_comp_index = -1

        for i in range(min_path_length):
            own_comp = own_path.GetComponent(i)
            other_comp = global_path.GetComponent(i)
            if own_comp.Equals(other_comp):
                last_shared_path_comp_index = i
            else:
                break

        if last_shared_path_comp_index == -1:
            return global_path

        num_upwards_moves = own_path.componentCount - 1 - last_shared_path_comp_index

        new_path_comps = []
        for _ in range(num_upwards_moves):
            new_path_comps.append(Path.Component.ToParent())
        for down in range(last_shared_path_comp_index + 1, global_path.componentCount):
            new_path_comps.append(global_path.GetComponent(down))

        return Path(new_path_comps, True)

    def CompactPathString(self, other_path: "Path"):
        if other_path.isRelative:
            relative_path_str = other_path.componentsString
            global_path_str = self.path.PathByAppendingPath(other_path).componentsString
        else:
            relative_path = self.ConvertPathToRelative(other_path)
            relative_path_str = relative_path.componentsString
            global_path_str = other_path.componentsString

        return relative_path_str if len(relative_path_str) < len(global_path_str) else global_path_str

    @property
    def rootContentContainer(self):
        ancestor = self
        while ancestor.parent:
            ancestor = ancestor.parent
        from .container import Container

        return as_or_null(ancestor, Container)

    def Copy(self):
        raise NotImplementedError("Doesn't support copying")

    def SetChild(self, obj, prop: str, value):
        if getattr(obj, prop, None) is not None:
            setattr(obj, prop, None)
        setattr(obj, prop, value)
        if getattr(obj, prop, None) is not None:
            getattr(obj, prop).parent = self

    def Equals(self, obj):
        return obj is self
