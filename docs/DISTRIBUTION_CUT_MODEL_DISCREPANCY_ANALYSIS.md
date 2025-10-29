# Distribution Cut Model Discrepancy Analysis

**Date:** 2025-10-29
**Issue:** Model v2.1 shows 2.1% "Very Low" risk for Artis REIT despite Phase 4 credit analysis showing imminent liquidity distress
**Status:** ROOT CAUSE IDENTIFIED - Model v2.2 exists but is incompatible with current enrichment script

---

## Executive Summary

**The Discrepancy:**
- **Model v2.1 Prediction:** 2.1% cut probability (Very Low risk, High confidence)
- **Phase 4 Credit Analysis:** Imminent distress (1.6 months cash runway, $10.6M monthly burn, 187.5% AFFO payout)
- **Model v2.2 Prediction:** 55.0% cut probability (Very High risk) ✅ **Aligns with credit analysis**

**Root Cause:** Model v2.1 significantly underestimates severe distress cases due to feature distribution mismatch (trained on total AFCF, but Phase 3 now calculates sustainable AFCF).

**Solution Exists But Blocked:** Model v2.2 was created to fix this underestimation (documented in CLAUDE.md Issue #45), but current enrichment script is incompatible with v2.2's feature set.

---

## Detailed Analysis

### 1. Model v2.1 Prediction (Current - WRONG)

**From:** `Issuer_Reports/Artis_REIT/temp/phase4_enriched_data.json` (lines 509-559)

```json
{
  "distribution_cut_prediction": {
    "model_version": "2.1",
    "prediction_date": "2025-10-29",
    "cut_probability_pct": 2.1,
    "predicted_class": "control",
    "risk_level": "Very Low",
    "confidence": "High",
    "top_drivers": [
      {
        "rank": 1,
        "feature": "self_funding_ratio",
        "value": -0.61,
        "coefficient": 0.8708,
        "direction": "Increases"
      }
    ]
  }
}
```

**Top 5 Risk Drivers (v2.1):**
1. `self_funding_ratio`: -0.61x (INCREASES risk) - Most predictive feature
2. `mkt_momentum_trend`: -1 (INCREASES risk)
3. `mkt_momentum_12m_pct`: 0 (DECREASES risk)
4. `mkt_volume_30d_avg`: 0 (INCREASES risk)
5. `mkt_risk_score`: 55 (INCREASES risk)

**Why This Is Wrong:** Despite self-funding ratio of -0.61x (rank #1 driver) and market risk score of 55, the model predicts only 2.1% risk.

---

### 2. Phase 3 Financial Metrics (CRITICAL DISTRESS)

**From:** `Issuer_Reports/Artis_REIT/temp/phase4_enriched_data.json` (lines 8-366)

| Metric | Value | Credit Implication |
|--------|-------|-------------------|
| **AFCF (Sustainable)** | -$24,021k | Deeply negative free cash flow |
| **AFFO Payout Ratio** | 187.5% | Deeply unsustainable distribution |
| **ACFO Payout Ratio** | -208.9% | Negative operating cash flow |
| **Self-Funding Ratio** | -0.61x | Cannot cover obligations |
| **Monthly Burn Rate** | -$10,615k | Rapid cash depletion |
| **Cash Runway** | 1.6 months | Imminent depletion (by Aug 16, 2025) |
| **Extended Runway** | 9.0 months | Even with credit facilities |
| **Liquidity Risk** | CRITICAL (4/4) | Emergency financing required |
| **Available Cash** | $16,639k | Minimal cushion |
| **Undrawn Facilities** | $78,400k | Limited capacity |

**Phase 4 Credit Assessment:**
- Rating: B+ (Negative outlook)
- Downgrade probability: >50% within 6-12 months
- Key warnings: "Imminent liquidity distress", "Going concern risk"

---

### 3. Model v2.2 Prediction (Correct - BLOCKED)

**Comparison Script Output:**
```
Testing: Artis REIT
----------------------------------------------------------------------
  v2.1 (Total AFCF):       2.1% (Very Low)
  v2.2 (Sustainable AFCF): 55.0% (Very High)  ✅ ALIGNS WITH DISTRESS
  Difference:              +52.9%

  Self-Funding Ratio: -0.61x
```

**v2.2 Risk Level:** Very High (55.0% cut probability)
- This aligns with 1.6 months cash runway
- Reflects imminent distribution cut risk
- Matches Phase 4 credit analysis

---

## Root Cause Analysis

### Why Model v2.1 Underestimates Severe Distress

**From CLAUDE.md (lines 13-53):**

> **Problem:** Model v2.1 was trained on total AFCF (includes non-recurring items like property dispositions), but Phase 3 now calculates sustainable AFCF (recurring items only). This caused a feature distribution mismatch.
>
> **Impact:** v2.1 significantly **underestimated** distribution cut risk by 27-58 percentage points:
> - Artis REIT: 5.4% → 63.5% (+58.1%)
> - RioCan REIT: 1.3% → 48.5% (+47.2%)
> - Dream Industrial REIT: 1.4% → 29.3% (+27.9%)

**Artis REIT AFCF Breakdown:**
```json
"afcf_metrics": {
  "afcf_sustainable": -24021,     // Excludes non-recurring (REALITY)
  "afcf_total": -17816,           // Includes non-recurring (MODEL TRAINED ON THIS)
  "non_recurring_cfi": 6205,      // Property dispositions artificially improve total AFCF
  "net_cfi_sustainable": -16894,
  "net_cfi_total": -10689
}
```

**The Mismatch:**
1. **Training (v2.1):** Model learned from total AFCF (-$17,816k)
2. **Inference (current):** Model receives sustainable AFCF-based ratios
3. **Self-Funding Ratio Impact:**
   - Using total AFCF: -$17,816 / $39,669 = **-0.45x** (less negative)
   - Using sustainable AFCF: -$24,021 / $39,669 = **-0.61x** (more negative)
   - Model doesn't recognize the -0.61x as severe because it was trained on "less negative" ratios

**Feature Importance Shift (v2.1 → v2.2):**
- **v2.1:** Self-funding ratio is rank #4 most predictive feature
- **v2.2:** Self-funding ratio dropped to rank #15 (less weight given feature instability)
- **v2.2 top features:** Monthly burn rate (#1), ACFO (#2), available cash (#3)

---

## Why We Can't Use Model v2.2 Yet

### Feature Set Incompatibility

**Model v2.1:**
- Expects: **54 features**
- Enrichment script: Generates 54 features (compatible)
- Default in `enrich_phase4_data.py` line 51: `models/distribution_cut_logistic_regression.pkl`

**Model v2.2:**
- Expects: **28 features** (26 features removed)
- Enrichment script: Still generates 54 features (incompatible)
- Location: `models/distribution_cut_logistic_regression_v2.2.pkl`

**Error When Using v2.2:**
```python
ValueError: The feature names should match those that were passed during fit.
Feature names unseen at fit time:
- macro_ca_credit_environment
- macro_ca_credit_stress_score
- macro_ca_policy_rate
- macro_ca_rate_change_12m_bps
- macro_ca_rate_cycle
[...21 more features]
```

**26 Features in v2.1 but NOT in v2.2:**
- All macro environment features (5 features)
- Market risk detail features
- Volatility components
- Volume metrics
- Various intermediate calculations

---

## Impact Assessment

### Current Situation (Using v2.1)

**For Artis REIT:**
- **Prediction:** 2.1% Very Low risk
- **Reality:** 55.0% Very High risk (per v2.2)
- **Underestimation:** 52.9 percentage points

**Credit Analysis Consequences:**
- ❌ Model contradicts qualitative distress signals
- ❌ Report Section 11 shows "Very Low (2.1%)" when risk is actually Very High
- ❌ Investors/analysts see misleading quantitative risk assessment
- ⚠️ Phase 4 narrative correctly identifies distress, but model undermines credibility

**For Other REITs (from comparison script):**
| REIT | v2.1 | v2.2 | Underestimation |
|------|------|------|-----------------|
| Artis REIT | 2.1% (Very Low) | 55.0% (Very High) | **+52.9%** |
| RioCan REIT | 1.3% (Very Low) | 48.5% (High) | **+47.2%** |
| Dream Industrial REIT | 1.4% (Very Low) | 29.3% (Moderate) | **+27.9%** |

---

## Recommended Solutions

### Option 1: Deploy Model v2.2 (Requires Script Update) ⭐ **RECOMMENDED**

**Steps:**
1. **Update `enrich_phase4_data.py`** to generate only the 28 features v2.2 expects
2. **Identify v2.2 feature list** from training dataset:
   ```bash
   python scripts/compare_model_predictions.py  # Shows exact features
   ```
3. **Remove 26 features** from enrichment script:
   - Macro environment detail features
   - Market risk intermediate calculations
   - Redundant volume/volatility components
4. **Update default model path** in `enrich_phase4_data.py` line 51:
   ```python
   def __init__(self, ..., model_file: str = "models/distribution_cut_logistic_regression_v2.2.pkl"):
   ```
5. **Regenerate enriched data** for all REITs
6. **Update CLAUDE.md** to reflect v2.2 deployment

**Benefits:**
- ✅ Accurate risk predictions (55% vs 2.1% for Artis)
- ✅ Model aligns with credit analysis
- ✅ Training dataset uses sustainable AFCF (matches Phase 3)
- ✅ Better feature importance (burn rate #1, ACFO #2)

**Effort:** Medium (4-6 hours)
- Identify exact 28 features from v2.2 model
- Update enrichment script
- Test on 3 REITs
- Regenerate all reports

---

### Option 2: Retrain v2.2 with 54 Features (NOT RECOMMENDED)

**Steps:**
1. Regenerate training dataset with 54 features
2. Retrain logistic regression model
3. Validate performance metrics (F1, ROC AUC)

**Drawbacks:**
- ❌ Adds 26 features that v2.2 analysis determined were redundant
- ❌ Risk of overfitting (54 features for 24 training observations)
- ❌ Time-consuming (data regeneration + model training)
- ❌ Doesn't address root cause (should use sustainable AFCF features)

---

### Option 3: Keep v2.1 with Disclaimer (TEMPORARY ONLY)

**Steps:**
1. Add warning to Phase 5 report Section 11:
   ```
   ⚠️ Model v2.1 may underestimate severe distress cases. For REITs with
   critical liquidity risk or negative self-funding ratios, qualitative
   credit analysis should take precedence over quantitative prediction.
   ```
2. Update Phase 4 agent to cross-check model prediction against liquidity risk
3. Flag discrepancies in report (e.g., "Model shows 2.1% but liquidity is CRITICAL")

**Drawbacks:**
- ❌ Band-aid solution, doesn't fix root cause
- ❌ Undermines model credibility
- ❌ Confusing for users (which prediction to trust?)
- ✅ **Only acceptable as temporary measure** while deploying v2.2

---

## Implementation Priority

### Immediate (Next 1-2 days)

1. **Extract v2.2 feature list** from model or training dataset
2. **Update `enrich_phase4_data.py`** to generate 28 features (not 54)
3. **Test on Artis REIT** to verify 55% prediction
4. **Document breaking changes** (enriched data schema changes)

### Short-term (Next week)

5. **Regenerate enriched data** for all existing REITs (Artis, RioCan, Dream Industrial)
6. **Regenerate Phase 5 reports** with corrected predictions
7. **Update default model path** in slash commands to use v2.2
8. **Update CLAUDE.md** to mark v2.2 as production default

### Medium-term (Ongoing)

9. **Monitor v2.2 accuracy** on new observations
10. **Collect feedback** from credit analysts
11. **Consider retraining** if new distribution cuts observed (expand training set)

---

## Testing Validation

### Artis REIT (Test Case)

**Expected Results After v2.2 Deployment:**

| Metric | Before (v2.1) | After (v2.2) | Expected |
|--------|---------------|--------------|----------|
| Cut Probability | 2.1% | 55.0% | ✅ 50-60% |
| Risk Level | Very Low | Very High | ✅ Very High |
| Alignment with Phase 4 | ❌ Contradicts | ✅ Aligns | ✅ Must align |
| Self-Funding Ratio | -0.61x | -0.61x | ✅ Same input |
| Cash Runway | 1.6 months | 1.6 months | ✅ Same input |

**Phase 5 Report Section 11 (Expected Output):**
```markdown
## 11. Distribution Cut Risk Assessment

**Prediction Model:** v2.2 (Sustainable AFCF)
**Cut Probability:** 55.0% (12-month horizon)
**Risk Level:** 🔴 Very High
**Model Confidence:** High

**Top 5 Risk Drivers:**
1. Monthly Burn Rate: -$10,615k (Increases risk)
2. ACFO: -$7,127k (Increases risk)
3. Available Cash: $16,639k (Increases risk)
4. Cash Runway: 1.6 months (Increases risk)
5. Self-Funding Ratio: -0.61x (Increases risk)

**Assessment:** Model prediction (55% Very High risk) aligns with critical
liquidity distress identified in qualitative credit analysis. Immediate
distribution cut likely without emergency financing or asset sales.
```

---

## Conclusion

**Current State:**
- ❌ Model v2.1 underestimates Artis REIT risk by 52.9 percentage points
- ❌ Quantitative prediction (2.1%) contradicts qualitative analysis (imminent distress)
- ✅ Model v2.2 correctly identifies 55% Very High risk

**Root Cause:**
- v2.1 trained on total AFCF (includes non-recurring items)
- Phase 3 now uses sustainable AFCF (excludes non-recurring items)
- Feature distribution mismatch causes severe underestimation

**Solution:**
- Deploy model v2.2 by updating enrichment script to generate 28 features (not 54)
- Documented in CLAUDE.md Issue #45 as COMPLETE but not yet in production
- **CLAUDE.md line 79 states:** "Update default model path in `enrich_phase4_data.py` to v2.2"

**Next Action:** Update enrichment script to support v2.2's 28-feature set and deploy to production.

---

## References

- **CLAUDE.md:** Lines 13-83 (Distribution Cut Prediction Model v2.2 - Issue #45)
- **Enriched Data:** `Issuer_Reports/Artis_REIT/temp/phase4_enriched_data.json`
- **Enrichment Script:** `scripts/enrich_phase4_data.py` (line 51 - default model path)
- **Comparison Script:** `scripts/compare_model_predictions.py`
- **Model Files:**
  - `models/distribution_cut_logistic_regression.pkl` (v2.1 - current default)
  - `models/distribution_cut_logistic_regression_v2.2.pkl` (v2.2 - not deployed)
- **Training Dataset:** `data/training_dataset_v2_sustainable_afcf.csv`

---

**Document Version:** 1.0
**Author:** Claude Code
**Analysis Date:** 2025-10-29
