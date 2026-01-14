from tests.common import from_json_test_context


def test_empty_list_origin():
    context = from_json_test_context("empty_list_origin", "lists")
    assert context.story.Continue() == "a, b\n"


def test_empty_list_origin_after_assignment():
    context = from_json_test_context("empty_list_origin_after_assignment", "lists")
    assert context.story.ContinueMaximally() == "a, b, c\n"


def test_list_basic_operations():
    context = from_json_test_context("list_basic_operations", "lists")
    assert context.story.ContinueMaximally() == "b, d\na, b, c, e\nb, c\nfalse\ntrue\ntrue\n"


def test_list_mixed_items():
    context = from_json_test_context("list_mixed_items", "lists")
    assert context.story.ContinueMaximally() == "a, y, c\n"


def test_list_random():
    context = from_json_test_context("list_random", "lists")
    while context.story.canContinue:
        result = context.story.Continue()
        assert result in ("B\n", "C\n", "D\n")


def test_list_range():
    context = from_json_test_context("list_range", "lists")
    assert (
        context.story.ContinueMaximally()
        == "Pound, Pizza, Euro, Pasta, Dollar, Curry, Paella\n"
        "Euro, Pasta, Dollar, Curry\n"
        "Two, Three, Four, Five, Six\n"
        "Two, Three, Four\n"
        "Two, Three, Four, Five\n"
        "Pizza, Pasta\n"
    )


def test_list_save_load():
    context = from_json_test_context("list_save_load", "lists")
    assert context.story.ContinueMaximally() == "a, x, c\n"
    saved_state = context.story.state.ToJson()

    context = from_json_test_context("list_save_load", "lists")
    context.story.state.LoadJson(saved_state)
    context.story.ChoosePathString("elsewhere")
    assert context.story.ContinueMaximally() == "a, x, c, z\n"


def test_more_list_operations():
    context = from_json_test_context("more_list_operations", "lists")
    assert context.story.ContinueMaximally() == "1\nl\nn\nl, m\nn\n"


def test_contains_empty_list_always_false():
    context = from_json_test_context("contains_empty_list_always_false", "lists")
    assert context.story.ContinueMaximally() == "false\nfalse\nfalse\n"
