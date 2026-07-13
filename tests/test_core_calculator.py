import pytest
import sympy as sp

from powercalc.core import (
	CalculationError,
	CalculationErrorCode,
	CalculationOutcome,
	CalculationResult,
	EvaluationOptions,
	calculate,
)


def assert_ok(expression, options=None):
	outcome = calculate(expression, options)
	assert outcome.ok, outcome.error
	assert outcome.result is not None
	return outcome.result


def assert_error(expression, code=None, options=None):
	outcome = calculate(expression, options)
	assert not outcome.ok
	assert outcome.result is None
	assert outcome.error is not None
	assert isinstance(outcome.error.code, CalculationErrorCode)
	if code is not None:
		assert outcome.error.code == code
	return outcome.error


def assert_same_value(actual, expected):
	assert sp.simplify(actual - expected) == 0


def test_basic_arithmetic_and_power():
	assert_same_value(assert_ok("2+3*4").value, sp.Integer(14))
	assert_same_value(assert_ok("(1+2)^3").value, sp.Integer(27))
	assert_same_value(assert_ok("2**3").value, sp.Integer(8))


def test_success_outcome_contract():
	outcome = calculate("1 + 1")

	assert outcome.ok is True
	assert isinstance(outcome.result, CalculationResult)
	assert outcome.error is None


def test_failure_outcome_contract():
	outcome = calculate("unknown_name")

	assert outcome.ok is False
	assert outcome.result is None
	assert isinstance(outcome.error, CalculationError)
	assert outcome.error.code is CalculationErrorCode.UNKNOWN_NAME


def test_outcome_factories_enforce_invariants():
	result = assert_ok("2")
	error = CalculationError(
		CalculationErrorCode.EMPTY_EXPRESSION,
		"Expression is empty.",
	)

	success = CalculationOutcome.success(result)
	failure = CalculationOutcome.failure(error)

	assert success.ok is True
	assert success.result == result
	assert success.error is None
	assert failure.ok is False
	assert failure.result is None
	assert failure.error == error

	with pytest.raises(TypeError):
		CalculationOutcome(ok=True, result=result)

	with pytest.raises(ValueError):
		CalculationOutcome._create(ok=True, result=None, error=error)

	with pytest.raises(ValueError):
		CalculationOutcome._create(ok=False, result=result, error=None)


def test_exact_and_decimal_output():
	result = assert_ok("sqrt(2)")

	assert result.exact_text == "sqrt(2)"
	assert result.decimal_text.startswith("1.41421356237")


def test_comma_separator_localizes_all_result_text_fields():
	options = EvaluationOptions(decimal_separator="comma")
	result = assert_ok("1,5 + 0,25", options)

	assert result.input_text == "1,5 + 0,25"
	assert result.normalized_text == "1,5 + 0,25"
	assert result.exact_text == "1,75000000000000"
	assert result.decimal_text == "1,75000000000"
	assert str(result.value) == "1.75000000000000"


def test_comma_separator_localizes_complex_and_scientific_results():
	options = EvaluationOptions(decimal_separator="comma")
	complex_result = assert_ok("sqrt(-2,25)", options)
	scientific_result = assert_ok("-1,5e-20", options)

	assert "." not in complex_result.decimal_text
	assert complex_result.normalized_text == "sqrt(-2,25)"
	assert complex_result.exact_text == "1,5*I"
	assert complex_result.decimal_text == "1,5*I"
	assert scientific_result.normalized_text == "-1,5e-20"
	assert scientific_result.exact_text == "-1,50000000000000e-20"
	assert scientific_result.decimal_text.startswith("-1,500")
	assert scientific_result.decimal_text.endswith("e-20")


def test_default_options_match_explicit_point_separator():
	for expression in ("1.5 + 2", "log(8, 2)", "sqrt(-2)"):
		default_outcome = calculate(expression)
		explicit_outcome = calculate(
			expression,
			EvaluationOptions(decimal_separator="point"),
		)

		assert default_outcome == explicit_outcome


def test_default_log_is_base_10():
	assert_same_value(assert_ok("log(100)").value, sp.Integer(2))
	assert_same_value(assert_ok("ln(e)").value, sp.Integer(1))
	assert_same_value(assert_ok("log10(1000)").value, sp.Integer(3))


