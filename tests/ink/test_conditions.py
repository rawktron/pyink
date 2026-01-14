from tests.common import from_json_test_context


def test_all_switch_branches_fail_is_clean():
    context = from_json_test_context("all_switch_branches_fail_is_clean", "conditions")

    context.story.Continue()
    assert len(context.story.state.evaluationStack) == 0


def test_conditionals():
    context = from_json_test_context("conditionals", "conditions")

    assert (
        context.story.ContinueMaximally()
        == "true\ntrue\ntrue\ntrue\ntrue\ngreat\nright?\n"
    )


def test_else_branches():
    context = from_json_test_context("else_branches", "conditions")

    assert context.story.ContinueMaximally() == "other\nother\nother\nother\n"


def test_empty_multiline_conditional_branch():
    context = from_json_test_context("empty_multiline_conditional_branch", "conditions")

    assert context.story.Continue() == ""


def test_trivial_condition():
    context = from_json_test_context("trivial_condition", "conditions")

    context.story.Continue()
