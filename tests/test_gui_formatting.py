from powercalc.core import (
	CalculationError,
	CalculationErrorCode,
	EvaluationOptions,
	calculate,
)
from powercalc.gui.formatting import (
	format_error_for_display,
	format_result_for_display,
)


def result_for(expression):
	outcome = calculate(expression)
	assert outcome.ok
	assert outcome.result is not None
	return outcome.result


def test_integer_result_is_displayed_without_decimal_zeroes():
	assert format_result_for_display(result_for("2+3*4")) == "14"


def test_fraction_result_keeps_decimal_digits():
	assert format_result_for_display(result_for("1/3")) == "0.333333333333"


def test_irrational_result_uses_decimal_text():
	assert format_result_for_display(result_for("sqrt(2)")).startswith(
		"1.41421356237"
	)


def test_integer_result_in_comma_mode_is_displayed_without_decimal_zeroes():
	outcome = calculate("7+2", EvaluationOptions(decimal_separator="comma"))
	assert outcome.ok
	assert outcome.result is not None

	assert format_result_for_display(outcome.result, "comma") == "9"


def test_fraction_result_in_comma_mode_keeps_decimal_digits():
	outcome = calculate("1/3", EvaluationOptions(decimal_separator="comma"))
	assert outcome.ok
	assert outcome.result is not None

	assert (
		format_result_for_display(outcome.result, "comma") == "0,333333333333"
	)


def test_error_display_is_concise():
	error = CalculationError(
		CalculationErrorCode.EMPTY_EXPRESSION,
		"Expression is empty.",
	)

	assert format_error_for_display(error) == "Error: Expression is empty."
