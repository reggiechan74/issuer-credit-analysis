# Quick Reference: REIT Distribution Cut Prediction

**Date:** 2025-10-21
**Full Report:** `docs/DIVIDEND_CUT_PREDICTION_RESEARCH.md`

---

## Top 5 Predictive Variables

| Rank | Variable | Cut Risk Threshold | Current Pipeline |
|------|----------|-------------------|------------------|
| 1 | AFFO Payout Ratio | >85-90% | ✅ Phase 3 |
| 2 | Interest Coverage (EBITDA/Interest) | <3.0x | ✅ Phase 3 |
| 3 | ACFO Payout Ratio | >80-85% | ✅ Phase 3 |
| 4 | Debt/EBITDA | >6.0x | ✅ Phase 3 |
| 5 | AFCF Self-Funding Ratio | <1.0x | ✅ Phase 3 (v1.0.6+) |

---

## Risk Threshold Matrix

### AFFO Payout Ratio
- ✅ **<70%:** Low risk (strong cushion)
- ⚠️ **70-80%:** Moderate risk (typical for well-run REITs)
- ⚠️ **80-90%:** Elevated risk (limited margin)
- 🚨 **90-100%:** High risk (tight coverage)
- 🚨 **>100%:** Critical risk (unsustainable)

### Interest Coverage
- ✅ **≥5.0x:** Low risk (strong coverage)
- ⚠️ **3.0-5.0x:** Moderate risk (adequate)
- ⚠️ **2.0-3.0x:** Elevated risk (tight)
- 🚨 **<2.0x:** High risk (distress)
- 🚨 **<1.5x:** Critical risk (covenant violation likely)

### Debt/EBITDA
- ✅ **<4.0x:** Low risk
- ⚠️ **4.0-6.0x:** Moderate risk (acceptable range)
- ⚠️ **6.0-7.3x:** Elevated risk (watchlist)
- 🚨 **>7.3x:** High risk (downgrade likely per DBRS)

### NAV Discount
- ✅ **Premium to NAV:** Positive signal
- ✅ **0-10% discount:** Normal range
- ⚠️ **10-20% discount:** Moderate concern
- 🚨 **>20% discount:** Significant market concern
- 🚨 **>30% discount:** Severe distress signal

---

## Recommended Model: Gradient Boosting Classifier

**Why:**
- 92-96% accuracy in financial distress studies
- Best Sharpe ratio (0.446) vs. Random Forest (0.219)
- Handles nonlinear relationships
- Feature importance validates with expert knowledge

**Expected Performance:**
- Accuracy: 92-96%
- Precision: 82-87%
- Recall: 85-90%
- AUC-ROC: 0.90-0.95

**Alternative:** Cox Proportional Hazards Model for time-to-event prediction

---

## Industry Best Practices

### Moody's REIT Rating
- **Aa rating:** FFO payout ratio <50%
- REITs "relatively unlikely to cut preferred dividends to preserve financial flexibility"
- Distribution requirement = capital market dependency

### S&P Thresholds
- **70-80% AFFO payout:** Typical for well-run REITs
- **Sector-specific coverage:**
  - Healthcare: >1.2x
  - Industrial: >1.15x
  - Mortgage: >1.05x

### DBRS Canadian REITs
- **Debt/EBITDA:** Mid-5.0x for investment grade
- **Downgrade threshold:** >7.3x debt/EBITDA OR <4.0x interest coverage

### REALPAC/NAREIT
- **60-80% AFFO:** Healthy and sustainable
- **80-90%:** Upper threshold
- **>90%:** Elevated risk (though some operate here due to 90% tax requirement)

---

## Warning Signals Beyond Ratios

1. **Share Price:**
   - NAV discount >20% = market skepticism
   - Dividend yield >8-10% often = falling price (not rising distribution)

2. **Equity Issuance:**
   - Frequent dilutive offerings = capital stress
   - Distributions funded by equity raises (not operations)

3. **Asset Sales:**
   - Forced sales at below-market prices = liquidity distress
   - Accelerating dispositions = weak financial position

4. **Covenant Pressure:**
   - Approaching debt/assets 60% limit
   - Interest coverage near 1.5x minimum
   - Unencumbered assets near 150% unsecured debt requirement

5. **Refinancing Risk:**
   - Heavy near-term maturities + weak liquidity
   - Bank loans (shorter term) = frequent refinancing pressure

6. **Sector Stress:**
   - Office REITs: 9 of 25 cuts (2023-24) from office sector
   - 39.4% of US equity REITs cut distributions vs. pre-pandemic

---

## Implementation in Current Pipeline

### Phase 2 (Extract - Already Available)
```json
{
  "ffo_affo": {"ffo": X, "affo_reported": Y},
  "acfo_metrics": {"acfo": Z},
  "distributions": {"common_distributions": D},
  "balance_sheet": {"total_debt": T, "total_assets": A},
  "income_statement": {"ebitda": E, "interest_expense": I}
}
```

