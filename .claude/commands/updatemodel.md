# Update Distribution Cut Prediction Model

Update the distribution cut prediction model (currently v2.2) with new training data from recent REIT observations.

---

## Task Overview

You are tasked with updating the distribution cut prediction model by incorporating new training data. This involves:

1. **Data Collection:** Gather new REIT observations (both distribution cuts and controls)
2. **Phase 3 Generation:** Run pipeline Phases 1-3 to generate calculated metrics
3. **Data Labeling:** Properly label observations (cut=1, no cut=0)
4. **Model Retraining:** Retrain logistic regression model with expanded dataset
5. **Validation:** Compare new model performance against current model (v2.2)
6. **Deployment:** Archive old model and deploy new version if improved

---

## Step 1: Assess Current Model

**First, review the current model specifications:**

```bash
cat models/README.md
```

**Current Model v2.2 Baseline:**
- Training observations: 24 (11 cuts, 13 controls)
- F1 Score: 0.870 (target: ≥0.80)
- ROC AUC: 0.930
- Features: 28 Phase 3 metrics (sustainable AFCF methodology)
- Top predictors: monthly_burn_rate, acfo_calculated, available_cash

**Goal:** Improve upon these metrics or maintain performance with more data.

---

## Step 2: Identify New Training Observations

**You need to identify REITs with recent financial events:**

### Distribution Cut Cases (Target: 3-5 new observations)

Look for REITs that announced distribution cuts in the last 6-12 months:
- Search news: "Canadian REIT distribution cut 2024 2025"
- Check REIT press releases on SEDAR+ (sedarplus.ca)
- Review quarterly MD&As for distribution policy changes
- Criteria: >10% reduction in distributions per unit

**For each cut identified, document:**
- REIT name and ticker
- Cut announcement date
- Cut magnitude (% reduction)
- Financial period to analyze (typically quarter BEFORE the cut announcement)

### Control Cases (Target: 3-5 new observations)

Look for REITs that MAINTAINED distributions despite challenging conditions:
- Similar sector/property type as cut cases
- Comparable leverage or operating metrics
- Same time period as cut cases
- Criteria: No distribution cut, stable or increased payout

**Create a tracking document:**
```bash
# Create new training data tracking file
cat > data/model_update_tracking.md << 'EOF'
# Model Update Training Data

## Distribution Cut Cases

1. **[REIT Name]** ([TICKER])
   - Cut Date: YYYY-MM-DD
   - Cut Magnitude: XX%
   - Analysis Period: QX YYYY (period BEFORE cut)
   - Status: [ ] PDF collected [ ] Phase 1-3 complete [ ] Labeled

2. [Add more cases...]

## Control Cases (No Cut)

1. **[REIT Name]** ([TICKER])
   - Observation Period: QX YYYY
   - Rationale: [Why selected as control]
   - Status: [ ] PDF collected [ ] Phase 1-3 complete [ ] Labeled

2. [Add more cases...]

## Summary
- Total new observations: X
- Distribution cuts: Y
- Controls: Z
- Target dataset size: 24 (current) + X (new) = [TOTAL]
EOF

# Open for editing
cat data/model_update_tracking.md
```

---

## Step 3: Collect Financial Statements

**For each REIT identified above, collect PDFs:**

### Data Requirements

For each observation, you need:
- **Financial Statements PDF:** Balance sheet, income statement, cash flows
- **MD&A PDF:** Management discussion, FFO/AFFO/ACFO reconciliations
- **Time Period:** Quarter BEFORE distribution cut announcement (for cut cases)

### Download Sources

1. **SEDAR+ (Primary - Official Filings):** https://www.sedarplus.ca
   - Search by REIT name
   - Filter: "Interim financial statements" or "Annual financial statements"
   - Download both Financial Statements PDF and MD&A PDF

2. **REIT Investor Relations Websites (Alternative)**
   - Navigate to Investor Relations → Financial Reports
   - Download quarterly reports for target period

### Storage Convention

