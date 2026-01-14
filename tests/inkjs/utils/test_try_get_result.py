from pyink.engine.try_get_result import try_get_value_from_map, try_parse_float, try_parse_int


def test_try_get_value_from_map_found():
    data = {"a": 1}
    result = try_get_value_from_map(data, "a", None)
    assert result.exists is True
    assert result.result == 1


def test_try_get_value_from_map_missing():
    data = {"a": 1}
    result = try_get_value_from_map(data, "b", 3)
    assert result.exists is False
    assert result.result == 3


def test_try_parse_int_success():
    result = try_parse_int("3")
    assert result.exists is True
    assert result.result == 3


def test_try_parse_int_fail():
    result = try_parse_int("nope", 7)
    assert result.exists is False
    assert result.result == 7


def test_try_parse_float_success():
    result = try_parse_float("3.5")
    assert result.exists is True
    assert result.result == 3.5


def test_try_parse_float_fail():
    result = try_parse_float("nope", 7.5)
    assert result.exists is False
    assert result.result == 7.5
