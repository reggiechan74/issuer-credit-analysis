"""
Unit tests for burn rate and cash runway calculations

Tests cover:
- calculate_burn_rate() - Monthly/annual burn rate from negative AFCF
- calculate_cash_runway() - Months until cash depletion
- assess_liquidity_risk() - Risk level assessment
- calculate_sustainable_burn_rate() - Maximum sustainable burn rate

Author: AI Assistant (Claude Code)
Date: 2025-10-20
Issue: #7 - Implement Cash Burn Rate and Runway Analysis
"""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from calculate_credit_metrics import (
    calculate_burn_rate,
    calculate_cash_runway,
    assess_liquidity_risk,
    calculate_sustainable_burn_rate
)


# ============================================================================
# Test calculate_burn_rate()
# ============================================================================

def test_burn_rate_with_afcf_below_financing_needs():
    """Test burn rate when AFCF cannot cover financing needs"""
    financial_data = {
        'cash_flow_financing': {
            'debt_principal_repayments': -18000,
            'distributions_common': -20000,
            'new_debt_issuances': 5000,
            'equity_issuances': 0
        },
        'coverage_ratios': {
            'annualized_interest_expense': 22000
        }
    }
    afcf_metrics = {
        'afcf': 25000,  # Positive AFCF, but insufficient for financing
        'data_quality': 'strong'
    }

    # Net Financing Needs = (22000 interest + 18000 principal + 20000 dist) - 5000 new debt = 55000
    # AFCF = 25000
    # Burn Rate = 55000 - 25000 = 30000 annually

    result = calculate_burn_rate(financial_data, afcf_metrics)

    assert result['applicable'] is True
    assert result['afcf'] == 25000
    assert result['net_financing_needs'] == 55000
    assert result['self_funding_ratio'] == pytest.approx(0.45, abs=0.01)  # 25000/55000
    assert result['annualized_burn_rate'] == 30000
    assert result['monthly_burn_rate'] == 2500
    assert result['data_quality'] == 'strong'


def test_burn_rate_with_afcf_exceeding_financing_needs():
    """Test that burn rate is not applicable when AFCF exceeds financing needs"""
    financial_data = {
        'cash_flow_financing': {
            'debt_principal_repayments': -10000,
            'distributions_common': -15000,
            'new_debt_issuances': 5000
        },
        'coverage_ratios': {
            'annualized_interest_expense': 12000
        }
    }
    afcf_metrics = {
        'afcf': 40000,  # Exceeds net financing needs
        'data_quality': 'strong'
    }

    # Net Financing Needs = (12000 + 10000 + 15000) - 5000 = 32000
    # AFCF = 40000 (exceeds needs by 8000)

    result = calculate_burn_rate(financial_data, afcf_metrics)

    assert result['applicable'] is False
    assert result['monthly_burn_rate'] is None
    assert result['self_funding_ratio'] == pytest.approx(1.25, abs=0.01)  # 40000/32000
    assert 'covers financing needs' in result['reason']
    assert result['monthly_surplus'] == pytest.approx(666.67, abs=1)


def test_burn_rate_missing_financing_data():
    """Test burn rate when financing data is missing"""
    financial_data = {}  # No cash_flow_financing or coverage_ratios
    afcf_metrics = {
        'afcf': 25000,
        'data_quality': 'moderate'
    }

    result = calculate_burn_rate(financial_data, afcf_metrics)

    assert result['applicable'] is False
    assert 'missing financing data' in result['reason']
    assert result['data_quality'] == 'limited'


def test_burn_rate_with_missing_afcf_metrics():
    """Test burn rate when AFCF metrics not provided"""
    financial_data = {}
    afcf_metrics = None

    result = calculate_burn_rate(financial_data, afcf_metrics)

    assert result['applicable'] is False
    assert result['reason'] == 'AFCF not calculated - missing AFCF metrics'
    assert result['data_quality'] == 'none'


