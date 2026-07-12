from pathlib import Path
import tomllib

from powercalc.version import get_version, get_versioned_title


def test_public_version_matches_project_metadata():
	pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
	metadata = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

	assert get_version() == metadata["project"]["version"]


def test_window_title_includes_public_version():
	assert get_versioned_title() == f"Powercalc {get_version()}"
