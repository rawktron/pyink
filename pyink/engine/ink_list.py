from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Optional

from .null_exception import throw_null_exception
from .string_builder import StringBuilder


@dataclass
class KeyValuePair:
    Key: "InkListItem"
    Value: int


class InkListItem:
    def __init__(self, origin_name: Optional[str] = None, item_name: Optional[str] = None):
        self.originName = None
        self.itemName = None
        if item_name is not None or origin_name is None:
            self.originName = origin_name
            self.itemName = item_name
        elif origin_name:
            full_name = origin_name
            name_parts = full_name.split(".")
            self.originName = name_parts[0]
            self.itemName = name_parts[1] if len(name_parts) > 1 else None

    @staticmethod
    def Null():
        return InkListItem(None, None)

    @property
    def isNull(self):
        return self.originName is None and self.itemName is None

    @property
    def fullName(self):
        return (self.originName if self.originName is not None else "?") + "." + str(self.itemName)

    def __str__(self):
        return self.fullName

    def Equals(self, obj: "InkListItem"):
        if isinstance(obj, InkListItem):
            return obj.itemName == self.itemName and obj.originName == self.originName
        return False

    def copy(self):
        return InkListItem(self.originName, self.itemName)

    def serialized(self) -> str:
        return json.dumps({"originName": self.originName, "itemName": self.itemName})

    @staticmethod
    def fromSerializedKey(key: str) -> "InkListItem":
        try:
            obj = json.loads(key)
        except json.JSONDecodeError:
            return InkListItem.Null()

        if not isinstance(obj, dict):
            return InkListItem.Null()
        if "originName" not in obj or "itemName" not in obj:
            return InkListItem.Null()
        origin_name = obj.get("originName")
        item_name = obj.get("itemName")
        if (origin_name is not None and not isinstance(origin_name, str)) or (
            item_name is not None and not isinstance(item_name, str)
        ):
            return InkListItem.Null()
        return InkListItem(origin_name, item_name)


