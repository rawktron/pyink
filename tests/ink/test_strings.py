from tests.common import from_json_test_context


def test_string_constants():
    context = from_json_test_context("string_constants", "strings")
    assert context.story.Continue() == "hi\n"


def test_string_contains():
    context = from_json_test_context("string_contains", "strings")
    assert context.story.ContinueMaximally() == "true\nfalse\ntrue\ntrue\n"


def test_string_type_coercion():
    context = from_json_test_context("string_type_coercion", "strings")
    assert context.story.ContinueMaximally() == "same\ndifferent\n"


def test_strings_in_choices():
    context = from_json_test_context("strings_in_choices", "strings")
    context.story.ContinueMaximally()
    assert len(context.story.currentChoices) == 1
    assert context.story.currentChoices[0].text == 'test1 "test2 test3"'
    context.story.ChooseChoiceIndex(0)
    assert context.story.Continue() == "test1 test4\n"
