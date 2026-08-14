"""gettext-based translation setup for Powercalc.

``_`` is installed globally into ``builtins`` so translatable strings can be
marked as ``_("...")`` anywhere in the codebase without a per-module import.
``install_default_translation`` runs as a side effect of importing the
top-level ``powercalc`` package, which guarantees ``_`` exists in builtins
before any submodule (in particular ``powercalc.core.catalog``, which
evaluates translatable strings at import time) is loaded.
"""

from __future__ import annotations

import gettext
from pathlib import Path
import sys


DOMAIN = "powercalc"

_SUPPORTED_LANGUAGES = ("en", "de")


def get_locale_dir() -> Path:
	"""Return the packaged or source-tree locale directory."""

	if getattr(sys, "frozen", False):
		base_path = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
		return base_path / "locale"

	return Path(__file__).resolve().parents[2] / "powercalc" / "locale"


def install_default_translation() -> None:
	"""Install an English passthrough translation as a safety net.

	English is the source language of every ``_()`` call, so no catalog is
	required for it: ``fallback=True`` returns a ``NullTranslations``
	instance that simply returns each message unchanged. This keeps ``_``
	available everywhere, including tests and tools that import
	``powercalc.core`` directly without going through the app entry point.
	"""

	gettext.translation(
		DOMAIN, localedir=get_locale_dir(), languages=["en"], fallback=True
	).install()


def install_translation(language: str) -> None:
	"""Install the translation for ``language``, falling back to English."""

	gettext.translation(
		DOMAIN,
		localedir=get_locale_dir(),
		languages=[language, "en"],
		fallback=True,
	).install()


def resolve_startup_language(setting: str) -> str:
	"""Resolve an ``AppSettings.language`` value to a concrete language code.

	``"en"``/``"de"`` pass through unchanged. ``"system"`` (or any other
	value) is resolved from the OS UI language, falling back to English when
	detection is unavailable or the detected language is not supported.
	"""

	if setting in _SUPPORTED_LANGUAGES:
		return setting
	return _detect_system_language()


def _detect_system_language() -> str:
	try:
		import ctypes
		import locale as locale_module

		kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
		locale_name = locale_module.windows_locale.get(
			kernel32.GetUserDefaultUILanguage()
		)
	except Exception:
		return "en"

	if locale_name and locale_name.startswith("de"):
		return "de"
	return "en"
