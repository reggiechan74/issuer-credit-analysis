#!/usr/bin/env python3
"""
Distribution Cut Prediction Interface

Predicts REIT distribution cut probability using trained LightGBM model.

Supports:
1. Single REIT prediction from manual input
2. Batch prediction from CSV file
3. Integration with training_dataset_v2.csv format
4. SHAP explanations for predictions

Usage:
    # Single REIT prediction
    python scripts/predict_distribution_cut.py --ticker "ABC.TO" \\
        --affo-payout 95 --interest-coverage 2.5 --debt-to-assets 55

    # Batch prediction from CSV
    python scripts/predict_distribution_cut.py --csv data/new_reits.csv

    # Using latest trained model
    python scripts/predict_distribution_cut.py --model models/lightgbm_model_*.pkl --csv data/new_reits.csv
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd
import numpy as np
import joblib
import shap

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')


class DistributionCutPredictor:
    """Predicts REIT distribution cut probability."""

    def __init__(self, model_path: str = None):
        """
        Initialize predictor with trained model.

        Args:
            model_path: Path to trained LightGBM model (.pkl).
                       If None, uses most recent model in models/ directory.
        """
        if model_path is None:
            # Find most recent LightGBM baseline model
            model_files = sorted(Path("models").glob("lightgbm_model_*.pkl"))
            if not model_files:
                raise FileNotFoundError("No trained LightGBM models found in models/")
            model_path = model_files[-1]

        print(f"📊 Loading model from {model_path}")
        self.model = joblib.load(model_path)
        self.model_path = model_path

        # Load feature names from training dataset
        self.feature_names = self._load_feature_names()
        print(f"✅ Model loaded ({len(self.feature_names)} features)")

    def _load_feature_names(self, dataset_path="data/training_dataset_v2.csv") -> List[str]:
        """Load feature names from training dataset."""
        df = pd.read_csv(dataset_path)

        # Exclude non-feature columns (same as training)
        exclude_cols = [
            'ticker', 'cut_date', 'sector', 'target_cut_occurred',
            'ttm_distribution_pre_cut', 'avg_monthly_distribution',
            'dividend_payment_count_ttm', 'current_price', 'current_yield',
            'data_quality', 'notes', 'cash_runway_months', 'self_funding_ratio',
            'risk_level'
        ]

        return [col for col in df.columns if col not in exclude_cols]

    def predict_single(self,
                      ticker: str,
                      affo_payout: float,
                      interest_coverage: float,
                      debt_to_assets: float,
                      debt_to_ebitda: float = None,
                      occupancy: float = None,
                      sector: str = None,
                      **kwargs) -> Dict:
        """
        Predict distribution cut for a single REIT.

        Args:
            ticker: REIT ticker symbol
            affo_payout: AFFO payout ratio (%)
            interest_coverage: Interest coverage ratio
            debt_to_assets: Debt to assets ratio (%)
            debt_to_ebitda: Debt to EBITDA ratio (optional)
            occupancy: Occupancy rate as decimal (e.g., 0.85 for 85%) (optional)
            sector: REIT sector (office/retail/industrial/residential) (optional)
            **kwargs: Additional features

        Returns:
            Dictionary with prediction results and explanations
        """
        # Create feature dict
        features = {
            'affo_payout_ratio': affo_payout,
            'interest_coverage': interest_coverage,
            'debt_to_assets': debt_to_assets,
            'debt_to_ebitda': debt_to_ebitda if debt_to_ebitda is not None else 0,
            'occupancy_rate': occupancy if occupancy is not None else 0,
            **kwargs
        }

        # Create DataFrame with all required features (fill missing with 0)
        feature_values = []
        for feat in self.feature_names:
            feature_values.append(features.get(feat, 0))

        X = np.array([feature_values])

        # Make prediction
        prediction = self.model.predict(X)[0]
        probability = self.model.predict_proba(X)[0, 1]

        # Get SHAP explanation
        explainer = shap.TreeExplainer(self.model)
        shap_values = explainer.shap_values(X)

        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # Positive class

        # Get top contributing features
        contributions = list(zip(self.feature_names, shap_values[0]))
        contributions.sort(key=lambda x: abs(x[1]), reverse=True)

        # Format result
        result = {
            'ticker': ticker,
            'prediction': 'CUT' if prediction == 1 else 'NO CUT',
            'cut_probability': float(probability),
            'risk_level': self._assess_risk_level(probability),
            'top_drivers': [
                {
                    'feature': feat,
                    'shap_value': float(shap_val),
                    'direction': 'increases' if shap_val > 0 else 'decreases',
                    'magnitude': 'high' if abs(shap_val) > 0.5 else 'moderate' if abs(shap_val) > 0.1 else 'low'
                }
                for feat, shap_val in contributions[:5]
            ],
            'input_features': {
                'affo_payout_ratio': affo_payout,
                'interest_coverage': interest_coverage,
                'debt_to_assets': debt_to_assets,
                'debt_to_ebitda': debt_to_ebitda,
                'occupancy_rate': occupancy,
                'sector': sector
            }
        }

        return result

    def predict_batch(self, csv_path: str) -> List[Dict]:
        """
        Predict distribution cuts for multiple REITs from CSV file.

        CSV should have columns: ticker, affo_payout_ratio, interest_coverage, debt_to_assets, etc.
        (same format as training_dataset_v2.csv)

        Args:
            csv_path: Path to CSV file with REIT data

        Returns:
            List of prediction results for each REIT
        """
        print(f"📊 Loading data from {csv_path}")
        df = pd.read_csv(csv_path)

        results = []
        for idx, row in df.iterrows():
            ticker = row.get('ticker', f'REIT_{idx}')

            # Extract features
            feature_dict = {}
            for feat in self.feature_names:
                if feat in row:
                    val = row[feat]
                    feature_dict[feat] = float(val) if pd.notna(val) else 0

            # Extract explicit parameters and remove from feature_dict to avoid duplicates
            affo_payout = feature_dict.pop('affo_payout_ratio', 0)
            interest_coverage = feature_dict.pop('interest_coverage', 0)
            debt_to_assets = feature_dict.pop('debt_to_assets', 0)
            debt_to_ebitda = feature_dict.pop('debt_to_ebitda', 0)
            occupancy = feature_dict.pop('occupancy_rate', 0)

            # Make prediction
            result = self.predict_single(
                ticker=ticker,
                affo_payout=affo_payout,
                interest_coverage=interest_coverage,
                debt_to_assets=debt_to_assets,
                debt_to_ebitda=debt_to_ebitda,
                occupancy=occupancy,
                sector=row.get('sector', None),
                **feature_dict
            )

            results.append(result)

        return results

    @staticmethod
    def _assess_risk_level(probability: float) -> str:
        """Assess risk level based on cut probability."""
        if probability >= 0.8:
            return 'CRITICAL'
        elif probability >= 0.6:
            return 'HIGH'
        elif probability >= 0.4:
            return 'MODERATE'
        elif probability >= 0.2:
            return 'LOW'
        else:
            return 'MINIMAL'

    def print_results(self, results: List[Dict]):
        """Print prediction results in formatted table."""
        print("\n" + "="*120)
        print("DISTRIBUTION CUT PREDICTIONS")
        print("="*120)

        for result in results:
            print(f"\n{'Ticker:':<25s} {result['ticker']}")
            print(f"{'Prediction:':<25s} {result['prediction']}")
            print(f"{'Cut Probability:':<25s} {result['cut_probability']:.1%}")
            print(f"{'Risk Level:':<25s} {result['risk_level']}")

            print(f"\n{'Top 5 Risk Drivers:':<25s}")
            for i, driver in enumerate(result['top_drivers'], 1):
                direction = "↑" if driver['direction'] == 'increases' else "↓"
                print(f"  {i}. {driver['feature']:30s} {direction} {driver['direction']:10s} cut risk "
                      f"(SHAP: {driver['shap_value']:+.4f}, {driver['magnitude']})")

            print(f"\n{'Input Features:':<25s}")
            for key, val in result['input_features'].items():
                if val is not None:
                    if isinstance(val, float):
                        print(f"  {key:30s} {val:.2f}")
                    else:
                        print(f"  {key:30s} {val}")

            print("-" * 120)

        print("="*120)

    def save_results(self, results: List[Dict], output_path: str = None):
        """Save prediction results to JSON file."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"predictions/distribution_cut_predictions_{timestamp}.json"

        output_path = Path(output_path)
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n✅ Saved predictions to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Predict REIT distribution cut probability')

    # Model selection
    parser.add_argument('--model', type=str, default=None,
                       help='Path to trained model (.pkl). If not specified, uses most recent.')

    # Single REIT prediction
    parser.add_argument('--ticker', type=str, help='REIT ticker symbol')
    parser.add_argument('--affo-payout', type=float, help='AFFO payout ratio (%%)')
    parser.add_argument('--interest-coverage', type=float, help='Interest coverage ratio')
    parser.add_argument('--debt-to-assets', type=float, help='Debt to assets ratio (%%)')
    parser.add_argument('--debt-to-ebitda', type=float, help='Debt to EBITDA ratio (optional)')
    parser.add_argument('--occupancy', type=float, help='Occupancy rate (0-1 decimal)')
    parser.add_argument('--sector', type=str, choices=['office', 'retail', 'industrial', 'residential'],
                       help='REIT sector')

    # Batch prediction
    parser.add_argument('--csv', type=str, help='Path to CSV file with REIT data')

    # Output
    parser.add_argument('--output', type=str, help='Output path for prediction results (JSON)')

    args = parser.parse_args()

    # Validate inputs
    if not args.ticker and not args.csv:
        parser.error("Must specify either --ticker (single prediction) or --csv (batch prediction)")

    if args.ticker and not all([args.affo_payout, args.interest_coverage, args.debt_to_assets]):
        parser.error("Single prediction requires --ticker, --affo-payout, --interest-coverage, --debt-to-assets")

    # Initialize predictor
    predictor = DistributionCutPredictor(model_path=args.model)

    # Make predictions
    if args.csv:
        # Batch prediction
        results = predictor.predict_batch(args.csv)
    else:
        # Single prediction
        result = predictor.predict_single(
            ticker=args.ticker,
            affo_payout=args.affo_payout,
            interest_coverage=args.interest_coverage,
            debt_to_assets=args.debt_to_assets,
            debt_to_ebitda=args.debt_to_ebitda,
            occupancy=args.occupancy,
            sector=args.sector
        )
        results = [result]

    # Print results
    predictor.print_results(results)

    # Save results
    if args.output or args.csv:
        predictor.save_results(results, args.output)

    # Summary statistics
    if len(results) > 1:
        cut_predictions = sum(1 for r in results if r['prediction'] == 'CUT')
        avg_probability = sum(r['cut_probability'] for r in results) / len(results)

        print(f"\n📊 Summary Statistics:")
        print(f"  Total REITs analyzed: {len(results)}")
        print(f"  Predicted cuts: {cut_predictions} ({cut_predictions/len(results):.1%})")
        print(f"  Average cut probability: {avg_probability:.1%}")

        # Risk level distribution
        risk_counts = {}
        for r in results:
            risk_counts[r['risk_level']] = risk_counts.get(r['risk_level'], 0) + 1

        print(f"\n  Risk Level Distribution:")
        for level in ['CRITICAL', 'HIGH', 'MODERATE', 'LOW', 'MINIMAL']:
            count = risk_counts.get(level, 0)
            if count > 0:
                print(f"    {level:10s}: {count:2d} ({count/len(results):.1%})")


if __name__ == "__main__":
    main()
