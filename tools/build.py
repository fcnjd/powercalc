"""Build release artifacts for Powercalc.

Run with ``uv run python -m tools.build portable`` or
``uv run python -m tools.build all``.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tomllib
import zipfile

from powercalc.version import get_version
from powercalc.settings import PORTABLE_MARKER_NAME


APP_NAME = "Powercalc"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILD_ROOT = PROJECT_ROOT / "build"
DIST_ROOT = PROJECT_ROOT / "dist"
RELEASE_ROOT = DIST_ROOT / "release"
ICON_PATH = PROJECT_ROOT / "assets" / "powercalc.ico"
INNO_SCRIPT = PROJECT_ROOT / "installer" / "powercalc.iss"


class BuildError(RuntimeError):
	"""Raised when a release artifact cannot be built."""


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument(
		"target",
		choices=("bundle", "portable", "installer", "checksums", "all"),
		help="Artifact target to build.",
	)
	args = parser.parse_args()

	try:
		run_target(args.target)
	except BuildError as exc:
		print(f"Build failed: {exc}", file=sys.stderr)
		return 1
	return 0


def run_target(target: str) -> None:
	validate_version_metadata()
	RELEASE_ROOT.mkdir(parents=True, exist_ok=True)

	if target == "bundle":
		build_pyinstaller_bundle()
	elif target == "portable":
		build_portable_zip()
	elif target == "installer":
		build_installer()
	elif target == "checksums":
		write_checksums()
	elif target == "all":
		build_portable_zip()
		build_installer()
		write_checksums()
	else:
		raise BuildError(f"Unknown target: {target}")


def validate_version_metadata() -> None:
	pyproject = tomllib.loads(
		(PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
	)
	project_version = pyproject["project"]["version"]
	runtime_version = get_version()
	if project_version != runtime_version:
		raise BuildError(
			"Version mismatch: pyproject.toml has "
			f"{project_version!r}, runtime has {runtime_version!r}."
		)


def build_pyinstaller_bundle() -> Path:
	if not ICON_PATH.exists():
		raise BuildError(f"Missing Windows icon: {ICON_PATH}")

	bundle_path = get_bundle_path()
	remove_path(bundle_path)

	command = [
		sys.executable,
		"-m",
		"PyInstaller",
		"--noconfirm",
		"--clean",
		"--windowed",
		"--name",
		APP_NAME,
		"--icon",
		str(ICON_PATH),
		"--add-data",
		f"{ICON_PATH}{os.pathsep}assets",
		"--exclude-module",
		"pytest",
		"--exclude-module",
		"ruff",
		"--exclude-module",
		"pygments",
		"--distpath",
		str(DIST_ROOT),
		"--workpath",
		str(BUILD_ROOT / "pyinstaller"),
		"--specpath",
		str(BUILD_ROOT / "pyinstaller"),
		str(PROJECT_ROOT / "main.py"),
	]
	run(command)
	if not bundle_path.exists():
		raise BuildError(f"PyInstaller did not create {bundle_path}")
	return bundle_path


def build_portable_zip() -> Path:
	bundle_path = build_pyinstaller_bundle()
	zip_path = RELEASE_ROOT / artifact_name("portable.zip")
	remove_path(zip_path)

	write_portable_archive(bundle_path, zip_path)

	print(f"Created {zip_path}")
	return zip_path


def write_portable_archive(bundle_path: Path, zip_path: Path) -> None:
	"""Write a portable ZIP containing the app and its mode marker."""

	with zipfile.ZipFile(
		zip_path,
		"w",
		compression=zipfile.ZIP_DEFLATED,
		compresslevel=9,
	) as archive:
		for file_path in sorted(bundle_path.rglob("*")):
			if file_path.is_file():
				archive.write(
					file_path,
					Path(APP_NAME) / file_path.relative_to(bundle_path),
				)
		archive.writestr(f"{APP_NAME}/{PORTABLE_MARKER_NAME}", "{}\n")


def build_installer() -> Path:
	if current_platform_tag() != "windows-x64":
		raise BuildError(
			"The Inno Setup installer can only be built on Windows x64."
		)
	if not INNO_SCRIPT.exists():
		raise BuildError(f"Missing Inno Setup script: {INNO_SCRIPT}")

	bundle_path = get_bundle_path()
	if not bundle_path.exists():
		bundle_path = build_pyinstaller_bundle()

	iscc = find_iscc()
	if iscc is None:
		raise BuildError(
			"ISCC.exe was not found. Install Inno Setup 7 or set ISCC "
			"to its path."
		)

	output_base = artifact_name("setup", include_extension=False)
	command = [
		str(iscc),
		f"/DAppVersion={get_version()}",
		f"/DSourceDir={bundle_path}",
		f"/DOutputDir={RELEASE_ROOT}",
		f"/DOutputBaseFilename={output_base}",
		str(INNO_SCRIPT),
	]
	run(command)

	installer_path = RELEASE_ROOT / f"{output_base}.exe"
	if not installer_path.exists():
		raise BuildError(f"Inno Setup did not create {installer_path}")
	return installer_path


def write_checksums() -> Path:
	artifacts = [
		path
		for path in sorted(RELEASE_ROOT.iterdir())
		if path.is_file() and path.name != "SHA256SUMS.txt"
	]
	if not artifacts:
		raise BuildError(f"No release artifacts found in {RELEASE_ROOT}")

	lines = []
	for artifact in artifacts:
		digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
		lines.append(f"{digest}  {artifact.name}")

	checksum_path = RELEASE_ROOT / "SHA256SUMS.txt"
	checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
	print(f"Created {checksum_path}")
	return checksum_path


def current_platform_tag() -> str:
	system = platform.system().lower()
	machine = platform.machine().lower()
	if system == "windows" and machine in {"amd64", "x86_64"}:
		return "windows-x64"
	if system == "darwin" and machine in {"arm64", "aarch64"}:
		return "macos-arm64"
	if system == "darwin":
		return "macos-x64"
	if system == "linux" and machine in {"amd64", "x86_64"}:
		return "linux-x64"
	return f"{system}-{machine}".replace(" ", "-")


def artifact_name(kind: str, *, include_extension: bool = True) -> str:
	version = get_version()
	platform_tag = current_platform_tag()
	if kind == "portable.zip":
		return f"{APP_NAME}-{version}-{platform_tag}-portable.zip"
	if kind == "setup":
		name = f"{APP_NAME}-{version}-{platform_tag}-setup"
		return name if not include_extension else f"{name}.exe"
	raise BuildError(f"Unknown artifact kind: {kind}")


def get_bundle_path() -> Path:
	return DIST_ROOT / APP_NAME


def find_iscc() -> Path | None:
	env_path = os.environ.get("ISCC")
	local_app_data = os.environ.get("LOCALAPPDATA")
	candidates = [
		Path(env_path) if env_path else None,
		Path(local_app_data) / "Programs/Inno Setup 7/ISCC.exe"
		if local_app_data
		else None,
		Path("C:/Program Files/Inno Setup 7/ISCC.exe"),
		Path("C:/Program Files (x86)/Inno Setup 7/ISCC.exe"),
	]
	which = shutil.which("iscc")
	if which:
		candidates.insert(0, Path(which))
	for candidate in candidates:
		if candidate and candidate.exists():
			return candidate
	return None


def remove_path(path: Path) -> None:
	if not path.exists():
		return
	resolved = path.resolve()
	root = PROJECT_ROOT.resolve()
	if root not in (resolved, *resolved.parents):
		raise BuildError(f"Refusing to remove path outside project: {resolved}")
	if path.is_dir():
		shutil.rmtree(path)
	else:
		path.unlink()


def run(command: list[str]) -> None:
	print("Running:", subprocess.list2cmdline(command))
	completed = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
	if completed.returncode != 0:
		raise BuildError(
			f"Command failed with exit code {completed.returncode}."
		)


if __name__ == "__main__":
	raise SystemExit(main())
