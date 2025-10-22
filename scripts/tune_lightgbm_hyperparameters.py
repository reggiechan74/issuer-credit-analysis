#!/usr/bin/env python3
"""
LightGBM Hyperparameter Tuning for Distribution Cut Prediction

Goal: Improve F1-Score from 0.857 to >0.90 by reducing false positives
while maintaining perfect recall.

Strategy:
1. GridSearchCV with LOOCV for small dataset (n=9)
2. Focus on regularization to reduce false positives
3. Custom scoring to balance precision and recall
4. Analyze feature importance changes with tuned model

Usage:
    python scripts/tune_lightgbm_hyperparameters.py
"""

import argparse
import json
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import GridSearchCV, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix, make_scorer
)
import lightgbm as lgb

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')


class LightGBMTuner:
    """Hyperparameter tuning for LightGBM distribution cut predictor."""

    def __init__(self, dataset_path: str = "data/training_dataset_v2.csv"):
        self.dataset_path = Path(dataset_path)
        self.scaler = StandardScaler()
        self.best_model = None
        self.best_params = None
        self.tuning_results = {}
        self.load_data()

    def load_data(self):
        """Load and preprocess training data."""
        print(f"📊 Loading dataset from {self.dataset_path}")
        df = pd.read_csv(self.dataset_path)

        print(f"Dataset shape: {df.shape}")
        print(f"Target distribution: {df['target_cut_occurred'].value_counts().to_dict()}")

        # Exclude non-feature columns
        exclude_cols = [
            'ticker', 'cut_date', 'sector', 'target_cut_occurred',
            'ttm_distribution_pre_cut', 'avg_monthly_distribution',
            'dividend_payment_count_ttm', 'current_price', 'current_yield',
            'data_quality', 'notes', 'cash_runway_months', 'self_funding_ratio',
            'risk_level'  # Categorical
        ]

        # Select features
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        self.feature_names = feature_cols

        print(f"Number of features: {len(feature_cols)}")

        # Prepare X and y
        self.X = df[feature_cols].values
        self.y = df['target_cut_occurred'].values
        self.tickers = df['ticker'].values

        # Convert to float and handle missing values
        self.X = self.X.astype(float)
        for i in range(self.X.shape[1]):
            col = self.X[:, i]
            if np.isnan(col).any():
                median = np.nanmedian(col)
                self.X[:, i] = np.where(np.isnan(self.X[:, i]), median, self.X[:, i])

        # Scale features
        self.X_scaled = self.scaler.fit_transform(self.X)

        print("✅ Data loaded and preprocessed")

    def get_param_grid(self, search_type: str = "focused"):
        """
        Define hyperparameter search space.

        Args:
            search_type: 'focused' (fewer params, faster) or 'extensive' (more params, slower)
        """
        if search_type == "focused":
            # Focused grid targeting false positive reduction
            param_grid = {
                'num_leaves': [7, 15, 31],                    # Reduce complexity
                'max_depth': [3, 5, 7],                        # Limit tree depth
                'min_child_samples': [3, 5, 10],               # Require more samples per leaf
                'learning_rate': [0.01, 0.05, 0.1],            # Learning rate
                'n_estimators': [50, 100, 200],                # Number of trees
                'reg_alpha': [0, 0.1, 0.5, 1.0],               # L1 regularization
                'reg_lambda': [0, 0.1, 0.5, 1.0],              # L2 regularization
                'subsample': [0.7, 0.8, 1.0],                  # Row sampling
                'colsample_bytree': [0.7, 0.8, 1.0],           # Feature sampling
            }
        else:
            # Extensive grid for thorough search
            param_grid = {
                'num_leaves': [7, 15, 31, 50],
                'max_depth': [3, 5, 7, 10, -1],
                'min_child_samples': [1, 3, 5, 10, 20],
                'learning_rate': [0.001, 0.01, 0.05, 0.1, 0.2],
                'n_estimators': [50, 100, 200, 300],
                'reg_alpha': [0, 0.01, 0.1, 0.5, 1.0, 2.0],
                'reg_lambda': [0, 0.01, 0.1, 0.5, 1.0, 2.0],
                'subsample': [0.5, 0.7, 0.8, 1.0],
                'colsample_bytree': [0.5, 0.7, 0.8, 1.0],
            }

        return param_grid

    def custom_f1_scorer(self, y_true, y_pred):
        """Custom F1 scorer with recall penalty for GridSearchCV."""
        f1 = f1_score(y_true, y_pred)
        recall = recall_score(y_true, y_pred)

        # Penalize if recall drops below 1.0 (we want to maintain perfect recall)
        if recall < 1.0:
            f1 *= 0.5  # Heavy penalty for missing actual cuts

        return f1

    def tune_hyperparameters(self, search_type: str = "focused", n_jobs: int = -1):
        """
        Perform hyperparameter tuning using GridSearchCV.

        Args:
            search_type: 'focused' or 'extensive'
            n_jobs: Number of parallel jobs (-1 = all cores)
        """
        print("\n" + "="*80)
        print("HYPERPARAMETER TUNING")
        print("="*80)
        print(f"Search type: {search_type}")

        # Get parameter grid
        param_grid = self.get_param_grid(search_type)

        total_combinations = np.prod([len(v) for v in param_grid.values()])
        print(f"Total parameter combinations: {total_combinations:,}")
        print(f"With LOOCV (n=9): {total_combinations * 9:,} model fits")

        if total_combinations > 1000:
            print("⚠️  WARNING: Large search space will take significant time")
            print("    Consider using search_type='focused' for faster results")

        # Create base model
        base_model = lgb.LGBMClassifier(
            objective='binary',
            random_state=42,
            verbose=-1
        )

        # Create custom scorer
        scorer = make_scorer(self.custom_f1_scorer)

        # Setup GridSearchCV with LOOCV
        print("\n🔍 Starting grid search with LOOCV...")
        grid_search = GridSearchCV(
            estimator=base_model,
            param_grid=param_grid,
            scoring=scorer,
            cv=LeaveOneOut(),
            n_jobs=n_jobs,
            verbose=2,
            return_train_score=True
        )

        # Fit grid search
        grid_search.fit(self.X_scaled, self.y)

        # Store best model and params
        self.best_model = grid_search.best_estimator_
        self.best_params = grid_search.best_params_

        print("\n✅ Grid search complete!")
        print("\nBest Parameters:")
        print("="*80)
        for param, value in self.best_params.items():
            print(f"  {param:20s} = {value}")
        print("="*80)

        # Evaluate best model
        self._evaluate_best_model()

        # Store tuning results
        self.tuning_results = {
            'best_params': self.best_params,
            'best_score': float(grid_search.best_score_),
            'cv_results': {
                'mean_test_score': grid_search.cv_results_['mean_test_score'].tolist(),
                'std_test_score': grid_search.cv_results_['std_test_score'].tolist(),
                'params': [str(p) for p in grid_search.cv_results_['params']]
            }
        }

        return self.best_model, self.best_params

    def _evaluate_best_model(self):
        """Evaluate best model using LOOCV."""
        print("\n" + "="*80)
        print("BEST MODEL EVALUATION (LOOCV)")
        print("="*80)

        loo = LeaveOneOut()
        y_pred_list = []
        y_true_list = []
        y_proba_list = []
        predictions_detail = []

        for train_idx, test_idx in loo.split(self.X_scaled):
            X_train, X_test = self.X_scaled[train_idx], self.X_scaled[test_idx]
            y_train, y_test = self.y[train_idx], self.y[test_idx]

            # Clone model with best params
            model = lgb.LGBMClassifier(**self.best_params, objective='binary', random_state=42, verbose=-1)
            model.fit(X_train, y_train)

            # Predict
            y_pred = model.predict(X_test)[0]
            y_proba = model.predict_proba(X_test)[0, 1]

            y_pred_list.append(y_pred)
            y_true_list.append(y_test[0])
            y_proba_list.append(y_proba)

            predictions_detail.append({
                'ticker': self.tickers[test_idx[0]],
                'true': int(y_test[0]),
                'pred': int(y_pred),
                'proba': float(y_proba)
            })

        y_pred = np.array(y_pred_list)
        y_true = np.array(y_true_list)
        y_proba = np.array(y_proba_list)

        # Calculate metrics
        precision = precision_score(y_true, y_pred)
        recall = recall_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred)
        roc_auc = roc_auc_score(y_true, y_proba)
        cm = confusion_matrix(y_true, y_pred)

        print(f"\n{'Metric':<20s} {'Value':>10s}")
        print("-" * 30)
        print(f"{'Precision':<20s} {precision:>10.4f}")
        print(f"{'Recall':<20s} {recall:>10.4f}")
        print(f"{'F1-Score':<20s} {f1:>10.4f}")
        print(f"{'ROC-AUC':<20s} {roc_auc:>10.4f}")
        print("-" * 30)

        print("\nConfusion Matrix:")
        print(f"  TN={cm[0,0]}  FP={cm[0,1]}")
        print(f"  FN={cm[1,0]}  TP={cm[1,1]}")

        # Store evaluation results
        self.tuning_results.update({
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'roc_auc': float(roc_auc),
            'confusion_matrix': cm.tolist(),
            'predictions_detail': predictions_detail
        })

        # Print individual predictions
        print("\nIndividual Predictions:")
        print("="*80)
        for pred in predictions_detail:
            true_label = "CUT" if pred['true'] == 1 else "NO CUT"
            pred_label = "CUT" if pred['pred'] == 1 else "NO CUT"
            correct = "✓" if pred['true'] == pred['pred'] else "✗"

            print(f"{pred['ticker']:12s}  True: {true_label:6s}  Pred: {pred_label:6s}  "
                  f"Prob: {pred['proba']:.3f}  {correct}")

        print("="*80)

        # Compare with baseline
        print("\n📊 Comparison with Baseline (Untuned) Model:")
        print("="*80)
        print(f"{'Metric':<20s} {'Baseline':>12s} {'Tuned':>12s} {'Change':>12s}")
        print("-" * 56)

        # Load baseline results (from train_distribution_cut_model.py)
        baseline_path = sorted(Path("models").glob("lightgbm_results_*.json"))
        if baseline_path:
            with open(baseline_path[-1]) as f:
                baseline = json.load(f)

            print(f"{'Precision':<20s} {baseline['precision']:>12.4f} {precision:>12.4f} "
                  f"{precision - baseline['precision']:>+12.4f}")
            print(f"{'Recall':<20s} {baseline['recall']:>12.4f} {recall:>12.4f} "
                  f"{recall - baseline['recall']:>+12.4f}")
            print(f"{'F1-Score':<20s} {baseline['f1_score']:>12.4f} {f1:>12.4f} "
                  f"{f1 - baseline['f1_score']:>+12.4f}")
            print(f"{'ROC-AUC':<20s} {baseline['roc_auc']:>12.4f} {roc_auc:>12.4f} "
                  f"{roc_auc - baseline['roc_auc']:>+12.4f}")

        print("="*80)

    def analyze_feature_importance(self):
        """Analyze feature importance of tuned model."""
        print("\n" + "="*80)
        print("FEATURE IMPORTANCE (TUNED MODEL)")
        print("="*80)

        # Retrain on full dataset to get feature importance
        self.best_model.fit(self.X_scaled, self.y)

        importance = self.best_model.feature_importances_
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)

        print(f"\nTop 15 Most Important Features:")
        print("="*80)
        for i, row in importance_df.head(15).iterrows():
            print(f"{i+1:2d}. {row['feature']:40s} {row['importance']:8.2f}")
        print("="*80)

        # Store in results
        self.tuning_results['feature_importance'] = importance_df.to_dict(orient='records')

        return importance_df

    def save_results(self, output_dir: str = "models"):
        """Save tuned model and results."""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save model
        model_path = output_dir / f"lightgbm_tuned_model_{timestamp}.pkl"
        joblib.dump(self.best_model, model_path)
        print(f"\n✅ Saved tuned model to: {model_path}")

        # Save scaler
        scaler_path = output_dir / f"lightgbm_tuned_scaler_{timestamp}.pkl"
        joblib.dump(self.scaler, scaler_path)
        print(f"✅ Saved scaler to: {scaler_path}")

        # Save results
        results_path = output_dir / f"lightgbm_tuned_results_{timestamp}.json"
        with open(results_path, 'w') as f:
            json.dump(self.tuning_results, f, indent=2)
        print(f"✅ Saved results to: {results_path}")

        # Save best params separately for easy reference
        params_path = output_dir / f"lightgbm_best_params_{timestamp}.json"
        with open(params_path, 'w') as f:
            json.dump(self.best_params, f, indent=2)
        print(f"✅ Saved best parameters to: {params_path}")

    def create_comparison_plot(self, output_path: str = "analysis/tuning_comparison.png"):
        """Create visual comparison of baseline vs tuned model."""
        output_path = Path(output_path)
        output_path.parent.mkdir(exist_ok=True)

        # Load baseline results
        baseline_path = sorted(Path("models").glob("lightgbm_results_*.json"))
        if not baseline_path:
            print("⚠️  Baseline results not found, skipping comparison plot")
            return

        with open(baseline_path[-1]) as f:
            baseline = json.load(f)

        # Prepare data
        metrics = ['Precision', 'Recall', 'F1-Score', 'ROC-AUC']
        baseline_vals = [baseline['precision'], baseline['recall'],
                        baseline['f1_score'], baseline['roc_auc']]
        tuned_vals = [self.tuning_results['precision'], self.tuning_results['recall'],
                     self.tuning_results['f1_score'], self.tuning_results['roc_auc']]

        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))

        x = np.arange(len(metrics))
        width = 0.35

        ax.bar(x - width/2, baseline_vals, width, label='Baseline', alpha=0.8)
        ax.bar(x + width/2, tuned_vals, width, label='Tuned', alpha=0.8)

        ax.set_xlabel('Metric')
        ax.set_ylabel('Score')
        ax.set_title('LightGBM: Baseline vs Tuned Model Performance')
        ax.set_xticks(x)
        ax.set_xticklabels(metrics)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        ax.set_ylim([0, 1.1])

        # Add value labels
        for i, (b, t) in enumerate(zip(baseline_vals, tuned_vals)):
            ax.text(i - width/2, b + 0.02, f'{b:.3f}', ha='center', va='bottom', fontsize=9)
            ax.text(i + width/2, t + 0.02, f'{t:.3f}', ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"\n✅ Saved comparison plot to: {output_path}")
        plt.close()


