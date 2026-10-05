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
		assert dialog.expression_input.GetName() == "f(x)"
		assert dialog.x_min_input.GetName() == "X minimum"
		assert dialog.x_max_input.GetName() == "X maximum"
		assert dialog.title_input.GetName() == "Title"
		assert dialog.profile_choice.GetStrings() == ["Swell paper", "Embosser"]
		assert dialog.paper_size_choice.GetStrings() == [
			"A3 landscape",
			"A3 portrait",
			"A4 landscape",
			"A4 portrait",
			"A5 landscape",
			"A5 portrait",
		]
		assert dialog.file_format_choice.GetStrings() == ["SVG", "PNG"]
		assert request.content_profile is ContentProfile.SWELL_PAPER
		assert request.paper_size is PaperSize.A4_LANDSCAPE
		for label, paper_size in (
			("A3 landscape", PaperSize.A3_LANDSCAPE),
			("A3 portrait", PaperSize.A3_PORTRAIT),
		):
			dialog.paper_size_choice.SetStringSelection(label)
			assert dialog.get_request().paper_size is paper_size
		assert request.file_format is PlotFileFormat.SVG
		assert dialog.save_button.GetLabel() == "Save plot…"
		assert [
			child.GetLabel()
			for child in dialog.GetChildren()
			if isinstance(child, wx.Button)
		] == ["Add function", "Save plot…", "Cancel"]
	finally:
		dialog.Destroy()
		app.Destroy()


def test_dialog_adds_and_removes_labelled_function_rows():
	app = wx.App(False)
	dialog = TactilePlotDialog(None, "x")
	try:
		assert dialog.add_function_button.GetLabel() == "Add function"
		children = list(dialog.GetChildren())
		assert children.index(dialog.additional_panel) < children.index(
			dialog.x_min_input
		)
		assert children.index(dialog.add_function_button) < children.index(
			dialog.x_min_input
		)
		dialog._on_add_function(wx.CommandEvent())
		row, expression, legend = dialog.additional_rows[0]
		assert expression.GetName() == "g(x)"
		assert legend.GetName() == "Legend label for g(x)"
		expression.SetValue("x^2")
		legend.SetValue("Square")
		request = dialog.get_request()
		assert [
			(item.expression, item.label)
			for item in request.additional_functions
		] == [("x^2", "Square")]
		dialog._remove_row(row)
		assert dialog.get_request().additional_functions == ()
	finally:
		dialog.Destroy()
		app.Destroy()


def test_dialog_bounds_function_rows_and_keeps_them_scrollable():
	app = wx.App(False)
	dialog = TactilePlotDialog(None, "x")
	try:
		for _ in range(5):
			dialog._on_add_function(wx.CommandEvent())
		assert len(dialog.get_request().additional_functions) == 5
		dialog._on_add_function(wx.CommandEvent())
		assert len(dialog.additional_rows) == 5
		assert not dialog.add_function_button.IsEnabled()
		assert dialog.GetSize().height <= 720
		assert dialog.additional_panel.HasScrollbar(wx.VERTICAL)
		dialog._remove_row(dialog.additional_rows[0][0])
		assert dialog.add_function_button.IsEnabled()
	finally:
		dialog.Destroy()
		app.Destroy()


def test_remove_and_readd_keeps_accessible_function_numbers_in_sync():
	app = wx.App(False)
	dialog = TactilePlotDialog(None, "x")
	try:
		for _ in range(3):
			dialog._on_add_function(wx.CommandEvent())
		dialog._remove_row(dialog.additional_rows[0][0])
		assert [field.GetName() for _, field, _ in dialog.additional_rows] == [
			"g(x)",
			"h(x)",
		]
		dialog._on_add_function(wx.CommandEvent())
		assert [field.GetName() for _, field, _ in dialog.additional_rows] == [
			"g(x)",
			"h(x)",
			"i(x)",
		]
		for number, (row, _, legend) in enumerate(dialog.additional_rows, 2):
			assert (
				legend.GetName()
				== f"Legend label for {chr(ord('f') + number - 1)}(x)"
			)
			buttons = [
				child
				for child in row.GetChildren()
				if isinstance(child, wx.Button)
			]
			assert (
				buttons[0].GetLabel()
				== f"Remove {chr(ord('f') + number - 1)}(x)"
			)
	finally:
		dialog.Destroy()
		app.Destroy()


def test_actual_export_target_requires_confirmation_when_suffix_changes(
	monkeypatch,
	tmp_path,
):
	from powercalc.gui import tactile_plot_dialog

	selected = tmp_path / "plot.txt"
	actual = tmp_path / "plot.svg"
	actual.write_text("existing plot", encoding="utf-8")
	seen = []

	class FakeConfirmation:
		def __init__(self, parent, message, title, style):
			seen.append((message, title, style))
			self.result = wx.ID_NO

		def ShowModal(self):
			return self.result

		def Destroy(self):
			pass

	monkeypatch.setattr(
		tactile_plot_dialog.wx, "MessageDialog", FakeConfirmation
	)
	assert (
		tactile_plot_dialog.confirm_plot_output_path(
			None, selected, PlotFileFormat.SVG
		)
		is None
	)
	assert str(actual) in seen[0][0]
	assert actual.read_text(encoding="utf-8") == "existing plot"

	monkeypatch.setattr(FakeConfirmation, "ShowModal", lambda self: wx.ID_YES)
	assert (
		tactile_plot_dialog.confirm_plot_output_path(
			None, selected, PlotFileFormat.SVG
		)
		== actual
	)
	assert (
		tactile_plot_dialog.confirm_plot_output_path(
			None, tmp_path / "new.txt", PlotFileFormat.SVG
		)
		== tmp_path / "new.svg"
	)
	assert len(seen) == 2
