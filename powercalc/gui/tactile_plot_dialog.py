"""Keyboard-operable dialog for tactile function-plot export."""

from __future__ import annotations

from pathlib import Path

import wx

from powercalc.core.tactile_plot import (
	ContentProfile,
	PaperSize,
	PlotFileFormat,
	PlotFunction,
	MAX_FUNCTIONS,
	TactilePlotRequest,
	braille_labels_available,
	plot_output_path,
)

_PROFILE_CHOICES = (
	(_("Swell paper"), ContentProfile.SWELL_PAPER),
	(_("Embosser"), ContentProfile.EMBOSSER),
)
_PAPER_SIZE_CHOICES = (
	(_("A4 landscape"), PaperSize.A4_LANDSCAPE),
	(_("A4 portrait"), PaperSize.A4_PORTRAIT),
	(_("A5 landscape"), PaperSize.A5_LANDSCAPE),
	(_("A5 portrait"), PaperSize.A5_PORTRAIT),
)
_FORMAT_CHOICES = (
	("SVG", PlotFileFormat.SVG),
	("PNG", PlotFileFormat.PNG),
)


def confirm_plot_output_path(
	parent: wx.Window,
	selected_path: Path,
	file_format: PlotFileFormat,
) -> Path | None:
	"""Confirm overwriting the actual output when its suffix changes."""

	output_path = plot_output_path(selected_path, file_format)
	if output_path == selected_path or not output_path.exists():
		return output_path
	confirmation = wx.MessageDialog(
		parent,
		_(
			"The selected format will save to {path}. "
			"Replace this existing file?"
		).format(path=output_path),
		_("Replace tactile plot?"),
		wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
	)
	try:
		return output_path if confirmation.ShowModal() == wx.ID_YES else None
	finally:
		confirmation.Destroy()


