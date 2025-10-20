#!/usr/bin/env python3
"""
Tests for FFO/AFFO Calculation Functions

Tests the REALPAC methodology implementation for calculating
Funds From Operations (FFO) and Adjusted Funds From Operations (AFFO)
when issuers don't report these metrics.

Issue #4: Implement AFFO Calculation When Issuer Does Not Provide It
"""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from calculate_credit_metrics import (
    calculate_ffo_from_components,
    calculate_affo_from_ffo,
    validate_ffo_affo,
    calculate_reit_metrics,
    generate_ffo_affo_reconciliation,
    format_reconciliation_table
)


# ==================== Test Fixtures ====================

@pytest.fixture
def complete_ffo_components():
    """Complete FFO components dataset with all adjustments (A-U)"""
    return {
        'issuer_name': 'Test REIT Inc.',
        'reporting_date': '2025-06-30',
        'reporting_period': 'Q2 2025',
        'currency': 'CAD',
        'balance_sheet': {
            'common_units_outstanding': 100000  # 100M units (in thousands)
        },
        'ffo_affo_components': {
            'net_income_ifrs': 50000,  # Starting point: $50M
            # FFO Adjustments (A-U)
            'unrealized_fv_changes': 20000,  # A: +$20M (add back unrealized gains)
            'depreciation_real_estate': 15000,  # B: +$15M (add back depreciation)
            'amortization_tenant_allowances': 2000,  # C: +$2M
            'amortization_intangibles': 1000,  # D: +$1M
            'gains_losses_property_sales': -5000,  # E: -$5M (remove realized gains)
            'tax_on_disposals': 1500,  # F: +$1.5M
            'deferred_taxes': 3000,  # G: +$3M
            'impairment_losses_reversals': 0,  # H: $0
            'revaluation_gains_losses': 0,  # I: $0
            'transaction_costs_business_comb': 500,  # J: +$0.5M
            'foreign_exchange_gains_losses': -200,  # K: -$0.2M
            'sale_foreign_operations': 0,  # L: $0
            'fv_changes_hedges': 800,  # M: +$0.8M
            'goodwill_impairment': 0,  # N: $0
            'puttable_instruments_effects': 0,  # O: $0
            'discontinued_operations': 0,  # P: $0
            'equity_accounted_adjustments': 400,  # Q: +$0.4M
            'incremental_leasing_costs': 300,  # R: +$0.3M
            'property_taxes_ifric21': 600,  # S: +$0.6M
            'rou_asset_revenue_expense': 100,  # T: +$0.1M
            'non_controlling_interests_ffo': 1000,  # U: -$1M (subtract NCI)
            # AFFO Adjustments (V-Z)
            'capex_sustaining': 8000,  # V: -$8M sustaining CAPEX
            'capex_development': 12000,  # For disclosure only (excluded from AFFO)
            'leasing_costs': 2500,  # W: -$2.5M leasing costs
            'tenant_improvements': 3000,  # X: -$3M tenant improvements
            'straight_line_rent': 500,  # Y: -$0.5M straight-line adjustment
            'non_controlling_interests_affo': 200,  # Z: -$0.2M NCI
            'calculation_method': 'actual',
            'reserve_methodology': None,
            'missing_adjustments': []
        }
    }


@pytest.fixture
def partial_ffo_components():
    """Partial FFO components dataset (missing some adjustments)"""
    return {
        'issuer_name': 'Partial Data REIT',
        'reporting_date': '2025-06-30',
        'ffo_affo_components': {
            'net_income_ifrs': 30000,
            # Only core adjustments present
            'unrealized_fv_changes': 10000,
            'depreciation_real_estate': 8000,
            'deferred_taxes': 2000,
            # Missing most other adjustments
            'capex_sustaining': 5000,
            'leasing_costs': 1500,
            'calculation_method': 'actual'
        }
    }


