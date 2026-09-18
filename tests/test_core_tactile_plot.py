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
