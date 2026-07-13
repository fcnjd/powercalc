"""Safe expression parsing and evaluation for Powercalc."""

from __future__ import annotations

import ast
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

import sympy as sp


AngleUnit = Literal["radian", "degree", "gradian"]
DecimalSeparator = Literal["point", "comma"]
LogMode = Literal["calculator", "natural"]
NumberDomain = Literal["complex", "real"]

MAX_EXPRESSION_LENGTH = 500
MAX_AST_NODES = 100
MAX_AST_DEPTH = 40
MAX_POWER_EXPONENT = 10000
MAX_FACTORIAL_INPUT = 1000


class CalculationErrorCode(StrEnum):
	"""Stable machine-readable calculation error codes.

	The enum values are English string identifiers intended for tests, GUI
	mapping, logging, and future localization. User-facing layers should branch
	on this enum instead of parsing the default English error message.
	"""

	EMPTY_EXPRESSION = "EMPTY_EXPRESSION"
	EXPRESSION_TOO_LONG = "EXPRESSION_TOO_LONG"
	EXPRESSION_TOO_COMPLEX = "EXPRESSION_TOO_COMPLEX"
	EXPRESSION_TOO_DEEP = "EXPRESSION_TOO_DEEP"
	INVALID_EXPRESSION = "INVALID_EXPRESSION"
	INVALID_OPTION = "INVALID_OPTION"
	INVALID_SEPARATOR = "INVALID_SEPARATOR"
	INVALID_ARGUMENT_COUNT = "INVALID_ARGUMENT_COUNT"
	UNKNOWN_NAME = "UNKNOWN_NAME"
	UNKNOWN_FUNCTION = "UNKNOWN_FUNCTION"
	UNSUPPORTED_SYNTAX = "UNSUPPORTED_SYNTAX"
	UNSUPPORTED_OPERATOR = "UNSUPPORTED_OPERATOR"
	UNSUPPORTED_LITERAL = "UNSUPPORTED_LITERAL"
	MALFORMED_FACTORIAL = "MALFORMED_FACTORIAL"
	INVALID_FACTORIAL = "INVALID_FACTORIAL"
	FACTORIAL_TOO_LARGE = "FACTORIAL_TOO_LARGE"
	EXPONENT_TOO_LARGE = "EXPONENT_TOO_LARGE"
	UNDEFINED_RESULT = "UNDEFINED_RESULT"
	NON_REAL_RESULT = "NON_REAL_RESULT"


@dataclass(frozen=True)
class EvaluationOptions:
	"""Options controlling expression evaluation.

	Attributes:
		decimal_precision: Number of significant digits used for
			``CalculationResult.decimal_text``. The default is 12.
		decimal_separator: ``"point"`` uses a decimal point and commas
			between function arguments. ``"comma"`` uses a decimal comma
			and semicolons between function arguments. The setting also
			controls the notation of the result text fields.
		number_domain: ``"complex"`` allows complex results; ``"real"``
			rejects non-real results with ``NON_REAL_RESULT``. The default is
			``"complex"``.
		log_mode: ``"calculator"`` makes ``log(x)`` base 10; ``"natural"``
			makes ``log(x)`` natural. ``ln(x)`` is always natural and
			``log(x, base)`` always uses the explicit base.
		angle_unit: ``"radian"``, ``"degree"``, or ``"gradian"``. The default
			is ``"radian"``. The setting applies only to trigonometric and
			inverse trigonometric functions.
	"""

	decimal_precision: int = 12
	decimal_separator: DecimalSeparator = "point"
	number_domain: NumberDomain = "complex"
	log_mode: LogMode = "calculator"
	angle_unit: AngleUnit = "radian"


@dataclass(frozen=True)
class CalculationError:
	"""Calculation failure details.

	Attributes:
		code: Stable machine-readable error code for branching, testing, and
			future localization.
		message: English default message suitable for early UI display.
		position: Optional zero-based character offset when a useful source
			position is available.
	"""

	code: CalculationErrorCode
	message: str
	position: int | None = None


