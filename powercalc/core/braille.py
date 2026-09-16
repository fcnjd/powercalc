"""Reliable Braille translation backed by a bundled Liblouis runtime.

This module intentionally exposes only the small forward-translation surface
Powercalc needs.  It does not depend on a similarly named PyPI package: the
Windows runtime is prepared from the official Liblouis release by
``tools.liblouis``.
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import byref, c_char_p, c_int, c_void_p, create_string_buffer
from pathlib import Path

GERMAN_GRADE_1_TABLE = "de-g1.ctb"
"""German Grade 1 table from Liblouis 3.39.0.

The selected table describes German literary Braille and is explicitly
forward-translation-only.  That is suitable for plot labels; Powercalc does
not offer Braille back-translation.
"""


class BrailleTranslationUnavailable(RuntimeError):
	"""Raised when the packaged Liblouis runtime cannot be used."""


def bundled_liblouis_root() -> Path:
	"""Return the directory containing the optional bundled runtime."""

	if getattr(sys, "frozen", False):
		base_path = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
		return base_path / "resources" / "liblouis"
	return Path(__file__).resolve().parents[1] / "resources" / "liblouis"


class LiblouisBrailleTranslator:
	"""Translate text with the verified Liblouis Windows runtime."""

	def __init__(self, runtime_root: Path | None = None) -> None:
		self._runtime_root = runtime_root or bundled_liblouis_root()
		self._library_path = self._runtime_root / "liblouis.dll"
		self._table_path = (
			self._runtime_root
			/ "share"
			/ "liblouis"
			/ "tables"
			/ GERMAN_GRADE_1_TABLE
		)
		self._library = self._load_library()
		self._char_size = self._configure_library()

	def is_available(self) -> bool:
		"""Return whether the runtime was loaded successfully."""

		return True

	def translate(self, text: str) -> str:
		"""Translate text to German Grade 1 Unicode Braille."""

		if not isinstance(text, str):
			raise TypeError("Braille translation input must be text.")
		if not text:
			return ""

		encoding = _wide_char_encoding(self._char_size)
		input_buffer = create_string_buffer(text.encode(encoding))
		input_length = c_int(len(text))
		output_length = c_int(max(16, len(text) * 8))
		output_buffer = create_string_buffer(
			output_length.value * self._char_size
		)

		success = self._library.lou_translateString(
			GERMAN_GRADE_1_TABLE.encode("ascii"),
			input_buffer,
			byref(input_length),
			output_buffer,
			byref(output_length),
			None,
			None,
			0,
		)
		if not success:
			raise BrailleTranslationUnavailable(
				"Liblouis could not translate with the bundled German table."
			)

		return output_buffer.raw[
			: output_length.value * self._char_size
		].decode(encoding)

	def _load_library(self):
		if not self._library_path.is_file():
			raise BrailleTranslationUnavailable(
				"The bundled Liblouis library is unavailable."
			)
		if not self._table_path.is_file():
			raise BrailleTranslationUnavailable(
				"The bundled German Braille table is unavailable."
			)
		try:
			loader = (
				getattr(ctypes, "WinDLL", ctypes.CDLL)
				if sys.platform == "win32"
				else ctypes.CDLL
			)
			return loader(str(self._library_path))
		except OSError as exc:
			raise BrailleTranslationUnavailable(
				"The bundled Liblouis library could not be loaded."
			) from exc

	def _configure_library(self) -> int:
		self._library.lou_charSize.restype = c_int
		self._library.lou_charSize.argtypes = ()
		self._library.lou_setDataPath.restype = c_char_p
		self._library.lou_setDataPath.argtypes = (c_char_p,)
		self._library.lou_translateString.restype = c_int
		self._library.lou_translateString.argtypes = (
			c_char_p,
			c_void_p,
			c_void_p,
			c_void_p,
			c_void_p,
			c_void_p,
			c_void_p,
			c_int,
		)
		char_size = self._library.lou_charSize()
		if char_size not in {2, 4}:
			raise BrailleTranslationUnavailable(
				"The bundled Liblouis library reported an unsupported "
				"character size."
			)
		self._library.lou_setDataPath(
			_encode_path(self._runtime_root / "share")
		)
		return char_size


def _encode_path(path: Path) -> bytes:
	"""Encode a runtime path using the platform filesystem convention."""

	encoding = (
		"mbcs" if sys.platform == "win32" else sys.getfilesystemencoding()
	)
	return str(path).encode(encoding)


def _wide_char_encoding(char_size: int) -> str:
	"""Return the Liblouis wide-character encoding for this runtime."""

	endianness = "le" if sys.byteorder == "little" else "be"
	return f"utf-{char_size * 8}-{endianness}"
