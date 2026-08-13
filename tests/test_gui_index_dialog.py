from powercalc.core import CatalogEntry
from powercalc.gui.index_dialog import filter_catalog_entries


def _entry(name):
	return CatalogEntry(name, f"{name}()", len(name) + 1)


def test_filter_matches_case_insensitive_substring_on_name():
	entries = [_entry("sqrt"), _entry("sin"), _entry("cos")]
	assert [e.name for e in filter_catalog_entries(entries, "SQ")] == [
		"sqrt",
	]


def test_filter_empty_query_returns_all_entries():
	entries = [_entry("sqrt"), _entry("sin")]
	assert filter_catalog_entries(entries, "") == entries


def test_filter_no_match_returns_empty_list():
	assert filter_catalog_entries([_entry("sqrt")], "zzz") == []
