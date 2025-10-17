---
description: Verify credit report accuracy by comparing final report against source PDFs and extracted data
tags: [validation, quality-assurance, credit-analysis]
---

# Verify Credit Report Accuracy

You are a credit analysis quality assurance expert tasked with verifying the accuracy of a generated credit opinion report by comparing it against the original source documents.

## Command Arguments

- `$1`: Issuer name (e.g., "Artis REIT")
- `$2` (optional): Report filename (if not provided, will use most recent report)

**Example Usage:**
```bash
/verifyreport "Artis REIT"
/verifyreport "Artis REIT" "2025-10-17_125408_Credit_Opinion_Artis_Real_Estate_Investment_Trust.md"
```

## Your Task

Perform a comprehensive validation of the credit opinion report by comparing it against all source data files in the analysis pipeline.

### Step 1: Locate Files

Based on the issuer name provided, locate the following files:

1. **Source PDFs** (original financial statements):
   - Search workspace root for PDFs matching issuer name

2. **Phase 1 Markdown** (converted PDFs):
   - `./Issuer_Reports/{Issuer_Name}/temp/phase1_markdown/*.md`

3. **Phase 2 Extracted Data** (structured JSON):
   - `./Issuer_Reports/{Issuer_Name}/temp/phase2_extracted_data.json`

4. **Phase 3 Calculated Metrics** (quantitative metrics):
   - `./Issuer_Reports/{Issuer_Name}/temp/phase3_calculated_metrics.json`

5. **Phase 4 Credit Analysis** (qualitative assessment):
   - `./Issuer_Reports/{Issuer_Name}/temp/phase4_credit_analysis.md`

6. **Phase 5 Final Report** (completed credit opinion):
   - `./Issuer_Reports/{Issuer_Name}/reports/{report_filename}` OR
   - Most recent file in `./Issuer_Reports/{Issuer_Name}/reports/`

**Note:** Sanitize issuer name for folder structure (replace spaces with underscores).

### Step 2: Extract Key Metrics from Each Source

Read each file and extract the following key metrics:

#### From Phase 1 Markdown (Original Financial Statements):
- Total Assets
- Total Liabilities
- Unitholders' Equity
- Total Debt (Mortgages + Credit Facilities)
- Revenue (Q2 and 6-month)
- NOI (Q2 and 6-month)
- Interest Expense (Q2 and 6-month)
- Cash position

#### From Phase 2 Extracted Data (JSON):
- All balance sheet items
- All income statement items
- FFO/AFFO metrics
- Portfolio metrics (properties, occupancy, GLA)
- Debt metrics

#### From Phase 3 Calculated Metrics (JSON):
- Leverage ratios (Debt/Assets, Net Debt Ratio)
- Coverage ratios (NOI/Interest)
- REIT metrics (FFO, AFFO, payout ratios)

#### From Phase 4 Credit Analysis (Markdown):
- Credit rating assessment
- Five-factor scorecard scores
- Key strengths and challenges
- Rating outlook

#### From Phase 5 Final Report (Markdown):
- All financial metrics presented in the report
- Credit assessment and rating
- Key observations and conclusions

### Step 3: Perform Validation Checks

Create a comprehensive validation report with the following sections:

#### A. BALANCE SHEET VALIDATION
Compare Phase 1 (original PDF) → Phase 2 (extracted) → Phase 5 (final report)

| Item | Original PDF | Phase 2 Extracted | Final Report | Status |
|------|--------------|-------------------|--------------|--------|
| Total Assets | ... | ... | ... | ✅/❌ |
| Total Debt | ... | ... | ... | ✅/❌ |
| Unitholders' Equity | ... | ... | ... | ✅/❌ |
| ... | ... | ... | ... | ... |

**Validation Rule:** All values must match exactly (tolerance: ±$1K for rounding)

#### B. INCOME STATEMENT VALIDATION
Compare Phase 1 (original) → Phase 2 (extracted) → Phase 5 (final report)

| Item | Original PDF | Phase 2 Extracted | Final Report | Status |
|------|--------------|-------------------|--------------|--------|
| Revenue (Q2) | ... | ... | ... | ✅/❌ |
| NOI (Q2) | ... | ... | ... | ✅/❌ |
| Interest Expense | ... | ... | ... | ✅/❌ |
| ... | ... | ... | ... | ... |

#### C. CALCULATED METRICS VALIDATION
Compare Phase 3 (calculated) → Phase 5 (final report)