@pytest.fixture
def issuer_reported_ffo_affo():
    """Dataset with issuer-reported FFO/AFFO for validation testing"""
    return {
        'issuer_name': 'Reporting REIT',
        'reporting_date': '2025-06-30',
        'balance_sheet': {
            'common_units_outstanding': 100000  # 100M units (in thousands)
        },
        'ffo_affo': {
            'ffo': 89000,  # Issuer-reported FFO
            'affo': 75000,  # Issuer-reported AFFO
            'ffo_per_unit': 0.89,
            'affo_per_unit': 0.75,
            'distributions_per_unit': 0.60
        },
        'ffo_affo_components': {
            'net_income_ifrs': 50000,
            'unrealized_fv_changes': 20000,
            'depreciation_real_estate': 15000,
            'amortization_tenant_allowances': 2000,
            'amortization_intangibles': 1000,
            'gains_losses_property_sales': -5000,
            'deferred_taxes': 3000,
            'non_controlling_interests_ffo': 1000,
            'capex_sustaining': 8000,
            'leasing_costs': 2500,
            'tenant_improvements': 3000,
            'straight_line_rent': 500,
            'calculation_method': 'actual'
        }
    }


# ==================== FFO Calculation Tests ====================

def test_calculate_ffo_complete_data(complete_ffo_components):
    """Test FFO calculation with all components available"""
    result = calculate_ffo_from_components(complete_ffo_components)

    # Expected FFO = 50000 + 20000 + 15000 + 2000 + 1000 - 5000 + 1500 + 3000
    #                + 500 - 200 + 800 + 400 + 300 + 600 + 100 - 1000
    # = 50000 + 39000 = 89000

    assert result is not None
    assert result['ffo_calculated'] == 89000
    assert result['net_income_ifrs'] == 50000
    assert result['total_adjustments'] == 39000
    assert result['data_quality'] == 'strong'  # All 21 adjustments present
    assert result['available_adjustments'] == 21
    assert len(result['missing_components']) == 0


def test_calculate_ffo_partial_data(partial_ffo_components):
    """Test FFO calculation with missing components"""
    result = calculate_ffo_from_components(partial_ffo_components)

    # Expected FFO = 30000 + 10000 + 8000 + 2000 = 50000
    assert result is not None
    assert result['ffo_calculated'] == 50000
    assert result['net_income_ifrs'] == 30000
    assert result['total_adjustments'] == 20000
    assert result['data_quality'] in ['moderate', 'limited']  # Not all adjustments
    assert len(result['missing_components']) > 0


def test_calculate_ffo_missing_net_income():
    """Test FFO calculation fails gracefully without net income"""
    data = {
        'ffo_affo_components': {
            # Missing net_income_ifrs
            'unrealized_fv_changes': 10000
        }
    }

    result = calculate_ffo_from_components(data)

    assert result['ffo_calculated'] is None
    assert 'error' in result
    assert 'net_income_ifrs' in result['error']


def test_calculate_ffo_no_components_section():
    """Test FFO calculation with no components section"""
    data = {
        'issuer_name': 'Test REIT'
        # No ffo_affo_components section
    }

    result = calculate_ffo_from_components(data)

    assert result['ffo_calculated'] is None
    assert result['data_quality'] == 'none'


# ==================== AFFO Calculation Tests ====================

def test_calculate_affo_from_ffo(complete_ffo_components):
    """Test AFFO calculation from FFO"""
    ffo = 89000  # From previous test

    result = calculate_affo_from_ffo(complete_ffo_components, ffo)

    # Expected AFFO = 89000 - 8000 - 2500 - 3000 - 500 - 200
    # = 89000 - 14200 = 74800

    assert result is not None
    assert result['affo_calculated'] == 74800
    assert result['ffo_starting_point'] == 89000
    assert result['total_adjustments'] == 14200
    assert result['data_quality'] == 'strong'  # All 5 AFFO adjustments present
    assert result['available_adjustments'] == 5
    assert result['calculation_method'] == 'actual'


def test_calculate_affo_partial_components(partial_ffo_components):
    """Test AFFO calculation with missing components"""
    ffo = 50000

    result = calculate_affo_from_ffo(partial_ffo_components, ffo)

    # Expected AFFO = 50000 - 5000 - 1500 = 43500
    assert result is not None
    assert result['affo_calculated'] == 43500
    assert result['data_quality'] in ['moderate', 'limited']
    assert len(result['missing_components']) > 0


# ==================== Validation Tests ====================

