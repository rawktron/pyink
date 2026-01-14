from tests.common import from_json_test_context


def test_multi_thread():
    context = from_json_test_context("multi_thread", "threads")

    assert (
        context.story.ContinueMaximally()
        == "This is place 1.\nThis is place 2.\n"
    )

    context.story.ChooseChoiceIndex(0)
    assert context.story.ContinueMaximally() == "choice in place 1\nThe end\n"


def test_thread_done():
    context = from_json_test_context("thread_done", "threads")

    assert (
        context.story.ContinueMaximally()
        == "This is a thread example\nHello.\nThe example is now complete.\n"
    )


def test_thread_in_logic():
    context = from_json_test_context("thread_in_logic", "threads")

    assert context.story.Continue() == "Content\n"


def test_top_flow_terminator_should_not_kill_thread_choices():
    context = from_json_test_context(
        "top_flow_terminator_should_not_kill_thread_choices",
        "threads",
    )

    assert context.story.Continue() == "Limes\n"
    assert len(context.story.currentChoices) == 1
