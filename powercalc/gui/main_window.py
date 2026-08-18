"""Main wxPython window for Powercalc."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from functools import partial

import wx

from powercalc.core import (
	FUNCTION_CATALOG,
	CatalogEntry,
	build_insertion,
	calculate,
)
from powercalc.gui.formatting import (
	format_error_for_display,
	format_result_for_display,
)
from powercalc.gui.index_dialog import FunctionIndexDialog
from powercalc.gui.resources import get_app_icon_path
from powercalc.settings import AppSettings, SettingsSaveError, SettingsStore
from powercalc.version import get_version, get_versioned_title


ID_CLEAR_INPUT = wx.NewIdRef()
ID_COPY_RESULT = wx.NewIdRef()
ID_DECIMAL_PRECISION = wx.NewIdRef()
ID_ERROR_SOUND = wx.NewIdRef()
ID_FUNCTION_INDEX = wx.NewIdRef()
ID_RESTORE_DEFAULTS = wx.NewIdRef()

KEYBOARD_HELP = _("""Keyboard commands:

Enter in expression input: Calculate.
Tab and Shift+Tab: Move between controls.
Ctrl+L: Clear expression input.
Ctrl+C in result output: Copy selected result.
Ctrl+Shift+X: Open function and constant index.
The index opens with the list focused; type a letter to jump, or use
arrow keys and Enter. Tab reaches a search field that filters by
substring. Escape closes without inserting. Inserting selects the
first argument so it can be typed over immediately.
F1: Show this help.
Alt+O: Open calculation options.
Options use arrow keys and Enter. Escape closes a menu without changes.
In decimal comma mode, use semicolons between function arguments.
Alt+H, A: Show version information.
Alt+F, Alt+E, Alt+O, Alt+H: Open menus.
Alt+F4: Exit.""")


class DecimalPrecisionDialog(wx.Dialog):
	"""Small accessible dialog for choosing decimal precision."""

	def __init__(self, parent: wx.Window, value: int) -> None:
		super().__init__(parent, title=_("Decimal Precision"))
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		label = wx.StaticText(
			self,
			label=_("Decimal precision, from 1 to 100"),
		)
		self.precision_input = wx.SpinCtrl(
			self,
			min=1,
			max=100,
			initial=value,
		)
		self.precision_input.SetName(_("Decimal precision, 1 to 100"))

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
		self.SetStatusText(_("Ready."))
		wx.CallAfter(self._finish_startup, startup_warning)

	def _create_menu_bar(self) -> None:
		menu_bar = wx.MenuBar()

		file_menu = wx.Menu()
		exit_item = file_menu.Append(
			wx.ID_EXIT,
			_("E&xit"),
			_("Exit Powercalc"),
		)
		self.Bind(wx.EVT_MENU, self._on_exit, exit_item)
		menu_bar.Append(file_menu, _("&File"))

		edit_menu = wx.Menu()
		clear_item = edit_menu.Append(
			ID_CLEAR_INPUT,
			_("Clear &Input\tCtrl+L"),
			_("Clear the expression input"),
		)
		copy_item = edit_menu.Append(
			ID_COPY_RESULT,
			_("Copy &Result"),
			_("Copy the result output"),
		)
		index_item = edit_menu.Append(
			ID_FUNCTION_INDEX,
			_("&Function Index...\tCtrl+Shift+X"),
			_("Open the function and constant index"),
		)
		self.Bind(wx.EVT_MENU, self._on_clear_input, clear_item)
		self.Bind(wx.EVT_MENU, self._on_copy_result, copy_item)
		self.Bind(wx.EVT_MENU, self._on_function_index, index_item)
		menu_bar.Append(edit_menu, _("&Edit"))

		options_menu = wx.Menu()
		self._option_items: dict[str, dict[object, wx.MenuItem]] = {}
		self._add_radio_submenu(
			options_menu,
			_("&Angle Unit"),
			"angle_unit",
			[
				(_("&Radians"), "radian", _("Angle unit: Radians.")),
				(_("&Degrees"), "degree", _("Angle unit: Degrees.")),
				(_("&Gradians"), "gradian", _("Angle unit: Gradians.")),
			],
		)
		self._add_radio_submenu(
			options_menu,
			_("&Decimal Separator"),
			"decimal_separator",
			[
				(
					_("&Point (1.5; arguments use commas)"),
					"point",
					_("Decimal separator: Point."),
				),
				(
					_("&Comma (1,5; arguments use semicolons)"),
					"comma",
					_("Decimal separator: Comma."),
				),
			],
		)
		self._add_radio_submenu(
			options_menu,
			_("&Number Domain"),
			"number_domain",
			[
				(_("&Complex"), "complex", _("Number domain: Complex.")),
				(_("&Real Only"), "real", _("Number domain: Real only.")),
			],
		)
		self._add_radio_submenu(
			options_menu,
			_("&Logarithm Mode"),
			"log_mode",
			[
				(_("&Base 10"), "calculator", _("Logarithm mode: Base 10.")),
				(_("&Natural"), "natural", _("Logarithm mode: Natural.")),
			],
		)
		self._add_radio_submenu(
			options_menu,
			_("&Language"),
			"language",
			[
				(
					_("&System"),
					"system",
					_(
						"Language set to System. Restart Powercalc for the "
						"change to take effect."
					),
				),
				(
					"&English",
					"en",
					_(
						"Language set to English. Restart Powercalc for the "
						"change to take effect."
					),
				),
				(
					"&Deutsch",
					"de",
					_(
						"Language set to Deutsch. Restart Powercalc for the "
						"change to take effect."
					),
				),
			],
			on_select=self._on_language_choice,
		)
		self._precision_item = options_menu.Append(
			ID_DECIMAL_PRECISION,
			_("Decimal &Precision..."),
			_("Set significant decimal digits"),
		)
		self._sound_item = options_menu.AppendCheckItem(
			ID_ERROR_SOUND,
			_("Play &Sound on Calculation Errors"),
			_("Play a system sound when a calculation fails"),
		)
		options_menu.AppendSeparator()
		restore_item = options_menu.Append(
			ID_RESTORE_DEFAULTS,
			_("&Restore Defaults..."),
			_("Restore all calculation options to their defaults"),
		)
		self.Bind(
			wx.EVT_MENU,
			self._on_decimal_precision,
			self._precision_item,
		)
		self.Bind(wx.EVT_MENU, self._on_error_sound, self._sound_item)
		self.Bind(wx.EVT_MENU, self._on_restore_defaults, restore_item)
		menu_bar.Append(options_menu, _("&Options"))
		self._sync_options_menu()

		help_menu = wx.Menu()
		commands_item = help_menu.Append(
			wx.ID_HELP,
			_("&Keyboard Commands\tF1"),
			_("Show keyboard commands"),
		)
		about_item = help_menu.Append(
			wx.ID_ABOUT,
			_("&About Powercalc"),
			_("Show Powercalc version information"),
		)
		self.Bind(wx.EVT_MENU, self._on_keyboard_help, commands_item)
		self.Bind(wx.EVT_MENU, self._on_about, about_item)
		menu_bar.Append(help_menu, _("&Help"))

		self.SetMenuBar(menu_bar)

	def _add_radio_submenu(
		self,
		parent_menu: wx.Menu,
		label: str,
		field: str,
		choices: list[tuple[str, object, str]],
		*,
		on_select: Callable[..., None] | None = None,
	) -> None:
		submenu = wx.Menu()
		items: dict[object, wx.MenuItem] = {}
		handler = on_select or self._on_choice_setting
		for item_label, value, status in choices:
			item = submenu.AppendRadioItem(wx.ID_ANY, item_label)
			self.Bind(
				wx.EVT_MENU,
				partial(
					handler,
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
			_("Decimal &Precision... ({precision})").format(
				precision=self.settings.decimal_precision
			)
		)

	def _set_window_icon(self) -> None:
		icon_path = get_app_icon_path()
		if icon_path is not None:
			self.SetIcon(wx.Icon(str(icon_path), wx.BITMAP_TYPE_ICO))

	def _create_controls(self) -> None:
		panel = wx.Panel(self)
		main_sizer = wx.BoxSizer(wx.VERTICAL)

		self.info_bar = wx.InfoBar(panel)
		main_sizer.Add(self.info_bar, wx.SizerFlags(0).Expand())

		expression_label = wx.StaticText(panel, label=_("Expression"))
		self.expression_input = wx.TextCtrl(
			panel,
			style=wx.TE_PROCESS_ENTER,
		)
		self.expression_input.SetName(_("Expression input"))
		self.expression_input.Bind(wx.EVT_TEXT_ENTER, self._on_calculate)

		self.calculate_button = wx.Button(panel, label=_("Calculate"))
		self.calculate_button.SetName(_("Calculate"))
		self.calculate_button.Bind(wx.EVT_BUTTON, self._on_calculate)

		input_row = wx.BoxSizer(wx.HORIZONTAL)
		input_row.Add(
			self.expression_input,
			wx.SizerFlags(1).Expand().Border(wx.RIGHT, 8),
		)
		input_row.Add(self.calculate_button, wx.SizerFlags(0))

		result_label = wx.StaticText(panel, label=_("Result"))
		self.result_output = KeyboardFocusableReadOnlyTextCtrl(panel)
		self.result_output.SetName(_("Result output"))
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

	def _announce(self, message: str) -> None:
		"""Report a minor, non-interrupting status update.

		Shown both in the status bar and in an ``InfoBar`` banner, since a
		plain status bar text change is not reliably discovered by screen
		readers (it is not a keyboard tab stop and is not announced
		proactively). Focus is left untouched, so this is for confirmations
		that do not require the user's attention right away.
		"""

		self.SetStatusText(message)
		self.info_bar.ShowMessage(message, wx.ICON_INFORMATION)

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
			status_text = _("Calculation complete.")
		else:
			assert outcome.error is not None
			output_text = format_error_for_display(outcome.error)
			status_text = _("Calculation failed.")

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
		self._announce(status)
		event.Skip(False)

	def _on_language_choice(
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
		dialog = wx.MessageDialog(
			self,
			status,
			_("Language Changed"),
			wx.OK | wx.ICON_INFORMATION,
		)
		try:
			dialog.ShowModal()
		finally:
			dialog.Destroy()
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
		self._announce(
			_("Decimal precision: {precision}.").format(precision=precision)
		)
		event.Skip(False)

	def _on_error_sound(self, event: wx.CommandEvent) -> None:
		self.settings = replace(
			self.settings,
			play_error_sound=event.IsChecked(),
		)
		self._sync_options_menu()
		self._save_settings()
		state = _("on") if self.settings.play_error_sound else _("off")
		self._announce(_("Error sound: {state}.").format(state=state))
		event.Skip(False)

	def _on_restore_defaults(self, event: wx.Event) -> None:
		dialog = wx.MessageDialog(
			self,
			_("Restore all calculation options to their default values?"),
			_("Restore Defaults"),
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
			self._announce(_("Default options restored."))
		event.Skip(False)

	def _save_settings(self) -> None:
		try:
			self.settings_store.save(self.settings)
		except SettingsSaveError:
			self._show_warning(
				_(
					"The options are active for this session but could not "
					"be saved."
				)
			)

	def _finish_startup(self, warning: str | None) -> None:
		if warning:
			self._show_warning(warning)
		self.expression_input.SetFocus()

	def _show_warning(self, message: str) -> None:
		dialog = wx.MessageDialog(
			self,
			message,
			_("Powercalc Settings"),
			wx.OK | wx.ICON_WARNING,
		)
		try:
			dialog.ShowModal()
		finally:
			dialog.Destroy()

	def _on_clear_input(self, event: wx.Event) -> None:
		self.expression_input.Clear()
		self.expression_input.SetFocus()
		self._announce(_("Input cleared."))
		event.Skip(False)

	def _on_copy_result(self, event: wx.Event) -> None:
		text = self.result_output.GetValue()
		if not text:
			self._announce(_("No result to copy."))
			event.Skip(False)
			return

		if not wx.TheClipboard.Open():
			self._announce(_("Clipboard is not available."))
			event.Skip(False)
			return

		try:
			wx.TheClipboard.SetData(wx.TextDataObject(text))
			self._announce(_("Result copied."))
		finally:
			wx.TheClipboard.Close()
		event.Skip(False)

	def _on_function_index(self, event: wx.Event) -> None:
		dialog = FunctionIndexDialog(
			self,
			FUNCTION_CATALOG,
			self.settings.decimal_separator,
		)
		try:
			if dialog.ShowModal() != wx.ID_OK:
				event.Skip(False)
				return
			entry = dialog.get_selected_entry()
		finally:
			dialog.Destroy()

		if entry is None:
			event.Skip(False)
			return
		self._insert_catalog_entry(entry)
		event.Skip(False)

	def _insert_catalog_entry(self, entry: CatalogEntry) -> None:
		text, start, end = build_insertion(
			entry, self.settings.decimal_separator
		)
		insertion_point = self.expression_input.GetInsertionPoint()
		self.expression_input.WriteText(text)
		if start == end:
			self.expression_input.SetInsertionPoint(insertion_point + start)
		else:
			self.expression_input.SetSelection(
				insertion_point + start, insertion_point + end
			)
		self.expression_input.SetFocus()
		self._announce(
			_("Inserted {name}.").format(name=entry.display_name)
		)

	def _on_keyboard_help(self, event: wx.Event) -> None:
		dialog = wx.MessageDialog(
			self,
			KEYBOARD_HELP,
			_("Keyboard Commands"),
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
			_(
				"Powercalc {version}\n\n"
				"Accessible desktop calculator.\n"
				"Updates are available from GitHub Releases."
			).format(version=get_version()),
			_("About Powercalc"),
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