def test_burn_rate_with_none_afcf():
    """Test burn rate when AFCF is None (calculation failed)"""
    financial_data = {}
    afcf_metrics = {
        'afcf': None
    }

    result = calculate_burn_rate(financial_data, afcf_metrics)

    assert result['applicable'] is False
    assert result['reason'] == 'AFCF is None - insufficient data for calculation'


def test_burn_rate_with_afcf_coverage_input():
    """Test burn rate using pre-calculated AFCF coverage metrics"""
    financial_data = {}
    afcf_metrics = {
        'afcf': 25000,
        'data_quality': 'strong'
    }
    afcf_coverage = {
        'net_financing_needs': 55000,
        'afcf_self_funding_ratio': 0.45
    }

    result = calculate_burn_rate(financial_data, afcf_metrics, afcf_coverage)

    assert result['applicable'] is True
    assert result['net_financing_needs'] == 55000
    assert result['annualized_burn_rate'] == 30000  # 55000 - 25000
    assert result['monthly_burn_rate'] == 2500


# ============================================================================
# Test calculate_cash_runway()
# ============================================================================

def test_cash_runway_comfortable():
    """Test cash runway calculation with comfortable liquidity (>24 months)"""
    financial_data = {
        'reporting_date': '2025-06-30',
        'liquidity': {
            'cash_and_equivalents': 65000000,
            'marketable_securities': 20000000,
            'restricted_cash': 5000000,
            'undrawn_credit_facilities': 150000000
        }
    }

    burn_rate_metrics = {
        'applicable': True,
        'monthly_burn_rate': 1833333.33,
        'annualized_burn_rate': 22000000
    }

    result = calculate_cash_runway(financial_data, burn_rate_metrics)

    assert result['available_cash'] == 80000000  # 65M + 20M - 5M
    assert result['total_available_liquidity'] == 230000000  # 80M + 150M
    assert result['runway_months'] == pytest.approx(43.6, abs=0.2)
    assert result['runway_years'] == pytest.approx(3.6, abs=0.1)
    assert result['extended_runway_months'] == pytest.approx(125.5, abs=0.5)
    assert result['extended_runway_years'] == pytest.approx(10.5, abs=0.1)
    assert result['data_quality'] == 'strong'
    assert result['error'] is None
    assert result['depletion_date'] is not None  # Should calculate a date


def test_cash_runway_moderate_risk():
    """Test cash runway with moderate liquidity (12-24 months)"""
    financial_data = {
        'liquidity': {
            'cash_and_equivalents': 40000000,
            'marketable_securities': 10000000,
            'restricted_cash': 2000000,
            'undrawn_credit_facilities': 75000000
        }
    }

    burn_rate_metrics = {
        'applicable': True,
        'monthly_burn_rate': 5000000  # High burn rate
    }

    result = calculate_cash_runway(financial_data, burn_rate_metrics)

    assert result['available_cash'] == 48000000
    assert result['runway_months'] == pytest.approx(9.6, abs=0.1)
    assert result['runway_years'] == pytest.approx(0.8, abs=0.1)
    assert result['extended_runway_months'] == pytest.approx(24.6, abs=0.1)


def test_cash_runway_critical():
    """Test cash runway with critical liquidity (<6 months)"""
    financial_data = {
        'liquidity': {
            'cash_and_equivalents': 15000000,
            'marketable_securities': 3000000,
            'restricted_cash': 1000000,
            'undrawn_credit_facilities': 25000000
        }
    }

    burn_rate_metrics = {
        'applicable': True,
        'monthly_burn_rate': 3333333  # $40M annual burn
    }

    result = calculate_cash_runway(financial_data, burn_rate_metrics)

    assert result['available_cash'] == 17000000
    assert result['runway_months'] == pytest.approx(5.1, abs=0.1)
    assert result['runway_years'] == pytest.approx(0.4, abs=0.1)
    assert result['data_quality'] in ['strong', 'moderate']