```bash
# Create storage directory
mkdir -p data/model_training_v2.3/

# Store PDFs with naming convention:
# [REIT]_[PERIOD]_[TYPE].pdf
#
# Example:
#   REIT_A_Q2_2024_statements.pdf
#   REIT_A_Q2_2024_mda.pdf
```

**Document sources:**
```bash
echo "# Data Sources Log" > data/model_training_v2.3/sources.md
echo "" >> data/model_training_v2.3/sources.md
echo "## REIT A - Q2 2024" >> data/model_training_v2.3/sources.md
echo "- Source: SEDAR+" >> data/model_training_v2.3/sources.md
echo "- Filing Date: YYYY-MM-DD" >> data/model_training_v2.3/sources.md
echo "- Documents: statements.pdf, mda.pdf" >> data/model_training_v2.3/sources.md
```

---

## Step 4: Generate Phase 3 Metrics for Each Observation

**Run the pipeline (Phases 1-3) for EACH new training observation:**

### For Each REIT:

```bash
# Set variables
ISSUER_NAME="[REIT Name]"
STATEMENTS_PDF="data/model_training_v2.3/[REIT]_[PERIOD]_statements.pdf"
MDA_PDF="data/model_training_v2.3/[REIT]_[PERIOD]_mda.pdf"

# Phase 1: PDF → Markdown
python scripts/preprocess_pdfs_enhanced.py \
  --issuer-name "$ISSUER_NAME" \
  "$STATEMENTS_PDF" \
  "$MDA_PDF"

# Phase 2: Markdown → JSON
python scripts/extract_key_metrics_efficient.py \
  --issuer-name "$ISSUER_NAME" \
  Issuer_Reports/${ISSUER_NAME// /_}/temp/phase1_markdown/*.md

# Validate schema (CRITICAL)
python scripts/validate_extraction_schema.py \
  Issuer_Reports/${ISSUER_NAME// /_}/temp/phase2_extracted_data.json

# Phase 3: Calculate metrics
python scripts/calculate_credit_metrics.py \
  Issuer_Reports/${ISSUER_NAME// /_}/temp/phase2_extracted_data.json

# Copy Phase 3 output to training data directory
cp Issuer_Reports/${ISSUER_NAME// /_}/temp/phase3_calculated_metrics.json \
  data/model_training_v2.3/${ISSUER_NAME// /_}_phase3.json
```

**Repeat for ALL new training observations (both cuts and controls).**

---

## Step 5: Build Training Dataset CSV

**Compile all Phase 3 metrics into a single training dataset:**

### Option A: Use Existing Script (if available)

```bash
# Check if batch script exists
ls scripts/regenerate_phase3_for_training.py

# If exists, adapt it for new data:
python scripts/regenerate_phase3_for_training.py \
  --input-dir data/model_training_v2.3/ \
  --output data/training_dataset_v2.3.csv
```

### Option B: Manual Compilation

Create a Python script to extract features from Phase 3 JSON files:

