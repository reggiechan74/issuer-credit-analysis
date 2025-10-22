# Option B: Full PDF Pipeline for Control REIT Metrics

**Status:** PLAN ONLY (not implemented)
**Created:** 2025-10-22
**Purpose:** Future reference if web-based extraction (Option A) proves insufficient

---

## Overview

Extract control REIT financial metrics using the full 5-phase PDF processing pipeline instead of web-based extraction.

**When to Use:**
- Web-based extraction fails or provides incomplete data
- Need comprehensive data for all REALPAC metrics (FFO/AFFO/ACFO components)
- Building larger training dataset requiring detailed reconciliation tables
- Quality concerns about web-extracted metrics

**Trade-offs:**
- **More thorough:** Complete Phase 2 extraction with all 26 REALPAC adjustments
- **More time:** 2-3 hours vs 30-60 minutes for web-based
- **More cost:** ~$0.90 (3 × $0.30 per issuer) vs minimal web search costs
- **Better validation:** Schema validation, automatic consistency checks

---

## Implementation Plan

### Phase 1: Download Q2 2025 Financial Reports

**For each control REIT (CAPREIT, SmartCentres, Dream Industrial):**

1. **Navigate to SEDAR+:**
   - Go to https://www.sedarplus.ca
   - Search by ticker: CAR-UN, SRU-UN, DIR-UN
   - Filter: "Financial Statements" + "Interim" + Q2 2025

2. **Download Required Files:**
   - **Condensed Consolidated Financial Statements (Q2 2025)**
     - Contains: Balance sheet, income statement, cash flow statement
     - File type: PDF (usually 20-40 pages)
   - **Management Discussion & Analysis (Q2 2025)**
     - Contains: FFO/AFFO reconciliations, operational metrics, covenant disclosures
     - File type: PDF (usually 30-60 pages)

3. **Save to Temp Directory:**
   ```
   /workspaces/issuer-credit-analysis/temp/
     CAPREIT_Q2_2025_Financials.pdf
     CAPREIT_Q2_2025_MDA.pdf
     SmartCentres_Q2_2025_Financials.pdf
     SmartCentres_Q2_2025_MDA.pdf
     DreamIndustrial_Q2_2025_Financials.pdf
     DreamIndustrial_Q2_2025_MDA.pdf
   ```

**Expected Time:** 15-20 minutes

---

### Phase 2: Run PDF → Markdown Conversion (Phase 1)

**Sequential Execution (3 issuers):**

```bash
# CAPREIT
python scripts/preprocess_pdfs_enhanced.py \
  --issuer-name "CAPREIT" \
  temp/CAPREIT_Q2_2025_Financials.pdf \
  temp/CAPREIT_Q2_2025_MDA.pdf

# SmartCentres REIT
python scripts/preprocess_pdfs_enhanced.py \
  --issuer-name "SmartCentres REIT" \
  temp/SmartCentres_Q2_2025_Financials.pdf \
  temp/SmartCentres_Q2_2025_MDA.pdf

# Dream Industrial REIT
python scripts/preprocess_pdfs_enhanced.py \
  --issuer-name "Dream Industrial REIT" \
  temp/DreamIndustrial_Q2_2025_Financials.pdf \
  temp/DreamIndustrial_Q2_2025_MDA.pdf
```

**Output Structure:**
```
Issuer_Reports/
  CAPREIT/temp/phase1_markdown/
    CAPREIT_Q2_2025_Financials.md
    CAPREIT_Q2_2025_MDA.md
  SmartCentres_REIT/temp/phase1_markdown/
    SmartCentres_Q2_2025_Financials.md
    SmartCentres_Q2_2025_MDA.md
  Dream_Industrial_REIT/temp/phase1_markdown/
    DreamIndustrial_Q2_2025_Financials.md
    DreamIndustrial_Q2_2025_MDA.md
```

**Expected Time:** 30-45 seconds (10-15s per issuer)

---

### Phase 3: Extract Structured JSON (Phase 2)

**Sequential Execution (MUST run after Phase 1 completes):**

```bash
# CAPREIT
python scripts/extract_key_metrics_efficient.py \
  --issuer-name "CAPREIT" \
  Issuer_Reports/CAPREIT/temp/phase1_markdown/*.md

# SmartCentres REIT
python scripts/extract_key_metrics_efficient.py \
  --issuer-name "SmartCentres REIT" \
  Issuer_Reports/SmartCentres_REIT/temp/phase1_markdown/*.md

# Dream Industrial REIT
python scripts/extract_key_metrics_efficient.py \
  --issuer-name "Dream Industrial REIT" \
  Issuer_Reports/Dream_Industrial_REIT/temp/phase1_markdown/*.md
```

**Output:**
```
Issuer_Reports/
  CAPREIT/temp/phase2_extracted_data.json
  SmartCentres_REIT/temp/phase2_extracted_data.json
  Dream_Industrial_REIT/temp/phase2_extracted_data.json
```

**Expected Time:** 15-30 minutes (5-10 minutes per issuer, ~1K tokens each)

---

### Phase 4: Validate Extraction Schema

**Before proceeding, validate each extraction:**

```bash
python scripts/validate_extraction_schema.py \
  Issuer_Reports/CAPREIT/temp/phase2_extracted_data.json

python scripts/validate_extraction_schema.py \
  Issuer_Reports/SmartCentres_REIT/temp/phase2_extracted_data.json

python scripts/validate_extraction_schema.py \
  Issuer_Reports/Dream_Industrial_REIT/temp/phase2_extracted_data.json
```

**Fix any schema violations before Phase 3 calculations**

