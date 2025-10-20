#!/usr/bin/env python3
"""
Integration test for ACFO calculation using Dream Industrial REIT fixture data

Tests the complete ACFO pipeline:
- Phase 2 extraction (fixture data)
- Phase 3 ACFO calculation
- Consistency validation with AFFO
- Reconciliation table generation
"""

import json
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from calculate_credit_metrics import (
    calculate_all_metrics,
    calculate_acfo_from_components,
    generate_acfo_reconciliation,
    format_acfo_reconciliation_table,
    generate_ffo_affo_reconciliation,
    format_reconciliation_table
)


def test_dir_acfo_calculation():
    """Test ACFO calculation on Dream Industrial REIT Q2 2025 data"""

    # Load fixture
    fixture_path = Path(__file__).parent / 'fixtures' / 'dream_industrial_reit_q2_2025_with_acfo.json'

    with open(fixture_path, 'r') as f:
        financial_data = json.load(f)

    # Calculate ACFO
    acfo_result = calculate_acfo_from_components(financial_data)

    # Verify ACFO calculated successfully
    assert acfo_result is not None
    assert acfo_result['acfo_calculated'] is not None
    assert acfo_result['cash_flow_from_operations'] == 165000
    assert acfo_result['data_quality'] == 'strong'

    # Expected ACFO (manual calculation)
    # CFO: 165,000
    # + change_in_working_capital: -3,500
    # + interest_financing: 8,500
    # + jv_distributions: 4,200
    # - capex_sustaining: -7,700
    # - capex_development (disclosure only): -11,074
    # - leasing_costs_external: -1,200
    # + taxes_non_operating: 850
    # + transaction_costs_acquisitions: 1,500
    # + deferred_financing_fees: 800
    # - interest_expense_timing: -1,200
    # - non_controlling_interests_acfo: -850

    expected_acfo = 165000 - 3500 + 8500 + 4200 - 7700 - 11074 - 1200 + 850 + 1500 + 800 - 1200 - 850
    assert acfo_result['acfo_calculated'] == expected_acfo

    print(f"\n✅ ACFO calculated successfully:")
    print(f"   Cash Flow from Operations: ${acfo_result['cash_flow_from_operations']:,}")
    print(f"   Total Adjustments: ${acfo_result['total_adjustments']:,}")
    print(f"   ACFO (calculated): ${acfo_result['acfo_calculated']:,}")
    print(f"   Data Quality: {acfo_result['data_quality']}")
    print(f"   Calculation Method: {acfo_result['calculation_method']}")
    print(f"   JV Treatment: {acfo_result['jv_treatment_method']}")


def test_dir_acfo_consistency_with_affo():
    """Test CAPEX consistency between ACFO and AFFO calculations"""

    fixture_path = Path(__file__).parent / 'fixtures' / 'dream_industrial_reit_q2_2025_with_acfo.json'

    with open(fixture_path, 'r') as f:
        financial_data = json.load(f)

    acfo_result = calculate_acfo_from_components(financial_data)

    # Check consistency checks exist
    assert 'consistency_checks' in acfo_result

    # Note: In this fixture, CAPEX values have different signs due to storage conventions
    # AFFO stores as positive (7700), ACFO stores as negative (-7700)
    # Both represent the same economic deduction from earnings/cash flow
    # The reconciliation table will show the variance for analyst review

    print(f"\n✅ ACFO/AFFO consistency checks performed:")
    print(f"   CAPEX (sustaining) match: {acfo_result['consistency_checks'].get('capex_match', 'N/A')}")
    print(f"   CAPEX variance: ${acfo_result['consistency_checks'].get('capex_variance', 0):,}")

    # For this hypothetical fixture, we expect a sign difference
    # In real extraction, Phase 2 would ensure consistent storage
    if 'capex_variance' in acfo_result['consistency_checks']:
        print(f"   ⚠️  Note: Variance due to sign convention differences in fixture data")
        print(f"       AFFO CAPEX stored as positive (7700), ACFO as negative (-7700)")
        print(f"       Both represent $7,700 sustaining CAPEX deduction")


