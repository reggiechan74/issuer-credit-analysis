#!/usr/bin/env python3
"""
Create comprehensive Phase 1B tracking spreadsheet.

Combines target cuts and matched controls into a single tracking file
for Phase 1B fundamental extraction (n=20).

Usage:
    python scripts/create_phase1b_tracking.py
"""

import pandas as pd
from pathlib import Path


def main():
    # Read targets and controls
    targets_df = pd.read_csv("data/phase1b_target_cuts.csv")
    controls_df = pd.read_csv("Issuer_Reports/phase1b/selected_controls.csv")

    print(f"✓ Loaded {len(targets_df)} target cuts")
    print(f"✓ Loaded {len(controls_df)} matched controls")

    # Standardize targets format
    targets_tracking = targets_df.copy()
    targets_tracking['observation_date'] = pd.to_datetime(targets_tracking['observation_date'])
    targets_tracking['observation_year'] = targets_tracking['observation_date'].dt.year
    targets_tracking['observation_quarter'] = targets_tracking['observation_date'].dt.quarter
    targets_tracking['observation_date_full'] = targets_tracking['observation_date'] + pd.DateOffset(months=3) - pd.DateOffset(days=1)
    targets_tracking['observation_date_full'] = targets_tracking['observation_date_full'].dt.strftime('%Y-%m-%d')
    targets_tracking['observation_date'] = targets_tracking['observation_date'].dt.strftime('%Y-%m-%d')
    targets_tracking['cut_occurred'] = 1

    # Standardize controls format
    controls_tracking = controls_df.copy()
    controls_tracking['cut_date'] = None
    controls_tracking['cut_magnitude_pct'] = None

    # Align columns
    common_cols = [
        'reit_name', 'ticker', 'sector', 'observation_year', 'observation_quarter',
        'observation_date_full', 'observation_date', 'cut_occurred',
        'cut_date', 'cut_magnitude_pct'
    ]

    # Add sector to targets (infer from name)
    def infer_sector(name):
        name_lower = name.lower()
        if 'residential' in name_lower or 'apartment' in name_lower:
            return 'Residential'
        elif 'office' in name_lower:
            return 'Office'
        elif 'retail' in name_lower or 'plaza' in name_lower:
            return 'Retail'
        elif 'industrial' in name_lower:
            return 'Industrial'
        elif 'healthcare' in name_lower:
            return 'Healthcare'
        return 'Diversified'

    if 'sector' not in targets_tracking.columns:
        targets_tracking['sector'] = targets_tracking['reit_name'].apply(infer_sector)

    # Combine
    combined = pd.concat([
        targets_tracking[common_cols],
        controls_tracking[common_cols]
    ], ignore_index=True)

    # Add tracking columns
    combined['status'] = 'pending'
    combined['pdf_downloaded'] = 'no'
    combined['phase1_complete'] = 'no'
    combined['phase2_complete'] = 'no'
    combined['phase3_complete'] = 'no'
    combined['fundamentals_extracted'] = 'no'
    combined['notes'] = ''

    # Sort by cut_occurred (targets first), then by date
    combined = combined.sort_values(['cut_occurred', 'observation_date'], ascending=[False, True])
    combined = combined.reset_index(drop=True)

    # Save
    output_path = Path("Issuer_Reports/phase1b/phase1b_tracking.csv")
    combined.to_csv(output_path, index=False)

    print(f"\n✅ Created comprehensive tracking file: {output_path}")
    print(f"   Total observations: {len(combined)}")
    print(f"   - Target cuts: {(combined['cut_occurred'] == 1).sum()}")
    print(f"   - Controls: {(combined['cut_occurred'] == 0).sum()}")

    # Summary by year
    print(f"\n📊 Distribution by Year:")
    year_summary = combined.groupby(['observation_year', 'cut_occurred']).size().unstack(fill_value=0)
    year_summary.columns = ['Controls', 'Target Cuts']
    print(year_summary)

    # Summary by sector
    print(f"\n🏗️  Distribution by Sector:")
    sector_summary = combined.groupby(['sector', 'cut_occurred']).size().unstack(fill_value=0)
    sector_summary.columns = ['Controls', 'Target Cuts']
    print(sector_summary)


if __name__ == "__main__":
    main()