**Expected Time:** 2-3 minutes

---

### Phase 5: Calculate Credit Metrics (Phase 3)

**Run metric calculations:**

```bash
python scripts/calculate_credit_metrics.py \
  Issuer_Reports/CAPREIT/temp/phase2_extracted_data.json

python scripts/calculate_credit_metrics.py \
  Issuer_Reports/SmartCentres_REIT/temp/phase2_extracted_data.json

python scripts/calculate_credit_metrics.py \
  Issuer_Reports/Dream_Industrial_REIT/temp/phase2_extracted_data.json
```

**Output:**
```
Issuer_Reports/
  CAPREIT/temp/phase3_calculated_metrics.json
  SmartCentres_REIT/temp/phase3_calculated_metrics.json
  Dream_Industrial_REIT/temp/phase3_calculated_metrics.json
```

**Expected Time:** < 5 seconds (pure Python calculations)

---

### Phase 6: Extract Key Metrics for Training Dataset

**Read Phase 3 outputs and extract:**

For each issuer, extract from `phase3_calculated_metrics.json`:

```json
{
  "affo_payout_ratio": <from affo_metrics.affo_payout_ratio>,
  "interest_coverage": <from coverage_metrics.interest_coverage_noi>,
  "debt_to_assets": <from leverage_metrics.debt_to_assets_pct>,
  "debt_to_ebitda": <from leverage_metrics.debt_to_ebitda>,
  "occupancy_rate": <from portfolio.occupancy_rate>,
  "sector": <from metadata.sector>,
  "liquidity_risk_score": <from liquidity_risk.risk_score>
}
```

**Manual Step:** Update `data/training_dataset_v1.csv` with extracted values

**Expected Time:** 10-15 minutes

---

### Phase 7: Re-run Feature Engineering

**Regenerate training_dataset_v2.csv with complete control metrics:**

```bash
python scripts/feature_engineering.py \
  --input data/training_dataset_v1.csv \
  --output data/training_dataset_v2.csv
```

**Expected Output:** 9 observations × 43 features (NO missing control metrics)

**Expected Time:** < 5 seconds

---

## Total Timeline

| Step | Time | Notes |
|------|------|-------|
| Download PDFs from SEDAR+ | 15-20 min | Manual |
| Phase 1 (PDF→Markdown) | 30-45 sec | Automated |
| Phase 2 (Markdown→JSON) | 15-30 min | Automated |
| Schema Validation | 2-3 min | Automated |
| Phase 3 (Calculations) | < 5 sec | Automated |
| Extract to Training Dataset | 10-15 min | Manual |
| Re-run Feature Engineering | < 5 sec | Automated |
| **TOTAL** | **45-75 min** | **~2-3 hours with contingency** |

---

## Cost Estimate

**Token Usage (per issuer):**
- Phase 1: 0 tokens
- Phase 2: ~1,000 tokens (file references)
- Phase 3: 0 tokens
- **Total per issuer:** ~1,000 tokens × 3 = ~3,000 tokens

**Cost:** ~$0.075 (minimal, primarily from Phase 2 extraction)

**Note:** Much cheaper than original estimate because Phase 2 uses file references, not embedded markdown

---

## Advantages Over Web-Based (Option A)

1. **Comprehensive Data:** All 26 REALPAC FFO/AFFO adjustments + 17 ACFO adjustments
2. **Schema Validation:** Automatic consistency checks and validation
3. **Audit Trail:** Markdown files preserved for verification
4. **Per-Unit Calculations:** Both basic and diluted share bases
5. **Dilution Analysis:** Detailed dilution tracking if disclosed (v1.0.8)
6. **AFCF Metrics:** Full free cash flow analysis if CFI/CFF data available (v1.0.6)
7. **Quality Assurance:** Phase 3 validation checks (balance sheet balancing, NOI margins, etc.)

---

## Disadvantages vs Web-Based

1. **Time:** 2-3 hours vs 30-60 minutes
2. **Manual Steps:** PDF downloads, metric extraction to CSV
3. **Overkill:** Only need 4-5 metrics for training dataset, not full 43 features
4. **Complexity:** 7 steps vs 1 step (parallel web extraction)

---

## When to Use This Approach

**Use Option B (PDF Pipeline) when:**
- Web-based extraction fails or incomplete
- Need comprehensive REALPAC metrics for larger training dataset
- Building production-grade model requiring detailed reconciliation
- Quality concerns about web-extracted data
- Future model expansion requiring all 43 engineered features

**Use Option A (Web-Based) when:**
- Need quick results (30-60 minutes)
- Only need 4-5 key metrics (sufficient for initial model)
- Web sources are reliable and complete
- Prototyping or proof-of-concept phase

---

## Future Enhancements

If implementing Option B, consider:

1. **Automation:** Script to download PDFs from SEDAR+ automatically
2. **Parallel Phase 2:** Run 3 Phase 2 extractions in parallel (requires Task tool with 3 agents)
3. **Direct CSV Export:** Phase 3 output directly to CSV row (skip manual extraction step)
4. **Batch Validation:** Single command to validate all 3 extractions

---

## References

- Pipeline architecture: `CLAUDE.md` (lines 50-95)
- Phase 2 schema: `.claude/knowledge/phase2_extraction_schema.json`
- Extraction guide: `.claude/knowledge/COMPREHENSIVE_EXTRACTION_GUIDE.md`
- Feature engineering: `scripts/feature_engineering.py`

---

**Status:** PLAN ONLY - Not implemented
**Decision:** Use Option A (web-based extraction) for Week 2 control metrics
**Future Use:** Reference this plan if web-based approach proves insufficient
