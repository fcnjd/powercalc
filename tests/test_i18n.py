from __future__ import annotations

import pytest

from powercalc.i18n import (
	install_default_translation,
	install_translation,
	resolve_startup_language,
)


@pytest.fixture(autouse=True)
def _restore_default_translation():
	# install_translation mutates the global `_` in builtins; reset it after
	# each test so other test modules always see the English passthrough.
	yield
	install_default_translation()


def test_resolve_startup_language_passes_through_explicit_choices():
	assert resolve_startup_language("en") == "en"
	assert resolve_startup_language("de") == "de"


def test_resolve_startup_language_system_and_unknown_fall_back_to_supported():
	assert resolve_startup_language("system") in ("en", "de")
	assert resolve_startup_language("klingon") in ("en", "de")


def test_install_translation_never_raises_for_unsupported_language():
	install_translation("xx")
	assert _("Calculate") == "Calculate"


def test_install_translation_loads_the_german_catalog():
	install_translation("de")
	assert _("Calculate") == "Berechnen"


def test_install_translation_english_is_a_passthrough():
	install_translation("en")
	assert _("Calculate") == "Calculate"
