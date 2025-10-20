#!/usr/bin/env python3
"""
Credit Metrics Calculator - Main Entry Point

This script has been refactored into a modular package structure.
All functions are now organized in the calculate_credit_metrics/ subfolder.

Usage:
    python calculate_credit_metrics.py <path_to_phase2_json>

Example:
    python calculate_credit_metrics.py Issuer_Reports/Artis_REIT/temp/phase2_extracted_data.json
"""

# Import all public functions from the modular package
from calculate_credit_metrics import (
    # Main entry point
    calculate_all_metrics,
    main,

    # Individual calculation functions (for direct use)
    validate_required_fields,
    calculate_leverage_metrics,
    calculate_ffo_from_components,
    calculate_affo_from_ffo,
    validate_ffo_affo,
    calculate_reit_metrics,
    calculate_acfo_from_components,
    validate_acfo,
    generate_acfo_reconciliation,
    calculate_afcf,
    calculate_afcf_coverage_ratios,
    validate_afcf_reconciliation,
    calculate_burn_rate,
    calculate_cash_runway,
    assess_liquidity_risk,
    calculate_sustainable_burn_rate,
    analyze_dilution,
    calculate_coverage_ratios,
    generate_ffo_affo_reconciliation,
    format_reconciliation_table,
    format_acfo_reconciliation_table
)

# For backward compatibility - expose all functions at module level
__all__ = [
    'calculate_all_metrics',
    'main',
    'validate_required_fields',
    'calculate_leverage_metrics',
    'calculate_ffo_from_components',
    'calculate_affo_from_ffo',
    'validate_ffo_affo',
    'calculate_reit_metrics',
    'calculate_acfo_from_components',
    'validate_acfo',
    'generate_acfo_reconciliation',
    'calculate_afcf',
    'calculate_afcf_coverage_ratios',
    'validate_afcf_reconciliation',
    'calculate_burn_rate',
    'calculate_cash_runway',
    'assess_liquidity_risk',
    'calculate_sustainable_burn_rate',
    'analyze_dilution',
    'calculate_coverage_ratios',
    'generate_ffo_affo_reconciliation',
    'format_reconciliation_table',
    'format_acfo_reconciliation_table'
]

if __name__ == '__main__':
    main()
