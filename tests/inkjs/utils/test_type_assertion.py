import pytest

from pyink.engine.type_assertion import (
    as_boolean_or_throws,
    as_number_or_throws,
    as_or_null,
    as_or_throws,
)


class Foo:
    pass


class Bar:
    pass


def test_as_or_null():
    foo = Foo()
    assert as_or_null(foo, Foo) is foo
    assert as_or_null(foo, Bar) is None


def test_as_or_throws():
    foo = Foo()
    assert as_or_throws(foo, Foo) is foo
    with pytest.raises(TypeError):
        as_or_throws(foo, Bar)


def test_as_number_or_throws():
    assert as_number_or_throws(3) == 3
    assert as_number_or_throws(3.5) == 3.5
    with pytest.raises(TypeError):
        as_number_or_throws("nope")


def test_as_boolean_or_throws():
    assert as_boolean_or_throws(True) is True
    assert as_boolean_or_throws(False) is False
    with pytest.raises(TypeError):
        as_boolean_or_throws(0)
