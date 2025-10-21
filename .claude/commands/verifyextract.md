---
description: Verify Phase 2 extraction accuracy by comparing extracted JSON against Phase 1 markdown (converted from source PDFs)
tags: [validation, quality-assurance, phase-2, extraction-verification]
---

# Verify Data Extraction Accuracy

You are a data extraction quality assurance expert tasked with verifying that the **Phase 2 extracted JSON data** accurately reflects the financial information in the **Phase 1 markdown files** (converted from source PDFs).

## Command Arguments

- `$1`: Issuer name (e.g., "Artis REIT")

**Example Usage:**
```bash
/verifyextract "Artis REIT"
```

## Validation Scope

**Purpose:** Ensure Phase 2 extraction accurately captured data from Phase 1 markdown:
1. ✅ **Balance sheet** - Assets, Liabilities, Equity correctly extracted
2. ✅ **Income statement** - Revenue, NOI, Interest correctly extracted
3. ✅ **FFO/AFFO** - Issuer-reported reconciliation correctly extracted
4. ✅ **Portfolio metrics** - Properties, GLA, occupancy correctly extracted
5. ✅ **Debt** - Mortgages and credit facilities correctly extracted

**NOT validating:** PDF-to-markdown conversion accuracy (that's Phase 1 validation)

---

## Step 1: Locate Files

Based on the issuer name provided, locate the following files:

**Note:** Sanitize issuer name for folder structure (replace spaces with underscores).

### Required Files

1. **Phase 1 Markdown** (converted PDFs):
   - `./Issuer_Reports/{Issuer_Name}/temp/phase1_markdown/*.md`
   - Look for files like: `MD&A_Q2_2025.md`, `Financial_Statements_Q2_2025.md`

2. **Phase 2 Extracted Data** (structured JSON):
   - `./Issuer_Reports/{Issuer_Name}/temp/phase2_extracted_data.json`

**Token Budget:** Reading Phase 1 markdown can be large (~100-140K tokens). Focus on specific sections:
- Consolidated Balance Sheet
- Consolidated Statement of Income
- FFO/AFFO Reconciliation tables
- Portfolio summary tables
- Debt note disclosures

---

## Step 2: Extract Values from Phase 1 Markdown

Search Phase 1 markdown files for key financial data. Use grep-style searching for specific values.

### A. Balance Sheet (as of reporting date)

**Search for:** "Consolidated Balance Sheet" or "Statement of Financial Position"

Extract:
- **Total Assets** - Look for "Total assets"
- **Total Liabilities** - Look for "Total liabilities"
- **Unitholders' Equity** - Look for "Unitholders' equity" or "Total equity"
- **Current Mortgages Payable** - Look for "Mortgages payable" (current portion)
- **Non-Current Mortgages Payable** - Look for "Mortgages payable" (non-current)
- **Credit Facilities** - Look for "Credit facilities" or "Revolving credit facility"
- **Cash and Cash Equivalents** - Look for "Cash and cash equivalents"
- **Common Units Outstanding** - Look for "Weighted average" units (basic)
- **Diluted Units Outstanding** - Look for "Weighted average" units (diluted)

### B. Income Statement (reporting period)

**Search for:** "Consolidated Statement of Income" or "Statement of Comprehensive Income"

Extract for **6-month period** (or applicable period):
- **Revenue** - Look for "Revenue from property operations" or "Rental revenue"
- **Property Operating Expenses** - Look for "Property operating expenses"
- **Realty Taxes** - Look for "Realty taxes"
- **NOI** - Calculate or look for "Net operating income"
- **Interest Expense** - Look for "Interest expense" or "Finance costs"
- **Net Income** - Look for "Net income" or "Net (loss) income"
- **Cash Flow from Operations** - Look for "Operating activities" in cash flow statement

### C. FFO/AFFO Reconciliation (if reported)

**Search for:** "FFO" or "Funds from Operations" or "AFFO" in MD&A

Extract:
- **FFO Total** - Issuer-reported FFO for the period
- **FFO Per Unit** - Issuer-reported FFO per unit
- **AFFO Total** - Issuer-reported AFFO for the period
- **AFFO Per Unit** - Issuer-reported AFFO per unit
- **ACFO Total** - Issuer-reported ACFO (rare)
- **ACFO Per Unit** - Issuer-reported ACFO per unit (rare)
- **Distributions Per Unit** - Declared distributions per unit
- **FFO Payout Ratio** - Calculated or reported
- **AFFO Payout Ratio** - Calculated or reported

### D. Portfolio Metrics

**Search for:** "Portfolio Summary" or "Property Portfolio"

Extract:
- **Total Properties** - Number of properties owned
- **Total GLA** - Gross leasable area (square feet)
- **Occupancy Rate** - Committed occupancy percentage
- **Occupancy with Commitments** - Including signed but not commenced leases

### E. Debt Details (from notes)

**Search for:** Note on "Mortgages Payable" and "Credit Facilities"

Extract:
- **Total Debt** - Sum of all mortgages and credit facilities
- **Weighted Average Interest Rate** - On debt
- **Debt Maturity Schedule** - Upcoming maturities
- **Undrawn Credit Capacity** - Available on credit facilities

---

## Step 3: Read Phase 2 Extracted JSON

Load and parse the Phase 2 JSON file to extract the same metrics.

**Structure:** See `.claude/knowledge/phase2_extraction_schema.json` for schema

**Extract:**
- `balance_sheet` - All balance sheet items
- `income_statement` - All income statement items
- `ffo_affo` - FFO/AFFO metrics
- `portfolio` - Portfolio metrics
- `debt` - Debt metrics

---

## Step 4: Perform Validation Checks

### A. BALANCE SHEET VALIDATION

**Compare:** Phase 1 Markdown → Phase 2 JSON

| Item | Phase 1 Markdown | Phase 2 JSON | Tolerance | Status |
|------|------------------|--------------|-----------|--------|
| **Total Assets** | ... | `balance_sheet.total_assets` | ±$1K | ✅/❌ |
| **Total Liabilities** | ... | `balance_sheet.total_liabilities` | ±$1K | ✅/❌ |
| **Unitholders' Equity** | ... | `balance_sheet.unitholders_equity` | ±$1K | ✅/❌ |
| **Mortgages Payable (Current)** | ... | `balance_sheet.mortgages_current` | ±$1K | ✅/❌ |
| **Mortgages Payable (Non-Current)** | ... | `balance_sheet.mortgages_non_current` | ±$1K | ✅/❌ |
| **Credit Facilities** | ... | `balance_sheet.credit_facilities` | ±$1K | ✅/❌ |
| **Cash & Equivalents** | ... | `balance_sheet.cash_and_equivalents` | ±$1K | ✅/❌ |
| **Common Units Outstanding** | ... | `balance_sheet.common_units_outstanding` | Exact | ✅/❌ |
| **Diluted Units Outstanding** | ... | `balance_sheet.diluted_units_outstanding` | Exact | ✅/❌ |

**Validation Rules:**
1. All values must match within tolerance (±$1K for thousands)
2. Balance sheet equation must hold: Assets = Liabilities + Equity
3. Total Debt = Mortgages (current + non-current) + Credit Facilities

**Expected:** 9/9 balance sheet items correct

### B. INCOME STATEMENT VALIDATION

**Compare:** Phase 1 Markdown → Phase 2 JSON

| Item | Phase 1 Markdown | Phase 2 JSON | Tolerance | Status |
|------|------------------|--------------|-----------|--------|
| **Revenue** | ... | `income_statement.revenue` | ±$1K | ✅/❌ |
| **Property Operating Expenses** | ... | `income_statement.property_operating_expenses` | ±$1K | ✅/❌ |
| **Realty Taxes** | ... | `income_statement.realty_taxes` | ±$1K | ✅/❌ |
| **NOI** | ... | `income_statement.noi` | ±$1K | ✅/❌ |
| **Interest Expense** | ... | `income_statement.interest_expense` | ±$1K | ✅/❌ |
| **Net Income** | ... | `income_statement.net_income` | ±$1K | ✅/❌ |
| **Cash Flow from Operations** | ... | `income_statement.cash_flow_from_operations` | ±$1K | ✅/❌ |

**Validation Rules:**
1. All values must match within tolerance
2. NOI = Revenue - Property OpEx - Realty Taxes (verify calculation)
3. Period consistency (Q2, 6-month, annual) must match

**Expected:** 7/7 income statement items correct

### C. FFO/AFFO VALIDATION (if reported by issuer)

**Compare:** Phase 1 Markdown → Phase 2 JSON

| Item | Phase 1 Markdown | Phase 2 JSON | Tolerance | Status |
|------|------------------|--------------|-----------|--------|
| **FFO Total** | ... | `ffo_affo.ffo` | ±$1K | ✅/❌ |
| **FFO Per Unit** | ... | `ffo_affo.ffo_per_unit` | ±$0.0001 | ✅/❌ |
| **AFFO Total** | ... | `ffo_affo.affo` | ±$1K | ✅/❌ |
| **AFFO Per Unit** | ... | `ffo_affo.affo_per_unit` | ±$0.0001 | ✅/❌ |
| **ACFO Total** | ... | `ffo_affo.acfo` | ±$1K | ✅/❌/⚠️ N/A |
| **ACFO Per Unit** | ... | `ffo_affo.acfo_per_unit` | ±$0.0001 | ✅/❌/⚠️ N/A |
| **Distributions Per Unit** | ... | `ffo_affo.distributions_per_unit` | ±$0.0001 | ✅/❌ |
| **FFO Payout Ratio** | ... | `ffo_affo.ffo_payout_ratio` | ±0.1% | ✅/❌ |
| **AFFO Payout Ratio** | ... | `ffo_affo.affo_payout_ratio` | ±0.1% | ✅/❌ |

**Validation Rules:**
1. Per-unit values must be precise (4 decimal places)
2. Payout ratios should match or be calculated: (Dist / Metric per unit) × 100
3. ACFO is rarely reported - mark as "N/A" if not in Phase 1

**Expected:** 7-9 FFO/AFFO items correct (depending on what issuer reports)

### D. PORTFOLIO METRICS VALIDATION

**Compare:** Phase 1 Markdown → Phase 2 JSON

| Item | Phase 1 Markdown | Phase 2 JSON | Tolerance | Status |
|------|------------------|--------------|-----------|--------|
| **Total Properties** | ... | `portfolio.total_properties` | Exact | ✅/❌ |
| **Total GLA (sq ft)** | ... | `portfolio.total_gla_sf` | ±1,000 | ✅/❌ |
| **Occupancy Rate** | ... | `portfolio.occupancy_rate` | ±0.1% | ✅/❌ |
| **Occupancy w/ Commitments** | ... | `portfolio.occupancy_including_commitments` | ±0.1% | ✅/❌ |

**Validation Rules:**
1. Property count must match exactly
2. GLA within ±1,000 sq ft tolerance
3. Occupancy rates as decimals (0.878 = 87.8%)

**Expected:** 4/4 portfolio metrics correct

### E. DEBT VALIDATION

**Compare:** Phase 1 Markdown → Phase 2 JSON

| Item | Phase 1 Markdown | Phase 2 JSON | Tolerance | Status |
|------|------------------|--------------|-----------|--------|
| **Total Debt** | ... | Calculated from JSON | ±$1K | ✅/❌ |
| **Weighted Avg Interest Rate** | ... | `debt.weighted_average_interest_rate` | ±0.1% | ✅/❌ |
| **Undrawn Credit Capacity** | ... | `liquidity.undrawn_credit_facilities` | ±$1K | ✅/❌ |

**Validation Rules:**
1. Total Debt = Mortgages (current + non-current) + Credit Facilities
2. Interest rate as decimal (0.045 = 4.5%)

**Expected:** 3/3 debt metrics correct

### F. DATA INTEGRITY CHECKS

**Phase 2 JSON Internal Consistency:**

1. **Balance Sheet Equation:**
   ```
   Check: total_assets = total_liabilities + unitholders_equity
   Tolerance: ±$5K (rounding across multiple line items)
   Status: ✅/❌
   ```

2. **NOI Calculation:**
   ```
   Check: NOI = Revenue - Property OpEx - Realty Taxes
   Tolerance: ±$2K
   Status: ✅/❌
   ```

3. **Total Debt Aggregation:**
   ```
   Check: Total Debt = Mortgages (current + non-current) + Credit Facilities
   Tolerance: ±$1K
   Status: ✅/❌
   ```

4. **FFO Payout Ratio:**
   ```
   Check: FFO Payout = (Distributions per unit / FFO per unit) × 100
   Tolerance: ±0.5% (rounding)
   Status: ✅/❌
   ```

---

## Step 5: Generate Extraction Validation Report

### Validation Summary

```markdown
## Extraction Validation Summary

✅ **PASSED:** XX/XX checks (XX.X%)
❌ **FAILED:** X/XX checks
⚠️  **WARNINGS:** X issues requiring attention

**Overall Status:** PASS / FAIL / PASS WITH WARNINGS
```

### Critical Extraction Errors (if any)

```markdown
## Critical Errors: X

1. ❌ **[Item]:** Extraction mismatch
   - **Phase 1 Markdown:** [Value found in markdown]
   - **Phase 2 JSON:** [Value in extracted JSON]
   - **Difference:** [Amount/percentage]
   - **Impact:** Material misstatement in [balance sheet/income statement]
   - **Recommended Fix:** Re-extract with corrected prompt

2. ❌ **Missing Data:** [Item] not extracted but present in Phase 1
   - **Phase 1 Markdown:** [Value visible in markdown]
   - **Phase 2 JSON:** null or missing
   - **Location:** [File and approximate line number in markdown]
   - **Recommended Fix:** Update extraction prompt to capture [item]
```

### Warnings (if any)

```markdown
## Warnings: X

1. ⚠️  **Rounding Difference:** [Item]
   - **Phase 1 Markdown:** [Value]
   - **Phase 2 JSON:** [Value]
   - **Difference:** [Small amount within tolerance but worth noting]
   - **Impact:** Minor, within tolerance

2. ⚠️  **Data Quality:** [Item] has inconsistent format
   - **Phase 1 Markdown:** [Format issue description]
   - **Phase 2 JSON:** [How it was interpreted]
   - **Recommendation:** Review extraction logic
```

### Validated Items

```markdown
## Validated Items: XX

### Balance Sheet Validation
✅ Total Assets: Correct
✅ Total Liabilities: Correct
✅ Unitholders' Equity: Correct
✅ Mortgages Payable: Correct
✅ Credit Facilities: Correct
✅ Cash & Equivalents: Correct
✅ Units Outstanding: Correct

### Income Statement Validation
✅ Revenue: Correct
✅ NOI: Correct
✅ Interest Expense: Correct
✅ Net Income: Correct
✅ Cash Flow from Ops: Correct

### FFO/AFFO Validation
✅ FFO: Correct
✅ AFFO: Correct
✅ Distributions: Correct
✅ Payout Ratios: Correct

### Portfolio Validation
✅ Total Properties: Correct
✅ Total GLA: Correct
✅ Occupancy: Correct

### Debt Validation
✅ Total Debt: Correct
✅ Interest Rate: Correct

### Data Integrity Checks
✅ Balance Sheet Equation: Valid
✅ NOI Calculation: Consistent
✅ Debt Aggregation: Correct
```

---

## Step 6: Detailed Validation Tables

Include all comparison tables from Step 4 with actual values filled in.

---

## Step 7: Recommendations

### If Extraction Errors Found:

```markdown
## Recommendations

### Critical Errors - Re-Extraction Required

1. **Fix [Item] Extraction:**
   - **Issue:** Value mismatch between Phase 1 and Phase 2
   - **Root Cause:** [Likely cause - table parsing error, wrong period, etc.]
   - **Action:** Re-run Phase 2 extraction with corrected prompt
   - **Updated Prompt:** [Specific prompt improvement]

2. **Add Missing Field:**
   - **Issue:** [Item] not extracted from Phase 1
   - **Root Cause:** Extraction prompt doesn't look for this field
   - **Action:** Update `.claude/knowledge/COMPREHENSIVE_EXTRACTION_GUIDE.md`
   - **Prompt Addition:** [Specific guidance to add]

### Warnings - Review Recommended

1. **Review Rounding:**
   - Minor rounding differences in [items]
   - Consider if more precision needed
   - Current tolerance: ±$1K may be too loose

2. **Verify Period Consistency:**
   - Ensure all metrics are from same reporting period
   - Check for Q2 vs 6-month vs annual mixing
```

### If All Passed:

```markdown
## Recommendations

✅ **All extractions validated successfully** - Phase 2 JSON is accurate

**Quality Checks Completed:**
- [X] All balance sheet items correctly extracted
- [X] All income statement items correctly extracted
- [X] FFO/AFFO metrics correctly extracted
- [X] Portfolio metrics correctly extracted
- [X] Data integrity checks passed

**Next Steps:**
- Phase 2 JSON is ready for Phase 3 calculations
- No re-extraction needed
- Consider this validation a baseline for future extractions
```

---

## Output Format Template

```markdown
# Extraction Validation: {Issuer Name}

**Phase 1 Source:** {List of markdown files}
**Phase 2 Extracted:** phase2_extracted_data.json
**Validation Date:** {current date}
**Validator:** Claude Code /verifyextract command

---

## Extraction Validation Summary

✅ **PASSED:** XX/XX checks (XX.X%)
❌ **FAILED:** X/XX checks
⚠️  **WARNINGS:** X issues

**Overall Status:** [PASS / FAIL / PASS WITH WARNINGS]

---

## Critical Errors: X

[List errors with Phase 1 values vs Phase 2 values]

---

## Warnings: X

[List warnings]

---

## Validated Items: XX

[Summary of validated extractions]

---

## Detailed Validation Results

### A. Balance Sheet Validation

[Complete comparison table with all values]

### B. Income Statement Validation

[Complete comparison table with all values]

### C. FFO/AFFO Validation

[Complete comparison table with all values]

### D. Portfolio Metrics Validation

[Complete comparison table with all values]

### E. Debt Validation

[Complete comparison table with all values]

### F. Data Integrity Checks

[Results of internal consistency checks]

---

## Recommendations

[Specific recommendations based on findings]

---

**Extraction Validation Complete** ✓
```

---

## Important Guidelines

1. **Be Specific:**
   - Quote exact values from Phase 1 markdown (with line numbers if possible)
   - Show exact JSON path in Phase 2 (e.g., `balance_sheet.total_assets`)
   - Calculate differences (both absolute and percentage)

2. **Context Matters:**
   - Note which markdown file the value came from
   - Note the reporting period (Q2, 6-month, annual)
   - Identify table or section in markdown

3. **Tolerance Appropriate:**
   - Thousands (000s): ±$1K
   - Per-unit values: ±$0.0001
   - Percentages: ±0.1%
   - Counts: Exact match

4. **Distinguish Error Types:**
   - **Missing extraction:** Field not in JSON but in markdown
   - **Wrong value:** Field in JSON but incorrect value
   - **Wrong period:** Right field but wrong time period
   - **Calculation error:** Derived field calculated incorrectly

5. **Actionable Fixes:**
   - For missing fields: Suggest prompt additions
   - For wrong values: Suggest table parsing improvements
   - For period issues: Suggest period validation logic

---

## Success Criteria

A successful extraction validation should:

- ✅ Validate 100% of critical balance sheet items
- ✅ Validate 100% of critical income statement items
- ✅ Verify data integrity (balance sheet equation, calculations)
- ✅ Identify any extraction errors with specific values
- ✅ Provide actionable recommendations for re-extraction if needed
- ✅ Give confidence that Phase 2 JSON is ready for Phase 3 calculations

---

## Error Handling

**If Phase 1 markdown files are missing:**
1. List expected file locations
2. Cannot perform validation
3. Mark validation as **INCOMPLETE**

**If Phase 2 JSON is malformed:**
1. Report JSON parsing error
2. Show first error encountered
3. Recommend checking JSON validity

**If Phase 1 markdown is too large (>150K tokens):**
1. Focus on critical sections only:
   - Balance Sheet table
   - Income Statement table
   - FFO/AFFO table (if present)
   - Portfolio summary
2. Skip narrative sections
3. Note partial validation in summary

---

## Integration with /verifyreport

These two validation commands work together:

- **`/verifyextract`** - Validates Phase 1 → Phase 2 (extraction accuracy)
- **`/verifyreport`** - Validates Phase 2/3/4 → Phase 5 (template accuracy)

**Quality Assurance Workflow:**
1. Generate report with `/analyzeREissuer`
2. Run `/verifyextract` to validate extraction quality
3. Run `/verifyreport` to validate final report accuracy
4. If both pass → Report ready for delivery
5. If either fails → Address errors and regenerate

---

**Note:** This validation ensures Phase 2 extraction accuracy and is essential for data quality assurance before proceeding to Phase 3 calculations.
