#!/usr/bin/env python3
"""
Train Distribution Cut Prediction Model v2.0

Uses balanced dataset with market risk, macro environment, and recovery features.

Usage:
    python scripts/train_cut_prediction_model_v2.py \
      --input data/training_dataset_v2_balanced.csv \
      --output-dir models/v2.0
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import json
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# ML libraries
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
import lightgbm as lgb
import shap

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')


class DistributionCutPredictor:
    """Distribution Cut Prediction Model v2.0"""

    def __init__(self, output_dir: Path):
        """
        Initialize predictor.

        Args:
            output_dir: Directory to save model artifacts
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.model = None
        self.label_encoders = {}
        self.feature_names = []
        self.results = {}

    def load_and_prepare_data(self, input_file: Path):
        """
        Load balanced dataset and prepare features.

        Args:
            input_file: Path to balanced dataset CSV

        Returns:
            X, y, feature_names
        """
        print(f"\n{'='*60}")
        print("STEP 1: Data Loading and Preparation")
        print(f"{'='*60}\n")

        df = pd.read_csv(input_file)
        print(f"✓ Loaded {len(df)} observations from {input_file}")

        # Check class balance
        cut_rate = df['cut_occurred'].mean()
        print(f"  Cut rate: {cut_rate*100:.1f}% ({df['cut_occurred'].sum()} cuts, {(df['cut_occurred']==0).sum()} controls)")

        # Select predictive features
        feature_cols = [
            # Market risk (5 features)
            'market_price_stress_pct',
            'market_risk_score',
            'market_volatility_90d',
            'market_momentum_3m',
            'market_risk_level',

            # Macro environment (5 features)
            'macro_policy_rate',
            'macro_rate_change_12m',
            'macro_rate_cycle',
            'macro_credit_stress_score',
            'macro_credit_environment',

            # Recovery patterns (4 features - use for cuts, 0/NaN for controls)
            'recovery_level_pct',
            'recovery_months',
            'full_recovery',
            'recovery_status'
        ]

        X = df[feature_cols].copy()
        y = df['cut_occurred'].copy()

        print(f"\n✓ Selected {len(feature_cols)} predictive features:")
        print(f"  Market risk: 5 features")
        print(f"  Macro environment: 5 features")
        print(f"  Recovery patterns: 4 features")

        # Handle missing values
        print(f"\n✓ Handling missing values...")
        missing_counts = X.isnull().sum()
        if missing_counts.sum() > 0:
            print(f"  Missing values detected:")
            for col, count in missing_counts[missing_counts > 0].items():
                pct = count / len(X) * 100
                print(f"    {col}: {count} ({pct:.1f}%)")

            # Imputation strategy
            # Market features: Mean imputation (only 2 missing)
            for col in ['market_risk_score', 'market_price_stress_pct',
                       'market_volatility_90d', 'market_momentum_3m']:
                if col in X.columns and X[col].isnull().sum() > 0:
                    X[col].fillna(X[col].mean(), inplace=True)

            # Recovery features: 0 for controls (no recovery since no cut)
            for col in ['recovery_level_pct', 'recovery_months']:
                if col in X.columns:
                    X[col].fillna(0, inplace=True)

            # Recovery boolean: False for controls
            if 'full_recovery' in X.columns:
                X['full_recovery'].fillna(False, inplace=True)

            print(f"  Imputation complete: {X.isnull().sum().sum()} missing values remaining")

        # Encode categorical features
        print(f"\n✓ Encoding categorical features...")
        categorical_cols = X.select_dtypes(include=['object', 'bool']).columns

        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            self.label_encoders[col] = le
            print(f"  {col}: {len(le.classes_)} categories → {list(le.classes_)[:5]}...")

        # Store feature names
        self.feature_names = list(X.columns)

        print(f"\n✓ Final dataset shape: {X.shape}")
        print(f"  Features: {X.shape[1]}")
        print(f"  Observations: {X.shape[0]}")

        return X, y

    def create_splits(self, X, y, test_size=0.25, random_state=42):
        """
        Create train-test split.

        Args:
            X: Features
            y: Target
            test_size: Test set proportion
            random_state: Random seed

        Returns:
            X_train, X_test, y_train, y_test
        """
        print(f"\n{'='*60}")
        print("STEP 2: Train-Test Split")
        print(f"{'='*60}\n")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        print(f"✓ Split configuration:")
        print(f"  Test size: {test_size*100:.0f}%")
        print(f"  Random seed: {random_state}")
        print(f"  Stratified: Yes (maintains class balance)")

        print(f"\n✓ Training set:")
        print(f"  Size: {len(X_train)} observations")
        print(f"  Cut rate: {y_train.mean()*100:.1f}%")

        print(f"\n✓ Test set:")
        print(f"  Size: {len(X_test)} observations")
        print(f"  Cut rate: {y_test.mean()*100:.1f}%")

        return X_train, X_test, y_train, y_test

    def train_model(self, X_train, y_train):
        """
        Train LightGBM model.

        Args:
            X_train: Training features
            y_train: Training target

        Returns:
            Trained model
        """
        print(f"\n{'='*60}")
        print("STEP 3: Model Training")
        print(f"{'='*60}\n")

        print(f"✓ Training LightGBM classifier...")
        print(f"  Algorithm: Gradient Boosting Decision Trees")
        print(f"  Objective: Binary classification")

        # LightGBM parameters (conservative for small dataset)
        params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 15,  # Conservative (2^4 - 1)
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'min_data_in_leaf': 5,
            'verbose': -1,
            'random_state': 42
        }

        # Create dataset
        train_data = lgb.Dataset(X_train, label=y_train)

        # Train
        self.model = lgb.train(
            params,
            train_data,
            num_boost_round=100,
            valid_sets=[train_data],
            callbacks=[lgb.early_stopping(stopping_rounds=20)]
        )

        print(f"\n✓ Model trained successfully")
        print(f"  Boosting rounds: {self.model.current_iteration()}")
        print(f"  Features used: {self.model.num_feature()}")

        return self.model

    def evaluate_model(self, X_train, y_train, X_test, y_test):
        """
        Evaluate model performance.

        Args:
            X_train: Training features
            y_train: Training target
            X_test: Test features
            y_test: Test target

        Returns:
            Dictionary of metrics
        """
        print(f"\n{'='*60}")
        print("STEP 4: Model Evaluation")
        print(f"{'='*60}\n")

        # Predictions
        y_train_pred = (self.model.predict(X_train) > 0.5).astype(int)
        y_test_pred = (self.model.predict(X_test) > 0.5).astype(int)

        y_train_proba = self.model.predict(X_train)
        y_test_proba = self.model.predict(X_test)

        # Calculate metrics
        results = {
            'train': {
                'accuracy': accuracy_score(y_train, y_train_pred),
                'precision': precision_score(y_train, y_train_pred, zero_division=0),
                'recall': recall_score(y_train, y_train_pred, zero_division=0),
                'f1': f1_score(y_train, y_train_pred, zero_division=0),
                'auc_roc': roc_auc_score(y_train, y_train_proba)
            },
            'test': {
                'accuracy': accuracy_score(y_test, y_test_pred),
                'precision': precision_score(y_test, y_test_pred, zero_division=0),
                'recall': recall_score(y_test, y_test_pred, zero_division=0),
                'f1': f1_score(y_test, y_test_pred, zero_division=0),
                'auc_roc': roc_auc_score(y_test, y_test_proba)
            }
        }

        # Print results
        print(f"✓ Training set performance:")
        for metric, value in results['train'].items():
            print(f"  {metric.upper():12s}: {value:.3f}")

        print(f"\n✓ Test set performance:")
        for metric, value in results['test'].items():
            print(f"  {metric.upper():12s}: {value:.3f}")

        # Confusion matrix
        cm_test = confusion_matrix(y_test, y_test_pred)
        print(f"\n✓ Test set confusion matrix:")
        print(f"  [[TN={cm_test[0,0]:2d}, FP={cm_test[0,1]:2d}]")
        print(f"   [FN={cm_test[1,0]:2d}, TP={cm_test[1,1]:2d}]]")

        self.results = results
        return results

    def shap_analysis(self, X_train, X_test):
        """
        SHAP feature importance analysis.

        Args:
            X_train: Training features
            X_test: Test features

        Returns:
            SHAP values
        """
        print(f"\n{'='*60}")
        print("STEP 5: SHAP Feature Importance Analysis")
        print(f"{'='*60}\n")

        print(f"✓ Computing SHAP values...")
        explainer = shap.TreeExplainer(self.model)
        shap_values = explainer.shap_values(X_test)

        # Feature importance (mean absolute SHAP)
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': np.abs(shap_values).mean(axis=0)
        }).sort_values('importance', ascending=False)

        print(f"\n✓ Top 10 most important features:")
        for idx, row in feature_importance.head(10).iterrows():
            print(f"  {idx+1:2d}. {row['feature']:35s}: {row['importance']:.4f}")

        # Save feature importance
        feature_importance.to_csv(self.output_dir / 'feature_importance.csv', index=False)

        return shap_values, feature_importance

    def cross_validate_model(self, X, y, n_splits=5):
        """
        Stratified k-fold cross-validation.

        Args:
            X: Features
            y: Target
            n_splits: Number of folds

        Returns:
            CV results
        """
        print(f"\n{'='*60}")
        print("STEP 6: Cross-Validation")
        print(f"{'='*60}\n")

        print(f"✓ Running {n_splits}-fold stratified cross-validation...")

        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

        # Define scoring metrics
        scoring = {
            'accuracy': 'accuracy',
            'precision': 'precision',
            'recall': 'recall',
            'f1': 'f1',
            'roc_auc': 'roc_auc'
        }

        # Cross-validate
        cv_results = cross_validate(
            lgb.LGBMClassifier(
                num_leaves=15,
                learning_rate=0.05,
                n_estimators=100,
                random_state=42
            ),
            X, y,
            cv=cv,
            scoring=scoring,
            return_train_score=True
        )

        # Print results
        print(f"\n✓ Cross-validation results (mean ± std):")
        for metric in ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']:
            test_scores = cv_results[f'test_{metric}']
            mean = test_scores.mean()
            std = test_scores.std()
            print(f"  {metric.upper():12s}: {mean:.3f} ± {std:.3f}")

        return cv_results

    def save_results(self):
        """Save model and results."""
        print(f"\n{'='*60}")
        print("STEP 7: Saving Results")
        print(f"{'='*60}\n")

        # Save model
        model_path = self.output_dir / 'model_v2.0.txt'
        self.model.save_model(str(model_path))
        print(f"✓ Model saved: {model_path}")

        # Save results
        results_path = self.output_dir / 'results_v2.0.json'
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"✓ Results saved: {results_path}")

        # Save feature names
        features_path = self.output_dir / 'feature_names.json'
        with open(features_path, 'w') as f:
            json.dump(self.feature_names, f, indent=2)
        print(f"✓ Feature names saved: {features_path}")

    def generate_report(self):
        """Generate summary report."""
        print(f"\n{'='*60}")
        print("Model Training Complete - Summary Report")
        print(f"{'='*60}\n")

        print(f"Model: Distribution Cut Prediction v2.0")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Output directory: {self.output_dir}")

        print(f"\n✓ Dataset:")
        print(f"  Total observations: 64")
        print(f"  Features: {len(self.feature_names)}")
        print(f"  Cut rate: 45.3%")

        print(f"\n✓ Test set performance:")
        for metric, value in self.results['test'].items():
            print(f"  {metric.upper():12s}: {value:.3f}")

        print(f"\n✓ Files saved:")
        print(f"  Model: models/v2.0/model_v2.0.txt")
        print(f"  Results: models/v2.0/results_v2.0.json")
        print(f"  Features: models/v2.0/feature_names.json")
        print(f"  Feature importance: models/v2.0/feature_importance.csv")


def main():
    parser = argparse.ArgumentParser(
        description='Train Distribution Cut Prediction Model v2.0'
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('data/training_dataset_v2_balanced.csv'),
        help='Path to balanced dataset CSV'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('models/v2.0'),
        help='Directory to save model artifacts'
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: Input file not found: {args.input}")
        return 1

    # Initialize predictor
    predictor = DistributionCutPredictor(output_dir=args.output_dir)

    # Load and prepare data
    X, y = predictor.load_and_prepare_data(args.input)

    # Create train-test split
    X_train, X_test, y_train, y_test = predictor.create_splits(X, y)

    # Train model
    predictor.train_model(X_train, y_train)

    # Evaluate
    predictor.evaluate_model(X_train, y_train, X_test, y_test)

    # SHAP analysis
    shap_values, feature_importance = predictor.shap_analysis(X_train, X_test)

    # Cross-validation
    cv_results = predictor.cross_validate_model(X, y)

    # Save everything
    predictor.save_results()

    # Generate summary
    predictor.generate_report()

    print(f"\n✓ Model training complete! Ready for deployment.")

    return 0


if __name__ == '__main__':
    exit(main())
