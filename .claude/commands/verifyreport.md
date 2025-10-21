---
description: Verify Phase 5 report accuracy by comparing against extracted data (Phase 2), calculated metrics (Phase 3), and credit analysis (Phase 4)
tags: [validation, quality-assurance, phase-5, template-verification]
---

# Verify Credit Report Accuracy

You are a credit analysis quality assurance expert tasked with verifying that the **Phase 5 final credit opinion report** correctly displays all data from the extraction, calculation, and analysis phases.

## Command Arguments

- `$1`: Issuer name (e.g., "Artis REIT")
- `$2` (optional): Report filename (if not provided, will use most recent report)

**Example Usage:**
```bash
/verifyreport "Artis REIT"
/verifyreport "Artis REIT" "2025-10-20_213350_Credit_Opinion_Artis_Real_Estate_Investment_Trust.md"
```

## Validation Scope

**Purpose:** Ensure Phase 5 report accurately reflects:
1. ✅ **Phase 2 extracted data** - Issuer-reported metrics correctly displayed
2. ✅ **Phase 3 calculated metrics** - Calculations correctly displayed
3. ✅ **Phase 4 credit analysis** - Narrative correctly incorporated
4. ✅ **Template substitution** - No unreplaced placeholders

**NOT validating:** PDF extraction accuracy (that's Phase 1/2 validation, separate concern)

---

## Step 1: Locate Files

Based on the issuer name provided, locate the following files:

**Note:** Sanitize issuer name for folder structure (replace spaces with underscores).

### Required Files

1. **Phase 2 Extracted Data** (structured JSON):
   - `./Issuer_Reports/{Issuer_Name}/temp/phase2_extracted_data.json`

2. **Phase 3 Calculated Metrics** (quantitative metrics):
   - `./Issuer_Reports/{Issuer_Name}/temp/phase3_calculated_metrics.json`

3. **Phase 4 Credit Analysis** (qualitative assessment):
   - `./Issuer_Reports/{Issuer_Name}/temp/phase4_credit_analysis.md`

4. **Phase 5 Final Report** (completed credit opinion):
   - `./Issuer_Reports/{Issuer_Name}/reports/{report_filename}` OR
   - Most recent file in `./Issuer_Reports/{Issuer_Name}/reports/`

**Token Budget:** Reading these 4 files uses ~38K tokens (well within limits)

---

## Step 2: Extract Key Metrics from Each Phase

### From Phase 2 Extracted Data (JSON)

**Balance Sheet:**
- Total Assets
- Total Liabilities
- Unitholders' Equity
- Total Debt
- Cash and Equivalents
- Common Units Outstanding
- Diluted Units Outstanding

**Income Statement:**
- Revenue (reporting period)
- NOI (reporting period)
- Interest Expense (reporting period)
- Net Income
- Cash Flow from Operations

**FFO/AFFO (Issuer-Reported):**
- FFO total and per-unit
- AFFO total and per-unit
- ACFO total and per-unit (if reported)
- Distributions per unit
- FFO payout ratio (reported)
- AFFO payout ratio (reported)

**Portfolio Metrics:**
- Total properties
- Total GLA (square feet)
- Occupancy rate
- Occupancy including commitments

### From Phase 3 Calculated Metrics (JSON)

**Leverage Ratios:**
- Debt/Assets ratio (%)
- Net Debt ratio (%)
- Gross Assets

**Coverage Ratios:**
- NOI/Interest coverage
- FFO coverage (reported per-unit)
- AFFO coverage (reported per-unit)
- ACFO coverage (calculated per-unit)
- AFCF coverage (calculated per-unit)

**REIT Metrics (Calculated):**
- FFO calculated total and per-unit
- AFFO calculated total and per-unit
- ACFO total and per-unit
- AFCF total and per-unit
- All payout ratios (calculated)

**Per-Unit Values (Both Basic & Diluted):**
- FFO per unit (basic and diluted)
- AFFO per unit (basic and diluted)
- ACFO per unit (basic and diluted)
- AFCF per unit (basic and diluted)

### From Phase 4 Credit Analysis (Markdown)

**Credit Assessment:**
- Credit rating (e.g., Baa2/BBB)
- Five-factor scorecard scores (F1-F5)
- Overall scorecard rating
- Key credit drivers (3-5 bullets)
- Credit strengths (3-5 bullets)
- Credit challenges (3-5 bullets)
- Rating outlook (Positive/Stable/Negative)
- Upgrade factors
- Downgrade factors

### From Phase 5 Final Report (Markdown)

**All metrics displayed in:**
- Section 2.2 FFO/AFFO/ACFO/AFCF Summary
- Section 2.5 Coverage Analysis
- Section 3.1 Balance Sheet
- Section 3.2 Income Statement
- Section 3.3 Portfolio Metrics
- Executive Summary
- Credit Scorecard

---

## Step 3: Perform Validation Checks

### A. PHASE 2 → PHASE 5: EXTRACTED DATA VALIDATION

**Purpose:** Verify issuer-reported metrics are correctly displayed in final report.

| Metric | Phase 2 Extracted | Phase 5 Report | Tolerance | Status |
|--------|-------------------|----------------|-----------|--------|
| **Balance Sheet** |
| Total Assets | ... | ... | ±$1K | ✅/❌ |
| Total Liabilities | ... | ... | ±$1K | ✅/❌ |
| Unitholders' Equity | ... | ... | ±$1K | ✅/❌ |
| Total Debt | ... | ... | ±$1K | ✅/❌ |
| Cash & Equivalents | ... | ... | ±$1K | ✅/❌ |
| Common Units Outstanding | ... | ... | Exact | ✅/❌ |
| **Income Statement** |
| Revenue | ... | ... | ±$1K | ✅/❌ |
| NOI | ... | ... | ±$1K | ✅/❌ |
| Interest Expense | ... | ... | ±$1K | ✅/❌ |
| Net Income | ... | ... | ±$1K | ✅/❌ |
| **FFO/AFFO (Reported)** |
| FFO total | ... | ... | ±$1K | ✅/❌ |
| FFO per unit | ... | ... | ±$0.0001 | ✅/❌ |
| AFFO total | ... | ... | ±$1K | ✅/❌ |
| AFFO per unit | ... | ... | ±$0.0001 | ✅/❌ |
| Distributions per unit | ... | ... | ±$0.0001 | ✅/❌ |
| FFO payout ratio | ... | ... | ±0.1% | ✅/❌ |
| AFFO payout ratio | ... | ... | ±0.1% | ✅/❌ |
| **Portfolio** |
| Total properties | ... | ... | Exact | ✅/❌ |
| Total GLA (sq ft) | ... | ... | ±1,000 | ✅/❌ |
| Occupancy rate | ... | ... | ±0.1% | ✅/❌ |

**Validation Rule:** All Phase 2 values must appear correctly in Phase 5 (within tolerance)

### B. PHASE 3 → PHASE 5: CALCULATED METRICS VALIDATION

**Purpose:** Verify calculated metrics are correctly displayed in final report.

| Metric | Phase 3 Calculated | Phase 5 Report | Manual Verification | Status |
|--------|-------------------|----------------|---------------------|--------|
| **Leverage Ratios** |
| Debt/Assets | ... | ... | Total Debt / Total Assets | ✅/❌ |
| Net Debt Ratio | ... | ... | (Debt - Cash) / Assets | ✅/❌ |
| **Coverage Ratios** |
| NOI/Interest | ... | ... | NOI / Interest Expense | ✅/❌ |
| FFO Coverage (reported) | ... | ... | FFO per unit / Dist per unit | ✅/❌ |
| AFFO Coverage (reported) | ... | ... | AFFO per unit / Dist per unit | ✅/❌ |
| ACFO Coverage (calculated) | ... | ... | ACFO per unit / Dist per unit | ✅/❌ |
| AFCF Coverage (calculated) | ... | ... | AFCF per unit / Dist per unit | ✅/❌ |
| **REIT Metrics (Calculated)** |
| FFO calculated total | ... | ... | Check Phase 3 reconciliation | ✅/❌ |
| FFO calculated per-unit | ... | ... | FFO / Common Units | ✅/❌ |
| AFFO calculated total | ... | ... | Check Phase 3 reconciliation | ✅/❌ |
| AFFO calculated per-unit | ... | ... | AFFO / Common Units | ✅/❌ |
| ACFO total | ... | ... | Check Phase 3 calculation | ✅/❌ |
| ACFO per-unit | ... | ... | ACFO / Common Units | ✅/❌ |
| AFCF total | ... | ... | ACFO + Net CFI | ✅/❌ |
| AFCF per-unit | ... | ... | AFCF / Common Units | ✅/❌ |
| **Payout Ratios (Calculated)** |
| FFO payout (calculated) | ... | ... | (Dist / FFO per unit) × 100 | ✅/❌ |
| AFFO payout (calculated) | ... | ... | (Dist / AFFO per unit) × 100 | ✅/❌ |
| ACFO payout (calculated) | ... | ... | (Dist / ACFO per unit) × 100 | ✅/❌ |
| AFCF payout (calculated) | ... | ... | (Dist / AFCF per unit) × 100 | ✅/❌ |

**Validation Rules:**
1. All Phase 3 calculations must appear correctly in Phase 5
2. Coverage ratios must use **per-unit basis** (metric per unit / distributions per unit)
3. Payout ratios must use **per-unit basis** ((distributions per unit / metric per unit) × 100)
4. Tolerance: ±0.01 for ratios, ±0.1% for percentages, ±$1K for totals

### C. PHASE 4 → PHASE 5: NARRATIVE CONSISTENCY VALIDATION

**Purpose:** Verify Phase 4 credit analysis is correctly incorporated into Phase 5.

| Element | Phase 4 Analysis | Phase 5 Report | Consistency Check |
|---------|------------------|----------------|-------------------|
| **Credit Assessment** |
| Credit Rating | ... | ... | ✅ Match / ❌ Mismatch |
| Five-Factor Scores | F1: ..., F2: ..., F3: ..., F4: ..., F5: ... | ... | ✅/❌ All scores match |
| Overall Scorecard Rating | ... | ... | ✅/❌ |
| **Key Drivers & Assessment** |
| Key Credit Drivers | [list from Phase 4] | [list from Phase 5] | ✅/❌ Consistent |
| Credit Strengths | [list from Phase 4] | [list from Phase 5] | ✅/❌ Consistent |
| Credit Challenges | [list from Phase 4] | [list from Phase 5] | ✅/❌ Consistent |
| Rating Outlook | Positive/Stable/Negative | ... | ✅/❌ |
| Upgrade Factors | [list from Phase 4] | [list from Phase 5] | ✅/❌ |
| Downgrade Factors | [list from Phase 4] | [list from Phase 5] | ✅/❌ |

**Validation Rules:**
1. Phase 4 narrative must be correctly incorporated (not contradictory)
2. Credit rating and scores must match exactly
3. Key drivers/strengths/challenges should be substantively similar (allow for formatting)
4. Outlook must match

### D. TEMPLATE PLACEHOLDER VALIDATION

**Purpose:** Detect any unreplaced placeholders or template errors.

**Search Phase 5 report for:**

1. **Unreplaced Placeholders:**
   - Pattern: `{{.*}}` (any text between double braces)
   - Example errors: `{{FFO_CUSHION}}`, `{{PLACEHOLDER}}`, `{{TEST}}`

2. **Data Availability Issues:**
   - "Not available" where Phase 2/3 data exists
   - Empty table cells where values should be present
   - "N/A" used incorrectly

3. **Formatting Errors:**
   - "0.0%" instead of proper percentage
   - "None" or "null" displayed literally
   - Incorrect number formatting (e.g., "1234567" instead of "1,234,567")

**Expected Result:** Zero unreplaced placeholders, all data properly displayed

---

## Step 4: Generate Validation Report

Provide a comprehensive validation report with:

### Validation Summary

```markdown
## Validation Summary

✅ **PASSED:** XX/XX checks (XX.X%)
❌ **FAILED:** X/XX checks
⚠️  **WARNINGS:** X issues requiring attention

**Overall Status:** PASS / FAIL / PASS WITH WARNINGS
```

### Critical Errors (if any)

List any errors that materially affect the credit opinion:

```markdown
## Critical Errors: X

1. ❌ **[Error Type]:** [Description]
   - **Phase 3:** [Value]
   - **Phase 5:** [Value]
   - **Location:** Section X.X, line XXX
   - **Impact:** Material misstatement affecting [credit assessment/calculations]

2. ❌ **Unreplaced Placeholder:** {{PLACEHOLDER_NAME}}
   - **Location:** Section X.X, line XXX
   - **Impact:** Template substitution failure
```

### Warnings (if any)

List minor discrepancies or areas requiring review:

```markdown
## Warnings: X

1. ⚠️  **[Warning Type]:** [Description]
   - **Phase 3:** [Value]
   - **Phase 5:** [Value]
   - **Location:** Section X.X, line XXX
   - **Impact:** Minor rounding difference / Display formatting issue

2. ⚠️  **Missing Data:** [Field] shows "Not available" but Phase 3 has value
   - **Phase 3:** [Value]
   - **Phase 5:** "Not available"
   - **Location:** Section X.X
```

### Validated Items

```markdown
## Validated Items: XX

### Phase 2 → Phase 5 Validation
✅ Balance Sheet: X/X items correct
✅ Income Statement: X/X items correct
✅ FFO/AFFO (Reported): X/X items correct
✅ Portfolio Metrics: X/X items correct

### Phase 3 → Phase 5 Validation
✅ Leverage Ratios: X/X items correct
✅ Coverage Ratios: X/X items correct
✅ REIT Metrics (Calculated): X/X items correct
✅ Payout Ratios: X/X items correct

### Phase 4 → Phase 5 Validation
✅ Credit Rating: Matches
✅ Five-Factor Scores: All match
✅ Narrative Consistency: Consistent
✅ Outlook: Matches

### Template Validation
✅ Placeholders: All replaced correctly
✅ Data Availability: All populated
✅ Formatting: Correct
```

---

## Step 5: Detailed Validation Tables

Include the complete comparison tables from Step 3 (A, B, C, D) with all values filled in.

---

## Step 6: Recommendations

Based on validation results, provide specific recommendations:

### If Errors Found:

```markdown
## Recommendations

### Critical Errors - Immediate Action Required

1. **Fix [Error Type]:**
   - File: `scripts/generate_final_report.py`
   - Line: [approximate location]
   - Change: [specific fix]
   - Reason: [explanation]

2. **Remove Orphaned Placeholder:**
   - File: `templates/credit_opinion_template.md`
   - Line: [approximate location]
   - Action: Remove `{{PLACEHOLDER_NAME}}`

### Warnings - Review Recommended

1. **Review Rounding Logic:**
   - Minor rounding discrepancy in [metric]
   - Consider adjusting precision in calculation

2. **Populate Missing Field:**
   - [Field] shows "Not available" but data exists in Phase 3
   - Update placeholder population logic
```

### If All Passed:

```markdown
## Recommendations

✅ **All validations passed** - Report is ready for delivery

**Quality Checks Completed:**
- [X] All Phase 2 extracted data correctly displayed
- [X] All Phase 3 calculated metrics accurate
- [X] Phase 4 narrative properly incorporated
- [X] No template substitution errors

**Next Steps:**
- Report can be delivered to stakeholders
- Consider archiving validation results with report
```

---

## Output Format Template

```markdown
# Credit Report Validation: {Issuer Name}

**Report Validated:** {Phase 5 report filename}
**Validation Date:** {current date}
**Validator:** Claude Code /verifyreport command
**Files Analyzed:** 4 (Phase 2, 3, 4, 5)

---

## Validation Summary

✅ **PASSED:** XX/XX checks (XX.X%)
❌ **FAILED:** X/XX checks
⚠️  **WARNINGS:** X issues

**Overall Status:** [PASS / FAIL / PASS WITH WARNINGS]

---

## Critical Errors: X

[List errors with details and locations]

---

## Warnings: X

[List warnings with details]

---

## Validated Items: XX

[Summary of all validated metrics]

---

## Detailed Validation Results

### A. Phase 2 → Phase 5: Extracted Data Validation

[Complete comparison table]

### B. Phase 3 → Phase 5: Calculated Metrics Validation

[Complete comparison table]

### C. Phase 4 → Phase 5: Narrative Consistency Validation

[Complete comparison table]

### D. Template Placeholder Validation

[List of checks performed]

---

## Recommendations

[Specific recommendations based on findings]

---

**Validation Complete** ✓
```

---

## Important Guidelines

1. **Precision:**
   - Thousands (000s): ±$1K tolerance
   - Per-unit values: ±$0.0001 tolerance
   - Percentages: ±0.1% tolerance
   - Ratios: ±0.01 tolerance
   - Counts (properties, units): Exact match required

2. **Thoroughness:**
   - Check ALL metrics in sections 2.2, 2.5, 3.1, 3.2, 3.3
   - Don't skip any Phase 3 calculated values
   - Verify both reported AND calculated metrics

3. **Evidence-Based:**
   - Cite specific section and line numbers for errors
   - Show both Phase 3 and Phase 5 values
   - Calculate manual verification for ratios

4. **Actionable:**
   - Provide file names and approximate line numbers for fixes
   - Suggest specific code changes if errors found
   - Prioritize critical errors vs. warnings

5. **Professional:**
   - Use credit analysis terminology
   - Format numbers consistently (thousands separator, decimals)
   - Clear pass/fail status for each check

---

## Success Criteria

A successful validation should:

- ✅ Validate 100% of Phase 2 extracted data matches Phase 5 display
- ✅ Confirm all Phase 3 calculations are correctly displayed
- ✅ Verify Phase 4 narrative consistency with Phase 5 report
- ✅ Detect any unreplaced placeholders or template errors
- ✅ Identify any material misstatements
- ✅ Provide actionable recommendations for any issues found
- ✅ Give confidence that the report is ready for stakeholder delivery

---

## Error Handling

**If files are missing:**
1. Report which file is missing and expected location
2. Note which validations cannot be performed
3. Provide partial validation with available files
4. Mark validation as **INCOMPLETE** in summary

**If Phase 3/4 data is incomplete:**
1. Note which metrics are missing in source data
2. Mark those checks as **SKIPPED** (not FAILED)
3. Validate what data is available
4. Flag incomplete analysis in summary

**If Phase 5 report has obvious errors:**
1. Stop after finding 10+ critical errors (likely systemic issue)
2. Report pattern of errors found
3. Recommend regenerating report before full validation

---

**Note:** This validation ensures Phase 5 template substitution accuracy and is essential for quality assurance before delivering credit reports to stakeholders.
