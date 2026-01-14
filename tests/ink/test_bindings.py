from tests.common import from_json_test_context


def test_external_bindings():
    context = from_json_test_context("external_binding", "bindings")

    test_external_binding_message = ""

    def message(arg):
        nonlocal test_external_binding_message
        test_external_binding_message = "MESSAGE: " + arg

    def multiply(arg1, arg2):
        return arg1 * arg2

    def times(number_of_times, string_value):
        return string_value * number_of_times

    context.story.BindExternalFunction("message", message)
    context.story.BindExternalFunction("multiply", multiply)
    context.story.BindExternalFunction("times", times)

    assert context.story.Continue() == "15\n"
    assert context.story.Continue() == "knock knock knock\n"
    assert test_external_binding_message == "MESSAGE: hello world"


def test_game_ink_back_and_forth():
    context = from_json_test_context("game_ink_back_and_forth", "bindings")

    def game_inc(x):
        x += 1
        x = context.story.EvaluateFunction("inkInc", [x])
        return x

    context.story.BindExternalFunction("gameInc", game_inc)

    final_result = context.story.EvaluateFunction("topExternal", [5], True)

    assert final_result["returned"] == 7
    assert final_result["output"] == "In top external\n"


def test_variable_observer():
    context = from_json_test_context("variable_observer", "bindings")

    current_var_value = 0
    observer_call_count = 0

    def observer(_var_name, new_value):
        nonlocal current_var_value, observer_call_count
        current_var_value = new_value
        observer_call_count += 1

    context.story.ObserveVariable("testVar", observer)
    context.story.ContinueMaximally()

    assert current_var_value == 15
    assert observer_call_count == 1

    context.story.ChooseChoiceIndex(0)
    context.story.Continue()

    assert current_var_value == 25
    assert observer_call_count == 2


def test_lookup_safe_or_not():
    context = from_json_test_context("lookup_safe_or_not", "bindings")

    call_count = 0

    def my_action():
        nonlocal call_count
        call_count += 1

    context.story.BindExternalFunction("myAction", my_action, True)
    context.story.ContinueMaximally()
    assert call_count == 2

    call_count = 0
    context.story.ResetState()
    context.story.UnbindExternalFunction("myAction")
    context.story.BindExternalFunction("myAction", my_action, False)

    context.story.ContinueMaximally()
    assert call_count == 1

    context = from_json_test_context("lookup_safe_or_not_with_post_glue", "bindings")
    context.story.BindExternalFunction("myAction", lambda: None)
    assert context.story.ContinueMaximally() == "One\nTwo\n"
