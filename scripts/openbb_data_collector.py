#!/usr/bin/env python3
"""
OpenBB Data Collector for Canadian REITs

Retrieves dividend history, price data, and market metrics from OpenBB Platform
to support distribution cut prediction and peer comparison analysis.

Usage:
    python scripts/openbb_data_collector.py --ticker REI-UN.TO --output data/riocan_openbb.json
    python scripts/openbb_data_collector.py --ticker DIR-UN.TO --peers REI-UN.TO,AX-UN.TO,SRU-UN.TO

Requirements:
    pip install openbb openbb-tmx pandas

Author: Claude Code
Version: 1.0.0
Date: 2025-10-21
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

try:
    from openbb import obb
    import pandas as pd
except ImportError as e:
    print(f"ERROR: Missing required package: {e}")
    print("Install with: pip install openbb openbb-tmx pandas")
    sys.exit(1)


class OpenBBDataCollector:
    """
    Collects dividend, price, and market data for Canadian REITs using OpenBB Platform.
    """

    def __init__(self, ticker: str, provider: str = "tmx"):
        """
        Initialize data collector for a specific REIT.

        Args:
            ticker: REIT ticker symbol (e.g., 'REI-UN.TO', 'DIR-UN.TO')
            provider: Data provider ('tmx' or 'yfinance')
        """
        self.ticker = ticker
        self.provider = provider
        self.reit_name = self._extract_reit_name(ticker)

    @staticmethod
    def _extract_reit_name(ticker: str) -> str:
        """Extract REIT name from ticker symbol."""
        symbol = ticker.split('.')[0].replace('-UN', '').replace('-', ' ')
        return symbol.upper()

    def get_dividend_history(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Retrieve complete dividend history for the REIT.

        Args:
            start_date: Start date (YYYY-MM-DD). Default: 10 years ago
            end_date: End date (YYYY-MM-DD). Default: today

        Returns:
            DataFrame with columns: ex_dividend_date, amount, currency, record_date,
                                    payment_date, declaration_date
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=3650)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        try:
            result = obb.equity.fundamental.dividends(
                symbol=self.ticker,
                provider=self.provider
            )
            df = result.to_df()

            # Filter by date range
            df['ex_dividend_date'] = pd.to_datetime(df['ex_dividend_date'])
            mask = (df['ex_dividend_date'] >= start_date) & (df['ex_dividend_date'] <= end_date)
            df = df[mask].copy()

            # Sort by date descending (most recent first)
            df = df.sort_values('ex_dividend_date', ascending=False)

            return df

        except Exception as e:
            print(f"ERROR retrieving dividend history for {self.ticker}: {e}")
            return pd.DataFrame()

    def get_current_price(self) -> Optional[float]:
        """
        Get current market price for the REIT.

        Returns:
            Current closing price or None if unavailable
        """
        try:
            result = obb.equity.price.historical(
                symbol=self.ticker,
                provider=self.provider,
                start_date=(datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
            )
            df = result.to_df()
            if not df.empty:
                return df['close'].iloc[-1]
        except Exception as e:
            print(f"WARNING: Could not retrieve price for {self.ticker}: {e}")
        return None

    def calculate_ttm_metrics(self, dividend_df: pd.DataFrame, current_price: float) -> Dict:
        """
        Calculate trailing-twelve-months dividend metrics.

        Args:
            dividend_df: DataFrame from get_dividend_history()
            current_price: Current market price

        Returns:
            Dict with TTM metrics (annual_dividend, yield, payment_count, etc.)
        """
        if dividend_df.empty or not current_price:
            return {}

        # Calculate TTM dividends (last 365 days)
        cutoff = datetime.now() - timedelta(days=365)
        ttm_divs = dividend_df[dividend_df['ex_dividend_date'] >= cutoff]

        annual_dividend = ttm_divs['amount'].sum()
        payment_count = len(ttm_divs)
        dividend_yield = (annual_dividend / current_price) * 100 if current_price > 0 else 0

        # Calculate monthly distribution (most recent)
        recent_div = dividend_df['amount'].iloc[0] if not dividend_df.empty else 0

        return {
            'annual_dividend_ttm': round(annual_dividend, 4),
            'dividend_yield_ttm': round(dividend_yield, 2),
            'payment_count_ttm': payment_count,
            'monthly_distribution': round(recent_div, 4),
            'current_price': round(current_price, 2),
            'calculation_date': datetime.now().strftime('%Y-%m-%d')
        }

    def detect_dividend_cuts(self, dividend_df: pd.DataFrame, lookback_years: int = 10) -> List[Dict]:
        """
        Detect dividend cuts in historical data.

        Args:
            dividend_df: DataFrame from get_dividend_history()
            lookback_years: Years to analyze (default: 10)

        Returns:
            List of detected cuts with dates, old/new amounts, and % reduction
        """
        if dividend_df.empty:
            return []

        cuts = []
        df = dividend_df.sort_values('ex_dividend_date', ascending=True)

        # Group by year-month to detect monthly distribution changes
        df['year_month'] = df['ex_dividend_date'].dt.to_period('M')
        monthly_avg = df.groupby('year_month')['amount'].mean()

        # Detect significant reductions (>10% from prior month)
        for i in range(1, len(monthly_avg)):
            prev_amount = monthly_avg.iloc[i-1]
            curr_amount = monthly_avg.iloc[i]

            if prev_amount > 0:
                pct_change = (curr_amount - prev_amount) / prev_amount

                if pct_change < -0.10:  # 10%+ reduction
                    cuts.append({
                        'cut_date': str(monthly_avg.index[i]),
                        'previous_monthly': round(prev_amount, 4),
                        'new_monthly': round(curr_amount, 4),
                        'cut_percentage': round(abs(pct_change) * 100, 1),
                        'previous_annual': round(prev_amount * 12, 2),
                        'new_annual': round(curr_amount * 12, 2)
                    })

        return cuts

    def compare_peers(self, peer_tickers: List[str]) -> pd.DataFrame:
        """
        Compare dividend yield and metrics across peer REITs.

        Args:
            peer_tickers: List of peer REIT tickers (e.g., ['REI-UN.TO', 'DIR-UN.TO'])

        Returns:
            DataFrame with peer comparison (ticker, price, yield, annual_dividend)
        """
        all_tickers = [self.ticker] + peer_tickers
        comparison_data = []

        for ticker in all_tickers:
            try:
                collector = OpenBBDataCollector(ticker, self.provider)
                div_df = collector.get_dividend_history()
                price = collector.get_current_price()

                if div_df.empty or not price:
                    continue

                ttm = collector.calculate_ttm_metrics(div_df, price)

                comparison_data.append({
                    'ticker': ticker,
                    'reit_name': collector.reit_name,
                    'current_price': ttm.get('current_price', 0),
                    'annual_dividend': ttm.get('annual_dividend_ttm', 0),
                    'dividend_yield': ttm.get('dividend_yield_ttm', 0),
                    'monthly_distribution': ttm.get('monthly_distribution', 0)
                })

            except Exception as e:
                print(f"WARNING: Could not retrieve data for peer {ticker}: {e}")
                continue

        if not comparison_data:
            return pd.DataFrame()

        df = pd.DataFrame(comparison_data)
        df = df.sort_values('dividend_yield', ascending=False)
        return df

    def validate_against_issuer(
        self,
        issuer_reported_distribution: float,
        tolerance: float = 0.05
    ) -> Dict:
        """
        Validate OpenBB dividend data against issuer-reported distribution.

        Args:
            issuer_reported_distribution: Issuer's reported monthly distribution ($)
            tolerance: Acceptable variance (default: 5%)

        Returns:
            Validation results dict
        """
        div_df = self.get_dividend_history()
        if div_df.empty:
            return {'valid': False, 'reason': 'No dividend data available'}

        recent_div = div_df['amount'].iloc[0]
        variance = abs(recent_div - issuer_reported_distribution) / issuer_reported_distribution

        is_valid = variance <= tolerance

        return {
            'valid': is_valid,
            'openbb_monthly': round(recent_div, 4),
            'issuer_reported_monthly': round(issuer_reported_distribution, 4),
            'variance_pct': round(variance * 100, 2),
            'variance_amount': round(abs(recent_div - issuer_reported_distribution), 4),
            'tolerance_pct': tolerance * 100,
            'validation_date': datetime.now().strftime('%Y-%m-%d'),
            'data_source': self.provider
        }

    def export_full_dataset(self, output_path: Path) -> Dict:
        """
        Export complete dataset for model training and analysis.

        Args:
            output_path: Path to output JSON file

        Returns:
            Complete dataset dict
        """
        print(f"Collecting data for {self.ticker}...")

        # Retrieve dividend history
        div_df = self.get_dividend_history()
        if div_df.empty:
            return {'error': 'No dividend data available'}

        # Get current price
        price = self.get_current_price()

        # Calculate TTM metrics
        ttm = self.calculate_ttm_metrics(div_df, price) if price else {}

        # Detect historical cuts
        cuts = self.detect_dividend_cuts(div_df)

        # Build dataset
        dataset = {
            'ticker': self.ticker,
            'reit_name': self.reit_name,
            'data_provider': self.provider,
            'collection_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_metrics': ttm,
            'dividend_history': {
                'total_records': len(div_df),
                'date_range': {
                    'earliest': div_df['ex_dividend_date'].min().strftime('%Y-%m-%d') if not div_df.empty else None,
                    'latest': div_df['ex_dividend_date'].max().strftime('%Y-%m-%d') if not div_df.empty else None
                },
                'records': div_df.to_dict(orient='records')
            },
            'detected_cuts': cuts,
            'cut_count': len(cuts)
        }

        # Export to JSON
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(dataset, f, indent=2, default=str)

        print(f"✓ Exported {len(div_df)} dividend records to {output_path}")
        print(f"✓ Detected {len(cuts)} historical cuts")

        return dataset


def main():
    """Command-line interface for OpenBB data collection."""
    parser = argparse.ArgumentParser(
        description="Collect dividend and market data for Canadian REITs using OpenBB"
    )
    parser.add_argument(
        '--ticker',
        required=True,
        help='REIT ticker symbol (e.g., REI-UN.TO, DIR-UN.TO)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output JSON file path (default: data/<ticker>_openbb.json)'
    )
    parser.add_argument(
        '--peers',
        help='Comma-separated list of peer tickers for comparison (e.g., REI-UN.TO,DIR-UN.TO)'
    )
    parser.add_argument(
        '--validate-distribution',
        type=float,
        help='Validate against issuer-reported monthly distribution amount ($)'
    )
    parser.add_argument(
        '--provider',
        default='tmx',
        choices=['tmx', 'yfinance'],
        help='Data provider (default: tmx)'
    )
    parser.add_argument(
        '--export-csv',
        action='store_true',
        help='Also export dividend history to CSV'
    )

    args = parser.parse_args()

    # Initialize collector
    collector = OpenBBDataCollector(args.ticker, args.provider)

    # Set default output path
    if not args.output:
        ticker_clean = args.ticker.replace('.TO', '').replace('-UN', '').replace('-', '')
        args.output = Path(f'data/{ticker_clean.lower()}_openbb.json')

    # Export full dataset
    dataset = collector.export_full_dataset(args.output)

    if 'error' in dataset:
        print(f"ERROR: {dataset['error']}")
        sys.exit(1)

    # Peer comparison
    if args.peers:
        peer_list = [p.strip() for p in args.peers.split(',')]
        print(f"\nComparing with {len(peer_list)} peers...")
        peer_df = collector.compare_peers(peer_list)

        if not peer_df.empty:
            print("\nPeer Comparison:")
            print(peer_df.to_string(index=False))

            # Export peer comparison
            peer_output = args.output.parent / f"{args.output.stem}_peer_comparison.csv"
            peer_df.to_csv(peer_output, index=False)
            print(f"\n✓ Exported peer comparison to {peer_output}")

    # Validation
    if args.validate_distribution:
        print(f"\nValidating against issuer-reported distribution: ${args.validate_distribution:.4f}/month")
        validation = collector.validate_against_issuer(args.validate_distribution)

        if validation['valid']:
            print(f"✓ VALID - OpenBB: ${validation['openbb_monthly']:.4f}, Variance: {validation['variance_pct']}%")
        else:
            print(f"✗ INVALID - OpenBB: ${validation['openbb_monthly']:.4f}, Variance: {validation['variance_pct']}% (>{validation['tolerance_pct']}% tolerance)")

    # CSV export
    if args.export_csv:
        div_df = collector.get_dividend_history()
        csv_output = args.output.parent / f"{args.output.stem}_dividends.csv"
        div_df.to_csv(csv_output, index=False)
        print(f"\n✓ Exported dividend history to {csv_output}")

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY: {collector.reit_name} ({args.ticker})")
    print(f"{'='*60}")
    if dataset.get('current_metrics'):
        metrics = dataset['current_metrics']
        print(f"Current Price:       ${metrics.get('current_price', 0):.2f}")
        print(f"Annual Dividend:     ${metrics.get('annual_dividend_ttm', 0):.4f}")
        print(f"Dividend Yield:      {metrics.get('dividend_yield_ttm', 0):.2f}%")
        print(f"Monthly Distribution:${metrics.get('monthly_distribution', 0):.4f}")
    print(f"Dividend Records:    {dataset['dividend_history']['total_records']}")
    print(f"Historical Cuts:     {dataset['cut_count']}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
