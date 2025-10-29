#!/usr/bin/env python3
"""
Train distribution cut prediction model v2.0 with fundamentals + market + macro features.

Uses LightGBM with 5-fold stratified cross-validation.

Target: F1 Score ≥ 0.75 (vs baseline 0.553 from market-only model)

Usage:
    python scripts/train_distribution_cut_model.py \
        --input data/training_dataset_v2_phase1b.csv \
        --output models/distribution_cut_v2_phase1b.pkl
"""

import argparse
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import lightgbm as lgb

def load_and_prepare_data(input_file):
    """Load training dataset and prepare features."""
    
    print("="*70)
    print("Loading Training Dataset")
    print("="*70)
    
    # Load data
    df = pd.read_csv(input_file)
    print(f"\n✓ Loaded {len(df)} observations")
    print(f"✓ Total columns: {len(df.columns)}")
    
    # Separate features and target
    metadata_cols = ['observation', 'issuer_name', 'reporting_date', 'reporting_period']
    target_col = 'cut_type'
    
    feature_cols = [col for col in df.columns if col not in metadata_cols + [target_col]]
    
    X = df[feature_cols].copy()
    y = df[target_col]
    
    print(f"\n✓ Features: {len(feature_cols)}")
    print(f"✓ Target: {target_col} ({y.value_counts().to_dict()})")
    
    # Handle categorical features
    categorical_cols = X.select_dtypes(include=['object']).columns.tolist()
    
    if categorical_cols:
        print(f"\n📋 Encoding {len(categorical_cols)} categorical features:")
        label_encoders = {}
        
        for col in categorical_cols:
            print(f"  • {col}")
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            label_encoders[col] = le
    else:
        label_encoders = {}
        print("\n✓ No categorical features to encode")
    
    # Handle missing values
    missing_counts = X.isnull().sum()
    if missing_counts.sum() > 0:
        print(f"\n⚠️  Missing values detected:")
        for col in missing_counts[missing_counts > 0].index:
            print(f"  • {col}: {missing_counts[col]} ({missing_counts[col]/len(X)*100:.1f}%)")
        
        # Fill with median for numeric columns
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].median())
        print(f"\n✓ Filled missing values with median")
    else:
        print(f"\n✓ No missing values")
    
    # Encode target
    le_target = LabelEncoder()
    y_encoded = le_target.fit_transform(y)
    
    print(f"\n✓ Target encoding: {dict(zip(le_target.classes_, le_target.transform(le_target.classes_)))}")
    
    return X, y_encoded, feature_cols, label_encoders, le_target, df

def train_model(X, y, feature_cols):
    """Train LightGBM model with 5-fold stratified CV."""
    
    print("\n" + "="*70)
    print("Model Training with 5-Fold Stratified Cross-Validation")
    print("="*70)
    
    # LightGBM parameters
    params = {
        'objective': 'binary',
        'metric': 'binary_logloss',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'random_state': 42
    }
    
    # 5-fold stratified CV
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    # Scoring metrics
    scoring = {
        'accuracy': 'accuracy',
        'precision': 'precision',
        'recall': 'recall',
        'f1': 'f1',
        'roc_auc': 'roc_auc'
    }
    
    # Create LightGBM dataset
    train_data = lgb.Dataset(X, label=y)
    
    # Cross-validation
    print(f"\n🔄 Running 5-fold cross-validation...")
    
    cv_results = lgb.cv(
        params,
        train_data,
        num_boost_round=100,
        nfold=5,
        stratified=True,
        shuffle=True,
        metrics='binary_logloss',
        seed=42,
        callbacks=[lgb.early_stopping(stopping_rounds=10, verbose=False)]
    )
    
    # Get best iteration
    best_iteration = len(cv_results['valid binary_logloss-mean'])
    best_score = cv_results['valid binary_logloss-mean'][-1]
    
    print(f"✓ Best iteration: {best_iteration}")
    print(f"✓ Best log loss: {best_score:.4f}")
    
    # Train final model on full dataset
    print(f"\n🎯 Training final model on full dataset...")
    final_model = lgb.train(
        params,
        train_data,
        num_boost_round=best_iteration
    )
    
    # Get predictions for evaluation
    y_pred_proba = final_model.predict(X)
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    return final_model, y_pred, y_pred_proba, cv_results

