from tools.build import artifact_name
from tools.release_notes import extract_release_notes


def test_windows_artifact_names_include_version_and_platform(monkeypatch):
	monkeypatch.setattr(
		"tools.build.current_platform_tag",
		lambda: "windows-x64",
	)

	assert (
		artifact_name("portable.zip")
		== "Powercalc-0.2.0-beta.1-windows-x64-portable.zip"
	)
	assert (
		artifact_name("setup") == "Powercalc-0.2.0-beta.1-windows-x64-setup.exe"
	)


def test_changelog_notes_can_be_extracted_for_current_beta():
	notes = extract_release_notes("0.2.0-beta.1")

	assert "Portable ZIP" in notes
	assert "SmartScreen" in notes
