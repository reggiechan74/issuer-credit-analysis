#!/usr/bin/env python3
"""
Enrich training dataset with market risk and macro features.

For each distribution cut observation, retrieves:
1. Market risk metrics (price stress, volatility, momentum) as of observation date
2. Macro environment (policy rate, credit stress) as of observation date

Usage:
    python scripts/enrich_training_dataset.py \
      --input data/training_dataset_v2_base.csv \
      --output data/training_dataset_v2_enriched.csv \
      --lookback-months 3
"""

import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys
import json
from typing import Dict, Optional
import requests
import time

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from openbb import obb
    OPENBB_AVAILABLE = True
except ImportError:
    print("WARNING: OpenBB not available. Install with: pip install openbb")
    OPENBB_AVAILABLE = False


class TrainingDatasetEnricher:
    """Enrich training dataset with historical market and macro features."""

    def __init__(self, lookback_months: int = 3):
        """
        Initialize enricher.

        Args:
            lookback_months: Months before cut to observe features (default: 3)
                           This creates a lead time for early warning
        """
        self.lookback_months = lookback_months

    def enrich_dataset(self, input_path: Path, output_path: Path):
        """
        Enrich dataset with market and macro features.

        Args:
            input_path: Path to base dataset CSV
            output_path: Path to save enriched dataset
        """
        print(f"\nLoading base dataset from {input_path}...")
        df = pd.read_csv(input_path)
        print(f"  Loaded {len(df)} distribution cut observations")

        # Add observation date column (cut_date - lookback_months)
        df['observation_date'] = pd.to_datetime(df['cut_date']).apply(
            lambda x: x - timedelta(days=self.lookback_months * 30)
        )

        print(f"\nEnriching with market risk and macro features...")
        print(f"  Observation window: {self.lookback_months} months before cut")
        print(f"  (Testing early warning hypothesis)\n")

        # Initialize feature columns
        market_features = [
            'market_price_stress_pct', 'market_risk_score', 'market_volatility_90d',
            'market_momentum_3m', 'market_risk_level'
        ]
        macro_features = [
            'macro_policy_rate', 'macro_rate_change_12m', 'macro_rate_cycle',
            'macro_credit_stress_score', 'macro_credit_environment'
        ]

        for col in market_features + macro_features:
            df[col] = None

        # Enrich each observation
        for idx, row in df.iterrows():
            ticker = row['ticker']
            obs_date = row['observation_date']
            cut_date = pd.to_datetime(row['cut_date'])

            print(f"[{idx+1}/{len(df)}] {row['reit_name']}: Cut {cut_date.strftime('%Y-%m')} "
                  f"→ Observe {obs_date.strftime('%Y-%m')} ({self.lookback_months}mo prior)")

            # Get market risk features
            market_data = self._get_historical_market_risk(ticker, obs_date)
            if market_data:
                df.loc[idx, 'market_price_stress_pct'] = market_data.get('price_stress_pct')
                df.loc[idx, 'market_risk_score'] = market_data.get('risk_score')
                df.loc[idx, 'market_volatility_90d'] = market_data.get('volatility_90d')
                df.loc[idx, 'market_momentum_3m'] = market_data.get('momentum_3m')
                df.loc[idx, 'market_risk_level'] = market_data.get('risk_level')
                print(f"  ✓ Market: Risk {market_data.get('risk_score')}/100, "
                      f"Stress {market_data.get('price_stress_pct'):.1f}%")
            else:
                print(f"  ✗ Market data unavailable")

            # Get macro features
            macro_data = self._get_historical_macro(obs_date)
            if macro_data:
                df.loc[idx, 'macro_policy_rate'] = macro_data.get('policy_rate')
                df.loc[idx, 'macro_rate_change_12m'] = macro_data.get('rate_change_12m')
                df.loc[idx, 'macro_rate_cycle'] = macro_data.get('rate_cycle')
                df.loc[idx, 'macro_credit_stress_score'] = macro_data.get('credit_stress_score')
                df.loc[idx, 'macro_credit_environment'] = macro_data.get('credit_environment')
                print(f"  ✓ Macro: Rate {macro_data.get('policy_rate')}%, "
                      f"Cycle {macro_data.get('rate_cycle')}, Stress {macro_data.get('credit_stress_score')}/100")
            else:
                print(f"  ✗ Macro data unavailable")

            # Rate limit to avoid overwhelming APIs
            time.sleep(1)

        # Save enriched dataset
        print(f"\n✓ Saving enriched dataset to {output_path}...")
        df.to_csv(output_path, index=False)
        print(f"  Saved {len(df)} observations with {len(df.columns)} features")

        # Summary statistics
        self._print_enrichment_summary(df, market_features, macro_features)

        return df

    def _get_historical_market_risk(self, ticker: str, obs_date: datetime) -> Optional[Dict]:
        """
        Calculate market risk metrics as of observation date.

        Args:
            ticker: REIT ticker
            obs_date: Observation date (e.g., 3 months before cut)

        Returns:
            Dictionary with market risk metrics, or None if unavailable
        """
        if not OPENBB_AVAILABLE:
            return None

        try:
            # Get price history: from obs_date - 12 months to obs_date
            start_date = obs_date - timedelta(days=365)
            end_str = obs_date.strftime('%Y-%m-%d')
            start_str = start_date.strftime('%Y-%m-%d')

            # Fetch historical prices
            result = obb.equity.price.historical(
                symbol=ticker,
                start_date=start_str,
                end_date=end_str,
                provider='tmx'
            )

            if not result or not result.results:
                return None

            df = result.to_df()

            if len(df) < 90:  # Need at least 90 days for volatility calc
                return None

            # Calculate metrics as of obs_date
            current_price = df['close'].iloc[-1]
            high_52w = df['close'].max()

            # Price stress
            price_stress_pct = ((high_52w - current_price) / high_52w) * 100

            # Volatility (90-day)
            returns = df['close'].pct_change().dropna()
            volatility_90d = returns.tail(90).std() * np.sqrt(252) * 100

            # Momentum (3-month)
            if len(df) >= 63:
                price_3m_ago = df['close'].iloc[-63]
                momentum_3m = ((current_price - price_3m_ago) / price_3m_ago) * 100
            else:
                momentum_3m = None

            # Risk score (0-100 composite)
            stress_points = min(price_stress_pct * 1.33, 40)  # 40% max
            vol_points = min(volatility_90d * 0.75, 30)        # 30% max
            momentum_points = max(0, -momentum_3m * 0.6) if momentum_3m else 15  # 30% max
            risk_score = int(stress_points + vol_points + momentum_points)

            # Risk level
            if risk_score >= 70:
                risk_level = "VERY HIGH"
            elif risk_score >= 50:
                risk_level = "HIGH"
            elif risk_score >= 30:
                risk_level = "MODERATE"
            elif risk_score >= 15:
                risk_level = "LOW"
            else:
                risk_level = "VERY LOW"

            return {
                'price_stress_pct': round(price_stress_pct, 1),
                'risk_score': risk_score,
                'volatility_90d': round(volatility_90d, 1),
                'momentum_3m': round(momentum_3m, 1) if momentum_3m else None,
                'risk_level': risk_level
            }

        except Exception as e:
            print(f"    ERROR: {str(e)[:100]}")
            return None

    def _get_historical_macro(self, obs_date: datetime) -> Optional[Dict]:
        """
        Get macro environment as of observation date.

        Args:
            obs_date: Observation date

        Returns:
            Dictionary with macro metrics, or None if unavailable
        """
        try:
            # Get Bank of Canada policy rate
            end_str = obs_date.strftime('%Y-%m-%d')
            start_12m = (obs_date - timedelta(days=365)).strftime('%Y-%m-%d')

            url = f"https://www.bankofcanada.ca/valet/observations/V122530/json"
            params = {
                'start_date': start_12m,
                'end_date': end_str
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                return None

            data = response.json()
            observations = data.get('observations', [])

            if len(observations) < 2:
                return None

            # Get rate as of obs_date (most recent)
            current_rate = float(observations[-1]['V122530']['v'])

            # Get rate 12 months prior
            rate_12m_ago = float(observations[0]['V122530']['v'])

            # Calculate rate change
            rate_change_12m = current_rate - rate_12m_ago

            # Classify rate cycle
            if abs(rate_change_12m) < 0.25:
                rate_cycle = "STABLE"
            elif rate_change_12m >= 2.0:
                rate_cycle = "AGGRESSIVE TIGHTENING"
            elif rate_change_12m >= 1.0:
                rate_cycle = "TIGHTENING"
            elif rate_change_12m >= 0.25:
                rate_cycle = "MILD TIGHTENING"
            elif rate_change_12m <= -2.0:
                rate_cycle = "AGGRESSIVE EASING"
            elif rate_change_12m <= -1.0:
                rate_cycle = "EASING"
            else:
                rate_cycle = "MILD EASING"

            # Credit stress score (0-100)
            # Higher rates + tightening = higher stress
            rate_stress = min(current_rate * 8, 40)  # 5% rate = 40 points
            cycle_stress = max(0, rate_change_12m * 15) if rate_change_12m > 0 else 0  # Tightening adds stress
            credit_stress_score = int(rate_stress + cycle_stress)

            # Credit environment
            if credit_stress_score >= 70:
                credit_environment = "RESTRICTIVE"
            elif credit_stress_score >= 50:
                credit_environment = "TIGHTENING"
            elif credit_stress_score >= 30:
                credit_environment = "NEUTRAL"
            else:
                credit_environment = "ACCOMMODATIVE"

            return {
                'policy_rate': current_rate,
                'rate_change_12m': round(rate_change_12m, 2),
                'rate_cycle': rate_cycle,
                'credit_stress_score': credit_stress_score,
                'credit_environment': credit_environment
            }

        except Exception as e:
            print(f"    ERROR: {str(e)[:100]}")
            return None

    def _print_enrichment_summary(self, df: pd.DataFrame,
                                  market_features: list,
                                  macro_features: list):
        """Print summary statistics of enrichment."""
        print("\n" + "="*60)
        print("Enrichment Summary")
        print("="*60)

        # Overall stats
        total_obs = len(df)

        # Market feature coverage
        market_coverage = (~df[market_features[0]].isna()).sum()
        market_pct = (market_coverage / total_obs) * 100

        # Macro feature coverage
        macro_coverage = (~df[macro_features[0]].isna()).sum()
        macro_pct = (macro_coverage / total_obs) * 100

        print(f"\nTotal observations:     {total_obs}")
        print(f"Market data coverage:   {market_coverage}/{total_obs} ({market_pct:.1f}%)")
        print(f"Macro data coverage:    {macro_coverage}/{total_obs} ({macro_pct:.1f}%)")

        # Market risk distribution
        if market_coverage > 0:
            print(f"\nMarket Risk Distribution (n={market_coverage}):")
            risk_counts = df['market_risk_level'].value_counts()
            for level in ['VERY HIGH', 'HIGH', 'MODERATE', 'LOW', 'VERY LOW']:
                count = risk_counts.get(level, 0)
                if count > 0:
                    print(f"  {level:12s}: {count:2d} ({count/market_coverage*100:.1f}%)")

        # Macro cycle distribution
        if macro_coverage > 0:
            print(f"\nRate Cycle Distribution (n={macro_coverage}):")
            cycle_counts = df['macro_rate_cycle'].value_counts()
            for cycle in cycle_counts.index:
                count = cycle_counts[cycle]
                print(f"  {cycle:22s}: {count:2d} ({count/macro_coverage*100:.1f}%)")

        # Summary stats
        if market_coverage > 0:
            print(f"\nMarket Risk Metrics (n={market_coverage}):")
            print(f"  Price Stress:  {df['market_price_stress_pct'].mean():.1f}% "
                  f"(range: {df['market_price_stress_pct'].min():.1f}% - "
                  f"{df['market_price_stress_pct'].max():.1f}%)")
            print(f"  Risk Score:    {df['market_risk_score'].mean():.1f}/100 "
                  f"(range: {df['market_risk_score'].min():.0f} - "
                  f"{df['market_risk_score'].max():.0f})")
            print(f"  Volatility:    {df['market_volatility_90d'].mean():.1f}% "
                  f"(range: {df['market_volatility_90d'].min():.1f}% - "
                  f"{df['market_volatility_90d'].max():.1f}%)")

        if macro_coverage > 0:
            print(f"\nMacro Environment (n={macro_coverage}):")
            print(f"  Policy Rate:   {df['macro_policy_rate'].mean():.2f}% "
                  f"(range: {df['macro_policy_rate'].min():.2f}% - "
                  f"{df['macro_policy_rate'].max():.2f}%)")
            print(f"  Rate Change:   {df['macro_rate_change_12m'].mean():.2f} bps/year "
                  f"(range: {df['macro_rate_change_12m'].min():.2f} - "
                  f"{df['macro_rate_change_12m'].max():.2f})")
            print(f"  Credit Stress: {df['macro_credit_stress_score'].mean():.1f}/100 "
                  f"(range: {df['macro_credit_stress_score'].min():.0f} - "
                  f"{df['macro_credit_stress_score'].max():.0f})")

        print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(
        description='Enrich training dataset with market risk and macro features'
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('data/training_dataset_v2_base.csv'),
        help='Path to base dataset CSV'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/training_dataset_v2_enriched.csv'),
        help='Path to save enriched dataset'
    )
    parser.add_argument(
        '--lookback-months',
        type=int,
        default=3,
        help='Months before cut to observe features (default: 3 for early warning)'
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.input.exists():
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)

    if not OPENBB_AVAILABLE:
        print("ERROR: OpenBB Platform not available. Install with: pip install openbb")
        sys.exit(1)

    # Run enrichment
    enricher = TrainingDatasetEnricher(lookback_months=args.lookback_months)
    enricher.enrich_dataset(args.input, args.output)

    print(f"\n✓ Dataset enrichment complete!")
    print(f"  Input:  {args.input}")
    print(f"  Output: {args.output}")
    print(f"  Lookback: {args.lookback_months} months (early warning window)")


if __name__ == '__main__':
    main()
