"""Main wxPython window for Powercalc."""

from __future__ import annotations

from dataclasses import replace
from functools import partial

import wx

from powercalc.core import calculate
from powercalc.gui.formatting import (
	format_error_for_display,
	format_result_for_display,
)
from powercalc.gui.resources import get_app_icon_path
from powercalc.settings import AppSettings, SettingsSaveError, SettingsStore
from powercalc.version import get_version, get_versioned_title


ID_CLEAR_INPUT = wx.NewIdRef()
ID_COPY_RESULT = wx.NewIdRef()
ID_DECIMAL_PRECISION = wx.NewIdRef()
ID_ERROR_SOUND = wx.NewIdRef()
ID_RESTORE_DEFAULTS = wx.NewIdRef()

KEYBOARD_HELP = """Keyboard commands:

Enter in expression input: Calculate.
Tab and Shift+Tab: Move between controls.
Ctrl+L: Clear expression input.
Ctrl+C in result output: Copy selected result.
F1: Show this help.
Alt+O: Open calculation options.
Options use arrow keys and Enter. Escape closes a menu without changes.
In decimal comma mode, use semicolons between function arguments.
Alt+H, A: Show version information.
Alt+F, Alt+E, Alt+O, Alt+H: Open menus.
Alt+F4: Exit."""


