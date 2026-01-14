from tests.common import from_json_test_context


def test_basic_tunnel():
    context = from_json_test_context("basic_tunnel", "diverts")

    assert context.story.Continue() == "Hello world\n"


def test_compare_divert_targets():
    context = from_json_test_context("compare_divert_targets", "diverts")

    assert (
        context.story.ContinueMaximally()
        == "different knot\nsame knot\nsame knot\ndifferent knot\nsame knot\nsame knot\n"
    )


def test_complex_tunnels():
    context = from_json_test_context("complex_tunnels", "diverts")

    assert (
        context.story.ContinueMaximally()
        == "one (1)\none and a half (1.5)\ntwo (2)\nthree (3)\n"
    )


def test_divert_in_conditional():
    context = from_json_test_context("divert_in_conditional", "diverts")

    assert context.story.ContinueMaximally() == ""


def test_divert_targets_with_parameters():
    context = from_json_test_context("divert_targets_with_parameters", "diverts")

    assert context.story.ContinueMaximally() == "5\n"


def test_divert_to_weave_points():
    context = from_json_test_context("divert_to_weave_points", "diverts")

    assert (
        context.story.ContinueMaximally()
        == "gather\ntest\nchoice content\ngather\nsecond time round\n"
    )


def test_done_stops_thread():
    context = from_json_test_context("done_stops_thread", "diverts")

    assert context.story.ContinueMaximally() == ""


def test_path_to_self():
    context = from_json_test_context("path_to_self", "diverts")

    context.story.Continue()
    context.story.ChooseChoiceIndex(0)

    context.story.Continue()
    context.story.ChooseChoiceIndex(0)

    assert context.story.canContinue is True


def test_same_line_divert_is_inline():
    context = from_json_test_context("same_line_divert_is_inline", "diverts")

    assert (
        context.story.Continue()
        == "We hurried home to Savile Row as fast as we could.\n"
    )


def test_tunnel_onwards_after_tunnel():
    context = from_json_test_context("tunnel_onwards_after_tunnel", "diverts")

    assert context.story.ContinueMaximally() == "Hello...\n...world.\nThe End.\n"


def test_tunnel_onwards_divert_after_with_arg():
    context = from_json_test_context("tunnel_onwards_divert_after_with_arg", "diverts")

    assert context.story.ContinueMaximally() == "8\n"


def test_tunnel_onwards_divert_override():
    context = from_json_test_context("tunnel_onwards_divert_override", "diverts")

    assert context.story.ContinueMaximally() == "This is A\nNow in B.\n"


def test_tunnel_onwards_with_param_default_choice():
    context = from_json_test_context("tunnel_onwards_with_param_default_choice", "diverts")

    assert context.story.ContinueMaximally() == "8\n"


def test_tunnel_vs_thread_behaviour():
    context = from_json_test_context("tunnel_vs_thread_behaviour", "diverts")

    assert "Finished tunnel" not in context.story.ContinueMaximally()
    assert len(context.story.currentChoices) == 2

    context.story.ChooseChoiceIndex(0)

    assert "Finished tunnel" in context.story.ContinueMaximally()
    assert len(context.story.currentChoices) == 3

    context.story.ChooseChoiceIndex(2)

    assert "Done." in context.story.ContinueMaximally()


def test_tunnel_onwards_to_variable_divert_target():
    context = from_json_test_context("tunnel_onwards_to_variable_divert_target", "diverts")

    assert "This is outer\nThis is the_esc\n" in context.story.ContinueMaximally()
