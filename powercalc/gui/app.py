"""wxPython application entry point for Powercalc."""

from __future__ import annotations

import wx

from powercalc.gui.main_window import MainFrame
from powercalc.settings import SettingsStore


def run() -> int:
	"""Start the Powercalc desktop application."""

	app = wx.App(False)
	settings_store = SettingsStore()
	loaded_settings = settings_store.load()
	frame = MainFrame(
		settings=loaded_settings.settings,
		settings_store=settings_store,
		startup_warning=loaded_settings.warning,
	)
	frame.Show()
	return app.MainLoop()
