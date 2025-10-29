#!/usr/bin/env python3
"""
Targeted LightGBM Hyperparameter Tuning for Distribution Cut Prediction

Fast, targeted search focusing on regularization and complexity reduction
to eliminate false positives while maintaining perfect recall.

Usage:
    python scripts/tune_lightgbm_targeted.py
"""

import json
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import LeaveOneOut
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix
)
import lightgbm as lgb

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')


def load_and_prepare_data(dataset_path="data/training_dataset_v2.csv"):
    """Load and preprocess training data."""
    print(f"📊 Loading dataset from {dataset_path}")
    df = pd.read_csv(dataset_path)

    # Exclude non-feature columns
    exclude_cols = [
        'ticker', 'cut_date', 'sector', 'target_cut_occurred',
        'ttm_distribution_pre_cut', 'avg_monthly_distribution',
        'dividend_payment_count_ttm', 'current_price', 'current_yield',
        'data_quality', 'notes', 'cash_runway_months', 'self_funding_ratio',
        'risk_level'
    ]

    feature_cols = [col for col in df.columns if col not in exclude_cols]
    X = df[feature_cols].values
    y = df['target_cut_occurred'].values
    tickers = df['ticker'].values

    # Convert to float and handle missing values
    X = X.astype(float)
    for i in range(X.shape[1]):
        col = X[:, i]
        if np.isnan(col).any():
            median = np.nanmedian(col)
            X[:, i] = np.where(np.isnan(X[:, i]), median, X[:, i])

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, y, feature_cols, tickers, scaler


def evaluate_with_loocv(params, X, y):
    """Evaluate model using LOOCV."""
    loo = LeaveOneOut()
    y_pred_list = []
    y_proba_list = []

    for train_idx, test_idx in loo.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        model = lgb.LGBMClassifier(**params, objective='binary', random_state=42, verbose=-1)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)[0]
        y_proba = model.predict_proba(X_test)[0, 1]

        y_pred_list.append(y_pred)
        y_proba_list.append(y_proba)

    y_pred = np.array(y_pred_list)
    y_proba = np.array(y_proba_list)

    # Calculate metrics
    precision = precision_score(y, y_pred, zero_division=0)
    recall = recall_score(y, y_pred, zero_division=0)
    f1 = f1_score(y, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y, y_proba) if len(np.unique(y_pred)) > 1 else 0.5

    # Custom score: F1 with heavy penalty for recall < 1.0
    score = f1 if recall == 1.0 else f1 * 0.3

    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'roc_auc': roc_auc,
        'custom_score': score,
        'y_pred': y_pred.tolist(),
        'y_proba': y_proba.tolist()
    }


def targeted_search(X, y):
    """
    Targeted hyperparameter search focusing on:
    1. High regularization to reduce false positives
    2. Low complexity to prevent overfitting
    3. Conservative learning
    """
    print("\n" + "="*80)
    print("TARGETED HYPERPARAMETER SEARCH")
    print("="*80)

    # Targeted parameter combinations (focusing on regularization + simplicity)
    param_configs = []

    # Strategy 1: High regularization with simple trees
    for reg_alpha in [0.5, 1.0, 2.0, 5.0]:
        for reg_lambda in [0.5, 1.0, 2.0, 5.0]:
            for num_leaves in [3, 5, 7]:
                param_configs.append({
                    'num_leaves': num_leaves,
                    'max_depth': 3,
                    'min_child_samples': 5,
                    'learning_rate': 0.05,
                    'n_estimators': 100,
                    'reg_alpha': reg_alpha,
                    'reg_lambda': reg_lambda,
                    'subsample': 0.8,
                    'colsample_bytree': 0.8
                })

    # Strategy 2: Very simple trees with moderate regularization
    for num_leaves in [3, 5]:
        for max_depth in [2, 3]:
            for min_child_samples in [5, 10]:
                param_configs.append({
                    'num_leaves': num_leaves,
                    'max_depth': max_depth,
                    'min_child_samples': min_child_samples,
                    'learning_rate': 0.05,
                    'n_estimators': 100,
                    'reg_alpha': 1.0,
                    'reg_lambda': 1.0,
                    'subsample': 0.8,
                    'colsample_bytree': 0.8
                })

    # Strategy 3: Low learning rate with regularization
    for learning_rate in [0.01, 0.03, 0.05]:
        for n_estimators in [100, 200, 300]:
            param_configs.append({
                'num_leaves': 5,
                'max_depth': 3,
                'min_child_samples': 5,
                'learning_rate': learning_rate,
                'n_estimators': n_estimators,
                'reg_alpha': 1.0,
                'reg_lambda': 1.0,
                'subsample': 0.8,
                'colsample_bytree': 0.8
            })

    print(f"Total configurations to test: {len(param_configs)}")
    print(f"With LOOCV (n=9): {len(param_configs) * 9} model fits\n")

    # Evaluate all configurations
    results = []
    best_score = -1
    best_params = None
    best_metrics = None

    for i, params in enumerate(param_configs, 1):
        if i % 10 == 0:
            print(f"Progress: {i}/{len(param_configs)} configurations tested...")

        metrics = evaluate_with_loocv(params, X, y)
        metrics['params'] = params

        results.append(metrics)

        if metrics['custom_score'] > best_score:
            best_score = metrics['custom_score']
            best_params = params
            best_metrics = metrics

    print(f"\n✅ Search complete! Tested {len(param_configs)} configurations")

    return best_params, best_metrics, results


