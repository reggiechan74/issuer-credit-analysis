#!/usr/bin/env python3
"""
Phase 4 Data Enrichment Script

Enriches Phase 3 calculated metrics with:
1. Market risk data (OpenBB market monitor)
2. Macroeconomic environment (OpenBB macro monitor)
3. Distribution history (OpenBB data collector)
4. Distribution cut prediction (trained model)

Usage:
    python scripts/enrich_phase4_data.py \
        --phase3 Issuer_Reports/RioCan_REIT/temp/phase3_calculated_metrics.json \
        --ticker REI-UN.TO \
        --output Issuer_Reports/RioCan_REIT/temp/phase4_enriched_data.json

Author: Claude Code
Version: 1.0.0
Date: 2025-10-22
"""

import argparse
import json
import pickle
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

# Import OpenBB monitoring classes
try:
    # Market monitor
    sys.path.insert(0, str(Path(__file__).parent))
    from openbb_market_monitor import MarketDataMonitor
    from openbb_macro_monitor import EnhancedMacroMonitor
    from openbb_data_collector import OpenBBDataCollector
except ImportError as e:
    print(f"ERROR: Cannot import OpenBB monitoring modules: {e}")
    print("Ensure openbb_market_monitor.py, openbb_macro_monitor.py, and openbb_data_collector.py exist")
    sys.exit(1)