```python
# Create: scripts/compile_training_data.py
import json
import pandas as pd
from pathlib import Path

def extract_features_from_phase3(phase3_json_path):
    """Extract 28 Phase 3 features used by model v2.2"""
    with open(phase3_json_path) as f:
        data = json.load(f)

    features = {
        # FFO/AFFO/ACFO metrics
        'ffo_calculated': data['ffo_metrics']['ffo'],
        'ffo_per_unit': data['ffo_metrics'].get('ffo_per_unit', 0),
        'affo_calculated': data['affo_metrics']['affo'],
        'affo_per_unit': data['affo_metrics'].get('affo_per_unit', 0),
        'affo_payout_ratio': data['affo_metrics'].get('affo_payout_ratio', 0),
        'acfo_calculated': data['acfo_metrics']['acfo'],
        'acfo_per_unit': data['acfo_metrics'].get('acfo_per_unit', 0),
        'acfo_coverage_ratio': data['acfo_metrics'].get('acfo_coverage_ratio', 0),

        # AFCF metrics (if present)
        'afcf': data.get('afcf_metrics', {}).get('afcf', 0),
        'afcf_per_unit': data.get('afcf_metrics', {}).get('afcf_per_unit', 0),
        'self_funding_ratio': data.get('afcf_coverage', {}).get('afcf_self_funding_ratio', 0),

        # Burn rate & liquidity
        'monthly_burn_rate': data.get('burn_rate_analysis', {}).get('monthly_burn_rate', 0),
        'cash_runway_months': data.get('cash_runway', {}).get('runway_months', 0),
        'liquidity_risk_score': data.get('liquidity_risk', {}).get('risk_score', 0),
        'available_cash': data.get('liquidity_position', {}).get('available_cash', 0),
        'total_available_liquidity': data.get('liquidity_position', {}).get('total_available_liquidity', 0),

        # Leverage
        'debt_to_assets': data['leverage_metrics']['debt_to_assets'],
        'net_debt_to_ebitda': data['leverage_metrics']['net_debt_to_ebitda'],
        'interest_coverage': data['leverage_metrics']['interest_coverage'],

        # Portfolio
        'occupancy_rate': data['portfolio_metrics']['occupancy_rate'],
        'noi_margin': data['portfolio_metrics']['noi_margin'],

        # Dilution (if present)
        'dilution_percentage': data.get('dilution_analysis', {}).get('dilution_percentage', 0),
        'dilution_materiality': data.get('dilution_analysis', {}).get('dilution_materiality', 'minimal'),

        # Add remaining features to reach 28 total
        # (Review model v2.2 feature list in models/README.md)
    }

    return features

# Process all Phase 3 files
training_data = []
phase3_dir = Path('data/model_training_v2.3/')

for phase3_file in phase3_dir.glob('*_phase3.json'):
    print(f"Processing {phase3_file.name}...")
    features = extract_features_from_phase3(phase3_file)

    # Add metadata
    features['issuer_name'] = phase3_file.stem.replace('_phase3', '')

    # IMPORTANT: Add label (you must manually set this)
    # distribution_cut = 1 if cut occurred, 0 if control
    features['distribution_cut'] = None  # SET THIS MANUALLY

    training_data.append(features)

# Create DataFrame
df = pd.DataFrame(training_data)

# Save to CSV
df.to_csv('data/training_dataset_v2.3_UNLABELED.csv', index=False)
print(f"Created training dataset with {len(df)} observations")
print("IMPORTANT: Must manually label 'distribution_cut' column!")
```

**Run the script:**
```bash
python scripts/compile_training_data.py
```

### Step 5b: Label the Data

**CRITICAL: Manually label each observation:**

```bash
# Open the CSV
cat data/training_dataset_v2.3_UNLABELED.csv

# Use a text editor or spreadsheet to set 'distribution_cut' column:
# - distribution_cut = 1 → REIT announced distribution cut
# - distribution_cut = 0 → REIT maintained distributions (control)

# Verify labeling is complete
python -c "import pandas as pd; df = pd.read_csv('data/training_dataset_v2.3_UNLABELED.csv'); print(f'Null labels: {df.distribution_cut.isna().sum()}')"

# If no nulls, rename file
mv data/training_dataset_v2.3_UNLABELED.csv data/training_dataset_v2.3.csv
```

---

## Step 6: Merge with Existing Training Data

**Combine new data with existing v2.2 training dataset:**

```bash
# Check existing dataset
head -5 data/training_dataset_v2_sustainable_afcf.csv

# Merge datasets
python << 'EOF'
import pandas as pd

# Load existing v2.2 dataset
df_existing = pd.read_csv('data/training_dataset_v2_sustainable_afcf.csv')
print(f"Existing dataset: {len(df_existing)} observations")

# Load new data
df_new = pd.read_csv('data/training_dataset_v2.3.csv')
print(f"New data: {len(df_new)} observations")

# Verify column alignment
assert set(df_existing.columns) == set(df_new.columns), "Column mismatch!"

# Merge
df_combined = pd.concat([df_existing, df_new], ignore_index=True)
print(f"Combined dataset: {len(df_combined)} observations")

# Check class balance
print(f"\nClass distribution:")
print(df_combined['distribution_cut'].value_counts())

# Save
df_combined.to_csv('data/training_dataset_v2.3_combined.csv', index=False)
print("\nSaved to: data/training_dataset_v2.3_combined.csv")
EOF
```

