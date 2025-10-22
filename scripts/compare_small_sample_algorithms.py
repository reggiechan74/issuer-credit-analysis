#!/usr/bin/env python3
"""
Compare algorithms suitable for small sample sizes (n=24).

Tests: Logistic Regression, Naive Bayes, kNN, Decision Tree
Reports cross-validated performance to identify best algorithm.

Usage:
    python scripts/compare_small_sample_algorithms.py
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import make_scorer, f1_score, accuracy_score, precision_score, recall_score, roc_auc_score

def load_data(input_file):
    """Load and prepare dataset."""

    df = pd.read_csv(input_file)

    metadata_cols = ['observation', 'issuer_name', 'reporting_date', 'reporting_period']
    target_col = 'cut_type'
    feature_cols = [col for col in df.columns if col not in metadata_cols + [target_col]]

    X = df[feature_cols].copy()
    y = df[target_col]

    # Encode categorical features
    categorical_cols = X.select_dtypes(include=['object']).columns.tolist()
    for col in categorical_cols:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))

    # Fill missing values
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].median())

    # Encode target
    le_target = LabelEncoder()
    y_encoded = le_target.fit_transform(y)

    return X, y_encoded, feature_cols

def select_features(X, y, k=15):
    """Select top k features using mutual information."""

    selector = SelectKBest(mutual_info_classif, k=min(k, X.shape[1]))
    X_selected = selector.fit_transform(X, y)

    selected_mask = selector.get_support()
    selected_features = X.columns[selected_mask].tolist()

    return X_selected, selected_features, selector

def evaluate_algorithm(name, model, X, y, use_scaling=True):
    """Evaluate algorithm with 5-fold cross-validation."""

    # Optionally scale features
    if use_scaling:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
    else:
        X_scaled = X

    # Scoring metrics
    scoring = {
        'accuracy': make_scorer(accuracy_score),
        'precision': make_scorer(precision_score, zero_division=0),
        'recall': make_scorer(recall_score, zero_division=0),
        'f1': make_scorer(f1_score, zero_division=0),
        'roc_auc': 'roc_auc'  # Use string alias for ROC AUC
    }

    # Stratified CV
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # Cross-validate
    cv_results = cross_validate(
        model, X_scaled, y,
        cv=cv,
        scoring=scoring,
        return_train_score=False,
        error_score='raise'
    )

    # Calculate means and stds
    results = {
        'algorithm': name,
        'accuracy_mean': cv_results['test_accuracy'].mean(),
        'accuracy_std': cv_results['test_accuracy'].std(),
        'precision_mean': cv_results['test_precision'].mean(),
        'precision_std': cv_results['test_precision'].std(),
        'recall_mean': cv_results['test_recall'].mean(),
        'recall_std': cv_results['test_recall'].std(),
        'f1_mean': cv_results['test_f1'].mean(),
        'f1_std': cv_results['test_f1'].std(),
        'roc_auc_mean': cv_results['test_roc_auc'].mean(),
        'roc_auc_std': cv_results['test_roc_auc'].std()
    }

    return results

def main():
    print("=" * 80)
    print("SMALL SAMPLE ALGORITHM COMPARISON (n=24)")
    print("=" * 80)

    # Load data
    print("\n📂 Loading data...")
    X, y, feature_cols = load_data('data/training_dataset_v2_phase1b_expanded.csv')
    print(f"✓ Loaded {len(X)} observations, {len(feature_cols)} features")

    # Feature selection
    print("\n🔍 Selecting top 15 features...")
    X_selected, selected_features, selector = select_features(X, y, k=15)
    print(f"✓ Selected {len(selected_features)} features")

    # Convert to DataFrame for easier handling
    X_df = pd.DataFrame(X_selected, columns=selected_features)

    # Define algorithms to test
    algorithms = [
        {
            'name': 'Logistic Regression',
            'model': LogisticRegression(C=1.0, max_iter=1000, random_state=42, class_weight='balanced'),
            'scaling': True
        },
        {
            'name': 'Gaussian Naive Bayes',
            'model': GaussianNB(),
            'scaling': False  # NB doesn't need scaling
        },
        {
            'name': 'kNN (k=3)',
            'model': KNeighborsClassifier(n_neighbors=3, weights='distance'),
            'scaling': True  # kNN needs scaling
        },
        {
            'name': 'kNN (k=5)',
            'model': KNeighborsClassifier(n_neighbors=5, weights='distance'),
            'scaling': True
        },
        {
            'name': 'Decision Tree (max_depth=3)',
            'model': DecisionTreeClassifier(max_depth=3, random_state=42, class_weight='balanced'),
            'scaling': False  # Trees don't need scaling
        },
        {
            'name': 'Decision Tree (max_depth=5)',
            'model': DecisionTreeClassifier(max_depth=5, random_state=42, class_weight='balanced'),
            'scaling': False
        }
    ]

    print("\n" + "=" * 80)
    print("EVALUATING ALGORITHMS (5-Fold Cross-Validation)")
    print("=" * 80)

    # Evaluate all algorithms
    all_results = []

    for algo in algorithms:
        print(f"\n🔄 Testing {algo['name']}...")

        try:
            results = evaluate_algorithm(
                algo['name'],
                algo['model'],
                X_df,
                y,
                use_scaling=algo['scaling']
            )
            all_results.append(results)

            print(f"  ✓ F1: {results['f1_mean']:.3f} ± {results['f1_std']:.3f}")
            print(f"  ✓ Accuracy: {results['accuracy_mean']:.3f} ± {results['accuracy_std']:.3f}")
            print(f"  ✓ ROC AUC: {results['roc_auc_mean']:.3f} ± {results['roc_auc_std']:.3f}")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue

    # Create results DataFrame
    results_df = pd.DataFrame(all_results)

    # Sort by F1 score
    results_df = results_df.sort_values('f1_mean', ascending=False)

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY (Sorted by F1 Score)")
    print("=" * 80)
    print()

    print(f"{'Rank':<6} {'Algorithm':<30} {'F1':<12} {'Accuracy':<12} {'ROC AUC':<12}")
    print("-" * 80)

    for i, row in results_df.iterrows():
        f1_str = f"{row['f1_mean']:.3f} ± {row['f1_std']:.3f}"
        acc_str = f"{row['accuracy_mean']:.3f} ± {row['accuracy_std']:.3f}"
        auc_str = f"{row['roc_auc_mean']:.3f} ± {row['roc_auc_std']:.3f}"

        rank = list(results_df.index).index(i) + 1
        marker = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "

        print(f"{marker} {rank:<4} {row['algorithm']:<30} {f1_str:<12} {acc_str:<12} {auc_str:<12}")

    # Best algorithm
    best = results_df.iloc[0]

    print("\n" + "=" * 80)
    print("🏆 BEST ALGORITHM")
    print("=" * 80)
    print(f"\nAlgorithm: {best['algorithm']}")
    print(f"F1 Score:  {best['f1_mean']:.3f} ± {best['f1_std']:.3f}")
    print(f"Accuracy:  {best['accuracy_mean']:.3f} ± {best['accuracy_std']:.3f}")
    print(f"Precision: {best['precision_mean']:.3f} ± {best['precision_std']:.3f}")
    print(f"Recall:    {best['recall_mean']:.3f} ± {best['recall_std']:.3f}")
    print(f"ROC AUC:   {best['roc_auc_mean']:.3f} ± {best['roc_auc_std']:.3f}")

    # Comparison to baseline
    baseline_f1 = 0.553
    improvement = (best['f1_mean'] - baseline_f1) / baseline_f1 * 100

    print(f"\n📈 Improvement over market-only baseline:")
    print(f"  Baseline F1: {baseline_f1:.3f}")
    print(f"  Best F1:     {best['f1_mean']:.3f}")
    print(f"  Improvement: +{improvement:.1f}%")

    if best['f1_mean'] >= 0.75:
        print(f"\n✅ TARGET MET: F1 = {best['f1_mean']:.3f} >= 0.75")
    else:
        print(f"\n⚠️  TARGET NOT MET: F1 = {best['f1_mean']:.3f} < 0.75")

    print("\n" + "=" * 80)
    print("✅ Comparison Complete")
    print("=" * 80)

    return results_df

if __name__ == '__main__':
    results = main()
