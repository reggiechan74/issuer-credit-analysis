#!/usr/bin/env python3
"""
Add economic indicators (GDP, unemployment) to training dataset.

Retrieves historical GDP growth and unemployment rate from Bank of Canada
Valet API for each observation date.

Usage:
    python scripts/add_economic_indicators.py \
      --input data/training_dataset_v2_enriched.csv \
      --output data/training_dataset_v2_with_econ.csv
"""

import argparse
import pandas as pd
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time


class EconomicIndicatorEnricher:
    """Add GDP growth and unemployment rate from Bank of Canada."""

    def __init__(self):
        """Initialize with Bank of Canada Valet API endpoint."""
        self.base_url = "https://www.bankofcanada.ca/valet/observations"

        # Series codes
        self.GDP_SERIES = "V41713474"  # Real GDP growth rate YoY
        self.UNEMPLOYMENT_SERIES = "V2062815"  # Unemployment rate

    def enrich_dataset(self, input_path: Path, output_path: Path):
        """
        Add GDP growth and unemployment rate to dataset.

        Args:
            input_path: Path to enriched dataset CSV
            output_path: Path to save dataset with economic indicators
        """
        print(f"\nLoading enriched dataset from {input_path}...")
        df = pd.read_csv(input_path)
        print(f"  Loaded {len(df)} observations")

        # Add economic indicator columns
        df['gdp_growth_yoy'] = None
        df['unemployment_rate'] = None

        print(f"\nRetrieving economic indicators from Bank of Canada...")

        # Get unique observation dates (reduce API calls)
        unique_dates = df['observation_date'].unique()
        print(f"  Unique observation dates: {len(unique_dates)}")

        # Cache for economic data
        econ_cache = {}

        for obs_date_str in unique_dates:
            obs_date = pd.to_datetime(obs_date_str)
            print(f"\n  Fetching data for {obs_date.strftime('%Y-%m')}...")

            # Get GDP growth
            gdp_data = self._get_gdp_growth(obs_date)
            if gdp_data:
                print(f"    ✓ GDP growth: {gdp_data:.1f}% YoY")
            else:
                print(f"    ✗ GDP data unavailable")

            # Get unemployment rate
            unemployment = self._get_unemployment_rate(obs_date)
            if unemployment:
                print(f"    ✓ Unemployment: {unemployment:.1f}%")
            else:
                print(f"    ✗ Unemployment data unavailable")

            econ_cache[obs_date_str] = {
                'gdp_growth_yoy': gdp_data,
                'unemployment_rate': unemployment
            }

            time.sleep(0.5)  # Rate limit

        # Apply cached data to all rows
        print(f"\n  Applying economic indicators to dataset...")
        for idx, row in df.iterrows():
            obs_date_str = row['observation_date']
            if obs_date_str in econ_cache:
                df.loc[idx, 'gdp_growth_yoy'] = econ_cache[obs_date_str]['gdp_growth_yoy']
                df.loc[idx, 'unemployment_rate'] = econ_cache[obs_date_str]['unemployment_rate']

        # Save
        print(f"\n✓ Saving dataset with economic indicators to {output_path}...")
        df.to_csv(output_path, index=False)
        print(f"  Saved {len(df)} observations with {len(df.columns)} features")

        # Summary
        self._print_summary(df)

        return df

    def _get_gdp_growth(self, obs_date: datetime) -> float:
        """
        Get Real GDP growth rate (YoY %) as of observation date.

        Args:
            obs_date: Observation date

        Returns:
            GDP growth rate YoY (%), or None if unavailable
        """
        try:
            # GDP data is quarterly, so we need to get the most recent quarter
            # Round to quarter end
            quarter_month = ((obs_date.month - 1) // 3) * 3 + 3
            if quarter_month == 3:
                quarter_end = obs_date.replace(month=3, day=31)
            elif quarter_month == 6:
                quarter_end = obs_date.replace(month=6, day=30)
            elif quarter_month == 9:
                quarter_end = obs_date.replace(month=9, day=30)
            else:
                quarter_end = obs_date.replace(month=12, day=31)

            # Get data for the quarter
            start_str = (quarter_end - timedelta(days=90)).strftime('%Y-%m-%d')
            end_str = quarter_end.strftime('%Y-%m-%d')

            url = f"{self.base_url}/{self.GDP_SERIES}/json"
            params = {
                'start_date': start_str,
                'end_date': end_str
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                return None

            data = response.json()
            observations = data.get('observations', [])

            if not observations:
                return None

            # Get most recent observation
            gdp_growth = float(observations[-1][self.GDP_SERIES]['v'])

            return round(gdp_growth, 2)

        except Exception as e:
            print(f"      ERROR fetching GDP: {str(e)[:80]}")
            return None

    def _get_unemployment_rate(self, obs_date: datetime) -> float:
        """
        Get unemployment rate (%) as of observation date.

        Args:
            obs_date: Observation date

        Returns:
            Unemployment rate (%), or None if unavailable
        """
        try:
            # Unemployment is monthly
            start_str = (obs_date - timedelta(days=60)).strftime('%Y-%m-%d')
            end_str = obs_date.strftime('%Y-%m-%d')

            url = f"{self.base_url}/{self.UNEMPLOYMENT_SERIES}/json"
            params = {
                'start_date': start_str,
                'end_date': end_str
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                return None

            data = response.json()
            observations = data.get('observations', [])

            if not observations:
                return None

            # Get most recent observation
            unemployment = float(observations[-1][self.UNEMPLOYMENT_SERIES]['v'])

            return round(unemployment, 2)

        except Exception as e:
            print(f"      ERROR fetching unemployment: {str(e)[:80]}")
            return None

    def _print_summary(self, df: pd.DataFrame):
        """Print summary statistics."""
        print("\n" + "="*60)
        print("Economic Indicators Summary")
        print("="*60)

        gdp_coverage = (~df['gdp_growth_yoy'].isna()).sum()
        unemp_coverage = (~df['unemployment_rate'].isna()).sum()
        total = len(df)

        print(f"\nCoverage:")
        print(f"  GDP growth:     {gdp_coverage}/{total} ({gdp_coverage/total*100:.1f}%)")
        print(f"  Unemployment:   {unemp_coverage}/{total} ({unemp_coverage/total*100:.1f}%)")

        if gdp_coverage > 0:
            print(f"\nGDP Growth YoY (%):")
            print(f"  Mean:   {df['gdp_growth_yoy'].mean():.2f}%")
            print(f"  Median: {df['gdp_growth_yoy'].median():.2f}%")
            print(f"  Range:  {df['gdp_growth_yoy'].min():.2f}% to {df['gdp_growth_yoy'].max():.2f}%")

        if unemp_coverage > 0:
            print(f"\nUnemployment Rate (%):")
            print(f"  Mean:   {df['unemployment_rate'].mean():.2f}%")
            print(f"  Median: {df['unemployment_rate'].median():.2f}%")
            print(f"  Range:  {df['unemployment_rate'].min():.2f}% to {df['unemployment_rate'].max():.2f}%")

        print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(
        description='Add GDP growth and unemployment rate to training dataset'
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('data/training_dataset_v2_enriched.csv'),
        help='Path to enriched dataset CSV'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/training_dataset_v2_with_econ.csv'),
        help='Path to save dataset with economic indicators'
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: Input file not found: {args.input}")
        return 1

    enricher = EconomicIndicatorEnricher()
    enricher.enrich_dataset(args.input, args.output)

    print(f"\n✓ Economic indicator enrichment complete!")
    print(f"  Output: {args.output}")

    return 0


if __name__ == '__main__':
    exit(main())
