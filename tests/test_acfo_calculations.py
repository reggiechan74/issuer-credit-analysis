#!/usr/bin/env python3
"""
Unit tests for ACFO (Adjusted Cash Flow from Operations) calculations

Tests based on REALPAC ACFO White Paper (January 2023) methodology
"""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from calculate_credit_metrics import (
    calculate_acfo_from_components,
    validate_acfo,
    generate_acfo_reconciliation,
    format_acfo_reconciliation_table,
    calculate_reit_metrics
)


def test_acfo_basic_calculation():
    """Test basic ACFO calculation with all components"""

    financial_data = {
        'issuer_name': 'Test REIT',
        'reporting_date': '2025-06-30',
        'acfo_components': {
            'cash_flow_from_operations': 100000,  # Starting point
            # Working capital & financing
            'change_in_working_capital': 5000,
            'interest_financing': 8000,
            # Joint ventures (use distributions method)
            'jv_distributions': 2000,
            # CAPEX & leasing
            'capex_sustaining_acfo': -15000,  # Deduction
            'leasing_costs_external': -3000,
            'tenant_improvements_acfo': -4000,
            # Investment & tax
            'realized_investment_gains_losses': -1000,
            'taxes_non_operating': 500,
            # Transaction costs
            'transaction_costs_acquisitions': 2500,
            'transaction_costs_disposals': 1500,
            # Financing
            'deferred_financing_fees': 1200,
            'debt_termination_costs': 0,
            # Other adjustments
            'non_controlling_interests_acfo': -800,
            # Metadata
            'calculation_method_acfo': 'actual',
            'jv_treatment_method': 'distributions'
        }
    }

    result = calculate_acfo_from_components(financial_data)

    assert result['acfo_calculated'] is not None
    assert result['cash_flow_from_operations'] == 100000
    assert result['data_quality'] in ['strong', 'moderate', 'limited']
    assert result['calculation_method'] == 'actual'
    assert result['jv_treatment_method'] == 'distributions'

    # ACFO should be CFO + sum of adjustments
    expected_acfo = 100000 + 5000 + 8000 + 2000 - 15000 - 3000 - 4000 - 1000 + 500 + 2500 + 1500 + 1200 - 800
    assert result['acfo_calculated'] == expected_acfo


def test_acfo_missing_starting_point():
    """Test ACFO calculation fails gracefully when CFO missing"""

    financial_data = {
        'acfo_components': {
            # Missing cash_flow_from_operations
            'change_in_working_capital': 5000
        }
    }

    result = calculate_acfo_from_components(financial_data)

    assert result['acfo_calculated'] is None
    assert result['error'] == 'Missing cash_flow_from_operations - cannot calculate ACFO'
    assert result['data_quality'] == 'insufficient'


def test_acfo_no_components_section():
    """Test ACFO calculation when acfo_components section missing"""

    financial_data = {
        'issuer_name': 'Test REIT',
        'reporting_date': '2025-06-30'
        # No acfo_components section
    }

    result = calculate_acfo_from_components(financial_data)

    assert result['acfo_calculated'] is None
    assert result['error'] == 'No acfo_components section in financial data'
    assert result['data_quality'] == 'none'