### Phase 3 (Calculate - Already Available v1.0.13)
```json
{
  "payout_ratios": {
    "affo_payout_ratio": 0.87,  // D / Y
    "acfo_payout_ratio": 0.82   // D / Z
  },
  "leverage_metrics": {
    "interest_coverage": 2.8,    // E / I
    "debt_to_ebitda": 6.5,       // T / E
    "debt_to_assets": 0.58       // T / A
  },
  "afcf_coverage": {
    "afcf_self_funding_ratio": 0.45  // AFCF / (debt service + distributions)
  }
}
```

### Phase 3 (NEW - Prediction Model)
```json
{
  "distribution_cut_risk": {
    "probability_12mo": 0.73,
    "probability_24mo": 0.85,
    "risk_level": "HIGH",
    "primary_drivers": [
      "AFFO payout ratio 92% (threshold: 90%)",
      "Interest coverage 2.1x (threshold: 3.0x)",
      "Debt/EBITDA 7.8x (threshold: 6.0x)"
    ],
    "model_version": "GradientBoostingClassifier_v1.0",
    "confidence": 0.89
  }
}
```

### Phase 5 (Report - NEW Section)
```markdown
### Distribution Sustainability Risk Assessment

**12-Month Cut Probability:** 73% (HIGH RISK)

**Primary Risk Drivers:**
1. AFFO payout ratio 92% exceeds 90% sustainability threshold
2. Interest coverage 2.1x below 3.0x prudent level
3. Debt/EBITDA 7.8x exceeds 6.0x acceptable range

**Credit Implications:**
- Distribution cut likely required to restore financial flexibility
- Covenant cushion minimal; violation risk if operations deteriorate
- Capital market access critical for refinancing $XXX million maturing within 12 months
```

---

## Quick Start: Feature Importance Rankings

**Top 10 Features (from Literature):**

1. **AFFO Payout Ratio** ⭐⭐⭐⭐⭐
2. **Interest Coverage** ⭐⭐⭐⭐⭐
3. **ACFO Payout Ratio** ⭐⭐⭐⭐⭐
4. **Debt/EBITDA** ⭐⭐⭐⭐
5. **AFCF Self-Funding Ratio** ⭐⭐⭐⭐
6. **NAV Discount** ⭐⭐⭐⭐
7. **Occupancy Rate** ⭐⭐⭐
8. **NOI Margin** ⭐⭐⭐
9. **Debt/Assets** ⭐⭐⭐
10. **Dividend Yield** ⭐⭐⭐

**Trend Features (high predictive power):**
- Payout ratio increasing over 4 quarters
- Occupancy declining over 4 quarters
- Leverage increasing while coverage declining

---

## Data Requirements

### Minimum (Current Pipeline)
- ✅ Balance sheet (debt, assets, equity)
- ✅ Income statement (NOI, EBITDA, interest)
- ✅ FFO/AFFO metrics
- ✅ ACFO metrics (if available)
- ✅ Distributions

### Enhanced (Recommended)
- ⚠️ Market data (share price, NAV per unit)
- ⚠️ Debt maturity schedule
- ⚠️ Covenant details
- ⚠️ Historical quarterly data (4-8 quarters)

### External (Future)
- ❌ Peer comparison metrics
- ❌ Macroeconomic variables (interest rates, cap rates)
- ❌ Management commentary sentiment analysis

---

## Next Steps

### Week 1: Data Collection
1. Compile historical REIT distribution cuts (2008-2024)
2. Extract Phase 2/3 metrics for 50-100 cut events
3. Create training dataset (REIT-quarter observations)

### Week 2: Baseline Model
1. Implement Gradient Boosting Classifier
2. Train/test split (80/20)
3. Calculate accuracy, precision, recall, AUC-ROC

### Week 3: Validation
1. K-fold cross-validation (k=5)
2. SHAP feature importance analysis
3. Threshold optimization

### Week 4: Integration
1. Add prediction function to `calculate_credit_metrics.py`
2. Output risk scores to Phase 3 JSON
3. Update Phase 5 template with risk section

---

## Key Takeaways

1. **Current pipeline already captures 8 of top 10 predictive variables** in Phase 3
2. **Implementation path is clear:** Add prediction model to Phase 3 calculations
3. **Expected accuracy:** 92-96% with Gradient Boosting Classifier
4. **Critical thresholds:** AFFO payout >85-90%, interest coverage <3.0x, debt/EBITDA >6.0x
5. **Survival analysis (Cox PH)** offers time-to-event predictions for enhanced risk assessment

---

**Full Research Report:** `docs/DIVIDEND_CUT_PREDICTION_RESEARCH.md` (58 pages, 10 sections)
