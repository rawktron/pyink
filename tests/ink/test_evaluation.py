from tests.common import from_json_test_context


def test_arithmetic():
    context = from_json_test_context("arithmetic", "evaluation")
    assert context.story.ContinueMaximally() == "36\n2\n3\n2\n2.3333333333333335\n8\n8\n"


def test_basic_string_literals():
    context = from_json_test_context("basic_string_literals", "evaluation")
    assert context.story.ContinueMaximally() == "Hello world 1\nHello world 2.\n"


def test_evaluating_function_variable_state_bug():
    context = from_json_test_context("evaluating_function_variable_state_bug", "evaluation")

    assert context.story.Continue() == "Start\n"
    assert context.story.Continue() == "In tunnel.\n"

    func_result = context.story.EvaluateFunction("function_to_evaluate")
    assert func_result == "RIGHT"
    assert context.story.Continue() == "End\n"


def test_evaluating_ink_functions_from_game():
    context = from_json_test_context("evaluating_ink_functions_from_game", "evaluation")

    context.story.Continue()

    returned_divert_target = context.story.EvaluateFunction("test")
    assert returned_divert_target == "-> somewhere.here"


def test_evaluating_ink_functions_from_game_2():
    context = from_json_test_context("evaluating_ink_functions_from_game_2", "evaluation")

    func_result = context.story.EvaluateFunction("func1", [], True)

    assert func_result["output"] == "This is a function\n"
    assert func_result["returned"] == 5

    assert context.story.Continue() == "One\n"

    func_result = context.story.EvaluateFunction("func2", [], True)

    assert func_result["output"] == "This is a function without a return value\n"
    assert func_result["returned"] is None

    assert context.story.Continue() == "Two\n"

    func_result = context.story.EvaluateFunction("add", [1, 2], True)

    assert func_result["output"] == "x = 1, y = 2\n"
    assert func_result["returned"] == 3

    assert context.story.Continue() == "Three\n"


def test_evaluation_stack_leaks():
    context = from_json_test_context("evaluation_stack_leaks", "evaluation")

    assert context.story.ContinueMaximally() == "else\nelse\nhi\n"
    assert len(context.story.state.evaluationStack) == 0


def test_factorial_by_reference():
    context = from_json_test_context("factorial_by_reference", "evaluation")

    assert context.story.ContinueMaximally() == "120\n"


def test_factorial_recursive():
    context = from_json_test_context("factorial_recursive", "evaluation")

    assert context.story.ContinueMaximally() == "120\n"


def test_increment():
    context = from_json_test_context("increment", "evaluation")

    assert context.story.ContinueMaximally() == "6\n5\n"


def test_literal_unary():
    context = from_json_test_context("literal_unary", "evaluation")

    assert context.story.ContinueMaximally() == "-1\nfalse\ntrue\n"