def test_acfo_data_quality_assessment():
    """Test data quality assessment based on available adjustments"""

    # Test "strong" data quality (12+ of 17 adjustments)
    financial_data_strong = {
        'acfo_components': {
            'cash_flow_from_operations': 100000,
            'change_in_working_capital': 5000,
            'interest_financing': 8000,
            'jv_distributions': 2000,
            'capex_sustaining_acfo': -15000,
            'leasing_costs_external': -3000,
            'tenant_improvements_acfo': -4000,
            'realized_investment_gains_losses': -1000,
            'taxes_non_operating': 500,
            'transaction_costs_acquisitions': 2500,
            'transaction_costs_disposals': 1500,
            'deferred_financing_fees': 1200,
            'non_controlling_interests_acfo': -800
        }
    }

    result_strong = calculate_acfo_from_components(financial_data_strong)
    assert result_strong['data_quality'] == 'strong'
    assert result_strong['available_adjustments'] >= 12

    # Test "moderate" data quality (6-11 adjustments)
    financial_data_moderate = {
        'acfo_components': {
            'cash_flow_from_operations': 100000,
            'change_in_working_capital': 5000,
            'interest_financing': 8000,
            'capex_sustaining_acfo': -15000,
            'leasing_costs_external': -3000,
            'tenant_improvements_acfo': -4000,
            'realized_investment_gains_losses': -1000  # Added to reach 6 adjustments
        }
    }

    result_moderate = calculate_acfo_from_components(financial_data_moderate)
    assert result_moderate['data_quality'] == 'moderate'
    assert 6 <= result_moderate['available_adjustments'] < 12

    # Test "limited" data quality (<6 adjustments)
    financial_data_limited = {
        'acfo_components': {
            'cash_flow_from_operations': 100000,
            'change_in_working_capital': 5000,
            'interest_financing': 8000
        }
    }

    result_limited = calculate_acfo_from_components(financial_data_limited)
    assert result_limited['data_quality'] == 'limited'


def test_acfo_consistency_checks_with_affo():
    """Test CAPEX and TI consistency validation between ACFO and AFFO"""

    # Case 1: CAPEX and TI match (should pass)
    financial_data_match = {
        'ffo_affo_components': {
            'net_income_ifrs': 50000,
            'capex_sustaining': 15000,
            'tenant_improvements': 4000
        },
        'acfo_components': {
            'cash_flow_from_operations': 100000,
            'capex_sustaining_acfo': 15000,  # Matches AFFO
            'tenant_improvements_acfo': 4000  # Matches AFFO
        }
    }

    result_match = calculate_acfo_from_components(financial_data_match)

    assert 'consistency_checks' in result_match
    assert result_match['consistency_checks']['capex_match'] is True
    assert result_match['consistency_checks']['capex_variance'] == 0
    assert result_match['consistency_checks']['tenant_improvements_match'] is True
    assert result_match['consistency_checks']['tenant_improvements_variance'] == 0

    # Case 2: CAPEX mismatch (should flag)
    financial_data_mismatch = {
        'ffo_affo_components': {
            'net_income_ifrs': 50000,
            'capex_sustaining': 15000,
            'tenant_improvements': 4000
        },
        'acfo_components': {
            'cash_flow_from_operations': 100000,
            'capex_sustaining_acfo': 18000,  # Mismatch!
            'tenant_improvements_acfo': 5000  # Mismatch!
        }
    }

    result_mismatch = calculate_acfo_from_components(financial_data_mismatch)

    assert result_mismatch['consistency_checks']['capex_match'] is False
    assert result_mismatch['consistency_checks']['capex_variance'] == 3000
    assert result_mismatch['consistency_checks']['tenant_improvements_match'] is False
    assert result_mismatch['consistency_checks']['tenant_improvements_variance'] == 1000


def test_validate_acfo_within_threshold():
    """Test ACFO validation with variance within 5% threshold"""

    calculated_acfo = 100000
    reported_acfo = 98000  # 2% variance

    result = validate_acfo(calculated_acfo, reported_acfo)

    assert result['acfo_variance_amount'] == 2000
    assert result['acfo_variance_percent'] == 2.04
    assert result['acfo_within_threshold'] is True
    assert result['validation_notes'] == []  # No issues when within threshold


def test_validate_acfo_exceeds_threshold():
    """Test ACFO validation with variance exceeding 5% threshold"""

    calculated_acfo = 100000
    reported_acfo = 90000  # 11.1% variance

    result = validate_acfo(calculated_acfo, reported_acfo)

    assert result['acfo_variance_amount'] == 10000
    assert result['acfo_variance_percent'] == 11.11
    assert result['acfo_within_threshold'] is False
    assert len(result['validation_notes']) > 0
    assert 'exceeds 5% threshold' in result['validation_notes'][0]


