import pytest

from tests.common import from_json_test_context


@pytest.fixture()
def context():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    return context


def test_lists_defined(context):
    context.story.ChoosePathString("lists.basic_list")
    assert context.story.Continue() == "cold\n"
    assert context.story.Continue() == "boiling\n"


def test_lists_increment_decrement(context):
    context.story.ChoosePathString("lists.increment")
    assert context.story.Continue() == "cold\n"
    assert context.story.Continue() == "boiling\n"
    assert context.story.Continue() == "evaporated\n"
    assert context.story.Continue() == "boiling\n"
    assert context.story.Continue() == "cold\n"


def test_lists_print_values(context):
    context.story.ChoosePathString("lists.list_value")
    assert context.story.Continue() == "1\n"
    assert context.story.Continue() == "2\n"
    assert context.story.Continue() == "3\n"


def test_lists_set_names_from_values(context):
    context.story.ChoosePathString("lists.value_from_number")
    assert context.story.Continue() == "cold\n"
    assert context.story.Continue() == "boiling\n"
    assert context.story.Continue() == "evaporated\n"


def test_lists_user_defined_values(context):
    context.story.ChoosePathString("lists.defined_value")
    assert context.story.Continue() == "2\n"
    assert context.story.Continue() == "3\n"
    assert context.story.Continue() == "0\n"


def test_lists_add_remove_values(context):
    context.story.ChoosePathString("lists.multivalue")
    assert context.story.Continue() == "\n"
    assert context.story.Continue() == "Denver, Eamonn\n"
    assert context.story.Continue() == "Denver\n"
    assert context.story.Continue() == "\n"
    assert context.story.Continue() == "\n"
    assert context.story.Continue() == "Eamonn\n"


def test_lists_queries(context):
    context.story.ChoosePathString("lists.listqueries")
    assert context.story.Continue() == "list is empty\n"
    assert context.story.Continue() == "2\n"
    assert context.story.Continue() == "Denver\n"
    assert context.story.Continue() == "Eamonn\n"
    assert context.story.Continue() == "list is not empty\n"

    assert context.story.Continue() == "exact equality\n"
    assert context.story.Continue() == "falsy exact equality\n"
    assert context.story.Continue() == "exact inequality\n"
    assert context.story.Continue() == "exact inequality works\n"

    assert context.story.Continue() == "has Eamonn\n"
    assert context.story.Continue() == "has falsy works\n"
    assert context.story.Continue() == "has not\n"
    assert context.story.Continue() == "falsy has not\n"
    assert context.story.Continue() == "Adams, Bernard, Cartwright, Denver, Eamonn\n"
    assert context.story.Continue() == "\n"
    assert context.story.Continue() == "\n"

    assert context.story.Continue() == "truthy greater than\n"
    assert context.story.Continue() == "falsy greater than\n"
    assert context.story.Continue() == "greater than empty\n"
    assert context.story.Continue() == "empty greater than\n"

    assert context.story.Continue() == "truthy smaller than\n"
    assert context.story.Continue() == "falsy smaller than\n"
    assert context.story.Continue() == "smaller than empty\n"
    assert context.story.Continue() == "empty smaller than\n"

    assert context.story.Continue() == "truthy greater than or equal\n"
    assert context.story.Continue() == "truthy greater than or equal\n"
    assert context.story.Continue() == "falsy greater than or equal\n"
    assert context.story.Continue() == "greater than or equals empty\n"
    assert context.story.Continue() == "empty greater than or equals\n"

    assert context.story.Continue() == "truthy smaller than or equal\n"
    assert context.story.Continue() == "truthy smaller than or equal\n"
    assert context.story.Continue() == "falsy smaller than or equal\n"
    assert context.story.Continue() == "smaller than or equals empty\n"
    assert context.story.Continue() == "empty smaller than or equals\n"

    assert context.story.Continue() == "truthy list AND\n"
    assert context.story.Continue() == "falsy list AND\n"
    assert context.story.Continue() == "truthy list OR\n"
    assert context.story.Continue() == "falsy list OR\n"
    assert context.story.Continue() == "truthy list not\n"
    assert context.story.Continue() == "falsy list not\n"

    assert context.story.Continue() == "Bernard, Cartwright, Denver\n"
    assert context.story.Continue() == "Smith, Jones\n"

    assert context.story.Continue() == "Carter, Braithwaite\n"
    assert context.story.Continue() == "self_belief\n"
