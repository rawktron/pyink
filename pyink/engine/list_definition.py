from __future__ import annotations

from typing import Dict

from .ink_list import InkListItem
from .try_get_result import TryGetResult


class ListDefinition:
    def __init__(self, name: str, items: Dict[str, int] | None):
        self._name = name or ""
        self._items = None
        self._itemNameToValues = items or {}

    @property
    def name(self):
        return self._name

    @property
    def items(self):
        if self._items is None:
            self._items = {}
            for key, value in self._itemNameToValues.items():
                item = InkListItem(self.name, key)
                self._items[item.serialized()] = value
        return self._items

    def ValueForItem(self, item: InkListItem):
        if not item.itemName:
            return 0
        int_val = self._itemNameToValues.get(item.itemName)
        return int_val if int_val is not None else 0

    def ContainsItem(self, item: InkListItem):
        if not item.itemName:
            return False
        if item.originName != self.name:
            return False
        return item.itemName in self._itemNameToValues

    def ContainsItemWithName(self, item_name: str):
        return item_name in self._itemNameToValues

    def TryGetItemWithValue(self, val: int, item: InkListItem):
        for key, value in self._itemNameToValues.items():
            if value == val:
                item = InkListItem(self.name, key)
                return TryGetResult(item, True)
        return TryGetResult(InkListItem.Null(), False)

    def TryGetValueForItem(self, item: InkListItem, int_val: int):
        if not item.itemName:
            return TryGetResult(0, False)
        value = self._itemNameToValues.get(item.itemName)
        if value is None:
            return TryGetResult(0, False)
        return TryGetResult(value, True)