class Phase4DataEnricher:
    """
    Enriches Phase 3 calculated metrics with market, macro, and predictive data.
    """

    def __init__(self, phase3_file: str, ticker: str, model_file: str = "models/distribution_cut_logistic_regression.pkl"):
        """
        Initialize enricher.

        Args:
            phase3_file: Path to Phase 3 calculated metrics JSON
            ticker: REIT ticker symbol (e.g., 'REI-UN.TO')
            model_file: Path to trained prediction model pickle file
        """
        self.phase3_file = Path(phase3_file)
        self.ticker = ticker
        self.model_file = Path(model_file)

        # Load Phase 3 data
        self.phase3_data = self._load_phase3_data()

        # Load prediction model
        self.model_data = self._load_model()

    def _load_phase3_data(self) -> Dict:
        """Load Phase 3 calculated metrics."""
        if not self.phase3_file.exists():
            raise FileNotFoundError(f"Phase 3 file not found: {self.phase3_file}")

        with open(self.phase3_file, 'r') as f:
            data = json.load(f)

        print(f"✓ Loaded Phase 3 data: {self.phase3_file}")
        return data

    def _load_model(self) -> Dict:
        """Load trained prediction model."""
        if not self.model_file.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_file}")

        with open(self.model_file, 'rb') as f:
            model_data = pickle.load(f)

        print(f"✓ Loaded prediction model: {self.model_file}")
        print(f"  Model type: {model_data.get('model_type', 'unknown')}")
        print(f"  Version: {model_data.get('version', 'unknown')}")
        print(f"  F1 Score: {model_data.get('metrics', {}).get('f1', 'N/A'):.3f}")

        return model_data

    def collect_market_data(self, lookback_days: int = 365) -> Dict:
        """
        Collect market risk data using OpenBB market monitor.

        Args:
            lookback_days: Number of days of historical data (default: 365)

        Returns:
            Market assessment dictionary
        """
        print(f"\n{'='*60}")
        print("Collecting Market Risk Data")
        print(f"{'='*60}")

        try:
            monitor = MarketDataMonitor(self.ticker, provider='tmx')
            assessment = monitor.generate_market_assessment(lookback_days)

            if 'error' in assessment:
                print(f"⚠️  Market data collection failed: {assessment['error']}")
                return self._generate_market_fallback()

            print(f"✓ Market data collected for {self.ticker}")
            print(f"  Current price: ${assessment.get('price_stress', {}).get('current_price', 'N/A'):.2f}")
            print(f"  Price stress: {assessment.get('price_stress', {}).get('decline_pct', 0):.1f}%")
            print(f"  Risk score: {assessment.get('risk_score', {}).get('total_score', 0)}/100")

            return assessment

        except Exception as e:
            print(f"⚠️  Market data collection error: {e}")
            return self._generate_market_fallback()

    def collect_macro_data(self, lookback_months: int = 120) -> Dict:
        """
        Collect macroeconomic data using OpenBB macro monitor.

        Args:
            lookback_months: Number of months of historical data (default: 120)

        Returns:
            Macro assessment dictionary
        """
        print(f"\n{'='*60}")
        print("Collecting Macroeconomic Data")
        print(f"{'='*60}")

        try:
            monitor = EnhancedMacroMonitor()
            assessment = monitor.generate_assessment(lookback_months)

            print(f"✓ Macro data collected")
            print(f"  Bank of Canada rate: {assessment.get('canada', {}).get('current_rate', 'N/A')}%")
            print(f"  US Fed rate: {assessment.get('united_states', {}).get('current_rate', 'N/A')}%")
            print(f"  Credit stress score: {assessment.get('credit_stress_score', 0)}/100")

            return assessment

        except Exception as e:
            print(f"⚠️  Macro data collection error: {e}")
            return self._generate_macro_fallback()

    def collect_distribution_history(self) -> Dict:
        """
        Collect distribution history using OpenBB data collector.

        Returns:
            Distribution history dictionary
        """
        print(f"\n{'='*60}")
        print("Collecting Distribution History")
        print(f"{'='*60}")

        try:
            collector = OpenBBDataCollector(self.ticker)
            # Calculate start_date for 10 years of history
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365*10)).strftime('%Y-%m-%d')
            history = collector.get_dividend_history(start_date=start_date, end_date=end_date)

            if history.empty:
                print(f"⚠️  No distribution history available for {self.ticker}")
                return self._generate_distribution_fallback()

            # Analyze distribution cuts
            cuts_list = collector.detect_dividend_cuts(history, lookback_years=10)
            # Convert list to DataFrame for consistency
            import pandas as pd
            if cuts_list:
                cuts = pd.DataFrame(cuts_list)
            else:
                cuts = pd.DataFrame()

            # Get current distribution
            if not history.empty:
                current_annual = history['amount'].iloc[-1] * 12  # Assume monthly
                current_monthly = history['amount'].iloc[-1]
            else:
                current_annual = 0
                current_monthly = 0

            # Recovery analysis (if cuts exist)
            recovery_status = "No cuts detected"
            recovery_level_pct = 100.0

            if not cuts.empty:
                latest_cut = cuts.iloc[-1]
                recovery_status = self._analyze_recovery(history, latest_cut)

                # Calculate recovery level
                pre_cut_amount = latest_cut.get('prev_amount', current_monthly)
                if pre_cut_amount > 0:
                    recovery_level_pct = (current_monthly / pre_cut_amount) * 100

            result = {
                'ticker': self.ticker,
                'history_years': 10,
                'total_distributions': len(history),
                'current_monthly': current_monthly,
                'current_annual': current_annual,
                'cuts_detected': len(cuts),
                'latest_cut_date': cuts.iloc[-1]['date'].strftime('%Y-%m-%d') if not cuts.empty else None,
                'latest_cut_magnitude_pct': cuts.iloc[-1]['cut_pct'] if not cuts.empty else 0,
                'recovery_status': recovery_status,
                'recovery_level_pct': recovery_level_pct,
                'data_quality': 'strong' if len(history) > 50 else 'weak'
            }

            print(f"✓ Distribution history collected")
            print(f"  Cuts detected: {len(cuts)}")
            print(f"  Current monthly: ${current_monthly:.4f}")
            print(f"  Recovery status: {recovery_status}")

            return result

        except Exception as e:
            print(f"⚠️  Distribution history collection error: {e}")
            return self._generate_distribution_fallback()

    def _analyze_recovery(self, history: pd.DataFrame, latest_cut: pd.Series) -> str:
        """Analyze recovery status after distribution cut."""
        cut_date = latest_cut['date']
        pre_cut_amount = latest_cut.get('prev_amount', 0)

        # Get distributions after cut
        post_cut = history[history['date'] > cut_date]

        if post_cut.empty:
            return "Cut occurred recently - no recovery data"

        current_amount = post_cut['amount'].iloc[-1]

        if current_amount >= pre_cut_amount:
            return "Fully restored"
        elif current_amount >= pre_cut_amount * 0.9:
            return "Substantially restored (90%+)"
        elif current_amount >= pre_cut_amount * 0.75:
            return "Partially restored (75-90%)"
        else:
            return "Minimal restoration (<75%)"

    def run_prediction_model(self, market_data: Dict, macro_data: Dict) -> Dict:
        """
        Run distribution cut prediction model.

        Args:
            market_data: Market assessment dictionary
            macro_data: Macro assessment dictionary

        Returns:
            Prediction results dictionary
        """
        print(f"\n{'='*60}")
        print("Running Distribution Cut Prediction Model")
        print(f"{'='*60}")

        try:
            # Extract features from Phase 3 data
            features = self._prepare_features(market_data, macro_data)

            # Load model components
            model = self.model_data['model']
            scaler = self.model_data['scaler']
            selector = self.model_data['selector']
            selected_features = self.model_data['selected_features']
            target_encoder = self.model_data['target_encoder']

            # Create feature vector (59 features)
            X = pd.DataFrame([features])

            # Apply feature selection (59 → 15)
            X_selected = selector.transform(X)

            # Scale features
            X_scaled = scaler.transform(X_selected)

            # Predict
            y_pred_proba = model.predict_proba(X_scaled)[0]
            y_pred = model.predict(X_scaled)[0]

            # Get prediction details
            cut_probability = y_pred_proba[1] * 100  # Probability of "target" class
            risk_level = self._classify_risk(cut_probability)
            risk_badge = self._get_risk_badge(risk_level)

            # Get top 5 risk drivers
            feature_importance = pd.DataFrame({
                'feature': selected_features,
                'coefficient': model.coef_[0],
                'abs_coefficient': np.abs(model.coef_[0])
            }).sort_values('abs_coefficient', ascending=False)

            top_drivers = []
            for i, row in feature_importance.head(5).iterrows():
                feature_value = X[row['feature']].iloc[0] if row['feature'] in X.columns else 0
                direction = "Increases" if row['coefficient'] > 0 else "Decreases"

                top_drivers.append({
                    'rank': len(top_drivers) + 1,
                    'feature': row['feature'],
                    'value': feature_value,
                    'coefficient': row['coefficient'],
                    'direction': direction
                })

            result = {
                'model_version': self.model_data['version'],
                'prediction_date': datetime.now().strftime('%Y-%m-%d'),
                'cut_probability_pct': round(cut_probability, 1),
                'predicted_class': target_encoder.inverse_transform([y_pred])[0],
                'risk_level': risk_level,
                'risk_badge': risk_badge,
                'confidence': 'High' if abs(cut_probability - 50) > 30 else 'Moderate',
                'top_drivers': top_drivers,
                'model_performance': {
                    'f1_score': self.model_data['metrics']['f1'],
                    'roc_auc': self.model_data['metrics']['roc_auc'],
                    'accuracy': self.model_data['metrics']['accuracy']
                }
            }

            print(f"✓ Prediction complete")
            print(f"  Cut probability: {cut_probability:.1f}%")
            print(f"  Risk level: {risk_level}")
            print(f"  Top driver: {top_drivers[0]['feature']} ({top_drivers[0]['direction']})")

            return result

        except Exception as e:
            print(f"⚠️  Prediction model error: {e}")
            import traceback
            traceback.print_exc()
            return self._generate_prediction_fallback()

    def _prepare_features(self, market_data: Dict, macro_data: Dict) -> Dict:
        """
        Prepare feature vector from Phase 3, market, and macro data.

        Returns:
            Dictionary of 59 features required by the model
        """
        phase3 = self.phase3_data

        # Extract fundamental features (33 from Phase 3)
        fundamentals = {}

        # Leverage metrics
        leverage = phase3.get('leverage_metrics', {})
        fundamentals['total_debt'] = leverage.get('total_debt', 0)
        fundamentals['debt_to_assets_percent'] = leverage.get('debt_to_assets_percent', 0)
        fundamentals['net_debt_ratio'] = leverage.get('net_debt_ratio', 0)

        # FFO/AFFO/ACFO metrics
        ffo_metrics = phase3.get('ffo_metrics', {})
        affo_metrics = phase3.get('affo_metrics', {})
        acfo_metrics = phase3.get('acfo_metrics', {})

        fundamentals['ffo_reported'] = ffo_metrics.get('ffo', 0)
        fundamentals['affo_reported'] = affo_metrics.get('affo', 0)
        fundamentals['ffo_per_unit'] = ffo_metrics.get('ffo_per_unit', 0)
        fundamentals['affo_per_unit'] = affo_metrics.get('affo_per_unit', 0)

        # Distribution metrics
        distributions = phase3.get('distribution_metrics', {})
        fundamentals['distributions_per_unit'] = distributions.get('distributions_per_unit', 0)
        fundamentals['ffo_payout_ratio'] = distributions.get('ffo_payout_ratio_calc', 0)
        fundamentals['affo_payout_ratio'] = distributions.get('affo_payout_ratio_calc', 0)

        # Calculated FFO/AFFO/ACFO
        fundamentals['ffo_calculated'] = ffo_metrics.get('ffo', 0)  # Use same if not recalculated
        fundamentals['affo_calculated'] = affo_metrics.get('affo', 0)
        fundamentals['acfo_calculated'] = acfo_metrics.get('acfo', 0)
        fundamentals['ffo_per_unit_calc'] = ffo_metrics.get('ffo_per_unit', 0)
        fundamentals['affo_per_unit_calc'] = affo_metrics.get('affo_per_unit', 0)
        fundamentals['acfo_per_unit_calc'] = acfo_metrics.get('acfo_per_unit', 0)

        # Coverage metrics
        coverage = phase3.get('coverage_metrics', {})
        fundamentals['noi_interest_coverage'] = coverage.get('noi_interest_coverage', 0)
        fundamentals['annualized_interest_expense'] = coverage.get('annualized_interest_expense', 0)

        # Portfolio metrics
        portfolio = phase3.get('portfolio_metrics', {})
        fundamentals['total_properties'] = portfolio.get('total_properties', 0)
        fundamentals['occupancy_rate'] = portfolio.get('occupancy_rate', 0)
        fundamentals['same_property_noi_growth'] = portfolio.get('same_property_noi_growth', 0)

        # Liquidity metrics
        liquidity = phase3.get('liquidity_metrics', {})
        fundamentals['available_cash'] = liquidity.get('available_cash', 0)
        fundamentals['total_available_liquidity'] = liquidity.get('total_available_liquidity', 0)

        # Burn rate and self-funding
        burn_rate = phase3.get('burn_rate_analysis', {})
        fundamentals['monthly_burn_rate'] = burn_rate.get('monthly_burn_rate', 0)

        afcf_coverage = phase3.get('afcf_coverage', {})
        fundamentals['self_funding_ratio'] = afcf_coverage.get('afcf_self_funding_ratio', 0)

        # Dilution
        dilution = phase3.get('dilution_analysis', {})
        fundamentals['dilution_percentage'] = dilution.get('dilution_percentage', 0)

        # Encode categorical feature: dilution_materiality
        dilution_materiality_str = dilution.get('dilution_materiality', 'low')
        materiality_encoding = {'minimal': 0, 'low': 1, 'moderate': 2, 'high': 3}
        fundamentals['dilution_materiality'] = materiality_encoding.get(dilution_materiality_str, 1)

        # Sector (from Phase 2 or default) - encode as numeric
        sector_str = phase3.get('sector', 'Other')
        sector_encoding = {
            'Retail': 0, 'Office': 1, 'Industrial': 2, 'Residential': 3,
            'Diversified': 4, 'Healthcare': 5, 'Storage': 6, 'Other': 7
        }
        fundamentals['sector'] = sector_encoding.get(sector_str, 7)

        # Market features (17 from market_data)
        market_features = self._extract_market_features(market_data)

        # Macro features (9 from macro_data)
        macro_features = self._extract_macro_features(macro_data)

        # Merge all features
        features = {**fundamentals, **market_features, **macro_features}

        return features

    def _extract_market_features(self, market_data: Dict) -> Dict:
        """Extract 17 market features from market assessment."""
        features = {}

        # Helper function to encode classification strings
        def encode_classification(value_str: str, encoding_map: dict, default: int = 0) -> int:
            """Extract first word from string like 'LOW (10-20%)' and encode."""
            if not isinstance(value_str, str):
                return default
            # Extract first word before parenthesis or space
            first_word = value_str.split('(')[0].split()[0].strip().upper()
            return encoding_map.get(first_word, default)

        # Encoding maps
        stress_encoding = {'MINIMAL': 0, 'LOW': 1, 'MODERATE': 2, 'HIGH': 3, 'SEVERE': 4}
        volatility_encoding = {'VERY': 0, 'LOW': 1, 'MODERATE': 2, 'HIGH': 3, 'EXTREME': 4}
        trend_encoding = {'STRONGLY': -2, 'NEGATIVE': -1, 'NEUTRAL': 0, 'POSITIVE': 1, 'STRONGLY POSITIVE': 2}
        risk_encoding = {'VERY': 0, 'LOW': 1, 'MODERATE': 2, 'HIGH': 3, 'CRITICAL': 4}

        # Price stress
        price_stress = market_data.get('price_stress', {})
        features['mkt_price_stress_decline_pct'] = price_stress.get('decline_pct', 0)
        features['mkt_price_stress_level'] = encode_classification(
            price_stress.get('stress_level', 'MINIMAL'), stress_encoding, 0
        )
        features['mkt_price_52w_high'] = price_stress.get('high_52w', 0)
        features['mkt_price_52w_low'] = price_stress.get('low_52w', 0)
        features['mkt_price_current'] = price_stress.get('current_price', 0)

        # Volatility
        volatility = market_data.get('volatility', {})
        features['mkt_volatility_30d_pct'] = volatility.get('metrics', {}).get('30_day', {}).get('annualized_volatility_pct', 0)
        features['mkt_volatility_90d_pct'] = volatility.get('metrics', {}).get('90_day', {}).get('annualized_volatility_pct', 0)
        features['mkt_volatility_252d_pct'] = volatility.get('metrics', {}).get('252_day', {}).get('annualized_volatility_pct', 0)
        features['mkt_volatility_classification'] = encode_classification(
            volatility.get('classification', 'LOW'), volatility_encoding, 1
        )

        # Momentum
        momentum = market_data.get('momentum', {})
        features['mkt_momentum_3m_pct'] = momentum.get('metrics', {}).get('3_month', {}).get('total_return_pct', 0)
        features['mkt_momentum_6m_pct'] = momentum.get('metrics', {}).get('6_month', {}).get('total_return_pct', 0)
        features['mkt_momentum_12m_pct'] = momentum.get('metrics', {}).get('12_month', {}).get('total_return_pct', 0)
        features['mkt_momentum_trend'] = encode_classification(
            momentum.get('trend', 'NEUTRAL'), trend_encoding, 0
        )

        # Volume and risk
        features['mkt_volume_30d_avg'] = market_data.get('volume', {}).get('avg_30d', 0)
        features['mkt_volume_vs_avg'] = market_data.get('volume', {}).get('vs_avg_pct', 0)
        features['mkt_risk_score'] = market_data.get('risk_score', {}).get('total_score', 0)
        features['mkt_risk_level'] = encode_classification(
            market_data.get('risk_score', {}).get('risk_level', 'LOW'), risk_encoding, 1
        )

        return features

    def _extract_macro_features(self, macro_data: Dict) -> Dict:
        """Extract 9 macro features from macro assessment."""
        features = {}

        # Encoding maps for macro features
        cycle_encoding = {'EASING': -1, 'STABLE': 0, 'TIGHTENING': 1}
        environment_encoding = {'SUPPORTIVE': 0, 'NEUTRAL': 1, 'STRESSED': 2, 'CRISIS': 3}

        # Canadian rates
        canada = macro_data.get('canada', {})
        features['macro_ca_policy_rate'] = canada.get('current_rate', 0)
        features['macro_ca_rate_change_12m_bps'] = canada.get('change_12m_bps', 0)
        # Encode cycle
        cycle_str = canada.get('cycle', 'STABLE')
        features['macro_ca_rate_cycle'] = cycle_encoding.get(cycle_str.upper() if isinstance(cycle_str, str) else 'STABLE', 0)
        features['macro_ca_credit_stress_score'] = macro_data.get('credit_stress_score', 0)
        # Encode environment
        env_str = macro_data.get('credit_environment', 'NEUTRAL')
        features['macro_ca_credit_environment'] = environment_encoding.get(env_str.upper() if isinstance(env_str, str) else 'NEUTRAL', 1)

        # US rates
        us = macro_data.get('united_states', {})
        features['macro_us_policy_rate'] = us.get('current_rate', 0) if us else 0
        features['macro_us_rate_change_12m_bps'] = us.get('change_12m_bps', 0) if us else 0
        # Encode US cycle
        us_cycle_str = us.get('cycle', 'STABLE') if us else 'STABLE'
        features['macro_us_rate_cycle'] = cycle_encoding.get(us_cycle_str.upper() if isinstance(us_cycle_str, str) else 'STABLE', 0)

        # Rate differential
        features['macro_rate_diff_ca_us_bps'] = macro_data.get('spread_bps', 0)

        return features

    def _classify_risk(self, probability: float) -> str:
        """Classify risk level based on cut probability."""
        if probability < 10:
            return "Very Low"
        elif probability < 25:
            return "Low"
        elif probability < 50:
            return "Moderate"
        elif probability < 75:
            return "High"
        else:
            return "Very High"

    def _get_risk_badge(self, risk_level: str) -> str:
        """Get emoji badge for risk level."""
        badges = {
            "Very Low": "🟢",
            "Low": "🟡",
            "Moderate": "🟠",
            "High": "🔴",
            "Very High": "🚨"
        }
        return badges.get(risk_level, "❓")

    def _generate_market_fallback(self) -> Dict:
        """Generate fallback market data when collection fails."""
        return {
            'ticker': self.ticker,
            'error': 'Market data unavailable',
            'price_stress': {'decline_pct': 0, 'stress_level': 'UNKNOWN'},
            'volatility': {'classification': 'UNKNOWN'},
            'momentum': {'trend': 'UNKNOWN'},
            'risk_score': {'total_score': 0, 'risk_level': 'UNKNOWN'}
        }

    def _generate_macro_fallback(self) -> Dict:
        """Generate fallback macro data when collection fails."""
        return {
            'canada': {'current_rate': 0, 'cycle': 'UNKNOWN'},
            'united_states': {'current_rate': 0, 'cycle': 'UNKNOWN'},
            'credit_stress_score': 0,
            'credit_environment': 'UNKNOWN'
        }

    def _generate_distribution_fallback(self) -> Dict:
        """Generate fallback distribution history when collection fails."""
        return {
            'ticker': self.ticker,
            'cuts_detected': 0,
            'recovery_status': 'Unknown',
            'data_quality': 'unavailable'
        }

    def _generate_prediction_fallback(self) -> Dict:
        """Generate fallback prediction when model fails."""
        return {
            'error': 'Prediction unavailable',
            'cut_probability_pct': 0,
            'risk_level': 'Unknown',
            'risk_badge': '❓'
        }

    def enrich(self, market_lookback_days: int = 365, macro_lookback_months: int = 120) -> Dict:
        """
        Run full enrichment pipeline.

        Args:
            market_lookback_days: Market data lookback (default: 365 days)
            macro_lookback_months: Macro data lookback (default: 120 months)

        Returns:
            Enriched data dictionary
        """
        print(f"\n{'='*60}")
        print(f"PHASE 4 DATA ENRICHMENT - {self.ticker}")
        print(f"{'='*60}")

        # Collect data
        market_data = self.collect_market_data(market_lookback_days)
        macro_data = self.collect_macro_data(macro_lookback_months)
        distribution_data = self.collect_distribution_history()

        # Run prediction
        prediction_data = self.run_prediction_model(market_data, macro_data)

        # Merge everything
        enriched = {
            'metadata': {
                'ticker': self.ticker,
                'enrichment_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'phase3_source': str(self.phase3_file),
                'model_version': self.model_data.get('version', 'unknown')
            },
            'phase3_metrics': self.phase3_data,
            'market_risk': market_data,
            'macro_environment': macro_data,
            'distribution_history': distribution_data,
            'distribution_cut_prediction': prediction_data
        }

        print(f"\n{'='*60}")
        print("✅ ENRICHMENT COMPLETE")
        print(f"{'='*60}")
        print(f"  Market risk collected: {'✓' if 'error' not in market_data else '✗'}")
        print(f"  Macro data collected: {'✓' if 'error' not in macro_data else '✗'}")
        print(f"  Distribution history: {'✓' if distribution_data.get('data_quality') != 'unavailable' else '✗'}")
        print(f"  Prediction generated: {'✓' if 'error' not in prediction_data else '✗'}")

        return enriched

    def save(self, enriched_data: Dict, output_file: str):
        """Save enriched data to JSON file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Custom JSON encoder to handle numpy types
        class NumpyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (np.integer, np.int64, np.int32)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float64, np.float32)):
                    return float(obj)
                elif isinstance(obj, (np.bool_,)):
                    return bool(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return super().default(obj)

        with open(output_path, 'w') as f:
            json.dump(enriched_data, f, indent=2, cls=NumpyEncoder)

        print(f"\n💾 Enriched data saved to: {output_path}")
        print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")


def main():
    """Command-line interface for Phase 4 data enrichment."""
    parser = argparse.ArgumentParser(
        description="Enrich Phase 3 metrics with market, macro, and predictive data"
    )
    parser.add_argument('--phase3', required=True, help='Path to Phase 3 calculated metrics JSON')
    parser.add_argument('--ticker', required=True, help='REIT ticker symbol (e.g., REI-UN.TO)')
    parser.add_argument('--output', help='Output file for enriched data (default: same dir as phase3)')
    parser.add_argument('--model', default='models/distribution_cut_logistic_regression.pkl',
                       help='Path to trained model (default: models/distribution_cut_logistic_regression.pkl)')
    parser.add_argument('--market-lookback', type=int, default=365,
                       help='Market data lookback days (default: 365)')
    parser.add_argument('--macro-lookback', type=int, default=120,
                       help='Macro data lookback months (default: 120)')

    args = parser.parse_args()

    # Default output path
    if not args.output:
        phase3_path = Path(args.phase3)
        args.output = phase3_path.parent / 'phase4_enriched_data.json'

    # Run enrichment
    enricher = Phase4DataEnricher(args.phase3, args.ticker, args.model)
    enriched_data = enricher.enrich(args.market_lookback, args.macro_lookback)
    enricher.save(enriched_data, args.output)

    print(f"\n{'='*60}")
    print("🎉 SUCCESS - Ready for Phase 4 agent")
    print(f"{'='*60}")
    print(f"\nNext step:")
    print(f"  python scripts/generate_final_report.py \\")
    print(f"    --enriched {args.output} \\")
    print(f"    --template templates/credit_opinion_template.md \\")
    print(f"    --output Issuer_Reports/.../reports/credit_opinion.md")

    return 0


if __name__ == '__main__':
    exit(main())