@dataclass(frozen=True)
class CalculationResult:
	"""Successful calculation result.

	Attributes:
		input_text: Original input string passed to ``calculate``.
		normalized_text: Parser-normalized form using the selected notation,
			for diagnostics only.
		exact_text: Exact mathematical text after simplification using the
			selected notation. Use ``str(value)`` for canonical SymPy text.
		decimal_text: Decimal approximation using the selected precision.
			The text uses the selected notation.
		value: Public SymPy expression for tests and future advanced features.
	"""

	input_text: str
	normalized_text: str
	exact_text: str
	decimal_text: str
	value: sp.Expr


@dataclass(frozen=True, init=False)
class CalculationOutcome:
	"""Calculation outcome containing either a result or an error.

	Use ``CalculationOutcome.success(result)`` and
	``CalculationOutcome.failure(error)`` to construct instances. Direct
	construction is intentionally unsupported so the ``ok``, ``result``, and
	``error`` invariants remain stable for GUI and service code.
	"""

	ok: bool
	result: CalculationResult | None = None
	error: CalculationError | None = None

	def __init__(self, *args: object, **kwargs: object) -> None:
		raise TypeError(
			"Use CalculationOutcome.success() or CalculationOutcome.failure()."
		)

	@classmethod
	def success(cls, result: CalculationResult) -> CalculationOutcome:
		"""Create a successful outcome with a result and no error."""

		return cls._create(ok=True, result=result, error=None)

	@classmethod
	def failure(cls, error: CalculationError) -> CalculationOutcome:
		"""Create a failed outcome with an error and no result."""

		return cls._create(ok=False, result=None, error=error)

	@classmethod
	def _create(
		cls,
		*,
		ok: bool,
		result: CalculationResult | None,
		error: CalculationError | None,
	) -> CalculationOutcome:
		if ok:
			if result is None or error is not None:
				raise ValueError("Successful outcomes require only a result.")
		elif error is None or result is not None:
			raise ValueError("Failed outcomes require only an error.")

		outcome = cls.__new__(cls)
		object.__setattr__(outcome, "ok", ok)
		object.__setattr__(outcome, "result", result)
		object.__setattr__(outcome, "error", error)
		return outcome


class ExpressionError(Exception):
	"""Internal parser/evaluator error converted to CalculationError."""

	def __init__(
		self,
		code: CalculationErrorCode,
		message: str,
		position: int | None = None,
	) -> None:
		super().__init__(message)
		self.error = CalculationError(code, message, position)


def calculate(
	expression: str,
	options: EvaluationOptions | None = None,
) -> CalculationOutcome:
	"""Parse and evaluate a mathematical expression safely.

	The input is parsed with Python's AST module and then converted through a
	strict whitelist of supported nodes, operators, constants, and functions.
	The function does not call Python ``eval`` and does not use SymPy string
	parsers for user input.

	Returns:
		A successful ``CalculationOutcome`` with exact and decimal result text,
		or a failed ``CalculationOutcome`` containing a ``CalculationError``.
		This function never raises parser errors for normal invalid user input.
	"""

	options = options or EvaluationOptions()

	try:
		_validate_options(options)
		canonical_normalized = _normalize_expression(expression, options)
		parsed = ast.parse(canonical_normalized, mode="eval")
		_check_ast_limits(parsed)
		context = _EvaluationContext(options)
		value = context.convert(parsed.body)
		value = sp.simplify(value)
		_validate_result(value, options)
		result = CalculationResult(
			input_text=expression,
			normalized_text=_localize_expression_text(
				canonical_normalized,
				options.decimal_separator,
			),
			exact_text=_localize_expression_text(
				str(value),
				options.decimal_separator,
			),
			decimal_text=_localize_expression_text(
				str(sp.N(value, options.decimal_precision)),
				options.decimal_separator,
			),
			value=value,
		)
		return CalculationOutcome.success(result)
	except ExpressionError as exc:
		return CalculationOutcome.failure(exc.error)
	except (SyntaxError, ValueError, TypeError, RecursionError) as exc:
		return CalculationOutcome.failure(
			CalculationError(
				CalculationErrorCode.INVALID_EXPRESSION,
				f"Invalid expression: {exc}",
			)
		)


