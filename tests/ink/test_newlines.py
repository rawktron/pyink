from tests.common import from_json_test_context


def test_newline_at_start_of_multiline_conditional():
    context = from_json_test_context("newline_at_start_of_multiline_conditional", "newlines")

    assert context.story.ContinueMaximally() == "X\nx\n"


def test_newline_consistency():
    context = from_json_test_context("newline_consistency_1", "newlines")
    assert context.story.ContinueMaximally() == "hello world\n"

    context = from_json_test_context("newline_consistency_2", "newlines")
    context.story.Continue()
    context.story.ChooseChoiceIndex(0)
    assert context.story.ContinueMaximally() == "hello world\n"

    context = from_json_test_context("newline_consistency_3", "newlines")
    context.story.Continue()
    context.story.ChooseChoiceIndex(0)
    assert context.story.ContinueMaximally() == "hello\nworld\n"


def test_newlines_trimming_with_func_external_fallback():
    context = from_json_test_context("newlines_trimming_with_func_external_fallback", "newlines")
    context.story.allowExternalFunctionFallbacks = True

    assert context.story.ContinueMaximally() == "Phrase 1\nPhrase 2\n"


def test_newlines_with_string_eval():
    context = from_json_test_context("newlines_with_string_eval", "newlines")

    assert context.story.ContinueMaximally() == "A\nB\nA\n3\nB\n"