def print_results(best_params, best_metrics, baseline_path="models/lightgbm_results_20251022_023051.json"):
    """Print detailed results and comparison."""
    print("\n" + "="*80)
    print("BEST PARAMETERS")
    print("="*80)
    for param, value in best_params.items():
        print(f"  {param:20s} = {value}")
    print("="*80)

    print("\n" + "="*80)
    print("BEST MODEL PERFORMANCE (LOOCV)")
    print("="*80)
    print(f"{'Metric':<20s} {'Value':>10s}")
    print("-" * 30)
    print(f"{'Precision':<20s} {best_metrics['precision']:>10.4f}")
    print(f"{'Recall':<20s} {best_metrics['recall']:>10.4f}")
    print(f"{'F1-Score':<20s} {best_metrics['f1_score']:>10.4f}")
    print(f"{'ROC-AUC':<20s} {best_metrics['roc_auc']:>10.4f}")
    print("-" * 30)

    # Compare with baseline
    if Path(baseline_path).exists():
        with open(baseline_path) as f:
            baseline = json.load(f)

        print("\n📊 Comparison with Baseline:")
        print("="*80)
        print(f"{'Metric':<20s} {'Baseline':>12s} {'Tuned':>12s} {'Change':>12s}")
        print("-" * 56)
        print(f"{'Precision':<20s} {baseline['precision']:>12.4f} {best_metrics['precision']:>12.4f} "
              f"{best_metrics['precision'] - baseline['precision']:>+12.4f}")
        print(f"{'Recall':<20s} {baseline['recall']:>12.4f} {best_metrics['recall']:>12.4f} "
              f"{best_metrics['recall'] - baseline['recall']:>+12.4f}")
        print(f"{'F1-Score':<20s} {baseline['f1_score']:>12.4f} {best_metrics['f1_score']:>12.4f} "
              f"{best_metrics['f1_score'] - baseline['f1_score']:>+12.4f}")
        print(f"{'ROC-AUC':<20s} {baseline['roc_auc']:>12.4f} {best_metrics['roc_auc']:>12.4f} "
              f"{best_metrics['roc_auc'] - baseline['roc_auc']:>+12.4f}")
        print("="*80)

    # Goal achievement
    if best_metrics['f1_score'] >= 0.90:
        print("\n🎉 TARGET ACHIEVED: F1-Score ≥ 0.90!")
    else:
        print(f"\n⚠️  Target not achieved (F1 = {best_metrics['f1_score']:.4f} < 0.90)")


def save_results(best_params, best_metrics, X, y, feature_names, scaler):
    """Save tuned model and results."""
    output_dir = Path("models")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Train final model on all data
    model = lgb.LGBMClassifier(**best_params, objective='binary', random_state=42, verbose=-1)
    model.fit(X, y)

    # Save model
    model_path = output_dir / f"lightgbm_tuned_targeted_{timestamp}.pkl"
    joblib.dump(model, model_path)
    print(f"\n✅ Saved tuned model to: {model_path}")

    # Save scaler
    scaler_path = output_dir / f"lightgbm_tuned_scaler_{timestamp}.pkl"
    joblib.dump(scaler, scaler_path)
    print(f"✅ Saved scaler to: {scaler_path}")

    # Save results
    results_data = {
        'model_name': 'LightGBM (Tuned - Targeted)',
        'best_params': best_params,
        'precision': best_metrics['precision'],
        'recall': best_metrics['recall'],
        'f1_score': best_metrics['f1_score'],
        'roc_auc': best_metrics['roc_auc'],
        'y_pred': best_metrics['y_pred'],
        'y_proba': best_metrics['y_proba']
    }

    results_path = output_dir / f"lightgbm_tuned_results_{timestamp}.json"
    with open(results_path, 'w') as f:
        json.dump(results_data, f, indent=2)
    print(f"✅ Saved results to: {results_path}")

    return model


def main():
    print("="*80)
    print("TARGETED LIGHTGBM HYPERPARAMETER TUNING")
    print("="*80)
    print("Goal: F1-Score ≥ 0.90 by reducing false positives")
    print("Strategy: High regularization + Low complexity")
    print("="*80)

    # Load data
    X, y, feature_names, tickers, scaler = load_and_prepare_data()

    # Targeted search
    best_params, best_metrics, all_results = targeted_search(X, y)

    # Print results
    print_results(best_params, best_metrics)

    # Save model and results
    model = save_results(best_params, best_metrics, X, y, feature_names, scaler)

    # Analyze feature importance
    print("\n" + "="*80)
    print("TOP 10 FEATURE IMPORTANCE (TUNED MODEL)")
    print("="*80)
    importance = model.feature_importances_
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importance
    }).sort_values('importance', ascending=False)

    for i, row in importance_df.head(10).iterrows():
        print(f"{i+1:2d}. {row['feature']:40s} {row['importance']:8.2f}")
    print("="*80)

    print("\n✅ Targeted hyperparameter tuning complete!")


if __name__ == "__main__":
    main()
