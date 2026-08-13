"""Declarative catalog of callable functions and constants."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogEntry:
	"""One function or constant offered by the function/constant index.

	``cursor_offset`` is the caret position after insertion, measured in
	characters from the start of ``insert_text``: right after the opening
	parenthesis for functions, or at the end of the text for constants.
	"""

	name: str
	insert_text: str
	cursor_offset: int


def _function(name: str) -> CatalogEntry:
	return CatalogEntry(name, f"{name}()", len(name) + 1)


def _constant(name: str) -> CatalogEntry:
	return CatalogEntry(name, name, len(name))


_ENTRIES = [
	_function("abs"),
	_function("acos"),
	_function("asin"),
	_function("atan"),
	_function("ceil"),
	_function("cos"),
	_function("cosh"),
	_constant("e"),
	_function("exp"),
	_function("factorial"),
	_function("floor"),
	_function("gamma"),
	_constant("i"),
	_function("im"),
	_function("ln"),
	_function("log"),
	_function("log10"),
	_function("max"),
	_function("min"),
	_constant("oo"),
	_constant("pi"),
	_function("re"),
	_function("sign"),
	_function("sin"),
	_function("sinh"),
	_function("sqrt"),
	_function("tan"),
	_function("tanh"),
	_constant("tau"),
]

FUNCTION_CATALOG: tuple[CatalogEntry, ...] = tuple(
	sorted(_ENTRIES, key=lambda entry: entry.name.casefold())
)
