"""Manage Powercalc's gettext translation catalogs.

Run with ``uv run python -m tools.i18n extract|update|compile``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BABEL_CONFIG = PROJECT_ROOT / "babel.cfg"
LOCALE_DIR = PROJECT_ROOT / "powercalc" / "locale"
POT_PATH = LOCALE_DIR / "powercalc.pot"
DOMAIN = "powercalc"

# English is the source language of every `_()` call, so it needs no
# catalog of its own; only target translations are listed here.
SUPPORTED_LANGUAGES = ("de",)


class I18nError(RuntimeError):
	"""Raised when a translation catalog step fails."""


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument(
		"action",
		choices=("extract", "update", "compile"),
		help="Translation catalog step to run.",
	)
	args = parser.parse_args()

	try:
		if args.action == "extract":
			extract()
		elif args.action == "update":
			update()
		elif args.action == "compile":
			compile_catalogs()
	except I18nError as exc:
		print(f"Translation catalog step failed: {exc}", file=sys.stderr)
		return 1
	return 0


def extract() -> None:
	"""Regenerate the .pot template from translatable source strings."""

	LOCALE_DIR.mkdir(parents=True, exist_ok=True)
	run(
		[
			"pybabel",
			"extract",
			"-F",
			"babel.cfg",
			"-o",
			str(POT_PATH.relative_to(PROJECT_ROOT)),
			"--project=Powercalc",
			"--copyright-holder=Powercalc",
			"powercalc",
		]
	)
	print(f"Created {POT_PATH}")


def update() -> None:
	"""Merge new/changed strings from the .pot into each language's .po."""

	if not POT_PATH.exists():
		raise I18nError(f"Missing {POT_PATH}; run 'extract' first.")

	for language in SUPPORTED_LANGUAGES:
		po_path = _po_path(language)
		po_path.parent.mkdir(parents=True, exist_ok=True)
		command = "update" if po_path.exists() else "init"
		run(
			[
				"pybabel",
				command,
				"-i",
				str(POT_PATH),
				"-o",
				str(po_path),
				"-l",
				language,
				"-D",
				DOMAIN,
			]
		)
		print(f"Updated {po_path}")


def compile_catalogs() -> None:
	"""Compile every language's .po into the .mo used at runtime."""

	for language in SUPPORTED_LANGUAGES:
		po_path = _po_path(language)
		if not po_path.exists():
			raise I18nError(f"Missing {po_path}; run 'update' first.")
		mo_path = po_path.with_suffix(".mo")
		run(
			[
				"pybabel",
				"compile",
				"-i",
				str(po_path),
				"-o",
				str(mo_path),
				"-l",
				language,
				"-D",
				DOMAIN,
			]
		)
		print(f"Compiled {mo_path}")


def _po_path(language: str) -> Path:
	return LOCALE_DIR / language / "LC_MESSAGES" / f"{DOMAIN}.po"


def run(command: list[str]) -> None:
	print("Running:", subprocess.list2cmdline(command))
	completed = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
	if completed.returncode != 0:
		raise I18nError(
			f"Command failed with exit code {completed.returncode}."
		)


if __name__ == "__main__":
	raise SystemExit(main())
