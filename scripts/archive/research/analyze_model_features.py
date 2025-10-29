#!/usr/bin/env python3
"""
Feature Importance and SHAP Analysis for Distribution Cut Prediction Model

Analyzes trained LightGBM model to understand:
1. Feature importance rankings
2. SHAP values for interpretability
3. Individual prediction explanations

Usage:
    python scripts/analyze_model_features.py --model models/lightgbm_model_*.pkl
"""

import argparse
import json
from pathlib import Path

import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import shap

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')


def load_model_and_data(model_path: str, dataset_path: str = "data/training_dataset_v2.csv"):
    """Load trained model and prepare data."""
    print(f"📊 Loading model from {model_path}")
    model = joblib.load(model_path)

    print(f"📊 Loading dataset from {dataset_path}")
    df = pd.read_csv(dataset_path)

    # Prepare features (same as training)
    exclude_cols = [
        'ticker', 'cut_date', 'sector', 'target_cut_occurred',
        'ttm_distribution_pre_cut', 'avg_monthly_distribution',
        'dividend_payment_count_ttm', 'current_price', 'current_yield',
        'data_quality', 'notes', 'cash_runway_months', 'self_funding_ratio',
        'risk_level'
    ]

    feature_cols = [col for col in df.columns if col not in exclude_cols]
    X = df[feature_cols].values.astype(float)
    y = df['target_cut_occurred'].values
    tickers = df['ticker'].values

    # Handle missing values (same as training)
    for i in range(X.shape[1]):
        col = X[:, i]
        if np.isnan(col).any():
            median = np.nanmedian(col)
            X[:, i] = np.where(np.isnan(X[:, i]), median, X[:, i])

    return model, X, y, feature_cols, tickers


def analyze_feature_importance(model, feature_names, top_n=15):
    """Extract and analyze feature importance from LightGBM."""
    print("\n" + "="*80)
    print("FEATURE IMPORTANCE ANALYSIS")
    print("="*80)

    # Get feature importance
    importance = model.feature_importances_

    # Create dataframe
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importance
    }).sort_values('importance', ascending=False)

    print(f"\nTop {top_n} Most Important Features:")
    print("="*80)
    for i, row in importance_df.head(top_n).iterrows():
        print(f"{i+1:2d}. {row['feature']:40s} {row['importance']:8.2f}")

    print("="*80)

    return importance_df


def analyze_shap_values(model, X, feature_names, tickers):
    """Compute SHAP values for model interpretability."""
    print("\n" + "="*80)
    print("SHAP VALUE ANALYSIS")
    print("="*80)

    print("\n🔍 Computing SHAP values (this may take a moment)...")

    # Create SHAP explainer
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # If binary classification, shap_values might be a list
    if isinstance(shap_values, list):
        shap_values = shap_values[1]  # Use positive class (cut=1)

    print("✅ SHAP values computed")

    # Feature importance based on mean absolute SHAP values
    shap_importance = np.abs(shap_values).mean(axis=0)
    shap_df = pd.DataFrame({
        'feature': feature_names,
        'mean_abs_shap': shap_importance
    }).sort_values('mean_abs_shap', ascending=False)

    print("\nTop 15 Features by Mean |SHAP|:")
    print("="*80)
    for i, row in shap_df.head(15).iterrows():
        print(f"{i+1:2d}. {row['feature']:40s} {row['mean_abs_shap']:8.4f}")
    print("="*80)

    # Individual predictions with SHAP explanations
    print("\n" + "="*80)
    print("INDIVIDUAL PREDICTION EXPLANATIONS")
    print("="*80)

    predictions = model.predict(X)
    probabilities = model.predict_proba(X)[:, 1]

    for i, ticker in enumerate(tickers):
        pred = "CUT" if predictions[i] == 1 else "NO CUT"
        prob = probabilities[i]

        print(f"\n{ticker}: Predicted={pred}, Probability={prob:.3f}")

        # Top 5 features driving this prediction
        feature_contributions = list(zip(feature_names, shap_values[i]))
        feature_contributions.sort(key=lambda x: abs(x[1]), reverse=True)

        print("  Top 5 Contributing Features:")
        for j, (feat, shap_val) in enumerate(feature_contributions[:5], 1):
            direction = "↑ INCREASES" if shap_val > 0 else "↓ DECREASES"
            print(f"    {j}. {feat:35s} {direction} cut risk by {abs(shap_val):.4f}")

    return shap_values, shap_df


def create_feature_importance_plot(importance_df, output_path="analysis/feature_importance.png"):
    """Create bar plot of feature importance."""
    output_path = Path(output_path)
    output_path.parent.mkdir(exist_ok=True)

    plt.figure(figsize=(10, 8))
    top_features = importance_df.head(15)

    plt.barh(range(len(top_features)), top_features['importance'])
    plt.yticks(range(len(top_features)), top_features['feature'])
    plt.xlabel('Feature Importance')
    plt.title('Top 15 Feature Importance (LightGBM)')
    plt.gca().invert_yaxis()
    plt.tight_layout()

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✅ Saved feature importance plot to: {output_path}")
    plt.close()


def create_shap_summary_plot(shap_values, X, feature_names, output_path="analysis/shap_summary.png"):
    """Create SHAP summary plot."""
    output_path = Path(output_path)
    output_path.parent.mkdir(exist_ok=True)

    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X, feature_names=feature_names, show=False)
    plt.tight_layout()

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved SHAP summary plot to: {output_path}")
    plt.close()


def save_analysis_results(importance_df, shap_df, output_path="analysis/feature_analysis.json"):
    """Save analysis results to JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(exist_ok=True)

    results = {
        'feature_importance': importance_df.to_dict(orient='records'),
        'shap_importance': shap_df.to_dict(orient='records')
    }

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"✅ Saved analysis results to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Analyze model feature importance and SHAP values')
    parser.add_argument('--model', type=str, required=True,
                       help='Path to trained model (.pkl)')
    parser.add_argument('--dataset', type=str, default='data/training_dataset_v2.csv',
                       help='Path to training dataset')
    parser.add_argument('--top-n', type=int, default=15,
                       help='Number of top features to display')

    args = parser.parse_args()

    print("="*80)
    print("FEATURE IMPORTANCE & SHAP ANALYSIS")
    print("="*80)
    print(f"Model: {args.model}")
    print(f"Dataset: {args.dataset}")
    print("="*80)

    # Load model and data
    model, X, y, feature_names, tickers = load_model_and_data(args.model, args.dataset)

    # Feature importance analysis
    importance_df = analyze_feature_importance(model, feature_names, args.top_n)

    # SHAP analysis
    shap_values, shap_df = analyze_shap_values(model, X, feature_names, tickers)

    # Create visualizations
    create_feature_importance_plot(importance_df)
    create_shap_summary_plot(shap_values, X, feature_names)

    # Save results
    save_analysis_results(importance_df, shap_df)

    print("\n✅ Analysis complete!")


if __name__ == "__main__":
    main()