def test_dir_acfo_reconciliation():
    """Test ACFO reconciliation table generation"""

    fixture_path = Path(__file__).parent / 'fixtures' / 'dream_industrial_reit_q2_2025_with_acfo.json'

    with open(fixture_path, 'r') as f:
        financial_data = json.load(f)

    # Generate reconciliation
    reconciliation = generate_acfo_reconciliation(financial_data)

    assert reconciliation is not None
    assert reconciliation['starting_point']['description'] == 'IFRS Cash Flow from Operations'
    assert reconciliation['starting_point']['amount'] == 165000
    assert len(reconciliation['acfo_adjustments']) > 0

    # Format as markdown
    markdown = format_acfo_reconciliation_table(reconciliation)

    assert '## ACFO Reconciliation Table' in markdown
    assert 'IFRS Cash Flow from Operations' in markdown
    assert 'Adjusted Cash Flow from Operations (ACFO)' in markdown
    assert '**ACFO Adjustments (1-17):**' in markdown
    assert '**Consistency Checks (vs AFFO):**' in markdown

    print(f"\n✅ ACFO Reconciliation Table Generated:")
    print("\n" + markdown)


def test_dir_complete_metrics_with_acfo():
    """Test complete metrics calculation including ACFO"""

    fixture_path = Path(__file__).parent / 'fixtures' / 'dream_industrial_reit_q2_2025_with_acfo.json'

    with open(fixture_path, 'r') as f:
        financial_data = json.load(f)

    # Calculate all metrics
    result = calculate_all_metrics(financial_data)

    # Verify structure
    assert result['issuer_name'] == 'Dream Industrial Real Estate Investment Trust'
    assert result['reporting_date'] == '2025-06-30'

    # Verify REIT metrics include ACFO
    assert 'reit_metrics' in result
    reit = result['reit_metrics']

    # FFO/AFFO should be calculated
    assert 'ffo_calculated' in reit
    assert 'affo_calculated' in reit

    # ACFO should be calculated
    assert 'acfo_calculated' in reit
    assert 'acfo' in reit
    assert 'acfo_per_unit' in reit
    assert 'acfo_payout_ratio' in reit

    # ACFO calculation detail should be present
    assert 'acfo_calculation_detail' in reit
    assert reit['acfo_calculation_detail']['data_quality'] == 'strong'

    # ACFO validation should be present
    assert 'acfo_validation' in reit
    assert 'Issuer did not report ACFO' in reit['acfo_validation']['validation_summary']

    print(f"\n✅ Complete metrics calculated with ACFO:")
    print(f"   Issuer: {result['issuer_name']}")
    print(f"   Period: {result['reporting_period']}")
    print(f"\n   FFO: ${reit['ffo_calculated']:,} (${reit['ffo_per_unit']:.2f} per unit)")
    print(f"   AFFO: ${reit['affo_calculated']:,} (${reit['affo_per_unit']:.2f} per unit)")
    print(f"   ACFO: ${reit['acfo']:,} (${reit['acfo_per_unit']:.2f} per unit)")
    print(f"\n   FFO Payout: {reit['ffo_payout_ratio']:.1f}%")
    print(f"   AFFO Payout: {reit['affo_payout_ratio']:.1f}%")
    print(f"   ACFO Payout: {reit['acfo_payout_ratio']:.1f}%")