class InkList(dict):
    def __init__(self, *args):
        super().__init__()
        self.origins: Optional[List["ListDefinition"]] = None
        self._originNames: Optional[List[str]] = []

        if len(args) == 1 and isinstance(args[0], InkList):
            other_list: InkList = args[0]
            self.update(other_list)
            other_origin_names = other_list.originNames
            if other_origin_names is not None:
                self._originNames = list(other_origin_names)
            if other_list.origins is not None:
                self.origins = list(other_list.origins)
        elif len(args) == 2 and isinstance(args[0], str):
            single_origin_list_name = args[0]
            origin_story = args[1]
            self.SetInitialOriginName(single_origin_list_name)
            if origin_story.listDefinitions is None:
                return throw_null_exception("originStory.listDefinitions")
            definition = origin_story.listDefinitions.TryListGetDefinition(single_origin_list_name, None)
            if definition.exists:
                if definition.result is None:
                    return throw_null_exception("def.result")
                self.origins = [definition.result]
            else:
                raise ValueError(
                    "InkList origin could not be found in story when constructing new list: "
                    + single_origin_list_name
                )
        elif len(args) == 1 and isinstance(args[0], dict) and "Key" in args[0] and "Value" in args[0]:
            single_element = args[0]
            self.Add(single_element["Key"], single_element["Value"])

    @staticmethod
    def FromString(my_list_item: str, origin_story):
        if not my_list_item:
            return InkList()
        list_value = origin_story.listDefinitions.FindSingleItemListWithName(my_list_item)
        if list_value:
            if list_value.value is None:
                return throw_null_exception("listValue.value")
            return InkList(list_value.value)
        raise ValueError(
            "Could not find the InkListItem from the string '"
            + my_list_item
            + "' to create an InkList because it doesn't exist in the original list definition in ink."
        )

    def AddItem(self, item_or_item_name, story_object=None):
        from .list_definition import ListDefinition

        if isinstance(item_or_item_name, InkListItem):
            item = item_or_item_name

            if item.originName is None:
                self.AddItem(item.itemName)
                return

            if self.origins is None:
                return throw_null_exception("self.origins")

            for origin in self.origins:
                if origin.name == item.originName:
                    int_val = origin.TryGetValueForItem(item, 0)
                    if int_val.exists:
                        self.Add(item, int_val.result)
                        return
                    raise ValueError(
                        "Could not add the item "
                        + str(item)
                        + " to this list because it doesn't exist in the original list definition in ink."
                    )

            raise ValueError(
                "Failed to add item to list because the item was from a new list definition that wasn't previously known to this list. Only items from previously known lists can be used, so that the int value can be found."
            )
        elif item_or_item_name is not None:
            item_name = item_or_item_name
            found_list_def: Optional[ListDefinition] = None

            if self.origins is None:
                return throw_null_exception("self.origins")

            for origin in self.origins:
                if item_name is None:
                    return throw_null_exception("itemName")
                if origin.ContainsItemWithName(item_name):
                    if found_list_def is not None:
                        raise ValueError(
                            "Could not add the item "
                            + item_name
                            + " to this list because it could come from either "
                            + origin.name
                            + " or "
                            + found_list_def.name
                        )
                    found_list_def = origin

            if found_list_def is None:
                if story_object is None:
                    raise ValueError(
                        "Could not add the item "
                        + item_name
                        + " to this list because it isn't known to any list definitions previously associated with this list."
                    )
                new_item = InkList.FromString(item_name, story_object).orderedItems[0]
                self.Add(new_item.Key, new_item.Value)
            else:
                item = InkListItem(found_list_def.name, item_name)
                item_val = found_list_def.ValueForItem(item)
                self.Add(item, item_val)

    def ContainsItemNamed(self, item_name: Optional[str]):
        for key in self.keys():
            item = InkListItem.fromSerializedKey(key)
            if item.itemName == item_name:
                return True
        return False

    def ContainsKey(self, key: InkListItem):
        return key.serialized() in self

    def Add(self, key: InkListItem, value: int):
        serialized_key = key.serialized()
        if serialized_key in self:
            raise ValueError(f"The Map already contains an entry for {key}")
        self[serialized_key] = value

    def Remove(self, key: InkListItem):
        return self.pop(key.serialized(), None) is not None

    @property
    def Count(self):
        return len(self)

    @property
    def originOfMaxItem(self):
        if self.origins is None:
            return None
        max_origin_name = self.maxItem.Key.originName
        result = None
        for origin in self.origins:
            if origin.name == max_origin_name:
                result = origin
                break
        return result

    @property
    def originNames(self):
        if self.Count > 0:
            if self._originNames is None and self.Count > 0:
                self._originNames = []
            else:
                if self._originNames is None:
                    self._originNames = []
                self._originNames.clear()

            for key in self.keys():
                item = InkListItem.fromSerializedKey(key)
                if item.originName is None:
                    return throw_null_exception("item.originName")
                self._originNames.append(item.originName)
        return self._originNames

    def SetInitialOriginName(self, initial_origin_name: str):
        self._originNames = [initial_origin_name]

    def SetInitialOriginNames(self, initial_origin_names: List[str]):
        if initial_origin_names is None:
            self._originNames = None
        else:
            self._originNames = list(initial_origin_names)

    @property
    def maxItem(self):
        max_item = KeyValuePair(InkListItem.Null(), 0)
        for key, value in self.items():
            item = InkListItem.fromSerializedKey(key)
            if max_item.Key.isNull or value > max_item.Value:
                max_item = KeyValuePair(item, value)
        return max_item

    @property
    def minItem(self):
        min_item = KeyValuePair(InkListItem.Null(), 0)
        for key, value in self.items():
            item = InkListItem.fromSerializedKey(key)
            if min_item.Key.isNull or value < min_item.Value:
                min_item = KeyValuePair(item, value)
        return min_item

    @property
    def inverse(self):
        list_result = InkList()
        if self.origins is not None:
            for origin in self.origins:
                for key, value in origin.items.items():
                    item = InkListItem.fromSerializedKey(key)
                    if not self.ContainsKey(item):
                        list_result.Add(item, value)
        return list_result

    @property
    def all(self):
        list_result = InkList()
        if self.origins is not None:
            for origin in self.origins:
                for key, value in origin.items.items():
                    item = InkListItem.fromSerializedKey(key)
                    list_result[item.serialized()] = value
        return list_result

    def Union(self, other_list: "InkList"):
        union = InkList(self)
        for key, value in other_list.items():
            union[key] = value
        return union

    def Intersect(self, other_list: "InkList"):
        intersection = InkList()
        for key, value in self.items():
            if key in other_list:
                intersection[key] = value
        return intersection

    def HasIntersection(self, other_list: "InkList"):
        for key in self.keys():
            if key in other_list:
                return True
        return False

    def Without(self, list_to_remove: "InkList"):
        result = InkList(self)
        for key in list_to_remove.keys():
            result.pop(key, None)
        return result

    def Contains(self, what):
        if isinstance(what, str):
            return self.ContainsItemNamed(what)
        other_list = what
        if other_list.Count == 0 or self.Count == 0:
            return False
        for key in other_list.keys():
            if key not in self:
                return False
        return True

    def GreaterThan(self, other_list: "InkList"):
        if self.Count == 0:
            return False
        if other_list.Count == 0:
            return True
        return self.minItem.Value > other_list.maxItem.Value

    def GreaterThanOrEquals(self, other_list: "InkList"):
        if self.Count == 0:
            return False
        if other_list.Count == 0:
            return True
        return self.minItem.Value >= other_list.minItem.Value and self.maxItem.Value >= other_list.maxItem.Value

    def LessThan(self, other_list: "InkList"):
        if other_list.Count == 0:
            return False
        if self.Count == 0:
            return True
        return self.maxItem.Value < other_list.minItem.Value

    def LessThanOrEquals(self, other_list: "InkList"):
        if other_list.Count == 0:
            return False
        if self.Count == 0:
            return True
        return self.maxItem.Value <= other_list.maxItem.Value and self.minItem.Value <= other_list.minItem.Value

    def MaxAsList(self):
        if self.Count > 0:
            return InkList({"Key": self.maxItem.Key, "Value": self.maxItem.Value})
        return InkList()

    def MinAsList(self):
        if self.Count > 0:
            return InkList({"Key": self.minItem.Key, "Value": self.minItem.Value})
        return InkList()

    def ListWithSubRange(self, min_bound, max_bound):
        if self.Count == 0:
            return InkList()

        ordered = self.orderedItems
        min_value = 0
        max_value = 9007199254740991

        if isinstance(min_bound, int):
            min_value = min_bound
        elif isinstance(min_bound, InkList) and min_bound.Count > 0:
            min_value = min_bound.minItem.Value

        if isinstance(max_bound, int):
            max_value = max_bound
        elif isinstance(max_bound, InkList) and max_bound.Count > 0:
            max_value = max_bound.maxItem.Value

        sub_list = InkList()
        sub_list.SetInitialOriginNames(self.originNames)
        for item in ordered:
            if min_value <= item.Value <= max_value:
                sub_list.Add(item.Key, item.Value)
        return sub_list

    def Equals(self, other_ink_list: "InkList"):
        if not isinstance(other_ink_list, InkList):
            return False
        if other_ink_list.Count != self.Count:
            return False
        for key in self.keys():
            if key not in other_ink_list:
                return False
        return True

    @property
    def orderedItems(self):
        ordered: List[KeyValuePair] = []
        for key, value in self.items():
            item = InkListItem.fromSerializedKey(key)
            ordered.append(KeyValuePair(item, value))

        def sort_key(kvp: KeyValuePair):
            if kvp.Key.originName is None:
                return ("", kvp.Value)
            return (kvp.Key.originName, kvp.Value)

        ordered.sort(
            key=lambda kvp: (
                kvp.Value,
                kvp.Key.originName if kvp.Key.originName is not None else "",
            )
        )
        return ordered

    @property
    def singleItem(self):
        for item in self.orderedItems:
            return item.Key
        return None

    def __str__(self):
        ordered = self.orderedItems
        sb = StringBuilder()
        for i, item in enumerate(ordered):
            if i > 0:
                sb.Append(", ")
            if item.Key.itemName is None:
                return throw_null_exception("item.itemName")
            sb.Append(item.Key.itemName)
        return str(sb)

    def valueOf(self):
        return float("nan")
