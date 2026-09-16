"""Safe, high-contrast SVG export for tactile function plots."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path

import matplotlib
import sympy as sp

from powercalc.core.calculator import (
	EvaluationOptions,
	ExpressionError,
	parse_function_expression,
)


# The exporter must also work on CI and on systems without a display server.
matplotlib.use("Agg")
from matplotlib import pyplot as plt


class TactilePlotError(ValueError):
	"""Raised when a tactile plot cannot be created from valid user input."""


@dataclass(frozen=True)
class TactilePlotRequest:
	"""A single real-valued function and its visible x range."""

	expression: str
	x_min: float = -10.0
	x_max: float = 10.0
	title: str = "Tactile function plot"
	use_braille_labels: bool = False
	samples: int = 201


_BRAILLE_MAP = {
	"a": "⠁",
	"b": "⠃",
	"c": "⠉",
	"d": "⠙",
	"e": "⠑",
	"f": "⠋",
	"g": "⠛",
	"h": "⠓",
	"i": "⠊",
	"j": "⠚",
	"k": "⠅",
	"l": "⠇",
	"m": "⠍",
	"n": "⠝",
	"o": "⠕",
	"p": "⠏",
	"q": "⠟",
	"r": "⠗",
	"s": "⠎",
	"t": "⠞",
	"u": "⠥",
	"v": "⠧",
	"w": "⠺",
	"x": "⠭",
	"y": "⠽",
	"z": "⠵",
	"0": "⠬",
	"1": "⠡",
	"2": "⠣",
	"3": "⠩",
	"4": "⠹",
	"5": "⠱",
	"6": "⠫",
	"7": "⠻",
	"8": "⠳",
	"9": "⠪",
	"-": "⠤",
	".": "⠄",
	" ": " ",
	"(": "⠦",
	")": "⠴",
	",": "⠂",
}


def to_braille(text: str) -> str:
	"""Return the limited uncontracted Braille transcription used in exports."""

	return "".join(
		_BRAILLE_MAP.get(character.lower(), "?") for character in text
	)


def export_tactile_svg(
	request: TactilePlotRequest,
	path: Path,
	options: EvaluationOptions | None = None,
) -> Path:
	"""Render a high-contrast, tactile-friendly function plot as SVG.

	The graph uses a thick black line, periodic circular markers, prominent
	axes, and a light dotted reference grid. SVG is deliberately chosen because
	it keeps lines and markers sharp when transferred to swell paper or an
	embosser.
	Points whose function value is non-real or undefined are omitted instead of
	being connected across a discontinuity.
	"""

	_validate_request(request)
	try:
		variable, expression = parse_function_expression(
			request.expression, options
		)
	except ExpressionError as exc:
		raise TactilePlotError(exc.error.message) from exc
	except (SyntaxError, TypeError, ValueError, RecursionError) as exc:
		raise TactilePlotError(f"Invalid function: {exc}") from exc

	points = _sample_real_points(variable, expression, request)
	if not points:
		raise TactilePlotError(
			"The function has no real, finite values in this x range."
		)

	path = path.with_suffix(".svg")
	path.parent.mkdir(parents=True, exist_ok=True)
	label = to_braille if request.use_braille_labels else str
	fig, axis = plt.subplots(figsize=(11, 8))
	try:
		for x_values, y_values in _segments(points):
			axis.plot(
				x_values,
				y_values,
				color="black",
				linewidth=2.8,
				marker="o",
				markersize=5,
				markevery=max(1, len(x_values) // 12),
			)
		axis.axhline(0, color="black", linewidth=2.2)
		axis.axvline(0, color="black", linewidth=2.2)
		axis.grid(True, color="black", linestyle=":", linewidth=0.8)
		axis.set_title(label(request.title), fontsize=20, pad=18)
		axis.set_xlabel(label("x axis"), fontsize=16, labelpad=14)
		axis.set_ylabel(label("y axis"), fontsize=16, labelpad=14)
		axis.tick_params(axis="both", which="major", width=2, length=8)
		for spine in axis.spines.values():
			spine.set_linewidth(2.2)
		fig.savefig(path, format="svg", bbox_inches="tight")
	finally:
		plt.close(fig)
	return path


def _validate_request(request: TactilePlotRequest) -> None:
	if not isfinite(request.x_min) or not isfinite(request.x_max):
		raise TactilePlotError("The x range must use finite numbers.")
	if request.x_min >= request.x_max:
		raise TactilePlotError(
			"The x minimum must be smaller than the x maximum."
		)
	if not 21 <= request.samples <= 2001:
		raise TactilePlotError("Samples must be between 21 and 2001.")


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
