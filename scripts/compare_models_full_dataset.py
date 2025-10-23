#!/usr/bin/env python3
"""
Compare v2.1 vs v2.2 predictions across all 24 training observations.
Shows the impact of sustainable AFCF methodology on risk assessment.
"""

import json
import pickle
import pandas as pd
import numpy as np
from pathlib import Path

# Load both models
model_v21_path = Path("models/distribution_cut_logistic_regression.pkl")
model_v22_path = Path("models/distribution_cut_logistic_regression_v2.2.pkl")

with open(model_v21_path, 'rb') as f:
    model_v21 = pickle.load(f)

with open(model_v22_path, 'rb') as f:
    model_v22 = pickle.load(f)

# Load training dataset
df_train = pd.read_csv("data/training_dataset_v2_sustainable_afcf.csv")

print("="*80)
print("MODEL COMPARISON: v2.1 (Total AFCF) vs v2.2 (Sustainable AFCF)")
print("="*80)
print(f"\nAnalyzing {len(df_train)} observations...")
print()

# Separate features and target
feature_cols = [col for col in df_train.columns if col not in
                ['observation', 'issuer_name', 'reporting_date', 'reporting_period', 'cut_type']]

X = df_train[feature_cols].copy()
y = df_train['cut_type'].copy()

# Encode target
y_encoded = (y == 'target').astype(int)

# Store results
results = []

# Get v2.1 predictions (need to load v2.1's encoders and selector)
try:
    # Apply v2.1's label encoders
    for col, encoder in model_v21['label_encoders'].items():
        if col in X.columns:
            X_v21 = X.copy()
            # Handle unknown categories
            def safe_encode(val):
                try:
                    return encoder.transform([val])[0]
                except ValueError:
                    return encoder.transform([encoder.classes_[0]])[0]
            X_v21[col] = X[col].apply(safe_encode)

    # Fill missing values
    X_v21_filled = X_v21.fillna(0)

    # Transform using v2.1's selector and scaler
    X_v21_selected = model_v21['selector'].transform(X_v21_filled)
    X_v21_scaled = model_v21['scaler'].transform(X_v21_selected)

    # Get v2.1 predictions
    v21_probs = model_v21['model'].predict_proba(X_v21_scaled)[:, 1] * 100

except Exception as e:
    print(f"⚠️  Error with v2.1 predictions: {e}")
    v21_probs = np.zeros(len(X))

# Get v2.2 predictions
try:
    X_v22 = X.copy()

    # Apply v2.2's label encoders
    for col, encoder in model_v22['label_encoders'].items():
        if col in X_v22.columns:
            def safe_encode(val):
                try:
                    return encoder.transform([val])[0]
                except ValueError:
                    return encoder.transform([encoder.classes_[0]])[0]
            X_v22[col] = X[col].apply(safe_encode)

    # Fill missing values
    X_v22_filled = X_v22.fillna(0)

    # Transform using v2.2's selector and scaler
    X_v22_selected = model_v22['selector'].transform(X_v22_filled)
    X_v22_scaled = model_v22['scaler'].transform(X_v22_selected)

    # Get v2.2 predictions
    v22_probs = model_v22['model'].predict_proba(X_v22_scaled)[:, 1] * 100

except Exception as e:
    print(f"⚠️  Error with v2.2 predictions: {e}")
    v22_probs = np.zeros(len(X))

# Build results table
df_results = pd.DataFrame({
    'observation': df_train['observation'],
    'issuer_name': df_train['issuer_name'],
    'reporting_period': df_train['reporting_period'],
    'actual_cut': y,
    'v21_prob': v21_probs,
    'v22_prob': v22_probs,
    'difference': v22_probs - v21_probs,
    'self_funding_ratio': df_train['self_funding_ratio']
})

# Add risk level classifications
def get_risk_level(prob):
    if prob < 5:
        return "Very Low"
    elif prob < 15:
        return "Low"
    elif prob < 30:
        return "Moderate"
    elif prob < 50:
        return "High"
    else:
        return "Very High"

df_results['v21_risk'] = df_results['v21_prob'].apply(get_risk_level)
df_results['v22_risk'] = df_results['v22_prob'].apply(get_risk_level)

# Add risk level change indicator
df_results['risk_change'] = df_results['v21_risk'] != df_results['v22_risk']

