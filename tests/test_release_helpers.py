from zipfile import ZipFile

import pytest

from powercalc.version import get_version
from tools.build import artifact_name, write_portable_archive
from tools.release_notes import (
	extract_release_notes,
	extract_release_notes_from_text,
)


def test_windows_artifact_names_include_version_and_platform(monkeypatch):
	monkeypatch.setattr(
		"tools.build.current_platform_tag",
		lambda: "windows-x64",
	)

	assert (
		artifact_name("portable.zip")
		== "Powercalc-0.3.0-beta.1-windows-x64-portable.zip"
	)
	assert (
		artifact_name("setup") == "Powercalc-0.3.0-beta.1-windows-x64-setup.exe"
	)


def test_extract_release_notes_from_text_returns_matching_section():
	changelog = (
		"# Changelog\n\n"
		"## [0.2.0]\n\n"
		"### Added\n\n- Newer feature.\n\n"
		"## [0.1.0]\n\n"
		"### Added\n\n- Older feature.\n"
	)

	notes = extract_release_notes_from_text(changelog, "0.2.0")

	assert notes == "### Added\n\n- Newer feature.\n"


def test_extract_release_notes_from_text_raises_for_missing_version():
	changelog = "## [0.1.0] - 2025-12-01\n\n- Older feature.\n"

	with pytest.raises(ValueError, match="no section for 0.9.0"):
		extract_release_notes_from_text(changelog, "0.9.0")


def test_extract_release_notes_from_text_raises_for_empty_section():
	changelog = "## [0.2.0]\n\n## [0.1.0]\n\n- Older.\n"

	with pytest.raises(ValueError, match="empty"):
		extract_release_notes_from_text(changelog, "0.2.0")


def test_current_beta_release_notes_disclose_smartscreen_warning():
	# Per AGENTS.md, unsigned beta builds must keep the SmartScreen warning
	# clear in the release notes until code signing is introduced.
	notes = extract_release_notes(get_version())

	assert "SmartScreen" in notes


def test_portable_archive_contains_mode_marker(tmp_path):
	bundle_path = tmp_path / "bundle"
	bundle_path.mkdir()
	(bundle_path / "Powercalc.exe").write_bytes(b"application")
	zip_path = tmp_path / "portable.zip"

	write_portable_archive(bundle_path, zip_path)

	with ZipFile(zip_path) as archive:
		assert archive.read("Powercalc/portable.json") == b"{}\n"
		assert archive.read("Powercalc/Powercalc.exe") == b"application"
