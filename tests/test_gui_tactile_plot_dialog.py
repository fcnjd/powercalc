"""UI contract checks for the tactile-plot export dialog."""

from __future__ import annotations

import wx

from powercalc.core.tactile_plot import (
	ContentProfile,
	PaperSize,
	PlotFileFormat,
)
from powercalc.gui.tactile_plot_dialog import TactilePlotDialog


def test_dialog_exposes_the_approved_v2_options_and_actions():
	app = wx.App(False)
	dialog = TactilePlotDialog(None, "x^2")
	try:
		request = dialog.get_request()
		assert dialog.GetTitle() == "Export tactile function plot"
		assert dialog.expression_input.GetName() == "Function of x"
		assert dialog.x_min_input.GetName() == "X minimum"
		assert dialog.x_max_input.GetName() == "X maximum"
		assert dialog.title_input.GetName() == "Title"
		assert dialog.profile_choice.GetStrings() == ["Swell paper", "Embosser"]
		assert dialog.paper_size_choice.GetStrings() == [
			"A4 landscape",
			"A4 portrait",
			"A5 landscape",
			"A5 portrait",
		]
		assert dialog.file_format_choice.GetStrings() == ["SVG", "PNG"]
		assert request.content_profile is ContentProfile.SWELL_PAPER
		assert request.paper_size is PaperSize.A4_LANDSCAPE
		assert request.file_format is PlotFileFormat.SVG
		assert dialog.save_button.GetLabel() == "Save plot…"
		assert [
			child.GetLabel()
			for child in dialog.GetChildren()
			if isinstance(child, wx.Button)
		] == ["Save plot…", "Cancel"]
	finally:
		dialog.Destroy()
		app.Destroy()
