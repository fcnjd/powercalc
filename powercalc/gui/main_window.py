"""Main wxPython window for Powercalc."""

from __future__ import annotations

import wx

from powercalc.core import calculate
from powercalc.gui.formatting import (
	format_error_for_display,
	format_result_for_display,
)
from powercalc.gui.resources import get_app_icon_path
from powercalc.version import get_version, get_versioned_title


ID_CLEAR_INPUT = wx.NewIdRef()
ID_COPY_RESULT = wx.NewIdRef()

KEYBOARD_HELP = """Keyboard commands:

Enter in expression input: Calculate.
Tab and Shift+Tab: Move between controls.
Ctrl+L: Clear expression input.
Ctrl+C in result output: Copy selected result.
F1: Show this help.
Alt+H, A: Show version information.
Alt+F, Alt+E, Alt+H: Open menus.
Alt+F4: Exit."""


class KeyboardFocusableReadOnlyTextCtrl(wx.TextCtrl):
	"""Read-only native text box that remains reachable by Tab.

	On Windows screen-reader testing, a plain read-only ``wx.TextCtrl`` was
	not reliably reachable via Tab. This subclass keeps the standard native
	text control while explicitly opting in to keyboard focus.
	"""

	def __init__(self, parent: wx.Window) -> None:
		super().__init__(parent)
		self.SetEditable(False)
		self.SetCanFocus(True)

	def AcceptsFocusFromKeyboard(self) -> bool:
		return True

	def CanAcceptFocusFromKeyboard(self) -> bool:
		return True


