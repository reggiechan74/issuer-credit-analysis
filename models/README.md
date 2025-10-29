# Distribution Cut Prediction Models

**Current Production Model:** v2.2

## Active Models

### distribution_cut_logistic_regression_v2.2.pkl

**Status:** ✅ Production (deployed 2025-10-29)
**Version:** 2.2
**Methodology:** Sustainable AFCF

**Model Specifications:**
- Algorithm: Logistic Regression
- Features: 28 Phase 3 fundamentals (SelectKBest → 15 selected)
- Training dataset: 24 observations (11 cuts, 13 controls)
- Performance: F1=0.870, ROC AUC=0.930, Accuracy=87.5%
- Training date: 2025-10-23

**Key Features (Top 5):**
1. `monthly_burn_rate` (coefficient: 1.1039)
2. `acfo_calculated` (coefficient: 0.7108)
3. `available_cash` (coefficient: 0.6859)
4. `self_funding_ratio` (coefficient: 0.6284) - Rank #15 (was #4 in v2.1)
5. `total_available_liquidity` (coefficient: 0.5948)

**Methodology:**
- Uses **sustainable AFCF** (excludes non-recurring items like property dispositions)
- Aligns with Phase 3 calculations (v1.0.14 - Issue #40)
- No market or macro features (Phase 3 fundamentals only)

**Usage:**
```bash
python scripts/enrich_phase4_data.py \
  --phase3 Issuer_Reports/REIT/temp/phase3_calculated_metrics.json \
  --ticker TICKER.TO
```

Default model is v2.2 (no `--model` argument needed).

**Validation:**
- Artis REIT: 67.1% High risk ✅ (v2.1 showed 2.1% Very Low - underestimated by 65 points)
- RioCan REIT: Expected ~48% High risk (v2.1 showed 1.3%)
- Dream Industrial REIT: Expected ~29% Moderate risk (v2.1 showed 1.4%)

---

## Archived Models

**Location:** `models/archive/`

### Model v2.1 (DEPRECATED)
- File: `distribution_cut_logistic_regression_v2.1_DEPRECATED.pkl`
- Reason: Underestimates severe distress by 27-58 percentage points
- See: `models/archive/README.md`

### Experimental Models
- LightGBM experiments (2025-10-22)
- XGBoost experiments (2025-10-22)
- Phase 1b prototypes
- v2.0 early development

---

## Training Data

**Location:** `data/training_dataset_v2_sustainable_afcf.csv`

**Structure:** 24 observations × 28 features + metadata

**Features (in order):**
1-3. Leverage metrics (total_debt, debt_to_assets_percent, net_debt_ratio)
4-7. Reported REIT metrics (ffo_reported, affo_reported, ffo_per_unit, affo_per_unit)
8-10. Distribution metrics (distributions_per_unit, ffo_payout_ratio, affo_payout_ratio)
11-16. Calculated metrics (ffo_calculated, affo_calculated, acfo_calculated, per-unit variants)
17-18. Coverage metrics (noi_interest_coverage, annualized_interest_expense)
19-21. Portfolio metrics (total_properties, occupancy_rate, same_property_noi_growth)
22-23. Liquidity metrics (available_cash, total_available_liquidity)
24-25. Burn rate metrics (monthly_burn_rate, self_funding_ratio)
26-28. Other (dilution_percentage, dilution_materiality, sector)

---

## Model Performance History

| Version | F1 Score | ROC AUC | Accuracy | Features | Notes |
|---------|----------|---------|----------|----------|-------|
| v2.2 | 0.870 | 0.930 | 87.5% | 28→15 | ✅ Production (sustainable AFCF) |
| v2.1 | 0.952 | 1.0 | 95.8% | 54→15 | ❌ Deprecated (underestimates distress) |
| v2.0 | - | - | - | 9 | ❌ Prototype (insufficient features) |

---

## Documentation

- **Model Analysis:** `docs/DISTRIBUTION_CUT_MODEL_DISCREPANCY_ANALYSIS.md`
- **AFCF Methodology:** `docs/AFCF_Methodology_Guidance_Note.md`
- **GitHub Issue:** #45 (Distribution Cut Prediction Model v2.2)
- **CLAUDE.md:** Lines 13-98 (complete model v2.2 documentation)

---

**Last Updated:** 2025-10-29
**Maintained By:** Claude Code