---

## Step 7: Train New Model

**Retrain the logistic regression model with expanded dataset:**

### Create Training Script

```python
# Create: scripts/train_model_v2.3.py
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.model_selection import cross_val_score, cross_validate
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib
from datetime import datetime

# Load data
df = pd.read_csv('data/training_dataset_v2.3_combined.csv')
print(f"Training data: {len(df)} observations")
print(f"Distribution cuts: {df['distribution_cut'].sum()}")
print(f"Controls: {len(df) - df['distribution_cut'].sum()}")

# Prepare features and target
X = df.drop(['distribution_cut', 'issuer_name'], axis=1, errors='ignore')
y = df['distribution_cut']

# Handle categorical features (e.g., dilution_materiality)
X = pd.get_dummies(X, drop_first=True)

print(f"\nFeatures: {X.shape[1]} total")
print(f"Feature names: {list(X.columns)}")

# Create pipeline
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('selector', SelectKBest(f_classif, k=15)),  # Select top 15 features
    ('classifier', LogisticRegression(
        max_iter=1000,
        class_weight='balanced',
        random_state=42
    ))
])

# Cross-validation (5-fold)
print("\n" + "="*60)
print("MODEL V2.3 TRAINING - 5-FOLD CROSS-VALIDATION")
print("="*60)

scoring = {
    'accuracy': 'accuracy',
    'precision': 'precision',
    'recall': 'recall',
    'f1': 'f1',
    'roc_auc': 'roc_auc'
}

cv_results = cross_validate(
    pipeline, X, y,
    cv=5,
    scoring=scoring,
    return_train_score=False,
    n_jobs=-1
)

print(f"\nCross-Validation Results:")
print(f"  Accuracy:  {cv_results['test_accuracy'].mean():.3f} ± {cv_results['test_accuracy'].std():.3f}")
print(f"  Precision: {cv_results['test_precision'].mean():.3f} ± {cv_results['test_precision'].std():.3f}")
print(f"  Recall:    {cv_results['test_recall'].mean():.3f} ± {cv_results['test_recall'].std():.3f}")
print(f"  F1 Score:  {cv_results['test_f1'].mean():.3f} ± {cv_results['test_f1'].std():.3f}")
print(f"  ROC AUC:   {cv_results['test_roc_auc'].mean():.3f} ± {cv_results['test_roc_auc'].std():.3f}")

# Compare to v2.2 baseline
print("\n" + "="*60)
print("COMPARISON TO MODEL V2.2 BASELINE")
print("="*60)
print(f"v2.2 F1 Score:  0.870")
print(f"v2.3 F1 Score:  {cv_results['test_f1'].mean():.3f}")
print(f"Improvement:    {(cv_results['test_f1'].mean() - 0.870):.3f}")

if cv_results['test_f1'].mean() >= 0.870:
    print("✅ Model v2.3 meets or exceeds v2.2 performance!")
else:
    print("⚠️  Model v2.3 underperforms v2.2 - consider collecting more data")

# Train final model on full dataset
print("\nTraining final model on full dataset...")
pipeline.fit(X, y)

# Get feature importances
selector = pipeline.named_steps['selector']
classifier = pipeline.named_steps['classifier']

selected_features = X.columns[selector.get_support()].tolist()
feature_importances = classifier.coef_[0]

print(f"\nTop 15 Selected Features:")
for i, (feat, imp) in enumerate(sorted(zip(selected_features, feature_importances),
                                       key=lambda x: abs(x[1]), reverse=True), 1):
    print(f"{i:2d}. {feat:40s} {imp:8.4f}")

# Save model
model_path = f'models/distribution_cut_logistic_regression_v2.3.pkl'
joblib.dump(pipeline, model_path)
print(f"\n✅ Model saved to: {model_path}")

# Save metadata
metadata = {
    'version': 'v2.3',
    'training_date': datetime.now().isoformat(),
    'training_observations': len(df),
    'distribution_cuts': int(df['distribution_cut'].sum()),
    'controls': int(len(df) - df['distribution_cut'].sum()),
    'cv_f1_score': float(cv_results['test_f1'].mean()),
    'cv_roc_auc': float(cv_results['test_roc_auc'].mean()),
    'cv_accuracy': float(cv_results['test_accuracy'].mean()),
    'num_features': len(selected_features),
    'top_features': selected_features
}

import json
with open('models/model_v2.3_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print("✅ Metadata saved to: models/model_v2.3_metadata.json")
```

