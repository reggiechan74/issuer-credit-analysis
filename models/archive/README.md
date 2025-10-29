# Archived Models

This folder contains deprecated model versions that are no longer used in production.

## Model v2.1 (DEPRECATED)

**File:** `distribution_cut_logistic_regression_v2.1_DEPRECATED.pkl`
**Deprecation Date:** 2025-10-29
**Replaced By:** Model v2.2

### Why Deprecated

Model v2.1 significantly underestimates distribution cut risk in severe distress cases due to feature distribution mismatch:

**Underestimation Examples:**
- Artis REIT: 2.1% → 55.0% (v2.2) - Underestimated by 52.9 percentage points
- RioCan REIT: 1.3% → 48.5% (v2.2) - Underestimated by 47.2 percentage points
- Dream Industrial REIT: 1.4% → 29.3% (v2.2) - Underestimated by 27.9 percentage points

**Root Cause:**
- v2.1 was trained on **total AFCF** (includes non-recurring items like property dispositions)
- Phase 3 now calculates **sustainable AFCF** (excludes non-recurring items)
- Self-funding ratio feature (#4 most important) became unreliable

**Model v2.1 Specifications:**
- Features: 54 (33 Phase 3 fundamentals + 17 market + 9 macro, reduced to 15 via SelectKBest)
- Training dataset: 24 observations (11 cuts, 13 controls)
- Performance: F1=0.952, ROC AUC=1.0, Accuracy=0.958
- Total AFCF methodology (non-recurring items included)

### Migration to v2.2

**What Changed:**
- Feature set reduced from 54 → 28 (Phase 3 fundamentals only)
- Model uses sustainable AFCF methodology (aligns with Phase 3 calculations)
- SelectKBest still selects 15 features from 28 inputs
- Top features reordered: monthly_burn_rate (#1), acfo_calculated (#2), available_cash (#3)

**How to Use v2.1 (Not Recommended):**
```bash
python scripts/enrich_phase4_data.py \
  --phase3 Issuer_Reports/REIT/temp/phase3_calculated_metrics.json \
  --ticker TICKER.TO \
  --model models/archive/distribution_cut_logistic_regression_v2.1_DEPRECATED.pkl
```

**⚠️ WARNING:** v2.1 predictions are unreliable for REITs with:
- Negative sustainable AFCF
- Critical liquidity risk (runway < 6 months)
- Self-funding ratio < 0 or deeply negative

Use model v2.2 for all new credit analyses.

---

**See:** `docs/DISTRIBUTION_CUT_MODEL_DISCREPANCY_ANALYSIS.md` for complete analysis
**GitHub Issue:** #45 (Distribution Cut Prediction Model v2.2)
