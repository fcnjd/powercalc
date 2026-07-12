"""Validate release tag and project version consistency."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument(
		"--tag",
		required=True,
		help="Release tag to validate, for example v0.2.0-beta.1.",
	)
	args = parser.parse_args()

	version = project_version()
	expected_tag = f"v{version}"
	if args.tag != expected_tag:
		print(
			f"Tag/version mismatch: tag is {args.tag!r}, "
			f"expected {expected_tag!r}.",
			file=sys.stderr,
		)
		return 1
	print(f"Validated release version {version}.")
	return 0


def project_version() -> str:
	pyproject = tomllib.loads(
		(PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
	)
	return pyproject["project"]["version"]


if __name__ == "__main__":
	raise SystemExit(main())