def _validate_options(options: EvaluationOptions) -> None:
	if options.decimal_precision < 1:
		raise ExpressionError(
			CalculationErrorCode.INVALID_OPTION,
			"Decimal precision must be at least 1.",
		)
	if options.decimal_separator not in {"point", "comma"}:
		raise ExpressionError(
			CalculationErrorCode.INVALID_OPTION,
			"Unknown decimal separator.",
		)
	if options.number_domain not in {"complex", "real"}:
		raise ExpressionError(
			CalculationErrorCode.INVALID_OPTION,
			"Unknown number domain.",
		)
	if options.log_mode not in {"calculator", "natural"}:
		raise ExpressionError(
			CalculationErrorCode.INVALID_OPTION,
			"Unknown log mode.",
		)
	if options.angle_unit not in {"radian", "degree", "gradian"}:
		raise ExpressionError(
			CalculationErrorCode.INVALID_OPTION,
			"Unknown angle unit.",
		)


def _normalize_expression(
	expression: str,
	options: EvaluationOptions,
) -> str:
	source = expression.strip()
	if not source:
		raise ExpressionError(
			CalculationErrorCode.EMPTY_EXPRESSION,
			"Expression is empty.",
		)
	if len(source) > MAX_EXPRESSION_LENGTH:
		raise ExpressionError(
			CalculationErrorCode.EXPRESSION_TOO_LONG,
			"Expression is too long.",
		)

	source = _normalize_expression_separators(
		source,
		options.decimal_separator,
	)
	source = source.replace("^", "**")
	source = _replace_factorials(source)

	if "!" in source:
		raise ExpressionError(
			CalculationErrorCode.UNSUPPORTED_OPERATOR,
			"The factorial operator is malformed.",
		)

	return source


def _normalize_expression_separators(
	source: str,
	decimal_separator: DecimalSeparator,
) -> str:
	if decimal_separator == "point":
		return source.replace(";", ",")

	characters: list[str] = []
	for index, character in enumerate(source):
		previous = source[index - 1] if index > 0 else ""
		following = source[index + 1] if index + 1 < len(source) else ""

		if character == ",":
			if previous.isdigit() and following.isdigit():
				characters.append(".")
				continue
			raise ExpressionError(
				CalculationErrorCode.INVALID_SEPARATOR,
				(
					"Use a semicolon to separate function arguments "
					"when decimal comma is selected."
				),
				index,
			)
		if character == "." and (previous.isdigit() or following.isdigit()):
			raise ExpressionError(
				CalculationErrorCode.INVALID_SEPARATOR,
				"Use a comma as the decimal separator.",
				index,
			)
		characters.append("," if character == ";" else character)

	return "".join(characters)


def _localize_expression_text(
	text: str,
	decimal_separator: DecimalSeparator,
) -> str:
	if decimal_separator == "point":
		return text

	characters: list[str] = []
	for index, character in enumerate(text):
		previous = text[index - 1] if index > 0 else ""
		following = text[index + 1] if index + 1 < len(text) else ""
		if character == "." and (previous.isdigit() or following.isdigit()):
			characters.append(",")
		elif character == ",":
			characters.append(";")
		else:
			characters.append(character)
	return "".join(characters)


