from unittest.mock import Mock

import pytest

from tests.common import from_json_test_context


def test_should_load_file():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    assert context.story.canContinue is True


def test_should_jump_to_knot():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    context.story.ChoosePathString("knot")
    assert context.story.canContinue is True
    assert context.story.Continue() == "Knot content\n"


def test_should_get_current_path_string():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    context.story.ChoosePathString("knot")
    assert context.story.state.currentPathString == "knot.0"
    assert context.story.canContinue is True
    context.story.Continue()
    assert context.story.state.currentPathString is None
    assert context.story.canContinue is False


def test_should_jump_to_stitch():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    context.story.ChoosePathString("knot.stitch")
    assert context.story.canContinue is True
    assert context.story.Continue() == "Stitch content\n"


def test_should_read_variables_from_ink():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    assert context.story.variablesState["stringvar"] == "Emilia"
    assert context.story.variablesState["intvar"] == 521
    assert context.story.variablesState["floatvar"] == 52.1
    assert str(context.story.variablesState["divertvar"]) == "logic.logic_divert_dest"


def test_should_write_variables_to_ink():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    assert context.story.variablesState["stringvar"] == "Emilia"
    context.story.variablesState["stringvar"] = "Jonas"
    assert context.story.variablesState["stringvar"] == "Jonas"


def test_print_variables_part_1():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    context.story.variablesState["stringvar"] = "\n\nDear Emilia"
    context.story.ChoosePathString("integration.variable_print")
    assert context.story.Continue() == "Dear Emilia\n"


def test_print_variables_part_2():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    context.story.variablesState["stringvar"] = "\n\nDear Emilia, \nHope you are well\n\n      "
    context.story.ChoosePathString("integration.variable_print")
    assert context.story.Continue() == "Dear Emilia,\nHope you are well\n"


def test_observe_variables():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    context.story.ChoosePathString("integration.variable_observer")
    assert context.story.variablesState["observedVar1"] == 1
    assert context.story.variablesState["observedVar2"] == 2

    spy1 = Mock(name="variable observer spy 1")
    spy2 = Mock(name="variable observer spy 2")
    common_spy = Mock(name="variable observer spy common")
    context.story.ObserveVariable("observedVar1", spy1)
    context.story.ObserveVariable("observedVar2", spy2)
    context.story.ObserveVariable("observedVar1", common_spy)
    context.story.ObserveVariable("observedVar2", common_spy)

    assert context.story.Continue() == "declared\n"
    assert context.story.variablesState["observedVar1"] == 1
    assert context.story.variablesState["observedVar2"] == 2
    assert spy1.call_count == 0
    assert spy2.call_count == 0
    assert common_spy.call_count == 0

    assert context.story.Continue() == "mutated 1\n"
    assert context.story.variablesState["observedVar1"] == 3
    assert context.story.variablesState["observedVar2"] == 2
    assert spy1.call_count == 1
    spy1.assert_called_with("observedVar1", 3)
    assert spy2.call_count == 0
    assert common_spy.call_count == 1
    common_spy.assert_called_with("observedVar1", 3)

    assert context.story.Continue() == "mutated 2\n"
    assert context.story.variablesState["observedVar1"] == 4
    assert context.story.variablesState["observedVar2"] == 5
    assert spy1.call_count == 2
    spy1.assert_called_with("observedVar1", 4)
    assert spy2.call_count == 1
    spy2.assert_called_with("observedVar2", 5)


def test_visit_count_increment_each_visit():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    assert context.story.state.VisitCountAtPathString("integration.visit_count") == 0

    for i in range(10):
        context.story.ChoosePathString("integration.visit_count")
        assert context.story.Continue() == "visited\n"
        assert context.story.canContinue is False
        assert context.story.state.VisitCountAtPathString("integration.visit_count") == i + 1
        context.story.ChoosePathString("integration.variable_observer")
        context.story.Continue()


def test_visit_count_reset_callstack():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    assert context.story.state.VisitCountAtPathString("integration.visit_count") == 0
    for i in range(10):
        context.story.ChoosePathString("integration.visit_count")
        assert context.story.Continue() == "visited\n"
        assert context.story.state.VisitCountAtPathString("integration.visit_count") == i + 1


def test_visit_count_no_reset_callstack():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    assert context.story.state.VisitCountAtPathString("integration.visit_count") == 0
    for _ in range(10):
        context.story.ChoosePathString("integration.visit_count", False)
        assert context.story.Continue() == "visited\n"
        assert context.story.state.VisitCountAtPathString("integration.visit_count") == 1


def test_call_ink_functions():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    assert context.story.EvaluateFunction("fn_with_return") == "returned"
    assert context.story.EvaluateFunction("fn_without_return") is None
    assert context.story.EvaluateFunction("fn_print") is None
    assert context.story.EvaluateFunction("fn_calls_other") == "nested function called"


def test_call_ink_functions_with_params():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    assert context.story.EvaluateFunction("fn_params", ["a", "b"]) == "was a"
    assert context.story.EvaluateFunction("fn_echo", ["string"]) == "string"
    assert context.story.EvaluateFunction("fn_echo", [5]) == 5
    assert context.story.EvaluateFunction("fn_echo", [5.3]) == 5.3


def test_report_invalid_params_to_ink_functions():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True

    class BadParameter:
        pass

    with pytest.raises(Exception, match="Argument was BadParameter"):
        context.story.EvaluateFunction("fn_params", [BadParameter()])


def test_report_invalid_params_to_knots():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True

    class BadParameter:
        pass

    with pytest.raises(Exception, match="Argument was BadParameter"):
        context.story.ChoosePathString("stitch_with_param", True, [BadParameter()])


def test_return_output_and_return_value():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    assert context.story.EvaluateFunction("fn_print", [], True) == {
        "output": "function called\n",
        "returned": None,
    }
    assert context.story.EvaluateFunction("fn_echo", ["string"], True) == {
        "output": "string\n",
        "returned": "string",
    }
    assert context.story.EvaluateFunction("fn_echo", [5], True) == {
        "output": "5\n",
        "returned": 5,
    }
    assert context.story.EvaluateFunction("fn_echo", [5.3], True) == {
        "output": "5.3\n",
        "returned": 5.3,
    }
