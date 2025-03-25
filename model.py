#!/usr/bin/env python

import sympy as sp

class CalculatorModel:
	def __init__(self):
		self.index_items = ['sin()', 'cos()', 'tan()', 'log()', 'exp()', 'sqrt()']

	def add_index_item(self, item):
		if item not in self.index_items:
			self.index_items.append(item)

	def get_index_items(self):
		return self.index_items[:]

	def evaluate_expression(self, expression):
		try:
			result = sp.sympify(expression)
			return result
		except sp.SympifyError as e:
			return f"Error: {str(e)}"


