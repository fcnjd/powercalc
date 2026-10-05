"""Headless export of tactile function plots.

The module intentionally contains no wxPython code.  The GUI supplies a
validated :class:`TactilePlotRequest`; rendering, output selection, and
Liblouis-backed label translation remain independently testable here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from pathlib import Path
from typing import Protocol

import matplotlib
import sympy as sp

from powercalc.core.braille import (
	BrailleTranslationUnavailable,
	LiblouisBrailleTranslator,
)
from powercalc.core.calculator import (
	EvaluationOptions,
	ExpressionError,
	parse_function_expression,
)

# Rendering must work in CI and on systems without a display server.
matplotlib.use("Agg")
from matplotlib import pyplot as plt


class TactilePlotError(ValueError):
	"""Raised when a tactile plot cannot be exported."""


class ContentProfile(StrEnum):
	"""The tactile encoding, independent from the saved file format."""

	SWELL_PAPER = "swell-paper"
	EMBOSSER = "embosser"


class PaperSize(StrEnum):
	"""Physical paper sizes supported by the v2 exporter."""

	A4_LANDSCAPE = "a4-landscape"
	A4_PORTRAIT = "a4-portrait"
	A5_LANDSCAPE = "a5-landscape"
	A5_PORTRAIT = "a5-portrait"


class PlotFileFormat(StrEnum):
	"""Output formats supported by the tactile exporter."""

	SVG = "svg"
	PNG = "png"


class BrailleTranslator(Protocol):
	"""Minimal translation boundary required by tactile-plot rendering."""

	def translate(self, text: str) -> str:
		"""Translate ordinary text to Unicode Braille."""


@dataclass(frozen=True)
class PlotFunction:
	"""An additional function and its legend label."""

	expression: str
	label: str


@dataclass(frozen=True)
class TactilePlotRequest:
	"""Real-valued functions and their tactile export options."""

	expression: str
	x_min: float = -10.0
	x_max: float = 10.0
	title: str = "Tactile function plot"
	content_profile: ContentProfile = ContentProfile.SWELL_PAPER
	paper_size: PaperSize = PaperSize.A4_LANDSCAPE
	file_format: PlotFileFormat = PlotFileFormat.SVG
	use_braille_labels: bool = False
	samples: int = 201
	label: str = ""
	additional_functions: tuple[PlotFunction, ...] = ()


@dataclass(frozen=True)
class _ProfileStyle:
	line_width: float
	marker: str
	marker_size: float
	marker_count: int
	axis_width: float
	grid: bool
	grid_style: str
	grid_width: float


_PROFILE_STYLES = {
	ContentProfile.SWELL_PAPER: _ProfileStyle(
		line_width=2.8,
		marker="o",
		marker_size=5.5,
		marker_count=12,
		axis_width=2.2,
		grid=True,
		grid_style=":",
		grid_width=0.8,
	),
	ContentProfile.EMBOSSER: _ProfileStyle(
		line_width=3.6,
		marker="s",
		marker_size=6.5,
		marker_count=8,
		axis_width=2.8,
		grid=False,
		grid_style="-",
		grid_width=0.0,
	),
}

# Each line is identifiable by touch without relying on colour. The first
# swell-paper line and following cycle follow the supplied notebook.
_SERIES_STYLES = {
	ContentProfile.SWELL_PAPER: (
		("-", None),
		("--", "o"),
		("-.", "s"),
		(":", "^"),
		("-", "D"),
		("--", "x"),
	),
	ContentProfile.EMBOSSER: (
		("-", "s"),
		(":", "o"),
		("--", "^"),
		("-.", "D"),
		(":", "x"),
		("--", "v"),
	),
}
FUNCTION_NAMES = ("f", "g", "h", "i", "j", "k")
MAX_FUNCTIONS = len(FUNCTION_NAMES)


def function_name(index: int) -> str:
	"""Return the stable mathematical label for a one-based curve index."""

	return f"{FUNCTION_NAMES[index - 1]}(x)"


_PAPER_SIZES_MM = {
	PaperSize.A4_LANDSCAPE: (297.0, 210.0),
	PaperSize.A4_PORTRAIT: (210.0, 297.0),
	PaperSize.A5_LANDSCAPE: (210.0, 148.0),
	PaperSize.A5_PORTRAIT: (148.0, 210.0),
}

PNG_DPI = 300
"""Fixed resolution used for rendered tactile-print transfer."""


def braille_labels_available() -> bool:
	"""Return whether the optional bundled Liblouis runtime can be loaded."""

	try:
		LiblouisBrailleTranslator()
	except BrailleTranslationUnavailable:
		return False
	return True


def export_tactile_plot(
	request: TactilePlotRequest,
	path: Path,
	options: EvaluationOptions | None = None,
	*,
	braille_translator: BrailleTranslator | None = None,
) -> Path:
	"""Export a tactile function plot in the selected SVG or PNG format.

	The selected content profile controls tactile encoding only. File format is
	intentionally independent, so either profile can be stored as vector SVG or
	high-resolution PNG.
	"""

	validate_tactile_plot_request(request, options)
	parsed = _parse_functions(request, options)
	series = []
	for index, (variable, expression, legend) in enumerate(parsed, 1):
		points = _sample_real_points(variable, expression, request)
		if not any(y_value is not None for _, y_value in points):
			raise TactilePlotError(
				f"{function_name(index)} has no real, finite values "
				"in this x range."
			)
		series.append((points, legend))

	label = _labeler(request, braille_translator)
	output_path = plot_output_path(path, request.file_format)
	try:
		output_path.parent.mkdir(parents=True, exist_ok=True)
	except OSError as exc:
		raise TactilePlotError(f"Could not write plot: {exc}") from exc
	temporary_path = output_path.with_name(
		f".{output_path.stem}.tmp{output_path.suffix}"
	)
	figure = _render_figure(request, series, label)
	try:
		_save_figure(figure, temporary_path, request.file_format)
		temporary_path.replace(output_path)
	except OSError as exc:
		raise TactilePlotError(f"Could not write plot: {exc}") from exc
	finally:
		plt.close(figure)
		if temporary_path.exists():
			temporary_path.unlink()
	return output_path


def plot_output_path(path: Path, file_format: PlotFileFormat) -> Path:
	"""Return the actual output filename for the selected file format."""

	return path.with_suffix(f".{file_format.value}")


def validate_tactile_plot_request(
	request: TactilePlotRequest,
	options: EvaluationOptions | None = None,
) -> tuple[sp.Symbol, sp.Expr]:
	"""Validate request options and safely parse its function of ``x``."""

	_validate_request(request)
	try:
		variable, expression, _ = _parse_functions(request, options)[0]
		return variable, expression
	except ExpressionError as exc:
		raise TactilePlotError(exc.error.message) from exc
	except (SyntaxError, TypeError, ValueError, RecursionError) as exc:
		raise TactilePlotError(f"Invalid function: {exc}") from exc


def paper_dimensions_inches(paper_size: PaperSize) -> tuple[float, float]:
	"""Return the selected physical paper dimensions in inches."""

	width_mm, height_mm = _PAPER_SIZES_MM[paper_size]
	return width_mm / 25.4, height_mm / 25.4


def _validate_request(request: TactilePlotRequest) -> None:
	if not isinstance(request.content_profile, ContentProfile):
		raise TactilePlotError("Unknown tactile content profile.")
	if not isinstance(request.paper_size, PaperSize):
		raise TactilePlotError("Unknown paper size.")
	if not isinstance(request.file_format, PlotFileFormat):
		raise TactilePlotError("Unknown plot file format.")
	if not isfinite(request.x_min) or not isfinite(request.x_max):
		raise TactilePlotError("The x range must use finite numbers.")
	if request.x_min >= request.x_max:
		raise TactilePlotError(
			"The x minimum must be smaller than the x maximum."
		)
	if not 21 <= request.samples <= 2001:
		raise TactilePlotError("Samples must be between 21 and 2001.")
	if len(request.additional_functions) + 1 > MAX_FUNCTIONS:
		raise TactilePlotError(
			f"At most {MAX_FUNCTIONS} functions are supported."
		)
	for entry in request.additional_functions:
		if not isinstance(entry, PlotFunction):
			raise TactilePlotError("Invalid additional function.")
	for legend in (
		request.label,
		*(item.label for item in request.additional_functions),
	):
		if len(legend) > 80 or "\n" in legend or "\r" in legend:
			raise TactilePlotError(
				"Function labels must be one line of at most 80 characters."
			)


def _parse_functions(
	request: TactilePlotRequest,
	options: EvaluationOptions | None,
) -> list[tuple[sp.Symbol, sp.Expr, str]]:
	"""Parse every curve through the restricted calculator parser."""

	parsed = []
	entries = ((request.expression, request.label),) + tuple(
		(item.expression, item.label) for item in request.additional_functions
	)
	for index, (source, legend) in enumerate(entries, 1):
		try:
			variable, expression = parse_function_expression(source, options)
		except ExpressionError as exc:
			raise TactilePlotError(
				f"{function_name(index)}: {exc.error.message}"
			) from exc
		parsed.append(
			(variable, expression, legend.strip() or function_name(index))
		)
	return parsed


def _labeler(
	request: TactilePlotRequest,
	translator: BrailleTranslator | None,
):
	if not request.use_braille_labels:
		return str
	if translator is not None:
		return translator.translate
	try:
		return LiblouisBrailleTranslator().translate
	except BrailleTranslationUnavailable as exc:
		raise TactilePlotError(
			"Braille labels are unavailable because the bundled Liblouis "
			"runtime could not be loaded."
		) from exc


def _render_figure(
	request: TactilePlotRequest,
	series: list[tuple[list[tuple[float, float | None]], str]],
	label,
):
	style = _PROFILE_STYLES[request.content_profile]
	with matplotlib.rc_context(
		{
			"font.family": "DejaVu Sans",
			"svg.fonttype": "path",
		}
	):
		figure, axis = plt.subplots(
			figsize=paper_dimensions_inches(request.paper_size)
		)
		for index, (points, legend) in enumerate(series):
			line_style, marker = _SERIES_STYLES[request.content_profile][index]
			for segment_index, (x_values, y_values) in enumerate(
				_segments(points)
			):
				axis.plot(
					x_values,
					y_values,
					color="black",
					linestyle=line_style,
					linewidth=style.line_width,
					marker=marker,
					markersize=style.marker_size,
					markevery=max(1, len(x_values) // style.marker_count),
					label=label(legend) if segment_index == 0 else None,
				)
		if len(series) > 1:
			axis.legend(
				loc="upper left", bbox_to_anchor=(1.01, 1), frameon=False
			)
		axis.axhline(0, color="black", linewidth=style.axis_width)
		axis.axvline(0, color="black", linewidth=style.axis_width)
		if style.grid:
			axis.grid(
				True,
				color="black",
				linestyle=style.grid_style,
				linewidth=style.grid_width,
			)
		axis.set_title(label(request.title), fontsize=20, pad=18)
		axis.set_xlabel(label("x axis"), fontsize=16, labelpad=14)
		axis.set_ylabel(label("y axis"), fontsize=16, labelpad=14)
		axis.tick_params(axis="both", which="major", width=2, length=8)
		for spine in axis.spines.values():
			spine.set_linewidth(style.axis_width)
		if request.use_braille_labels:
			x_ticks = axis.get_xticks()
			y_ticks = axis.get_yticks()
			axis.set_xticks(
				x_ticks,
				labels=[label(_format_tick(value)) for value in x_ticks],
			)
			axis.set_yticks(
				y_ticks,
				labels=[label(_format_tick(value)) for value in y_ticks],
			)
		figure.tight_layout()
	return figure


def _save_figure(figure, path: Path, file_format: PlotFileFormat) -> None:
	kwargs = {"format": file_format.value}
	if file_format is PlotFileFormat.PNG:
		kwargs["dpi"] = PNG_DPI
	with matplotlib.rc_context({"svg.fonttype": "path"}):
		figure.savefig(path, **kwargs)


def _format_tick(value: float) -> str:
	return f"{value:g}"


def _sample_real_points(
	variable: sp.Symbol,
	expression: sp.Expr,
	request: TactilePlotRequest,
) -> list[tuple[float, float | None]]:
	evaluator = sp.lambdify(variable, expression, modules="math")
	step = (request.x_max - request.x_min) / (request.samples - 1)
	points: list[tuple[float, float | None]] = []
	for index in range(request.samples):
		x_value = request.x_min + index * step
		try:
			y_value = evaluator(x_value)
			value = float(y_value)
		except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
			points.append((x_value, None))
			continue
		points.append((x_value, value if isfinite(value) else None))
	return points


def _segments(
	points: list[tuple[float, float | None]],
) -> list[tuple[list[float], list[float]]]:
	segments: list[tuple[list[float], list[float]]] = []
	x_values: list[float] = []
	y_values: list[float] = []
	for x_value, y_value in points:
		if y_value is None:
			if x_values:
				segments.append((x_values, y_values))
				x_values, y_values = [], []
			continue
		x_values.append(x_value)
		y_values.append(y_value)
	if x_values:
		segments.append((x_values, y_values))
	return segments
