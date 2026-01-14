import math
import pytest

from pyink.engine.simple_json import SimpleJson


def test_writer_inner_hierarchy():
    writer = SimpleJson.Writer()
    writer.WriteObjectStart()
    writer.WriteProperty("callstackThreads", lambda w: _write_callstack_threads(w))
    writer.WriteIntProperty("inkSaveVersion", 8)
    writer.WriteObjectEnd()

    assert (
        writer.toString()
        == '{"callstackThreads":{"callstack":[{"cPath":"path.to.component","idx":2,"exp":"expression","type":3},null],"threadIndex":0,"previousContentObject":"path.to.object"},"inkSaveVersion":8}'
    )


def _write_callstack_threads(writer):
    writer.WriteObjectStart()
    writer.WritePropertyStart("callstack")
    writer.WriteArrayStart()
    writer.WriteObjectStart()
    writer.WriteProperty("cPath", "path.to.component")
    writer.WriteIntProperty("idx", 2)
    writer.WriteProperty("exp", "expression")
    writer.WriteIntProperty("type", 3)
    writer.WriteObjectEnd()
    writer.WriteNull()
    writer.WriteArrayEnd()
    writer.WritePropertyEnd()
    writer.WriteIntProperty("threadIndex", 0)
    writer.WriteProperty("previousContentObject", "path.to.object")
    writer.WriteObjectEnd()


def test_writer_inner_string():
    writer = SimpleJson.Writer()
    writer.WriteObjectStart()

    writer.WritePropertyNameStart()
    writer.WritePropertyNameInner("prop")
    writer.WritePropertyNameInner("erty")
    writer.WritePropertyNameEnd()

    writer.WriteStringStart()
    writer.WriteStringInner("^")
    writer.WriteStringInner("Hello World.")
    writer.WriteStringEnd()
    writer.WritePropertyEnd()

    writer.WritePropertyStart("key")
    writer.WriteArrayStart()
    writer.WriteStringStart()
    writer.WriteStringInner("^")
    writer.WriteStringInner("Hello World.")
    writer.WriteStringEnd()
    writer.WriteArrayEnd()
    writer.WritePropertyEnd()

    writer.WriteObjectEnd()
    assert writer.toString() == '{"property":"^Hello World.","key":["^Hello World."]}'


def test_writer_nested_arrays():
    writer = SimpleJson.Writer()
    writer.WriteArrayStart()
    writer.WriteArrayStart()
    writer.WriteArrayStart()
    writer.WriteArrayStart()
    writer.WriteNull()
    writer.WriteArrayEnd()
    writer.WriteArrayEnd()
    writer.WriteArrayEnd()
    writer.WriteArrayEnd()
    assert writer.toString() == "[[[[null]]]]"


def test_writer_unbalanced_calls():
    writer = SimpleJson.Writer()
    with pytest.raises(AssertionError):
        writer.WriteObjectStart()
        writer.WritePropertyEnd()

    writer = SimpleJson.Writer()
    with pytest.raises(AssertionError):
        writer.WriteStringStart()
        writer.WriteArrayStart()
        writer.WriteStringEnd()


def test_writer_integers_object_hierarchy():
    writer = SimpleJson.Writer()
    writer.WriteObjectStart()
    writer.WriteIntProperty("property", 3)
    writer.WriteObjectEnd()
    assert writer.toString() == '{"property":3}'


def test_writer_integers_array_hierarchy():
    writer = SimpleJson.Writer()
    writer.WriteArrayStart()
    writer.WriteInt(3)
    writer.WriteArrayEnd()
    assert writer.toString() == "[3]"


def test_writer_integers_convert_floats():
    writer = SimpleJson.Writer()
    writer.WriteArrayStart()
    writer.WriteObjectStart()
    writer.WriteIntProperty("property", 3.9)
    writer.WriteObjectEnd()
    writer.WriteArrayStart()
    writer.WriteInt(3.1)
    writer.WriteInt(4.0)
    writer.WriteArrayEnd()
    writer.WriteArrayEnd()
    assert writer.toString() == '[{"property":3},[3,4]]'


def test_writer_floats_object_hierarchy():
    writer = SimpleJson.Writer()
    writer.WriteObjectStart()
    writer.WriteFloatProperty("property", 3.4)
    writer.WriteObjectEnd()
    assert writer.toString() == '{"property":3.4}'


def test_writer_floats_array_hierarchy():
    writer = SimpleJson.Writer()
    writer.WriteArrayStart()
    writer.WriteFloat(36.1456)
    writer.WriteArrayEnd()
    assert writer.toString() == "[36.1456]"


def test_writer_floats_integer_values():
    writer = SimpleJson.Writer()
    writer.WriteArrayStart()
    writer.WriteFloat(3)
    writer.WriteFloat(4)
    writer.WriteArrayEnd()
    assert writer.toString() == "[3,4]"


def test_writer_floats_convert_infinity_nan():
    writer = SimpleJson.Writer()
    writer.WriteArrayStart()
    writer.WriteFloat(float("inf"))
    writer.WriteFloat(float("-inf"))
    writer.WriteFloat(float("nan"))
    writer.WriteArrayEnd()
    assert writer.toString() == "[3.4e+38,-3.4e+38,0]"


def test_reader_parses_object():
    json_string = '{"key":"value", "array": [1, 2, null, 3.0, false]}'
    obj = {"array": [1, 2, None, "3.0f", False], "key": "value"}
    reader = SimpleJson.Reader(json_string)
    assert reader.ToDictionary() == obj
    assert SimpleJson.TextToDictionary(json_string) == obj


def test_reader_parses_array():
    json_string = "[1, 2, null, 3.0, false]"
    obj = [1, 2, None, "3.0f", False]
    reader = SimpleJson.Reader(json_string)
    assert reader.ToArray() == obj
    assert SimpleJson.TextToArray(json_string) == obj


def test_reader_throws_on_malformed():
    json_string = '{key: "value"]'
    with pytest.raises(Exception):
        reader = SimpleJson.Reader(json_string)
        reader.ToDictionary()
    with pytest.raises(Exception):
        SimpleJson.TextToDictionary(json_string)
