"""Native dialog for exporting a tactile function plot."""

from __future__ import annotations

import wx

from powercalc.core.tactile_plot import TactilePlotRequest


class TactilePlotDialog(wx.Dialog):
	"""Collect the small, keyboard-first set of tactile plot parameters."""

	def __init__(self, parent: wx.Window, expression: str) -> None:
		super().__init__(parent, title=_("Export Tactile Plot"))
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		intro = wx.StaticText(
			self,
			label=_(
				"Export one real-valued function of x as a high-contrast SVG. "
				"SVG stays sharp for swell paper and embossers."
			),
		)
		intro.Wrap(460)
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
		main_sizer.Add(
			grid,
			wx.SizerFlags(1).Expand().Border(wx.LEFT | wx.RIGHT, 12),
		)
		self.braille_labels = wx.CheckBox(
			self, label=_("Use simple Braille labels")
		)
		self.braille_labels.SetName(_("Use simple Braille labels"))
		main_sizer.Add(
			self.braille_labels,
			wx.SizerFlags(0).Border(wx.ALL, 12),
		)
		buttons = self.CreateStdDialogButtonSizer(wx.ID_SAVE | wx.ID_CANCEL)
		assert buttons is not None
		main_sizer.Add(
			buttons,
			wx.SizerFlags(0).Expand().Border(wx.ALL, 12),
		)
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

	def get_request(self) -> TactilePlotRequest:
		"""Return the request or raise ``ValueError`` for malformed bounds."""

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
			use_braille_labels=self.braille_labels.GetValue(),
		)
