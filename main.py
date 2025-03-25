#!/usr/bin/env python

import wx
from view import CalculatorView
from controller import CalculatorController
from model import CalculatorModel
import i18n

def main():
	i18n.set_language('de')
	app = wx.App(False)
	frame = CalculatorView(None, title=i18n.translate('title'))
	model_instance = CalculatorModel()
	CalculatorController(model_instance, frame)
	app.MainLoop()

if __name__ == '__main__':
	main()


