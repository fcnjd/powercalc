"""wxPython application entry point for Powercalc."""

from __future__ import annotations

import wx

from powercalc.gui.main_window import MainFrame


def run() -> int:
	"""Start the Powercalc desktop application."""

	app = wx.App(False)
	frame = MainFrame()
	frame.Show()
	return app.MainLoop()
