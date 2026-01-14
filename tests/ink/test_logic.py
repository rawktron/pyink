from tests.common import from_json_test_context


def test_logic_lines_with_newlines():
    context = from_json_test_context("logic_lines_with_newlines", "logic")

    assert context.story.ContinueMaximally() == "text1\ntext 2\ntext1\ntext 2\n"


def test_multiline_logic_with_glue():
    context = from_json_test_context("multiline_logic_with_glue", "logic")

    assert context.story.ContinueMaximally() == "a b\na b\n"


def test_nested_pass_by_reference():
    context = from_json_test_context("nested_pass_by_reference", "logic")

    assert context.story.ContinueMaximally() == "5\n625\n"


def test_print_num():
    context = from_json_test_context("print_num", "logic")

    assert (
        context.story.ContinueMaximally()
        == ". four .\n. fifteen .\n. thirty-seven .\n. one hundred and one .\n. two hundred and twenty-two .\n. one thousand two hundred and thirty-four .\n"
    )