def test_validation_within_threshold():
    """Test validation when calculated vs reported variance < 5%"""
    calculated_ffo = 89000
    calculated_affo = 75000
    reported_ffo = 90000  # 1.1% variance
    reported_affo = 76000  # 1.3% variance

    result = validate_ffo_affo(calculated_ffo, calculated_affo, reported_ffo, reported_affo)

    assert result['ffo_variance_amount'] == -1000
    assert abs(result['ffo_variance_percent']) < 5.0
    assert result['ffo_within_threshold'] is True

    assert result['affo_variance_amount'] == -1000
    assert abs(result['affo_variance_percent']) < 5.0
    assert result['affo_within_threshold'] is True

    assert 'validated' in result['validation_summary']


def test_validation_outside_threshold():
    """Test validation when calculated vs reported variance > 5%"""
    calculated_ffo = 89000
    calculated_affo = 75000
    reported_ffo = 100000  # 11% variance (outside threshold)
    reported_affo = 85000  # 11.8% variance (outside threshold)

    result = validate_ffo_affo(calculated_ffo, calculated_affo, reported_ffo, reported_affo)

    assert result['ffo_variance_amount'] == -11000
    assert abs(result['ffo_variance_percent']) > 5.0
    assert result['ffo_within_threshold'] is False

    assert result['affo_variance_amount'] == -10000
    assert abs(result['affo_variance_percent']) > 5.0
    assert result['affo_within_threshold'] is False

    assert 'exceeds 5% threshold' in result['validation_summary']


def test_validation_no_reported_values():
    """Test validation when issuer didn't report FFO/AFFO"""
    calculated_ffo = 89000
    calculated_affo = 75000
    reported_ffo = None
    reported_affo = None

    result = validate_ffo_affo(calculated_ffo, calculated_affo, reported_ffo, reported_affo)

    assert result['ffo_variance_percent'] is None
    assert result['affo_variance_percent'] is None
    assert 'did not report' in result['validation_summary']


# ==================== Enhanced REIT Metrics Tests ====================

def test_calculate_reit_metrics_issuer_reported(issuer_reported_ffo_affo):
    """Test REIT metrics with issuer-reported FFO/AFFO"""
    result = calculate_reit_metrics(issuer_reported_ffo_affo)

    assert result['ffo'] == 89000  # Issuer-reported
    assert result['affo'] == 75000  # Issuer-reported
    assert result['source'] == 'issuer_reported'
    assert 'ffo_calculated' in result  # Also includes calculated values
    assert 'validation' in result  # Includes validation


def test_calculate_reit_metrics_calculated_only(complete_ffo_components):
    """Test REIT metrics with calculated FFO/AFFO only (no issuer-reported)"""
    # Remove issuer-reported section
    data = complete_ffo_components.copy()

    result = calculate_reit_metrics(data)

    assert result['ffo'] == 89000  # Calculated (in thousands)
    assert result['affo'] == 74800  # Calculated (in thousands)
    assert result['source'] == 'calculated_from_components'
    assert 'ffo_per_unit' in result
    # FFO per unit: 89,000 thousands / 100,000 thousand units = 0.89
    assert result['ffo_per_unit'] == 0.89  # 89000 / 100000 = 0.89


def test_calculate_reit_metrics_no_data():
    """Test REIT metrics with insufficient data"""
    data = {
        'issuer_name': 'Test REIT'
        # No ffo_affo or ffo_affo_components
    }

    with pytest.raises(KeyError) as exc_info:
        calculate_reit_metrics(data)

    assert 'Missing FFO/AFFO data' in str(exc_info.value)


# ==================== Reconciliation Table Tests ====================

def test_generate_reconciliation_complete(complete_ffo_components):
    """Test reconciliation table generation with complete data"""
    result = generate_ffo_affo_reconciliation(complete_ffo_components)

    assert result is not None
    assert result['starting_point']['amount'] == 50000
    assert result['ffo_total']['amount'] == 89000
    assert result['affo_total']['amount'] == 74800
    assert len(result['ffo_adjustments']) > 0
    assert len(result['affo_adjustments']) > 0
    assert result['metadata']['ffo_data_quality'] == 'strong'


