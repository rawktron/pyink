from __future__ import annotations

from typing import Dict, Set

from .try_get_result import TryGetResult


class StatePatch:
    def __init__(self, to_copy=None):
        if to_copy is not None:
            self._globals = dict(to_copy._globals)
            self._changedVariables = set(to_copy._changedVariables)
            self._visitCounts = dict(to_copy._visitCounts)
            self._turnIndices = dict(to_copy._turnIndices)
        else:
            self._globals = {}
            self._changedVariables = set()
            self._visitCounts = {}
            self._turnIndices = {}

    @property
    def globals(self):
        return self._globals

    @property
    def changedVariables(self):
        return self._changedVariables

    @property
    def visitCounts(self):
        return self._visitCounts

    @property
    def turnIndices(self):
        return self._turnIndices

    def TryGetGlobal(self, name: str | None, value):
        if name is not None and name in self._globals:
            return TryGetResult(self._globals.get(name), True)
        return TryGetResult(value, False)

    def SetGlobal(self, name: str, value):
        self._globals[name] = value

    def AddChangedVariable(self, name: str):
        self._changedVariables.add(name)

    def TryGetVisitCount(self, container, count: int):
        if container in self._visitCounts:
            return TryGetResult(self._visitCounts.get(container), True)
        return TryGetResult(count, False)

    def SetVisitCount(self, container, count: int):
        self._visitCounts[container] = count

    def SetTurnIndex(self, container, index: int):
        self._turnIndices[container] = index

    def TryGetTurnIndex(self, container, index: int):
        if container in self._turnIndices:
            return TryGetResult(self._turnIndices.get(container), True)
        return TryGetResult(index, False)