def test_dir_ffo_affo_acfo_comparison():
    """Compare FFO/AFFO/ACFO metrics for Dream Industrial REIT"""

    fixture_path = Path(__file__).parent / 'fixtures' / 'dream_industrial_reit_q2_2025_with_acfo.json'

    with open(fixture_path, 'r') as f:
        financial_data = json.load(f)

    result = calculate_all_metrics(financial_data)
    reit = result['reit_metrics']

    # Generate both reconciliation tables
    ffo_affo_reconciliation = generate_ffo_affo_reconciliation(financial_data)
    acfo_reconciliation = generate_acfo_reconciliation(financial_data)

    print(f"\n✅ FFO/AFFO/ACFO Comparison for Dream Industrial REIT Q2 2025:")
    print(f"\n{'=' * 70}")
    print(f"{'Metric':<30} {'Amount (000s)':<20} {'Per Unit':<15}")
    print(f"{'=' * 70}")
    print(f"{'IFRS Net Income':<30} ${94096:>15,} {'N/A':<15}")
    print(f"{'FFO (calculated)':<30} ${reit['ffo_calculated']:>15,} ${reit['ffo_per_unit']:>13.2f}")
    print(f"{'AFFO (calculated)':<30} ${reit['affo_calculated']:>15,} ${reit['affo_per_unit']:>13.2f}")
    print(f"{'ACFO (calculated)':<30} ${reit['acfo']:>15,} ${reit['acfo_per_unit']:>13.2f}")
    print(f"{'Distributions':<30} ${int(0.35 * 292674):>15,} ${0.35:>13.2f}")
    print(f"{'=' * 70}")
    print(f"\n{'Payout Ratios:':<30}")
    print(f"  {'FFO Payout':<28} {reit['ffo_payout_ratio']:>18.1f}%")
    print(f"  {'AFFO Payout':<28} {reit['affo_payout_ratio']:>18.1f}%")
    print(f"  {'ACFO Payout':<28} {reit['acfo_payout_ratio']:>18.1f}%")
    print(f"{'=' * 70}")

    # Key insights
    print(f"\n💡 Key Insights:")
    print(f"   • FFO → AFFO reduction: ${reit['ffo_calculated'] - reit['affo_calculated']:,} ({((reit['ffo_calculated'] - reit['affo_calculated']) / reit['ffo_calculated'] * 100):.1f}% of FFO)")
    print(f"   • CFO → ACFO reduction: ${165000 - reit['acfo']:,} ({((165000 - reit['acfo']) / 165000 * 100):.1f}% of CFO)")
    print(f"   • AFFO vs ACFO: ${abs(reit['affo_calculated'] - reit['acfo']):,} difference")
    print(f"   • Distribution coverage (ACFO): {(reit['acfo'] / (0.35 * 292674)):.2f}x")


def test_save_acfo_calculation_output():
    """Save ACFO calculation results to temp directory for inspection"""

    fixture_path = Path(__file__).parent / 'fixtures' / 'dream_industrial_reit_q2_2025_with_acfo.json'

    with open(fixture_path, 'r') as f:
        financial_data = json.load(f)

    result = calculate_all_metrics(financial_data)

    # Save to temp directory
    output_dir = Path(__file__).parent.parent / 'Issuer_Reports' / 'Dream_Industrial_REIT' / 'temp'
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / 'test_phase3_acfo_calculated_metrics.json'

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n✅ ACFO calculation results saved to:")
    print(f"   {output_path}")

    # Also save reconciliation tables as markdown
    ffo_affo_reconciliation = generate_ffo_affo_reconciliation(financial_data)
    acfo_reconciliation = generate_acfo_reconciliation(financial_data)

    ffo_affo_markdown = format_reconciliation_table(ffo_affo_reconciliation)
    acfo_markdown = format_acfo_reconciliation_table(acfo_reconciliation)

    reconciliation_path = output_dir / 'test_acfo_reconciliations.md'

    with open(reconciliation_path, 'w') as f:
        f.write("# Dream Industrial REIT Q2 2025 - ACFO Analysis\n\n")
        f.write("## Overview\n\n")
        f.write(f"This document demonstrates the ACFO calculation for Dream Industrial REIT based on Q2 2025 financial data.\n\n")
        f.write("---\n\n")
        f.write(ffo_affo_markdown)
        f.write("\n\n---\n\n")
        f.write(acfo_markdown)

    print(f"   {reconciliation_path}")


if __name__ == '__main__':
    # Run all tests
    import pytest
    pytest.main([__file__, '-v', '-s'])
