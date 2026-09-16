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
RUNTIME_LIBRARY_MEMBER = "bin/liblouis.dll"
TABLE_ROOT = "share/liblouis/tables"
GERMAN_GRADE_1_TABLE = "de-g1.ctb"


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

	with ZipFile(archive_path) as archive:
		_extract_member(
			archive, RUNTIME_LIBRARY_MEMBER, destination / "liblouis.dll"
		)
		for table_name in _required_tables(archive, GERMAN_GRADE_1_TABLE):
			_extract_member(
				archive,
				f"{TABLE_ROOT}/{table_name}",
				destination / "share" / "liblouis" / "tables" / table_name,
			)
	return destination


def _required_tables(archive: ZipFile, root_table: str) -> list[str]:
	"""Return a stable, include-complete table list rooted at ``root_table``."""

	seen: set[str] = set()
	pending = [root_table]
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


def _validate_table_name(table_name: str) -> None:
	path = PurePosixPath(table_name)
	if path.is_absolute() or ".." in path.parts:
		raise LiblouisBuildError(
			f"Unsafe Liblouis table reference {table_name!r}."
		)
