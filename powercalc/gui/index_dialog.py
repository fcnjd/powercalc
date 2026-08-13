"""Searchable index of functions and constants."""

from __future__ import annotations

from collections.abc import Sequence

import wx

from powercalc.core import CatalogEntry


def filter_catalog_entries(
	entries: Sequence[CatalogEntry], query: str
) -> list[CatalogEntry]:
	"""Return entries whose name contains ``query`` (case-insensitive)."""

	needle = query.casefold()
	return [entry for entry in entries if needle in entry.name.casefold()]


class FunctionIndexDialog(wx.Dialog):
	"""Accessible searchable list of functions and constants."""

	def __init__(
		self,
		parent: wx.Window,
		entries: Sequence[CatalogEntry],
	) -> None:
		super().__init__(
			parent,
			title="Function and Constant Index",
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
			size=(360, 420),
		)
		self._all_entries = sorted(
			entries, key=lambda entry: entry.name.casefold()
		)
		self._visible_entries: list[CatalogEntry] = []

		main_sizer = wx.BoxSizer(wx.VERTICAL)

		filter_label = wx.StaticText(self, label="Search")
		self.filter_input = wx.TextCtrl(self)
		self.filter_input.SetName("Filter functions and constants")
		self.filter_input.Bind(wx.EVT_TEXT, self._on_filter_text)
		self.filter_input.Bind(wx.EVT_KEY_DOWN, self._on_filter_key_down)

		self.results_list = wx.ListCtrl(
			self,
			style=wx.LC_REPORT | wx.LC_SINGLE_SEL,
		)
		self.results_list.SetName("Functions and constants")
		self.results_list.InsertColumn(0, "Name", width=140)
		self.results_list.InsertColumn(1, "Code", width=140)
		self.results_list.Bind(
			wx.EVT_LIST_ITEM_ACTIVATED,
			self._on_list_item_activated,
		)

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
		self.SetMinSize((320, 360))

		self._apply_filter("")
		wx.CallAfter(self.filter_input.SetFocus)

	def get_selected_entry(self) -> CatalogEntry | None:
		"""Return the currently selected entry, or ``None``."""

		index = self.results_list.GetFirstSelected()
		if index == -1 or index >= len(self._visible_entries):
			return None
		return self._visible_entries[index]

	def _apply_filter(self, query: str) -> None:
		self._visible_entries = filter_catalog_entries(self._all_entries, query)
		self.results_list.DeleteAllItems()
		for row, entry in enumerate(self._visible_entries):
			self.results_list.InsertItem(row, entry.name)
			self.results_list.SetItem(row, 1, entry.insert_text)
		if self._visible_entries:
			self._select_row(0)
		self._update_ok_enabled()

	def _select_row(self, index: int) -> None:
		for row in range(self.results_list.GetItemCount()):
			self.results_list.Select(row, on=(row == index))
		self.results_list.EnsureVisible(index)

	def _move_selection(self, delta: int) -> None:
		count = len(self._visible_entries)
		if not count:
			return
		current = self.results_list.GetFirstSelected()
		current = 0 if current == -1 else current
		new_index = max(0, min(count - 1, current + delta))
		self._select_row(new_index)

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

	def _on_filter_key_down(self, event: wx.KeyEvent) -> None:
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

	def _on_list_item_activated(self, event: wx.ListEvent) -> None:
		self.EndModal(wx.ID_OK)
