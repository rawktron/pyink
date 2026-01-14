from __future__ import annotations

from typing import Dict, List

from .ink_list import InkListItem
from .list_definition import ListDefinition
from .null_exception import throw_null_exception
from .try_get_result import TryGetResult
from .value import ListValue


class ListDefinitionsOrigin:
    def __init__(self, lists: List[ListDefinition]):
        self._lists: Dict[str, ListDefinition] = {}
        self._allUnambiguousListValueCache: Dict[str, ListValue] = {}

        for list_def in lists:
            self._lists[list_def.name] = list_def

            for key, val in list_def.items.items():
                item = InkListItem.fromSerializedKey(key)
                list_value = ListValue(item, val)

                if not item.itemName:
                    raise ValueError("item.itemName is null or undefined.")

                self._allUnambiguousListValueCache[item.itemName] = list_value
                self._allUnambiguousListValueCache[item.fullName] = list_value

    @property
    def lists(self) -> List[ListDefinition]:
        return list(self._lists.values())

    def TryListGetDefinition(self, name: str | None, definition: ListDefinition | None):
        if name is None:
            return TryGetResult(definition, False)
        list_def = self._lists.get(name)
        if list_def is None:
            return TryGetResult(definition, False)
        return TryGetResult(list_def, True)

    def FindSingleItemListWithName(self, name: str | None):
        if name is None:
            return throw_null_exception("name")
        return self._allUnambiguousListValueCache.get(name)
