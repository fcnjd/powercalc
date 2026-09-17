"""Prepare the pinned official Liblouis runtime for Windows bundles."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path, PurePosixPath
from urllib.request import urlretrieve
from zipfile import ZipFile

LIBLOUIS_VERSION = "3.39.0"
WINDOWS_X64_URL = (
	"https://github.com/liblouis/liblouis/releases/download/"
	f"v{LIBLOUIS_VERSION}/liblouis-{LIBLOUIS_VERSION}-win64.zip"
)
WINDOWS_X64_SHA256 = (
	"64d669ac30f1411e0023b1cecc81c7a7b5374678ee41302c95ac8c7c8fbc6591"
)
LICENSE_URL = (
	"https://raw.githubusercontent.com/liblouis/liblouis/"
	f"v{LIBLOUIS_VERSION}/COPYING.LESSER"
)
LICENSE_SHA256 = (
	"dc626520dcd53a22f727af3ee42c770e56c97a64fe3adb063799d8ab032fe551"
)
RUNTIME_LIBRARY_MEMBER = "bin/liblouis.dll"
TABLE_ROOT = "share/liblouis/tables"
GERMAN_GRADE_1_TABLE = "de-g1.ctb"
UNICODE_DISPLAY_TABLE = "unicode.dis"


class LiblouisBuildError(RuntimeError):
	"""Raised when the official Liblouis runtime cannot be prepared."""


def download_windows_x64_release(download_path: Path) -> Path:
	"""Download the pinned official release and verify its checksum."""

	download_path.parent.mkdir(parents=True, exist_ok=True)
	if not download_path.exists():
		urlretrieve(WINDOWS_X64_URL, download_path)
	verify_sha256(download_path, WINDOWS_X64_SHA256)
	return download_path


def verify_sha256(archive_path: Path, expected: str) -> None:
	"""Raise if an archive does not match its pinned SHA-256 digest."""

	digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
	if digest != expected:
		raise LiblouisBuildError(
			"Liblouis archive checksum mismatch: "
			f"expected {expected}, got {digest}."
		)


def prepare_windows_x64_runtime(
	archive_path: Path,
	destination: Path,
) -> Path:
	"""Extract the DLL and only tables needed by German Grade 1 Braille."""

	if destination.exists():
		shutil.rmtree(destination)
	destination.mkdir(parents=True)

	license_path = destination / "licenses" / "LGPL-2.1-or-later.txt"
	download_pinned_license(license_path)

	with ZipFile(archive_path) as archive:
		_extract_member(
			archive, RUNTIME_LIBRARY_MEMBER, destination / "liblouis.dll"
		)
		table_names = _required_tables(
			archive, GERMAN_GRADE_1_TABLE, UNICODE_DISPLAY_TABLE
		)
		for table_name in table_names:
			_extract_member(
				archive,
				f"{TABLE_ROOT}/{table_name}",
				destination / "share" / "liblouis" / "tables" / table_name,
			)
	_write_third_party_notice(destination, table_names)
	return destination


def download_pinned_license(license_path: Path) -> Path:
	"""Fetch Liblouis' LGPL text from the pinned release tag and verify it."""

	license_path.parent.mkdir(parents=True, exist_ok=True)
	if not license_path.exists():
		urlretrieve(LICENSE_URL, license_path)
	verify_sha256(license_path, LICENSE_SHA256)
	return license_path


def _required_tables(archive: ZipFile, *root_tables: str) -> list[str]:
	"""Return an include-complete table list rooted at ``root_tables``."""

	seen: set[str] = set()
	pending = list(root_tables)
	while pending:
		table_name = pending.pop()
		if table_name in seen:
			continue
		_validate_table_name(table_name)
		member = f"{TABLE_ROOT}/{table_name}"
		try:
			content = archive.read(member).decode("utf-8")
		except KeyError as exc:
			raise LiblouisBuildError(
				f"Liblouis release is missing required table {table_name!r}."
			) from exc
		seen.add(table_name)
		for line in content.splitlines():
			parts = line.strip().split(maxsplit=1)
			if len(parts) == 2 and parts[0] == "include":
				pending.append(parts[1])
	return sorted(seen)


def _extract_member(archive: ZipFile, member: str, destination: Path) -> None:
	try:
		content = archive.read(member)
	except KeyError as exc:
		raise LiblouisBuildError(
			f"Liblouis release is missing required member {member!r}."
		) from exc
	destination.parent.mkdir(parents=True, exist_ok=True)
	destination.write_bytes(content)


def _write_third_party_notice(
	destination: Path, table_names: list[str]
) -> None:
	"""Write the attribution that ships alongside the bundled runtime."""

	table_list = "\n".join(f"- `{table_name}`" for table_name in table_names)
	(destination / "THIRD_PARTY_NOTICES.md").write_text(
		"# Third-party notices\n\n"
		"## Liblouis\n\n"
		f"Powercalc bundles Liblouis {LIBLOUIS_VERSION} for German Grade 1 "
		"Braille translation on Windows.\n\n"
		f"- Runtime source: {WINDOWS_X64_URL}\n"
		f"- Runtime SHA-256: `{WINDOWS_X64_SHA256}`\n"
		f"- License text source: {LICENSE_URL}\n"
		f"- License text SHA-256: `{LICENSE_SHA256}`\n"
		"- License: GNU Lesser General Public License, version 2.1 or later; "
		"see `licenses/LGPL-2.1-or-later.txt`.\n\n"
		"Bundled Liblouis translation tables:\n"
		f"{table_list}\n",
		encoding="utf-8",
	)


def _validate_table_name(table_name: str) -> None:
	path = PurePosixPath(table_name)
	if path.is_absolute() or ".." in path.parts:
		raise LiblouisBuildError(
			f"Unsafe Liblouis table reference {table_name!r}."
		)
