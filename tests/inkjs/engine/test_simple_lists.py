import pytest

from tests.common import from_json_test_context


@pytest.fixture()
def context():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    return context


def test_sequence(context):
    context.story.ChoosePathString("simple_lists.sequence")
    assert context.story.Continue() == "one\n"

    context.story.ChoosePathString("simple_lists.sequence")
    assert context.story.Continue() == "two\n"

    context.story.ChoosePathString("simple_lists.sequence")
    assert context.story.Continue() == "three\n"

    context.story.ChoosePathString("simple_lists.sequence")
    assert context.story.Continue() == "final\n"

    context.story.ChoosePathString("simple_lists.sequence")
    assert context.story.Continue() == "final\n"


def test_cycle(context):
    results = ["one\n", "two\n", "three\n"]
    for i in range(10):
        context.story.ChoosePathString("simple_lists.cycle")
        assert context.story.Continue() == results[i % 3]


def test_once(context):
    context.story.ChoosePathString("simple_lists.once")
    assert context.story.Continue() == "one\n"

    context.story.ChoosePathString("simple_lists.once")
    assert context.story.Continue() == "two\n"

    context.story.ChoosePathString("simple_lists.once")
    assert context.story.Continue() == "three\n"

    context.story.ChoosePathString("simple_lists.once")
    assert context.story.Continue() == ""


def test_shuffle(context):
    results = ["heads\n", "tails\n"]
    for _ in range(40):
        context.story.ChoosePathString("simple_lists.shuffle")
        assert context.story.Continue() in results


def test_blank_elements(context):
    for _ in range(3):
        context.story.ChoosePathString("simple_lists.blanks")
        assert context.story.Continue() == ""

    context.story.ChoosePathString("simple_lists.blanks")
    assert context.story.Continue() == "end\n"
