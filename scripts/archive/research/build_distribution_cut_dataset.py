#!/usr/bin/env python3
"""
Automated Distribution Cut Dataset Builder

Scans 20-30 Canadian REITs for historical distribution cuts to build
training dataset for distribution cut prediction model (Issue #38 v2.0).

Usage:
    python scripts/build_distribution_cut_dataset.py --config config/canadian_reits.yaml --output data/training_dataset_v2.csv

Features:
    - Automatic cut detection (>10% decline threshold)
    - Recovery pattern analysis
    - Cut magnitude, timing, and recovery metrics
    - CSV export for model training
    - Progress tracking and error handling

Author: Claude Code
Version: 1.0.0
Date: 2025-10-22
"""

import argparse
import csv
import json
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from openbb_data_collector import OpenBBDataCollector
    import pandas as pd
except ImportError as e:
    print(f"ERROR: Missing required package: {e}")
    print("Install with: pip install openbb openbb-tmx pandas pyyaml")
    sys.exit(1)


class DistributionCutDatasetBuilder:
    """
    Builds training dataset for distribution cut prediction by scanning
    multiple Canadian REITs for historical cuts and recovery patterns.
    """

    def __init__(self, reit_config: Dict, provider: str = "tmx"):
        """
        Initialize dataset builder with REIT configuration.

        Args:
            reit_config: Dict of REIT configurations (name → ticker mapping)
            provider: Data provider ('tmx' or 'yfinance')
        """
        self.reit_config = reit_config
        self.provider = provider
        self.results = []
        self.errors = []

    def scan_reit(self, reit_name: str, ticker: str) -> Optional[Dict]:
        """
        Scan a single REIT for distribution cuts and recovery patterns.

        Args:
            reit_name: REIT name (e.g., "RioCan REIT")
            ticker: REIT ticker (e.g., "REI-UN.TO")

        Returns:
            Dict with cut analysis or None if error
        """
        try:
            print(f"Scanning {reit_name} ({ticker})...")
            collector = OpenBBDataCollector(ticker, self.provider)

            # Get dividend history
            div_df = collector.get_dividend_history()
            if div_df.empty:
                self.errors.append({'reit': reit_name, 'error': 'No dividend data'})
                return None

            # Get current price
            price = collector.get_current_price()

            # Detect cuts
            cuts = collector.detect_dividend_cuts(div_df)

            # Analyze recovery
            recovery = collector.analyze_recovery(div_df, cuts)

            # Calculate TTM metrics
            ttm = collector.calculate_ttm_metrics(div_df, price) if price else {}

            result = {
                'reit_name': reit_name,
                'ticker': ticker,
                'scan_date': datetime.now().strftime('%Y-%m-%d'),
                'total_records': len(div_df),
                'date_range_start': div_df['ex_dividend_date'].min().strftime('%Y-%m-%d') if not div_df.empty else None,
                'date_range_end': div_df['ex_dividend_date'].max().strftime('%Y-%m-%d') if not div_df.empty else None,
                'cut_count': len(cuts),
                'cuts': cuts,
                'recovery_analysis': recovery,
                'current_metrics': ttm
            }

            print(f"  ✓ Found {len(cuts)} cuts, {len(recovery)} recovery patterns")
            return result

        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            self.errors.append({'reit': reit_name, 'ticker': ticker, 'error': str(e)})
            return None

    def scan_all_reits(self) -> List[Dict]:
        """
        Scan all REITs from configuration file.

        Returns:
            List of scan results for REITs with cuts detected
        """
        print(f"Starting scan of {len(self.reit_config)} REITs...")
        print(f"{'='*60}\n")

        for reit_name, ticker in self.reit_config.items():
            result = self.scan_reit(reit_name, ticker)
            if result:
                self.results.append(result)

        print(f"\n{'='*60}")
        print(f"Scan Complete:")
        print(f"  REITs scanned:     {len(self.reit_config)}")
        print(f"  REITs with data:   {len(self.results)}")
        print(f"  Errors:            {len(self.errors)}")
        print(f"{'='*60}\n")

        return self.results

    def export_to_csv(self, output_path: Path) -> None:
        """
        Export dataset to CSV for model training.

        Each row represents a detected distribution cut with:
        - REIT identification (name, ticker)
        - Cut details (date, magnitude, pre/post amounts)
        - Recovery metrics (recovery level, months to recover, status)
        - Current metrics (price, yield, distribution)

        Args:
            output_path: Path to output CSV file
        """
        if not self.results:
            print("ERROR: No data to export")
            return

        # Flatten results into CSV rows
        csv_rows = []
        for result in self.results:
            reit_name = result['reit_name']
            ticker = result['ticker']
            current = result.get('current_metrics', {})

            # Create a row for each cut
            for i, cut in enumerate(result['cuts']):
                # Find corresponding recovery analysis
                recovery = result['recovery_analysis'][i] if i < len(result['recovery_analysis']) else {}

                row = {
                    # REIT identification
                    'reit_name': reit_name,
                    'ticker': ticker,
                    'scan_date': result['scan_date'],

                    # Cut details
                    'cut_date': cut['cut_date'],
                    'cut_magnitude_pct': cut['cut_percentage'],
                    'pre_cut_monthly': cut['previous_monthly'],
                    'post_cut_monthly': cut['new_monthly'],
                    'pre_cut_annual': cut['previous_annual'],
                    'post_cut_annual': cut['new_annual'],

                    # Recovery metrics
                    'recovery_level_pct': recovery.get('recovery_level_pct', 0),
                    'recovery_months': recovery.get('recovery_months'),
                    'full_recovery': recovery.get('full_recovery', False),
                    'recovery_status': recovery.get('recovery_status', 'Unknown'),
                    'current_monthly': recovery.get('current_monthly'),

                    # Current market metrics
                    'current_price': current.get('current_price'),
                    'current_yield': current.get('dividend_yield_ttm'),
                    'current_annual_dividend': current.get('annual_dividend_ttm'),

                    # Data quality
                    'total_records': result['total_records'],
                    'data_range_start': result['date_range_start'],
                    'data_range_end': result['date_range_end']
                }

                csv_rows.append(row)

        # Write to CSV
        if csv_rows:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', newline='') as f:
                fieldnames = csv_rows[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_rows)

            print(f"✓ Exported {len(csv_rows)} distribution cuts to {output_path}")
            print(f"  REITs with cuts: {len(self.results)}")
            print(f"  Total cuts detected: {len(csv_rows)}")
        else:
            print("ERROR: No cuts detected in any REIT")

    def export_summary_report(self, output_path: Path) -> None:
        """
        Export summary report with statistics and quality assessment.

        Args:
            output_path: Path to output text report
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            f.write("Distribution Cut Dataset - Summary Report\n")
            f.write(f"{'='*60}\n\n")
            f.write(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Data Provider: {self.provider}\n\n")

            # Overall statistics
            total_cuts = sum(r['cut_count'] for r in self.results)
            reits_with_cuts = sum(1 for r in self.results if r['cut_count'] > 0)

            f.write("Overall Statistics:\n")
            f.write(f"  REITs scanned:           {len(self.reit_config)}\n")
            f.write(f"  REITs with data:         {len(self.results)}\n")
            f.write(f"  REITs with cuts:         {reits_with_cuts}\n")
            f.write(f"  Total cuts detected:     {total_cuts}\n")
            f.write(f"  Errors encountered:      {len(self.errors)}\n\n")

            # Recovery statistics
            total_recovery_analyzed = sum(len(r['recovery_analysis']) for r in self.results)
            fully_recovered = sum(
                sum(1 for rec in r['recovery_analysis'] if rec.get('full_recovery', False))
                for r in self.results
            )

            f.write("Recovery Statistics:\n")
            f.write(f"  Cuts with recovery data: {total_recovery_analyzed}\n")
            f.write(f"  Fully recovered cuts:    {fully_recovered}\n")
            f.write(f"  Partial recovery:        {total_recovery_analyzed - fully_recovered}\n")
            if total_recovery_analyzed > 0:
                recovery_rate = (fully_recovered / total_recovery_analyzed) * 100
                f.write(f"  Recovery rate:           {recovery_rate:.1f}%\n")
            f.write("\n")

            # Per-REIT summary
            f.write("Per-REIT Summary:\n")
            f.write(f"{'REIT':<30} {'Cuts':>5} {'Recovered':>10} {'Status':<20}\n")
            f.write(f"{'-'*70}\n")

            for result in self.results:
                if result['cut_count'] > 0:
                    recovered = sum(1 for r in result['recovery_analysis'] if r.get('full_recovery', False))
                    latest_recovery = result['recovery_analysis'][-1] if result['recovery_analysis'] else {}
                    status = latest_recovery.get('recovery_status', 'N/A')

                    f.write(f"{result['reit_name']:<30} {result['cut_count']:>5} {recovered:>10} {status:<20}\n")

            f.write("\n")

            # Errors
            if self.errors:
                f.write("Errors Encountered:\n")
                for error in self.errors:
                    f.write(f"  {error['reit']}: {error['error']}\n")

        print(f"✓ Exported summary report to {output_path}")


def load_reit_config(config_path: Path) -> Dict[str, str]:
    """
    Load REIT configuration from YAML file.

    Expected format:
        reits:
          RioCan REIT: REI-UN.TO
          Dream Industrial REIT: DIR-UN.TO
          Artis REIT: AX-UN.TO
          ...

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Dict mapping REIT names to tickers
    """
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    if 'reits' not in config:
        print("ERROR: Config file must contain 'reits' section")
        sys.exit(1)

    return config['reits']


def main():
    """Command-line interface for dataset builder."""
    parser = argparse.ArgumentParser(
        description="Build training dataset for distribution cut prediction model"
    )
    parser.add_argument(
        '--config',
        type=Path,
        required=True,
        help='Path to YAML config file with REIT ticker mappings'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/distribution_cut_dataset.csv'),
        help='Output CSV file path (default: data/distribution_cut_dataset.csv)'
    )
    parser.add_argument(
        '--summary',
        type=Path,
        help='Output path for summary report (optional)'
    )
    parser.add_argument(
        '--provider',
        default='tmx',
        choices=['tmx', 'yfinance'],
        help='Data provider (default: tmx)'
    )
    parser.add_argument(
        '--export-json',
        action='store_true',
        help='Also export full results to JSON'
    )

    args = parser.parse_args()

    # Load REIT configuration
    reit_config = load_reit_config(args.config)
    print(f"Loaded {len(reit_config)} REITs from {args.config}\n")

    # Build dataset
    builder = DistributionCutDatasetBuilder(reit_config, args.provider)
    results = builder.scan_all_reits()

    # Export to CSV
    builder.export_to_csv(args.output)

    # Export summary report
    if args.summary:
        builder.export_summary_report(args.summary)
    else:
        summary_path = args.output.parent / f"{args.output.stem}_summary.txt"
        builder.export_summary_report(summary_path)

    # Export JSON (optional)
    if args.export_json:
        json_output = args.output.parent / f"{args.output.stem}.json"
        with open(json_output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"✓ Exported full results to {json_output}")

    # Final summary
    total_cuts = sum(r['cut_count'] for r in results)
    print(f"\n{'='*60}")
    print("Dataset Build Complete")
    print(f"{'='*60}")
    print(f"REITs processed:     {len(results)}/{len(reit_config)}")
    print(f"Distribution cuts:   {total_cuts}")
    print(f"Output file:         {args.output}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
