#!/usr/bin/env python

import wx
import i18n

class CalculatorView(wx.Frame):
	def __init__(self, parent, title):
		super().__init__(parent, title=title, size=(600, 400))
		self.current_language = i18n.get_language()
		self.index_provider = None
		self._build_ui()
		self.Centre()
		self.Show()

	def _build_ui(self):
		self.create_menu_bar()

		panel = wx.Panel(self, style=wx.TAB_TRAVERSAL)
		main_sizer = wx.BoxSizer(wx.VERTICAL)

		input_label = wx.StaticText(panel, label=i18n.translate('input_label'))
		self.input_ctrl = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
		self.input_ctrl.SetName("input_field")
		self.input_ctrl.SetToolTip(i18n.translate('input_label') + " für mathematische Ausdrücke")

		output_label = wx.StaticText(panel, label=i18n.translate('output_label'))
		self.output_ctrl = wx.TextCtrl(panel, style=wx.TE_READONLY)
		self.output_ctrl.AcceptsFocusFromKeyboard=lambda: True
		self.output_ctrl.SetName("output_field")
		self.output_ctrl.SetToolTip(i18n.translate('output_label'))

		main_sizer.Add(input_label, 0, wx.ALL, 5)
		main_sizer.Add(self.input_ctrl, 0, wx.EXPAND | wx.ALL, 5)
		main_sizer.Add(output_label, 0, wx.ALL, 5)
		main_sizer.Add(self.output_ctrl, 0, wx.EXPAND | wx.ALL, 5)

		panel.SetSizer(main_sizer)

		accel_entries = []
		accel_entries.append((wx.ACCEL_CTRL, ord('I'), wx.NewIdRef()))
		accel_entries.append((wx.ACCEL_CTRL, ord('O'), wx.NewIdRef()))
		accel_entries.append((wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord('X'), wx.NewIdRef()))

		accel_table = wx.AcceleratorTable([
			(wx.ACCEL_CTRL, ord('I'), accel_entries[0][2]),
			(wx.ACCEL_CTRL, ord('O'), accel_entries[1][2]),
			(wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord('X'), accel_entries[2][2])
		])
		self.SetAcceleratorTable(accel_table)

		self.Bind(wx.EVT_MENU, self.on_accel_focus_input, id=accel_entries[0][2])
		self.Bind(wx.EVT_MENU, self.on_accel_focus_output, id=accel_entries[1][2])
		self.Bind(wx.EVT_MENU, self.on_accel_show_index, id=accel_entries[2][2])

		self.input_ctrl.SetFocus()

	def create_menu_bar(self):
		menu_bar = wx.MenuBar()

		file_menu = wx.Menu()
		exit_item = file_menu.Append(wx.ID_EXIT, i18n.translate('menu_exit'))
		self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
		menu_bar.Append(file_menu, i18n.translate('menu_file'))

		language_menu = wx.Menu()
		english_item = language_menu.Append(wx.ID_ANY, i18n.translate('menu_english'))
		german_item = language_menu.Append(wx.ID_ANY, i18n.translate('menu_german'))
		self.Bind(wx.EVT_MENU, self.on_set_english, english_item)
		self.Bind(wx.EVT_MENU, self.on_set_german, german_item)
		menu_bar.Append(language_menu, i18n.translate('menu_language'))

		self.SetMenuBar(menu_bar)

	def on_exit(self, event):
		self.Close()

	def on_set_english(self, event):
		self.current_language = 'en'
		i18n.set_language('en')
		self.update_language()

	def on_set_german(self, event):
		self.current_language = 'de'
		i18n.set_language('de')
		self.update_language()

	def update_language(self):
		self.SetTitle(i18n.translate('title'))
		menu_bar = self.GetMenuBar()
		if menu_bar:
			file_menu = menu_bar.GetMenu(0)
			file_menu.SetLabel(i18n.translate('menu_file'))
			exit_item = file_menu.FindItemById(wx.ID_EXIT)
			exit_item.SetItemLabel(i18n.translate('menu_exit'))
			language_menu = menu_bar.GetMenu(1)
			language_menu.SetLabel(i18n.translate('menu_language'))
			language_menu.FindItemByPosition(0).SetItemLabel(i18n.translate('menu_english'))
			language_menu.FindItemByPosition(1).SetItemLabel(i18n.translate('menu_german'))
		children = self.GetChildren()[0].GetChildren()
		if len(children) >= 4:
			children[0].SetLabel(i18n.translate('input_label'))
			children[2].SetLabel(i18n.translate('output_label'))
		self.input_ctrl.SetToolTip(i18n.translate('input_label') + " für mathematische Ausdrücke")
		self.output_ctrl.SetToolTip(i18n.translate('output_label'))
		self.Layout()

	def on_accel_focus_input(self, event):
		self.input_ctrl.SetFocus()

	def on_accel_focus_output(self, event):
		self.output_ctrl.SetFocus()

	def on_accel_show_index(self, event):
		self.show_index_dialog()

	def show_index_dialog(self, index_items=None):
		if index_items is None:
			if self.index_provider is not None:
				index_items = self.index_provider()
			else:
				index_items = []
		dlg = IndexDialog(self, index_items)
		dlg.ShowModal()
		selected_item = dlg.GetStringSelection()
		if selected_item:
			pos = self.input_ctrl.GetInsertionPoint()
			current_text = self.input_ctrl.GetValue()
			new_text = current_text[:pos] + selected_item + current_text[pos:]
			self.input_ctrl.ChangeValue(new_text)
			self.input_ctrl.SetFocus()
			self.input_ctrl.SetInsertionPoint(pos + len(selected_item))

	def get_input(self):
		return self.input_ctrl.GetValue()

	def set_output(self, text):
		self.output_ctrl.SetValue(str(text))

	def bind_expression_enter(self, callback):
		self.input_ctrl.Bind(wx.EVT_TEXT_ENTER, callback)

	def set_index_provider(self, provider_callable):
		"""Ermöglicht dem Controller, eine Funktion anzugeben, über die der Index
		   abgefragt werden kann (z. B. model.get_index_items)."""
		self.index_provider = provider_callable


class IndexDialog(wx.SingleChoiceDialog):
	def __init__(self, parent, index_items):
		super().__init__(parent, i18n.translate('index_title'), i18n.translate('index_message'), index_items)
		self.SetName("index_dialog")
