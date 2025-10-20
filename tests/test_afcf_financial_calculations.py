#!/usr/bin/env python3
"""
Unit tests for AFCF (Adjusted Free Cash Flow) calculations

Tests based on methodology from AFCF Research Proposal (2025-10-20):
- AFCF = ACFO + Net Cash Flow from Investing Activities
- AFCF represents cash available for financing obligations after all investments
- Double-counting prevention with ACFO components
"""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from calculate_credit_metrics import (
    calculate_afcf,
    calculate_afcf_coverage_ratios,
    validate_afcf_reconciliation
)


def test_afcf_basic_calculation():
    """Test basic AFCF calculation with all components"""
    financial_data = {
        'issuer_name': 'Test REIT',
        'reporting_date': '2025-06-30',
        'acfo_calculated': 50000,  # Starting point
        'cash_flow_investing': {
            'development_capex': -20000,
            'property_acquisitions': -30000,
            'property_dispositions': 25000,
            'jv_capital_contributions': -5000,
            'jv_return_of_capital': 2000,
            'business_combinations': 0,
            'other_investing_outflows': -1000,
            'other_investing_inflows': 1000,
            'total_cfi': -28000  # For reconciliation
        }
    }

    result = calculate_afcf(financial_data)

    assert result['afcf'] is not None
    assert result['acfo_starting_point'] == 50000
    assert result['has_cfi_data'] is True

    # Net CFI should be sum of all components
    expected_net_cfi = -20000 + (-30000) + 25000 + (-5000) + 2000 + 0 + (-1000) + 1000
    assert result['net_cfi'] == expected_net_cfi

    # AFCF = ACFO + Net CFI
    expected_afcf = 50000 + expected_net_cfi
    assert result['afcf'] == expected_afcf
    assert result['afcf'] == 22000  # 50000 - 28000

    # Reconciliation check should pass
    assert result['reconciliation_check'] is not None
    assert result['reconciliation_check']['matches'] is True


def test_afcf_no_cfi_data():
    """Test AFCF when no cash_flow_investing data available"""
    financial_data = {
        'issuer_name': 'Test REIT',
        'acfo_calculated': 50000
        # No cash_flow_investing section
    }

    result = calculate_afcf(financial_data)

    assert result['afcf'] is None
    assert result['has_cfi_data'] is False
    assert result['error'] == 'No cash_flow_investing section in financial data'
    assert result['data_quality'] == 'none'


def test_afcf_no_acfo():
    """Test AFCF fails when ACFO not available"""
    financial_data = {
        'issuer_name': 'Test REIT',
        'cash_flow_investing': {
            'property_acquisitions': -10000
        }
        # No ACFO
    }

    result = calculate_afcf(financial_data)

    assert result['afcf'] is None
    assert result['error'] == 'ACFO must be calculated before AFCF'
    assert result['data_quality'] == 'insufficient'


def test_afcf_data_quality_assessment():
    """Test AFCF data quality assessment based on available components"""

    # Strong data quality (6+ components)
    financial_data_strong = {
        'acfo_calculated': 50000,
        'cash_flow_investing': {
            'development_capex': -20000,
            'property_acquisitions': -30000,
            'property_dispositions': 25000,
            'jv_capital_contributions': -5000,
            'jv_return_of_capital': 2000,
            'business_combinations': -10000,
            'other_investing_outflows': -1000,
            # 7 of 8 components
        }
    }

    result_strong = calculate_afcf(financial_data_strong)
    assert result_strong['data_quality'] == 'strong'
    assert result_strong['available_components'] == 7

    # Moderate data quality (3-5 components)
    financial_data_moderate = {
        'acfo_calculated': 50000,
        'cash_flow_investing': {
            'development_capex': -20000,
            'property_acquisitions': -30000,
            'property_dispositions': 25000,
            # 3 of 8 components
        }
    }

    result_moderate = calculate_afcf(financial_data_moderate)
    assert result_moderate['data_quality'] == 'moderate'
    assert result_moderate['available_components'] == 3

    # Limited data quality (< 3 components)
    financial_data_limited = {
        'acfo_calculated': 50000,
        'cash_flow_investing': {
            'property_acquisitions': -30000,
            # 1 of 8 components
        }
    }

    result_limited = calculate_afcf(financial_data_limited)
    assert result_limited['data_quality'] == 'limited'
    assert result_limited['available_components'] == 1


def test_afcf_coverage_debt_service():
    """Test AFCF debt service coverage ratio calculation"""
    financial_data = {
        'coverage_ratios': {
            'annualized_interest_expense': 40000  # Interest
        },
        'cash_flow_financing': {
            'debt_principal_repayments': -15000,  # Principal (negative)
        }
    }

    afcf = 22000

    result = calculate_afcf_coverage_ratios(financial_data, afcf)

    # Total debt service = Interest + Principal
    expected_debt_service = 40000 + 15000  # 55000
    assert result['total_debt_service'] == expected_debt_service

    # AFCF Debt Service Coverage = AFCF / Total Debt Service
    expected_coverage = 22000 / 55000
    assert result['afcf_debt_service_coverage'] == round(expected_coverage, 2)
    assert result['afcf_debt_service_coverage'] == 0.40  # Low coverage - needs external financing