def test_cash_runway_no_available_cash():
    """Test cash runway when no available cash (immediate crisis)"""
    financial_data = {
        'liquidity': {
            'cash_and_equivalents': 0,
            'marketable_securities': 0,
            'restricted_cash': 0,
            'undrawn_credit_facilities': 50000000
        }
    }

    burn_rate_metrics = {
        'applicable': True,
        'monthly_burn_rate': 2000000
    }

    result = calculate_cash_runway(financial_data, burn_rate_metrics)

    assert result['error'] == 'No available cash - immediate liquidity crisis'
    assert result['available_cash'] == 0
    assert result['runway_months'] is None


def test_cash_runway_not_applicable():
    """Test cash runway when burn rate not applicable (positive AFCF)"""
    financial_data = {
        'liquidity': {
            'cash_and_equivalents': 50000000
        }
    }

    burn_rate_metrics = {
        'applicable': False,
        'reason': 'Positive AFCF'
    }

    result = calculate_cash_runway(financial_data, burn_rate_metrics)

    assert result['error'] == 'Burn rate not applicable - AFCF is not negative'
    assert result['runway_months'] is None


def test_cash_runway_no_liquidity_data():
    """Test cash runway when liquidity section missing"""
    financial_data = {}

    burn_rate_metrics = {
        'applicable': True,
        'monthly_burn_rate': 2000000
    }

    result = calculate_cash_runway(financial_data, burn_rate_metrics)

    assert result['error'] == 'No liquidity section in financial data'
    assert result['data_quality'] == 'none'


# ============================================================================
# Test assess_liquidity_risk()
# ============================================================================

def test_liquidity_risk_critical():
    """Test CRITICAL risk level (<6 months runway)"""
    runway_metrics = {
        'runway_months': 5.1,
        'runway_years': 0.4,
        'available_cash': 17000000,
        'data_quality': 'strong'
    }

    result = assess_liquidity_risk(runway_metrics)

    assert result['risk_level'] == 'CRITICAL'
    assert result['risk_score'] == 4
    assert 'Immediate financing required' in result['assessment']
    assert '🚨' in result['assessment']
    assert len(result['warning_flags']) > 0
    assert 'Cash depletion imminent' in result['warning_flags']
    assert len(result['recommendations']) > 0
    assert any('Suspend or reduce distributions' in rec for rec in result['recommendations'])


def test_liquidity_risk_high():
    """Test HIGH risk level (6-12 months runway)"""
    runway_metrics = {
        'runway_months': 9.6,
        'runway_years': 0.8,
        'available_cash': 48000000,
        'data_quality': 'strong'
    }

    result = assess_liquidity_risk(runway_metrics)

    assert result['risk_level'] == 'HIGH'
    assert result['risk_score'] == 3
    assert 'Near-term capital raise required' in result['assessment']
    assert len(result['warning_flags']) > 0
    assert len(result['recommendations']) > 0


def test_liquidity_risk_moderate():
    """Test MODERATE risk level (12-24 months runway)"""
    runway_metrics = {
        'runway_months': 18.0,
        'runway_years': 1.5,
        'available_cash': 60000000,
        'data_quality': 'strong'
    }

    result = assess_liquidity_risk(runway_metrics)

    assert result['risk_level'] == 'MODERATE'
    assert result['risk_score'] == 2
    assert 'Plan financing within 12 months' in result['assessment']
    assert len(result['recommendations']) > 0


def test_liquidity_risk_low():
    """Test LOW risk level (>24 months runway)"""
    runway_metrics = {
        'runway_months': 43.6,
        'runway_years': 3.6,
        'available_cash': 80000000,
        'data_quality': 'strong'
    }

    result = assess_liquidity_risk(runway_metrics)

    assert result['risk_level'] == 'LOW'
    assert result['risk_score'] == 1
    assert 'Adequate liquidity runway' in result['assessment']
    assert '✓' in result['assessment']
    assert len(result['warning_flags']) == 0
    assert len(result['recommendations']) > 0


def test_liquidity_risk_extended_runway_warning():
    """Test warning when extended runway (with facilities) is still concerning"""
    runway_metrics = {
        'runway_months': 15.0,  # MODERATE (12-24 months)
        'extended_runway_months': 10.0,  # But extended is < 12 months
        'available_cash': 45000000,
        'data_quality': 'strong'
    }

    result = assess_liquidity_risk(runway_metrics)

    assert result['risk_level'] == 'MODERATE'
    # Should have additional warning about limited extended runway
    assert len(result['warning_flags']) > 0


