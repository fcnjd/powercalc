import json
from pathlib import Path

import pytest

from powercalc.settings import (
	AppSettings,
	PORTABLE_MARKER_NAME,
	SettingsSaveError,
	SettingsStore,
	get_settings_path,
)


def test_settings_round_trip(tmp_path):
	path = tmp_path / "settings.json"
	store = SettingsStore(path)
	settings = AppSettings(
		decimal_precision=40,
		decimal_separator="comma",
		number_domain="real",
		log_mode="natural",
		angle_unit="degree",
		play_error_sound=False,
	)

	store.save(settings)
	loaded = store.load()

	assert loaded.settings == settings
	assert loaded.warning is None
	assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == 1


def test_missing_settings_use_defaults_without_creating_file(tmp_path):
	path = tmp_path / "settings.json"

	loaded = SettingsStore(path).load()

	assert loaded.settings == AppSettings()
	assert loaded.warning is None
	assert not path.exists()


def test_invalid_values_are_replaced_field_by_field(tmp_path):
	path = tmp_path / "settings.json"
	path.write_text(
		json.dumps(
			{
				"schema_version": 1,
				"calculation": {
					"angle_unit": "degree",
					"decimal_separator": "invalid",
					"number_domain": "real",
					"log_mode": "natural",
					"decimal_precision": 101,
				},
				"accessibility": {"play_error_sound": False},
			}
		),
		encoding="utf-8",
	)

	loaded = SettingsStore(path).load()

	assert loaded.warning is not None
	assert loaded.settings.angle_unit == "degree"
	assert loaded.settings.decimal_separator == "point"
	assert loaded.settings.number_domain == "real"
	assert loaded.settings.decimal_precision == 12
	assert loaded.settings.play_error_sound is False
	assert (
		json.loads(path.read_text(encoding="utf-8"))["calculation"][
			"decimal_separator"
		]
		== "point"
	)


def test_invalid_json_is_backed_up_and_repaired(tmp_path):
	path = tmp_path / "settings.json"
	path.write_text("not json", encoding="utf-8")

	loaded = SettingsStore(path).load()

	assert loaded.settings == AppSettings()
	assert loaded.warning is not None
	assert list(tmp_path.glob("settings.invalid-*.json"))
	assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == 1


def test_evaluation_options_reflect_application_settings():
	settings = AppSettings(
		decimal_precision=25,
		decimal_separator="comma",
		number_domain="real",
		log_mode="natural",
		angle_unit="gradian",
	)

	options = settings.evaluation_options()

	assert options.decimal_precision == 25
	assert options.decimal_separator == "comma"
	assert options.number_domain == "real"
	assert options.log_mode == "natural"
	assert options.angle_unit == "gradian"


def test_portable_marker_selects_settings_beside_executable(
	tmp_path,
	monkeypatch,
):
	executable = tmp_path / "Powercalc.exe"
	(tmp_path / PORTABLE_MARKER_NAME).write_text("{}\n", encoding="utf-8")
	monkeypatch.setattr("powercalc.settings.sys.frozen", True, raising=False)
	monkeypatch.setattr("powercalc.settings.sys.executable", str(executable))

	assert get_settings_path() == tmp_path / "settings.json"


def test_non_portable_run_uses_platform_config_path(tmp_path, monkeypatch):
	monkeypatch.delattr("powercalc.settings.sys.frozen", raising=False)
	monkeypatch.setattr(
		"powercalc.settings.user_config_path",
		lambda *args, **kwargs: tmp_path,
	)

	assert get_settings_path() == tmp_path / "settings.json"


def test_save_error_has_understandable_message(tmp_path, monkeypatch):
	store = SettingsStore(tmp_path / "settings.json")
	monkeypatch.setattr(
		"powercalc.settings.os.replace",
		lambda *args: (_ for _ in ()).throw(OSError("denied")),
	)

	with pytest.raises(SettingsSaveError, match="could not be saved"):
		store.save(AppSettings())


def test_settings_path_type_is_path(tmp_path):
	assert isinstance(SettingsStore(tmp_path / "settings.json").path, Path)
