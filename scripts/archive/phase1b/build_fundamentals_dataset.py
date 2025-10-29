#!/usr/bin/env python3
"""
Build comprehensive fundamentals dataset from all Phase 3 metrics files.

Extracts key features from Phase 3 JSON files and creates a CSV dataset
for Issue #38 v2.0 distribution cut prediction model training.

Usage:
    python scripts/build_fundamentals_dataset.py --output data/fundamentals_dataset_phase1b.csv
"""

import json
import csv
import glob
import argparse
from pathlib import Path

# Observation type mapping (from Phase 1B plan)
OBSERVATION_TYPES = {
    # Target cuts (distribution cuts)
    1: "target", 2: "target", 3: "target", 4: "target", 5: "target",
    6: "target", 7: "target", 8: "target", 9: "target", 10: "target",
    # Controls (no cuts)
    11: "control", 12: "control", 13: "control", 14: "control", 15: "control",
    16: "control", 17: "control", 18: "control", 19: "control", 20: "control",
    # Phase 1B expansion (obs 21-27)
    21: "control",  # RioCan Q4 2024 - no cut
    22: "control",  # RioCan Q4 2023 - no cut
    25: "target",   # First Capital Q4 2023 - 33% cut Sept 2022
    26: "control",  # Killam Q4 2023 - no cut
    27: "control"   # Choice Properties Q4 2024 - no cut
}

def extract_observation_number(filename):
    """Extract observation number from filename like 'obs1_HR_Q4_2022_phase3_metrics.json'"""
    basename = Path(filename).name
    if basename.startswith('obs'):
        num_str = basename.split('_')[0].replace('obs', '')
        return int(num_str)
    return None

def infer_sector(issuer_name):
    """Infer REIT sector from issuer name."""
    name_lower = issuer_name.lower()
    
    if "residential" in name_lower or "apartment" in name_lower:
        return "Residential"
    elif "office" in name_lower:
        return "Office"
    elif "retail" in name_lower or "shopping" in name_lower or "plaza" in name_lower:
        return "Retail"
    elif "industrial" in name_lower:
        return "Industrial"
    elif "healthcare" in name_lower or "medical" in name_lower or "care" in name_lower:
        return "Healthcare"
    elif "diversified" in name_lower or "mixed" in name_lower:
        return "Diversified"
    else:
        return "Other"

def extract_fundamentals(phase3_file):
    """Extract key fundamental features from Phase 3 metrics JSON."""
    
    with open(phase3_file, 'r') as f:
        data = json.load(f)
    
    # Extract observation number and type
    obs_num = extract_observation_number(phase3_file)
    cut_type = OBSERVATION_TYPES.get(obs_num, 'unknown')
    
    # Extract features
    features = {
        'observation': obs_num,
        'issuer_name': data.get('issuer_name', ''),
        'reporting_date': data.get('reporting_date', ''),
        'reporting_period': data.get('reporting_period', ''),
        'cut_type': cut_type,
        
        # Leverage metrics
        'total_debt': data.get('leverage_metrics', {}).get('total_debt', None),
        'debt_to_assets_percent': data.get('leverage_metrics', {}).get('debt_to_assets_percent', None),
        'net_debt_ratio': data.get('leverage_metrics', {}).get('net_debt_ratio', None),
        
        # REIT metrics - issuer reported
        'ffo_reported': data.get('reit_metrics', {}).get('ffo', None),
        'affo_reported': data.get('reit_metrics', {}).get('affo', None),
        'ffo_per_unit': data.get('reit_metrics', {}).get('ffo_per_unit', None),
        'affo_per_unit': data.get('reit_metrics', {}).get('affo_per_unit', None),
        'distributions_per_unit': data.get('reit_metrics', {}).get('distributions_per_unit', None),
        'ffo_payout_ratio': data.get('reit_metrics', {}).get('ffo_payout_ratio', None),
        'affo_payout_ratio': data.get('reit_metrics', {}).get('affo_payout_ratio', None),
        
        # REIT metrics - calculated
        'ffo_calculated': data.get('reit_metrics', {}).get('ffo_calculated', None),
        'affo_calculated': data.get('reit_metrics', {}).get('affo_calculated', None),
        'acfo_calculated': data.get('reit_metrics', {}).get('acfo_calculated', None),
        
        # Calculated per-unit metrics
        'ffo_per_unit_calc': data.get('reit_metrics', {}).get('ffo_calculation_detail', {}).get('ffo_per_unit', None),
        'affo_per_unit_calc': data.get('reit_metrics', {}).get('affo_calculation_detail', {}).get('affo_per_unit', None),
        'acfo_per_unit_calc': data.get('reit_metrics', {}).get('acfo_calculation_detail', {}).get('acfo_per_unit', None),
        
        # Coverage ratios
        'noi_interest_coverage': data.get('coverage_ratios', {}).get('noi_interest_coverage', None),
        'annualized_interest_expense': data.get('coverage_ratios', {}).get('annualized_interest_expense', None),
        
        # Portfolio metrics
        'total_properties': data.get('portfolio_metrics', {}).get('total_properties', None),
        'occupancy_rate': data.get('portfolio_metrics', {}).get('occupancy_rate', None),
        'same_property_noi_growth': data.get('portfolio_metrics', {}).get('same_property_noi_growth', None),
        
        # Liquidity and burn rate
        'available_cash': data.get('liquidity_position', {}).get('available_cash', None),
        'total_available_liquidity': data.get('liquidity_position', {}).get('total_available_liquidity', None),
        'monthly_burn_rate': data.get('burn_rate_analysis', {}).get('monthly_burn_rate', None),
        'self_funding_ratio': data.get('burn_rate_analysis', {}).get('self_funding_ratio', None),
        
        # Dilution analysis
        'dilution_percentage': data.get('dilution_analysis', {}).get('dilution_percentage', None),
        'dilution_materiality': data.get('dilution_analysis', {}).get('dilution_materiality', None),
        
        # Sector (inferred from issuer name)
        'sector': infer_sector(data.get('issuer_name', ''))
    }
    
    return features

