import pytest

from powercalc.core import FUNCTION_CATALOG, build_insertion, calculate


def _round_trip_expression(entry):
	if not entry.parameters:
		return entry.function_name
	arguments = ", ".join("2" for _ in entry.parameters)
	return f"{entry.function_name}({arguments})"


def test_catalog_has_no_duplicate_display_names():
	names = [entry.display_name for entry in FUNCTION_CATALOG]
	assert len(names) == len(set(names))


def test_catalog_is_sorted_alphabetically_by_display_name():
	names = [entry.display_name for entry in FUNCTION_CATALOG]
	assert names == sorted(names, key=str.casefold)


@pytest.mark.parametrize(
	"entry", FUNCTION_CATALOG, ids=lambda entry: entry.function_name
)
def test_catalog_entry_round_trips_through_calculate(entry):
	outcome = calculate(_round_trip_expression(entry))
	assert outcome.ok, outcome.error


def test_build_insertion_for_constant_has_no_selection():
	pi_entry = next(e for e in FUNCTION_CATALOG if e.function_name == "pi")
	text, start, end = build_insertion(pi_entry, "point")
	assert text == "pi"
	assert start == end == 2


def test_build_insertion_uses_comma_between_arguments_in_point_mode():
	log_entry = next(e for e in FUNCTION_CATALOG if e.function_name == "log")
	text, start, end = build_insertion(log_entry, "point")
	assert text == "log(n, a)"
	assert (start, end) == (4, 5)


def test_build_insertion_uses_semicolon_between_arguments_in_comma_mode():
	log_entry = next(e for e in FUNCTION_CATALOG if e.function_name == "log")
	text, start, end = build_insertion(log_entry, "comma")
	assert text == "log(n; a)"
	assert (start, end) == (4, 5)


def test_build_insertion_selects_the_first_argument_name():
	sqrt_entry = next(e for e in FUNCTION_CATALOG if e.function_name == "sqrt")
	text, start, end = build_insertion(sqrt_entry, "point")
	assert text == "sqrt(n)"
	assert text[start:end] == "n"
