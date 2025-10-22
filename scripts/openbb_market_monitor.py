#!/usr/bin/env python3
"""
OpenBB Market Data Monitor for Canadian REITs

Retrieves and analyzes market data to detect price stress, volatility,
and momentum indicators for credit risk assessment.

Usage:
    python scripts/openbb_market_monitor.py --ticker REI-UN.TO --output data/riocan_market.json
    python scripts/openbb_market_monitor.py --ticker AX-UN.TO --lookback 365

Features:
    - Price stress detection (>30% decline from 52-week high)
    - Volatility metrics (standard deviation, coefficient of variation)
    - Momentum indicators (3-month, 6-month, 12-month returns)
    - 52-week high/low tracking
    - Trading volume analysis
    - Price trend classification

Author: Claude Code
Version: 1.0.0
Date: 2025-10-22
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from openbb import obb
    import pandas as pd
    import numpy as np
except ImportError as e:
    print(f"ERROR: Missing required package: {e}")
    print("Install with: pip install openbb openbb-tmx pandas numpy")
    sys.exit(1)


class MarketDataMonitor:
    """
    Monitors market data for Canadian REITs to detect price stress,
    volatility, and momentum shifts that may indicate credit risk.
    """

    def __init__(self, ticker: str, provider: str = "tmx"):
        """
        Initialize market monitor for a specific REIT.

        Args:
            ticker: REIT ticker symbol (e.g., 'REI-UN.TO', 'AX-UN.TO')
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

    def get_price_history(
        self,
        lookback_days: int = 365
    ) -> pd.DataFrame:
        """
        Retrieve historical price data.

        Args:
            lookback_days: Number of days to retrieve (default: 365)

        Returns:
            DataFrame with OHLCV data
        """
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        try:
            result = obb.equity.price.historical(
                symbol=self.ticker,
                provider=self.provider,
                start_date=start_date,
                end_date=end_date
            )
            df = result.to_df()

            if df.empty:
                print(f"WARNING: No price data retrieved for {self.ticker}")
                return pd.DataFrame()

            # Ensure date column
            if 'date' not in df.columns and df.index.name == 'date':
                df = df.reset_index()

            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date', ascending=True)

            return df

        except Exception as e:
            print(f"ERROR retrieving price history for {self.ticker}: {e}")
            return pd.DataFrame()

    def detect_price_stress(
        self,
        price_df: pd.DataFrame,
        threshold: float = 0.30
    ) -> Dict:
        """
        Detect price stress (>30% decline from 52-week high).

        Args:
            price_df: DataFrame from get_price_history()
            threshold: Decline threshold for stress signal (default: 30%)

        Returns:
            Dict with stress metrics and classification
        """
        if price_df.empty:
            return {'stress_detected': False, 'reason': 'No price data'}

        current_price = price_df['close'].iloc[-1]
        high_52w = price_df['close'].max()
        low_52w = price_df['close'].min()

        # Calculate decline from peak
        decline_from_peak = (high_52w - current_price) / high_52w
        decline_from_peak_pct = decline_from_peak * 100

        # Find peak date
        peak_date = price_df.loc[price_df['close'].idxmax(), 'date']
        days_since_peak = (datetime.now() - pd.to_datetime(peak_date)).days

        # Stress classification
        stress_detected = decline_from_peak >= threshold
        stress_level = self._classify_stress_level(decline_from_peak)

        return {
            'stress_detected': stress_detected,
            'current_price': round(current_price, 2),
            'high_52w': round(high_52w, 2),
            'low_52w': round(low_52w, 2),
            'decline_from_peak_pct': round(decline_from_peak_pct, 1),
            'peak_date': peak_date.strftime('%Y-%m-%d') if hasattr(peak_date, 'strftime') else str(peak_date),
            'days_since_peak': days_since_peak,
            'stress_level': stress_level,
            'price_range_52w': round(high_52w - low_52w, 2),
            'distance_from_low_pct': round(((current_price - low_52w) / low_52w) * 100, 1)
        }

    @staticmethod
    def _classify_stress_level(decline_pct: float) -> str:
        """
        Classify price stress level based on decline from peak.

        Args:
            decline_pct: Decline percentage (0-1 scale)

        Returns:
            Stress level classification
        """
        if decline_pct >= 0.50:
            return "SEVERE (>50%)"
        elif decline_pct >= 0.40:
            return "HIGH (40-50%)"
        elif decline_pct >= 0.30:
            return "MODERATE (30-40%)"
        elif decline_pct >= 0.20:
            return "MILD (20-30%)"
        elif decline_pct >= 0.10:
            return "LOW (10-20%)"
        else:
            return "MINIMAL (<10%)"

    def calculate_volatility(
        self,
        price_df: pd.DataFrame,
        windows: List[int] = [30, 90, 252]
    ) -> Dict:
        """
        Calculate price volatility metrics.

        Args:
            price_df: DataFrame from get_price_history()
            windows: Lookback windows in days (default: 30, 90, 252 days)

        Returns:
            Dict with volatility metrics
        """
        if price_df.empty:
            return {}

        # Calculate daily returns
        price_df = price_df.copy()
        price_df['returns'] = price_df['close'].pct_change()

        volatility_metrics = {}

        for window in windows:
            if len(price_df) >= window:
                recent_returns = price_df['returns'].tail(window)

                # Annualized volatility (std dev * sqrt(252))
                volatility_annualized = recent_returns.std() * np.sqrt(252)

                # Coefficient of variation (relative volatility)
                mean_return = recent_returns.mean()
                cv = abs(recent_returns.std() / mean_return) if mean_return != 0 else None

                volatility_metrics[f'{window}d'] = {
                    'volatility_annualized_pct': round(volatility_annualized * 100, 2),
                    'std_dev_daily_pct': round(recent_returns.std() * 100, 2),
                    'coefficient_of_variation': round(cv, 2) if cv is not None else None,
                    'max_daily_return_pct': round(recent_returns.max() * 100, 2),
                    'min_daily_return_pct': round(recent_returns.min() * 100, 2)
                }

        # Overall volatility classification
        current_vol = volatility_metrics.get('90d', {}).get('volatility_annualized_pct', 0)
        vol_classification = self._classify_volatility(current_vol)

        return {
            'metrics': volatility_metrics,
            'classification': vol_classification,
            'assessment_date': datetime.now().strftime('%Y-%m-%d')
        }

    @staticmethod
    def _classify_volatility(annualized_vol_pct: float) -> str:
        """
        Classify volatility level.

        Args:
            annualized_vol_pct: Annualized volatility (%)

        Returns:
            Volatility classification
        """
        if annualized_vol_pct >= 40:
            return "VERY HIGH (>40%)"
        elif annualized_vol_pct >= 30:
            return "HIGH (30-40%)"
        elif annualized_vol_pct >= 20:
            return "MODERATE (20-30%)"
        elif annualized_vol_pct >= 10:
            return "LOW (10-20%)"
        else:
            return "VERY LOW (<10%)"

    def calculate_momentum(
        self,
        price_df: pd.DataFrame,
        periods: List[int] = [63, 126, 252]  # ~3mo, 6mo, 12mo (trading days)
    ) -> Dict:
        """
        Calculate price momentum indicators.

        Args:
            price_df: DataFrame from get_price_history()
            periods: Lookback periods in trading days (default: 3mo, 6mo, 12mo)

        Returns:
            Dict with momentum metrics
        """
        if price_df.empty:
            return {}

        current_price = price_df['close'].iloc[-1]
        momentum_metrics = {}

        period_labels = {
            63: '3_month',
            126: '6_month',
            252: '12_month'
        }

        for period in periods:
            if len(price_df) >= period:
                past_price = price_df['close'].iloc[-period]
                total_return = (current_price - past_price) / past_price
                total_return_pct = total_return * 100

                # Annualized return
                years = period / 252
                annualized_return = ((1 + total_return) ** (1 / years)) - 1
                annualized_return_pct = annualized_return * 100

                label = period_labels.get(period, f'{period}d')

                momentum_metrics[label] = {
                    'total_return_pct': round(total_return_pct, 2),
                    'annualized_return_pct': round(annualized_return_pct, 2),
                    'start_price': round(past_price, 2),
                    'end_price': round(current_price, 2),
                    'period_days': period
                }

        # Momentum trend classification
        recent_momentum = momentum_metrics.get('3_month', {}).get('total_return_pct', 0)
        momentum_trend = self._classify_momentum(recent_momentum)

        return {
            'metrics': momentum_metrics,
            'trend': momentum_trend,
            'assessment_date': datetime.now().strftime('%Y-%m-%d')
        }

    @staticmethod
    def _classify_momentum(return_pct: float) -> str:
        """
        Classify momentum trend.

        Args:
            return_pct: Return percentage

        Returns:
            Momentum classification
        """
        if return_pct >= 20:
            return "STRONG POSITIVE (>20%)"
        elif return_pct >= 10:
            return "POSITIVE (10-20%)"
        elif return_pct >= 5:
            return "MILD POSITIVE (5-10%)"
        elif return_pct >= -5:
            return "NEUTRAL (-5% to 5%)"
        elif return_pct >= -10:
            return "MILD NEGATIVE (-10% to -5%)"
        elif return_pct >= -20:
            return "NEGATIVE (-20% to -10%)"
        else:
            return "STRONG NEGATIVE (<-20%)"

    def analyze_trading_volume(
        self,
        price_df: pd.DataFrame,
        windows: List[int] = [30, 90]
    ) -> Dict:
        """
        Analyze trading volume patterns.

        Args:
            price_df: DataFrame from get_price_history()
            windows: Lookback windows in days

        Returns:
            Dict with volume metrics
        """
        if price_df.empty or 'volume' not in price_df.columns:
            return {}

        volume_metrics = {}

        for window in windows:
            if len(price_df) >= window:
                recent_volume = price_df['volume'].tail(window)

                volume_metrics[f'{window}d'] = {
                    'avg_daily_volume': int(recent_volume.mean()),
                    'total_volume': int(recent_volume.sum()),
                    'max_daily_volume': int(recent_volume.max()),
                    'min_daily_volume': int(recent_volume.min()),
                    'volume_std_dev': int(recent_volume.std())
                }

        # Current vs average volume
        if len(price_df) >= 30:
            current_volume = price_df['volume'].iloc[-1]
            avg_30d = price_df['volume'].tail(30).mean()
            volume_ratio = current_volume / avg_30d if avg_30d > 0 else None

            return {
                'metrics': volume_metrics,
                'current_volume': int(current_volume),
                'volume_vs_30d_avg': round(volume_ratio, 2) if volume_ratio else None,
                'volume_trend': self._classify_volume_trend(volume_ratio) if volume_ratio else 'Unknown'
            }

        return {'metrics': volume_metrics}

    @staticmethod
    def _classify_volume_trend(ratio: float) -> str:
        """
        Classify volume trend based on current vs average ratio.

        Args:
            ratio: Current volume / average volume

        Returns:
            Volume trend classification
        """
        if ratio >= 2.0:
            return "VERY HIGH (>2x average)"
        elif ratio >= 1.5:
            return "HIGH (1.5-2x average)"
        elif ratio >= 0.75:
            return "NORMAL (0.75-1.5x average)"
        elif ratio >= 0.5:
            return "LOW (0.5-0.75x average)"
        else:
            return "VERY LOW (<0.5x average)"

    def generate_market_assessment(
        self,
        lookback_days: int = 365
    ) -> Dict:
        """
        Generate comprehensive market data assessment.

        Args:
            lookback_days: Lookback period in days

        Returns:
            Complete market assessment dict
        """
        print(f"Analyzing market data for {self.ticker}...")

        # Get price history
        price_df = self.get_price_history(lookback_days)
        if price_df.empty:
            return {'error': 'No price data available'}

        # Run all analyses
        stress = self.detect_price_stress(price_df)
        volatility = self.calculate_volatility(price_df)
        momentum = self.calculate_momentum(price_df)
        volume = self.analyze_trading_volume(price_df)

        # Overall risk assessment
        risk_score = self._calculate_risk_score(stress, volatility, momentum)

        assessment = {
            'ticker': self.ticker,
            'reit_name': self.reit_name,
            'assessment_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'lookback_days': lookback_days,
            'data_points': len(price_df),
            'price_stress': stress,
            'volatility': volatility,
            'momentum': momentum,
            'volume': volume,
            'risk_score': risk_score,
            'overall_assessment': self._generate_narrative(stress, volatility, momentum, risk_score)
        }

        return assessment

    def _calculate_risk_score(
        self,
        stress: Dict,
        volatility: Dict,
        momentum: Dict
    ) -> Dict:
        """
        Calculate overall market risk score (0-100).

        Scoring:
        - Price stress: 0-40 points
        - Volatility: 0-30 points
        - Momentum: 0-30 points

        Args:
            stress: Stress metrics
            volatility: Volatility metrics
            momentum: Momentum metrics

        Returns:
            Risk score dict
        """
        score = 0
        max_score = 100

        # Price stress (0-40 points)
        decline = stress.get('decline_from_peak_pct', 0)
        if decline >= 50:
            stress_points = 40
        elif decline >= 40:
            stress_points = 35
        elif decline >= 30:
            stress_points = 30
        elif decline >= 20:
            stress_points = 20
        elif decline >= 10:
            stress_points = 10
        else:
            stress_points = 0

        # Volatility (0-30 points)
        vol_90d = volatility.get('metrics', {}).get('90d', {}).get('volatility_annualized_pct', 0)
        if vol_90d >= 40:
            vol_points = 30
        elif vol_90d >= 30:
            vol_points = 25
        elif vol_90d >= 20:
            vol_points = 15
        elif vol_90d >= 10:
            vol_points = 5
        else:
            vol_points = 0

        # Momentum (0-30 points) - negative momentum = higher risk
        momentum_3m = momentum.get('metrics', {}).get('3_month', {}).get('total_return_pct', 0)
        if momentum_3m <= -20:
            momentum_points = 30
        elif momentum_3m <= -10:
            momentum_points = 20
        elif momentum_3m <= -5:
            momentum_points = 10
        elif momentum_3m <= 5:
            momentum_points = 5
        else:
            momentum_points = 0

        score = stress_points + vol_points + momentum_points

        # Risk classification
        if score >= 70:
            risk_level = "VERY HIGH"
        elif score >= 50:
            risk_level = "HIGH"
        elif score >= 30:
            risk_level = "MODERATE"
        elif score >= 15:
            risk_level = "LOW"
        else:
            risk_level = "VERY LOW"

        return {
            'total_score': score,
            'max_score': max_score,
            'risk_level': risk_level,
            'components': {
                'stress_points': stress_points,
                'volatility_points': vol_points,
                'momentum_points': momentum_points
            }
        }

    def _generate_narrative(
        self,
        stress: Dict,
        volatility: Dict,
        momentum: Dict,
        risk_score: Dict
    ) -> str:
        """
        Generate narrative assessment of market conditions.

        Args:
            stress: Stress metrics
            volatility: Volatility metrics
            momentum: Momentum metrics
            risk_score: Risk score

        Returns:
            Narrative assessment string
        """
        narratives = []

        # Price stress narrative
        decline = stress.get('decline_from_peak_pct', 0)
        stress_level = stress.get('stress_level', '')
        if decline >= 30:
            narratives.append(f"⚠️ Price stress detected: {decline:.1f}% decline from 52-week high ({stress_level}).")
        elif decline >= 20:
            narratives.append(f"Price {decline:.1f}% below 52-week high ({stress_level}).")
        else:
            narratives.append(f"Price within {decline:.1f}% of 52-week high (minimal stress).")

        # Volatility narrative
        vol_90d = volatility.get('metrics', {}).get('90d', {}).get('volatility_annualized_pct', 0)
        vol_class = volatility.get('classification', '')
        narratives.append(f"90-day volatility: {vol_90d:.1f}% annualized ({vol_class}).")

        # Momentum narrative
        momentum_3m = momentum.get('metrics', {}).get('3_month', {}).get('total_return_pct', 0)
        momentum_trend = momentum.get('trend', '')
        if momentum_3m < 0:
            narratives.append(f"Negative 3-month momentum: {momentum_3m:.1f}% ({momentum_trend}).")
        else:
            narratives.append(f"Positive 3-month momentum: {momentum_3m:.1f}% ({momentum_trend}).")

        # Overall assessment
        risk_level = risk_score.get('risk_level', '')
        total_score = risk_score.get('total_score', 0)
        narratives.append(f"Overall market risk: {risk_level} (score: {total_score}/100).")

        return ' '.join(narratives)

    def export_assessment(self, output_path: Path, assessment: Dict) -> None:
        """
        Export market assessment to JSON file.

        Args:
            output_path: Path to output JSON file
            assessment: Assessment dict from generate_market_assessment()
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(assessment, f, indent=2, default=str)

        print(f"✓ Exported market assessment to {output_path}")


def main():
    """Command-line interface for market data monitor."""
    parser = argparse.ArgumentParser(
        description="Monitor market data for Canadian REITs (price stress, volatility, momentum)"
    )
    parser.add_argument(
        '--ticker',
        required=True,
        help='REIT ticker symbol (e.g., REI-UN.TO, AX-UN.TO)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output JSON file path (default: data/<ticker>_market.json)'
    )
    parser.add_argument(
        '--lookback',
        type=int,
        default=365,
        help='Lookback period in days (default: 365)'
    )
    parser.add_argument(
        '--provider',
        default='tmx',
        choices=['tmx', 'yfinance'],
        help='Data provider (default: tmx)'
    )

    args = parser.parse_args()

    # Initialize monitor
    monitor = MarketDataMonitor(args.ticker, args.provider)

    # Set default output path
    if not args.output:
        ticker_clean = args.ticker.replace('.TO', '').replace('-UN', '').replace('-', '')
        args.output = Path(f'data/{ticker_clean.lower()}_market.json')

    # Generate assessment
    assessment = monitor.generate_market_assessment(args.lookback)

    if 'error' in assessment:
        print(f"ERROR: {assessment['error']}")
        sys.exit(1)

    # Export to JSON
    monitor.export_assessment(args.output, assessment)

    # Display summary
    print(f"\n{'='*60}")
    print(f"MARKET ASSESSMENT: {monitor.reit_name} ({args.ticker})")
    print(f"{'='*60}")

    # Price stress
    stress = assessment.get('price_stress', {})
    print(f"\nPrice Stress:")
    print(f"  Current Price:        ${stress.get('current_price', 0):.2f}")
    print(f"  52-Week High:         ${stress.get('high_52w', 0):.2f}")
    print(f"  52-Week Low:          ${stress.get('low_52w', 0):.2f}")
    print(f"  Decline from Peak:    {stress.get('decline_from_peak_pct', 0):.1f}%")
    print(f"  Stress Level:         {stress.get('stress_level', 'N/A')}")
    print(f"  Days Since Peak:      {stress.get('days_since_peak', 0)}")

    # Volatility
    volatility = assessment.get('volatility', {})
    vol_90d = volatility.get('metrics', {}).get('90d', {})
    print(f"\nVolatility (90-day):")
    print(f"  Annualized:           {vol_90d.get('volatility_annualized_pct', 0):.2f}%")
    print(f"  Classification:       {volatility.get('classification', 'N/A')}")

    # Momentum
    momentum = assessment.get('momentum', {})
    mom_3m = momentum.get('metrics', {}).get('3_month', {})
    mom_12m = momentum.get('metrics', {}).get('12_month', {})
    print(f"\nMomentum:")
    print(f"  3-Month Return:       {mom_3m.get('total_return_pct', 0):.2f}%")
    print(f"  12-Month Return:      {mom_12m.get('total_return_pct', 0):.2f}%")
    print(f"  Trend:                {momentum.get('trend', 'N/A')}")

    # Risk score
    risk = assessment.get('risk_score', {})
    print(f"\nOverall Risk Assessment:")
    print(f"  Risk Score:           {risk.get('total_score', 0)}/100")
    print(f"  Risk Level:           {risk.get('risk_level', 'N/A')}")

    # Narrative
    narrative = assessment.get('overall_assessment', '')
    print(f"\n{narrative}")

    print(f"\n{'='*60}")


if __name__ == '__main__':
    main()
