#!/usr/bin/env python

import wx
import i18n

class CalculatorController:
	def __init__(self, model_instance, view_instance):
		self.model = model_instance
		self.view = view_instance
		self.view.set_index_provider(self.model.get_index_items)
		self.view.bind_expression_enter(self.on_expression_enter)

	def on_expression_enter(self, event):
		expression = self.view.get_input()
		result = self.model.evaluate_expression(expression)
		self.view.set_output(result)
		self.view.output_ctrl.SetFocus()
		self.view.output_ctrl.SetInsertionPointEnd()