**Run training:**
```bash
python scripts/train_model_v2.3.py
```

---

## Step 8: Validate New Model

**Test the new model against the existing v2.2 model:**

### Create Validation Script

```bash
# Create: scripts/compare_model_v2.2_vs_v2.3.py
cat > scripts/compare_model_v2.2_vs_v2.3.py << 'EOF'
import joblib
import pandas as pd
import json

# Load models
model_v22 = joblib.load('models/distribution_cut_logistic_regression_v2.2.pkl')
model_v23 = joblib.load('models/distribution_cut_logistic_regression_v2.3.pkl')

# Load test data (use a holdout set or recent observations)
df_test = pd.read_csv('data/training_dataset_v2.3_combined.csv')
X_test = df_test.drop(['distribution_cut', 'issuer_name'], axis=1, errors='ignore')
X_test = pd.get_dummies(X_test, drop_first=True)
y_test = df_test['distribution_cut']

# Get predictions
v22_probs = model_v22.predict_proba(X_test)[:, 1]
v23_probs = model_v23.predict_proba(X_test)[:, 1]

# Compare predictions
comparison = pd.DataFrame({
    'issuer': df_test['issuer_name'],
    'actual_cut': y_test,
    'v2.2_prob': v22_probs,
    'v2.3_prob': v23_probs,
    'difference': v23_probs - v22_probs
})

print("="*80)
print("MODEL COMPARISON: v2.2 vs v2.3")
print("="*80)
print(comparison.to_string(index=False))

# Calculate metrics
from sklearn.metrics import f1_score, roc_auc_score, accuracy_score

print("\n" + "="*80)
print("PERFORMANCE METRICS")
print("="*80)
print(f"{'Metric':<20} {'v2.2':<15} {'v2.3':<15} {'Improvement':<15}")
print("-"*80)

for metric_name, metric_func in [
    ('Accuracy', accuracy_score),
    ('F1 Score', f1_score),
    ('ROC AUC', roc_auc_score)
]:
    v22_score = metric_func(y_test, (v22_probs > 0.5).astype(int)) if metric_name != 'ROC AUC' else metric_func(y_test, v22_probs)
    v23_score = metric_func(y_test, (v23_probs > 0.5).astype(int)) if metric_name != 'ROC AUC' else metric_func(y_test, v23_probs)
    improvement = v23_score - v22_score

    print(f"{metric_name:<20} {v22_score:<15.3f} {v23_score:<15.3f} {improvement:+.3f}")

# Recommendation
print("\n" + "="*80)
print("RECOMMENDATION")
print("="*80)

f1_v22 = f1_score(y_test, (v22_probs > 0.5).astype(int))
f1_v23 = f1_score(y_test, (v23_probs > 0.5).astype(int))

if f1_v23 > f1_v22:
    print("✅ DEPLOY MODEL V2.3 - Improved performance over v2.2")
elif f1_v23 >= f1_v22 - 0.05:
    print("⚠️  CONSIDER DEPLOYMENT - Similar performance, more training data")
else:
    print("❌ DO NOT DEPLOY - Performance degradation from v2.2")
    print("   Recommendation: Collect more training data or review feature engineering")
EOF

python scripts/compare_model_v2.2_vs_v2.3.py
```

---

## Step 9: Deploy New Model (If Approved)

**If validation shows improvement, deploy the new model:**

### Archive Old Model

```bash
# Move current production model to archive
mv models/distribution_cut_logistic_regression_v2.2.pkl \
   models/archive/distribution_cut_logistic_regression_v2.2.pkl

echo "✅ Model v2.2 archived"
```

### Deploy New Model

```bash
# Move new model to production
cp models/distribution_cut_logistic_regression_v2.3.pkl \
   models/distribution_cut_logistic_regression_v2.3.pkl

echo "✅ Model v2.3 deployed to production"
```

