from tests.common import from_json_test_context


def test_choice_count():
    context = from_json_test_context("choice_count", "choices")
    assert context.story.Continue() == "2\n"


def test_choice_diverts_to_done():
    context = from_json_test_context("choice_diverts_to_done", "choices")
    context.story.Continue()

    assert len(context.story.currentChoices) == 1
    context.story.ChooseChoiceIndex(0)

    assert context.story.Continue() == "choice"


def test_choice_with_brackets_only():
    context = from_json_test_context("choice_with_brackets_only", "choices")
    context.story.Continue()

    assert len(context.story.currentChoices) == 1
    assert context.story.currentChoices[0].text == "Option"
    context.story.ChooseChoiceIndex(0)

    assert context.story.Continue() == "Text\n"


def test_choice_thread_forking():
    context = from_json_test_context("choice_thread_forking", "choices")
    context.story.Continue()
    saved_state = context.story.state.ToJson()

    context = from_json_test_context("choice_thread_forking", "choices")
    context.story.state.LoadJson(saved_state)

    context.story.ChooseChoiceIndex(0)
    context.story.ContinueMaximally()

    assert context.story.hasWarning is False


def test_conditional_choices():
    context = from_json_test_context("conditional_choices", "choices")
    context.story.ContinueMaximally()

    assert len(context.story.currentChoices) == 4
    assert context.story.currentChoices[0].text == "one"
    assert context.story.currentChoices[1].text == "two"
    assert context.story.currentChoices[2].text == "three"
    assert context.story.currentChoices[3].text == "four"


def test_default_choice():
    context = from_json_test_context("default_choices", "choices")

    assert context.story.Continue() == ""
    assert len(context.story.currentChoices) == 2

    context.story.ChooseChoiceIndex(0)
    assert context.story.Continue() == "After choice\n"

    assert len(context.story.currentChoices) == 1

    context.story.ChooseChoiceIndex(0)
    assert context.story.ContinueMaximally() == "After choice\nThis is default.\n"


def test_default_simple_gather():
    context = from_json_test_context("default_simple_gather", "choices")
    assert context.story.Continue() == "x\n"


def test_fallback_choice_on_thread():
    context = from_json_test_context("fallback_choice_on_thread", "choices")
    assert context.story.Continue() == "Should be 1 not 0: 1.\n"


def test_gather_choice_same_line():
    context = from_json_test_context("gather_choice_same_line", "choices")

    context.story.Continue()
    assert context.story.currentChoices[0].text == "hello"

    context.story.ChooseChoiceIndex(0)
    context.story.Continue()

    assert context.story.currentChoices[0].text == "world"


def test_has_read_on_choice():
    context = from_json_test_context("has_read_on_choice", "choices")

    context.story.ContinueMaximally()
    assert len(context.story.currentChoices) == 1
    assert context.story.currentChoices[0].text == "visible choice"


def test_logic_in_choices():
    context = from_json_test_context("logic_in_choices", "choices")

    context.story.ContinueMaximally()
    assert context.story.currentChoices[0].text == "'Hello Joe, your name is Joe.'"
    context.story.ChooseChoiceIndex(0)
    assert (
        context.story.ContinueMaximally()
        == "'Hello Joe,' I said, knowing full well that his name was Joe.\n"
    )


def test_non_text_in_choice_inner_content():
    context = from_json_test_context("non_text_in_choice_inner_content", "choices")

    context.story.Continue()
    context.story.ChooseChoiceIndex(0)

    assert context.story.Continue() == "option text. Conditional bit. Next.\n"


def test_once_only_choices_can_link_back_to_self():
    context = from_json_test_context("once_only_choices_can_link_back_to_self", "choices")

    context.story.ContinueMaximally()

    assert len(context.story.currentChoices) == 1
    assert context.story.currentChoices[0].text == "First choice"

    context.story.ChooseChoiceIndex(0)
    context.story.ContinueMaximally()

    assert len(context.story.currentChoices) == 1
    assert context.story.currentChoices[0].text == "Second choice"

    context.story.ChooseChoiceIndex(0)
    context.story.ContinueMaximally()

    assert context.story.hasError is False


def test_once_only_choices_with_own_content():
    context = from_json_test_context("once_only_choices_with_own_content", "choices")

    context.story.ContinueMaximally()

    assert len(context.story.currentChoices) == 3

    context.story.ChooseChoiceIndex(0)
    context.story.ContinueMaximally()

    assert len(context.story.currentChoices) == 2

    context.story.ChooseChoiceIndex(0)
    context.story.ContinueMaximally()

    assert len(context.story.currentChoices) == 1

    context.story.ChooseChoiceIndex(0)
    context.story.ContinueMaximally()

    assert len(context.story.currentChoices) == 0


def test_should_not_gather_due_to_choice():
    context = from_json_test_context("should_not_gather_due_to_choice", "choices")

    context.story.ContinueMaximally()
    context.story.ChooseChoiceIndex(0)

    assert context.story.ContinueMaximally() == "opt\ntext\n"


def test_sticky_choices_stay_sticky():
    context = from_json_test_context("sticky_choices_stay_sticky", "choices")

    context.story.ContinueMaximally()
    assert len(context.story.currentChoices) == 2

    context.story.ChooseChoiceIndex(0)
    context.story.ContinueMaximally()
    assert len(context.story.currentChoices) == 2


def test_various_default_choices():
    context = from_json_test_context("various_default_choices", "choices")
    assert context.story.ContinueMaximally() == "1\n2\n3\n"


def test_state_rollback_over_default_choice():
    context = from_json_test_context("state_rollback_over_default_choice", "choices")

    assert context.story.Continue() == "Text.\n"
    assert context.story.Continue() == "5\n"


def test_tags_in_choice():
    context = from_json_test_context("tags_in_choice", "choices")
    context.story.Continue()

    assert len(context.story.currentTags) == 0
    assert len(context.story.currentChoices) == 1
    assert context.story.currentChoices[0].tags == ["one", "two"]

    context.story.ChooseChoiceIndex(0)
    assert context.story.Continue() == "one three"
    assert context.story.currentTags == ["one", "three"]


def test_fallback_choices_remain_hidden_after_load():
    context = from_json_test_context("default_choices", "choices")
    context.story.Continue()

    assert len(context.story.currentChoices) == 2
    assert context.story.currentChoices[0].text == "Choice 1"
    assert context.story.currentChoices[1].text == "Choice 2"

    saved_state = context.story.state.ToJson()
    context.story.state.LoadJson(saved_state)

    assert len(context.story.currentChoices) == 2
    assert context.story.currentChoices[0].text == "Choice 1"
    assert context.story.currentChoices[1].text == "Choice 2"
