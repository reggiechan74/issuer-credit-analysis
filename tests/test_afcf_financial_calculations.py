#!/usr/bin/env python3
"""
Unit tests for AFCF (Adjusted Free Cash Flow) calculations

Tests based on Two-Tier AFCF Methodology (v1.0.14, 2025-10-23):
- Sustainable AFCF = ACFO + Recurring CFI Only (PRIMARY METRIC)
- Total AFCF = ACFO + All CFI (COMPARISON METRIC)
- Excludes non-recurring items: property dispositions, M&A, JV exits
- Follows AFFO/ACFO sustainability principles
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


def test_afcf_two_tier_calculation():
    """Test two-tier AFCF calculation (sustainable + total)"""
    financial_data = {
        'issuer_name': 'Test REIT',
        'reporting_date': '2025-06-30',
        'acfo_calculated': 50000,  # Starting point
        'cash_flow_investing': {
            # Recurring items (included in sustainable AFCF)
            'development_capex': -20000,
            'property_acquisitions': -8000,  # Routine
            'jv_capital_contributions': -5000,
            'other_investing_outflows': -2000,

            # Non-recurring items (excluded from sustainable AFCF)
            'property_dispositions': 35000,  # Asset sales
            'jv_return_of_capital': 3000,  # JV exits
            'business_combinations': 0,
            'other_investing_inflows': 1000,

            'total_cfi': 4000  # For reconciliation
        }
    }

    result = calculate_afcf(financial_data)

    # Primary metric: Sustainable AFCF
    assert result['afcf'] is not None
    assert result['afcf_sustainable'] is not None
    assert result['acfo_starting_point'] == 50000
    assert result['has_cfi_data'] is True

    # Sustainable Net CFI (recurring only)
    expected_sustainable_cfi = -20000 + (-8000) + (-5000) + (-2000)  # -35000
    assert result['net_cfi_sustainable'] == expected_sustainable_cfi

    # Sustainable AFCF = ACFO + Recurring CFI
    expected_sustainable_afcf = 50000 + (-35000)  # 15000
    assert result['afcf_sustainable'] == expected_sustainable_afcf
    assert result['afcf'] == expected_sustainable_afcf  # Primary metric

    # Total Net CFI (all components)
    expected_total_cfi = -35000 + 35000 + 3000 + 0 + 1000  # 4000
    assert result['net_cfi_total'] == expected_total_cfi
    assert result['net_cfi_total'] == 4000  # Reconciles to IFRS

    # Total AFCF (for comparison)
    expected_total_afcf = 50000 + 4000  # 54000
    assert result['afcf_total'] == expected_total_afcf

    # Non-recurring adjustment
    expected_non_recurring = expected_total_cfi - expected_sustainable_cfi  # 39000
    assert result['non_recurring_cfi'] == expected_non_recurring

    # Reconciliation check should pass
    assert result['reconciliation_check'] is not None
    assert result['reconciliation_check']['matches'] is True


def test_afcf_component_classification():
    """Test CFI component classification (recurring vs non-recurring)"""
    financial_data = {
        'acfo_calculated': 50000,
        'cash_flow_investing': {
            'development_capex': -20000,
            'property_acquisitions': -8000,
            'jv_capital_contributions': -5000,
            'other_investing_outflows': -2000,
            'property_dispositions': 35000,
            'jv_return_of_capital': 3000,
            'other_investing_inflows': 1000,
        }
    }

    result = calculate_afcf(financial_data)

    # Check breakdown has recurring flags
    assert 'cfi_breakdown' in result
    breakdown = result['cfi_breakdown']

    # Recurring components
    assert breakdown['development_capex']['recurring'] is True
    assert breakdown['property_acquisitions']['recurring'] is True
    assert breakdown['jv_capital_contributions']['recurring'] is True
    assert breakdown['other_investing_outflows']['recurring'] is True

    # Non-recurring components
    assert breakdown['property_dispositions']['recurring'] is False
    assert breakdown['jv_return_of_capital']['recurring'] is False
    assert breakdown['other_investing_inflows']['recurring'] is False

    # Each component should have rationale
    assert 'rationale' in breakdown['development_capex']
    assert 'rationale' in breakdown['property_dispositions']


def test_afcf_artis_reit_example():
    """Test with Artis REIT Q2 2025 data (real-world example)"""
    financial_data = {
        'issuer_name': 'Artis REIT',
        'reporting_date': '2025-06-30',
        'acfo_calculated': 7198,
        'cash_flow_investing': {
            'development_capex': -9346,
            'property_acquisitions': 0,
            'jv_capital_contributions': -408,
            'other_investing_outflows': -30877,
            'property_dispositions': 47389,  # Large asset sale
            'jv_return_of_capital': 3511,
            'business_combinations': 0,
            'other_investing_inflows': 32785,
            'total_cfi': 43054
        }
    }

    result = calculate_afcf(financial_data)

    # Sustainable AFCF should be negative (shows cash burn)
    expected_sustainable_cfi = -9346 + 0 + (-408) + (-30877)  # -40631
    assert result['net_cfi_sustainable'] == expected_sustainable_cfi

    expected_sustainable_afcf = 7198 + (-40631)  # -33433
    assert result['afcf_sustainable'] == expected_sustainable_afcf
    assert result['afcf'] < 0  # Negative (realistic)

    # Total AFCF (misleading - inflated by asset sales)
    assert result['net_cfi_total'] == 43054  # Reconciles to IFRS
    expected_total_afcf = 7198 + 43054  # 50252
    assert result['afcf_total'] == expected_total_afcf

    # Non-recurring adjustment is massive
    expected_non_recurring = 47389 + 3511 + 32785  # 83685
    assert result['non_recurring_cfi'] == expected_non_recurring
    assert result['non_recurring_cfi'] > 80000  # Huge impact

    # This example shows why two-tier is critical
    # Sustainable AFCF: -$33,433k (realistic)
    # Total AFCF: +$50,252k (misleading)
    # Difference: $83,685k in non-recurring items


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


def test_afcf_coverage_uses_sustainable():
    """Test that coverage ratios use Sustainable AFCF (not Total)"""
    financial_data = {
        'coverage_ratios': {
            'period_interest_expense': 11000  # Period interest
        },
        'cash_flow_financing': {
            'debt_principal_repayments': -15000,
            'distributions_common': -18000,
            'new_debt_issuances': 10000,
            'equity_issuances': 5000,
        }
    }

    # Use Sustainable AFCF (primary metric)
    afcf_sustainable = 15000  # From Artis-style calculation

    result = calculate_afcf_coverage_ratios(financial_data, afcf_sustainable)

    # Total debt service = Interest + Principal (period amounts)
    expected_debt_service = 11000 + 15000  # 26000
    assert result['total_debt_service'] == expected_debt_service

    # AFCF Debt Service Coverage uses SUSTAINABLE AFCF
    expected_coverage = 15000 / 26000
    assert result['afcf_debt_service_coverage'] == round(expected_coverage, 2)
    assert result['afcf_debt_service_coverage'] == 0.58

    # Self-funding ratio also uses SUSTAINABLE AFCF
    total_obligations = 26000 + 18000  # 44000
    expected_self_funding = 15000 / 44000
    assert result['afcf_self_funding_ratio'] == round(expected_self_funding, 2)
    assert result['afcf_self_funding_ratio'] == 0.34


def test_afcf_coverage_debt_service():
    """Test AFCF debt service coverage ratio calculation"""
    financial_data = {
        'coverage_ratios': {
            'period_interest_expense': 22000  # Period interest (not annualized)
        },
        'cash_flow_financing': {
            'debt_principal_repayments': -15000,  # Principal (negative)
        }
    }

    afcf = 22000  # Sustainable AFCF

    result = calculate_afcf_coverage_ratios(financial_data, afcf)

    # Total debt service = Interest + Principal
    expected_debt_service = 22000 + 15000  # 37000
    assert result['total_debt_service'] == expected_debt_service

    # AFCF Debt Service Coverage = AFCF / Total Debt Service
    expected_coverage = 22000 / 37000
    assert result['afcf_debt_service_coverage'] == round(expected_coverage, 2)
    assert result['afcf_debt_service_coverage'] == 0.59  # Moderate coverage


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

    afcf = 22000  # Sustainable AFCF

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


def test_afcf_self_funding_ratio_does_not_subtract_new_financing():
    """Test that self-funding ratio measures inherent capacity (no financing deduction)"""
    financial_data = {
        'coverage_ratios': {
            'period_interest_expense': 22000
        },
        'cash_flow_financing': {
            'debt_principal_repayments': -15000,
            'new_debt_issuances': 10000,  # New financing (positive)
            'equity_issuances': 5000,
            'distributions_common': -18000,
            'distributions_preferred': -1000,
        }
    }

    afcf = 15000  # Sustainable AFCF

    result = calculate_afcf_coverage_ratios(financial_data, afcf)

    # Total obligations (debt service + distributions)
    total_obligations = (22000 + 15000) + (18000 + 1000)  # 56000
    assert total_obligations == 56000

    # Self-funding ratio = AFCF / Total Obligations
    # NOTE: Does NOT subtract new financing (measures inherent capacity)
    expected_ratio = 15000 / 56000
    assert result['afcf_self_funding_ratio'] == round(expected_ratio, 2)
    assert result['afcf_self_funding_ratio'] == 0.27

    # Interpretation: Can only cover 27% of obligations from free cash flow
    # Needs external financing for remaining 73%


def test_afcf_coverage_no_financing_data():
    """Test AFCF coverage when no financing data available"""
    financial_data = {}
    afcf = 22000

    result = calculate_afcf_coverage_ratios(financial_data, afcf)

    # All coverage metrics should be None or 0
    assert result['afcf_debt_service_coverage'] is None
    assert result['afcf_distribution_coverage'] is None
    assert result['afcf_payout_ratio'] is None


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


def test_afcf_reconciliation_valid_two_tier():
    """Test AFCF reconciliation validation with two-tier methodology"""
    financial_data = {
        'cash_flow_investing': {
            # Recurring
            'development_capex': -20000,
            'property_acquisitions': -8000,
            'jv_capital_contributions': -5000,
            'other_investing_outflows': -2000,
            # Non-recurring
            'property_dispositions': 35000,
            'jv_return_of_capital': 3000,
            'other_investing_inflows': 1000,
            'total_cfi': 4000
        },
        'acfo_components': {
            'capex_development_acfo': -20000  # Should match CFI development_capex
        }
    }

    acfo = 50000
    afcf = 15000  # Sustainable AFCF (50000 - 35000 recurring CFI)

    result = validate_afcf_reconciliation(financial_data, acfo, afcf)

    assert result['afcf_calculation_valid'] is True
    assert result['acfo_cfi_reconciles'] is True
    assert result['development_capex_consistent'] is True

    # Check for sustainable AFCF validation note
    notes = ' '.join(result['validation_notes'])
    assert 'Sustainable AFCF calculation correct' in notes
    assert 'Total AFCF' in notes  # Should show comparison
    assert 'Non-recurring CFI excluded' in notes


def test_afcf_reconciliation_calculation_error():
    """Test AFCF reconciliation detects calculation errors"""
    financial_data = {
        'cash_flow_investing': {
            'property_acquisitions': -30000,  # Recurring
            'property_dispositions': 25000,  # Non-recurring
        }
    }

    acfo = 50000
    afcf = 30000  # WRONG! Should be 50000 + (-30000) = 20000 (sustainable)

    result = validate_afcf_reconciliation(financial_data, acfo, afcf)

    assert result['afcf_calculation_valid'] is False
    assert result['acfo_cfi_reconciles'] is False
    assert '✗ AFCF calculation error' in result['validation_notes'][0]


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

    # Sustainable Net CFI should only be investment items
    expected_sustainable_cfi = -20000 + (-30000) + (-5000)  # -55000
    assert result['net_cfi_sustainable'] == expected_sustainable_cfi

    # Sustainable AFCF should be negative (high investment period)
    expected_afcf = 50000 + (-55000)  # -5000
    assert result['afcf_sustainable'] == expected_afcf
    assert result['afcf'] == expected_afcf


def test_afcf_integration_with_reit_metrics():
    """Test AFCF calculation using ACFO from reit_metrics"""
    financial_data = {
        'issuer_name': 'Test REIT',
        'reit_metrics': {
            'acfo': 50000  # ACFO from reit metrics
        },
        'cash_flow_investing': {
            'property_acquisitions': -30000,  # Recurring
            'property_dispositions': 20000,  # Non-recurring
        }
    }

    result = calculate_afcf(financial_data)

    # Should find ACFO from reit_metrics
    assert result['acfo_starting_point'] == 50000
    assert result['afcf'] is not None

    # Sustainable Net CFI (recurring only)
    assert result['net_cfi_sustainable'] == -30000

    # Sustainable AFCF
    expected_sustainable_afcf = 50000 + (-30000)  # 20000
    assert result['afcf_sustainable'] == expected_sustainable_afcf

    # Total Net CFI (includes dispositions)
    expected_total_cfi = -30000 + 20000  # -10000
    assert result['net_cfi_total'] == expected_total_cfi

    # Total AFCF
    expected_total_afcf = 50000 + (-10000)  # 40000
    assert result['afcf_total'] == expected_total_afcf


def test_afcf_negative_sustainable_positive_total():
    """Test when Sustainable AFCF is negative but Total AFCF is positive (asset sale impact)"""
    financial_data = {
        'acfo_calculated': 30000,
        'cash_flow_investing': {
            'development_capex': -40000,  # Heavy development
            'property_acquisitions': -20000,  # Acquisitions
            'property_dispositions': 80000,  # Large asset sale
        }
    }

    result = calculate_afcf(financial_data)

    # Sustainable Net CFI (recurring only - negative)
    expected_sustainable_cfi = -40000 + (-20000)  # -60000
    assert result['net_cfi_sustainable'] == expected_sustainable_cfi

    # Sustainable AFCF (negative - shows true cash burn)
    expected_sustainable_afcf = 30000 + (-60000)  # -30000
    assert result['afcf_sustainable'] == expected_sustainable_afcf
    assert result['afcf'] < 0  # Negative (realistic)

    # Total Net CFI (includes dispositions - positive)
    expected_total_cfi = -60000 + 80000  # 20000
    assert result['net_cfi_total'] == expected_total_cfi

    # Total AFCF (positive - misleading due to asset sale)
    expected_total_afcf = 30000 + 20000  # 50000
    assert result['afcf_total'] == expected_total_afcf
    assert result['afcf_total'] > 0  # Positive (misleading)

    # This demonstrates the two-tier methodology's value
    # Sustainable: -$30,000 (shows need for financing)
    # Total: +$50,000 (misleading - inflated by asset sale)


def test_afcf_methodology_note():
    """Test that methodology note is included in output"""
    financial_data = {
        'acfo_calculated': 50000,
        'cash_flow_investing': {
            'development_capex': -20000,
            'property_dispositions': 10000,
        }
    }

    result = calculate_afcf(financial_data)

    assert 'methodology_note' in result
    assert 'Sustainable AFCF' in result['methodology_note']
    assert 'non-recurring' in result['methodology_note']
    assert 'AFFO/ACFO principles' in result['methodology_note']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
