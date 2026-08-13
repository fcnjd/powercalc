"""Extract release notes from CHANGELOG.md for one version."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--version", required=True)
	parser.add_argument("--output", required=True, type=Path)
	args = parser.parse_args()

	try:
		notes = extract_release_notes(args.version)
	except ValueError as exc:
		print(str(exc), file=sys.stderr)
		return 1

	args.output.parent.mkdir(parents=True, exist_ok=True)
	args.output.write_text(notes, encoding="utf-8", newline="\n")
	print(f"Wrote release notes for {args.version} to {args.output}")
	return 0


def extract_release_notes(version: str) -> str:
	changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
	return extract_release_notes_from_text(changelog, version)


def extract_release_notes_from_text(changelog: str, version: str) -> str:
	"""Return the notes for one version heading from changelog text.

	Kept separate from ``extract_release_notes`` so parsing behavior can be
	unit-tested against synthetic changelog text, independent of the current
	contents of CHANGELOG.md.
	"""

	heading_pattern = re.compile(r"^## \[(?P<version>[^\]]+)\]", re.MULTILINE)
	matches = list(heading_pattern.finditer(changelog))
	for index, match in enumerate(matches):
		if match.group("version") != version:
			continue
		start = match.end()
		end = matches[index + 1].start() if index + 1 < len(matches) else None
		notes = changelog[start:end].strip()
		if not notes:
			raise ValueError(f"CHANGELOG.md section for {version} is empty.")
		return notes + "\n"
	raise ValueError(f"CHANGELOG.md has no section for {version}.")


if __name__ == "__main__":
	raise SystemExit(main())
