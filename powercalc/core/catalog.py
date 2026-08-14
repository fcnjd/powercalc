"""Declarative catalog of callable functions and constants."""

from __future__ import annotations

from dataclasses import dataclass

from powercalc.core.calculator import DecimalSeparator


@dataclass(frozen=True)
class CatalogEntry:
	"""One function or constant offered by the function/constant index.

	``parameters`` holds the argument names shown to the user, e.g.
	``("n",)`` for ``sqrt`` or ``("n", "a")`` for ``log``. An empty tuple
	marks a constant, inserted as bare text with no parentheses.
	"""

	display_name: str
	function_name: str
	parameters: tuple[str, ...]


def build_insertion(
	entry: CatalogEntry, decimal_separator: DecimalSeparator
) -> tuple[str, int, int]:
	"""Return the text to insert and the first placeholder's selection.

	For a function, the returned text is ``"name(arg1; arg2)"`` (using the
	argument separator matching ``decimal_separator``) and the selection
	span covers the first argument name, so it can be typed over
	immediately. For a constant, the selection span is empty and marks
	the caret position at the end of the inserted text.
	"""

	if not entry.parameters:
		text = entry.function_name
		return text, len(text), len(text)

	separator = ", " if decimal_separator == "point" else "; "
	arguments = separator.join(entry.parameters)
	text = f"{entry.function_name}({arguments})"
	start = len(entry.function_name) + 1
	end = start + len(entry.parameters[0])
	return text, start, end


def _function(
	display_name: str, function_name: str, *parameters: str
) -> CatalogEntry:
	return CatalogEntry(display_name, function_name, parameters)


def _constant(display_name: str, name: str) -> CatalogEntry:
	return CatalogEntry(display_name, name, ())


_ENTRIES = [
	_function(_("Absolute value of n"), "abs", "n"),
	_function(_("Arccosine (current angle unit)"), "acos", "n"),
	_function(_("Arcsine (current angle unit)"), "asin", "n"),
	_function(_("Arctangent (current angle unit)"), "atan", "n"),
	_constant(_("Circle constant pi"), "pi"),
	_function(_("Cosine (current angle unit)"), "cos", "n"),
	_constant(_("Euler's number e"), "e"),
	_function(_("Exponential function e to the power of n"), "exp", "n"),
	_function(_("Factorial of n"), "factorial", "n"),
	_function(_("Gamma function of n"), "gamma", "n"),
	_function(_("Hyperbolic cosine of n"), "cosh", "n"),
	_function(_("Hyperbolic sine of n"), "sinh", "n"),
	_function(_("Hyperbolic tangent of n"), "tanh", "n"),
	_function(_("Imaginary part of n"), "im", "n"),
	_constant(_("Imaginary unit i"), "i"),
	_constant(_("Infinity"), "oo"),
	_function(_("Largest of several values"), "max", "n", "m"),
	_function(_("Logarithm of n to base 10"), "log10", "n"),
	_function(_("Logarithm of n to base a"), "log", "n", "a"),
	_function(_("Logarithm of n, natural (base e)"), "ln", "n"),
	_function(_("Real part of n"), "re", "n"),
	_function(_("Round n down to the nearest integer"), "floor", "n"),
	_function(_("Round n up to the nearest integer"), "ceil", "n"),
	_function(_("Sign of n"), "sign", "n"),
	_function(_("Sine (current angle unit)"), "sin", "n"),
	_function(_("Smallest of several values"), "min", "n", "m"),
	_function(_("Square root of n"), "sqrt", "n"),
	_function(_("Tangent (current angle unit)"), "tan", "n"),
	_constant(_("Tau (2π)"), "tau"),
]

FUNCTION_CATALOG: tuple[CatalogEntry, ...] = tuple(
	sorted(_ENTRIES, key=lambda entry: entry.display_name.casefold())
)
