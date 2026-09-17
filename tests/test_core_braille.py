import ctypes
from pathlib import Path

import pytest

from powercalc.core.braille import (
	BrailleTranslationUnavailable,
	LiblouisBrailleTranslator,
	_wide_char_encoding,
)
from tools.braille_smoke import find_runtime_root


def test_translator_reports_missing_bundled_library(tmp_path: Path):
	table_path = tmp_path / "share" / "liblouis" / "tables" / "de-g1.ctb"
	table_path.parent.mkdir(parents=True)
	table_path.write_text("", encoding="utf-8")

	with pytest.raises(
		BrailleTranslationUnavailable, match="library is unavailable"
	):
		LiblouisBrailleTranslator(tmp_path)


def test_translator_reports_missing_german_table(tmp_path: Path):
	(tmp_path / "liblouis.dll").write_bytes(b"not a real DLL")

	with pytest.raises(
		BrailleTranslationUnavailable, match="table is unavailable"
	):
		LiblouisBrailleTranslator(tmp_path)


def test_translator_rejects_non_text_input_before_native_translation(
	tmp_path: Path,
):
	translator = object.__new__(LiblouisBrailleTranslator)

	with pytest.raises(TypeError, match="must be text"):
		translator.translate(42)  # type: ignore[arg-type]


def test_smoke_finds_pyinstaller_internal_data_directory(tmp_path: Path):
	runtime_root = tmp_path / "_internal" / "resources" / "liblouis"
	runtime_root.mkdir(parents=True)

	assert find_runtime_root(tmp_path) == runtime_root


def test_translator_accepts_supported_liblouis_character_width(tmp_path: Path):
	class FakeFunction:
		def __init__(self, result=None):
			self.result = result
			self.calls = []

		def __call__(self, *args):
			self.calls.append(args)
			return self.result

	class FakeLibrary:
		lou_charSize = FakeFunction(4)
		lou_translateString = FakeFunction(1)

	translator = object.__new__(LiblouisBrailleTranslator)
	translator._library = FakeLibrary()
	translator._runtime_root = tmp_path
	translator._tables_path = tmp_path / "share" / "liblouis" / "tables"
	translator._table_path = translator._tables_path / "de-g1.ctb"

	assert translator._configure_library() == 4


def test_wide_char_encoding_supports_liblouis_character_widths():
	assert _wide_char_encoding(2).startswith("utf-16-")
	assert _wide_char_encoding(4).startswith("utf-32-")


def test_translator_uses_bundled_unicode_and_root_table_paths(tmp_path: Path):
	class TranslateFunction:
		def __init__(self):
			self.calls = []

		def __call__(
			self, table, _input, _input_length, _output, output_length, *_
		):
			self.calls.append(table)
			ctypes.cast(output_length, ctypes.POINTER(ctypes.c_int))[0] = 0
			return 1

	translator = object.__new__(LiblouisBrailleTranslator)
	translator._char_size = 2
	translator._table_path = (
		tmp_path / "share" / "liblouis" / "tables" / "de-g1.ctb"
	)
	translator._unicode_display_path = (
		tmp_path / "share" / "liblouis" / "tables" / "unicode.dis"
	)
	translator._library = type("FakeLibrary", (), {})()
	translator._library.lou_translateString = TranslateFunction()

	assert translator.translate("abc") == ""
	assert translator._library.lou_translateString.calls == [
		b",".join(
			(
				str(translator._unicode_display_path).encode("utf-8"),
				str(translator._table_path).encode("utf-8"),
			)
		)
	]
