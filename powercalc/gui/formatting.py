"""Formatting helpers for the Powercalc GUI."""

from __future__ import annotations

from powercalc.core import CalculationError, CalculationResult


def format_result_for_display(result: CalculationResult) -> str:
	"""Return concise result text for the first calculator GUI.

	The core intentionally exposes both exact and decimal text. The first GUI
	increment is decimal-oriented, but strips unnecessary trailing zeroes so
	ordinary integer results are read naturally by screen readers.
	"""

	if result.value.is_integer is True and result.value.is_number:
		return _strip_decimal_trailing_zeroes(result.decimal_text)
	return _strip_decimal_trailing_zeroes(result.decimal_text)


def format_error_for_display(error: CalculationError) -> str:
	"""Return concise user-facing error text."""

	return f"Error: {error.message}"


def _strip_decimal_trailing_zeroes(text: str) -> str:
	if not _looks_like_plain_decimal(text):
		return text
	if "." not in text:
		return text

	stripped = text.rstrip("0").rstrip(".")
	if stripped in {"", "-"}:
		return "0"
	return stripped


def _looks_like_plain_decimal(text: str) -> bool:
	if not text:
		return False
	return all(character in "0123456789.-" for character in text)
