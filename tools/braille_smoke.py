"""Smoke-test a bundled Liblouis runtime on Windows."""

from __future__ import annotations

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from powercalc.core.braille import LiblouisBrailleTranslator
from powercalc.core.tactile_plot import (
	ContentProfile,
	PlotFileFormat,
	TactilePlotRequest,
	export_tactile_plot,
)


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
	license = runtime_root / "licenses" / "LGPL-2.1-or-later.txt"
	notice = runtime_root / "THIRD_PARTY_NOTICES.md"
	if not license.is_file() or not notice.is_file():
		raise RuntimeError(
			"The Powercalc bundle lacks Liblouis license notices."
		)
	if "Liblouis" not in notice.read_text(encoding="utf-8"):
		raise RuntimeError("The bundled Liblouis attribution is incomplete.")
	translation = LiblouisBrailleTranslator(runtime_root).translate("abc")
	if translation != "⠁⠃⠉":
		raise RuntimeError(
			f"Unexpected German Grade 1 translation for 'abc': {translation!r}."
		)
	translator = LiblouisBrailleTranslator(runtime_root)
	with TemporaryDirectory() as temporary_directory:
		temporary_path = Path(temporary_directory)
		svg_path = export_tactile_plot(
			TactilePlotRequest(
				"x^2",
				content_profile=ContentProfile.SWELL_PAPER,
				use_braille_labels=True,
			),
			temporary_path / "tactile-plot",
			braille_translator=translator,
		)
		png_path = export_tactile_plot(
			TactilePlotRequest(
				"x^2",
				content_profile=ContentProfile.EMBOSSER,
				file_format=PlotFileFormat.PNG,
			),
			temporary_path / "tactile-plot",
		)
		if "<svg" not in svg_path.read_text(encoding="utf-8"):
			raise RuntimeError(
				"The bundled runtime did not export a valid SVG."
			)
		if png_path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
			raise RuntimeError(
				"The bundled runtime did not export a valid PNG."
			)
	print("Liblouis and tactile-plot Windows smoke check passed.")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
