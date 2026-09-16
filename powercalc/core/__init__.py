"""Calculation core for Powercalc."""

from powercalc.core.calculator import (
	CalculationError,
	CalculationErrorCode,
	CalculationOutcome,
	CalculationResult,
	DecimalSeparator,
	EvaluationOptions,
	calculate,
	parse_function_expression,
)
from powercalc.core.catalog import (
	CatalogEntry,
	FUNCTION_CATALOG,
	build_insertion,
)

__all__ = [
	"CalculationError",
	"CalculationErrorCode",
	"CalculationOutcome",
	"CalculationResult",
	"CatalogEntry",
	"DecimalSeparator",
	"EvaluationOptions",
	"FUNCTION_CATALOG",
	"build_insertion",
	"calculate",
	"parse_function_expression",
]
