from tests.common import from_json_test_context


def test_bools():
    context = from_json_test_context("true", "booleans")
    assert context.story.Continue() == "true\n"

    context = from_json_test_context("true_plus_one", "booleans")
    assert context.story.Continue() == "2\n"

    context = from_json_test_context("two_plus_true", "booleans")
    assert context.story.Continue() == "3\n"

    context = from_json_test_context("false_plus_false", "booleans")
    assert context.story.Continue() == "0\n"

    context = from_json_test_context("true_plus_true", "booleans")
    assert context.story.Continue() == "2\n"

    context = from_json_test_context("true_equals_one", "booleans")
    assert context.story.Continue() == "true\n"

    context = from_json_test_context("not_one", "booleans")
    assert context.story.Continue() == "false\n"

    context = from_json_test_context("not_true", "booleans")
    assert context.story.Continue() == "false\n"

    context = from_json_test_context("three_greater_than_one", "booleans")
    assert context.story.Continue() == "true\n"

    context = from_json_test_context("list_hasnt", "booleans")
    assert context.story.Continue() == "true\n"
