#!/usr/bin/env python3
"""
Credit Metrics Calculation Library for Real Estate Issuers

ORCHESTRATION MODULE:
- This module ONLY contains orchestration logic (calculate_all_metrics, main)
- All calculation logic lives in specialized modules
- NO duplicate function implementations

EXAMPLE USAGE (documentation only - not executable):

    # After Phase 2 extraction produces: sample_extracted_data.json
    $ python scripts/calculate_credit_metrics.py sample_extracted_data.json

    Calculating metrics for: Sample Real Estate Investment Trust
    Reporting date: 2025-06-30
    ✓ Metrics calculated and saved to calculated_metrics.json
"""

import json
import sys
from pathlib import Path

# Import all calculation functions from specialized modules
from .validation import validate_required_fields
from .leverage import calculate_leverage_metrics
from .ffo_affo import (
    calculate_ffo_from_components,
    calculate_affo_from_ffo,
    validate_ffo_affo
)
from .acfo import calculate_acfo_from_components
from .afcf import (
    calculate_afcf,
    calculate_afcf_coverage_ratios,
    validate_afcf_reconciliation
)
from .reit_metrics import calculate_reit_metrics
from .burn_rate import (
    calculate_burn_rate,
    calculate_cash_runway,
    assess_liquidity_risk,
    calculate_sustainable_burn_rate
)
from .coverage import calculate_coverage_ratios
from .dilution import analyze_dilution
from .reconciliation import (
    generate_ffo_affo_reconciliation,
    format_reconciliation_table,
    format_acfo_reconciliation_table
)


def calculate_all_metrics(financial_data):
    """
    Calculate all metrics and return comprehensive results

    Args:
        financial_data (dict): Validated JSON from Phase 2

    Returns:
        dict: Complete metrics with issuer identification
    """

    # Validate issuer identification exists
    if 'issuer_name' not in financial_data:
        raise KeyError("Missing issuer_name in financial_data")
    if 'reporting_date' not in financial_data:
        raise KeyError("Missing reporting_date in financial_data")

    # Calculate all metric categories
    leverage_metrics = calculate_leverage_metrics(financial_data)
    reit_metrics = calculate_reit_metrics(financial_data)
    coverage_ratios = calculate_coverage_ratios(financial_data)

    # Calculate ACFO if cash flow statement data available
    acfo_metrics = None
    if 'cash_flow_operating' in financial_data or ('ffo_affo_components' in financial_data and 'acfo_components' in financial_data):
        try:
            acfo_result = calculate_acfo_from_components(financial_data)
            if acfo_result and acfo_result.get('acfo') is not None:
                acfo_metrics = acfo_result
                # Add to financial_data for AFCF calculation
                financial_data['acfo_calculated'] = acfo_result['acfo']
        except (KeyError, ValueError) as e:
            # ACFO calculation failed - continue without it
            pass

    # Calculate AFCF metrics if cash flow data available
    afcf_metrics = None
    afcf_coverage = None
    afcf_reconciliation = None

    if 'cash_flow_investing' in financial_data:
        # First, ensure financial_data has access to ACFO
        # ACFO may be in reit_metrics or acfo_calculated at top level
        if 'acfo' in reit_metrics:
            financial_data['acfo_calculated'] = reit_metrics['acfo']
        elif acfo_metrics and 'acfo' in acfo_metrics:
            financial_data['acfo_calculated'] = acfo_metrics['acfo']

        # Calculate AFCF
        afcf_result = calculate_afcf(financial_data)

        if afcf_result and afcf_result.get('afcf') is not None:
            afcf_metrics = afcf_result

            # Calculate AFCF coverage ratios if financing data available
            if 'cash_flow_financing' in financial_data:
                # Add coverage_ratios to financial_data for AFCF coverage calculation
                financial_data['coverage_ratios'] = coverage_ratios
                afcf_coverage = calculate_afcf_coverage_ratios(financial_data, afcf_result['afcf'])

            # Validate AFCF reconciliation
            acfo_for_validation = afcf_result.get('acfo_starting_point')
            if acfo_for_validation is not None:
                afcf_reconciliation = validate_afcf_reconciliation(
                    financial_data,
                    acfo_for_validation,
                    afcf_result['afcf']
                )

    # Extract portfolio metrics if available
    portfolio_metrics = {}
    if 'portfolio' in financial_data:
        portfolio = financial_data['portfolio']

        # Handle null values by converting to 0
        gla = portfolio.get('total_gla_sf')
        if gla is None:
            gla = 0

        # Support both naming conventions for occupancy_with_commitments
        occ_with_commitments = (
            portfolio.get('occupancy_with_commitments') or
            portfolio.get('occupancy_including_commitments', 0)
        )

        # Support both naming conventions for same property NOI growth
        noi_growth = (
            portfolio.get('same_property_noi_growth_6m') or
            portfolio.get('same_property_noi_growth', 0)
        )

        portfolio_metrics = {
            'total_properties': portfolio.get('property_count', portfolio.get('total_properties', 0)),
            'gla_sf': gla,
            'occupancy_rate': portfolio.get('occupancy_rate', 0),
            'occupancy_including_commitments': occ_with_commitments,
            'same_property_noi_growth': noi_growth
        }

    # Assemble complete output with issuer identification
    result = {
        'issuer_name': financial_data['issuer_name'],
        'reporting_date': financial_data['reporting_date'],
        'reporting_period': financial_data.get('reporting_period', 'Unknown'),
        'currency': financial_data.get('currency', 'Unknown'),
        'leverage_metrics': leverage_metrics,
        'reit_metrics': reit_metrics,
        'coverage_ratios': coverage_ratios,
        'portfolio_metrics': portfolio_metrics
    }

    # Add ACFO metrics if calculated
    if acfo_metrics is not None:
        result['acfo_metrics'] = acfo_metrics

    # Add AFCF metrics if calculated
    if afcf_metrics is not None:
        result['afcf_metrics'] = afcf_metrics
    if afcf_coverage is not None:
        result['afcf_coverage'] = afcf_coverage
    if afcf_reconciliation is not None:
        result['afcf_reconciliation'] = afcf_reconciliation

    # Calculate burn rate and cash runway if AFCF available
    burn_rate_analysis = None
    liquidity_position = None
    cash_runway = None
    liquidity_risk = None
    sustainable_burn = None

    if afcf_metrics is not None:
        # Calculate burn rate (only applicable if AFCF < Net Financing Needs)
        burn_rate_analysis = calculate_burn_rate(financial_data, afcf_metrics, afcf_coverage)

        # If burn rate is applicable and liquidity data exists, calculate runway and risk
        if burn_rate_analysis.get('applicable', False) and 'liquidity' in financial_data:
            # Extract liquidity position for output
            liquidity_data = financial_data['liquidity']
            liquidity_position = {
                'cash_and_equivalents': liquidity_data.get('cash_and_equivalents', 0),
                'marketable_securities': liquidity_data.get('marketable_securities', 0),
                'restricted_cash': liquidity_data.get('restricted_cash', 0),
                'undrawn_credit_facilities': liquidity_data.get('undrawn_credit_facilities', 0),
                'credit_facility_limit': liquidity_data.get('credit_facility_limit', 0),
                'available_cash': liquidity_data.get('available_cash'),
                'total_available_liquidity': liquidity_data.get('total_available_liquidity'),
                'data_source': liquidity_data.get('data_source', 'Not specified')
            }

            # Calculate cash runway
            cash_runway = calculate_cash_runway(financial_data, burn_rate_analysis)

            # Assess liquidity risk
            if cash_runway and not cash_runway.get('error'):
                liquidity_risk = assess_liquidity_risk(cash_runway)

                # Calculate sustainable burn rate
                sustainable_burn = calculate_sustainable_burn_rate(
                    financial_data,
                    burn_rate_analysis,
                    target_runway_months=24
                )

    # Add burn rate metrics if calculated
    if burn_rate_analysis is not None:
        result['burn_rate_analysis'] = burn_rate_analysis
    if liquidity_position is not None:
        result['liquidity_position'] = liquidity_position
    if cash_runway is not None:
        result['cash_runway'] = cash_runway
    if liquidity_risk is not None:
        result['liquidity_risk'] = liquidity_risk
    if sustainable_burn is not None:
        result['sustainable_burn'] = sustainable_burn

    # Analyze dilution if detail available
    dilution_analysis = analyze_dilution(financial_data)
    if dilution_analysis['has_dilution_detail']:
        result['dilution_analysis'] = dilution_analysis

    return result