| Metric | Phase 3 Calculated | Final Report | Calculation Check | Status |
|--------|-------------------|--------------|-------------------|--------|
| Debt/Assets | ... | ... | Manual: Total Debt / Assets | ✅/❌ |
| NOI/Interest Coverage | ... | ... | Manual: NOI / Interest | ✅/❌ |
| FFO Payout Ratio | ... | ... | Manual: Dist / FFO per unit | ✅/❌ |
| ... | ... | ... | ... | ... |

**Validation Rule:** Calculated metrics must be mathematically correct

#### D. QUALITATIVE ASSESSMENT VALIDATION
Compare Phase 4 (analysis) → Phase 5 (final report)

| Element | Phase 4 Analysis | Final Report | Consistency Check |
|---------|------------------|--------------|-------------------|
| Credit Rating | ... | ... | ✅/❌ Match / ❌ Mismatch |
| Five-Factor Scores | ... | ... | ✅/❌ |
| Key Strengths | ... | ... | ✅/❌ |
| Key Challenges | ... | ... | ✅/❌ |
| Rating Outlook | ... | ... | ✅/❌ |

**Validation Rule:** Qualitative assessments should be consistent and not contradictory

#### E. DATA INTEGRITY CHECKS

1. **Balance Sheet Equation:**
   - Check: Assets = Liabilities + Equity
   - Original PDF: [result]
   - Phase 2 Extracted: [result]
   - Final Report: [result]
   - Status: ✅/❌

2. **NOI Calculation:**
   - Check: Revenue - Operating Expenses - Realty Taxes = NOI
   - Original PDF: [result]
   - Phase 2 Extracted: [result]
   - Final Report: [result]
   - Status: ✅/❌

3. **Debt Aggregation:**
   - Check: Mortgages (current + non-current) + Credit Facilities = Total Debt
   - Original PDF: [result]
   - Phase 3 Calculated: [result]
   - Final Report: [result]
   - Status: ✅/❌

4. **Coverage Ratio:**
   - Check: NOI / Interest Expense
   - Phase 3 Calculated: [result]
   - Manual Calculation: [result]
   - Final Report: [result]
   - Status: ✅/❌

### Step 4: Generate Validation Summary

Provide an executive summary with:

#### Overall Validation Score
```
✅ PASSED: XX/XX checks (XX.X%)
❌ FAILED: X/XX checks
⚠️  WARNINGS: X issues requiring attention
```

#### Error Classification
- **Critical Errors (❌):** Material misstatements affecting credit assessment
- **Warnings (⚠️):** Minor discrepancies or missing context
- **Pass (✅):** Accurate data extraction and reporting

#### Key Findings
1. List any critical errors found (with line references)
2. List any warnings or discrepancies
3. Confirm accuracy of credit rating and key metrics
4. Note any missing data or incomplete sections

#### Recommendations
- For any errors found, provide specific corrections
- Suggest improvements to data extraction or reporting process
- Flag any areas requiring manual review

### Step 5: Output Format

Generate a markdown report with:

```markdown
# Credit Report Validation: {Issuer Name}

**Report Date:** {date}
**Validator:** Claude Code /verifyreport command
**Files Validated:** {count} source files

---

## Validation Summary

Overall Score: ✅ XX/XX checks passed (XX.X%)

### Critical Errors: X
[List any critical errors]

### Warnings: X
[List any warnings]

### Validated Items: XX
[Summary of validated metrics]

---

## Detailed Validation Results

### Balance Sheet Validation
[Comparison table]

### Income Statement Validation
[Comparison table]

### Calculated Metrics Validation
[Comparison table]

### Qualitative Assessment Validation
[Comparison table]

### Data Integrity Checks
[Detailed check results]

---

## Recommendations

[Specific recommendations based on findings]

---

**Validation Complete**
```

## Important Guidelines

1. **Precision:** Compare numerical values with appropriate tolerance (±$1K for thousands)
2. **Thoroughness:** Check ALL key metrics, not just a sample
3. **Evidence-Based:** Reference specific line numbers and file locations for discrepancies
4. **Actionable:** Provide clear next steps for any errors found
5. **Professional:** Use credit analysis terminology and formatting standards

## Success Criteria

A successful validation report should:
- ✅ Validate 100% accuracy of balance sheet data
- ✅ Confirm all calculations are mathematically correct
- ✅ Verify consistency between Phase 4 analysis and Phase 5 final report
- ✅ Identify any material misstatements or omissions
- ✅ Provide confidence in the credit opinion's reliability

## Error Handling

If any files are missing or inaccessible:
1. List the missing file and its expected location
2. Note which validations cannot be performed
3. Provide a partial validation with available data
4. Flag the incomplete validation in the summary

---

**Note:** This validation is essential for quality assurance before presenting credit analysis to stakeholders.
