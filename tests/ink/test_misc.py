from tests.common import from_json_test_context


def test_empty():
    context = from_json_test_context("empty", "misc")

    assert context.story.ContinueMaximally() == ""


def test_end():
    context = from_json_test_context("end", "misc")

    assert context.story.ContinueMaximally() == "hello\n"


def test_end2():
    context = from_json_test_context("end2", "misc")

    assert context.story.ContinueMaximally() == "hello\n"


def test_escape_character():
    context = from_json_test_context("escape_character", "misc")

    assert context.story.ContinueMaximally() == "this is a '|' character\n"


def test_hello_world():
    context = from_json_test_context("hello_world", "misc")

    assert context.story.Continue() == "Hello world\n"


def test_identifiers_can_start_with_number():
    context = from_json_test_context("identifiers_can_start_with_number", "misc")

    assert context.story.ContinueMaximally() == "512x2 = 1024\n512x2p2 = 1026\n"


def test_include():
    context = from_json_test_context("include", "misc")

    assert (
        context.story.ContinueMaximally()
        == "This is include 1.\nThis is include 2.\nThis is the main file.\n"
    )


def test_nested_include():
    context = from_json_test_context("nested_include", "misc")

    assert (
        context.story.ContinueMaximally()
        == "The value of a variable in test file 2 is 5.\nThis is the main file\nThe value when accessed from knot_in_2 is 5.\n"
    )


def test_quote_character_significance():
    context = from_json_test_context("quote_character_significance", "misc")

    assert context.story.ContinueMaximally() == 'My name is "Joe"\n'


def test_whitespace():
    context = from_json_test_context("whitespace", "misc")

    assert context.story.ContinueMaximally() == "Hello!\nWorld.\n"
