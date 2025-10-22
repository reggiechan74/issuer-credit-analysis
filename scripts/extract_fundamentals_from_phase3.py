#!/usr/bin/env python3
"""
Extract fundamental features from Phase 3 calculated metrics JSON files.

This script reads Phase 3 output and extracts the 6 fundamental features
needed for Issue #38 v2.0 distribution cut prediction model:
1. AFFO payout ratio (%)
2. Interest coverage ratio (NOI / Interest Expense)
3. Debt-to-assets ratio (%)
4. Debt-to-EBITDA ratio
5. Occupancy rate (%)
6. Sector (property type)

Usage:
    python scripts/extract_fundamentals_from_phase3.py \
        <phase3_json_file> \
        --output <fundamentals_json>
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional


def extract_fundamentals(phase3_data: Dict) -> Dict:
    """
    Extract fundamental features from Phase 3 calculated metrics.

    Args:
        phase3_data: Phase 3 JSON data

    Returns:
        Dictionary with 6 fundamental features
    """
    fundamentals = {
        "issuer_name": phase3_data.get("issuer_name"),
        "reporting_date": phase3_data.get("reporting_date"),
        "reporting_period": phase3_data.get("reporting_period"),
        "currency": phase3_data.get("currency", "CAD")
    }

    # 1. AFFO Payout Ratio (%)
    reit_metrics = phase3_data.get("reit_metrics", {})
    fundamentals["affo_payout_ratio"] = reit_metrics.get("affo_payout_ratio")

    # 2. Interest Coverage Ratio (NOI / Interest Expense)
    coverage = phase3_data.get("coverage_ratios", {})
    fundamentals["interest_coverage_ratio"] = coverage.get("noi_interest_coverage")

    # 3. Debt-to-Assets Ratio (%)
    leverage = phase3_data.get("leverage_metrics", {})
    fundamentals["debt_to_assets_pct"] = leverage.get("debt_to_assets_percent")

    # 4. Debt-to-EBITDA Ratio
    # Check both ebitda_metrics and leverage_metrics
    ebitda_metrics = phase3_data.get("ebitda_metrics", {})
    debt_to_ebitda = ebitda_metrics.get("net_debt_to_ebitda")
    if debt_to_ebitda is None:
        debt_to_ebitda = leverage.get("debt_to_ebitda")
    fundamentals["debt_to_ebitda"] = debt_to_ebitda

    # 5. Occupancy Rate (%)
    portfolio = phase3_data.get("portfolio_metrics", {})
    occupancy = portfolio.get("occupancy_rate")
    if occupancy is not None:
        # Convert from decimal to percentage if needed
        if occupancy < 1.0:
            occupancy = occupancy * 100
    fundamentals["occupancy_rate_pct"] = occupancy

    # 6. Sector (property type)
    # Try to infer from issuer name or portfolio composition
    sector = infer_sector(phase3_data)
    fundamentals["sector"] = sector

    # Data quality assessment
    available_count = sum(1 for v in fundamentals.values()
                         if v is not None and v != "")
    fundamentals["data_quality"] = {
        "total_fields": 10,  # 4 metadata + 6 fundamental
        "available_fields": available_count,
        "completeness_pct": round(available_count / 10 * 100, 1)
    }

    return fundamentals


def infer_sector(phase3_data: Dict) -> Optional[str]:
    """
    Infer REIT sector from issuer name or portfolio composition.

    Sector categories:
    - Residential (apartments, multi-family)
    - Office (commercial office buildings)
    - Retail (shopping centers, malls)
    - Industrial (warehouses, logistics)
    - Healthcare (hospitals, medical offices, senior housing)
    - Diversified (mixed portfolio)

    Args:
        phase3_data: Phase 3 JSON data

    Returns:
        Sector string or None
    """
    issuer_name = phase3_data.get("issuer_name", "").lower()

    # Pattern matching on issuer name
    if "residential" in issuer_name or "apartment" in issuer_name:
        return "Residential"
    elif "office" in issuer_name:
        return "Office"
    elif "retail" in issuer_name or "shopping" in issuer_name or "plaza" in issuer_name:
        return "Retail"
    elif "industrial" in issuer_name:
        return "Industrial"
    elif "healthcare" in issuer_name or "medical" in issuer_name:
        return "Healthcare"
    elif "diversified" in issuer_name or "mixed" in issuer_name:
        return "Diversified"

    # Check portfolio breakdown if available
    portfolio = phase3_data.get("portfolio_metrics", {})
    portfolio_breakdown = portfolio.get("property_type_breakdown", {})

    if portfolio_breakdown:
        # Find dominant property type (>60% = pure play)
        for prop_type, allocation in portfolio_breakdown.items():
            if allocation > 0.6:
                return prop_type.title()
        return "Diversified"

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Extract fundamental features from Phase 3 JSON"
    )
    parser.add_argument(
        "phase3_file",
        type=Path,
        help="Path to phase3_calculated_metrics.json"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON file (default: print to stdout)"
    )

    args = parser.parse_args()

    # Read Phase 3 data
    if not args.phase3_file.exists():
        print(f"ERROR: File not found: {args.phase3_file}", file=sys.stderr)
        sys.exit(1)

    with open(args.phase3_file) as f:
        phase3_data = json.load(f)

    # Extract fundamentals
    fundamentals = extract_fundamentals(phase3_data)

    # Output
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(fundamentals, f, indent=2)
        print(f"✓ Fundamentals extracted to: {args.output}")
    else:
        print(json.dumps(fundamentals, indent=2))

    # Summary
    quality = fundamentals["data_quality"]
    print(f"\n✓ Extracted {quality['available_fields']}/{quality['total_fields']} fields " +
          f"({quality['completeness_pct']}% complete)", file=sys.stderr)

    # Show what's available
    print(f"\nAvailable fundamentals:", file=sys.stderr)
    for key, value in fundamentals.items():
        if key not in ["issuer_name", "reporting_date", "reporting_period",
                      "currency", "data_quality"]:
            status = "✓" if value is not None else "✗"
            print(f"  {status} {key}: {value}", file=sys.stderr)


if __name__ == "__main__":
    main()
