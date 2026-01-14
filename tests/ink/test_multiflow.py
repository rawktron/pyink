from tests.common import from_json_test_context


def test_multi_flow_basics():
    context = from_json_test_context("multi_flow_basics", "multiflow")

    context.story.SwitchFlow("First")
    context.story.ChoosePathString("knot1")
    assert context.story.Continue() == "knot 1 line 1\n"

    context.story.SwitchFlow("Second")
    context.story.ChoosePathString("knot2")
    assert context.story.Continue() == "knot 2 line 1\n"

    context.story.SwitchFlow("First")
    assert context.story.Continue() == "knot 1 line 2\n"

    context.story.SwitchFlow("Second")
    assert context.story.Continue() == "knot 2 line 2\n"


def test_multi_flow_save_load_threads():
    context = from_json_test_context("multi_flow_save_load_threads", "multiflow")

    assert context.story.Continue() == "Default line 1\n"

    context.story.SwitchFlow("Blue Flow")
    context.story.ChoosePathString("blue")
    assert context.story.Continue() == "Hello I'm blue\n"

    context.story.SwitchFlow("Red Flow")
    context.story.ChoosePathString("red")
    assert context.story.Continue() == "Hello I'm red\n"

    context.story.SwitchFlow("Blue Flow")
    assert context.story.currentText == "Hello I'm blue\n"
    assert context.story.currentChoices[0].text == "Thread 1 blue choice"

    context.story.SwitchFlow("Red Flow")
    assert context.story.currentText == "Hello I'm red\n"
    assert context.story.currentChoices[0].text == "Thread 1 red choice"

    saved = context.story.state.ToJson()

    context.story.ChooseChoiceIndex(0)
    assert (
        context.story.ContinueMaximally()
        == "Thread 1 red choice\nAfter thread 1 choice (red)\n"
    )
    context.story.ResetState()

    context.story.state.LoadJson(saved)

    context.story.ChooseChoiceIndex(1)
    assert (
        context.story.ContinueMaximally()
        == "Thread 2 red choice\nAfter thread 2 choice (red)\n"
    )

    context.story.state.LoadJson(saved)
    context.story.SwitchFlow("Blue Flow")
    context.story.ChooseChoiceIndex(0)
    assert (
        context.story.ContinueMaximally()
        == "Thread 1 blue choice\nAfter thread 1 choice (blue)\n"
    )

    context.story.state.LoadJson(saved)
    context.story.SwitchFlow("Blue Flow")
    context.story.ChooseChoiceIndex(1)
    assert (
        context.story.ContinueMaximally()
        == "Thread 2 blue choice\nAfter thread 2 choice (blue)\n"
    )

    context.story.RemoveFlow("Blue Flow")
    assert context.story.Continue() == "Default line 2\n"
