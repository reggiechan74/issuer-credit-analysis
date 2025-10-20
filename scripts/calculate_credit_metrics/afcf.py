"""
AFCF (Adjusted Free Cash Flow) calculations

Extends ACFO analysis to measure cash available after ALL investing activities.
"""

from ._core import (
    calculate_afcf,
    calculate_afcf_coverage_ratios,
    validate_afcf_reconciliation
)

__all__ = [
    'calculate_afcf',
    'calculate_afcf_coverage_ratios',
    'validate_afcf_reconciliation'
]
