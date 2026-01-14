from tests.common import from_json_test_context


def test_arithmetic_2():
    context = from_json_test_context("arithmetic_2", "extra")

    assert (
        context.story.ContinueMaximally()
        == "2\n2.3333333333333335\n2.3333333333333335\n2.3333333333333335\n2.3333333333333335\n2.3333333333333335\n"
    )
