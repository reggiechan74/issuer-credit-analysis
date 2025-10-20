"""
Integration tests for burn rate calculations with real REIT financial data

Tests burn rate analysis on:
1. Dream Industrial REIT Q2 2025 (positive AFCF - no burn)
2. Hypothetical high burn rate scenario (negative AFCF)
3. Full pipeline integration with calculate_all_metrics()

Author: AI Assistant (Claude Code)
Date: 2025-10-20
Issue: #7 - Implement Cash Burn Rate and Runway Analysis
"""

import pytest
import json
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from calculate_credit_metrics import (
    calculate_all_metrics,
    calculate_burn_rate,
    calculate_cash_runway,
    assess_liquidity_risk,
    calculate_sustainable_burn_rate,
    calculate_acfo_from_components,
    calculate_afcf
)


@pytest.fixture
def dir_q2_2025_with_liquidity():
    """
    Dream Industrial REIT Q2 2025 data with added AFCF and liquidity data
    Expected: Positive AFCF, no burn rate
    """
    fixture_path = Path(__file__).parent / 'fixtures' / 'dream_industrial_reit_q2_2025_with_acfo.json'
    with open(fixture_path) as f:
        data = json.load(f)

    # Add AFCF data (hypothetical positive AFCF scenario)
    data['cash_flow_investing'] = {
        "development_capex": -11074,  # From acfo_components
        "property_acquisitions": -15000,
        "property_dispositions": 8000,
        "jv_capital_contributions": -2000,
        "jv_return_of_capital": 500,
        "total_cfi": -19574
    }

    data['cash_flow_financing'] = {
        "debt_principal_repayments": -25000,
        "new_debt_issuances": 30000,
        "distributions_common": -102435,  # 292,674 units * $0.35
        "equity_issuances": 5000,
        "total_cff": -92435
    }

    # Add coverage_ratios for burn rate calculation
    data['coverage_ratios'] = {
        "annualized_interest_expense": data['income_statement']['interest_expense'] * 2  # Annualize from Q2
    }

    # Add liquidity data (from balance sheet + estimated facilities)
    data['liquidity'] = {
        "cash_and_equivalents": 42595,
        "marketable_securities": 8000,  # Estimated
        "restricted_cash": 1500,  # Estimated
        "undrawn_credit_facilities": 250000,  # Estimated strong facility
        "credit_facility_limit": 500000,
        "available_cash": 49095,
        "total_available_liquidity": 299095,
        "data_source": "balance sheet + estimated credit facility"
    }

    return data


@pytest.fixture
def high_burn_scenario():
    """Load high burn rate scenario fixture"""
    fixture_path = Path(__file__).parent / 'fixtures' / 'reit_burn_rate_high_risk.json'
    with open(fixture_path) as f:
        return json.load(f)


# ============================================================================
# Dream Industrial REIT Tests (Positive AFCF - No Burn)
# ============================================================================

def test_dir_acfo_calculation(dir_q2_2025_with_liquidity):
    """Test ACFO calculation matches expected value for DIR"""
    result = calculate_acfo_from_components(dir_q2_2025_with_liquidity)

    # ACFO should be calculated successfully
    assert result['acfo_calculated'] is not None
    assert result['data_quality'] in ['strong', 'moderate']

    print(f"\nDIR ACFO: ${result['acfo_calculated']:,.0f}")


def test_dir_afcf_positive(dir_q2_2025_with_liquidity):
    """Test DIR has positive AFCF (operations exceed investments)"""
    # First calculate ACFO
    acfo_result = calculate_acfo_from_components(dir_q2_2025_with_liquidity)
    dir_q2_2025_with_liquidity['acfo_calculated'] = acfo_result['acfo_calculated']

    # Calculate AFCF
    afcf_result = calculate_afcf(dir_q2_2025_with_liquidity)

    assert afcf_result['afcf'] is not None
    # AFCF should be positive (ACFO stronger than net CFI)
    # ACFO ~155K, Net CFI ~-20K, so AFCF ~135K (positive)
    assert afcf_result['afcf'] > 0, "DIR should have positive AFCF (cash-generative)"

    print(f"\nDIR Q2 2025 AFCF Analysis:")
    print(f"  ACFO: ${afcf_result['acfo_starting_point']:,.0f}")
    print(f"  Net CFI: ${afcf_result['net_cfi']:,.0f}")
    print(f"  AFCF: ${afcf_result['afcf']:,.0f}")


