from powercalc.gui.resources import get_app_icon_path


def test_app_icon_path_exists_in_source_tree():
	icon_path = get_app_icon_path()

	assert icon_path is not None
	assert icon_path.name == "powercalc.ico"
	assert icon_path.exists()
