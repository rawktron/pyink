from tests.common import from_json_test_context


def test_tags():
    context = from_json_test_context("tags", "tags")
    global_tags = ["author: Joe", "title: My Great Story"]
    knot_tags = ["knot tag"]
    knot_tags_when_continued_twice = ["end of knot tag"]
    stitch_tags = ["stitch tag"]

    assert context.story.globalTags == global_tags
    assert context.story.Continue() == "This is the content\n"
    assert context.story.currentTags == global_tags

    assert context.story.TagsForContentAtPath("knot") == knot_tags
    assert context.story.TagsForContentAtPath("knot.stitch") == stitch_tags

    context.story.ChoosePathString("knot")
    assert context.story.Continue() == "Knot content\n"
    assert context.story.currentTags == knot_tags
    assert context.story.Continue() == ""
    assert context.story.currentTags == knot_tags_when_continued_twice


def test_tags_in_sequence():
    context = from_json_test_context("tags_in_seq", "tags")
    assert context.story.Continue() == "A red sequence.\n"
    assert context.story.currentTags == ["red"]
    assert context.story.Continue() == "A white sequence.\n"
    assert context.story.currentTags == ["white"]


def test_tags_dynamic_content():
    context = from_json_test_context("tags_dynamic_content", "tags")
    assert context.story.Continue() == "tag\n"
    assert context.story.currentTags == ["pic8red.jpg"]
