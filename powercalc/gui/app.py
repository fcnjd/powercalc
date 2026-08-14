"""wxPython application entry point for Powercalc."""

from __future__ import annotations

import wx

from powercalc.gui.main_window import MainFrame
from powercalc.settings import SettingsLoadResult, SettingsStore


_WX_LANGUAGE_BY_CODE = {
	"de": wx.LANGUAGE_GERMAN,
	"en": wx.LANGUAGE_ENGLISH,
}


def run(
	settings_store: SettingsStore,
	loaded_settings: SettingsLoadResult,
	language: str,
) -> int:
	"""Start the Powercalc desktop application.

	``language`` is the already-resolved startup language code (see
	``powercalc.i18n.resolve_startup_language``); ``gettext`` translation
	must already be installed by the caller before this is called.
	"""

	app = wx.App(False)
	# Kept alive on the app object; wx.Locale stops localizing stock
	# control labels (e.g. OK/Cancel) once its instance is garbage collected.
	app.wx_locale = wx.Locale(
		_WX_LANGUAGE_BY_CODE.get(language, wx.LANGUAGE_ENGLISH)
	)
	frame = MainFrame(
		settings=loaded_settings.settings,
		settings_store=settings_store,
		startup_warning=loaded_settings.warning,
	)
	frame.Show()
	return app.MainLoop()
