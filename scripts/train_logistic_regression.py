#!/usr/bin/env python3
"""
Train Logistic Regression model for distribution cut prediction.

Optimized for small sample sizes (n=20-50) with feature selection.

Usage:
    python scripts/train_logistic_regression.py \
        --input data/training_dataset_v2_phase1b_expanded.csv \
        --output models/distribution_cut_logistic_regression.pkl
"""

import argparse
import csv
import json
import pickle
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score
)

def load_and_prepare_data(input_file):
    """Load dataset and prepare features."""

    print("=" * 70)
    print("Loading Training Dataset")
    print("=" * 70)

    df = pd.read_csv(input_file)

    print(f"\n✓ Loaded {len(df)} observations")
    print(f"✓ Total columns: {len(df.columns)}")

    # Identify columns
    metadata_cols = ['observation', 'issuer_name', 'reporting_date', 'reporting_period']
    target_col = 'cut_type'

    feature_cols = [col for col in df.columns if col not in metadata_cols + [target_col]]

    print(f"\n✓ Features: {len(feature_cols)}")
    print(f"✓ Target: {target_col} ({df[target_col].value_counts().to_dict()})")

    # Separate features and target
    X = df[feature_cols].copy()
    y = df[target_col]

    # Encode categorical features
    categorical_cols = X.select_dtypes(include=['object']).columns.tolist()

    if categorical_cols:
        print(f"\n📋 Encoding {len(categorical_cols)} categorical features:")
        for col in categorical_cols:
            print(f"  • {col}")

        label_encoders = {}
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            label_encoders[col] = le
    else:
        label_encoders = {}

    # Handle missing values
    missing_counts = X.isnull().sum()
    missing_features = missing_counts[missing_counts > 0]

    if len(missing_features) > 0:
        print(f"\n⚠️  Missing values detected:")
        for feat, count in missing_features.items():
            pct = count / len(X) * 100
            print(f"  • {feat}: {count} ({pct:.1f}%)")

        # Fill with median
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].median())

        print(f"\n✓ Filled missing values with median")

    # Encode target
    le_target = LabelEncoder()
    y_encoded = le_target.fit_transform(y)

    print(f"\n✓ Target encoding: {dict(zip(le_target.classes_, le_target.transform(le_target.classes_)))}")

    return X, y_encoded, feature_cols, label_encoders, le_target, df

def select_features(X, y, k=15, method='mutual_info'):
    """Select top k features using mutual information or ANOVA F-test."""

    print("\n" + "=" * 70)
    print(f"Feature Selection (top {k} features)")
    print("=" * 70)

    if method == 'mutual_info':
        print("\n🔍 Using Mutual Information for feature selection...")
        selector = SelectKBest(mutual_info_classif, k=min(k, X.shape[1]))
    else:
        print("\n🔍 Using ANOVA F-test for feature selection...")
        selector = SelectKBest(f_classif, k=min(k, X.shape[1]))

    X_selected = selector.fit_transform(X, y)

    # Get selected feature names
    selected_mask = selector.get_support()
    selected_features = X.columns[selected_mask].tolist()
    feature_scores = selector.scores_[selected_mask]

    print(f"\n✓ Selected {len(selected_features)} features:")

    # Sort by score
    feature_score_pairs = list(zip(selected_features, feature_scores))
    feature_score_pairs.sort(key=lambda x: x[1], reverse=True)

    for i, (feat, score) in enumerate(feature_score_pairs, 1):
        print(f"  {i:2d}. {feat:40s} (score: {score:.4f})")

    return X_selected, selected_features, selector

def train_logistic_regression(X, y, feature_names):
    """Train Logistic Regression with 5-fold stratified CV."""

    print("\n" + "=" * 70)
    print("Model Training with 5-Fold Stratified Cross-Validation")
    print("=" * 70)

    # Standardize features (important for logistic regression)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("\n✓ Features standardized (mean=0, std=1)")

    # Create model with L2 regularization (Ridge)
    # C = 1.0 is moderate regularization (good for small samples)
    model = LogisticRegression(
        penalty='l2',
        C=1.0,
        solver='lbfgs',
        max_iter=1000,
        random_state=42,
        class_weight='balanced'  # Handle class imbalance
    )

    print("\n🔄 Running 5-fold cross-validation...")

    # Stratified CV to preserve class distribution
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # Cross-validation scores
    cv_scores = {
        'accuracy': cross_val_score(model, X_scaled, y, cv=cv, scoring='accuracy'),
        'precision': cross_val_score(model, X_scaled, y, cv=cv, scoring='precision'),
        'recall': cross_val_score(model, X_scaled, y, cv=cv, scoring='recall'),
        'f1': cross_val_score(model, X_scaled, y, cv=cv, scoring='f1'),
        'roc_auc': cross_val_score(model, X_scaled, y, cv=cv, scoring='roc_auc')
    }

    print("\n📊 Cross-Validation Results (mean ± std):")
    for metric, scores in cv_scores.items():
        print(f"  • {metric:10s}: {scores.mean():.3f} ± {scores.std():.3f}")

    # Train final model on full dataset
    print("\n🎯 Training final model on full dataset...")
    model.fit(X_scaled, y)

    # Get predictions
    y_pred = model.predict(X_scaled)
    y_pred_proba = model.predict_proba(X_scaled)[:, 1]

    # Feature importance (absolute coefficients)
    feature_importance = pd.DataFrame({
        'feature': feature_names,
        'coefficient': model.coef_[0],
        'abs_coefficient': np.abs(model.coef_[0])
    }).sort_values('abs_coefficient', ascending=False)

    return model, scaler, y_pred, y_pred_proba, feature_importance, cv_scores

