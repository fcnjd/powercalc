"""Formatting helpers for the Powercalc GUI."""

from __future__ import annotations

from powercalc.core import CalculationError, CalculationResult, DecimalSeparator


def format_result_for_display(
	result: CalculationResult,
	decimal_separator: DecimalSeparator = "point",
) -> str:
	"""Return concise result text for the first calculator GUI.

	The core intentionally exposes both exact and decimal text. The first GUI
	increment is decimal-oriented, but strips unnecessary trailing zeroes so
	ordinary integer results are read naturally by screen readers.
	"""

	return _strip_decimal_trailing_zeroes(
		result.decimal_text,
		decimal_separator,
	)


def format_error_for_display(error: CalculationError) -> str:
	"""Return concise user-facing error text."""

	return f"Error: {error.message}"


def _strip_decimal_trailing_zeroes(
	text: str,
	decimal_separator: DecimalSeparator,
) -> str:
	point = "," if decimal_separator == "comma" else "."
	if not _looks_like_plain_decimal(text, point):
		return text
	if point not in text:
		return text

	stripped = text.rstrip("0").rstrip(point)
	if stripped in {"", "-"}:
		return "0"
	return stripped


def _looks_like_plain_decimal(text: str, point: str) -> bool:
	if not text:
		return False
	allowed = "0123456789-" + point
	return all(character in allowed for character in text)