def _replace_factorials(source: str) -> str:
	while True:
		position = source.find("!")
		if position == -1:
			return source
		if position + 1 < len(source) and source[position + 1] == "=":
			raise ExpressionError(
				CalculationErrorCode.UNSUPPORTED_OPERATOR,
				"The != operator is not supported.",
				position,
			)

		operand_end = position
		cursor = position - 1
		while cursor >= 0 and source[cursor].isspace():
			cursor -= 1
		if cursor < 0:
			raise ExpressionError(
				CalculationErrorCode.MALFORMED_FACTORIAL,
				"Factorial requires a preceding value.",
				position,
			)

		operand_start = _find_factorial_operand_start(source, cursor)
		operand = source[operand_start:operand_end].rstrip()
		if not operand:
			raise ExpressionError(
				CalculationErrorCode.MALFORMED_FACTORIAL,
				"Factorial requires a preceding value.",
				position,
			)

		source = (
			source[:operand_start]
			+ f"factorial({operand})"
			+ source[position + 1 :]
		)


def _find_factorial_operand_start(source: str, operand_end: int) -> int:
	if source[operand_end] == ")":
		open_index = _find_matching_open_parenthesis(source, operand_end)
		name_start = _find_call_name_start(source, open_index)
		return name_start if name_start is not None else open_index

	cursor = operand_end
	while cursor >= 0 and (
		source[cursor].isalnum() or source[cursor] in {"_", "."}
	):
		cursor -= 1
	return cursor + 1


def _find_matching_open_parenthesis(source: str, close_index: int) -> int:
	depth = 0
	for index in range(close_index, -1, -1):
		character = source[index]
		if character == ")":
			depth += 1
		elif character == "(":
			depth -= 1
			if depth == 0:
				return index
	raise ExpressionError(
		CalculationErrorCode.MALFORMED_FACTORIAL,
		"Factorial operand has unmatched parentheses.",
		close_index,
	)


def _find_call_name_start(source: str, open_index: int) -> int | None:
	cursor = open_index - 1
	while cursor >= 0 and source[cursor].isspace():
		cursor -= 1
	if cursor < 0 or not (source[cursor].isalpha() or source[cursor] == "_"):
		return None

	while cursor >= 0 and (source[cursor].isalnum() or source[cursor] == "_"):
		cursor -= 1
	return cursor + 1


def _check_ast_limits(node: ast.AST) -> None:
	node_count = 0
	stack: list[tuple[ast.AST, int]] = [(node, 1)]

	while stack:
		current, depth = stack.pop()
		node_count += 1
		if node_count > MAX_AST_NODES:
			raise ExpressionError(
				CalculationErrorCode.EXPRESSION_TOO_COMPLEX,
				"Expression contains too many parts.",
			)
		if depth > MAX_AST_DEPTH:
			raise ExpressionError(
				CalculationErrorCode.EXPRESSION_TOO_DEEP,
				"Expression nesting is too deep.",
			)
		for child in ast.iter_child_nodes(current):
			stack.append((child, depth + 1))


def _validate_result(value: sp.Expr, options: EvaluationOptions) -> None:
	if value.has(sp.zoo, sp.nan):
		raise ExpressionError(
			CalculationErrorCode.UNDEFINED_RESULT,
			"Expression result is undefined.",
		)
	if options.number_domain == "real" and value.is_real is not True:
		raise ExpressionError(
			CalculationErrorCode.NON_REAL_RESULT,
			"Expression result is not real.",
		)