def main():
    """Main execution - command-line interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Calculate credit metrics from extracted financial data',
        epilog='Example: python calculate_credit_metrics.py --issuer-name "Artis REIT" phase2_extracted_data.json'
    )
    parser.add_argument(
        'input_json',
        help='Path to Phase 2 extracted data JSON (REQUIRED)'
    )
    parser.add_argument(
        '--issuer-name',
        default=None,
        help='Issuer name (for folder organization, optional - can infer from input path)'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output path for calculated metrics (default: auto-generated from input path)'
    )

    args = parser.parse_args()

    # MUST provide input file - no defaults
    input_path = Path(args.input_json)

    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        sys.exit(1)

    # Auto-generate output path if not specified (same folder as input)
    if args.output is None:
        args.output = str(input_path.parent / 'phase3_calculated_metrics.json')

    print(f"📊 Loading financial data from: {input_path}")

    try:
        with open(input_path, 'r') as f:
            financial_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in input file: {e}")
        sys.exit(1)

    # Validate issuer identification
    if 'issuer_name' not in financial_data:
        print("❌ Error: Missing issuer_name in input data")
        print("   Phase 2 extraction must include issuer_name field")
        sys.exit(1)

    print(f"\n🏢 Calculating metrics for: {financial_data['issuer_name']}")
    print(f"📅 Reporting date: {financial_data['reporting_date']}")

    try:
        # Calculate all metrics
        print("\n⚙️  Calculating leverage metrics...")
        print("⚙️  Calculating REIT metrics...")
        print("⚙️  Calculating coverage ratios...")

        result = calculate_all_metrics(financial_data)

        # Save results
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"\n✅ Success! Metrics calculated and saved to: {output_path}")

        # Print summary
        print("\n📊 SUMMARY")
        print("=" * 60)
        print(f"Issuer: {result['issuer_name']}")
        print(f"Period: {result['reporting_period']}")
        print(f"\nLeverage:")
        print(f"  • Total Debt: {result['leverage_metrics']['total_debt']:,.0f}")
        print(f"  • Debt/Assets: {result['leverage_metrics']['debt_to_assets_percent']:.1f}%")
        print(f"\nREIT Metrics:")
        print(f"  • FFO per Unit: {result['reit_metrics']['ffo_per_unit']:.2f}")
        print(f"  • AFFO Payout: {result['reit_metrics']['affo_payout_ratio']:.1f}%")
        print(f"\nCoverage:")
        print(f"  • NOI/Interest: {result['coverage_ratios']['noi_interest_coverage']:.2f}x")
        print("=" * 60)

        sys.exit(0)

    except KeyError as e:
        print(f"\n❌ Error: Missing required field: {e}")
        print("   Check that Phase 2 extraction completed successfully")
        sys.exit(1)

    except ValueError as e:
        print(f"\n❌ Error: Invalid data: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
