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


def test_default_log_is_base_10():
	assert_same_value(assert_ok("log(100)").value, sp.Integer(2))
	assert_same_value(assert_ok("ln(e)").value, sp.Integer(1))
	assert_same_value(assert_ok("log10(1000)").value, sp.Integer(3))


def test_natural_log_mode_changes_one_argument_log():
	options = EvaluationOptions(log_mode="natural")

	assert_same_value(assert_ok("log(e)", options).value, sp.Integer(1))


def test_explicit_log_base_is_supported():
	assert_same_value(assert_ok("log(8, 2)").value, sp.Integer(3))


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


def test_invalid_factorial_is_rejected():
	assert_error("2.5!", CalculationErrorCode.INVALID_FACTORIAL)
	assert_error("(-1)!", CalculationErrorCode.INVALID_FACTORIAL)


def test_undefined_and_too_large_expressions_are_rejected():
	assert_error("1/0", CalculationErrorCode.UNDEFINED_RESULT)
	assert_error("2^10001", CalculationErrorCode.EXPONENT_TOO_LARGE)
	assert_error("1001!", CalculationErrorCode.FACTORIAL_TOO_LARGE)
	assert_error("1" * 501, CalculationErrorCode.EXPRESSION_TOO_LONG)
