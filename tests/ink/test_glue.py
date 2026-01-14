from tests.common import from_json_test_context


def test_implicit_inline_glue():
    context = from_json_test_context("implicit_inline_glue", "glue")
    assert context.story.Continue() == "I have five eggs.\n"


def test_implicit_inline_glue_b():
    context = from_json_test_context("implicit_inline_glue_b", "glue")
    assert context.story.ContinueMaximally() == "A\nX\n"


def test_implicit_inline_glue_c():
    context = from_json_test_context("implicit_inline_glue_c", "glue")
    assert context.story.ContinueMaximally() == "A\nC\n"


def test_left_right_glue_matching():
    context = from_json_test_context("left_right_glue_matching", "glue")
    assert context.story.ContinueMaximally() == "A line.\nAnother line.\n"


def test_simple_glue():
    context = from_json_test_context("simple_glue", "glue")
    assert context.story.Continue() == "Some content with glue.\n"
