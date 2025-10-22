# CAPREIT Q2 2025 Missing Metrics - Manual Extraction Template

**Status:** Awaiting manual extraction from PDF
**PDF File:** `Issuer_FS/CapREIT/CAPREITQ2-2025-Full-Report-SEDAR.pdf`
**Purpose:** Fill in missing metrics for training_dataset_v1.csv (Issue #37)

---

## Instructions

Please read the PDF manually and fill in the values below. Once complete, update `data/training_dataset_v1.csv` line 8 (CAR-UN.TO row) with these values.

---

## Missing Metrics for Training Dataset

### 1. AFFO Payout Ratio (%)
**Where to find:** Look in MD&A section "Non-IFRS Measures" → "Funds From Operations" or "Adjusted Cash Flow from Operations"

**Look for:**
- Table showing "FFO per unit" and "AFFO per unit" or "ACFO per unit"
- Usually has columns for "Three Months Ended June 30, 2025" and "Six Months Ended June 30, 2025"
- Look for "FFO payout ratio" or "ACFO payout ratio" calculated as: Distributions / FFO (or ACFO)

**Expected format:** Percentage (e.g., 85.3 means 85.3%)

**Value to extract:**
```
ACFO Payout Ratio (Q2 2025): 99.6%%
```

**Notes:**
- If AFFO not disclosed, use ACFO payout ratio instead
- Prefer TTM (trailing twelve months) if available
- If only quarterly, note that

---

### 2. Interest Coverage Ratio
**Where to find:** Look in "Non-IFRS Measures" section → "Interest Coverage Ratio"

**Look for:**
- Section titled "Interest Coverage Ratio" (usually page 60-65 of MD&A)
- Formula: Adjusted EBITDAFV ÷ Interest Expense
- Table showing trailing 12 months calculation
- Look for covenant disclosure (may say "Interest Coverage Ratio as at June 30, 2025: X.Xx")

**Expected format:** Decimal ratio (e.g., 2.75 means 2.75x coverage)

**Value to extract:**
```
Interest Coverage Ratio (as at June 30, 2025): 3.3x
```

**Notes:**
- Should be in the 2.5-3.5x range for CAPREIT (residential REIT)
- Look for "Trailing 12 months" or "TTM" column

---

### 3. Debt to Assets Ratio (%)
**Where to find:** Look in "Non-IFRS Measures" section → "Total Debt and Total Debt Ratios"

**Look for:**
- Section titled "Total Debt to Gross Book Value" (usually page 59-62 of MD&A)
- Table showing: Total Debt / Gross Book Value (GBV)
- Formula: Total Debt ÷ Gross Book Value × 100%
- Look for row "Total Debt to Gross Book Value" with percentage

**Expected format:** Percentage (e.g., 45.2 means 45.2%)

**Value to extract:**
```
Total Debt to Gross Book Value (as at June 30, 2025): ______________38.5%
```

**Notes:**
- Should be in the 40-50% range for CAPREIT (conservative leverage)
- Also called "Debt/GBV ratio" or "Leverage ratio"

---

### 4. Debt to EBITDA Ratio (optional)
**Where to find:** May be in "Non-IFRS Measures" or covenant disclosure sections

**Look for:**
- "Debt to EBITDA" or "Net Debt to EBITDA" or "Net Debt to Adjusted EBITDAFV"
- Usually disclosed if required by debt covenants

**Expected format:** Decimal ratio (e.g., 8.5 means 8.5x)

**Value to extract:**
```
Debt to EBITDA (if disclosed): not disclosed x

Or: Not disclosed ☐
```

---

## Additional Context (Already Extracted)

These values were successfully extracted via PDF conversion:

✅ **Occupancy Rate:** 98.3% (Total Canadian residential suites)
✅ **Available Liquidity:** $140,970,000 ($141M)
✅ **Sector:** Residential
✅ **Reporting Period:** Q2 2025 (June 30, 2025)

---

## Validation Checks

After filling in the values, verify they make sense:

- [ ] AFFO/ACFO payout ratio is between 60-95% (healthy for residential REIT)
- [ ] Interest coverage is between 2.0-4.0x (typical for residential)
- [ ] Debt/Assets is between 35-55% (conservative to moderate leverage)
- [ ] All values are from Q2 2025 or trailing twelve months (TTM)

---

## How to Update training_dataset_v1.csv

Once you have the values, update line 8 in `data/training_dataset_v1.csv`:

**Current line 8:**
```csv
CAR-UN.TO,2025-10,Residential,0,3.0234,0.2326,13,39.3,7.69,,,,,999+,,1,moderate,"Q2 2025: Occupancy 98.3%, Liquidity $141M available, PDF extraction incomplete (table values not captured), residential leader with 26-year distribution history"
```

**Updated line 8 (example with filled values):**
```csv
CAR-UN.TO,2025-10,Residential,0,3.0234,0.2326,13,39.3,7.69,[AFFO_PAYOUT],[INTEREST_COV],[DEBT_EBITDA],,999+,[DEBT_ASSETS],1,good,"Q2 2025: AFFO payout [X]%, Interest coverage [X]x, Debt/Assets [X]%, Occupancy 98.3%, Liquidity $141M, Canada's largest residential REIT"
```

**Field positions:**
- Column 10: `affo_payout_ratio` (e.g., 85.3)
- Column 11: `interest_coverage` (e.g., 2.75)
- Column 12: `debt_to_ebitda` (e.g., 8.5 or leave blank if not disclosed)
- Column 15: `debt_to_assets` (e.g., 45.2)

---

## After Updating

1. Save `data/training_dataset_v1.csv`
2. Re-run feature engineering:
   ```bash
   python scripts/feature_engineering.py --input data/training_dataset_v1.csv --output data/training_dataset_v2.csv
   ```
3. Verify the new risk score separation includes CAPREIT's complete metrics
4. Commit the changes:
   ```bash
   git add data/training_dataset_v1.csv data/training_dataset_v2.csv
   git commit -m "fix: Complete CAPREIT Q2 2025 metrics via manual PDF extraction"
   ```

---

## Reference: Comparable Control REITs

For context, here are the other 2 control REITs:

**SmartCentres (SRU-UN.TO) - Retail:**
- AFFO Payout: 85.3%
- Interest Coverage: 2.6x
- Debt/Assets: 44.2%

**Dream Industrial (DIR-UN.TO) - Industrial:**
- FFO Payout: 67.3%
- Interest Coverage: 5.1x
- Debt/Assets: 38.0%

CAPREIT (Residential) should show similar healthy metrics given its 26-year distribution history and strong operational performance.