def evaluate_model(y_true, y_pred, y_pred_proba, le_target):
    """Evaluate model performance."""
    
    print("\n" + "="*70)
    print("Model Evaluation Results")
    print("="*70)
    
    # Classification report
    print("\n📊 Classification Report:")
    print("-" * 70)
    report = classification_report(y_true, y_pred, target_names=le_target.classes_, digits=3)
    print(report)
    
    # Confusion matrix
    print("\n📊 Confusion Matrix:")
    print("-" * 70)
    cm = confusion_matrix(y_true, y_pred)
    print(f"                 Predicted")
    print(f"                 Control  Target")
    print(f"Actual Control   {cm[0,0]:7d}  {cm[0,1]:7d}")
    print(f"       Target    {cm[1,0]:7d}  {cm[1,1]:7d}")
    
    # Extract metrics
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred)
    recall = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    roc_auc = roc_auc_score(y_true, y_pred_proba)
    
    print("\n" + "="*70)
    print("📈 Performance Summary")
    print("="*70)
    print(f"  Accuracy:  {accuracy:.3f}")
    print(f"  Precision: {precision:.3f}")
    print(f"  Recall:    {recall:.3f}")
    print(f"  F1 Score:  {f1:.3f} {'🎉' if f1 >= 0.75 else '⚠️'}")
    print(f"  ROC AUC:   {roc_auc:.3f}")
    
    # Compare to target
    print("\n" + "="*70)
    print("🎯 Target Achievement")
    print("="*70)
    baseline_f1 = 0.553
    print(f"  Baseline F1 (market-only): {baseline_f1:.3f}")
    print(f"  Current F1 (full model):   {f1:.3f}")
    print(f"  Improvement:               {(f1-baseline_f1):.3f} ({(f1-baseline_f1)/baseline_f1*100:+.1f}%)")
    
    if f1 >= 0.75:
        print(f"\n  ✅ TARGET ACHIEVED! F1 = {f1:.3f} ≥ 0.75")
        print(f"  ✅ Hypothesis VALIDATED: Fundamentals improve model performance")
        print(f"\n  📍 Recommendation: Proceed with full dataset expansion (n=20-30 REITs)")
    else:
        print(f"\n  ⚠️  TARGET NOT MET: F1 = {f1:.3f} < 0.75")
        print(f"  📊 Improvement over baseline: {(f1-baseline_f1)/baseline_f1*100:+.1f}%")
        
        if f1 > baseline_f1:
            print(f"  ✓ Model improved over baseline - partial success")
            print(f"\n  📍 Recommendation: Review feature importance, consider:")
            print(f"     - Feature engineering (interaction terms)")
            print(f"     - Hyperparameter tuning")
            print(f"     - Additional features (distribution history, recovery patterns)")
        else:
            print(f"  ❌ Model did NOT improve over baseline")
            print(f"\n  📍 Recommendation: Investigate fundamental hypothesis")
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'roc_auc': roc_auc
    }

def show_feature_importance(model, feature_cols, top_n=20):
    """Display feature importance."""
    
    print("\n" + "="*70)
    print(f"🔍 Top {top_n} Most Important Features")
    print("="*70)
    
    # Get feature importance
    importance = model.feature_importance(importance_type='gain')
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': importance
    }).sort_values('importance', ascending=False)
    
    # Display top N
    print("\n")
    max_importance = feature_importance['importance'].max()

    if max_importance > 0 and not pd.isna(max_importance):
        for i, row in feature_importance.head(top_n).iterrows():
            bar_length = int(row['importance'] / max_importance * 40)
            bar = '█' * bar_length
            print(f"  {row['feature']:35s} {bar} {row['importance']:,.0f}")
    else:
        print("  ⚠️  All features have zero importance (model did not split on any features)")
        for i, row in feature_importance.head(top_n).iterrows():
            print(f"  {row['feature']:35s} {row['importance']:,.0f}")
    
    return feature_importance

def save_model(model, feature_cols, label_encoders, le_target, metrics, output_file):
    """Save trained model and metadata."""
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    model_package = {
        'model': model,
        'feature_cols': feature_cols,
        'label_encoders': label_encoders,
        'target_encoder': le_target,
        'metrics': metrics,
        'version': '2.0',
        'training_date': pd.Timestamp.now().isoformat()
    }
    
    with open(output_path, 'wb') as f:
        pickle.dump(model_package, f)
    
    print(f"\n💾 Model saved to: {output_file}")
    print(f"✓ Model version: 2.0")
    print(f"✓ Features: {len(feature_cols)}")
    print(f"✓ Training date: {model_package['training_date']}")

def main():
    parser = argparse.ArgumentParser(description='Train distribution cut prediction model')
    parser.add_argument('--input', default='data/training_dataset_v2_phase1b.csv',
                       help='Input training dataset CSV')
    parser.add_argument('--output', default='models/distribution_cut_v2_phase1b.pkl',
                       help='Output model file')
    
    args = parser.parse_args()
    
    # Load and prepare data
    X, y, feature_cols, label_encoders, le_target, df = load_and_prepare_data(args.input)
    
    # Train model
    model, y_pred, y_pred_proba, cv_results = train_model(X, y, feature_cols)
    
    # Evaluate
    metrics = evaluate_model(y, y_pred, y_pred_proba, le_target)
    
    # Feature importance
    feature_importance = show_feature_importance(model, feature_cols, top_n=20)
    
    # Save model
    save_model(model, feature_cols, label_encoders, le_target, metrics, args.output)
    
    print("\n" + "="*70)
    print("✅ Model Training Complete!")
    print("="*70)
    
    return 0

if __name__ == '__main__':
    exit(main())
