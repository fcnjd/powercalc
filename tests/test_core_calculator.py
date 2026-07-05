import sympy as sp

from powercalc.core import EvaluationOptions, calculate


def assert_ok(expression, options=None):
	outcome = calculate(expression, options)
	assert outcome.ok, outcome.error
	assert outcome.result is not None
	return outcome.result


def assert_error(expression, code=None, options=None):
	outcome = calculate(expression, options)
	assert not outcome.ok
	assert outcome.error is not None
	if code is not None:
		assert outcome.error.code == code
	return outcome.error


def assert_same_value(actual, expected):
	assert sp.simplify(actual - expected) == 0


def test_basic_arithmetic_and_power():
	assert_same_value(assert_ok("2+3*4").value, sp.Integer(14))
	assert_same_value(assert_ok("(1+2)^3").value, sp.Integer(27))
	assert_same_value(assert_ok("2**3").value, sp.Integer(8))


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

	assert_error("sqrt(-1)", "NON_REAL_RESULT", options)


def test_unknown_names_and_functions_are_rejected():
	assert_error("x + 1", "UNKNOWN_NAME")
	assert_error("foo(1)", "UNKNOWN_FUNCTION")


def test_unsafe_or_unsupported_syntax_is_rejected():
	assert_error("__import__('os')", "UNSUPPORTED_LITERAL")
	assert_error("(1).__class__", "UNSUPPORTED_SYNTAX")
	assert_error("[1, 2, 3]", "UNSUPPORTED_SYNTAX")
	assert_error("sin(90 deg)", "INVALID_EXPRESSION")


def test_invalid_argument_counts_are_rejected():
	assert_error("sin(1, 2)", "INVALID_ARGUMENT_COUNT")
	assert_error("min()", "INVALID_ARGUMENT_COUNT")
	assert_error("log(1, 2, 3)", "INVALID_ARGUMENT_COUNT")


def test_invalid_factorial_is_rejected():
	assert_error("2.5!", "INVALID_FACTORIAL")
	assert_error("(-1)!", "INVALID_FACTORIAL")


def test_undefined_and_too_large_expressions_are_rejected():
	assert_error("1/0", "UNDEFINED_RESULT")
	assert_error("2^10001", "EXPONENT_TOO_LARGE")
	assert_error("1001!", "FACTORIAL_TOO_LARGE")
	assert_error("1" * 501, "EXPRESSION_TOO_LONG")
