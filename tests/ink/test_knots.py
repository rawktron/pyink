from tests.common import from_json_test_context


def test_knot_do_not_gather():
    context = from_json_test_context("knot_do_not_gather", "knots")
    assert context.story.Continue() == "g\n"


def test_knot_stitch_gather_counts():
    context = from_json_test_context("knot_stitch_gather_counts", "knots")
    assert (
        context.story.ContinueMaximally()
        == "1 1\n2 2\n3 3\n1 1\n2 1\n3 1\n1 2\n2 2\n3 2\n1 1\n2 1\n3 1\n1 2\n2 2\n3 2\n"
    )


def test_knot_thread_interaction():
    context = from_json_test_context("knot_thread_interaction", "knots")
    assert context.story.ContinueMaximally() == "blah blah\n"
    assert len(context.story.currentChoices) == 2
    assert "option" in context.story.currentChoices[0].text
    assert "wigwag" in context.story.currentChoices[1].text
    context.story.ChooseChoiceIndex(1)
    assert context.story.Continue() == "wigwag\n"
    assert context.story.Continue() == "THE END\n"


def test_knot_thread_interaction_2():
    context = from_json_test_context("knot_thread_interaction_2", "knots")
    assert context.story.ContinueMaximally() == "I’m in a tunnel\nWhen should this get printed?\n"
    assert len(context.story.currentChoices) == 1
    assert context.story.currentChoices[0].text == "I’m an option"
    context.story.ChooseChoiceIndex(0)
    assert context.story.ContinueMaximally() == "I’m an option\nFinishing thread.\n"