class TactilePlotDialog(wx.Dialog):
	"""Collect the approved v2 tactile-plot request parameters."""

	def __init__(self, parent: wx.Window, expression: str) -> None:
		super().__init__(parent, title=_("Export tactile function plot"))
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		intro = wx.StaticText(
			self,
			label=_(
				"Export real-valued functions of x as a tactile graphic. "
				"The content profile and file format are selected separately."
			),
		)
		intro.Wrap(500)
		main_sizer.Add(
			intro,
			wx.SizerFlags(0).Expand().Border(wx.ALL, 12),
		)

		grid = wx.FlexGridSizer(cols=2, hgap=8, vgap=8)
		grid.AddGrowableCol(1, 1)
		self.expression_input = self._add_text_field(
			grid, _("Function of x"), expression or "x^2"
		)
		self.first_label_input = self._add_text_field(
			grid, _("Function 1 legend label"), ""
		)
		main_sizer.Add(
			grid,
			wx.SizerFlags(0).Expand().Border(wx.LEFT | wx.RIGHT, 12),
		)

		self.additional_rows: list[
			tuple[wx.Panel, wx.TextCtrl, wx.TextCtrl]
		] = []
		self.additional_panel = wx.ScrolledWindow(
			self, style=wx.VSCROLL | wx.TAB_TRAVERSAL
		)
		self.additional_panel.SetScrollRate(0, 15)
		self.additional_sizer = wx.BoxSizer(wx.VERTICAL)
		self.additional_panel.SetSizer(self.additional_sizer)
		self.additional_panel.SetMinSize((-1, 0))
		main_sizer.Add(
			self.additional_panel,
			wx.SizerFlags(0).Expand().Border(wx.LEFT | wx.RIGHT, 12),
		)
		self.add_function_button = wx.Button(self, label=_("Add function"))
		self.add_function_button.SetName(_("Add function"))
		self.add_function_button.Bind(wx.EVT_BUTTON, self._on_add_function)
		main_sizer.Add(
			self.add_function_button,
			wx.SizerFlags(0).Border(wx.LEFT | wx.RIGHT | wx.TOP, 12),
		)

		grid = wx.FlexGridSizer(cols=2, hgap=8, vgap=8)
		grid.AddGrowableCol(1, 1)
		self.x_min_input = self._add_text_field(grid, _("X minimum"), "-10")
		self.x_max_input = self._add_text_field(grid, _("X maximum"), "10")
		self.title_input = self._add_text_field(
			grid, _("Title"), _("Tactile function plot")
		)
		self.profile_choice = self._add_choice(
			grid, _("Content profile"), _PROFILE_CHOICES
		)
		self.paper_size_choice = self._add_choice(
			grid, _("Paper size"), _PAPER_SIZE_CHOICES
		)
		self.file_format_choice = self._add_choice(
			grid, _("File format"), _FORMAT_CHOICES
		)
		main_sizer.Add(
			grid,
			wx.SizerFlags(0).Expand().Border(wx.LEFT | wx.RIGHT, 12),
		)

		self.braille_labels = wx.CheckBox(self, label=_("Braille labels"))
		self.braille_labels.SetName(_("Braille labels"))
		if braille_labels_available():
			self.braille_labels.SetToolTip(
				_("Use bundled Liblouis for German Grade 1 Braille labels.")
			)
		else:
			self.braille_labels.Disable()
			braille_help = wx.StaticText(
				self,
				label=_(
					"Braille labels are unavailable because this installation "
					"does not include the Liblouis runtime."
				),
			)
			self.braille_labels.SetToolTip(
				_(
					"Braille labels require the bundled Liblouis runtime and "
					"are unavailable in this installation."
				)
			)
		main_sizer.Add(
			self.braille_labels,
			wx.SizerFlags(0).Border(wx.LEFT | wx.RIGHT | wx.TOP, 12),
		)
		if not self.braille_labels.IsEnabled():
			main_sizer.Add(
				braille_help,
				wx.SizerFlags(0)
				.Expand()
				.Border(wx.LEFT | wx.RIGHT | wx.TOP, 12),
			)

		button_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.save_button = wx.Button(self, wx.ID_SAVE, _("Save plot…"))
		cancel_button = wx.Button(self, wx.ID_CANCEL, _("Cancel"))
		button_sizer.AddStretchSpacer()
		button_sizer.Add(
			self.save_button,
			wx.SizerFlags(0).Border(wx.RIGHT, 8),
		)
		button_sizer.Add(cancel_button)
		main_sizer.Add(
			button_sizer,
			wx.SizerFlags(0).Expand().Border(wx.ALL, 12),
		)
		self.SetEscapeId(wx.ID_CANCEL)
		self.SetAffirmativeId(wx.ID_SAVE)
		self.save_button.SetDefault()
		self.SetSizerAndFit(main_sizer)
		self.SetMinSize(self.GetSize())
		wx.CallAfter(self.expression_input.SetFocus)

	def _on_add_function(self, event: wx.Event) -> None:
		"""Add an accessible expression/legend pair below the first function."""

		index = len(self.additional_rows) + 2
		row = wx.Panel(self.additional_panel)
		row_sizer = wx.BoxSizer(wx.VERTICAL)
		fields = wx.FlexGridSizer(cols=2, hgap=8, vgap=5)
		fields.AddGrowableCol(1, 1)
		expression_label = _("Function {number} of x").format(number=index)
		legend_label = _("Function {number} legend label").format(number=index)
		fields.Add(
			wx.StaticText(row, label=expression_label),
			0,
			wx.ALIGN_CENTER_VERTICAL,
		)
		expression = wx.TextCtrl(row)
		expression.SetName(expression_label)
		fields.Add(expression, 1, wx.EXPAND)
		fields.Add(
			wx.StaticText(row, label=legend_label),
			0,
			wx.ALIGN_CENTER_VERTICAL,
		)
		legend = wx.TextCtrl(row)
		legend.SetName(legend_label)
		fields.Add(legend, 1, wx.EXPAND)
		row_sizer.Add(fields, 0, wx.EXPAND)
		remove_button = wx.Button(
			row, label=_("Remove function {number}").format(number=index)
		)
		remove_button.Bind(wx.EVT_BUTTON, lambda unused: self._remove_row(row))
		row_sizer.Add(remove_button, 0, wx.ALIGN_RIGHT | wx.TOP, 4)
		row.SetSizer(row_sizer)
		self.additional_sizer.Add(row, 0, wx.EXPAND | wx.TOP, 8)
		self.additional_rows.append((row, expression, legend))
		self._renumber_rows()
		self._resize_additional_rows()
		self.add_function_button.Enable(
			len(self.additional_rows) + 1 < MAX_FUNCTIONS
		)
		expression.SetFocus()

	def _remove_row(self, row: wx.Panel) -> None:
		self.additional_rows = [
			entry for entry in self.additional_rows if entry[0] is not row
		]
		self.additional_sizer.Detach(row)
		row.Destroy()
		self._renumber_rows()
		self.add_function_button.Enable()
		self._resize_additional_rows()
		self.add_function_button.SetFocus()

	def _renumber_rows(self) -> None:
		"""Keep accessible numbers aligned with validation errors."""

		for number, (row, expression, legend) in enumerate(
			self.additional_rows, 2
		):
			labels = [
				child
				for child in row.GetChildren()
				if isinstance(child, wx.StaticText)
			]
			expression_label = _("Function {number} of x").format(number=number)
			legend_label = _("Function {number} legend label").format(
				number=number
			)
			labels[0].SetLabel(expression_label)
			labels[1].SetLabel(legend_label)
			expression.SetName(expression_label)
			legend.SetName(legend_label)
			button = next(
				child
				for child in row.GetChildren()
				if isinstance(child, wx.Button)
			)
			button.SetLabel(_("Remove function {number}").format(number=number))

	def _resize_additional_rows(self) -> None:
		self.additional_panel.FitInside()
		content_height = self.additional_sizer.GetMinSize().height
		self.additional_panel.SetMinSize((-1, min(content_height, 160)))
		self.SetSizerAndFit(self.GetSizer())
		self.Layout()

	def _add_text_field(
		self,
		grid: wx.FlexGridSizer,
		label: str,
		value: str,
	) -> wx.TextCtrl:
		field_label = wx.StaticText(self, label=label)
		field = wx.TextCtrl(self, value=value)
		field.SetName(label)
		grid.Add(field_label, wx.SizerFlags(0).CenterVertical())
		grid.Add(field, wx.SizerFlags(1).Expand())
		return field

	def _add_choice(
		self,
		grid: wx.FlexGridSizer,
		label: str,
		choices: tuple[tuple[str, object], ...],
	) -> wx.Choice:
		field_label = wx.StaticText(self, label=label)
		field = wx.Choice(self, choices=[display for display, _ in choices])
		field.SetName(label)
		field.SetSelection(0)
		grid.Add(field_label, wx.SizerFlags(0).CenterVertical())
		grid.Add(field, wx.SizerFlags(1).Expand())
		return field

	def get_request(self) -> TactilePlotRequest:
		"""Return the selected request or raise ``ValueError`` for bounds."""

		try:
			x_min = float(self.x_min_input.GetValue())
			x_max = float(self.x_max_input.GetValue())
		except ValueError as exc:
			raise ValueError(
				_("X minimum and maximum must be numbers.")
			) from exc
		return TactilePlotRequest(
			expression=self.expression_input.GetValue(),
			label=self.first_label_input.GetValue(),
			additional_functions=tuple(
				PlotFunction(field.GetValue(), legend.GetValue())
				for _, field, legend in self.additional_rows
			),
			x_min=x_min,
			x_max=x_max,
			title=self.title_input.GetValue(),
			content_profile=_PROFILE_CHOICES[
				self.profile_choice.GetSelection()
			][1],
			paper_size=_PAPER_SIZE_CHOICES[
				self.paper_size_choice.GetSelection()
			][1],
			file_format=_FORMAT_CHOICES[self.file_format_choice.GetSelection()][
				1
			],
			use_braille_labels=self.braille_labels.GetValue(),
		)
