import pytest

from tests.common import from_json_test_context


@pytest.fixture()
def context():
    context = from_json_test_context("tests", "inkjs")
    context.story.allowExternalFunctionFallbacks = True
    return context


def test_define_variables(context):
    context.story.ChoosePathString("logic.vardef")
    assert context.story.Continue() == "variables defined: Emilia 521 52.1\n"


def test_cast_variables(context):
    context.story.ChoosePathString("logic.casts")
    assert context.story.Continue() == "521.5\n"
    assert context.story.Continue() == "521hello\n"
    assert context.story.Continue() == "float var is truthy\n"
    assert context.story.Continue() == "52.1hello\n"
    assert context.story.Continue() == "string var is truthy\n"


def test_math_operations(context):
    context.story.ChoosePathString("logic.math")

    assert context.story.Continue() == "2\n"
    assert context.story.Continue() == "0\n"
    assert context.story.Continue() == "-5\n"
    assert context.story.Continue() == "2\n"
    assert context.story.Continue() == "5\n"
    assert context.story.Continue() == "1\n"

    assert context.story.Continue() == "int truthy equal\n"
    assert context.story.Continue() == "int falsy equal\n"

    assert context.story.Continue() == "int truthy greater\n"
    assert context.story.Continue() == "int falsy greater\n"

    assert context.story.Continue() == "int truthy lesser\n"
    assert context.story.Continue() == "int falsy lesser\n"

    assert context.story.Continue() == "int truthy greater or equal\n"
    assert context.story.Continue() == "int falsy greater or equal\n"

    assert context.story.Continue() == "int truthy lesser or equal\n"
    assert context.story.Continue() == "int falsy lesser or equal\n"

    assert context.story.Continue() == "int truthy not equal\n"
    assert context.story.Continue() == "int falsy not equal\n"

    assert context.story.Continue() == "int truthy not\n"
    assert context.story.Continue() == "int falsy not\n"

    assert context.story.Continue() == "int truthy and\n"
    assert context.story.Continue() == "int falsy and\n"

    assert context.story.Continue() == "int truthy or\n"
    assert context.story.Continue() == "int falsy or\n"

    assert float(context.story.Continue()) == pytest.approx(2.6)
    assert float(context.story.Continue()) == pytest.approx(0)
    assert float(context.story.Continue()) == pytest.approx(-5.2)
    assert float(context.story.Continue()) == pytest.approx(3.6)
    assert float(context.story.Continue()) == pytest.approx(4.2)
    assert float(context.story.Continue()) == pytest.approx(1.5)

    assert context.story.Continue() == "float truthy equal\n"
    assert context.story.Continue() == "float falsy equal\n"

    assert context.story.Continue() == "float truthy greater\n"
    assert context.story.Continue() == "float falsy greater\n"

    assert context.story.Continue() == "float truthy lesser\n"
    assert context.story.Continue() == "float falsy lesser\n"

    assert context.story.Continue() == "float truthy greater or equal\n"
    assert context.story.Continue() == "float falsy greater or equal\n"

    assert context.story.Continue() == "float truthy lesser or equal\n"
    assert context.story.Continue() == "float falsy lesser or equal\n"

    assert context.story.Continue() == "float truthy not equal\n"
    assert context.story.Continue() == "float falsy not equal\n"

    assert context.story.Continue() == "float falsy not\n"

    assert context.story.Continue() == "float truthy and\n"
    assert context.story.Continue() == "float falsy and\n"

    assert context.story.Continue() == "float truthy or\n"
    assert context.story.Continue() == "float falsy or\n"

    assert context.story.Continue() == "truthy string equal\n"
    assert context.story.Continue() == "falsy string equal\n"
    assert context.story.Continue() == "truthy string not equal\n"
    assert context.story.Continue() == "falsy string not equal\n"
    assert context.story.Continue() == "truthy divert equal\n"
    assert context.story.Continue() == "falsy divert equal\n"


def test_if_else(context):
    context.story.ChoosePathString("logic.ifelse")
    assert context.story.Continue() == "if text\n"
    assert context.story.Continue() == "else text\n"
    assert context.story.Continue() == "elseif text\n"


def test_stitch_params(context):
    context.story.ChoosePathString("logic.stitch_param")
    assert context.story.Continue() == "Called with param\n"


def test_constants(context):
    context.story.ChoosePathString("logic.constants")
    assert context.story.Continue() == "constants defined: Emilia 521 52.1\n"


def test_simple_functions(context):
    context.story.ChoosePathString("logic.simple_functions")
    assert context.story.Continue() == "returned\n"
    assert context.story.Continue() == "function called\n"
    assert context.story.Continue() == "nested function called\n"
    assert context.story.Continue() == "Function called inline and returned something\n"


def test_param_functions(context):
    context.story.ChoosePathString("logic.param_functions")
    assert context.story.variablesState["fnParamA"] == "a"
    assert context.story.variablesState["fnParamB"] == "b"

    assert context.story.Continue() == "was a\n"
    assert context.story.variablesState["fnParamA"] == "a"
    assert context.story.variablesState["fnParamB"] == "b"

    assert context.story.Continue() == "was a\n"
    assert context.story.variablesState["fnParamA"] == "was a"
    assert context.story.variablesState["fnParamB"] == "was b"

    assert context.story.canContinue is False


def test_void_function(context):
    context.story.ChoosePathString("logic.void_function")
    context.story.Continue()
    assert context.story.canContinue is False


def test_random_numbers(context):
    context.story.ChoosePathString("logic.random")
    assert context.story.Continue() == "27\n"
    assert context.story.Continue() == "8\n"