def test_validate_acfo_no_reported_value():
    """Test ACFO validation when issuer doesn't report ACFO"""

    calculated_acfo = 100000
    reported_acfo = None

    result = validate_acfo(calculated_acfo, reported_acfo)

    assert result['acfo_variance_amount'] is None
    assert result['acfo_variance_percent'] is None
    assert result['acfo_within_threshold'] is None
    assert len(result['validation_notes']) > 0
    assert 'missing' in result['validation_notes'][0].lower()


def test_generate_acfo_reconciliation():
    """Test ACFO reconciliation table generation"""

    financial_data = {
        'acfo_components': {
            'cash_flow_from_operations': 100000,
            'change_in_working_capital': 5000,
            'interest_financing': 8000,
            'capex_sustaining_acfo': -15000,
            'leasing_costs_external': -3000,
            'calculation_method_acfo': 'actual',
            'jv_treatment_method': 'distributions'
        }
    }

    reconciliation = generate_acfo_reconciliation(financial_data)

    assert reconciliation is not None
    assert reconciliation['starting_point']['description'] == 'Cash Flow from Operations (IFRS)'
    assert reconciliation['starting_point']['amount'] == 100000
    assert reconciliation['acfo_total']['description'] == 'Adjusted Cash Flow from Operations (ACFO)'
    assert len(reconciliation['acfo_adjustments']) > 0  # Should have adjustments
    assert reconciliation['metadata']['data_quality'] in ['strong', 'moderate', 'limited']
    assert reconciliation['metadata']['calculation_method'] == 'actual'


def test_generate_acfo_reconciliation_missing_cfo():
    """Test reconciliation generation fails when CFO missing"""

    financial_data = {
        'acfo_components': {
            # Missing cash_flow_from_operations
            'change_in_working_capital': 5000
        }
    }

    reconciliation = generate_acfo_reconciliation(financial_data)

    assert reconciliation is None


def test_format_acfo_reconciliation_table():
    """Test markdown formatting of ACFO reconciliation"""

    financial_data = {
        'acfo_components': {
            'cash_flow_from_operations': 100000,
            'change_in_working_capital': 5000,
            'interest_financing': 8000,
            'capex_sustaining_acfo': -15000
        },
        'ffo_affo_components': {
            'net_income_ifrs': 50000,
            'capex_sustaining': 15000  # Should trigger consistency check
        }
    }

    reconciliation = generate_acfo_reconciliation(financial_data)
    markdown = format_acfo_reconciliation_table(reconciliation)

    assert '## ACFO Reconciliation Table' in markdown
    assert 'Cash Flow from Operations (IFRS)' in markdown
    assert 'Adjusted Cash Flow from Operations (ACFO)' in markdown
    assert '**ACFO Adjustments (1-17):**' in markdown
    assert '**Data Quality:**' in markdown
    assert 'REALPAC ACFO White Paper for IFRS (January 2023)' in markdown
    # Should show consistency check
    assert '**Consistency Checks (vs AFFO):**' in markdown or 'capex' in markdown.lower()


def test_acfo_integration_in_reit_metrics():
    """Test ACFO calculation integrated into calculate_reit_metrics()"""

    financial_data = {
        'issuer_name': 'Test REIT',
        'reporting_date': '2025-06-30',
        'balance_sheet': {
            'total_assets': 1000000,
            'mortgages_noncurrent': 300000,
            'mortgages_current': 50000,
            'credit_facilities': 100000,
            'cash': 50000,
            'common_units_outstanding': 100000
        },
        'income_statement': {
            'noi': 50000,
            'interest_expense': 10000,
            'revenue': 80000
        },
        'ffo_affo': {
            'ffo': 40000,
            'affo': 35000,
            'ffo_per_unit': 0.40,
            'affo_per_unit': 0.35,
            'distributions_per_unit': 0.28
        },
        'acfo_components': {
            'cash_flow_from_operations': 45000,
            'change_in_working_capital': 2000,
            'interest_financing': 5000,
            'capex_sustaining_acfo': -8000,
            'leasing_costs_external': -2000,
            'tenant_improvements_acfo': -3000
        }
    }

    result = calculate_reit_metrics(financial_data)

    # Should have ACFO calculated
    assert 'acfo_calculated' in result
    assert result['acfo_calculated'] is not None
    assert 'acfo_calculation_detail' in result
    assert 'acfo_validation' in result

    # Should have ACFO value
    assert 'acfo' in result
    assert result['acfo'] == result['acfo_calculated']

    # Should have per-unit ACFO
    assert 'acfo_per_unit' in result
    assert result['acfo_per_unit'] == round(result['acfo'] / 100000, 4)

    # Should have ACFO payout ratio
    assert 'acfo_payout_ratio' in result
    assert result['acfo_payout_ratio'] == round((0.28 / result['acfo_per_unit']) * 100, 1)


