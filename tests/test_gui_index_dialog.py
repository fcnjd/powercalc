from powercalc.core import CatalogEntry
from powercalc.gui.index_dialog import filter_catalog_entries


def _entry(display_name, function_name, *parameters):
	return CatalogEntry(display_name, function_name, parameters)


def test_filter_matches_case_insensitive_substring_on_display_name():
	entries = [
		_entry("Quadratwurzel von n", "sqrt", "n"),
		_entry("Sinus (aktuelle Winkeleinheit)", "sin", "n"),
	]
	assert [
		e.function_name for e in filter_catalog_entries(entries, "sinus")
	] == [
		"sin",
	]


def test_filter_matches_raw_function_name_even_if_not_in_display_name():
	entries = [
		_entry("Quadratwurzel von n", "sqrt", "n"),
		_entry("Sinus (aktuelle Winkeleinheit)", "sin", "n"),
	]
	assert [
		e.function_name for e in filter_catalog_entries(entries, "sqrt")
	] == [
		"sqrt",
	]


def test_filter_empty_query_returns_all_entries():
	entries = [
		_entry("Quadratwurzel von n", "sqrt", "n"),
		_entry("Sinus (aktuelle Winkeleinheit)", "sin", "n"),
	]
	assert filter_catalog_entries(entries, "") == entries


def test_filter_no_match_returns_empty_list():
	entries = [_entry("Quadratwurzel von n", "sqrt", "n")]
	assert filter_catalog_entries(entries, "zzz") == []
