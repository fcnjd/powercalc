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
	_function("Betrag von n", "abs", "n"),
	_function("Arkuskosinus (aktuelle Winkeleinheit)", "acos", "n"),
	_function("Aufrunden von n zur nächsten ganzen Zahl", "ceil", "n"),
	_function("Arkussinus (aktuelle Winkeleinheit)", "asin", "n"),
	_function("Arkustangens (aktuelle Winkeleinheit)", "atan", "n"),
	_function("Kosinus (aktuelle Winkeleinheit)", "cos", "n"),
	_function("Kosinus hyperbolicus von n", "cosh", "n"),
	_constant("Eulersche Zahl e", "e"),
	_function("Exponentialfunktion e hoch n", "exp", "n"),
	_function("Fakultät von n", "factorial", "n"),
	_function("Abrunden von n zur nächsten ganzen Zahl", "floor", "n"),
	_function("Gammafunktion von n", "gamma", "n"),
	_constant("Imaginäre Einheit i", "i"),
	_function("Imaginärteil von n", "im", "n"),
	_function("Logarithmus von n, natürlich (Basis e)", "ln", "n"),
	_function("Logarithmus von n zur Basis a", "log", "n", "a"),
	_function("Logarithmus von n zur Basis 10", "log10", "n"),
	_function("Größter von mehreren Werten", "max", "n", "m"),
	_function("Kleinster von mehreren Werten", "min", "n", "m"),
	_constant("Unendlich", "oo"),
	_constant("Kreiszahl Pi", "pi"),
	_function("Realteil von n", "re", "n"),
	_function("Vorzeichen von n", "sign", "n"),
	_function("Sinus (aktuelle Winkeleinheit)", "sin", "n"),
	_function("Sinus hyperbolicus von n", "sinh", "n"),
	_function("Quadratwurzel von n", "sqrt", "n"),
	_function("Tangens (aktuelle Winkeleinheit)", "tan", "n"),
	_function("Tangens hyperbolicus von n", "tanh", "n"),
	_constant("Tau (2π)", "tau"),
]

FUNCTION_CATALOG: tuple[CatalogEntry, ...] = tuple(
	sorted(_ENTRIES, key=lambda entry: entry.display_name.casefold())
)
