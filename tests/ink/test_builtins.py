from tests.common import from_json_test_context


def test_floor_ceiling_and_casts():
    context = from_json_test_context("floor_ceiling_and_casts", "builtins")
    assert context.story.ContinueMaximally() == "1\n1\n2\n0.6666666666666666\n0\n1\n"


def test_read_count_across_callstack():
    context = from_json_test_context("read_count_across_callstack", "builtins")
    assert (
        context.story.ContinueMaximally()
        == "1) Seen first 1 times.\nIn second.\n2) Seen first 1 times.\n"
    )


def test_read_count_across_threads():
    context = from_json_test_context("read_count_across_threads", "builtins")
    assert context.story.ContinueMaximally() == "1\n1\n"


def test_read_count_dot_separated_path():
    context = from_json_test_context("read_count_dot_separated_path", "builtins")
    assert context.story.ContinueMaximally() == "hi\nhi\nhi\n3\n"


def test_read_count_variable_target():
    context = from_json_test_context("read_count_variable_target", "builtins")
    assert (
        context.story.ContinueMaximally()
        == "Count start: 0 0 0\n1\n2\n3\nCount end: 3 3 3\n"
    )


def test_turns_since_nested():
    context = from_json_test_context("turns_since_nested", "builtins")

    assert context.story.ContinueMaximally() == "-1 = -1\n"

    assert len(context.story.currentChoices) == 1
    context.story.ChooseChoiceIndex(0)
    assert context.story.ContinueMaximally() == "stuff\n0 = 0\n"

    assert len(context.story.currentChoices) == 1
    context.story.ChooseChoiceIndex(0)
    assert context.story.ContinueMaximally() == "more stuff\n1 = 1\n"


def test_turns_since_with_variable_target():
    context = from_json_test_context("turns_since_with_variable_target", "builtins")

    assert context.story.ContinueMaximally() == "0\n0\n"

    assert len(context.story.currentChoices) == 1
    context.story.ChooseChoiceIndex(0)
    assert context.story.ContinueMaximally() == "1\n"


def test_turns_since():
    context = from_json_test_context("turns_since", "builtins")

    assert context.story.ContinueMaximally() == "-1\n0\n"

    context.story.ChooseChoiceIndex(0)
    assert context.story.ContinueMaximally() == "1\n"

    context.story.ChooseChoiceIndex(0)
    assert context.story.ContinueMaximally() == "2\n"


def test_turns():
    context = from_json_test_context("turns", "builtins")

    for i in range(10):
        assert context.story.Continue() == f"{i}\n"
        context.story.ChooseChoiceIndex(0)


def test_visit_counts_when_choosing():
    context = from_json_test_context("visit_counts_when_choosing", "builtins")

    assert context.story.state.VisitCountAtPathString("TestKnot") == 0
    assert context.story.state.VisitCountAtPathString("TestKnot2") == 0

    context.story.ChoosePathString("TestKnot")

    assert context.story.state.VisitCountAtPathString("TestKnot") == 1
    assert context.story.state.VisitCountAtPathString("TestKnot2") == 0

    context.story.Continue()

    assert context.story.state.VisitCountAtPathString("TestKnot") == 1
    assert context.story.state.VisitCountAtPathString("TestKnot2") == 0

    context.story.ChooseChoiceIndex(0)

    assert context.story.state.VisitCountAtPathString("TestKnot") == 1
    assert context.story.state.VisitCountAtPathString("TestKnot2") == 0

    context.story.Continue()

    assert context.story.state.VisitCountAtPathString("TestKnot") == 1
    assert context.story.state.VisitCountAtPathString("TestKnot2") == 1


def test_visit_count_bug_due_to_nested_containers():
    context = from_json_test_context("visit_count_bug_due_to_nested_containers", "builtins")

    assert context.story.Continue() == "1\n"

    context.story.ChooseChoiceIndex(0)
    assert context.story.ContinueMaximally() == "choice\n1\n"
