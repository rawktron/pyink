from tests.common import from_json_test_context


def test_blanks_in_inline_sequences():
    context = from_json_test_context("blanks_in_inline_sequences", "sequences")
    assert (
        context.story.ContinueMaximally()
        == "1. a\n2.\n3. b\n4. b\n---\n1.\n2. a\n3. a\n---\n1. a\n2.\n3.\n---\n1.\n2.\n3.\n"
    )


def test_empty_sequence_content():
    context = from_json_test_context("empty_sequence_content", "sequences")
    assert context.story.ContinueMaximally() == "Wait for it....\nSurprise!\nDone.\n"


def test_gather_read_count_with_initial_sequence():
    context = from_json_test_context("gather_read_count_with_initial_sequence", "sequences")
    assert context.story.Continue() == "seen test\n"


def test_leading_newline_multiline_sequence():
    context = from_json_test_context("leading_newline_multiline_sequence", "sequences")
    assert context.story.Continue() == "a line after an empty line\n"


def test_shuffle_stack_muddying():
    context = from_json_test_context("shuffle_stack_muddying", "sequences")

    context.story.Continue()
    assert len(context.story.currentChoices) == 2


def test_all_sequence_types():
    context = from_json_test_context("all_sequence_types", "sequences")

    assert (
        context.story.ContinueMaximally()
        == "Once: one two\nStopping: one two two two\nDefault: one two two two\nCycle: one two one two\nShuffle: two one one two\nShuffle stopping: one two final final\nShuffle once: two one\n"
    )