def test_natural_log_mode_changes_one_argument_log():
	options = EvaluationOptions(log_mode="natural")

	assert_same_value(assert_ok("log(e)", options).value, sp.Integer(1))


def test_explicit_log_base_is_supported():
	assert_same_value(assert_ok("log(8, 2)").value, sp.Integer(3))


def test_multi_argument_functions_use_selected_separators():
	comma_options = EvaluationOptions(decimal_separator="comma")

	comma_log = assert_ok("log(8; 2)", comma_options)
	comma_min = assert_ok("min(1,5; 2,5)", comma_options)
	comma_max = assert_ok("max(1,5; 2,5)", comma_options)
	point_semicolon = assert_ok("log(8; 2)")

	assert_same_value(comma_log.value, sp.Integer(3))
	assert comma_log.normalized_text == "log(8; 2)"
	assert_same_value(comma_min.value, sp.Float("1.5"))
	assert_same_value(comma_max.value, sp.Float("2.5"))
	assert_same_value(point_semicolon.value, sp.Integer(3))
	assert point_semicolon.normalized_text == "log(8, 2)"


def test_comma_inside_number_is_not_a_function_argument_separator():
	options = EvaluationOptions(decimal_separator="comma")
	square_root = assert_ok("sqrt(2,25)", options)
	one_argument_log = assert_ok("log(8,2)", options)
	explicit_base_log = assert_ok("log(8; 2)", options)

	assert_same_value(square_root.value, sp.Float("1.5"))
	assert_same_value(
		one_argument_log.value,
		sp.log(sp.Float("8.2"), 10),
	)
	assert_same_value(explicit_base_log.value, sp.Integer(3))


def test_comma_separator_survives_expression_normalization():
	options = EvaluationOptions(decimal_separator="comma")
	power = assert_ok("(2,5)^2", options)
	function_power = assert_ok("max(2; 3)^2", options)
	factorial = assert_ok("5!", options)

	assert power.normalized_text == "(2,5)**2"
	assert function_power.normalized_text == "max(2; 3)**2"
	assert factorial.normalized_text == "factorial(5)"
	assert_same_value(power.value, sp.Float("6.25"))
	assert_same_value(function_power.value, sp.Integer(9))
	assert_same_value(factorial.value, sp.Integer(120))


def test_trigonometry_uses_radians_by_default():
	assert_same_value(assert_ok("sin(pi/2)").value, sp.Integer(1))
	assert_same_value(assert_ok("asin(1)").value, sp.pi / 2)


def test_degree_angle_unit_affects_trig_and_inverse_trig():
	options = EvaluationOptions(angle_unit="degree")

	assert_same_value(assert_ok("sin(90)", options).value, sp.Integer(1))
	assert_same_value(assert_ok("asin(1)", options).value, sp.Integer(90))
	assert assert_ok("sin(pi/2)", options).value != 1


def test_gradian_angle_unit_affects_trig_and_inverse_trig():
	options = EvaluationOptions(angle_unit="gradian")

	assert_same_value(assert_ok("sin(100)", options).value, sp.Integer(1))
	assert_same_value(assert_ok("asin(1)", options).value, sp.Integer(100))


def test_supported_broad_function_set():
	assert_same_value(assert_ok("5!").value, sp.Integer(120))
	assert_same_value(assert_ok("(2+3)!").value, sp.Integer(120))
	assert_same_value(assert_ok("5 % 2").value, sp.Integer(1))
	assert_same_value(assert_ok("gamma(5)").value, sp.Integer(24))
	assert_same_value(assert_ok("floor(2.9)").value, sp.Integer(2))
	assert_same_value(assert_ok("ceil(2.1)").value, sp.Integer(3))
	assert_same_value(assert_ok("min(3, 1, 2)").value, sp.Integer(1))
	assert_same_value(assert_ok("max(3, 1, 2)").value, sp.Integer(3))
	assert_same_value(assert_ok("re(1+2*i)").value, sp.Integer(1))
	assert_same_value(assert_ok("im(1+2*I)").value, sp.Integer(2))
	assert_same_value(assert_ok("sign(-5)").value, sp.Integer(-1))


