#!/usr/bin/env python3
"""
Dividend Cut Analysis and Training Dataset Preparation

Analyzes OpenBB collected dividend data to validate historical cuts and prepare
features for distribution cut prediction model training.

Usage:
    python scripts/analyze_dividend_cuts.py --data-dir data/openbb_collections

Author: Claude Code
Version: 1.0.0
Date: 2025-10-21
"""

import argparse
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import sys

class DividendCutAnalyzer:
    """Analyzes dividend cuts and prepares training data."""

    def __init__(self, data_dir: Path):
        """
        Initialize analyzer with OpenBB data directory.

        Args:
            data_dir: Directory containing OpenBB JSON collections
        """
        self.data_dir = Path(data_dir)
        self.reits = {}
        self.cuts_database = []

    def load_all_reits(self) -> int:
        """
        Load all REIT dividend data from JSON files.

        Returns:
            Number of REITs loaded
        """
        json_files = list(self.data_dir.glob('*.json'))

        for json_file in json_files:
            with open(json_file) as f:
                data = json.load(f)
                ticker = data['ticker']
                self.reits[ticker] = data

        print(f"✓ Loaded {len(self.reits)} REITs from {self.data_dir}")
        return len(self.reits)

    def validate_historical_cuts(self) -> pd.DataFrame:
        """
        Validate detected cuts against historical research.

        Returns:
            DataFrame with cut validation results
        """
        # Historical cuts from research (Agent 2)
        historical_cuts = {
            'HR-UN.TO': [
                {'date': '2020-05', 'magnitude': 50.0, 'from': 1.38, 'to': 0.69}
            ],
            'SOT-UN.TO': [
                {'date': '2023-11', 'magnitude': 100.0, 'from': 0.40, 'to': 0.00}
            ],
            'REI-UN.TO': [
                {'date': '2020-12', 'magnitude': 33.0, 'from': 1.44, 'to': 0.96}
            ],
            'TNT-UN.TO': [
                {'date': '2023-03', 'magnitude': 50.0, 'from': 0.59, 'to': 0.30},
                {'date': '2023-11', 'magnitude': 100.0, 'from': 0.30, 'to': 0.00}
            ],
            'AX-UN.TO': [
                {'date': '2018-11', 'magnitude': 50.0, 'from': 1.08, 'to': 0.54}
            ]
        }

        validation_results = []

        for ticker, expected_cuts in historical_cuts.items():
            if ticker not in self.reits:
                print(f"⚠️  {ticker} not found in collected data")
                continue

            detected_cuts = self.reits[ticker].get('detected_cuts', [])

            for expected in expected_cuts:
                # Find matching detected cut (within same month)
                matched = False
                for detected in detected_cuts:
                    if detected['cut_date'].startswith(expected['date'][:7]):  # YYYY-MM match
                        matched = True
                        magnitude_match = abs(detected['cut_percentage'] - expected['magnitude']) < 5.0

                        validation_results.append({
                            'ticker': ticker,
                            'cut_date': expected['date'],
                            'expected_magnitude': expected['magnitude'],
                            'detected_magnitude': detected['cut_percentage'],
                            'magnitude_match': magnitude_match,
                            'status': '✓ Matched' if magnitude_match else '⚠️ Magnitude mismatch'
                        })
                        break

                if not matched:
                    validation_results.append({
                        'ticker': ticker,
                        'cut_date': expected['date'],
                        'expected_magnitude': expected['magnitude'],
                        'detected_magnitude': None,
                        'magnitude_match': False,
                        'status': '✗ Not detected'
                    })

        return pd.DataFrame(validation_results)

    def extract_cut_features(self, ticker: str, cut_date: str) -> Dict:
        """
        Extract features for a specific cut event.

        Args:
            ticker: REIT ticker
            cut_date: Cut date (YYYY-MM format)

        Returns:
            Dictionary of features for model training
        """
        if ticker not in self.reits:
            return {}

        data = self.reits[ticker]
        dividend_history = pd.DataFrame(data['dividend_history']['records'])
        dividend_history['ex_dividend_date'] = pd.to_datetime(dividend_history['ex_dividend_date'])

        # Get 6-12 months before cut for pre-cut metrics
        cut_datetime = pd.to_datetime(cut_date + '-01')
        six_months_before = cut_datetime - pd.DateOffset(months=6)
        twelve_months_before = cut_datetime - pd.DateOffset(months=12)

        # Filter dividends in pre-cut window
        pre_cut_divs = dividend_history[
            (dividend_history['ex_dividend_date'] >= twelve_months_before) &
            (dividend_history['ex_dividend_date'] < cut_datetime)
        ]

        if pre_cut_divs.empty:
            return {}

        # Calculate pre-cut annual distribution (TTM)
        ttm_distribution = pre_cut_divs['amount'].sum()
        avg_monthly_distribution = pre_cut_divs['amount'].mean()

        # Get current metrics at time of collection
        current_metrics = data.get('current_metrics', {})

        # Extract sector from ticker mapping (would need to be loaded)
        # For now, infer from ticker
        sector = self._infer_sector(ticker)

        features = {
            'ticker': ticker,
            'cut_date': cut_date,
            'sector': sector,
            'ttm_distribution_pre_cut': round(ttm_distribution, 4),
            'avg_monthly_distribution': round(avg_monthly_distribution, 4),
            'dividend_payment_count_ttm': len(pre_cut_divs),
            'current_price': current_metrics.get('current_price'),
            'current_yield': current_metrics.get('dividend_yield_ttm'),
            # Placeholders for Phase 3 metrics (to be filled from financial statements)
            'affo_payout_ratio': None,  # Need Phase 2/3 data
            'interest_coverage': None,
            'debt_to_ebitda': None,
            'self_funding_ratio': None,
            'cash_runway_months': None,
            'debt_to_assets': None,
            'liquidity_risk_score': None
        }

        return features

    def _infer_sector(self, ticker: str) -> str:
        """Infer REIT sector from ticker (simple mapping)."""
        sector_map = {
            'HR-UN.TO': 'Retail/Office',
            'SOT-UN.TO': 'Office',
            'REI-UN.TO': 'Retail',
            'TNT-UN.TO': 'Office',
            'AX-UN.TO': 'Office',
            'CAR-UN.TO': 'Residential',
            'SRU-UN.TO': 'Retail',
            'DIR-UN.TO': 'Industrial'
        }
        return sector_map.get(ticker, 'Unknown')

    def compare_cut_vs_nocut_yields(self) -> pd.DataFrame:
        """
        Compare dividend yields between REITs that cut vs those that didn't.

        Returns:
            Comparison DataFrame
        """
        cut_reits = ['HR-UN.TO', 'SOT-UN.TO', 'REI-UN.TO', 'TNT-UN.TO', 'AX-UN.TO']
        nocut_reits = ['CAR-UN.TO', 'SRU-UN.TO', 'DIR-UN.TO']

        comparison = []

        for ticker in self.reits:
            current_metrics = self.reits[ticker].get('current_metrics', {})
            cut_count = self.reits[ticker].get('cut_count', 0)

            comparison.append({
                'ticker': ticker,
                'reit_name': self.reits[ticker]['reit_name'],
                'current_price': current_metrics.get('current_price'),
                'annual_dividend': current_metrics.get('annual_dividend_ttm'),
                'dividend_yield': current_metrics.get('dividend_yield_ttm'),
                'cut_count': cut_count,
                'category': 'Cut' if ticker in cut_reits else 'No Cut',
                'sector': self._infer_sector(ticker)
            })

        return pd.DataFrame(comparison).sort_values('dividend_yield', ascending=False)

    def generate_summary_report(self) -> str:
        """
        Generate comprehensive summary report of collected data.

        Returns:
            Formatted summary report
        """
        report = []
        report.append("=" * 80)
        report.append("DIVIDEND CUT ANALYSIS - SUMMARY REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"REITs Analyzed: {len(self.reits)}")
        report.append("")

        # Summary statistics
        total_records = sum(r['dividend_history']['total_records'] for r in self.reits.values())
        total_cuts = sum(r['cut_count'] for r in self.reits.values())

        report.append("COLLECTION STATISTICS:")
        report.append(f"  Total Dividend Records: {total_records:,}")
        report.append(f"  Total Cuts Detected: {total_cuts}")
        report.append("")

        # Individual REIT summaries
        report.append("REIT-BY-REIT SUMMARY:")
        report.append("")

        for ticker in sorted(self.reits.keys()):
            data = self.reits[ticker]
            current_metrics = data.get('current_metrics', {})

            report.append(f"{ticker} ({data['reit_name']})")
            report.append(f"  Sector: {self._infer_sector(ticker)}")
            report.append(f"  Records: {data['dividend_history']['total_records']}")
            report.append(f"  Date Range: {data['dividend_history']['date_range']['earliest']} to {data['dividend_history']['date_range']['latest']}")
            report.append(f"  Current Price: ${current_metrics.get('current_price', 0):.2f}")
            report.append(f"  Annual Dividend (TTM): ${current_metrics.get('annual_dividend_ttm', 0):.4f}")
            report.append(f"  Dividend Yield: {current_metrics.get('dividend_yield_ttm', 0):.2f}%")
            report.append(f"  Detected Cuts: {data['cut_count']}")

            if data['cut_count'] > 0:
                report.append(f"  Cut Details:")
                for cut in data['detected_cuts']:
                    report.append(f"    - {cut['cut_date']}: ${cut['previous_monthly']:.4f} → ${cut['new_monthly']:.4f} ({cut['cut_percentage']:.1f}% reduction)")

            report.append("")

        # Cut vs No Cut comparison
        comparison_df = self.compare_cut_vs_nocut_yields()

        report.append("CUT vs NO CUT COMPARISON:")
        report.append("")

        cut_yields = comparison_df[comparison_df['category'] == 'Cut']['dividend_yield']
        nocut_yields = comparison_df[comparison_df['category'] == 'No Cut']['dividend_yield']

        if not cut_yields.empty and not nocut_yields.empty:
            report.append(f"  Average Yield (Cut REITs): {cut_yields.mean():.2f}%")
            report.append(f"  Average Yield (No Cut REITs): {nocut_yields.mean():.2f}%")
            report.append(f"  Yield Spread: {cut_yields.mean() - nocut_yields.mean():+.2f}%")
            report.append("")

        report.append("=" * 80)

        return "\n".join(report)

    def export_training_dataset_skeleton(self, output_path: Path) -> None:
        """
        Export skeleton training dataset with OpenBB features.
        Financial metrics (Phase 2/3) need to be added separately.

        Args:
            output_path: Path to output CSV file
        """
        training_data = []

        # Extract features for documented cuts
        documented_cuts = {
            'HR-UN.TO': ['2020-05'],
            'SOT-UN.TO': ['2023-11'],
            'REI-UN.TO': ['2020-12'],
            'TNT-UN.TO': ['2023-03', '2023-11'],
            'AX-UN.TO': ['2018-11']
        }

        for ticker, cut_dates in documented_cuts.items():
            for cut_date in cut_dates:
                features = self.extract_cut_features(ticker, cut_date)
                if features:
                    features['target_cut_occurred'] = 1
                    training_data.append(features)

        # Add no-cut control group observations
        nocut_reits = ['CAR-UN.TO', 'SRU-UN.TO', 'DIR-UN.TO']
        for ticker in nocut_reits:
            # Use current date as "observation date" for no-cut cases
            features = self.extract_cut_features(ticker, '2025-10')
            if features:
                features['target_cut_occurred'] = 0
                training_data.append(features)

        df = pd.DataFrame(training_data)

        # Reorder columns for readability
        cols_order = [
            'ticker', 'cut_date', 'sector', 'target_cut_occurred',
            'ttm_distribution_pre_cut', 'avg_monthly_distribution', 'dividend_payment_count_ttm',
            'current_price', 'current_yield',
            'affo_payout_ratio', 'interest_coverage', 'debt_to_ebitda',
            'self_funding_ratio', 'cash_runway_months', 'debt_to_assets', 'liquidity_risk_score'
        ]

        df = df[[col for col in cols_order if col in df.columns]]

        df.to_csv(output_path, index=False)
        print(f"✓ Exported training dataset skeleton to {output_path}")
        print(f"  Rows: {len(df)} ({(df['target_cut_occurred']==1).sum()} cuts, {(df['target_cut_occurred']==0).sum()} no-cut)")
        print(f"  Columns: {len(df.columns)}")
        print(f"\n⚠️  Financial metrics (affo_payout_ratio, etc.) need to be filled from Phase 2/3 data")


def main():
    """Command-line interface for dividend cut analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze collected dividend data and prepare training dataset"
    )
    parser.add_argument(
        '--data-dir',
        type=Path,
        default=Path('data/openbb_collections'),
        help='Directory containing OpenBB JSON files'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/training_dataset_skeleton.csv'),
        help='Output path for training dataset CSV'
    )
    parser.add_argument(
        '--validate-cuts',
        action='store_true',
        help='Validate detected cuts against historical research'
    )
    parser.add_argument(
        '--export-report',
        type=Path,
        help='Export summary report to file'
    )

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = DividendCutAnalyzer(args.data_dir)

    # Load all REITs
    count = analyzer.load_all_reits()
    if count == 0:
        print(f"ERROR: No REIT data found in {args.data_dir}")
        sys.exit(1)

    print("")

    # Validate historical cuts
    if args.validate_cuts:
        print("VALIDATING HISTORICAL CUTS:")
        print("-" * 80)
        validation_df = analyzer.validate_historical_cuts()
        print(validation_df.to_string(index=False))
        print("")

    # Generate summary report
    print("GENERATING SUMMARY REPORT:")
    print("")
    report = analyzer.generate_summary_report()
    print(report)

    if args.export_report:
        args.export_report.parent.mkdir(parents=True, exist_ok=True)
        with open(args.export_report, 'w') as f:
            f.write(report)
        print(f"\n✓ Summary report exported to {args.export_report}")

    # Export training dataset skeleton
    print("\nEXPORTING TRAINING DATASET:")
    print("-" * 80)
    analyzer.export_training_dataset_skeleton(args.output)


if __name__ == '__main__':
    main()
