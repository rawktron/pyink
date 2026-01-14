import pytest

from tests.common import from_json_test_context


def test_const():
    context = from_json_test_context("const", "variables")
    assert context.story.Continue() == "5\n"


def test_multiple_constant_references():
    context = from_json_test_context("multiple_constant_references", "variables")
    assert context.story.Continue() == "success\n"


def test_set_non_existent_variable():
    context = from_json_test_context("set_non_existent_variable", "variables")
    assert context.story.Continue() == "Hello world.\n"
    with pytest.raises(Exception):
        context.story.variablesState["y"] = "earth"


def test_temp_global_conflict():
    context = from_json_test_context("temp_global_conflict", "variables")
    assert context.story.Continue() == "0\n"


def test_temp_not_found():
    context = from_json_test_context("temp_not_found", "variables")
    with pytest.raises(Exception):
        assert context.story.ContinueMaximally() == "0\nhello\n"
    assert context.story.hasWarning is True


def test_temp_usage_in_options():
    context = from_json_test_context("temp_usage_in_options", "variables")
    context.story.Continue()
    assert len(context.story.currentChoices) == 1
    assert context.story.currentChoices[0].text == "1"
    context.story.ChooseChoiceIndex(0)
    assert context.story.ContinueMaximally() == "1\nEnd of choice\nthis another\n"
    assert len(context.story.currentChoices) == 0


def test_temporaries_at_global_scope():
    context = from_json_test_context("temporaries_at_global_scope", "variables")
    assert context.story.Continue() == "54\n"


def test_variable_declaration_in_conditional():
    context = from_json_test_context("variable_declaration_in_conditional", "variables")
    assert context.story.Continue() == "5\n"


def test_variable_divert_target():
    context = from_json_test_context("variable_divert_target", "variables")
    assert context.story.Continue() == "Here.\n"


def test_variable_get_set_api():
    context = from_json_test_context("variable_get_set_api", "variables")
    assert context.story.ContinueMaximally() == "5\n"
    assert context.story.variablesState["x"] == 5

    context.story.variablesState["x"] = 10
    context.story.ChooseChoiceIndex(0)
    assert context.story.ContinueMaximally() == "10\n"
    assert context.story.variablesState["x"] == 10

    context.story.variablesState["x"] = 8.5
    context.story.ChooseChoiceIndex(0)
    assert context.story.ContinueMaximally() == "8.5\n"
    assert context.story.variablesState["x"] == 8.5

    context.story.variablesState["x"] = "a string"
    context.story.ChooseChoiceIndex(0)
    assert context.story.ContinueMaximally() == "a string\n"
    assert context.story.variablesState["x"] == "a string"

    assert context.story.variablesState["z"] is None

    with pytest.raises(Exception):
        context.story.variablesState["x"] = {"nope": "nope"}


def test_variable_pointer_ref_from_knot():
    context = from_json_test_context("variable_pointer_ref_from_knot", "variables")
    assert context.story.Continue() == "6\n"


def test_variable_swap_recurse():
    context = from_json_test_context("variable_swap_recurse", "variables")
    assert context.story.ContinueMaximally() == "1 2\n"


def test_variable_tunnel():
    context = from_json_test_context("variable_tunnel", "variables")
    assert context.story.ContinueMaximally() == "STUFF\n"