def test_afcf_coverage_distributions():
    """Test AFCF distribution coverage and payout ratio"""
    financial_data = {
        'coverage_ratios': {},
        'cash_flow_financing': {
            'distributions_common': -18000,  # Negative in data
            'distributions_preferred': -1000,
            'distributions_nci': -500,
        }
    }

    afcf = 22000

    result = calculate_afcf_coverage_ratios(financial_data, afcf)

    # Total distributions (sum of all, make positive)
    expected_distributions = 18000 + 1000 + 500  # 19500
    assert result['total_distributions'] == expected_distributions

    # AFCF Distribution Coverage = AFCF / Distributions
    expected_coverage = 22000 / 19500
    assert result['afcf_distribution_coverage'] == round(expected_coverage, 2)
    assert result['afcf_distribution_coverage'] == 1.13  # Good coverage

    # AFCF Payout Ratio = Distributions / AFCF (%)
    expected_payout = (19500 / 22000) * 100
    assert result['afcf_payout_ratio'] == round(expected_payout, 1)
    assert result['afcf_payout_ratio'] == 88.6


def test_afcf_coverage_self_funding():
    """Test AFCF self-funding ratio"""
    financial_data = {
        'coverage_ratios': {
            'annualized_interest_expense': 40000
        },
        'cash_flow_financing': {
            'debt_principal_repayments': -15000,
            'new_debt_issuances': 10000,  # New financing (positive)
            'equity_issuances': 5000,
            'distributions_common': -18000,
            'distributions_preferred': -1000,
        }
    }

    afcf = 22000

    result = calculate_afcf_coverage_ratios(financial_data, afcf)

    # Net financing needs = Debt Service + Distributions - New Financing
    # = (40000 + 15000) + (18000 + 1000) - (10000 + 5000)
    # = 55000 + 19000 - 15000 = 59000
    expected_net_financing_needs = 55000 + 19000 - 15000
    assert result['net_financing_needs'] == expected_net_financing_needs

    # Self-funding ratio = AFCF / Net Financing Needs
    expected_ratio = 22000 / 59000
    assert result['afcf_self_funding_ratio'] == round(expected_ratio, 2)
    assert result['afcf_self_funding_ratio'] == 0.37  # Needs external financing


def test_afcf_coverage_no_financing_data():
    """Test AFCF coverage when no financing data available"""
    financial_data = {}
    afcf = 22000

    result = calculate_afcf_coverage_ratios(financial_data, afcf)

    # All coverage metrics should be None or 0
    assert result['afcf_debt_service_coverage'] is None
    assert result['afcf_distribution_coverage'] is None
    assert result['afcf_payout_ratio'] is None
    assert result['data_quality'] == 'limited'


def test_afcf_coverage_no_afcf():
    """Test coverage calculation fails when AFCF is None"""
    financial_data = {
        'cash_flow_financing': {
            'debt_principal_repayments': -15000
        }
    }

    result = calculate_afcf_coverage_ratios(financial_data, None)

    assert result['error'] == 'AFCF must be calculated first'
    assert all(v is None for k, v in result.items() if k != 'error' and k != 'data_quality')


def test_afcf_reconciliation_valid():
    """Test AFCF reconciliation validation when calculation is correct"""
    financial_data = {
        'cash_flow_investing': {
            'development_capex': -20000,
            'property_acquisitions': -30000,
            'property_dispositions': 25000,
            'jv_capital_contributions': -5000,
            'jv_return_of_capital': 2000,
            'other_investing_outflows': -1000,
            'other_investing_inflows': 1000,
            'total_cfi': -28000
        },
        'acfo_components': {
            'capex_development_acfo': -20000  # Should match CFI development_capex
        }
    }

    acfo = 50000
    net_cfi = -28000
    afcf = 22000  # 50000 - 28000

    result = validate_afcf_reconciliation(financial_data, acfo, afcf)

    assert result['afcf_calculation_valid'] is True
    assert result['acfo_cfi_reconciles'] is True
    assert result['development_capex_consistent'] is True
    assert '✓ AFCF calculation correct' in result['validation_notes'][0]
    assert '✓ Development CAPEX consistent' in result['validation_notes'][1]


def test_afcf_reconciliation_calculation_error():
    """Test AFCF reconciliation detects calculation errors"""
    financial_data = {
        'cash_flow_investing': {
            'property_acquisitions': -30000,
            'property_dispositions': 25000,
        }
    }

    acfo = 50000
    afcf = 30000  # WRONG! Should be 50000 + (-30000 + 25000) = 45000

    result = validate_afcf_reconciliation(financial_data, acfo, afcf)

    assert result['afcf_calculation_valid'] is False
    assert result['acfo_cfi_reconciles'] is False
    assert '✗ AFCF calculation error' in result['validation_notes'][0]