def main():
    parser = argparse.ArgumentParser(description='Tune LightGBM hyperparameters')
    parser.add_argument('--dataset', type=str, default='data/training_dataset_v2.csv',
                       help='Path to training dataset')
    parser.add_argument('--search-type', type=str, choices=['focused', 'extensive'],
                       default='focused', help='Search space size')
    parser.add_argument('--n-jobs', type=int, default=-1,
                       help='Number of parallel jobs (-1 = all cores)')

    args = parser.parse_args()

    print("="*80)
    print("LIGHTGBM HYPERPARAMETER TUNING")
    print("="*80)
    print(f"Dataset: {args.dataset}")
    print(f"Search type: {args.search_type}")
    print(f"Parallel jobs: {args.n_jobs if args.n_jobs > 0 else 'all cores'}")
    print("="*80)

    # Create tuner
    tuner = LightGBMTuner(args.dataset)

    # Tune hyperparameters
    best_model, best_params = tuner.tune_hyperparameters(
        search_type=args.search_type,
        n_jobs=args.n_jobs
    )

    # Analyze feature importance
    tuner.analyze_feature_importance()

    # Save results
    tuner.save_results()

    # Create comparison plot
    tuner.create_comparison_plot()

    print("\n✅ Hyperparameter tuning complete!")

    # Final summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Best F1-Score: {tuner.tuning_results['f1_score']:.4f}")
    print(f"Best Precision: {tuner.tuning_results['precision']:.4f}")
    print(f"Best Recall: {tuner.tuning_results['recall']:.4f}")
    print(f"Best ROC-AUC: {tuner.tuning_results['roc_auc']:.4f}")

    if tuner.tuning_results['f1_score'] >= 0.90:
        print("\n🎉 TARGET ACHIEVED: F1-Score ≥ 0.90!")
    else:
        print(f"\n⚠️  Target not achieved (F1 = {tuner.tuning_results['f1_score']:.4f} < 0.90)")
        print("   Consider using --search-type extensive for more thorough search")

    print("="*80)


if __name__ == "__main__":
    main()
