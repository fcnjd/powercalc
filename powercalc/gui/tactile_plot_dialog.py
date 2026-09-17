"""Keyboard-operable dialog for tactile function-plot export."""

from __future__ import annotations

import wx

from powercalc.core.tactile_plot import (
	ContentProfile,
	PaperSize,
	PlotFileFormat,
	TactilePlotRequest,
	braille_labels_available,
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


class TactilePlotDialog(wx.Dialog):
	"""Collect the approved v2 tactile-plot request parameters."""

	def __init__(self, parent: wx.Window, expression: str) -> None:
		super().__init__(parent, title=_("Export tactile function plot"))
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		intro = wx.StaticText(
			self,
			label=_(
				"Export one real-valued function of x as a tactile graphic. "
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
			wx.SizerFlags(1).Expand().Border(wx.LEFT | wx.RIGHT, 12),
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
			wx.SizerFlags(0).Right().Border(wx.RIGHT, 8),
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