class DecimalPrecisionDialog(wx.Dialog):
	"""Small accessible dialog for choosing decimal precision."""

	def __init__(self, parent: wx.Window, value: int) -> None:
		super().__init__(parent, title="Decimal Precision")
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		label = wx.StaticText(
			self,
			label="Decimal precision, from 1 to 100",
		)
		self.precision_input = wx.SpinCtrl(
			self,
			min=1,
			max=100,
			initial=value,
		)
		self.precision_input.SetName("Decimal precision, 1 to 100")

		main_sizer.Add(
			label,
			wx.SizerFlags(0).Expand().Border(wx.ALL, 12),
		)
		main_sizer.Add(
			self.precision_input,
			wx.SizerFlags(0)
			.Expand()
			.Border(wx.LEFT | wx.RIGHT | wx.BOTTOM, 12),
		)
		button_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
		main_sizer.Add(
			button_sizer,
			wx.SizerFlags(0).Expand().Border(wx.ALL, 12),
		)
		self.SetSizerAndFit(main_sizer)
		self.SetMinSize(self.GetSize())
		wx.CallAfter(self.precision_input.SetFocus)

	def get_value(self) -> int:
		"""Return the selected number of significant decimal digits."""

		return self.precision_input.GetValue()


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

	def __init__(
		self,
		*,
		settings: AppSettings | None = None,
		settings_store: SettingsStore | None = None,
		startup_warning: str | None = None,
	) -> None:
		super().__init__(None, title=get_versioned_title(), size=(640, 260))
		self.settings = settings or AppSettings()
		self.settings_store = settings_store or SettingsStore()
		self._set_window_icon()
		self._create_menu_bar()
		self._create_controls()
		self.CreateStatusBar()
		self.SetStatusText("Ready.")
		wx.CallAfter(self._finish_startup, startup_warning)

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

		options_menu = wx.Menu()
		self._option_items: dict[str, dict[object, wx.MenuItem]] = {}
		self._add_radio_submenu(
			options_menu,
			"&Angle Unit",
			"angle_unit",
			[
				("&Radians", "radian", "Angle unit: Radians."),
				("&Degrees", "degree", "Angle unit: Degrees."),
				("&Gradians", "gradian", "Angle unit: Gradians."),
			],
		)
		self._add_radio_submenu(
			options_menu,
			"&Decimal Separator",
			"decimal_separator",
			[
				(
					"&Point (1.5; arguments use commas)",
					"point",
					"Decimal separator: Point.",
				),
				(
					"&Comma (1,5; arguments use semicolons)",
					"comma",
					"Decimal separator: Comma.",
				),
			],
		)
		self._add_radio_submenu(
			options_menu,
			"&Number Domain",
			"number_domain",
			[
				("&Complex", "complex", "Number domain: Complex."),
				("&Real Only", "real", "Number domain: Real only."),
			],
		)
		self._add_radio_submenu(
			options_menu,
			"&Logarithm Mode",
			"log_mode",
			[
				("&Base 10", "calculator", "Logarithm mode: Base 10."),
				("&Natural", "natural", "Logarithm mode: Natural."),
			],
		)
		self._precision_item = options_menu.Append(
			ID_DECIMAL_PRECISION,
			"Decimal &Precision...",
			"Set significant decimal digits",
		)
		self._sound_item = options_menu.AppendCheckItem(
			ID_ERROR_SOUND,
			"Play &Sound on Calculation Errors",
			"Play a system sound when a calculation fails",
		)
		options_menu.AppendSeparator()
		restore_item = options_menu.Append(
			ID_RESTORE_DEFAULTS,
			"&Restore Defaults...",
			"Restore all calculation options to their defaults",
		)
		self.Bind(
			wx.EVT_MENU,
			self._on_decimal_precision,
			self._precision_item,
		)
		self.Bind(wx.EVT_MENU, self._on_error_sound, self._sound_item)
		self.Bind(wx.EVT_MENU, self._on_restore_defaults, restore_item)
		menu_bar.Append(options_menu, "&Options")
		self._sync_options_menu()

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

	def _add_radio_submenu(
		self,
		parent_menu: wx.Menu,
		label: str,
		field: str,
		choices: list[tuple[str, object, str]],
	) -> None:
		submenu = wx.Menu()
		items: dict[object, wx.MenuItem] = {}
		for item_label, value, status in choices:
			item = submenu.AppendRadioItem(wx.ID_ANY, item_label)
			self.Bind(
				wx.EVT_MENU,
				partial(
					self._on_choice_setting,
					field=field,
					value=value,
					status=status,
				),
				item,
			)
			items[value] = item
		self._option_items[field] = items
		parent_menu.AppendSubMenu(submenu, label)

	def _sync_options_menu(self) -> None:
		for field, items in self._option_items.items():
			items[getattr(self.settings, field)].Check(True)
		self._sound_item.Check(self.settings.play_error_sound)
		self._precision_item.SetItemLabel(
			f"Decimal &Precision... ({self.settings.decimal_precision})"
		)

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
		outcome = calculate(
			self.expression_input.GetValue(),
			self.settings.evaluation_options(),
		)
		if outcome.ok:
			assert outcome.result is not None
			output_text = format_result_for_display(
				outcome.result,
				self.settings.decimal_separator,
			)
			status_text = "Calculation complete."
		else:
			assert outcome.error is not None
			output_text = format_error_for_display(outcome.error)
			status_text = "Calculation failed."

		self.result_output.SetValue(output_text)
		if not outcome.ok and self.settings.play_error_sound:
			wx.Bell()
		self.result_output.SetFocus()
		self.result_output.SelectAll()
		self.SetStatusText(status_text)
		event.Skip(False)

	def _on_choice_setting(
		self,
		event: wx.Event,
		*,
		field: str,
		value: object,
		status: str,
	) -> None:
		self.settings = replace(self.settings, **{field: value})
		self._sync_options_menu()
		self._save_settings()
		self.SetStatusText(status)
		event.Skip(False)

	def _on_decimal_precision(self, event: wx.Event) -> None:
		dialog = DecimalPrecisionDialog(
			self,
			self.settings.decimal_precision,
		)
		try:
			if dialog.ShowModal() != wx.ID_OK:
				event.Skip(False)
				return
			precision = dialog.get_value()
		finally:
			dialog.Destroy()

		self.settings = replace(
			self.settings,
			decimal_precision=precision,
		)
		self._sync_options_menu()
		self._save_settings()
		self.SetStatusText(f"Decimal precision: {precision}.")
		event.Skip(False)

	def _on_error_sound(self, event: wx.CommandEvent) -> None:
		self.settings = replace(
			self.settings,
			play_error_sound=event.IsChecked(),
		)
		self._sync_options_menu()
		self._save_settings()
		state = "on" if self.settings.play_error_sound else "off"
		self.SetStatusText(f"Error sound: {state}.")
		event.Skip(False)

	def _on_restore_defaults(self, event: wx.Event) -> None:
		dialog = wx.MessageDialog(
			self,
			"Restore all calculation options to their default values?",
			"Restore Defaults",
			wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
		)
		try:
			confirmed = dialog.ShowModal() == wx.ID_YES
		finally:
			dialog.Destroy()
		if confirmed:
			self.settings = AppSettings()
			self._sync_options_menu()
			self._save_settings()
			self.SetStatusText("Default options restored.")
		event.Skip(False)

	def _save_settings(self) -> None:
		try:
			self.settings_store.save(self.settings)
		except SettingsSaveError:
			self._show_warning(
				"The options are active for this session but could not be "
				"saved."
			)

	def _finish_startup(self, warning: str | None) -> None:
		if warning:
			self._show_warning(warning)
		self.expression_input.SetFocus()

	def _show_warning(self, message: str) -> None:
		dialog = wx.MessageDialog(
			self,
			message,
			"Powercalc Settings",
			wx.OK | wx.ICON_WARNING,
		)
		try:
			dialog.ShowModal()
		finally:
			dialog.Destroy()

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