def test_afcf_reconciliation_capex_mismatch():
    """Test reconciliation detects development CAPEX mismatch"""
    financial_data = {
        'cash_flow_investing': {
            'development_capex': -20000,
            'total_cfi': -20000
        },
        'acfo_components': {
            'capex_development_acfo': -25000  # Mismatch!
        }
    }

    acfo = 50000
    afcf = 30000  # 50000 - 20000

    result = validate_afcf_reconciliation(financial_data, acfo, afcf)

    assert result['development_capex_consistent'] is False
    assert '⚠ Development CAPEX mismatch' in result['validation_notes'][1]


def test_afcf_reconciliation_full_cash_flow():
    """Test full cash flow statement reconciliation"""
    financial_data = {
        'cash_flow_investing': {
            'development_capex': -20000,
            'property_acquisitions': -10000,
            'total_cfi': -30000
        },
        'acfo_components': {
            'cash_flow_from_operations': 50000  # IFRS CFO
        },
        'cash_flow_financing': {
            'debt_principal_repayments': -15000,
            'new_debt_issuances': 10000,
            'distributions_common': -10000,
            'total_cff': -15000
        }
    }

    acfo = 50000
    afcf = 20000  # 50000 - 30000

    result = validate_afcf_reconciliation(financial_data, acfo, afcf)

    # Should have cash flow components note
    assert result['cash_flow_statement_reconciles'] is True
    assert any('Cash flow components' in note for note in result['validation_notes'])

    # CFO + CFI + CFF should be in notes
    # 50000 + (-30000) + (-15000) = 5000
    assert '5,000' in result['reconciliation_summary']


def test_afcf_double_counting_prevention():
    """Test that AFCF doesn't double-count items already in ACFO"""

    # This is a conceptual test - AFCF should NOT include:
    # - Sustaining CAPEX (already in ACFO Adj 4)
    # - Tenant Improvements sustaining (already in ACFO Adj 6)
    # - External Leasing Costs (already in ACFO Adj 5)
    # - JV Distributions (already in ACFO Adj 3)

    financial_data = {
        'acfo_calculated': 50000,  # Already deducted sustaining items
        'cash_flow_investing': {
            # Should ONLY include development/growth items
            'development_capex': -20000,  # NOT sustaining
            'property_acquisitions': -30000,  # New investment
            'jv_capital_contributions': -5000,  # NOT distributions (which are in ACFO)
        }
    }

    result = calculate_afcf(financial_data)

    # Net CFI should only be investment items
    expected_net_cfi = -20000 + (-30000) + (-5000)  # -55000
    assert result['net_cfi'] == expected_net_cfi

    # AFCF should be negative (high investment period)
    expected_afcf = 50000 + (-55000)  # -5000
    assert result['afcf'] == expected_afcf


def test_afcf_integration_with_reit_metrics():
    """Test AFCF calculation using ACFO from reit_metrics"""
    financial_data = {
        'issuer_name': 'Test REIT',
        'reit_metrics': {
            'acfo': 50000  # ACFO from reit metrics
        },
        'cash_flow_investing': {
            'property_acquisitions': -30000,
            'property_dispositions': 20000,
        }
    }

    result = calculate_afcf(financial_data)

    # Should find ACFO from reit_metrics
    assert result['acfo_starting_point'] == 50000
    assert result['afcf'] is not None

    # Net CFI
    expected_net_cfi = -30000 + 20000  # -10000
    assert result['net_cfi'] == expected_net_cfi

    # AFCF
    expected_afcf = 50000 + (-10000)  # 40000
    assert result['afcf'] == expected_afcf


def test_afcf_negative_free_cash_flow():
    """Test AFCF when free cash flow is negative (growth-oriented REIT)"""
    financial_data = {
        'acfo_calculated': 30000,
        'cash_flow_investing': {
            'development_capex': -40000,  # Heavy development
            'property_acquisitions': -50000,  # Aggressive acquisitions
            'property_dispositions': 10000,  # Some dispositions
        }
    }

    result = calculate_afcf(financial_data)

    # Net CFI heavily negative
    expected_net_cfi = -40000 + (-50000) + 10000  # -80000
    assert result['net_cfi'] == expected_net_cfi

    # AFCF negative (needs external financing)
    expected_afcf = 30000 + (-80000)  # -50000
    assert result['afcf'] == expected_afcf
    assert result['afcf'] < 0  # Negative FCF


def test_afcf_positive_net_cfi():
    """Test AFCF when net CFI is positive (disposition-focused strategy)"""
    financial_data = {
        'acfo_calculated': 30000,
        'cash_flow_investing': {
            'property_dispositions': 80000,  # Large asset sales
            'property_acquisitions': -20000,  # Limited new acquisitions
            'jv_return_of_capital': 10000,  # JV exits
        }
    }

    result = calculate_afcf(financial_data)

    # Net CFI positive (net seller)
    expected_net_cfi = 80000 + (-20000) + 10000  # 70000
    assert result['net_cfi'] == expected_net_cfi

    # AFCF very strong
    expected_afcf = 30000 + 70000  # 100000
    assert result['afcf'] == expected_afcf
    assert result['afcf'] > result['acfo_starting_point']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