def evaluate_model(y_true, y_pred, y_pred_proba, le_target):
    """Evaluate model performance."""

    print("\n" + "=" * 70)
    print("Model Evaluation Results")
    print("=" * 70)

    # Classification report
    print("\n📊 Classification Report:")
    print("-" * 70)
    print(classification_report(
        y_true, y_pred,
        target_names=le_target.classes_,
        zero_division=0
    ))

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    print("\n📊 Confusion Matrix:")
    print("-" * 70)
    print("                 Predicted")
    print("                 Control  Target")
    print(f"Actual Control  {cm[0][0]:7d}  {cm[0][1]:6d}")
    print(f"       Target   {cm[1][0]:7d}  {cm[1][1]:6d}")

    # Metrics
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_true, y_pred_proba)

    print("\n" + "=" * 70)
    print("📈 Performance Summary")
    print("=" * 70)
    print(f"  Accuracy:  {accuracy:.3f}")
    print(f"  Precision: {precision:.3f}")
    print(f"  Recall:    {recall:.3f}")
    print(f"  F1 Score:  {f1:.3f}", end="")

    if f1 >= 0.75:
        print(" ✅")
    elif f1 >= 0.65:
        print(" 🟡")
    else:
        print(" ⚠️")

    print(f"  ROC AUC:   {roc_auc:.3f}")

    # Compare to baseline
    baseline_f1 = 0.553  # Market-only baseline
    improvement = (f1 - baseline_f1) / baseline_f1 * 100

    print("\n" + "=" * 70)
    print("🎯 Target Achievement")
    print("=" * 70)
    print(f"  Baseline F1 (market-only): {baseline_f1:.3f}")
    print(f"  Current F1 (full model):   {f1:.3f}")
    print(f"  Improvement:               {f1 - baseline_f1:+.3f} ({improvement:+.1f}%)")

    if f1 >= 0.75:
        print(f"\n  ✅ TARGET MET: F1 = {f1:.3f} >= 0.75")
    elif f1 >= baseline_f1:
        print(f"\n  🟡 PARTIAL SUCCESS: F1 = {f1:.3f}")
        print(f"  📊 Improvement over baseline: {improvement:+.1f}%")
        print(f"  🎯 Target F1 not met (need 0.75)")
    else:
        print(f"\n  ⚠️  TARGET NOT MET: F1 = {f1:.3f} < 0.75")
        print(f"  📊 Improvement over baseline: {improvement:+.1f}%")
        print(f"  ❌ Model did NOT improve over baseline")

    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'roc_auc': roc_auc
    }

def show_feature_importance(feature_importance, top_n=15):
    """Display top features by absolute coefficient."""

    print("\n" + "=" * 70)
    print(f"🔍 Top {top_n} Most Important Features (by coefficient)")
    print("=" * 70)
    print()

    for i, row in feature_importance.head(top_n).iterrows():
        direction = "+" if row['coefficient'] > 0 else "-"
        bar_length = int(row['abs_coefficient'] / feature_importance['abs_coefficient'].max() * 40)
        bar = '█' * bar_length
        print(f"  {row['feature']:40s} {direction} {bar} {row['abs_coefficient']:.4f}")

def save_model(model, scaler, selector, feature_names, selected_features,
               label_encoders, le_target, metrics, cv_scores, output_file):
    """Save trained model and metadata."""

    model_data = {
        'model': model,
        'scaler': scaler,
        'selector': selector,
        'feature_names': feature_names,
        'selected_features': selected_features,
        'label_encoders': label_encoders,
        'target_encoder': le_target,
        'metrics': metrics,
        'cv_scores': {k: v.tolist() for k, v in cv_scores.items()},
        'model_type': 'logistic_regression',
        'version': '2.1',
        'training_date': datetime.now().isoformat()
    }

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'wb') as f:
        pickle.dump(model_data, f)

    print(f"\n💾 Model saved to: {output_path}")
    print(f"✓ Model type: logistic_regression")
    print(f"✓ Selected features: {len(selected_features)}")
    print(f"✓ Training date: {model_data['training_date']}")

def main():
    parser = argparse.ArgumentParser(description='Train Logistic Regression for distribution cut prediction')
    parser.add_argument('--input', default='data/training_dataset_v2_phase1b_expanded.csv',
                       help='Input training dataset CSV')
    parser.add_argument('--output', default='models/distribution_cut_logistic_regression.pkl',
                       help='Output model file')
    parser.add_argument('--k-features', type=int, default=15,
                       help='Number of features to select (default: 15)')
    parser.add_argument('--selection-method', choices=['mutual_info', 'f_test'], default='mutual_info',
                       help='Feature selection method (default: mutual_info)')

    args = parser.parse_args()

    # Load data
    X, y, feature_cols, label_encoders, le_target, df = load_and_prepare_data(args.input)

    # Feature selection
    X_selected, selected_features, selector = select_features(
        X, y, k=args.k_features, method=args.selection_method
    )

    # Train model
    model, scaler, y_pred, y_pred_proba, feature_importance, cv_scores = train_logistic_regression(
        X_selected, y, selected_features
    )

    # Evaluate
    metrics = evaluate_model(y, y_pred, y_pred_proba, le_target)

    # Show feature importance
    show_feature_importance(feature_importance, top_n=min(15, len(selected_features)))

    # Save model
    save_model(
        model, scaler, selector, feature_cols, selected_features,
        label_encoders, le_target, metrics, cv_scores, args.output
    )

    print("\n" + "=" * 70)
    print("✅ Model Training Complete!")
    print("=" * 70)

    return 0

if __name__ == '__main__':
    exit(main())