def test_acfo_jv_treatment_methods():
    """Test different joint venture treatment methods"""

    # Method 1: Use JV distributions
    financial_data_distributions = {
        'acfo_components': {
            'cash_flow_from_operations': 100000,
            'jv_distributions': 5000,  # Use distributions method
            'jv_treatment_method': 'distributions'
        }
    }

    result_dist = calculate_acfo_from_components(financial_data_distributions)
    assert result_dist['jv_treatment_method'] == 'distributions'
    assert result_dist['adjustments_detail']['adjustment_3a_jv_distributions'] == 5000

    # Method 2: Use JV ACFO calculation
    financial_data_acfo = {
        'acfo_components': {
            'cash_flow_from_operations': 100000,
            'jv_acfo': 6000,  # Use ACFO method
            'jv_notional_interest': 500,
            'jv_treatment_method': 'acfo'
        }
    }

    result_acfo = calculate_acfo_from_components(financial_data_acfo)
    assert result_acfo['jv_treatment_method'] == 'acfo'
    assert result_acfo['adjustments_detail']['adjustment_3b_jv_acfo'] == 6000
    assert result_acfo['adjustments_detail']['adjustment_3c_jv_notional_interest'] == 500


def test_acfo_rou_asset_adjustments():
    """Test IFRS 16 Right of Use Asset adjustments"""

    financial_data = {
        'acfo_components': {
            'cash_flow_from_operations': 100000,
            # IFRS 16 adjustments (4 components)
            'rou_sublease_principal_received': 1000,
            'rou_sublease_interest_received': 500,
            'rou_lease_principal_paid': -2000,
            'rou_depreciation_amortization': 1500
        }
    }

    result = calculate_acfo_from_components(financial_data)

    assert result['adjustments_detail']['adjustment_16a_rou_sublease_principal_received'] == 1000
    assert result['adjustments_detail']['adjustment_16b_rou_sublease_interest_received'] == 500
    assert result['adjustments_detail']['adjustment_16c_rou_lease_principal_paid'] == -2000
    assert result['adjustments_detail']['adjustment_16d_rou_depreciation_amortization'] == 1500

    # ACFO should include all ROU adjustments
    expected_rou_impact = 1000 + 500 - 2000 + 1500
    assert result['total_adjustments'] == expected_rou_impact
    assert result['acfo_calculated'] == 100000 + expected_rou_impact


def test_acfo_puttable_instruments():
    """Test IAS 32 puttable instruments adjustments"""

    financial_data = {
        'acfo_components': {
            'cash_flow_from_operations': 100000,
            # IAS 32 adjustments
            'puttable_instruments_distributions': 3000,
            'nci_puttable_units': -1000
        }
    }

    result = calculate_acfo_from_components(financial_data)

    assert result['adjustments_detail']['adjustment_15_puttable_instruments_distributions'] == 3000
    assert result['adjustments_detail']['adjustment_17b_nci_puttable_units'] == -1000

    expected_acfo = 100000 + 3000 - 1000
    assert result['acfo_calculated'] == expected_acfo


def test_acfo_reserve_methodology():
    """Test reserve methodology metadata"""

    financial_data = {
        'acfo_components': {
            'cash_flow_from_operations': 100000,
            'capex_sustaining_acfo': -15000,
            'calculation_method_acfo': 'reserve',
            'reserve_methodology_acfo': '3-year rolling average of actual CAPEX'
        }
    }

    result = calculate_acfo_from_components(financial_data)

    assert result['calculation_method'] == 'reserve'
    assert result['reserve_methodology'] == '3-year rolling average of actual CAPEX'


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
