#!/usr/bin/env python3
"""
Merge cuts and controls into balanced training dataset.

Creates final dataset with target variable for modeling.

Usage:
    python scripts/merge_balanced_dataset.py \
      --cuts data/training_dataset_v2.csv \
      --controls data/control_observations_enriched.csv \
      --output data/training_dataset_v2_balanced.csv
"""

import argparse
import pandas as pd
from pathlib import Path


def merge_datasets(cuts_file: Path, controls_file: Path, output_file: Path):
    """
    Merge cuts and controls into balanced dataset.

    Args:
        cuts_file: Path to enriched cuts dataset
        controls_file: Path to enriched controls dataset
        output_file: Path to save balanced dataset
    """
    print(f"\nLoading datasets...")
    cuts_df = pd.read_csv(cuts_file)
    controls_df = pd.read_csv(controls_file)

    print(f"  Cuts: {len(cuts_df)} observations")
    print(f"  Controls: {len(controls_df)} observations")

    # Add target variable
    cuts_df['cut_occurred'] = 1
    controls_df['cut_occurred'] = 0

    # Select common columns for alignment
    # Cuts have: reit_name, ticker, cut_date, cut_magnitude_pct, recovery_*, market_*, macro_*
    # Controls have: reit_name, ticker, sector, observation_date, market_*, macro_*

    # Create aligned dataset with common schema
    cuts_aligned = pd.DataFrame({
        'reit_name': cuts_df['reit_name'],
        'ticker': cuts_df['ticker'],
        'observation_date': cuts_df['observation_date'],
        'cut_occurred': cuts_df['cut_occurred'],
        'cut_date': cuts_df['cut_date'],
        'cut_magnitude_pct': cuts_df['cut_magnitude_pct'],
        'recovery_level_pct': cuts_df['recovery_level_pct'],
        'recovery_months': cuts_df['recovery_months'],
        'full_recovery': cuts_df['full_recovery'],
        'recovery_status': cuts_df['recovery_status'],
        'market_price_stress_pct': cuts_df['market_price_stress_pct'],
        'market_risk_score': cuts_df['market_risk_score'],
        'market_volatility_90d': cuts_df['market_volatility_90d'],
        'market_momentum_3m': cuts_df['market_momentum_3m'],
        'market_risk_level': cuts_df['market_risk_level'],
        'macro_policy_rate': cuts_df['macro_policy_rate'],
        'macro_rate_change_12m': cuts_df['macro_rate_change_12m'],
        'macro_rate_cycle': cuts_df['macro_rate_cycle'],
        'macro_credit_stress_score': cuts_df['macro_credit_stress_score'],
        'macro_credit_environment': cuts_df['macro_credit_environment']
    })

    controls_aligned = pd.DataFrame({
        'reit_name': controls_df['reit_name'],
        'ticker': controls_df['ticker'],
        'observation_date': controls_df['observation_date'],
        'cut_occurred': controls_df['cut_occurred'],
        'cut_date': None,
        'cut_magnitude_pct': None,
        'recovery_level_pct': None,
        'recovery_months': None,
        'full_recovery': None,
        'recovery_status': None,
        'market_price_stress_pct': controls_df['market_price_stress_pct'],
        'market_risk_score': controls_df['market_risk_score'],
        'market_volatility_90d': controls_df['market_volatility_90d'],
        'market_momentum_3m': controls_df['market_momentum_3m'],
        'market_risk_level': controls_df['market_risk_level'],
        'macro_policy_rate': controls_df['macro_policy_rate'],
        'macro_rate_change_12m': controls_df['macro_rate_change_12m'],
        'macro_rate_cycle': controls_df['macro_rate_cycle'],
        'macro_credit_stress_score': controls_df['macro_credit_stress_score'],
        'macro_credit_environment': controls_df['macro_credit_environment']
    })

    # Merge
    balanced_df = pd.concat([cuts_aligned, controls_aligned], ignore_index=True)

    # Shuffle to mix cuts and controls
    balanced_df = balanced_df.sample(frac=1, random_state=42).reset_index(drop=True)

    print(f"\n✓ Created balanced dataset:")
    print(f"  Total observations: {len(balanced_df)}")
    print(f"  Cuts (1): {balanced_df['cut_occurred'].sum()} ({balanced_df['cut_occurred'].sum()/len(balanced_df)*100:.1f}%)")
    print(f"  Controls (0): {(balanced_df['cut_occurred']==0).sum()} ({(balanced_df['cut_occurred']==0).sum()/len(balanced_df)*100:.1f}%)")

    # Data quality summary
    print(f"\n✓ Data quality:")
    print(f"  Market coverage: {(~balanced_df['market_risk_score'].isna()).sum()}/{len(balanced_df)} ({(~balanced_df['market_risk_score'].isna()).sum()/len(balanced_df)*100:.1f}%)")
    print(f"  Macro coverage: {(~balanced_df['macro_policy_rate'].isna()).sum()}/{len(balanced_df)} ({(~balanced_df['macro_policy_rate'].isna()).sum()/len(balanced_df)*100:.1f}%)")

    # Feature summary
    print(f"\n✓ Feature summary:")
    print(f"  Total features: {len(balanced_df.columns)}")
    print(f"  Predictive features: 14 (5 market + 5 macro + 4 recovery)")
    print(f"  Target variable: cut_occurred (0/1)")
    print(f"  Metadata: {len(balanced_df.columns) - 15} columns")

    # Save
    print(f"\n✓ Saving balanced dataset to {output_file}...")
    balanced_df.to_csv(output_file, index=False)
    print(f"  Saved {len(balanced_df)} observations")

    # Summary stats by class
    print(f"\n" + "="*60)
    print("Class-Specific Summary Statistics")
    print("="*60)

    for class_val, class_name in [(0, "Controls"), (1, "Cuts")]:
        subset = balanced_df[balanced_df['cut_occurred'] == class_val]
        print(f"\n{class_name} (n={len(subset)}):")

        if (~subset['market_risk_score'].isna()).sum() > 0:
            print(f"  Market Risk Score: {subset['market_risk_score'].mean():.1f} ± {subset['market_risk_score'].std():.1f}")
            print(f"  Price Stress: {subset['market_price_stress_pct'].mean():.1f}% ± {subset['market_price_stress_pct'].std():.1f}%")
            print(f"  Volatility: {subset['market_volatility_90d'].mean():.1f}% ± {subset['market_volatility_90d'].std():.1f}%")

        if (~subset['macro_policy_rate'].isna()).sum() > 0:
            print(f"  Policy Rate: {subset['macro_policy_rate'].mean():.2f}% ± {subset['macro_policy_rate'].std():.2f}%")
            print(f"  Credit Stress: {subset['macro_credit_stress_score'].mean():.1f} ± {subset['macro_credit_stress_score'].std():.1f}")

    print("\n" + "="*60)

    return balanced_df


def main():
    parser = argparse.ArgumentParser(
        description='Merge cuts and controls into balanced training dataset'
    )
    parser.add_argument(
        '--cuts',
        type=Path,
        default=Path('data/training_dataset_v2.csv'),
        help='Path to enriched cuts dataset'
    )
    parser.add_argument(
        '--controls',
        type=Path,
        default=Path('data/control_observations_enriched.csv'),
        help='Path to enriched controls dataset'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/training_dataset_v2_balanced.csv'),
        help='Path to save balanced dataset'
    )

    args = parser.parse_args()

    if not args.cuts.exists():
        print(f"ERROR: Cuts file not found: {args.cuts}")
        return 1

    if not args.controls.exists():
        print(f"ERROR: Controls file not found: {args.controls}")
        return 1

    merge_datasets(args.cuts, args.controls, args.output)

    print(f"\n✓ Balanced dataset creation complete!")
    print(f"  Output: {args.output}")
    print(f"\n📊 Ready for Week 3: Model Training!")

    return 0


if __name__ == '__main__':
    exit(main())
