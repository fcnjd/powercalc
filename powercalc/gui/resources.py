"""Runtime resource path helpers for the wxPython GUI."""

from __future__ import annotations

from pathlib import Path
import sys


def get_app_icon_path() -> Path | None:
	"""Return the packaged or source-tree Windows icon path if available."""

	if getattr(sys, "frozen", False):
		base_path = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
		candidate = base_path / "assets" / "powercalc.ico"
	else:
		candidate = (
			Path(__file__).resolve().parents[2] / "assets" / "powercalc.ico"
		)

	if candidate.exists():
		return candidate
	return None
