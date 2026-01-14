from tests.common import from_json_test_context


def test_call_stack_evaluation():
    context = from_json_test_context("callstack_evaluation", "callstack")
    assert context.story.Continue() == "8\n"


def test_clean_callstack_reset_on_path_choice():
    context = from_json_test_context("clean_callstack_reset_on_path_choice", "callstack")

    assert context.story.Continue() == "The first line.\n"

    context.story.ChoosePathString("SomewhereElse")

    assert context.story.ContinueMaximally() == "somewhere else\n"
