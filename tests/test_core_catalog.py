import pytest

from powercalc.core import FUNCTION_CATALOG, calculate


def _expression_for(entry):
	if entry.insert_text.endswith("()"):
		return entry.insert_text[:-1] + "2)"
	return entry.insert_text


def test_catalog_has_no_duplicate_names():
	names = [entry.name for entry in FUNCTION_CATALOG]
	assert len(names) == len(set(names))


def test_catalog_is_sorted_alphabetically():
	names = [entry.name for entry in FUNCTION_CATALOG]
	assert names == sorted(names, key=str.casefold)


@pytest.mark.parametrize(
	"entry", FUNCTION_CATALOG, ids=lambda entry: entry.name
)
def test_catalog_entry_round_trips_through_calculate(entry):
	outcome = calculate(_expression_for(entry))
	assert outcome.ok, outcome.error
