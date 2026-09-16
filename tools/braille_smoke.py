"""Smoke-test a bundled Liblouis runtime on Windows."""

from __future__ import annotations

import argparse
from pathlib import Path

from powercalc.core.braille import LiblouisBrailleTranslator


def find_runtime_root(bundle_root: Path) -> Path:
	"""Locate PyInstaller's data directory for one-dir bundle layouts."""

	candidates = (
		bundle_root / "resources" / "liblouis",
		bundle_root / "_internal" / "resources" / "liblouis",
	)
	for candidate in candidates:
		if candidate.is_dir():
			return candidate
	raise RuntimeError("The Powercalc bundle does not contain Liblouis data.")


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("bundle_root", type=Path)
	args = parser.parse_args()

	runtime_root = find_runtime_root(args.bundle_root)
	translation = LiblouisBrailleTranslator(runtime_root).translate("abc")
	if translation != "⠁⠃⠉":
		raise RuntimeError(
			f"Unexpected German Grade 1 translation for 'abc': {translation!r}."
		)
	print("Liblouis Windows runtime smoke check passed.")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
