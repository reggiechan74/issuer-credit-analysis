# Phase 1B Expansion - Download Plan (Option 2: Breadth)

**Target:** Add 11 new observations from 7 unique REITs
**Current:** 19 observations → **Target:** 30 observations

---

## 📋 Download List

### 1. RioCan REIT (REI-UN.TO) - PRIORITY 🎯
**Observations:** 2 (Q4 2023, Q4 2024)
**Type:** Likely TARGET (check for distribution cuts 2020-2024)
**Investor Relations:** https://www.riocan.com/investor-relations/

**Download:**
- [ ] **Obs 21:** Q4 2024 Annual Report + MD&A
  - File: 2024 Annual Financial Statements
  - File: 2024 Annual MD&A
  - Date: 2024-12-31
  - Notes: Most recent, check distribution history

- [ ] **Obs 22:** Q4 2023 Annual Report + MD&A
  - File: 2023 Annual Financial Statements
  - File: 2023 Annual MD&A
  - Date: 2023-12-31
  - Notes: Previous year comparison

---

### 2. SmartCentres REIT (SRU-UN.TO) - FIX INCOMPLETE
**Observations:** 1 (Q3 2023 - retry extraction)
**Type:** CONTROL
**Investor Relations:** https://www.smartcentres.com/investor-relations/

**Action:**
- [ ] **Obs 17 (Retry):** Q3 2023 Quarterly Report + MD&A
  - File: Q3 2023 Financial Statements
  - File: Q3 2023 MD&A
  - Date: 2023-09-30
  - Notes: Previous extraction failed (file too large), try manual extraction or split approach

---

### 3. Boardwalk REIT (BEI-UN.TO)
**Observations:** 2 (Q4 2023, Q4 2024)
**Type:** CONTROL (stable residential)
**Investor Relations:** https://www.bwalk.com/en/investor-relations/

**Download:**
- [ ] **Obs 23:** Q4 2024 Annual Report + MD&A
  - File: 2024 Annual Financial Statements
  - File: 2024 Annual MD&A
  - Date: 2024-12-31

- [ ] **Obs 24:** Q4 2023 Annual Report + MD&A
  - File: 2023 Annual Financial Statements
  - File: 2023 Annual MD&A
  - Date: 2023-12-31

---

### 4. Dream Industrial REIT (DIR-UN.TO)
**Observations:** 1 (Q4 2024)
**Type:** CONTROL (strong industrial sector)
**Investor Relations:** https://www.dreamindustrialreit.ca/investors/

**Download:**
- [ ] **Obs 25:** Q4 2024 Annual Report + MD&A
  - File: 2024 Annual Financial Statements
  - File: 2024 Annual MD&A
  - Date: 2024-12-31

---

### 5. First Capital REIT (FCR-UN.TO)
**Observations:** 1 (Q4 2023)
**Type:** Check for cuts (urban retail)
**Investor Relations:** https://www.fcr.ca/investor-relations/

**Download:**
- [ ] **Obs 26:** Q4 2023 Annual Report + MD&A
  - File: 2023 Annual Financial Statements
  - File: 2023 Annual MD&A
  - Date: 2023-12-31
  - Notes: Check distribution history for COVID-era cuts

---

### 6. Killam Apartment REIT (KMP-UN.TO)
**Observations:** 1 (Q4 2023)
**Type:** CONTROL (regional residential)
**Investor Relations:** https://killamreit.com/investor-relations/

**Download:**
- [ ] **Obs 27:** Q4 2023 Annual Report + MD&A
  - File: 2023 Annual Financial Statements
  - File: 2023 Annual MD&A
  - Date: 2023-12-31

---

### 7. Choice Properties REIT (CHP-UN.TO)
**Observations:** 1 (Q4 2024)
**Type:** CONTROL (Loblaw-controlled, very stable)
**Investor Relations:** https://www.choicereit.ca/investor-centre/

**Download:**
- [ ] **Obs 28:** Q4 2024 Annual Report + MD&A
  - File: 2024 Annual Financial Statements
  - File: 2024 Annual MD&A
  - Date: 2024-12-31

---

## 📊 Summary

**Total New Observations:** 11
- RioCan: 2
- SmartCentres: 1 (retry)
- Boardwalk: 2
- Dream Industrial: 1
- First Capital: 1
- Killam: 1
- Choice Properties: 1

**Expected Distribution:**
- Targets (cuts): +1-3 (RioCan?, First Capital?)
- Controls (no cuts): +8-10

**Final Dataset:**
- Total observations: 19 + 11 = **30**
- Unique REITs: 13 + 6 = **19 REITs**
- Coverage: **65-70%** of Canadian REIT universe

---

## 🚀 Execution Steps

### Step 1: Download PDFs (Today)
1. Visit each REIT's investor relations page
2. Navigate to "Financial Reports" or "Quarterly Results"
3. Download Annual/Quarterly Financial Statements PDF
4. Download Annual/Quarterly MD&A PDF
5. Save to `Issuer_Reports/{REIT_Name}/` folder

### Step 2: Phase 1 - PDF to Markdown (Day 1)
```bash
# Run for each new REIT
python scripts/preprocess_pdfs_enhanced.py \
  --issuer-name "RioCan REIT" \
  Issuer_Reports/RioCan_REIT/2024-Annual-FS.pdf \
  Issuer_Reports/RioCan_REIT/2024-Annual-MDA.pdf
```

### Step 3: Phase 2 - Markdown to JSON (Day 1-2)
```bash
# Use financial_data_extractor agent for each observation
# Save to: Issuer_Reports/phase1b/extractions/obs{N}_*_extracted_data.json
```

### Step 4: Phase 3 - Calculate Metrics (Day 2)
```bash
# Run for each extracted JSON
python scripts/calculate_credit_metrics.py \
  Issuer_Reports/phase1b/extractions/obs21_RioCan_Q4_2024_extracted_data.json
```

### Step 5: Collect Market + Macro Data (Day 2)
```bash
# Update ticker mapping
# Run automated collection
python scripts/collect_phase1b_market_data.py
```

### Step 6: Merge and Retrain (Day 3)
```bash
# Merge all datasets
python scripts/merge_training_dataset.py

# Retrain model
python scripts/train_distribution_cut_model.py
```

---

## 🎯 Expected Results

**With n=30 observations:**
- **Target F1:** 0.74-0.78
- **Expected accuracy:** 75-80%
- **Feature importance:** Should now have non-zero importance (sufficient data for tree splits)
- **ROC AUC:** >0.70 (better than random)

**Decision point:**
- If F1 ≥ 0.75: ✅ Hypothesis fully validated, model production-ready
- If F1 = 0.70-0.75: ⚠️ Partial success, consider Option 3 (Hybrid) for n=35-40
- If F1 < 0.70: ❌ Investigate feature engineering or alternative models

---

**Start Date:** 2025-10-22
**Target Completion:** 2025-10-25 (3 days)
**Estimated Time:** 8-12 hours total work