### Update Default Model Path in Scripts

```bash
# Update enrich_phase4_data.py to use v2.3 by default
sed -i "s/distribution_cut_logistic_regression_v2.2.pkl/distribution_cut_logistic_regression_v2.3.pkl/g" \
  scripts/enrich_phase4_data.py

echo "✅ Default model path updated in scripts"
```

### Update Documentation

```bash
# Update models/README.md
cat > models/README.md << 'EOF'
# Distribution Cut Prediction Models

## Current Production Model: v2.3

**File:** `distribution_cut_logistic_regression_v2.3.pkl`
**Training Date:** [INSERT DATE]
**Status:** Production

### Model Specifications

- **Algorithm:** Logistic Regression (scikit-learn)
- **Features:** 28 Phase 3 fundamentals (sustainable AFCF methodology)
- **Training Data:** [INSERT N] observations ([X] cuts, [Y] controls)
- **Feature Selection:** SelectKBest (k=15)
- **Class Weight:** Balanced

### Performance Metrics (5-fold CV)

| Metric | Score |
|--------|-------|
| F1 Score | [INSERT] |
| ROC AUC | [INSERT] |
| Accuracy | [INSERT] |
| Precision | [INSERT] |
| Recall | [INSERT] |

### Top Predictive Features

1. [Feature 1] ([Importance])
2. [Feature 2] ([Importance])
3. [Feature 3] ([Importance])
... [Continue for top 15]

### Changes from v2.2

- Training data expanded from 24 to [N] observations
- [Describe any methodology changes]
- [Describe performance improvements]

### Usage

```bash
python scripts/enrich_phase4_data.py \
  --phase3 path/to/phase3_metrics.json \
  --ticker REIT-UN.TO \
  --model models/distribution_cut_logistic_regression_v2.3.pkl
```

---

## Model Archive

Previous models are stored in `models/archive/` with detailed deprecation rationale.

### v2.2 (Archived YYYY-MM-DD)
- Training: 24 observations
- F1: 0.870, ROC AUC: 0.930
- Replaced by: v2.3 (expanded training data)

### v2.1 (Deprecated YYYY-MM-DD)
- Critical underestimation issue
- See: `models/archive/README.md`
EOF

echo "✅ models/README.md updated"
```

### Update CHANGELOG.md

```bash
# Add entry to CHANGELOG.md
cat >> CHANGELOG.md << 'EOF'

## [1.0.16] - YYYY-MM-DD

### Changed - Distribution Cut Prediction Model v2.3

**Model Update:** Retrained distribution cut prediction model with expanded training dataset.

#### Training Data Expansion

**v2.2 → v2.3:**
- Observations: 24 → [N] (+[X] observations, +[Y]%)
- Distribution cuts: 11 → [N]
- Controls: 13 → [N]
- Time period: 2022-2024 → 2022-2025

#### Model Performance

**v2.3 Metrics (5-fold CV):**
- F1 Score: [X] (v2.2: 0.870)
- ROC AUC: [X] (v2.2: 0.930)
- Accuracy: [X]% (v2.2: 87.5%)

**Improvement:** [+/- X.X%] F1 score vs v2.2

#### Top Predictive Features (v2.3)

1. [Feature] ([Importance])
2. [Feature] ([Importance])
... [Continue]

#### Files Modified

**Models:**
- ✅ `models/distribution_cut_logistic_regression_v2.3.pkl` - New production model
- ✅ `models/model_v2.3_metadata.json` - Model metadata
- ✅ `models/archive/distribution_cut_logistic_regression_v2.2.pkl` - v2.2 archived

**Training Data:**
- ✅ `data/training_dataset_v2.3_combined.csv` - Expanded training dataset
- ✅ `data/model_update_tracking.md` - New observation tracking

**Scripts:**
- ✅ `scripts/train_model_v2.3.py` - v2.3 training script
- ✅ `scripts/compare_model_v2.2_vs_v2.3.py` - Model comparison
- ✅ `scripts/enrich_phase4_data.py` - Updated default model path

**Documentation:**
- ✅ `models/README.md` - Updated specifications
- ✅ `CHANGELOG.md` - This entry

#### Deployment Date

**Deployed:** YYYY-MM-DD
**By:** [Your name/Claude Code]

---
EOF

echo "✅ CHANGELOG.md updated"
```

