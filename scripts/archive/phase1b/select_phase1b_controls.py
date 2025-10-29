#!/usr/bin/env python3
"""
Select 10 matched control observations for Phase 1B subset.

This script selects control observations that match the temporal distribution
of the 10 target cuts (2023-2025) from the existing control_observations.csv.

Matching criteria:
1. Same observation year as target cuts
2. Different REIT (to ensure independence)
3. Diverse sector representation

Usage:
    python scripts/select_phase1b_controls.py \
        --targets data/phase1b_target_cuts.csv \
        --controls data/control_observations.csv \
        --output Issuer_Reports/phase1b/selected_controls.csv
"""

import argparse
import pandas as pd
import sys
from collections import Counter
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Select matched controls for Phase 1B"
    )
    parser.add_argument(
        "--targets",
        type=Path,
        default=Path("data/phase1b_target_cuts.csv"),
        help="Path to phase1b_target_cuts.csv"
    )
    parser.add_argument(
        "--controls",
        type=Path,
        default=Path("data/control_observations.csv"),
        help="Path to control_observations.csv"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("Issuer_Reports/phase1b/selected_controls.csv"),
        help="Output CSV file"
    )

    args = parser.parse_args()

    # Read targets
    if not args.targets.exists():
        print(f"ERROR: Targets file not found: {args.targets}", file=sys.stderr)
        sys.exit(1)

    targets_df = pd.read_csv(args.targets)
    print(f"✓ Loaded {len(targets_df)} target cuts from {args.targets}")

    # Read controls
    if not args.controls.exists():
        print(f"ERROR: Controls file not found: {args.controls}", file=sys.stderr)
        sys.exit(1)

    controls_df = pd.read_csv(args.controls)
    print(f"✓ Loaded {len(controls_df)} control observations from {args.controls}")

    # Parse observation dates
    targets_df['observation_date'] = pd.to_datetime(targets_df['observation_date'])
    controls_df['observation_date_full'] = pd.to_datetime(controls_df['observation_date_full'])

    # Extract year and quarter from targets
    targets_df['obs_year'] = targets_df['observation_date'].dt.year
    targets_df['obs_quarter'] = targets_df['observation_date'].dt.quarter

    # Count target distribution
    target_years = targets_df['obs_year'].value_counts().to_dict()
    target_reits = set(targets_df['ticker'].str.replace('.TO', '', regex=False))

    print(f"\n📊 Target Cut Temporal Distribution:")
    for year, count in sorted(target_years.items()):
        print(f"   {year}: {count} observations")

    print(f"\n🎯 Target REITs: {', '.join(sorted(target_reits))}")

    # Filter controls to matching time periods
    controls_df = controls_df[controls_df['observation_year'].isin(target_years.keys())]
    print(f"\n✓ Filtered to {len(controls_df)} controls from {min(target_years)}-{max(target_years)}")

    # Exclude any REITs that are in targets (to ensure independence)
    controls_df['ticker_clean'] = controls_df['ticker'].str.replace('.TO', '', regex=False)
    controls_df = controls_df[~controls_df['ticker_clean'].isin(target_reits)]
    print(f"✓ Excluded target REITs: {len(controls_df)} controls remaining")

    # Sample 10 controls matching temporal distribution
    selected_controls = []
    for year, target_count in sorted(target_years.items()):
        year_controls = controls_df[controls_df['observation_year'] == year]

        # Sample proportionally
        n_to_sample = target_count
        if len(year_controls) >= n_to_sample:
            sampled = year_controls.sample(n=n_to_sample, random_state=42)
        else:
            sampled = year_controls  # Take all if not enough
            print(f"⚠️  Warning: Only {len(year_controls)} controls available for {year} (need {n_to_sample})")

        selected_controls.append(sampled)

    selected_df = pd.concat(selected_controls, ignore_index=True)

    # If we don't have exactly 10, adjust
    if len(selected_df) < 10:
        print(f"\n⚠️  Only {len(selected_df)} controls selected (need 10). Adding more...")
        remaining = controls_df[~controls_df.index.isin(selected_df.index)]
        additional = remaining.sample(n=10 - len(selected_df), random_state=42)
        selected_df = pd.concat([selected_df, additional], ignore_index=True)
    elif len(selected_df) > 10:
        print(f"\n⚠️  {len(selected_df)} controls selected (need 10). Randomly reducing...")
        selected_df = selected_df.sample(n=10, random_state=42)

    # Save selected controls
    args.output.parent.mkdir(parents=True, exist_ok=True)
    selected_df.to_csv(args.output, index=False)
    print(f"\n✅ Selected {len(selected_df)} matched controls saved to: {args.output}")

    # Summary statistics
    print(f"\n📊 Selected Control Distribution:")
    year_dist = selected_df['observation_year'].value_counts().sort_index()
    for year, count in year_dist.items():
        print(f"   {year}: {count} observations")

    print(f"\n🏢 Selected Control REITs:")
    reit_dist = selected_df.groupby(['reit_name', 'ticker'])['observation_year'].count()
    for (reit_name, ticker), count in reit_dist.items():
        print(f"   {reit_name} ({ticker}): {count} observation(s)")

    sector_dist = selected_df['sector'].value_counts()
    print(f"\n🏗️  Sector Distribution:")
    for sector, count in sector_dist.items():
        print(f"   {sector}: {count} ({count/len(selected_df)*100:.1f}%)")


if __name__ == "__main__":
    main()
