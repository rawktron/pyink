import pytest

from tests.common import from_json_test_context


@pytest.fixture()
def context():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    return context


def test_tunnel_call(context):
    context.story.ChoosePathString("flow_control.tunnel_call")
    assert context.story.Continue() == "tunnel end\n"
    assert context.story.canContinue is False


def test_threads(context):
    context.story.ChoosePathString("flow_control.thread")
    assert context.story.Continue() == "thread start\n"
    assert context.story.Continue() == "threaded text\n"
    assert context.story.Continue() == "thread end\n"
    assert context.story.canContinue is False
    assert len(context.story.currentChoices) == 2
    assert context.story.currentChoices[0].text == "first threaded choice"
    assert context.story.currentChoices[1].text == "second threaded choice"

    context.story.ChooseChoiceIndex(0)
    assert context.story.Continue() == "first threaded choice\n"
    assert context.story.canContinue is False
