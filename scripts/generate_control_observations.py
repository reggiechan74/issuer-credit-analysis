#!/usr/bin/env python3
"""
Generate control observations for distribution cut prediction model.

Samples non-cut quarters from stable REITs to create balanced dataset.

Usage:
    python scripts/generate_control_observations.py \
      --cuts-file data/training_dataset_v2.csv \
      --output data/control_observations.csv \
      --num-controls 35
"""

import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import random

# Control REIT candidates (REITs with no cuts detected)
CONTROL_REITS = {
    # Retail
    "SmartCentres REIT": {"ticker": "SRU-UN.TO", "sector": "Retail"},
    "CT REIT": {"ticker": "CRT-UN.TO", "sector": "Retail"},
    "Choice Properties REIT": {"ticker": "CHP-UN.TO", "sector": "Retail"},
    "Plaza Retail REIT": {"ticker": "PLZ-UN.TO", "sector": "Retail"},
    "Slate Grocery REIT": {"ticker": "SGR-U.TO", "sector": "Retail"},

    # Industrial
    "Dream Industrial REIT": {"ticker": "DIR-UN.TO", "sector": "Industrial"},
    "Nexus Industrial REIT": {"ticker": "NXR-UN.TO", "sector": "Industrial"},

    # Residential
    "InterRent REIT": {"ticker": "IIP-UN.TO", "sector": "Residential"},
    "Minto Apartment REIT": {"ticker": "MI-UN.TO", "sector": "Residential"},
    "Killam Apartment REIT": {"ticker": "KMP-UN.TO", "sector": "Residential"},
    "Morguard North American Residential REIT": {"ticker": "MRG-UN.TO", "sector": "Residential"},

    # Healthcare
    "Chartwell Retirement Residences": {"ticker": "CSH-UN.TO", "sector": "Healthcare"},
    "Extendicare": {"ticker": "EXE.TO", "sector": "Healthcare"}
}