def test_liquidity_risk_no_data():
    """Test risk assessment when runway data unavailable"""
    runway_metrics = {
        'error': 'No liquidity section in financial data',
        'runway_months': None
    }

    result = assess_liquidity_risk(runway_metrics)

    assert result['risk_level'] == 'N/A'
    assert result['risk_score'] == 0
    assert 'No liquidity section' in result['assessment']


# ============================================================================
# Test calculate_sustainable_burn_rate()
# ============================================================================

def test_sustainable_burn_above_sustainable():
    """Test sustainable burn rate when actual burn exceeds sustainable level"""
    financial_data = {
        'liquidity': {
            'cash_and_equivalents': 48000000,
            'marketable_securities': 0,
            'restricted_cash': 0
        }
    }

    burn_rate_metrics = {
        'applicable': True,
        'monthly_burn_rate': 5000000,
        'data_quality': 'strong'
    }

    result = calculate_sustainable_burn_rate(financial_data, burn_rate_metrics, target_runway_months=24)

    assert result['target_runway_months'] == 24
    assert result['available_cash'] == 48000000
    assert result['sustainable_monthly_burn'] == 2000000  # 48M / 24 months
    assert result['actual_monthly_burn'] == 5000000
    assert result['excess_burn_per_month'] == 3000000  # 5M - 2M
    assert result['excess_burn_annualized'] == 36000000  # 3M * 12
    assert 'Above sustainable' in result['status']
    assert 'Overspending' in result['status']


def test_sustainable_burn_below_sustainable():
    """Test sustainable burn rate when actual burn is below sustainable level"""
    financial_data = {
        'liquidity': {
            'cash_and_equivalents': 80000000,
            'marketable_securities': 20000000,
            'restricted_cash': 5000000
        }
    }

    burn_rate_metrics = {
        'applicable': True,
        'monthly_burn_rate': 1833333,  # ~$22M annual
        'data_quality': 'strong'
    }

    result = calculate_sustainable_burn_rate(financial_data, burn_rate_metrics, target_runway_months=24)

    assert result['available_cash'] == 95000000  # 80M + 20M - 5M
    assert result['sustainable_monthly_burn'] == pytest.approx(3958333, abs=10000)  # 95M / 24
    assert result['excess_burn_per_month'] < 0  # Negative = under sustainable
    assert 'Below sustainable' in result['status']
    assert 'cushion' in result['status']


def test_sustainable_burn_not_applicable():
    """Test sustainable burn when burn rate not applicable (positive AFCF)"""
    financial_data = {
        'liquidity': {
            'cash_and_equivalents': 50000000
        }
    }

    burn_rate_metrics = {
        'applicable': False,
        'reason': 'Positive AFCF'
    }

    result = calculate_sustainable_burn_rate(financial_data, burn_rate_metrics)

    assert result['status'] == 'N/A - REIT is cash-generative'
    assert result['sustainable_monthly_burn'] is None


def test_sustainable_burn_no_liquidity_data():
    """Test sustainable burn when liquidity data missing"""
    financial_data = {}

    burn_rate_metrics = {
        'applicable': True,
        'monthly_burn_rate': 2000000
    }

    result = calculate_sustainable_burn_rate(financial_data, burn_rate_metrics)

    assert result['available_cash'] is None
    assert result['sustainable_monthly_burn'] is None