class _EvaluationContext:
	def __init__(self, options: EvaluationOptions) -> None:
		self.options = options
		self.constants: dict[str, sp.Expr] = {
			"pi": sp.pi,
			"e": sp.E,
			"tau": 2 * sp.pi,
			"oo": sp.oo,
			"i": sp.I,
			"I": sp.I,
		}

	def convert(self, node: ast.AST) -> sp.Expr:
		match node:
			case ast.BinOp():
				return self._convert_bin_op(node)
			case ast.UnaryOp():
				return self._convert_unary_op(node)
			case ast.Call():
				return self._convert_call(node)
			case ast.Name():
				return self._convert_name(node)
			case ast.Constant():
				return self._convert_constant(node)
			case _:
				raise ExpressionError(
					CalculationErrorCode.UNSUPPORTED_SYNTAX,
					f"Unsupported syntax: {type(node).__name__}.",
					getattr(node, "col_offset", None),
				)

	def _convert_bin_op(self, node: ast.BinOp) -> sp.Expr:
		left = self.convert(node.left)
		right = self.convert(node.right)

		match node.op:
			case ast.Add():
				return left + right
			case ast.Sub():
				return left - right
			case ast.Mult():
				return left * right
			case ast.Div():
				return left / right
			case ast.Mod():
				return sp.Mod(left, right)
			case ast.Pow():
				self._check_power_exponent(right, node)
				return left**right
			case _:
				raise ExpressionError(
					CalculationErrorCode.UNSUPPORTED_OPERATOR,
					f"Unsupported operator: {type(node.op).__name__}.",
					getattr(node, "col_offset", None),
				)

	def _convert_unary_op(self, node: ast.UnaryOp) -> sp.Expr:
		operand = self.convert(node.operand)

		match node.op:
			case ast.UAdd():
				return operand
			case ast.USub():
				return -operand
			case _:
				raise ExpressionError(
					CalculationErrorCode.UNSUPPORTED_OPERATOR,
					f"Unsupported unary operator: {type(node.op).__name__}.",
					getattr(node, "col_offset", None),
				)

	def _convert_call(self, node: ast.Call) -> sp.Expr:
		if node.keywords:
			raise ExpressionError(
				CalculationErrorCode.UNSUPPORTED_SYNTAX,
				"Function keyword arguments are not supported.",
				getattr(node, "col_offset", None),
			)
		if not isinstance(node.func, ast.Name):
			raise ExpressionError(
				CalculationErrorCode.UNSUPPORTED_SYNTAX,
				"Only named functions are supported.",
				getattr(node, "col_offset", None),
			)

		function_name = node.func.id
		args = [self.convert(arg) for arg in node.args]
		return self._call_function(function_name, args, node)

	def _convert_name(self, node: ast.Name) -> sp.Expr:
		try:
			return self.constants[node.id]
		except KeyError as exc:
			raise ExpressionError(
				CalculationErrorCode.UNKNOWN_NAME,
				f"Unknown name: {node.id}.",
				getattr(node, "col_offset", None),
			) from exc

	def _convert_constant(self, node: ast.Constant) -> sp.Expr:
		value = node.value
		if isinstance(value, bool):
			raise ExpressionError(
				CalculationErrorCode.UNSUPPORTED_LITERAL,
				"Boolean literals are not supported.",
				getattr(node, "col_offset", None),
			)
		if isinstance(value, int):
			return sp.Integer(value)
		if isinstance(value, float):
			return sp.Float(repr(value))
		raise ExpressionError(
			CalculationErrorCode.UNSUPPORTED_LITERAL,
			f"Unsupported literal: {type(value).__name__}.",
			getattr(node, "col_offset", None),
		)

	def _call_function(
		self,
		name: str,
		args: list[sp.Expr],
		node: ast.Call,
	) -> sp.Expr:
		if name in {"sin", "cos", "tan"}:
			self._require_arity(name, args, 1, node)
			return _trig_function(name)(self._angle_to_radian(args[0]))
		if name in {"asin", "acos", "atan"}:
			self._require_arity(name, args, 1, node)
			result = _inverse_trig_function(name)(args[0])
			return self._angle_from_radian(result)
		if name == "log":
			return self._call_log(args, node)
		if name == "ln":
			self._require_arity(name, args, 1, node)
			return sp.log(args[0])
		if name == "log10":
			self._require_arity(name, args, 1, node)
			return sp.log(args[0], 10)
		if name == "factorial":
			self._require_arity(name, args, 1, node)
			return _factorial(args[0], getattr(node, "col_offset", None))
		if name in _SINGLE_ARGUMENT_FUNCTIONS:
			self._require_arity(name, args, 1, node)
			return _SINGLE_ARGUMENT_FUNCTIONS[name](args[0])
		if name == "min":
			self._require_at_least_one_arg(name, args, node)
			return sp.Min(*args)
		if name == "max":
			self._require_at_least_one_arg(name, args, node)
			return sp.Max(*args)

		raise ExpressionError(
			CalculationErrorCode.UNKNOWN_FUNCTION,
			f"Unknown function: {name}.",
			getattr(node, "col_offset", None),
		)

	def _call_log(self, args: list[sp.Expr], node: ast.Call) -> sp.Expr:
		if len(args) == 1:
			if self.options.log_mode == "calculator":
				return sp.log(args[0], 10)
			return sp.log(args[0])
		if len(args) == 2:
			return sp.log(args[0], args[1])
		raise ExpressionError(
			CalculationErrorCode.INVALID_ARGUMENT_COUNT,
			"log expects 1 or 2 arguments.",
			getattr(node, "col_offset", None),
		)

	def _angle_to_radian(self, value: sp.Expr) -> sp.Expr:
		if self.options.angle_unit == "degree":
			return value * sp.pi / 180
		if self.options.angle_unit == "gradian":
			return value * sp.pi / 200
		return value

	def _angle_from_radian(self, value: sp.Expr) -> sp.Expr:
		if self.options.angle_unit == "degree":
			return value * 180 / sp.pi
		if self.options.angle_unit == "gradian":
			return value * 200 / sp.pi
		return value

	def _require_arity(
		self,
		name: str,
		args: list[sp.Expr],
		expected: int,
		node: ast.Call,
	) -> None:
		if len(args) != expected:
			raise ExpressionError(
				CalculationErrorCode.INVALID_ARGUMENT_COUNT,
				f"{name} expects {expected} argument.",
				getattr(node, "col_offset", None),
			)

	def _require_at_least_one_arg(
		self,
		name: str,
		args: list[sp.Expr],
		node: ast.Call,
	) -> None:
		if not args:
			raise ExpressionError(
				CalculationErrorCode.INVALID_ARGUMENT_COUNT,
				f"{name} expects at least 1 argument.",
				getattr(node, "col_offset", None),
			)

	def _check_power_exponent(self, exponent: sp.Expr, node: ast.BinOp) -> None:
		if exponent.is_integer is True and exponent.is_number:
			if abs(int(exponent)) > MAX_POWER_EXPONENT:
				raise ExpressionError(
					CalculationErrorCode.EXPONENT_TOO_LARGE,
					"Exponent is too large.",
					getattr(node, "col_offset", None),
				)