def test_dir_has_burn_rate_despite_positive_afcf(dir_q2_2025_with_liquidity):
    """Test DIR has burn rate despite positive AFCF (financing needs exceed AFCF)"""
    # Calculate ACFO and AFCF
    acfo_result = calculate_acfo_from_components(dir_q2_2025_with_liquidity)
    dir_q2_2025_with_liquidity['acfo_calculated'] = acfo_result['acfo_calculated']
    afcf_result = calculate_afcf(dir_q2_2025_with_liquidity)

    # Calculate burn rate
    burn_result = calculate_burn_rate(dir_q2_2025_with_liquidity, afcf_result)

    # KEY INSIGHT: Positive AFCF doesn't mean no burn rate!
    # DIR generates positive free cash flow BUT it's insufficient to cover
    # debt service + distributions, so burn rate IS applicable

    assert afcf_result['afcf'] > 0, "DIR should have positive AFCF"
    assert burn_result['applicable'] is True, "Burn rate should be applicable despite positive AFCF"
    assert burn_result['monthly_burn_rate'] is not None
    assert burn_result['monthly_burn_rate'] > 0
    assert burn_result['self_funding_ratio'] < 1.0, "Self-funding ratio should be < 1.0"
    assert burn_result['net_financing_needs'] > afcf_result['afcf'], "Financing needs exceed AFCF"

    print(f"\nDIR Burn Rate Analysis:")
    print(f"  AFCF: ${afcf_result['afcf']:,.0f} (POSITIVE but insufficient)")
    print(f"  Net Financing Needs: ${burn_result['net_financing_needs']:,.0f}")
    print(f"  Self-Funding Ratio: {burn_result['self_funding_ratio']:.0%}")
    print(f"  Monthly Burn Rate: ${burn_result['monthly_burn_rate']:,.0f}")


def test_dir_full_pipeline(dir_q2_2025_with_liquidity):
    """Test complete burn rate pipeline with DIR data"""
    result = calculate_all_metrics(dir_q2_2025_with_liquidity)

    # Should have AFCF metrics
    assert 'afcf_metrics' in result
    assert result['afcf_metrics']['afcf'] > 0

    # Should have burn rate analysis (applicable despite positive AFCF)
    assert 'burn_rate_analysis' in result
    assert result['burn_rate_analysis']['applicable'] is True
    assert result['burn_rate_analysis']['self_funding_ratio'] < 1.0

    # Should have runway and risk metrics (calculated when burn rate applicable)
    assert 'cash_runway' in result
    assert result['cash_runway']['runway_months'] is not None
    assert 'liquidity_risk' in result

    print(f"\nDIR Full Pipeline Results:")
    print(f"  AFCF: ${result['afcf_metrics']['afcf']:,.0f}")
    print(f"  Burn Rate Applicable: {result['burn_rate_analysis']['applicable']}")
    print(f"  Self-Funding Ratio: {result['burn_rate_analysis']['self_funding_ratio']:.0%}")
    print(f"  Cash Runway: {result['cash_runway']['runway_months']:.1f} months")


# ============================================================================
# High Burn Rate Scenario Tests (Negative AFCF)
# ============================================================================

def test_high_burn_acfo_calculation(high_burn_scenario):
    """Test ACFO calculation for high burn scenario"""
    result = calculate_acfo_from_components(high_burn_scenario)

    expected = high_burn_scenario['expected_results']['acfo_calculated']

    assert result['acfo_calculated'] is not None
    # Should be close to expected value (within 5%)
    assert abs(result['acfo_calculated'] - expected) / expected < 0.05

    print(f"\nHigh Burn Scenario ACFO:")
    print(f"  Expected: ${expected:,.0f}")
    print(f"  Calculated: ${result['acfo_calculated']:,.0f}")
    print(f"  Variance: {((result['acfo_calculated'] - expected) / expected * 100):.1f}%")


