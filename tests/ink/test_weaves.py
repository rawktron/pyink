from tests.common import from_json_test_context


def test_conditional_choice_in_weave():
    context = from_json_test_context("conditional_choice_in_weave", "weaves")

    assert context.story.ContinueMaximally() == "start\ngather should be seen\n"
    assert len(context.story.currentChoices) == 1
    assert context.story.currentChoices[0].text == "go to a stitch"

    context.story.ChooseChoiceIndex(0)

    assert context.story.ContinueMaximally() == "result\n"


def test_conditional_choice_in_weave_2():
    context = from_json_test_context("conditional_choice_in_weave_2", "weaves")

    assert context.story.Continue() == "first gather\n"
    assert len(context.story.currentChoices) == 2

    context.story.ChooseChoiceIndex(0)

    assert context.story.ContinueMaximally() == "the main gather\nbottom gather\n"
    assert len(context.story.currentChoices) == 0


def test_unbalanced_weave_indentation():
    context = from_json_test_context("unbalanced_weave_indentation", "weaves")

    context.story.ContinueMaximally()

    assert len(context.story.currentChoices) == 1
    assert context.story.currentChoices[0].text == "First"

    context.story.ChooseChoiceIndex(0)
    assert context.story.ContinueMaximally() == "First\n"
    assert len(context.story.currentChoices) == 1
    assert context.story.currentChoices[0].text == "Very indented"

    context.story.ChooseChoiceIndex(0)
    assert context.story.ContinueMaximally() == "Very indented\nEnd\n"
    assert len(context.story.currentChoices) == 0


def test_weave_gathers():
    context = from_json_test_context("weave_gathers", "weaves")

    context.story.ContinueMaximally()

    assert len(context.story.currentChoices) == 2
    assert context.story.currentChoices[0].text == "one"
    assert context.story.currentChoices[1].text == "four"

    context.story.ChooseChoiceIndex(0)
    context.story.ContinueMaximally()

    assert len(context.story.currentChoices) == 1
    assert context.story.currentChoices[0].text == "two"

    context.story.ChooseChoiceIndex(0)
    assert context.story.ContinueMaximally() == "two\nthree\nsix\n"


def test_weave_options():
    context = from_json_test_context("weave_options", "weaves")

    context.story.ContinueMaximally()
    assert context.story.currentChoices[0].text == "Hello."

    context.story.ChooseChoiceIndex(0)
    assert context.story.Continue() == "Hello, world.\n"


def test_weave_within_sequence():
    context = from_json_test_context("weave_within_sequence", "weaves")

    context.story.Continue()
    assert len(context.story.currentChoices) == 1

    context.story.ChooseChoiceIndex(0)
    assert context.story.ContinueMaximally() == "choice\nnextline\n"
