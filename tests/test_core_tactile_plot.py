from __future__ import annotations

import re
import struct
from pathlib import Path

import pytest

from powercalc.core.tactile_plot import (
	ContentProfile,
	PaperSize,
	PlotFileFormat,
	TactilePlotError,
	TactilePlotRequest,
	export_tactile_plot,
	paper_dimensions_inches,
)


def test_profiles_export_distinct_monochrome_svg_graphics(tmp_path: Path):
	base = {"expression": "x^2", "title": "Square"}
	swell_path = export_tactile_plot(
		TactilePlotRequest(**base, content_profile=ContentProfile.SWELL_PAPER),
		tmp_path / "swell",
	)
	embosser_path = export_tactile_plot(
		TactilePlotRequest(**base, content_profile=ContentProfile.EMBOSSER),
		tmp_path / "embosser",
	)

	swell_svg = swell_path.read_text(encoding="utf-8")
	embosser_svg = embosser_path.read_text(encoding="utf-8")
	assert swell_path.suffix == ".svg"
	assert embosser_path.suffix == ".svg"
	assert "#000000" in swell_svg
	assert "#000000" in embosser_svg
	assert "stroke-dasharray" in swell_svg
	assert "stroke-dasharray" not in embosser_svg


def test_png_export_uses_selected_format_and_high_resolution(tmp_path: Path):
	path = export_tactile_plot(
		TactilePlotRequest(
			"x",
			paper_size=PaperSize.A5_PORTRAIT,
			file_format=PlotFileFormat.PNG,
		),
		tmp_path / "plot.svg",
	)

	assert path.suffix == ".png"
	with path.open("rb") as image:
		assert image.read(8) == b"\x89PNG\r\n\x1a\n"
		assert image.read(4) == b"\x00\x00\x00\r"
		assert image.read(4) == b"IHDR"
		width, height = struct.unpack(">II", image.read(8))
	assert width > 1500
	assert height > 2000


@pytest.mark.parametrize(
	("paper_size", "expected_inches"),
	[
		(PaperSize.A4_LANDSCAPE, (297 / 25.4, 210 / 25.4)),
		(PaperSize.A4_PORTRAIT, (210 / 25.4, 297 / 25.4)),
		(PaperSize.A5_LANDSCAPE, (210 / 25.4, 148 / 25.4)),
		(PaperSize.A5_PORTRAIT, (148 / 25.4, 210 / 25.4)),
	],
)
def test_paper_sizes_have_expected_physical_dimensions(
	paper_size: PaperSize,
	expected_inches: tuple[float, float],
):
	assert paper_dimensions_inches(paper_size) == pytest.approx(expected_inches)


def test_svg_preserves_selected_physical_paper_size(tmp_path: Path):
	path = export_tactile_plot(
		TactilePlotRequest("x", paper_size=PaperSize.A4_LANDSCAPE),
		tmp_path / "plot",
	)
	svg = path.read_text(encoding="utf-8")
	match = re.search(r'<svg[^>]+width="([0-9.]+)pt" height="([0-9.]+)pt"', svg)
	assert match is not None
	width, height = (float(value) / 72 for value in match.groups())
	assert (width, height) == pytest.approx(
		paper_dimensions_inches(PaperSize.A4_LANDSCAPE), abs=0.01
	)


def test_braille_labels_use_injected_reliable_translator(tmp_path: Path):
	class FakeTranslator:
		def __init__(self) -> None:
			self.calls: list[str] = []

		def translate(self, text: str) -> str:
			self.calls.append(text)
			return "⠁"

	translator = FakeTranslator()
	export_tactile_plot(
		TactilePlotRequest("x", title="Linear", use_braille_labels=True),
		tmp_path / "plot",
		braille_translator=translator,
	)

	assert "Linear" in translator.calls
	assert "x axis" in translator.calls
	assert "y axis" in translator.calls


@pytest.mark.parametrize(
	"plot_request",
	[
		TactilePlotRequest("unsafe_name + x"),
		TactilePlotRequest("sin("),
		TactilePlotRequest("x", x_min=1, x_max=1),
		TactilePlotRequest("x", content_profile="invalid"),  # type: ignore[arg-type]
		TactilePlotRequest("x", paper_size="invalid"),  # type: ignore[arg-type]
		TactilePlotRequest("x", file_format="invalid"),  # type: ignore[arg-type]
	],
)
def test_invalid_or_unsafe_requests_fail_without_output(
	tmp_path: Path,
	plot_request: TactilePlotRequest,
):
	with pytest.raises(TactilePlotError):
		export_tactile_plot(plot_request, tmp_path / "plot")
	assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("profile", list(ContentProfile))
def test_multiple_functions_have_distinct_tactile_styles_and_legend(
	profile: ContentProfile,
	monkeypatch: pytest.MonkeyPatch,
	tmp_path: Path,
):
	from powercalc.core import tactile_plot

	captured = []
	original = tactile_plot._save_figure

	def inspect_figure(figure, path, file_format):
		captured.append(figure.axes[0])
		original(figure, path, file_format)

	monkeypatch.setattr(tactile_plot, "_save_figure", inspect_figure)
	request = TactilePlotRequest(
		"x^2",
		label="Square",
		additional_functions=(tactile_plot.PlotFunction("x", "Linear"),),
		content_profile=profile,
	)
	path = export_tactile_plot(request, tmp_path / "multiple")
	axis = captured[0]
	lines = [
		line for line in axis.lines if line.get_label() in {"Square", "Linear"}
	]
	assert path.exists()
	assert [line.get_label() for line in lines] == ["Square", "Linear"]
	assert all(line.get_color() == "black" for line in lines)
	assert (lines[0].get_linestyle(), lines[0].get_marker()) != (
		lines[1].get_linestyle(),
		lines[1].get_marker(),
	)
	assert axis.get_legend() is not None


def test_invalid_second_function_never_creates_output(tmp_path: Path):
	from powercalc.core.tactile_plot import PlotFunction

	request = TactilePlotRequest(
		"x", additional_functions=(PlotFunction("__import__('os')", "Unsafe"),)
	)
	with pytest.raises(TactilePlotError, match="Function 2"):
		export_tactile_plot(request, tmp_path / "plot")
	assert not list(tmp_path.iterdir())


def test_output_suffix_is_normalized_before_export(tmp_path: Path):
	from powercalc.core.tactile_plot import plot_output_path

	selected = tmp_path / "plot.txt"
	assert (
		plot_output_path(selected, PlotFileFormat.SVG) == tmp_path / "plot.svg"
	)
	assert (
		plot_output_path(selected, PlotFileFormat.PNG) == tmp_path / "plot.png"
	)


def test_unwritable_parent_is_readable_error(tmp_path: Path):
	parent = tmp_path / "not-a-directory"
	parent.write_text("keep this file", encoding="utf-8")
	with pytest.raises(TactilePlotError, match="Could not write plot"):
		export_tactile_plot(TactilePlotRequest("x"), parent / "plot")
	assert parent.read_text(encoding="utf-8") == "keep this file"