# Print summary statistics
print("="*80)
print("SUMMARY STATISTICS")
print("="*80)
print()
print(f"Average v2.1 probability: {df_results['v21_prob'].mean():.1f}%")
print(f"Average v2.2 probability: {df_results['v22_prob'].mean():.1f}%")
print(f"Average difference: {df_results['difference'].mean():.1f}%")
print(f"Max increase: {df_results['difference'].max():.1f}%")
print(f"Max decrease: {df_results['difference'].min():.1f}%")
print()
print(f"Observations with risk level change: {df_results['risk_change'].sum()}/{len(df_results)} ({df_results['risk_change'].sum()/len(df_results)*100:.1f}%)")
print()

# Print by actual outcome
print("="*80)
print("BY ACTUAL OUTCOME")
print("="*80)
print()

for outcome in ['target', 'control']:
    subset = df_results[df_results['actual_cut'] == outcome]
    print(f"{outcome.upper()} (n={len(subset)}):")
    print(f"  v2.1 avg: {subset['v21_prob'].mean():.1f}%")
    print(f"  v2.2 avg: {subset['v22_prob'].mean():.1f}%")
    print(f"  Avg diff: {subset['difference'].mean():+.1f}%")
    print()

# Top 10 largest changes
print("="*80)
print("TOP 10 LARGEST INCREASES (v2.2 more conservative)")
print("="*80)
print()

top_increases = df_results.nlargest(10, 'difference')
for idx, row in top_increases.iterrows():
    print(f"{row['issuer_name'][:40]:40} | {row['reporting_period']:20}")
    print(f"  v2.1: {row['v21_prob']:5.1f}% ({row['v21_risk']:10}) → v2.2: {row['v22_prob']:5.1f}% ({row['v22_risk']:10}) | Δ {row['difference']:+5.1f}%")
    print(f"  Actual: {row['actual_cut']:7} | Self-Funding: {row['self_funding_ratio']:+.2f}x")
    print()

# Risk level transition matrix
print("="*80)
print("RISK LEVEL TRANSITION MATRIX (v2.1 → v2.2)")
print("="*80)
print()

transition = pd.crosstab(df_results['v21_risk'], df_results['v22_risk'],
                         rownames=['v2.1'], colnames=['v2.2'])
print(transition)
print()

# Save detailed results to CSV
output_path = "data/model_comparison_v21_v22_full.csv"
df_results.to_csv(output_path, index=False)
print(f"✓ Detailed results saved to: {output_path}")
print()

# Generate summary for GitHub issue
print("="*80)
print("GITHUB ISSUE UPDATE - COPY/PASTE SECTION")
print("="*80)
print()

print("### Full Dataset Comparison (24 Observations)")
print()
print(f"**Overall Statistics:**")
print(f"- Average prediction increase: **{df_results['difference'].mean():.1f}%** (v2.2 more conservative)")
print(f"- Observations with risk level change: **{df_results['risk_change'].sum()}/{len(df_results)} ({df_results['risk_change'].sum()/len(df_results)*100:.1f}%)**")
print(f"- Maximum increase: **{df_results['difference'].max():.1f}%**")
print()

print("**By Actual Outcome:**")
targets = df_results[df_results['actual_cut'] == 'target']
controls = df_results[df_results['actual_cut'] == 'control']
print(f"- Target cuts (n={len(targets)}): v2.1 avg {targets['v21_prob'].mean():.1f}% → v2.2 avg {targets['v22_prob'].mean():.1f}% (Δ {targets['difference'].mean():+.1f}%)")
print(f"- Controls (n={len(controls)}): v2.1 avg {controls['v21_prob'].mean():.1f}% → v2.2 avg {controls['v22_prob'].mean():.1f}% (Δ {controls['difference'].mean():+.1f}%)")
print()

print("**Top 5 Largest Increases:**")
print()
print("| Rank | Issuer | Period | v2.1 | v2.2 | Change | Actual |")
print("|------|--------|--------|------|------|--------|--------|")
for i, (idx, row) in enumerate(top_increases.head(5).iterrows(), 1):
    issuer_short = row['issuer_name'].replace(' Real Estate Investment Trust', ' REIT').replace('Investment Trust', 'Trust')
    if len(issuer_short) > 25:
        issuer_short = issuer_short[:22] + "..."
    actual_emoji = "🔴" if row['actual_cut'] == 'target' else "🟢"
    print(f"| {i} | {issuer_short} | {row['reporting_period'][:10]} | {row['v21_prob']:.1f}% | {row['v22_prob']:.1f}% | +{row['difference']:.1f}% | {actual_emoji} {row['actual_cut']} |")

print()
print("✓ Full analysis complete")
