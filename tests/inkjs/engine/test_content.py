import pytest

from tests.common import from_json_test_context


@pytest.fixture()
def context():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    return context


def test_read_simple_content(context):
    context.story.ChoosePathString("content.simple")
    assert context.story.Continue() == "Simple content inside a knot\n"


def test_read_multiline_content(context):
    context.story.ChoosePathString("content.multiline")
    assert context.story.Continue() == "First line\n"
    assert context.story.canContinue is True
    assert context.story.Continue() == "Second line\n"


def test_print_variable(context):
    context.story.ChoosePathString("content.variable_text")
    assert context.story.Continue() == "variable text\n"


def test_print_truthy_conditional_text(context):
    context.story.ChoosePathString("content.if_text_truthy")
    assert context.story.Continue() == "I… I saw him. Only for a moment.\n"


def test_print_falsy_conditional_text(context):
    context.story.ChoosePathString("content.if_text_falsy")
    assert context.story.Continue() == "I…\n"


def test_if_else_text(context):
    context.story.ChoosePathString("content.if_else_text")
    assert context.story.Continue() == "I saw him. Only for a moment.\n"
    assert context.story.Continue() == "I missed him. Was he particularly evil?\n"


def test_glue_lines_together(context):
    context.story.ChoosePathString("glue.simple")
    assert context.story.Continue() == "Simple glue\n"


def test_glue_diverts(context):
    context.story.ChoosePathString("glue.diverted_glue")
    assert context.story.Continue() == "More glue\n"


def test_divert_to_knot(context):
    context.story.ChoosePathString("divert.divert_knot")
    assert context.story.Continue() == "Diverted to a knot\n"


def test_divert_to_stitch(context):
    context.story.ChoosePathString("divert.divert_stitch")
    assert context.story.Continue() == "Diverted to a stitch\n"


def test_divert_to_internal_stitch(context):
    context.story.ChoosePathString("divert.internal_stitch")
    assert context.story.Continue() == "Diverted to internal stitch\n"


def test_divert_with_variable(context):
    context.story.ChoosePathString("divert.divert_var")
    assert context.story.Continue() == "Diverted with a variable\n"


def test_choice_count_query(context):
    context.story.ChoosePathString("game_queries.choicecount")
    context.story.Continue()

    assert len(context.story.currentChoices) == 1
    assert context.story.currentChoices[0].text == "count 0"

    context.story.ChooseChoiceIndex(0)
    context.story.Continue()

    assert len(context.story.currentChoices) == 2
    assert context.story.currentChoices[1].text == "count 1"

    context.story.ChooseChoiceIndex(0)
    context.story.Continue()

    assert len(context.story.currentChoices) == 3
    assert context.story.currentChoices[2].text == "count 2"

    context.story.ChooseChoiceIndex(0)
    context.story.Continue()

    assert len(context.story.currentChoices) == 4
    assert context.story.currentChoices[1].text == "count 1"
    assert context.story.currentChoices[3].text == "count 3"


def test_turns_since_query(context):
    context.story.ChoosePathString("game_queries.turnssince_before")
    assert context.story.Continue() == "-1\n"
    assert context.story.Continue() == "0\n"

    assert len(context.story.currentChoices) == 1
    context.story.ChooseChoiceIndex(0)
    assert context.story.Continue() == "1\n"

    assert len(context.story.currentChoices) == 1
    context.story.ChooseChoiceIndex(0)
    assert context.story.Continue() == "2\n"