def main():
    parser = argparse.ArgumentParser(description='Build fundamentals dataset from Phase 3 metrics')
    parser.add_argument('--output', default='data/fundamentals_dataset_phase1b.csv',
                       help='Output CSV file path')
    parser.add_argument('--input-dir', default='Issuer_Reports/phase1b/extractions',
                       help='Directory containing Phase 3 metrics JSON files')
    
    args = parser.parse_args()
    
    # Find all Phase 3 metrics files
    pattern = f"{args.input_dir}/*_phase3_metrics.json"
    phase3_files = sorted(glob.glob(pattern))
    
    if not phase3_files:
        print(f"❌ No Phase 3 metrics files found in {args.input_dir}")
        return 1
    
    print(f"📊 Found {len(phase3_files)} Phase 3 metrics files")
    
    # Extract features from all files
    all_features = []
    for phase3_file in phase3_files:
        try:
            features = extract_fundamentals(phase3_file)
            all_features.append(features)
            print(f"✓ Obs {features['observation']:2d}: {features['issuer_name'][:30]:30s} ({features['cut_type']})")
        except Exception as e:
            print(f"❌ Error processing {phase3_file}: {e}")
            continue
    
    if not all_features:
        print("❌ No features extracted")
        return 1
    
    # Sort by observation number
    all_features.sort(key=lambda x: x['observation'])
    
    # Write to CSV
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = list(all_features[0].keys())
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_features)
    
    print(f"\n✅ Fundamentals dataset saved to: {output_path}")
    print(f"📊 Total observations: {len(all_features)}")
    
    # Summary statistics
    targets = sum(1 for f in all_features if f['cut_type'] == 'target')
    controls = sum(1 for f in all_features if f['cut_type'] == 'control')
    
    print(f"\n📈 Distribution:")
    print(f"   • Target cuts: {targets}")
    print(f"   • Controls: {controls}")
    
    # Calculate summary stats for key metrics
    affo_payouts = [f['affo_payout_ratio'] for f in all_features if f['affo_payout_ratio'] is not None]
    if affo_payouts:
        avg_payout = sum(affo_payouts) / len(affo_payouts)
        print(f"\n📊 AFFO Payout Ratio:")
        print(f"   • Average: {avg_payout:.1f}%")
        print(f"   • Min: {min(affo_payouts):.1f}%")
        print(f"   • Max: {max(affo_payouts):.1f}%")
    
    leverage = [f['debt_to_assets_percent'] for f in all_features if f['debt_to_assets_percent'] is not None]
    if leverage:
        avg_leverage = sum(leverage) / len(leverage)
        print(f"\n📊 Debt/Assets:")
        print(f"   • Average: {avg_leverage:.1f}%")
        print(f"   • Min: {min(leverage):.1f}%")
        print(f"   • Max: {max(leverage):.1f}%")
    
    coverage = [f['noi_interest_coverage'] for f in all_features if f['noi_interest_coverage'] is not None and f['noi_interest_coverage'] > 0]
    if coverage:
        avg_coverage = sum(coverage) / len(coverage)
        print(f"\n📊 Interest Coverage:")
        print(f"   • Average: {avg_coverage:.2f}x")
        print(f"   • Min: {min(coverage):.2f}x")
        print(f"   • Max: {max(coverage):.2f}x")
    
    return 0

if __name__ == '__main__':
    exit(main())
