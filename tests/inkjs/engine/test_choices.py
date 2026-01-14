import pytest

from tests.common import from_json_test_context


@pytest.fixture()
def context():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    return context


def test_offer_single_choice(context):
    context.story.ChoosePathString("choices.basic_choice")
    context.story.Continue()
    assert len(context.story.currentChoices) == 1
    assert context.story.canContinue is False


def test_offer_multiple_choices(context):
    context.story.ChoosePathString("choices.multiple_choices")
    context.story.Continue()
    assert len(context.story.currentChoices) == 3
    assert context.story.canContinue is False


def test_select_choice(context):
    context.story.ChoosePathString("choices.multiple_choices")
    context.story.Continue()
    context.story.ChooseChoiceIndex(0)
    assert context.story.Continue() == "choice 1\n"
    assert context.story.canContinue is False


def test_invalid_choice_throws(context):
    context.story.ChoosePathString("choices.multiple_choices")
    context.story.Continue()
    with pytest.raises(Exception):
        context.story.ChooseChoiceIndex(10)


def test_suppress_choice_text(context):
    context.story.ChoosePathString("choices.choice_text")
    context.story.Continue()
    assert len(context.story.currentChoices) == 1
    assert context.story.canContinue is False
    assert context.story.currentChoices[0].text == "always choice only"
    context.story.ChooseChoiceIndex(0)
    assert context.story.canContinue is True
    assert context.story.Continue() == "always output only\n"
    assert context.story.canContinue is False


def test_suppress_choices_after_selected(context):
    context.story.ChoosePathString("choices.suppression")
    assert context.story.canContinue is True
    context.story.Continue()

    assert len(context.story.currentChoices) == 2
    assert context.story.currentChoices[0].text == "choice 1"
    assert context.story.currentChoices[1].text == "choice 2"

    context.story.ChooseChoiceIndex(1)
    assert context.story.Continue() == "choice 2\n"
    assert context.story.canContinue is False

    context.story.ChoosePathString("choices.suppression")
    assert context.story.canContinue is True
    context.story.Continue()

    assert len(context.story.currentChoices) == 1
    assert context.story.currentChoices[0].text == "choice 1"

    context.story.ChooseChoiceIndex(0)
    assert context.story.Continue() == "choice 1\n"
    assert context.story.canContinue is False

    context.story.ChoosePathString("choices.suppression")
    assert context.story.canContinue is True


def test_select_fallback_choice(context):
    context.story.ChoosePathString("choices.fallback")
    assert context.story.canContinue is True
    context.story.Continue()

    assert len(context.story.currentChoices) == 1
    assert context.story.currentChoices[0].text == "choice 1"
    context.story.ChooseChoiceIndex(0)
    context.story.Continue()

    context.story.ChoosePathString("choices.fallback")
    assert context.story.canContinue is True
    context.story.Continue()

    assert len(context.story.currentChoices) == 0
    assert context.story.canContinue is False


def test_sticky_choice(context):
    context.story.ChoosePathString("choices.sticky")
    assert context.story.canContinue is True
    context.story.Continue()

    assert len(context.story.currentChoices) == 2
    assert context.story.currentChoices[0].text == "disapears"
    assert context.story.currentChoices[1].text == "stays"

    context.story.ChooseChoiceIndex(0)
    context.story.Continue()

    for _ in range(3):
        context.story.ChoosePathString("choices.sticky")
        assert context.story.canContinue is True
        context.story.Continue()

        assert len(context.story.currentChoices) == 1
        assert context.story.currentChoices[0].text == "stays"
        context.story.ChooseChoiceIndex(0)
        assert context.story.Continue() == "stays\n"


def test_conditional_choices(context):
    context.story.ChoosePathString("choices.conditional")
    assert context.story.canContinue is True
    context.story.Continue()

    assert len(context.story.currentChoices) == 3
    assert context.story.currentChoices[0].text == "no condition"
    assert context.story.currentChoices[1].text == "available"
    assert context.story.currentChoices[2].text == "multi condition available"