class ControlObservationGenerator:
    """Generate control observations matching temporal distribution of cuts."""

    def __init__(self, num_controls: int = 35, lookback_months: int = 3):
        """
        Initialize generator.

        Args:
            num_controls: Target number of control observations
            lookback_months: Months before observation for features
        """
        self.num_controls = num_controls
        self.lookback_months = lookback_months
        random.seed(42)  # Reproducibility

    def generate_controls(self, cuts_file: Path, output_file: Path):
        """
        Generate control observations.

        Args:
            cuts_file: Path to cuts dataset
            output_file: Path to save control observations
        """
        print(f"\nLoading cuts dataset from {cuts_file}...")
        cuts_df = pd.read_csv(cuts_file)
        print(f"  Loaded {len(cuts_df)} cut observations")

        # Analyze temporal distribution of cuts
        cuts_df['cut_year'] = pd.to_datetime(cuts_df['cut_date']).dt.year
        cuts_df['cut_quarter'] = pd.to_datetime(cuts_df['cut_date']).dt.quarter

        year_dist = cuts_df['cut_year'].value_counts().sort_index()

        print(f"\nCut temporal distribution:")
        for year, count in year_dist.items():
            pct = count / len(cuts_df) * 100
            print(f"  {year}: {count:2d} cuts ({pct:.1f}%)")

        # Calculate target controls per year (match distribution)
        target_controls_per_year = {}
        for year, count in year_dist.items():
            target = int((count / len(cuts_df)) * self.num_controls)
            target_controls_per_year[year] = max(target, 1)  # At least 1

        # Adjust to hit exact target
        total = sum(target_controls_per_year.values())
        if total < self.num_controls:
            # Add extras to most recent years
            years_sorted = sorted(target_controls_per_year.keys(), reverse=True)
            for year in years_sorted:
                if total >= self.num_controls:
                    break
                target_controls_per_year[year] += 1
                total += 1

        print(f"\nTarget control distribution (n={self.num_controls}):")
        for year in sorted(target_controls_per_year.keys()):
            count = target_controls_per_year[year]
            print(f"  {year}: {count:2d} controls")

        # Generate control observations
        control_observations = []

        for year, target_count in target_controls_per_year.items():
            # Select random REITs for this year
            reits_needed = target_count
            selected_reits = random.sample(list(CONTROL_REITS.keys()),
                                         min(reits_needed, len(CONTROL_REITS)))

            # If need more controls than REITs, sample with replacement
            if reits_needed > len(selected_reits):
                selected_reits = random.choices(list(CONTROL_REITS.keys()), k=reits_needed)
            else:
                selected_reits = selected_reits[:reits_needed]

            # For each selected REIT, generate a random quarter in that year
            for reit_name in selected_reits:
                reit_info = CONTROL_REITS[reit_name]

                # Random quarter in year
                quarter = random.randint(1, 4)

                # Quarter end month
                quarter_end_month = quarter * 3

                # Random day in quarter-end month (28-31 depending on month)
                if quarter_end_month in [3, 12]:
                    day = 31
                elif quarter_end_month == 6:
                    day = 30
                else:  # Sep
                    day = 30

                try:
                    observation_date_full = datetime(year, quarter_end_month, day)
                except ValueError:
                    observation_date_full = datetime(year, quarter_end_month, 28)

                # Observation date (3 months prior)
                observation_date = observation_date_full - timedelta(days=self.lookback_months * 30)

                control_obs = {
                    'reit_name': reit_name,
                    'ticker': reit_info['ticker'],
                    'sector': reit_info['sector'],
                    'observation_year': year,
                    'observation_quarter': quarter,
                    'observation_date_full': observation_date_full.strftime('%Y-%m-%d'),
                    'observation_date': observation_date.strftime('%Y-%m-%d'),
                    'cut_occurred': 0,  # Control observation
                    'cut_date': None,
                    'cut_magnitude_pct': None
                }

                control_observations.append(control_obs)

        # Convert to DataFrame
        controls_df = pd.DataFrame(control_observations)

        print(f"\n✓ Generated {len(controls_df)} control observations")

        # Summary by sector
        print(f"\nControl observations by sector:")
        sector_counts = controls_df['sector'].value_counts()
        for sector, count in sector_counts.items():
            pct = count / len(controls_df) * 100
            print(f"  {sector:12s}: {count:2d} ({pct:.1f}%)")

        # Summary by REIT
        print(f"\nControl observations by REIT (top 10):")
        reit_counts = controls_df['reit_name'].value_counts().head(10)
        for reit, count in reit_counts.items():
            print(f"  {reit[:40]:40s}: {count:2d}")

        # Save
        print(f"\n✓ Saving control observations to {output_file}...")
        controls_df.to_csv(output_file, index=False)
        print(f"  Saved {len(controls_df)} control observations")

        return controls_df


def main():
    parser = argparse.ArgumentParser(
        description='Generate control observations for balanced dataset'
    )
    parser.add_argument(
        '--cuts-file',
        type=Path,
        default=Path('data/training_dataset_v2.csv'),
        help='Path to cuts dataset CSV'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/control_observations.csv'),
        help='Path to save control observations'
    )
    parser.add_argument(
        '--num-controls',
        type=int,
        default=35,
        help='Target number of control observations (default: 35 for ~50/50 balance with 29 cuts)'
    )

    args = parser.parse_args()

    if not args.cuts_file.exists():
        print(f"ERROR: Cuts file not found: {args.cuts_file}")
        return 1

    generator = ControlObservationGenerator(num_controls=args.num_controls)
    generator.generate_controls(args.cuts_file, args.output)

    print(f"\n✓ Control observation generation complete!")
    print(f"  Cuts: 29 observations (from {args.cuts_file})")
    print(f"  Controls: {args.num_controls} observations (saved to {args.output})")
    print(f"  Total dataset: {29 + args.num_controls} observations")
    print(f"  Cut rate: {29/(29 + args.num_controls)*100:.1f}%")

    return 0


if __name__ == '__main__':
    exit(main())