---

## Step 10: Verify Deployment

**Test the deployed model:**

```bash
# Test on a recent REIT analysis
python scripts/enrich_phase4_data.py \
  --phase3 Issuer_Reports/Example_REIT/temp/phase3_calculated_metrics.json \
  --ticker REIT-UN.TO

# Verify model v2.3 is being used
grep "Model version" Issuer_Reports/Example_REIT/temp/phase3_enriched_data.json

# Expected output:
# "model_version": "v2.3"
```

**Run full pipeline test:**

```bash
/analyzeREissuer @test_statements.pdf @test_mda.pdf "Test REIT"
```

---

## Step 11: Commit and Document

**Commit all changes to version control:**

```bash
# Stage all changes
git add -A

# Commit with detailed message
git commit -m "feat: deploy distribution cut prediction model v2.3

Model Update Summary:
- Expanded training data from 24 to [N] observations (+[X]%)
- F1 Score: [X] (v2.2: 0.870) = [+/- X]% change
- ROC AUC: [X] (v2.2: 0.930)
- Top predictors: [list top 3-5 features]

Training Data:
- New distribution cut cases: [N] REITs
- New control cases: [N] REITs
- Time period coverage: 2022-2025

Files Modified:
- models/distribution_cut_logistic_regression_v2.3.pkl (NEW)
- models/README.md (UPDATED)
- scripts/enrich_phase4_data.py (default model → v2.3)
- data/training_dataset_v2.3_combined.csv (NEW)
- CHANGELOG.md (v1.0.16 entry)

Model v2.2 archived to models/archive/

Verified with test pipeline run on [Test REIT]."

# Push to remote
git push origin main
```

---

## Success Criteria

**Model update is complete when:**

✅ New training data collected (minimum 5 new observations recommended)
✅ Phase 3 metrics generated for all new observations
✅ Training dataset properly labeled (distribution_cut: 0 or 1)
✅ Model v2.3 trained with F1 score ≥ 0.80 (target)
✅ Model v2.3 performance compared to v2.2 baseline
✅ Model v2.2 archived, v2.3 deployed to production
✅ Documentation updated (README, CHANGELOG)
✅ Deployment tested with full pipeline run
✅ All changes committed and pushed to repository

---

## Troubleshooting

### Issue: New model underperforms v2.2

**Possible causes:**
- Insufficient training data (need more observations)
- Class imbalance (too few cut cases or controls)
- Feature distribution shift (check for outliers)
- Labeling errors (verify distribution_cut labels)

**Solutions:**
- Collect more training observations (aim for 30+ total)
- Ensure balanced dataset (40-60% cuts, 60-40% controls)
- Review and clean outliers in Phase 3 metrics
- Double-check labeling accuracy

### Issue: Phase 3 extraction failures

**Possible causes:**
- Schema violations in Phase 2 extraction
- Missing financial data in source PDFs
- PDF quality issues (scanned images vs text)

**Solutions:**
- Always run `validate_extraction_schema.py` after Phase 2
- Use higher quality financial statement PDFs
- Consider using Docling for cleaner PDF extraction

### Issue: Feature alignment errors

**Possible causes:**
- Different feature names between v2.2 and v2.3 training data
- Missing features in new Phase 3 extractions
- Categorical feature encoding mismatches

**Solutions:**
- Verify column names match exactly between datasets
- Check that all 28 Phase 3 features are present
- Use `pd.get_dummies()` consistently for categorical features

---

## Notes

- Model updates should be performed quarterly or when 5+ new observations are available
- Always maintain at least 40% representation of minority class (usually cut cases)
- Archive ALL previous model versions in `models/archive/` before deploying new model
- Test deployed model on 2-3 recent REIT analyses before announcing update
- Update GitHub release notes if model update is part of a versioned release

---

**End of /updatemodel slash command**
