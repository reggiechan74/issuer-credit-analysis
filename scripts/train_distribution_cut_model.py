#!/usr/bin/env python3
"""
Distribution Cut Prediction Model - Training Script

Trains machine learning models to predict REIT distribution cuts using
engineered features from training_dataset_v2.csv.

Model Types:
- XGBoost (Gradient Boosting)
- LightGBM (Gradient Boosting)
- Logistic Regression (baseline)

Cross-Validation: Leave-One-Out (LOOCV) given small n=9
Metrics: Precision, Recall, F1-Score, ROC-AUC

Usage:
    python scripts/train_distribution_cut_model.py --model xgboost
    python scripts/train_distribution_cut_model.py --model lightgbm
    python scripts/train_distribution_cut_model.py --model logistic
    python scripts/train_distribution_cut_model.py --model all
"""

import argparse
import json
import warnings
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.model_selection import LeaveOneOut, cross_validate
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    classification_report, confusion_matrix, make_scorer
)
import joblib

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Try importing XGBoost and LightGBM (may not be installed)
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️  XGBoost not installed. Install with: pip install xgboost")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("⚠️  LightGBM not installed. Install with: pip install lightgbm")


class DistributionCutPredictor:
    """
    Distribution cut prediction model trainer and evaluator.

    Handles:
    - Data loading and preprocessing
    - Feature selection
    - Model training with LOOCV
    - Performance evaluation
    - Model persistence
    """

    def __init__(self, dataset_path: str = "data/training_dataset_v2.csv"):
        self.dataset_path = Path(dataset_path)
        self.models = {}
        self.results = {}
        self.scaler = StandardScaler()

        # Load and prepare data
        self.load_data()

    def load_data(self):
        """Load training dataset and prepare features."""
        print(f"📊 Loading training dataset from {self.dataset_path}")

        df = pd.read_csv(self.dataset_path)
        print(f"   Loaded {len(df)} observations with {len(df.columns)} features")

        # Target variable
        self.y = df['target_cut_occurred'].values

        # Remove non-feature columns (non-numeric or target-related)
        exclude_cols = [
            'ticker', 'cut_date', 'sector', 'target_cut_occurred',
            'ttm_distribution_pre_cut', 'avg_monthly_distribution',
            'dividend_payment_count_ttm', 'current_price', 'current_yield',
            'data_quality', 'notes', 'cash_runway_months', 'self_funding_ratio',
            'risk_level'  # Categorical - exclude (already captured in risk_score_scaled)
        ]

        feature_cols = [col for col in df.columns if col not in exclude_cols]
        self.X = df[feature_cols].values
        self.feature_names = feature_cols

        print(f"   Features: {len(self.feature_names)}")
        print(f"   Target distribution: {sum(self.y)} cuts, {len(self.y) - sum(self.y)} no cuts")

        # Handle missing values (impute with median)
        # Convert to float to handle any string/object columns
        self.X = self.X.astype(float)

        for i in range(self.X.shape[1]):
            col = self.X[:, i]
            if np.isnan(col).any():
                median = np.nanmedian(col)
                self.X[:, i] = np.where(np.isnan(self.X[:, i]), median, self.X[:, i])
                print(f"   ⚠️  Imputed missing values in {self.feature_names[i]} with median {median:.2f}")

    def train_xgboost(self, params: dict = None):
        """Train XGBoost model with LOOCV."""
        if not XGBOOST_AVAILABLE:
            print("❌ XGBoost not available")
            return None

        print("\n" + "="*80)
        print("TRAINING: XGBoost Classifier")
        print("="*80)

        # Default hyperparameters optimized for small datasets
        default_params = {
            'max_depth': 3,
            'learning_rate': 0.1,
            'n_estimators': 50,
            'min_child_weight': 1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'scale_pos_weight': 1,  # Balanced classes (6 cuts, 3 controls)
            'random_state': 42,
            'eval_metric': 'logloss'
        }

        if params:
            default_params.update(params)

        model = xgb.XGBClassifier(**default_params)

        # Leave-One-Out Cross-Validation
        results = self._cross_validate(model, "XGBoost")

        # Train on full dataset for deployment
        model.fit(self.X, self.y)

        self.models['xgboost'] = model
        self.results['xgboost'] = results

        return results

    def train_lightgbm(self, params: dict = None):
        """Train LightGBM model with LOOCV."""
        if not LIGHTGBM_AVAILABLE:
            print("❌ LightGBM not available")
            return None

        print("\n" + "="*80)
        print("TRAINING: LightGBM Classifier")
        print("="*80)

        # Default hyperparameters optimized for small datasets
        default_params = {
            'max_depth': 3,
            'learning_rate': 0.1,
            'n_estimators': 50,
            'num_leaves': 7,
            'min_child_samples': 1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'verbose': -1
        }

        if params:
            default_params.update(params)

        model = lgb.LGBMClassifier(**default_params)

        # Leave-One-Out Cross-Validation
        results = self._cross_validate(model, "LightGBM")

        # Train on full dataset for deployment
        model.fit(self.X, self.y)

        self.models['lightgbm'] = model
        self.results['lightgbm'] = results

        return results

    def train_logistic(self, params: dict = None):
        """Train Logistic Regression baseline model with LOOCV."""
        print("\n" + "="*80)
        print("TRAINING: Logistic Regression (Baseline)")
        print("="*80)

        # Default hyperparameters
        default_params = {
            'penalty': 'l2',
            'C': 1.0,
            'max_iter': 1000,
            'random_state': 42
        }

        if params:
            default_params.update(params)

        model = LogisticRegression(**default_params)

        # Scale features for logistic regression
        X_scaled = self.scaler.fit_transform(self.X)

        # Leave-One-Out Cross-Validation
        results = self._cross_validate(model, "Logistic Regression", X_scaled)

        # Train on full dataset for deployment
        model.fit(X_scaled, self.y)

        self.models['logistic'] = model
        self.results['logistic'] = results

        return results

    def _cross_validate(self, model, model_name: str, X=None):
        """
        Perform Leave-One-Out Cross-Validation.

        Args:
            model: Scikit-learn compatible model
            model_name: Name for reporting
            X: Feature matrix (uses self.X if None)

        Returns:
            dict: Cross-validation results
        """
        if X is None:
            X = self.X

        print(f"\n📊 Cross-Validation: Leave-One-Out (LOOCV)")
        print(f"   Training on {len(self.y)} observations")

        loo = LeaveOneOut()

        # Collect predictions
        y_true = []
        y_pred = []
        y_proba = []

        for train_idx, test_idx in loo.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = self.y[train_idx], self.y[test_idx]

            # Train and predict
            model.fit(X_train, y_train)
            pred = model.predict(X_test)[0]
            proba = model.predict_proba(X_test)[0][1]  # Probability of class 1 (cut)

            y_true.append(y_test[0])
            y_pred.append(pred)
            y_proba.append(proba)

        y_true = np.array(y_true)
        y_pred = np.array(y_pred)
        y_proba = np.array(y_proba)

        # Calculate metrics
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        # ROC-AUC (handle case where all predictions are same class)
        try:
            roc_auc = roc_auc_score(y_true, y_proba)
        except ValueError:
            roc_auc = 0.0

        cm = confusion_matrix(y_true, y_pred)

        # Print results
        print(f"\n{'='*60}")
        print(f"{model_name} - LOOCV Results")
        print(f"{'='*60}")
        print(f"Precision: {precision:.3f}")
        print(f"Recall:    {recall:.3f}")
        print(f"F1-Score:  {f1:.3f}")
        print(f"ROC-AUC:   {roc_auc:.3f}")
        print(f"\nConfusion Matrix:")
        print(f"                 Predicted")
        print(f"                 No Cut  Cut")
        print(f"Actual No Cut    {cm[0][0]:4d}    {cm[0][1]:3d}")
        print(f"Actual Cut       {cm[1][0]:4d}    {cm[1][1]:3d}")
        print(f"{'='*60}\n")

        # Detailed classification report
        print("Classification Report:")
        print(classification_report(y_true, y_pred,
                                   target_names=['No Cut', 'Cut'],
                                   zero_division=0))

        return {
            'model_name': model_name,
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'roc_auc': float(roc_auc),
            'confusion_matrix': cm.tolist(),
            'y_true': y_true.tolist(),
            'y_pred': y_pred.tolist(),
            'y_proba': y_proba.tolist()
        }

    def save_model(self, model_name: str, output_dir: str = "models"):
        """Save trained model and results."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        if model_name not in self.models:
            print(f"❌ Model '{model_name}' not trained")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save model
        model_file = output_path / f"{model_name}_model_{timestamp}.pkl"
        joblib.dump(self.models[model_name], model_file)
        print(f"✅ Saved model to: {model_file}")

        # Save scaler if logistic regression
        if model_name == 'logistic':
            scaler_file = output_path / f"{model_name}_scaler_{timestamp}.pkl"
            joblib.dump(self.scaler, scaler_file)
            print(f"✅ Saved scaler to: {scaler_file}")

        # Save results
        results_file = output_path / f"{model_name}_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results[model_name], f, indent=2)
        print(f"✅ Saved results to: {results_file}")

    def compare_models(self):
        """Compare all trained models."""
        if not self.results:
            print("❌ No models trained yet")
            return

        print("\n" + "="*80)
        print("MODEL COMPARISON")
        print("="*80)

        comparison = []
        for model_name, results in self.results.items():
            comparison.append({
                'Model': results['model_name'],
                'Precision': f"{results['precision']:.3f}",
                'Recall': f"{results['recall']:.3f}",
                'F1-Score': f"{results['f1_score']:.3f}",
                'ROC-AUC': f"{results['roc_auc']:.3f}"
            })

        df = pd.DataFrame(comparison)
        print(df.to_string(index=False))
        print("="*80)

        # Recommend best model
        best_f1 = max(self.results.items(), key=lambda x: x[1]['f1_score'])
        print(f"\n🏆 Best Model (by F1-Score): {best_f1[0].upper()}")
        print(f"   F1-Score: {best_f1[1]['f1_score']:.3f}")


def main():
    parser = argparse.ArgumentParser(description='Train distribution cut prediction models')
    parser.add_argument('--model', type=str, default='all',
                       choices=['xgboost', 'lightgbm', 'logistic', 'all'],
                       help='Model to train (default: all)')
    parser.add_argument('--dataset', type=str, default='data/training_dataset_v2.csv',
                       help='Path to training dataset')
    parser.add_argument('--save', action='store_true',
                       help='Save trained models')

    args = parser.parse_args()

    print("="*80)
    print("REIT DISTRIBUTION CUT PREDICTION - MODEL TRAINING")
    print("="*80)
    print(f"Dataset: {args.dataset}")
    print(f"Model(s): {args.model}")
    print("="*80)

    # Initialize predictor
    predictor = DistributionCutPredictor(args.dataset)

    # Train models
    if args.model in ['xgboost', 'all']:
        predictor.train_xgboost()

    if args.model in ['lightgbm', 'all']:
        predictor.train_lightgbm()

    if args.model in ['logistic', 'all']:
        predictor.train_logistic()

    # Compare models if multiple trained
    if args.model == 'all':
        predictor.compare_models()

    # Save models if requested
    if args.save:
        for model_name in predictor.models.keys():
            predictor.save_model(model_name)

    print("\n✅ Training complete!")


if __name__ == "__main__":
    main()
