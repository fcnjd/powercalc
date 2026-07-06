import powercalc.gui


def test_gui_package_exports_callable_run_function():
	assert callable(powercalc.gui.run)