def test_complex_is_default_number_domain():
	assert_same_value(assert_ok("sqrt(-1)").value, sp.I)
	assert_same_value(assert_ok("log(-1)").value, sp.I * sp.pi / sp.log(10))


def test_real_number_domain_rejects_complex_results():
	options = EvaluationOptions(number_domain="real")

	assert_error("sqrt(-1)", CalculationErrorCode.NON_REAL_RESULT, options)


def test_unknown_names_and_functions_are_rejected():
	assert_error("x + 1", CalculationErrorCode.UNKNOWN_NAME)
	assert_error("foo(1)", CalculationErrorCode.UNKNOWN_FUNCTION)


def test_unsafe_or_unsupported_syntax_is_rejected():
	assert_error("__import__('os')", CalculationErrorCode.UNSUPPORTED_LITERAL)
	assert_error("(1).__class__", CalculationErrorCode.UNSUPPORTED_SYNTAX)
	assert_error("[1, 2, 3]", CalculationErrorCode.UNSUPPORTED_SYNTAX)
	assert_error("sin(90 deg)", CalculationErrorCode.INVALID_EXPRESSION)


def test_invalid_argument_counts_are_rejected():
	assert_error("sin(1, 2)", CalculationErrorCode.INVALID_ARGUMENT_COUNT)
	assert_error("min()", CalculationErrorCode.INVALID_ARGUMENT_COUNT)
	assert_error("log(1, 2, 3)", CalculationErrorCode.INVALID_ARGUMENT_COUNT)


def test_invalid_separators_are_rejected_in_comma_mode():
	options = EvaluationOptions(decimal_separator="comma")

	point_error = assert_error(
		"1.5 + 2",
		CalculationErrorCode.INVALID_SEPARATOR,
		options,
	)
	argument_error = assert_error(
		"log(8, 2)",
		CalculationErrorCode.INVALID_SEPARATOR,
		options,
	)

	assert point_error.position == 1
	assert argument_error.position == 5


@pytest.mark.parametrize(
	("expression", "code", "position"),
	[
		(",5", CalculationErrorCode.INVALID_SEPARATOR, 0),
		("5,", CalculationErrorCode.INVALID_SEPARATOR, 1),
		("1,2,3", CalculationErrorCode.INVALID_EXPRESSION, None),
	],
)
def test_malformed_comma_numbers_are_rejected(expression, code, position):
	options = EvaluationOptions(decimal_separator="comma")

	error = assert_error(expression, code, options)

	assert error.position == position


def test_invalid_decimal_separator_option_is_rejected():
	options = EvaluationOptions(decimal_separator="invalid")

	assert_error("1 + 1", CalculationErrorCode.INVALID_OPTION, options)


def test_comma_separator_combines_with_other_evaluation_options():
	degree_result = assert_ok(
		"sin(90,0)",
		EvaluationOptions(decimal_separator="comma", angle_unit="degree"),
	)
	natural_log_result = assert_ok(
		"log(2,5)",
		EvaluationOptions(decimal_separator="comma", log_mode="natural"),
	)
	real_mode_options = EvaluationOptions(
		decimal_separator="comma",
		number_domain="real",
	)

	assert_same_value(degree_result.value, sp.Integer(1))
	assert degree_result.normalized_text == "sin(90,0)"
	assert_same_value(natural_log_result.value, sp.log(sp.Float("2.5")))
	assert "." not in natural_log_result.exact_text
	assert "." not in natural_log_result.decimal_text
	assert_error(
		"sqrt(-1,0)",
		CalculationErrorCode.NON_REAL_RESULT,
		real_mode_options,
	)


def test_invalid_factorial_is_rejected():
	assert_error("2.5!", CalculationErrorCode.INVALID_FACTORIAL)
	assert_error("(-1)!", CalculationErrorCode.INVALID_FACTORIAL)


def test_undefined_and_too_large_expressions_are_rejected():
	assert_error("1/0", CalculationErrorCode.UNDEFINED_RESULT)
	assert_error("2^10001", CalculationErrorCode.EXPONENT_TOO_LARGE)
	assert_error("1001!", CalculationErrorCode.FACTORIAL_TOO_LARGE)
	assert_error("1" * 501, CalculationErrorCode.EXPRESSION_TOO_LONG)