def _trig_function(name: str) -> Callable[[sp.Expr], sp.Expr]:
	return {"sin": sp.sin, "cos": sp.cos, "tan": sp.tan}[name]


def _inverse_trig_function(name: str) -> Callable[[sp.Expr], sp.Expr]:
	return {"asin": sp.asin, "acos": sp.acos, "atan": sp.atan}[name]


def _factorial(value: sp.Expr, position: int | None) -> sp.Expr:
	if value.is_integer is not True or value.is_nonnegative is not True:
		raise ExpressionError(
			CalculationErrorCode.INVALID_FACTORIAL,
			"Factorial requires a non-negative integer.",
			position,
		)
	if value.is_number and int(value) > MAX_FACTORIAL_INPUT:
		raise ExpressionError(
			CalculationErrorCode.FACTORIAL_TOO_LARGE,
			"Factorial input is too large.",
			position,
		)
	return sp.factorial(value)


_SINGLE_ARGUMENT_FUNCTIONS: dict[str, Callable[[sp.Expr], sp.Expr]] = {
	"sqrt": sp.sqrt,
	"exp": sp.exp,
	"abs": sp.Abs,
	"floor": sp.floor,
	"ceil": sp.ceiling,
	"gamma": sp.gamma,
	"re": sp.re,
	"im": sp.im,
	"sign": sp.sign,
	"sinh": sp.sinh,
	"cosh": sp.cosh,
	"tanh": sp.tanh,
}