def test_format_reconciliation_table(complete_ffo_components):
    """Test markdown formatting of reconciliation table"""
    reconciliation = generate_ffo_affo_reconciliation(complete_ffo_components)
    markdown = format_reconciliation_table(reconciliation)

    assert 'IFRS Net Income' in markdown
    assert 'Funds From Operations (FFO)' in markdown
    assert 'Adjusted Funds From Operations (AFFO)' in markdown
    assert 'REALPAC' in markdown
    assert '50,000' in markdown  # Net income
    assert '89,000' in markdown  # FFO
    assert '74,800' in markdown  # AFFO


def test_reconciliation_no_data():
    """Test reconciliation with insufficient data"""
    data = {'issuer_name': 'Test REIT'}

    result = generate_ffo_affo_reconciliation(data)
    assert result is None

    markdown = format_reconciliation_table(None)
    assert 'Insufficient data' in markdown


# ==================== Edge Cases & Error Handling ====================

def test_zero_ffo_affo():
    """Test handling of zero FFO/AFFO values"""
    data = {
        'ffo_affo_components': {
            'net_income_ifrs': 0,
            'capex_sustaining': 0
        }
    }

    ffo_result = calculate_ffo_from_components(data)
    assert ffo_result['ffo_calculated'] == 0

    affo_result = calculate_affo_from_ffo(data, 0)
    assert affo_result['affo_calculated'] == 0


def test_negative_net_income():
    """Test FFO calculation with negative IFRS net income (loss)"""
    data = {
        'ffo_affo_components': {
            'net_income_ifrs': -10000,  # Loss
            'unrealized_fv_changes': 15000,  # Add back
            'depreciation_real_estate': 8000
        }
    }

    result = calculate_ffo_from_components(data)

    # FFO = -10000 + 15000 + 8000 = 13000
    assert result['ffo_calculated'] == 13000


def test_large_nci_adjustment():
    """Test handling of large non-controlling interest adjustments"""
    data = {
        'ffo_affo_components': {
            'net_income_ifrs': 50000,
            'unrealized_fv_changes': 20000,
            'non_controlling_interests_ffo': 15000,  # Large NCI (subtract)
            'capex_sustaining': 5000,
            'non_controlling_interests_affo': 2000
        }
    }

    ffo_result = calculate_ffo_from_components(data)
    # FFO = 50000 + 20000 - 15000 = 55000
    assert ffo_result['ffo_calculated'] == 55000

    affo_result = calculate_affo_from_ffo(data, ffo_result['ffo_calculated'])
    # AFFO = 55000 - 5000 - 2000 = 48000
    assert affo_result['affo_calculated'] == 48000


# ==================== Integration Test ====================

def test_full_pipeline_integration(complete_ffo_components):
    """Integration test: Complete pipeline from components to reconciliation"""
    # Step 1: Calculate FFO
    ffo_result = calculate_ffo_from_components(complete_ffo_components)
    assert ffo_result['ffo_calculated'] == 89000

    # Step 2: Calculate AFFO
    affo_result = calculate_affo_from_ffo(
        complete_ffo_components,
        ffo_result['ffo_calculated']
    )
    assert affo_result['affo_calculated'] == 74800

    # Step 3: Validate (no issuer-reported values)
    validation = validate_ffo_affo(
        ffo_result['ffo_calculated'],
        affo_result['affo_calculated'],
        None,
        None
    )
    assert 'did not report' in validation['validation_summary']

    # Step 4: Generate reconciliation
    reconciliation = generate_ffo_affo_reconciliation(complete_ffo_components)
    assert reconciliation is not None
    assert reconciliation['ffo_total']['amount'] == 89000
    assert reconciliation['affo_total']['amount'] == 74800

    # Step 5: Format as markdown
    markdown = format_reconciliation_table(reconciliation)
    assert '89,000' in markdown
    assert '74,800' in markdown

    # Step 6: Calculate complete REIT metrics
    reit_metrics = calculate_reit_metrics(complete_ffo_components)
    assert reit_metrics['ffo'] == 89000
    assert reit_metrics['affo'] == 74800
    assert reit_metrics['source'] == 'calculated_from_components'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
