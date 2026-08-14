"""Application settings and JSON persistence for Powercalc."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import TYPE_CHECKING, Literal

from platformdirs import user_config_path

if TYPE_CHECKING:
	from powercalc.core import EvaluationOptions


AngleUnit = Literal["radian", "degree", "gradian"]
AppLanguage = Literal["system", "en", "de"]
DecimalSeparator = Literal["point", "comma"]
LogMode = Literal["calculator", "natural"]
NumberDomain = Literal["complex", "real"]

SETTINGS_FILE_NAME = "settings.json"
PORTABLE_MARKER_NAME = "portable.json"
SETTINGS_SCHEMA_VERSION = 1


class SettingsSaveError(RuntimeError):
	"""Raised when settings cannot be saved persistently."""


@dataclass(frozen=True)
class AppSettings:
	"""User-configurable calculation and accessibility settings."""

	decimal_precision: int = 12
	decimal_separator: DecimalSeparator = "point"
	number_domain: NumberDomain = "complex"
	log_mode: LogMode = "calculator"
	angle_unit: AngleUnit = "radian"
	play_error_sound: bool = True
	language: AppLanguage = "system"

	def evaluation_options(self) -> EvaluationOptions:
		"""Return the calculation-core options represented by these settings."""

		from powercalc.core import EvaluationOptions

		return EvaluationOptions(
			decimal_precision=self.decimal_precision,
			decimal_separator=self.decimal_separator,
			number_domain=self.number_domain,
			log_mode=self.log_mode,
			angle_unit=self.angle_unit,
		)


@dataclass(frozen=True)
class SettingsLoadResult:
	"""Settings loaded for a session and an optional user-facing warning."""

	settings: AppSettings
	warning: str | None = None


def get_settings_path() -> Path:
	"""Return the settings path for the current installed or portable run."""

	if getattr(sys, "frozen", False):
		executable_dir = Path(sys.executable).resolve().parent
		if (executable_dir / PORTABLE_MARKER_NAME).is_file():
			return executable_dir / SETTINGS_FILE_NAME

	return user_config_path("Powercalc", appauthor=False) / SETTINGS_FILE_NAME


class SettingsStore:
	"""Load and atomically save application settings at a fixed path."""

	def __init__(self, path: Path | None = None) -> None:
		self.path = path or get_settings_path()

	def load(self) -> SettingsLoadResult:
		"""Load settings, repairing invalid data where possible."""

		defaults = AppSettings()
		if not self.path.exists():
			return SettingsLoadResult(defaults)

		try:
			data = json.loads(self.path.read_text(encoding="utf-8"))
		except (OSError, UnicodeError, json.JSONDecodeError):
			return self._repair_broken_file(defaults)

		if (
			not isinstance(data, dict)
			or data.get("schema_version", SETTINGS_SCHEMA_VERSION)
			!= SETTINGS_SCHEMA_VERSION
		):
			return self._repair_broken_file(defaults)

		settings, had_invalid_values = _settings_from_data(data)
		if not had_invalid_values:
			return SettingsLoadResult(settings)

		warning = (
			"Some settings were invalid and were replaced with default values."
		)
		try:
			self.save(settings)
		except SettingsSaveError:
			warning += " The repaired settings could not be saved."
		return SettingsLoadResult(settings, warning)

	def save(self, settings: AppSettings) -> None:
		"""Atomically save settings as readable UTF-8 JSON."""

		payload = (
			json.dumps(
				_settings_to_data(settings),
				indent=2,
				ensure_ascii=False,
			)
			+ "\n"
		)
		temporary_path: Path | None = None
		try:
			self.path.parent.mkdir(parents=True, exist_ok=True)
			with tempfile.NamedTemporaryFile(
				"w",
				encoding="utf-8",
				dir=self.path.parent,
				prefix=f".{self.path.name}.",
				suffix=".tmp",
				delete=False,
				newline="\n",
			) as temporary_file:
				temporary_file.write(payload)
				temporary_file.flush()
				os.fsync(temporary_file.fileno())
				temporary_path = Path(temporary_file.name)
			os.replace(temporary_path, self.path)
		except OSError as exc:
			if temporary_path is not None:
				try:
					temporary_path.unlink(missing_ok=True)
				except OSError:
					pass
			raise SettingsSaveError("Settings could not be saved.") from exc

	def _repair_broken_file(
		self,
		settings: AppSettings,
	) -> SettingsLoadResult:
		timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
		backup_path = self.path.with_name(f"settings.invalid-{timestamp}.json")
		warning = (
			"The settings file could not be read. Default settings are in use."
		)
		try:
			os.replace(self.path, backup_path)
			self.save(settings)
		except (OSError, SettingsSaveError):
			warning += " The settings file could not be repaired."
		else:
			warning += f" The original file was saved as {backup_path.name}."
		return SettingsLoadResult(settings, warning)


def _settings_to_data(settings: AppSettings) -> dict[str, object]:
	return {
		"schema_version": SETTINGS_SCHEMA_VERSION,
		"calculation": {
			"angle_unit": settings.angle_unit,
			"decimal_separator": settings.decimal_separator,
			"number_domain": settings.number_domain,
			"log_mode": settings.log_mode,
			"decimal_precision": settings.decimal_precision,
		},
		"accessibility": {
			"play_error_sound": settings.play_error_sound,
		},
		"localization": {
			"language": settings.language,
		},
	}


def _settings_from_data(data: dict[str, object]) -> tuple[AppSettings, bool]:
	defaults = AppSettings()
	calculation = data.get("calculation", {})
	accessibility = data.get("accessibility", {})
	localization = data.get("localization", {})
	invalid = False
	if not isinstance(calculation, dict):
		calculation = {}
		invalid = True
	if not isinstance(accessibility, dict):
		accessibility = {}
		invalid = True
	if not isinstance(localization, dict):
		localization = {}
		invalid = True

	angle_unit, was_invalid = _choice_value(
		calculation,
		"angle_unit",
		defaults.angle_unit,
		{"radian", "degree", "gradian"},
	)
	invalid |= was_invalid
	decimal_separator, was_invalid = _choice_value(
		calculation,
		"decimal_separator",
		defaults.decimal_separator,
		{"point", "comma"},
	)
	invalid |= was_invalid
	number_domain, was_invalid = _choice_value(
		calculation,
		"number_domain",
		defaults.number_domain,
		{"complex", "real"},
	)
	invalid |= was_invalid
	log_mode, was_invalid = _choice_value(
		calculation,
		"log_mode",
		defaults.log_mode,
		{"calculator", "natural"},
	)
	invalid |= was_invalid
	language, was_invalid = _choice_value(
		localization,
		"language",
		defaults.language,
		{"system", "en", "de"},
	)
	invalid |= was_invalid

	precision = calculation.get(
		"decimal_precision",
		defaults.decimal_precision,
	)
	if (
		isinstance(precision, bool)
		or not isinstance(precision, int)
		or not 1 <= precision <= 100
	):
		precision = defaults.decimal_precision
		invalid = True

	play_error_sound = accessibility.get(
		"play_error_sound",
		defaults.play_error_sound,
	)
	if not isinstance(play_error_sound, bool):
		play_error_sound = defaults.play_error_sound
		invalid = True

	return (
		AppSettings(
			decimal_precision=precision,
			decimal_separator=decimal_separator,
			number_domain=number_domain,
			log_mode=log_mode,
			angle_unit=angle_unit,
			play_error_sound=play_error_sound,
			language=language,
		),
		invalid,
	)


def _choice_value(
	data: dict[str, object],
	key: str,
	default: str,
	allowed: set[str],
) -> tuple[str, bool]:
	value = data.get(key, default)
	if isinstance(value, str) and value in allowed:
		return value, False
	return default, True