class MainFrame(wx.Frame):
	"""Main calculator window built from native wxPython controls."""

	def __init__(self) -> None:
		super().__init__(None, title=get_versioned_title(), size=(640, 260))
		self._set_window_icon()
		self._create_menu_bar()
		self._create_controls()
		self.CreateStatusBar()
		self.SetStatusText("Ready.")
		wx.CallAfter(self.expression_input.SetFocus)

	def _create_menu_bar(self) -> None:
		menu_bar = wx.MenuBar()

		file_menu = wx.Menu()
		exit_item = file_menu.Append(
			wx.ID_EXIT,
			"E&xit",
			"Exit Powercalc",
		)
		self.Bind(wx.EVT_MENU, self._on_exit, exit_item)
		menu_bar.Append(file_menu, "&File")

		edit_menu = wx.Menu()
		clear_item = edit_menu.Append(
			ID_CLEAR_INPUT,
			"Clear &Input\tCtrl+L",
			"Clear the expression input",
		)
		copy_item = edit_menu.Append(
			ID_COPY_RESULT,
			"Copy &Result",
			"Copy the result output",
		)
		self.Bind(wx.EVT_MENU, self._on_clear_input, clear_item)
		self.Bind(wx.EVT_MENU, self._on_copy_result, copy_item)
		menu_bar.Append(edit_menu, "&Edit")

		help_menu = wx.Menu()
		commands_item = help_menu.Append(
			wx.ID_HELP,
			"&Keyboard Commands\tF1",
			"Show keyboard commands",
		)
		about_item = help_menu.Append(
			wx.ID_ABOUT,
			"&About Powercalc",
			"Show Powercalc version information",
		)
		self.Bind(wx.EVT_MENU, self._on_keyboard_help, commands_item)
		self.Bind(wx.EVT_MENU, self._on_about, about_item)
		menu_bar.Append(help_menu, "&Help")

		self.SetMenuBar(menu_bar)

	def _set_window_icon(self) -> None:
		icon_path = get_app_icon_path()
		if icon_path is not None:
			self.SetIcon(wx.Icon(str(icon_path), wx.BITMAP_TYPE_ICO))

	def _create_controls(self) -> None:
		panel = wx.Panel(self)
		main_sizer = wx.BoxSizer(wx.VERTICAL)

		expression_label = wx.StaticText(panel, label="Expression")
		self.expression_input = wx.TextCtrl(
			panel,
			style=wx.TE_PROCESS_ENTER,
		)
		self.expression_input.SetName("Expression input")
		self.expression_input.Bind(wx.EVT_TEXT_ENTER, self._on_calculate)

		self.calculate_button = wx.Button(panel, label="Calculate")
		self.calculate_button.SetName("Calculate")
		self.calculate_button.Bind(wx.EVT_BUTTON, self._on_calculate)

		input_row = wx.BoxSizer(wx.HORIZONTAL)
		input_row.Add(
			self.expression_input,
			wx.SizerFlags(1).Expand().Border(wx.RIGHT, 8),
		)
		input_row.Add(self.calculate_button, wx.SizerFlags(0))

		result_label = wx.StaticText(panel, label="Result")
		self.result_output = KeyboardFocusableReadOnlyTextCtrl(panel)
		self.result_output.SetName("Result output")
		self.calculate_button.MoveAfterInTabOrder(self.expression_input)
		self.result_output.MoveAfterInTabOrder(self.calculate_button)

		main_sizer.Add(
			expression_label,
			wx.SizerFlags(0).Expand().Border(wx.LEFT | wx.RIGHT | wx.TOP, 12),
		)
		main_sizer.Add(
			input_row,
			wx.SizerFlags(0).Expand().Border(wx.LEFT | wx.RIGHT | wx.TOP, 12),
		)
		main_sizer.Add(
			result_label,
			wx.SizerFlags(0).Expand().Border(wx.LEFT | wx.RIGHT | wx.TOP, 12),
		)
		main_sizer.Add(
			self.result_output,
			wx.SizerFlags(0).Expand().Border(wx.ALL, 12),
		)

		panel.SetSizer(main_sizer)

	def _on_calculate(self, event: wx.Event) -> None:
		outcome = calculate(self.expression_input.GetValue())
		if outcome.ok:
			assert outcome.result is not None
			output_text = format_result_for_display(outcome.result)
			status_text = "Calculation complete."
		else:
			assert outcome.error is not None
			output_text = format_error_for_display(outcome.error)
			status_text = "Calculation failed."

		self.result_output.SetValue(output_text)
		self.result_output.SetFocus()
		self.result_output.SelectAll()
		self.SetStatusText(status_text)
		event.Skip(False)

	def _on_clear_input(self, event: wx.Event) -> None:
		self.expression_input.Clear()
		self.expression_input.SetFocus()
		self.SetStatusText("Input cleared.")
		event.Skip(False)

	def _on_copy_result(self, event: wx.Event) -> None:
		text = self.result_output.GetValue()
		if not text:
			self.SetStatusText("No result to copy.")
			event.Skip(False)
			return

		if not wx.TheClipboard.Open():
			self.SetStatusText("Clipboard is not available.")
			event.Skip(False)
			return

		try:
			wx.TheClipboard.SetData(wx.TextDataObject(text))
			self.SetStatusText("Result copied.")
		finally:
			wx.TheClipboard.Close()
		event.Skip(False)

	def _on_keyboard_help(self, event: wx.Event) -> None:
		dialog = wx.MessageDialog(
			self,
			KEYBOARD_HELP,
			"Keyboard Commands",
			wx.OK | wx.ICON_INFORMATION,
		)
		try:
			dialog.ShowModal()
		finally:
			dialog.Destroy()
		event.Skip(False)

	def _on_about(self, event: wx.Event) -> None:
		dialog = wx.MessageDialog(
			self,
			(
				f"Powercalc {get_version()}\n\n"
				"Accessible desktop calculator.\n"
				"Updates are available from GitHub Releases."
			),
			"About Powercalc",
			wx.OK | wx.ICON_INFORMATION,
		)
		try:
			dialog.ShowModal()
		finally:
			dialog.Destroy()
		event.Skip(False)

	def _on_exit(self, event: wx.Event) -> None:
		self.Close()
		event.Skip(False)
