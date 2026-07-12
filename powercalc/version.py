"""Version helpers for Powercalc."""

from __future__ import annotations

__version__ = "0.2.0-beta.1"


def get_version() -> str:
	"""Return the public Powercalc version string."""

	return __version__


def get_versioned_title() -> str:
	"""Return the main window title including the version."""

	return f"Powercalc {get_version()}"
