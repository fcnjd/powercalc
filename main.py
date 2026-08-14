def main() -> int:
	from powercalc.i18n import install_translation, resolve_startup_language
	from powercalc.settings import SettingsStore

	settings_store = SettingsStore()
	loaded_settings = settings_store.load()
	language = resolve_startup_language(loaded_settings.settings.language)
	install_translation(language)

	from powercalc.gui import run

	return run(settings_store, loaded_settings, language)


if __name__ == "__main__":
	raise SystemExit(main())