def test_high_burn_afcf_negative(high_burn_scenario):
    """Test AFCF is negative due to heavy investment program"""
    # Calculate ACFO first
    acfo_result = calculate_acfo_from_components(high_burn_scenario)
    high_burn_scenario['acfo_calculated'] = acfo_result['acfo_calculated']

    # Calculate AFCF
    afcf_result = calculate_afcf(high_burn_scenario)

    expected_afcf = high_burn_scenario['expected_results']['afcf_calculated']

    assert afcf_result['afcf'] is not None
    assert afcf_result['afcf'] < 0, "AFCF should be negative (heavy investment program)"

    # Check within 10% of expected (some variance acceptable)
    assert abs(afcf_result['afcf'] - expected_afcf) / abs(expected_afcf) < 0.10

    print(f"\nHigh Burn Scenario AFCF:")
    print(f"  ACFO: ${afcf_result['acfo_starting_point']:,.0f}")
    print(f"  Net CFI: ${afcf_result['net_cfi']:,.0f}")
    print(f"  AFCF: ${afcf_result['afcf']:,.0f}")
    print(f"  Expected AFCF: ${expected_afcf:,.0f}")


def test_high_burn_burn_rate_calculation(high_burn_scenario):
    """Test burn rate calculation for high burn scenario"""
    # Calculate ACFO and AFCF
    acfo_result = calculate_acfo_from_components(high_burn_scenario)
    high_burn_scenario['acfo_calculated'] = acfo_result['acfo_calculated']
    afcf_result = calculate_afcf(high_burn_scenario)

    # Calculate burn rate
    burn_result = calculate_burn_rate(high_burn_scenario, afcf_result)

    expected_monthly = high_burn_scenario['expected_results']['monthly_burn_rate']
    expected_annual = high_burn_scenario['expected_results']['annualized_burn_rate']

    assert burn_result['applicable'] is True
    assert burn_result['monthly_burn_rate'] is not None
    assert abs(burn_result['monthly_burn_rate'] - expected_monthly) / expected_monthly < 0.10
    assert abs(burn_result['annualized_burn_rate'] - expected_annual) / expected_annual < 0.10

    print(f"\nHigh Burn Scenario Burn Rate:")
    print(f"  Monthly Burn: ${burn_result['monthly_burn_rate']:,.0f} (expected: ${expected_monthly:,.0f})")
    print(f"  Annual Burn: ${burn_result['annualized_burn_rate']:,.0f} (expected: ${expected_annual:,.0f})")


def test_high_burn_cash_runway(high_burn_scenario):
    """Test cash runway calculation for high burn scenario"""
    # Calculate full chain
    acfo_result = calculate_acfo_from_components(high_burn_scenario)
    high_burn_scenario['acfo_calculated'] = acfo_result['acfo_calculated']
    afcf_result = calculate_afcf(high_burn_scenario)
    burn_result = calculate_burn_rate(high_burn_scenario, afcf_result)

    # Calculate cash runway
    runway_result = calculate_cash_runway(high_burn_scenario, burn_result)

    expected_runway = high_burn_scenario['expected_results']['runway_months']

    assert runway_result['error'] is None
    assert runway_result['runway_months'] is not None
    # Should be within 2 months of expected
    assert abs(runway_result['runway_months'] - expected_runway) < 2.0

    print(f"\nHigh Burn Scenario Cash Runway:")
    print(f"  Available Cash: ${runway_result['available_cash']:,.0f}")
    print(f"  Runway: {runway_result['runway_months']:.1f} months ({runway_result['runway_years']:.1f} years)")
    print(f"  Expected: {expected_runway:.1f} months")
    print(f"  Extended Runway (w/ facilities): {runway_result['extended_runway_months']:.1f} months")


def test_high_burn_liquidity_risk(high_burn_scenario):
    """Test liquidity risk assessment for high burn scenario"""
    # Calculate full chain
    acfo_result = calculate_acfo_from_components(high_burn_scenario)
    high_burn_scenario['acfo_calculated'] = acfo_result['acfo_calculated']
    afcf_result = calculate_afcf(high_burn_scenario)
    burn_result = calculate_burn_rate(high_burn_scenario, afcf_result)
    runway_result = calculate_cash_runway(high_burn_scenario, burn_result)

    # Assess liquidity risk
    risk_result = assess_liquidity_risk(runway_result)

    expected_risk = high_burn_scenario['expected_results']['risk_level']

    assert risk_result['risk_level'] is not None
    assert risk_result['risk_level'] == expected_risk
    assert risk_result['risk_score'] > 0
    assert len(risk_result['recommendations']) > 0

    print(f"\nHigh Burn Scenario Liquidity Risk:")
    print(f"  Risk Level: {risk_result['risk_level']} (expected: {expected_risk})")
    print(f"  Risk Score: {risk_result['risk_score']}/4")
    print(f"  Assessment: {risk_result['assessment']}")
    print(f"  Warning Flags: {len(risk_result['warning_flags'])}")
    print(f"  Recommendations: {len(risk_result['recommendations'])}")


