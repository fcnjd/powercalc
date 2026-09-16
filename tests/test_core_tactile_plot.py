import pytest

from powercalc.core.tactile_plot import (
	TactilePlotError,
	TactilePlotRequest,
	export_tactile_svg,
	to_braille,
)


def test_export_tactile_svg_creates_vector_plot(tmp_path):
	path = export_tactile_svg(
		TactilePlotRequest("x^2", x_min=-2, x_max=2, title="Square"),
		tmp_path / "square.svg",
	)

	content = path.read_text(encoding="utf-8")

	assert path == tmp_path / "square.svg"
	assert "<svg" in content
	assert "#000000" in content


def test_tactile_svg_uses_safe_function_parser(tmp_path):
	with pytest.raises(TactilePlotError, match="Unknown name"):
		export_tactile_svg(
			TactilePlotRequest("unsafe_name + x"),
			tmp_path / "unsafe.svg",
		)


def test_tactile_plot_reports_malformed_function(tmp_path):
	with pytest.raises(TactilePlotError, match="Invalid function"):
		export_tactile_svg(
			TactilePlotRequest("sin("),
			tmp_path / "malformed.svg",
		)


def test_tactile_plot_rejects_invalid_range(tmp_path):
	with pytest.raises(TactilePlotError, match="minimum"):
		export_tactile_svg(
			TactilePlotRequest("x", x_min=2, x_max=2),
			tmp_path / "invalid.svg",
		)


def test_braille_transcription_covers_plot_labels():
	assert to_braille("x axis 2") == "⠭ ⠁⠭⠊⠎ ⠣"
