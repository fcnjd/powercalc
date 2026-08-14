"""Searchable index of functions and constants."""

from __future__ import annotations

from collections.abc import Sequence

import wx

from powercalc.core import CatalogEntry, DecimalSeparator, build_insertion


def filter_catalog_entries(
	entries: Sequence[CatalogEntry], query: str
) -> list[CatalogEntry]:
	"""Return entries whose display or function name contains ``query``.

	Matching is case-insensitive and checks both the descriptive display
	name and the raw function/constant name, so a user who knows the
	technical name (e.g. "sqrt") can find it even though the list shows
	a descriptive label (e.g. "Quadratwurzel von n").
	"""

	needle = query.casefold()
	return [
		entry
		for entry in entries
		if needle in entry.display_name.casefold()
		or needle in entry.function_name.casefold()
	]


class FunctionIndexDialog(wx.Dialog):
	"""Accessible searchable list of functions and constants."""

	def __init__(
		self,
		parent: wx.Window,
		entries: Sequence[CatalogEntry],
		decimal_separator: DecimalSeparator,
	) -> None:
		super().__init__(
			parent,
			title=_("Function and Constant Index"),
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
			size=(480, 420),
		)
		self._decimal_separator = decimal_separator
		self._all_entries = sorted(
			entries, key=lambda entry: entry.display_name.casefold()
		)
		self._visible_entries: list[CatalogEntry] = []

		main_sizer = wx.BoxSizer(wx.VERTICAL)

		filter_label = wx.StaticText(self, label=_("Search"))
		self.filter_input = wx.TextCtrl(self)
		self.filter_input.SetName(_("Filter functions and constants"))
		self.filter_input.Bind(wx.EVT_TEXT, self._on_filter_text)
		self.filter_input.Bind(wx.EVT_KEY_DOWN, self._on_navigation_key_down)

		self.results_list = wx.ListBox(self, style=wx.LB_SINGLE)
		self.results_list.SetName(_("Functions and constants"))
		self.results_list.Bind(
			wx.EVT_LISTBOX_DCLICK,
			self._on_list_item_activated,
		)
		self.results_list.Bind(wx.EVT_KEY_DOWN, self._on_navigation_key_down)

		main_sizer.Add(filter_label, wx.SizerFlags(0).Border(wx.ALL, 12))
		main_sizer.Add(
			self.filter_input,
			wx.SizerFlags(0)
			.Expand()
			.Border(wx.LEFT | wx.RIGHT | wx.BOTTOM, 12),
		)
		main_sizer.Add(
			self.results_list,
			wx.SizerFlags(1)
			.Expand()
			.Border(wx.LEFT | wx.RIGHT | wx.BOTTOM, 12),
		)
		button_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
		main_sizer.Add(
			button_sizer,
			wx.SizerFlags(0).Expand().Border(wx.ALL, 12),
		)
		self.SetSizer(main_sizer)
		self.SetMinSize((360, 360))

		self._apply_filter("")
		wx.CallAfter(self.results_list.SetFocus)

	def get_selected_entry(self) -> CatalogEntry | None:
		"""Return the currently selected entry, or ``None``."""

		index = self.results_list.GetSelection()
		if index == wx.NOT_FOUND or index >= len(self._visible_entries):
			return None
		return self._visible_entries[index]

	def _row_label(self, entry: CatalogEntry) -> str:
		text, _, _ = build_insertion(entry, self._decimal_separator)
		return f"{entry.display_name} — {text}"

	def _apply_filter(self, query: str) -> None:
		self._visible_entries = filter_catalog_entries(self._all_entries, query)
		self.results_list.Set(
			[self._row_label(entry) for entry in self._visible_entries]
		)
		if self._visible_entries:
			self.results_list.SetSelection(0)
		self._update_ok_enabled()

	def _move_selection(self, delta: int) -> None:
		count = len(self._visible_entries)
		if not count:
			return
		current = self.results_list.GetSelection()
		current = 0 if current == wx.NOT_FOUND else current
		new_index = max(0, min(count - 1, current + delta))
		self.results_list.SetSelection(new_index)

	def _update_ok_enabled(self) -> None:
		ok_button = self.FindWindowById(wx.ID_OK)
		if ok_button is not None:
			ok_button.Enable(bool(self._visible_entries))

	def _confirm_selection(self) -> None:
		if self.get_selected_entry() is not None:
			self.EndModal(wx.ID_OK)
		else:
			wx.Bell()

	def _on_filter_text(self, event: wx.CommandEvent) -> None:
		self._apply_filter(self.filter_input.GetValue())
		event.Skip()

	def _on_navigation_key_down(self, event: wx.KeyEvent) -> None:
		key = event.GetKeyCode()
		if key == wx.WXK_DOWN:
			self._move_selection(1)
		elif key == wx.WXK_UP:
			self._move_selection(-1)
		elif key == wx.WXK_RETURN:
			self._confirm_selection()
		elif key == wx.WXK_ESCAPE:
			self.EndModal(wx.ID_CANCEL)
		else:
			event.Skip()

	def _on_list_item_activated(self, event: wx.CommandEvent) -> None:
		self.EndModal(wx.ID_OK)