def test_high_burn_sustainable_burn(high_burn_scenario):
    """Test sustainable burn rate calculation"""
    # Calculate full chain
    acfo_result = calculate_acfo_from_components(high_burn_scenario)
    high_burn_scenario['acfo_calculated'] = acfo_result['acfo_calculated']
    afcf_result = calculate_afcf(high_burn_scenario)
    burn_result = calculate_burn_rate(high_burn_scenario, afcf_result)

    # Calculate sustainable burn
    sustainable_result = calculate_sustainable_burn_rate(
        high_burn_scenario,
        burn_result,
        target_runway_months=24
    )

    assert sustainable_result['sustainable_monthly_burn'] is not None
    assert sustainable_result['excess_burn_per_month'] is not None
    # Should be overspending (actual > sustainable)
    assert sustainable_result['excess_burn_per_month'] > 0
    assert 'Above sustainable' in sustainable_result['status']

    print(f"\nHigh Burn Scenario Sustainable Burn:")
    print(f"  Actual Monthly Burn: ${sustainable_result['actual_monthly_burn']:,.0f}")
    print(f"  Sustainable Monthly Burn: ${sustainable_result['sustainable_monthly_burn']:,.0f}")
    print(f"  Excess Burn: ${sustainable_result['excess_burn_per_month']:,.0f}/month")
    print(f"  Status: {sustainable_result['status']}")


def test_high_burn_full_pipeline(high_burn_scenario):
    """Test complete burn rate pipeline with high burn scenario"""
    result = calculate_all_metrics(high_burn_scenario)

    # Should have complete burn rate analysis
    assert 'afcf_metrics' in result
    assert result['afcf_metrics']['afcf'] < 0

    assert 'burn_rate_analysis' in result
    assert result['burn_rate_analysis']['applicable'] is True

    assert 'liquidity_position' in result
    assert result['liquidity_position']['available_cash'] > 0

    assert 'cash_runway' in result
    assert result['cash_runway']['runway_months'] is not None

    assert 'liquidity_risk' in result
    assert result['liquidity_risk']['risk_level'] == 'HIGH'

    assert 'sustainable_burn' in result
    assert result['sustainable_burn']['excess_burn_per_month'] > 0

    print(f"\n=== High Burn Scenario Full Pipeline Results ===")
    print(f"Issuer: {result['issuer_name']}")
    print(f"Reporting Date: {result['reporting_date']}")
    print(f"\nAFCF Analysis:")
    print(f"  AFCF: ${result['afcf_metrics']['afcf']:,.0f}")
    print(f"  Data Quality: {result['afcf_metrics']['data_quality']}")
    print(f"\nBurn Rate:")
    print(f"  Monthly: ${result['burn_rate_analysis']['monthly_burn_rate']:,.0f}")
    print(f"  Annual: ${result['burn_rate_analysis']['annualized_burn_rate']:,.0f}")
    print(f"\nLiquidity:")
    print(f"  Available Cash: ${result['liquidity_position']['available_cash']:,.0f}")
    print(f"  Total Liquidity: ${result['liquidity_position']['total_available_liquidity']:,.0f}")
    print(f"\nCash Runway:")
    print(f"  Runway: {result['cash_runway']['runway_months']:.1f} months")
    print(f"  Extended: {result['cash_runway']['extended_runway_months']:.1f} months")
    print(f"\nLiquidity Risk:")
    print(f"  Level: {result['liquidity_risk']['risk_level']}")
    print(f"  Score: {result['liquidity_risk']['risk_score']}/4")
    print(f"\nSustainable Burn:")
    print(f"  Target: ${result['sustainable_burn']['sustainable_monthly_burn']:,.0f}/month")
    print(f"  Overspend: ${result['sustainable_burn']['excess_burn_per_month']:,.0f}/month")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
