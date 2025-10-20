"""
Credit Metrics Calculation Package

Modular package for calculating real estate issuer credit metrics including:
- Leverage metrics
- FFO/AFFO (REALPAC methodology)
- ACFO (Adjusted Cash Flow from Operations)
- AFCF (Adjusted Free Cash Flow)
- Burn rate and liquidity analysis
- Dilution analysis
- Coverage ratios

Usage:
    from calculate_credit_metrics import calculate_all_metrics

    metrics = calculate_all_metrics(financial_data)
"""

# Import from fully-extracted modules
from .validation import validate_required_fields
from .leverage import calculate_leverage_metrics
from .ffo_affo import (
    calculate_ffo_from_components,
    calculate_affo_from_ffo,
    validate_ffo_affo
)

# Import from wrapper modules (temporarily importing from _core)
from .acfo import (
    calculate_acfo_from_components,
    validate_acfo,
    generate_acfo_reconciliation
)
from .afcf import (
    calculate_afcf,
    calculate_afcf_coverage_ratios,
    validate_afcf_reconciliation
)
from .burn_rate import (
    calculate_burn_rate,
    calculate_cash_runway,
    assess_liquidity_risk,
    calculate_sustainable_burn_rate
)
from .dilution import analyze_dilution
from .coverage import calculate_coverage_ratios
from .reconciliation import (
    generate_ffo_affo_reconciliation,
    format_reconciliation_table,
    format_acfo_reconciliation_table
)

# Import orchestrator (uses imports from submodules)
from .reit_metrics import calculate_reit_metrics

# Import main entry points from core
from ._core import calculate_all_metrics, main

# Public API
__all__ = [
    # Validation
    'validate_required_fields',

    # Leverage
    'calculate_leverage_metrics',

    # FFO/AFFO
    'calculate_ffo_from_components',
    'calculate_affo_from_ffo',
    'validate_ffo_affo',

    # REIT metrics orchestrator
    'calculate_reit_metrics',

    # ACFO
    'calculate_acfo_from_components',
    'validate_acfo',
    'generate_acfo_reconciliation',

    # AFCF
    'calculate_afcf',
    'calculate_afcf_coverage_ratios',
    'validate_afcf_reconciliation',

    # Burn rate
    'calculate_burn_rate',
    'calculate_cash_runway',
    'assess_liquidity_risk',
    'calculate_sustainable_burn_rate',

    # Dilution
    'analyze_dilution',

    # Coverage
    'calculate_coverage_ratios',

    # Reconciliation
    'generate_ffo_affo_reconciliation',
    'format_reconciliation_table',
    'format_acfo_reconciliation_table',

    # Main entry point
    'calculate_all_metrics',
    'main'
]

__version__ = '1.0.8'
