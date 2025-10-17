#!/usr/bin/env python3
"""
Credit Metrics Calculation Library for Real Estate Issuers

SAFETY DESIGN:
- NO hardcoded financial data anywhere in this module
- All functions require explicit input (no defaults)
- Fail loudly with KeyError/ValueError if data missing or invalid
- Include issuer identification in all outputs

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


def validate_required_fields(data, required_fields):
    """
    Ensure all required fields exist - fail loudly if missing

    Args:
        data: Dictionary to validate
        required_fields: List of dot-notation field paths (e.g., 'balance_sheet.total_assets')

    Raises:
        KeyError: If any required field is missing
    """
    for field in required_fields:
        keys = field.split('.')
        current = data
        for key in keys:
            if key not in current:
                raise KeyError(
                    f"Missing required field: {field}. "
                    f"Ensure Phase 2 extraction included this field."
                )
            current = current[key]


def calculate_leverage_metrics(financial_data):
    """
    Calculate leverage metrics from standardized financial data.

    SAFETY: This function has NO defaults and NO hardcoded data.
    It will fail loudly if required data is missing.

    Args:
        financial_data (dict): Validated JSON from Phase 2 extraction
                               REQUIRED - no defaults

    Returns:
        dict: Calculated leverage metrics

    Raises:
        KeyError: If required fields are missing
        ValueError: If data validation fails
    """

    # Validate all required fields exist (fail loudly)
    required_fields = [
        'balance_sheet.total_assets',
        'balance_sheet.mortgages_noncurrent',
        'balance_sheet.mortgages_current',
        'balance_sheet.credit_facilities',
        'balance_sheet.cash'
    ]
    validate_required_fields(financial_data, required_fields)

    # Extract from provided data only
    bs = financial_data['balance_sheet']

    # Validate individual debt components (must be non-negative)
    debt_components = {
        'mortgages_noncurrent': bs['mortgages_noncurrent'],
        'mortgages_current': bs['mortgages_current'],
        'credit_facilities': bs['credit_facilities']
    }

    for component_name, value in debt_components.items():
        if value < 0:
            raise ValueError(
                f"Invalid {component_name}: {value}. "
                f"Debt components cannot be negative. Check Phase 2 extraction."
            )

    total_debt = (
        bs['mortgages_noncurrent'] +
        bs['mortgages_current'] +
        bs['credit_facilities']
    )

    # Add senior unsecured debentures if present
    if 'senior_unsecured_debentures' in bs:
        if bs['senior_unsecured_debentures'] < 0:
            raise ValueError(
                f"Invalid senior_unsecured_debentures: {bs['senior_unsecured_debentures']}. "
                f"Debt cannot be negative."
            )
        total_debt += bs['senior_unsecured_debentures']

    net_debt = total_debt - bs['cash']

    # Get total assets
    total_assets = bs['total_assets']

    # Safety checks: reasonable values
    if total_assets <= 0:
        raise ValueError(
            f"Invalid total_assets: {total_assets}. "
            f"Assets must be positive. Check Phase 2 extraction."
        )

    # Calculate metrics
    debt_to_assets_percent = (total_debt / total_assets) * 100
    net_debt_ratio = (net_debt / total_assets) * 100

    return {
        'total_debt': total_debt,
        'net_debt': net_debt,
        'gross_assets': total_assets,
        'debt_to_assets_percent': round(debt_to_assets_percent, 2),
        'net_debt_ratio': round(net_debt_ratio, 2)
    }


def calculate_reit_metrics(financial_data):
    """
    Calculate REIT-specific metrics (FFO, AFFO, payout ratios)

    Args:
        financial_data (dict): Validated JSON from Phase 2 extraction

    Returns:
        dict: REIT metrics

    Raises:
        KeyError: If required fields are missing
    """

    required_fields = [
        'ffo_affo.ffo',
        'ffo_affo.affo',
        'ffo_affo.ffo_per_unit',
        'ffo_affo.affo_per_unit',
        'ffo_affo.distributions_per_unit'
    ]
    validate_required_fields(financial_data, required_fields)

    ffo_data = financial_data['ffo_affo']

    # Calculate payout ratios
    ffo_payout = (ffo_data['distributions_per_unit'] / ffo_data['ffo_per_unit']) * 100
    affo_payout = (ffo_data['distributions_per_unit'] / ffo_data['affo_per_unit']) * 100

    return {
        'ffo': ffo_data['ffo'],
        'affo': ffo_data['affo'],
        'ffo_per_unit': ffo_data['ffo_per_unit'],
        'affo_per_unit': ffo_data['affo_per_unit'],
        'distributions_per_unit': ffo_data['distributions_per_unit'],
        'ffo_payout_ratio': round(ffo_payout, 1),
        'affo_payout_ratio': round(affo_payout, 1)
    }


def calculate_coverage_ratios(financial_data):
    """
    Calculate interest coverage and EBITDA-based ratios

    Args:
        financial_data (dict): Validated JSON from Phase 2 extraction

    Returns:
        dict: Coverage ratios

    Raises:
        KeyError: If required fields are missing
        ValueError: If calculations produce invalid results
    """

    required_fields = [
        'income_statement.noi',
        'income_statement.interest_expense'
    ]
    validate_required_fields(financial_data, required_fields)

    income = financial_data['income_statement']

    noi = income['noi']
    interest_expense = income['interest_expense']

    if interest_expense <= 0:
        raise ValueError(
            f"Invalid interest_expense: {interest_expense}. "
            f"Interest expense must be positive."
        )

    # NOI / Interest Coverage
    noi_interest_coverage = noi / interest_expense

    # Annualized interest (assuming quarterly data, multiply by 4)
    annualized_interest = interest_expense * 4

    return {
        'noi_interest_coverage': round(noi_interest_coverage, 2),
        'annualized_interest_expense': annualized_interest,
        'quarterly_interest_expense': interest_expense
    }


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

    # Assemble complete output with issuer identification
    return {
        'issuer_name': financial_data['issuer_name'],
        'reporting_date': financial_data['reporting_date'],
        'report_period': financial_data.get('report_period', 'Unknown'),
        'currency': financial_data.get('currency', 'Unknown'),
        'leverage_metrics': leverage_metrics,
        'reit_metrics': reit_metrics,
        'coverage_ratios': coverage_ratios
    }


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
        print(f"Period: {result['report_period']}")
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