def test_sustainable_burn_custom_target_runway():
    """Test sustainable burn with custom target runway (36 months)"""
    financial_data = {
        'liquidity': {
            'cash_and_equivalents': 72000000,
            'marketable_securities': 0,
            'restricted_cash': 0
        }
    }

    burn_rate_metrics = {
        'applicable': True,
        'monthly_burn_rate': 3000000
    }

    result = calculate_sustainable_burn_rate(financial_data, burn_rate_metrics, target_runway_months=36)

    assert result['target_runway_months'] == 36
    assert result['sustainable_monthly_burn'] == 2000000  # 72M / 36 months
    assert result['excess_burn_per_month'] == 1000000  # 3M - 2M


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_burn_rate_pipeline_afcf_below_needs():
    """Test complete burn rate pipeline when AFCF < Net Financing Needs"""
    financial_data = {
        'reporting_date': '2025-06-30',
        'cash_flow_financing': {
            'debt_principal_repayments': -25000000,
            'distributions_common': -19000000,
            'new_debt_issuances': 10000000,
            'equity_issuances': 5000000
        },
        'coverage_ratios': {
            'annualized_interest_expense': 22000000
        },
        'liquidity': {
            'cash_and_equivalents': 65000000,
            'marketable_securities': 20000000,
            'restricted_cash': 5000000,
            'undrawn_credit_facilities': 150000000
        }
    }

    afcf_metrics = {
        'afcf': 28000000,  # Positive AFCF, but below net financing needs
        'data_quality': 'strong'
    }

    # Net Financing Needs = (22M interest + 25M principal + 19M dist) - 15M new financing = 51M
    # AFCF = 28M
    # Burn Rate = 51M - 28M = 23M annually

    # Step 1: Calculate burn rate
    burn_rate = calculate_burn_rate(financial_data, afcf_metrics)
    assert burn_rate['applicable'] is True
    assert burn_rate['net_financing_needs'] == 51000000
    assert burn_rate['annualized_burn_rate'] == 23000000
    assert burn_rate['monthly_burn_rate'] == pytest.approx(1916667, abs=10)

    # Step 2: Calculate cash runway
    # Available Cash = 65M + 20M - 5M = 80M
    # Monthly Burn = 23M / 12 = 1.917M
    # Runway = 80M / 1.917M = 41.7 months
    runway = calculate_cash_runway(financial_data, burn_rate)
    assert runway['available_cash'] == 80000000
    assert runway['runway_months'] == pytest.approx(41.7, abs=0.2)
    assert runway['error'] is None

    # Step 3: Assess liquidity risk
    risk = assess_liquidity_risk(runway)
    assert risk['risk_level'] == 'LOW'  # > 24 months
    assert risk['risk_score'] == 1

    # Step 4: Calculate sustainable burn
    sustainable = calculate_sustainable_burn_rate(financial_data, burn_rate, target_runway_months=24)
    # Sustainable = 80M / 24 = 3.33M/month
    # Actual = 1.917M/month
    # Status: Below sustainable (good)
    assert 'Below sustainable' in sustainable['status']


def test_full_burn_rate_pipeline_afcf_exceeds_needs():
    """Test complete pipeline when AFCF exceeds financing needs (no burn)"""
    financial_data = {
        'cash_flow_financing': {
            'debt_principal_repayments': -8000000,
            'distributions_common': -12000000,
            'new_debt_issuances': 5000000
        },
        'coverage_ratios': {
            'annualized_interest_expense': 10000000
        },
        'liquidity': {
            'cash_and_equivalents': 50000000
        }
    }

    afcf_metrics = {
        'afcf': 35000000,  # Exceeds net financing needs
        'data_quality': 'strong'
    }

    # Net Financing Needs = (10M + 8M + 12M) - 5M = 25M
    # AFCF = 35M (exceeds by 10M)

    # Step 1: Calculate burn rate
    burn_rate = calculate_burn_rate(financial_data, afcf_metrics)
    assert burn_rate['applicable'] is False
    assert burn_rate['self_funding_ratio'] == 1.4  # 35M / 25M
    assert 'covers financing needs' in burn_rate['reason']

    # Step 2: Runway should not calculate
    runway = calculate_cash_runway(financial_data, burn_rate)
    assert runway['error'] == 'Burn rate not applicable - AFCF is not negative'

    # Step 3: Risk assessment should handle this gracefully
    risk = assess_liquidity_risk(runway)
    assert risk['risk_level'] == 'N/A'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
