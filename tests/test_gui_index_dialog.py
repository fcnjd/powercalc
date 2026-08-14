from powercalc.core import CatalogEntry
from powercalc.gui.index_dialog import filter_catalog_entries


def _entry(display_name, function_name, *parameters):
	return CatalogEntry(display_name, function_name, parameters)


def test_filter_matches_case_insensitive_substring_on_display_name():
	entries = [
		_entry("Square root of n", "sqrt", "n"),
		_entry("Sine (current angle unit)", "sin", "n"),
	]
	assert [
		e.function_name for e in filter_catalog_entries(entries, "sine")
	] == [
		"sin",
	]


def test_filter_matches_raw_function_name_even_if_not_in_display_name():
	entries = [
		_entry("Square root of n", "sqrt", "n"),
		_entry("Sine (current angle unit)", "sin", "n"),
	]
	assert [
		e.function_name for e in filter_catalog_entries(entries, "sqrt")
	] == [
		"sqrt",
	]


def test_filter_empty_query_returns_all_entries():
	entries = [
		_entry("Square root of n", "sqrt", "n"),
		_entry("Sine (current angle unit)", "sin", "n"),
	]
	assert filter_catalog_entries(entries, "") == entries


def test_filter_no_match_returns_empty_list():
	entries = [_entry("Square root of n", "sqrt", "n")]
	assert filter_catalog_entries(entries, "zzz") == []
