#!/usr/bin/env python3
"""
Feature Engineering for Distribution Cut Prediction Model

Transforms raw financial metrics into ML-ready features based on:
- EDA findings (Issue #37 Week 2 Agent 1)
- Threshold analysis (Issue #37 Week 2 Agent 2)

Author: Claude Code
Version: 1.0.0
Date: 2025-10-21
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple


class DistributionCutFeatureEngineer:
    """Feature engineering for REIT distribution cut prediction."""

    def __init__(self):
        """Initialize feature engineer with threshold values from analysis."""
        # Thresholds from Agent 2 analysis
        self.PAYOUT_CRITICAL = 100.0  # >100% = mathematically unsustainable
        self.PAYOUT_HIGH = 95.0       # >95% = high risk (all 5 cuts ≥99%)
        self.PAYOUT_MODERATE = 85.0   # >85% = moderate risk

        self.COVERAGE_CRITICAL = 2.5  # <2.5x = distressed (True North 2.43x)
        self.COVERAGE_HIGH = 3.0      # <3.0x = elevated risk (all cuts ≤3.14x)
        self.COVERAGE_SAFE = 3.5      # >3.5x = low risk

        self.LEVERAGE_EXTREME = 9.0   # >9.0x Debt/EBITDA = critical
        self.LEVERAGE_HIGH = 8.0      # >8.0x = elevated risk

        self.DEBT_ASSETS_HIGH = 60.0  # >60% = approaching covenant limits
        self.DEBT_ASSETS_MODERATE = 55.0

        self.COVENANT_CRITICAL = 2.0  # <2% cushion = imminent breach
        self.COVENANT_HIGH = 5.0      # <5% = elevated risk

        # Office sector adjustment (more conservative threshold)
        self.OFFICE_PAYOUT_HIGH = 90.0  # Office REITs more sensitive

    def load_data(self, filepath: Path) -> pd.DataFrame:
        """Load training dataset."""
        df = pd.read_csv(filepath)
        print(f"✓ Loaded {len(df)} observations from {filepath}")
        return df

    def create_sector_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create sector dummy variables."""
        # Office sector flag (includes "Office" and "Retail/Office")
        df['is_office'] = df['sector'].str.contains('Office', case=False, na=False).astype(int)

        # Other sector flags
        df['is_retail'] = ((df['sector'] == 'Retail') |
                           (df['sector'] == 'Retail/Office')).astype(int)
        df['is_industrial'] = (df['sector'] == 'Industrial').astype(int)
        df['is_residential'] = (df['sector'] == 'Residential').astype(int)

        print(f"✓ Created sector features: {df['is_office'].sum()} office REITs")
        return df

    def create_binary_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create binary risk flags based on thresholds."""
        # AFFO Payout flags
        df['payout_critical'] = (df['affo_payout_ratio'] > self.PAYOUT_CRITICAL).astype(int)
        df['payout_high'] = (df['affo_payout_ratio'] > self.PAYOUT_HIGH).astype(int)
        df['payout_moderate'] = (df['affo_payout_ratio'] > self.PAYOUT_MODERATE).astype(int)

        # Interest Coverage flags
        df['coverage_critical'] = (df['interest_coverage'] < self.COVERAGE_CRITICAL).astype(int)
        df['coverage_high'] = (df['interest_coverage'] < self.COVERAGE_HIGH).astype(int)
        df['coverage_safe'] = (df['interest_coverage'] > self.COVERAGE_SAFE).astype(int)

        # Debt/EBITDA flags (handle missing values)
        df['leverage_extreme'] = (df['debt_to_ebitda'] > self.LEVERAGE_EXTREME).fillna(0).astype(int)
        df['leverage_high'] = (df['debt_to_ebitda'] > self.LEVERAGE_HIGH).fillna(0).astype(int)

        # Debt/Assets flags
        df['debt_assets_high'] = (df['debt_to_assets'] > self.DEBT_ASSETS_HIGH).astype(int)
        df['debt_assets_moderate'] = (df['debt_to_assets'] > self.DEBT_ASSETS_MODERATE).astype(int)

        # Dual stress flag (STRONGEST PREDICTOR from Agent 2)
        df['dual_stress'] = ((df['affo_payout_ratio'] > self.PAYOUT_HIGH) &
                             (df['interest_coverage'] < self.COVERAGE_HIGH)).astype(int)

        # Office-specific high risk (lower threshold for office)
        df['office_high_risk'] = ((df['is_office'] == 1) &
                                   (df['affo_payout_ratio'] > self.OFFICE_PAYOUT_HIGH)).astype(int)

        flag_count = df[[c for c in df.columns if c.endswith('_flag') or
                          c.startswith('payout_') or c.startswith('coverage_') or
                          c.startswith('leverage_') or c.startswith('debt_assets_') or
                          c == 'dual_stress' or c == 'office_high_risk']].shape[1]
        print(f"✓ Created {flag_count} binary risk flags")
        return df

    def create_interaction_terms(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create interaction features (strongest predictors)."""
        # Primary interaction: AFFO Payout × Office Sector
        # Agent 2: "Likely strongest predictor (office + high payout = near-certain cut)"
        df['affo_payout_x_office'] = df['affo_payout_ratio'] * df['is_office']

        # Secondary interaction: Payout × Coverage (dual stress continuous)
        df['payout_coverage_product'] = df['affo_payout_ratio'] * df['interest_coverage']

        # Debt/Assets × Liquidity Risk (from EDA: r=0.83 correlation)
        df['leverage_liquidity_interaction'] = (df['debt_to_assets'] / 100.0) * df['liquidity_risk_score']

        print("✓ Created 3 interaction terms")
        return df

    def create_composite_risk_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create composite risk score (0-100 scale).

        Based on Agent 2 threshold analysis scoring system:
        - Payout points: 0-5
        - Coverage points: 0-4
        - Leverage points: 0-3
        - Sector points: 0-2
        - Covenant points: 0-5

        Max score: 19 points → scaled to 0-100
        """
        df['risk_score'] = 0

        # Payout points (max 5)
        df.loc[df['affo_payout_ratio'] > 100, 'risk_score'] += 5
        df.loc[(df['affo_payout_ratio'] > 95) & (df['affo_payout_ratio'] <= 100), 'risk_score'] += 4
        df.loc[(df['affo_payout_ratio'] > 85) & (df['affo_payout_ratio'] <= 95), 'risk_score'] += 2

        # Coverage points (max 4)
        df.loc[df['interest_coverage'] < 2.5, 'risk_score'] += 4
        df.loc[(df['interest_coverage'] >= 2.5) & (df['interest_coverage'] < 3.0), 'risk_score'] += 3
        df.loc[(df['interest_coverage'] >= 3.0) & (df['interest_coverage'] < 3.5), 'risk_score'] += 2

        # Leverage points (max 3, handle missing)
        df.loc[df['debt_to_ebitda'] > 9, 'risk_score'] += 3
        df.loc[(df['debt_to_ebitda'] >= 8) & (df['debt_to_ebitda'] <= 9), 'risk_score'] += 2
        df.loc[df['debt_to_assets'] > 60, 'risk_score'] += 1

        # Sector points (max 2)
        df.loc[df['is_office'] == 1, 'risk_score'] += 2
        df.loc[df['is_retail'] == 1, 'risk_score'] += 1

        # Liquidity risk points (max 3)
        df.loc[df['liquidity_risk_score'] >= 3, 'risk_score'] += 3
        df.loc[df['liquidity_risk_score'] == 2, 'risk_score'] += 2

        # Scale to 0-100
        df['risk_score_scaled'] = (df['risk_score'] / 19.0) * 100.0

        # Risk level classification
        df['risk_level'] = pd.cut(
            df['risk_score_scaled'],
            bins=[0, 40, 60, 80, 100],
            labels=['LOW', 'MODERATE', 'HIGH', 'CRITICAL'],
            include_lowest=True
        )

        print(f"✓ Created composite risk score (mean: {df['risk_score_scaled'].mean():.1f}, max: {df['risk_score_scaled'].max():.1f})")
        return df

    def create_missing_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create missing value indicators (may be predictive)."""
        df['has_affo_data'] = (~df['affo_payout_ratio'].isna()).astype(int)
        df['has_coverage_data'] = (~df['interest_coverage'].isna()).astype(int)
        df['has_debt_ebitda_data'] = (~df['debt_to_ebitda'].isna()).astype(int)

        missing_cols = ['has_affo_data', 'has_coverage_data', 'has_debt_ebitda_data']
        print(f"✓ Created {len(missing_cols)} missing value indicators")
        return df

    def impute_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Conservative imputation for sparse metrics.

        Strategy from EDA:
        - Use median for continuous metrics (interest_coverage)
        - Flag missing Debt/EBITDA (too sparse to impute)
        """
        # Interest coverage: use median 2.75x (from EDA)
        if df['interest_coverage'].isna().any():
            median_coverage = df.loc[df['target_cut_occurred'] == 1, 'interest_coverage'].median()
            n_imputed = df['interest_coverage'].isna().sum()
            df['interest_coverage'].fillna(median_coverage, inplace=True)
            print(f"✓ Imputed {n_imputed} missing interest_coverage values with median {median_coverage:.2f}x")

        # Debt/EBITDA: too sparse (33% coverage) - leave as NaN, use missing indicator
        # Self-funding ratio: 0% coverage - leave as NaN

        return df

    def validate_features(self, df: pd.DataFrame) -> Dict[str, any]:
        """Validate engineered features and return statistics."""
        stats = {
            'total_features': len(df.columns),
            'binary_flags': len([c for c in df.columns if df[c].dtype in ['int64', 'bool'] and c not in ['target_cut_occurred']]),
            'continuous_features': len([c for c in df.columns if df[c].dtype in ['float64', 'int64'] and c not in ['target_cut_occurred']]),
            'cuts_with_dual_stress': df.loc[df['target_cut_occurred'] == 1, 'dual_stress'].sum(),
            'controls_with_dual_stress': df.loc[df['target_cut_occurred'] == 0, 'dual_stress'].sum(),
            'mean_risk_score_cuts': df.loc[df['target_cut_occurred'] == 1, 'risk_score_scaled'].mean(),
            'mean_risk_score_controls': df.loc[df['target_cut_occurred'] == 0, 'risk_score_scaled'].mean(),
        }
        return stats

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run full feature engineering pipeline."""
        print("\n" + "="*80)
        print("FEATURE ENGINEERING PIPELINE")
        print("="*80 + "\n")

        # 1. Sector features
        df = self.create_sector_features(df)

        # 2. Binary risk flags
        df = self.create_binary_flags(df)

        # 3. Interaction terms
        df = self.create_interaction_terms(df)

        # 4. Composite risk score
        df = self.create_composite_risk_score(df)

        # 5. Missing indicators
        df = self.create_missing_indicators(df)

        # 6. Impute missing values
        df = self.impute_missing_values(df)

        # 7. Validate
        stats = self.validate_features(df)

        print("\n" + "="*80)
        print("FEATURE ENGINEERING SUMMARY")
        print("="*80)
        print(f"Total features: {stats['total_features']}")
        print(f"Binary flags: {stats['binary_flags']}")
        print(f"Continuous features: {stats['continuous_features']}")
        print(f"\nDual Stress Signal (payout >95% + coverage <3.0x):")
        print(f"  Cuts: {stats['cuts_with_dual_stress']}/6 ({stats['cuts_with_dual_stress']/6*100:.0f}%)")
        print(f"  Controls: {stats['controls_with_dual_stress']}/3 ({stats['controls_with_dual_stress']/3*100:.0f}%)")
        print(f"\nComposite Risk Score (0-100):")
        print(f"  Cuts mean: {stats['mean_risk_score_cuts']:.1f}")
        print(f"  Controls mean: {stats['mean_risk_score_controls']:.1f}")
        print(f"  Separation: {stats['mean_risk_score_cuts'] - stats['mean_risk_score_controls']:.1f} points")
        print("="*80 + "\n")

        return df

    def save_dataset(self, df: pd.DataFrame, output_path: Path) -> None:
        """Save engineered dataset to CSV."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"✓ Saved engineered dataset to {output_path}")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {len(df.columns)}")


def main():
    """Command-line interface for feature engineering."""
    parser = argparse.ArgumentParser(
        description="Feature engineering for REIT distribution cut prediction"
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('data/training_dataset_v1.csv'),
        help='Input training dataset (v1)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/training_dataset_v2.csv'),
        help='Output engineered dataset (v2)'
    )

    args = parser.parse_args()

    # Initialize engineer
    engineer = DistributionCutFeatureEngineer()

    # Load data
    df = engineer.load_data(args.input)

    # Engineer features
    df_engineered = engineer.engineer_features(df)

    # Save
    engineer.save_dataset(df_engineered, args.output)

    print("\n✅ Feature engineering complete!")


if __name__ == '__main__':
    main()
