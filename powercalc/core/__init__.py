"""Calculation core for Powercalc."""

from powercalc.core.calculator import (
	CalculationError,
	CalculationErrorCode,
	CalculationOutcome,
	CalculationResult,
	DecimalSeparator,
	EvaluationOptions,
	calculate,
)
from powercalc.core.catalog import CatalogEntry, FUNCTION_CATALOG

__all__ = [
	"CalculationError",
	"CalculationErrorCode",
	"CalculationOutcome",
	"CalculationResult",
	"CatalogEntry",
	"DecimalSeparator",
	"EvaluationOptions",
	"FUNCTION_CATALOG",
	"calculate",
]
