from hashlib import sha256
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from tools.liblouis import (
	LiblouisBuildError,
	prepare_windows_x64_runtime,
	verify_sha256,
)


def _write_release_archive(archive_path: Path) -> None:
	with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
		archive.writestr("bin/liblouis.dll", b"official DLL")
		archive.writestr(
			"share/liblouis/tables/de-g1.ctb",
			"include de-g0.utb\ninclude de-g1-core.cti\n",
		)
		archive.writestr(
			"share/liblouis/tables/de-g0.utb",
			"include de-chardefs6.cti\n",
		)
		archive.writestr("share/liblouis/tables/de-g1-core.cti", "")
		archive.writestr("share/liblouis/tables/de-chardefs6.cti", "")
		archive.writestr("share/liblouis/tables/unicode.dis", "")


def test_prepare_windows_runtime_extracts_dll_and_transitive_tables(
	tmp_path: Path,
):
	archive_path = tmp_path / "liblouis.zip"
	_write_release_archive(archive_path)

	runtime_path = prepare_windows_x64_runtime(
		archive_path,
		tmp_path / "runtime",
	)

	assert (runtime_path / "liblouis.dll").read_bytes() == b"official DLL"
	table_root = runtime_path / "share" / "liblouis" / "tables"
	assert (table_root / "de-g1.ctb").exists()
	assert (table_root / "de-g0.utb").exists()
	assert (table_root / "de-g1-core.cti").exists()
	assert (table_root / "de-chardefs6.cti").exists()
	assert (table_root / "unicode.dis").exists()


def test_prepare_windows_runtime_rejects_missing_included_table(tmp_path: Path):
	archive_path = tmp_path / "liblouis.zip"
	with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
		archive.writestr("bin/liblouis.dll", b"official DLL")
		archive.writestr(
			"share/liblouis/tables/de-g1.ctb",
			"include missing.cti\n",
		)

	with pytest.raises(LiblouisBuildError, match="missing required table"):
		prepare_windows_x64_runtime(archive_path, tmp_path / "runtime")


def test_verify_sha256_rejects_tampered_archive(tmp_path: Path):
	archive_path = tmp_path / "liblouis.zip"
	archive_path.write_bytes(b"untrusted")

	with pytest.raises(LiblouisBuildError, match="checksum mismatch"):
		verify_sha256(archive_path, sha256(b"official").hexdigest())
