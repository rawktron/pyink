import pytest

from tests.common import from_json_test_context


@pytest.fixture()
def context():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    return context


def test_global_tags(context):
    tags = context.story.globalTags
    assert len(tags) == 1
    assert tags[0] == "global tag"


def test_knot_level_tags(context):
    tags = context.story.TagsForContentAtPath("tags")
    assert len(tags) == 1
    assert tags[0] == "knot tag"


def test_line_by_line_tags(context):
    context.story.ChoosePathString("tags.line_by_Line")
    context.story.Continue()
    tags = context.story.currentTags
    assert len(tags) == 1
    assert tags[0] == "a tag"

    context.story.Continue()
    tags = context.story.currentTags
    assert len(tags) == 2
    assert tags[0] == "tag1"
    assert tags[1] == "tag2"

    context.story.Continue()
    tags = context.story.currentTags
    assert len(tags) == 2
    assert tags[0] == "tag above"
    assert tags[1] == "tag after"


def test_tags_on_choice_points(context):
    context.story.ChoosePathString("tags.choice")
    context.story.Continue()
    assert len(context.story.currentChoices) == 1
    assert context.story.currentChoices[0].text == "a choice"
    assert len(context.story.currentTags) == 0

    context.story.ChooseChoiceIndex(0)
    assert context.story.Continue() == "a choice\n"
    assert len(context.story.currentTags) == 1
    assert context.story.currentTags[0] == "a tag"


def test_tag_edge_cases(context):
    context.story.ChoosePathString("tags.weird")
    context.story.Continue()
    tags = context.story.currentTags
    assert len(tags) == 2
    assert tags[0] == "space around"
    assert tags[1] == "0"
