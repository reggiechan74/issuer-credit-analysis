---
description: Verify Phase 1 markdown conversion quality by validating table structure, data integrity, and completeness
tags: [validation, quality-assurance, phase-1, pdf-conversion]
---

# Verify PDF-to-Markdown Conversion Quality

You are a document conversion quality assurance expert tasked with verifying that the **Phase 1 markdown files** (converted from source PDFs using PyMuPDF4LLM + Camelot) contain accurate, well-structured financial data suitable for Phase 2 extraction.

## Command Arguments

- `$1`: Issuer name (e.g., "Artis REIT")

**Example Usage:**
```bash
/verifyconversion "Artis REIT"
```

## Validation Scope

**Purpose:** Ensure Phase 1 markdown files have:
1. ✅ **Complete financial statements** - All required tables present
2. ✅ **Table structure integrity** - Proper markdown table formatting
3. ✅ **Data consistency** - Balance sheet equation holds, totals match
4. ✅ **Number formatting** - Currency values properly formatted
5. ✅ **No conversion errors** - No garbled text, missing columns, or malformed tables

**NOT performing:** Direct PDF comparison (PDFs are binary, difficult to validate programmatically)

**Approach:** Validate markdown quality and internal consistency as a proxy for conversion accuracy

---

## Step 1: Locate Phase 1 Markdown Files

Based on the issuer name provided, locate:

**Location:** `./Issuer_Reports/{Issuer_Name}/temp/phase1_markdown/*.md`

**Note:** Sanitize issuer name for folder structure (replace spaces with underscores).

**Expected Files:**
- MD&A (Management Discussion & Analysis)
- Financial Statements (Consolidated Balance Sheet, Income Statement, Cash Flow)
- Notes to Financial Statements (if extracted)

**Token Budget Consideration:**
- Phase 1 markdown can be 100-140K tokens total
- Focus validation on critical sections:
  - Balance Sheet
  - Income Statement
  - FFO/AFFO reconciliation (if in MD&A)
  - Key notes (debt, units outstanding)
- Skip long narrative sections for validation efficiency

---

## Step 2: Identify Critical Sections

For each markdown file, identify these critical sections:

### Financial Statements File

**Required Sections:**
- [ ] Consolidated Balance Sheet (or Statement of Financial Position)
- [ ] Consolidated Statement of Income (or Comprehensive Income)
- [ ] Consolidated Statement of Cash Flows
- [ ] Statement of Changes in Equity

**Key Indicators of Quality Conversion:**
- Section headers properly identified with `#` markdown
- Tables use proper markdown format: `| Column | Column |`
- Table alignment correct (numbers right-aligned)
- Thousands/millions noted in headers

### MD&A File

**Required Sections:**
- [ ] FFO/AFFO Reconciliation (if issuer reports)
- [ ] Portfolio Summary
- [ ] Debt Summary
- [ ] Key Performance Indicators

**Key Indicators of Quality Conversion:**
- Headings hierarchically structured (`##`, `###`)
- Tables properly formatted
- Bullet lists properly formatted (`-` or `*`)

---

## Step 3: Table Structure Validation

For each critical table, validate structure:

### A. BALANCE SHEET TABLE VALIDATION

**Check for:**

1. **Column Headers Present:**
   ```markdown
   | Item | As at [Date] | As at [Prior Date] |
   ```

2. **Row Structure:**
   - Assets section (Current Assets, Non-Current Assets, Total Assets)
   - Liabilities section (Current Liabilities, Non-Current Liabilities, Total Liabilities)
   - Equity section (Unitholders' Equity, Total Equity)

3. **Totals and Subtotals:**
   - "Total current assets"
   - "Total assets"
   - "Total current liabilities"
   - "Total liabilities"
   - "Total equity"

4. **Number Formatting:**
   - Consistent use of commas: `1,234,567`
   - Parentheses for negatives: `(123)`
   - Proper decimal alignment

**Validation Checks:**

| Check | Expected | Status |
|-------|----------|--------|
| Table uses markdown format | ` | Header | Header | ` | ✅/❌ |
| All column headers present | Date columns identified | ✅/❌ |
| Assets section complete | Current + Non-Current + Total | ✅/❌ |
| Liabilities section complete | Current + Non-Current + Total | ✅/❌ |
| Equity section present | Unitholders' Equity | ✅/❌ |
| Numbers properly formatted | Commas, no text corruption | ✅/❌ |
| No missing cells | All table cells have values or `-` | ✅/❌ |

### B. INCOME STATEMENT TABLE VALIDATION

**Check for:**

1. **Column Headers Present:**
   ```markdown
   | Item | 3 months ended [Q2 Date] | 3 months ended [Q2 Prior] | 6 months ended [Date] | 6 months ended [Prior] |
   ```

2. **Row Structure:**
   - Revenue section
   - Expenses section
   - Net income (loss)

3. **Key Line Items:**
   - "Revenue from property operations" or "Rental revenue"
   - "Property operating expenses"
   - "Realty taxes"
   - "Interest expense" or "Finance costs"
   - "Net income (loss)"

**Validation Checks:**

| Check | Expected | Status |
|-------|----------|--------|
| Table uses markdown format | ` | Header | Header | ` | ✅/❌ |
| Revenue line present | First line item | ✅/❌ |
| Operating expenses present | Multiple expense lines | ✅/❌ |
| Interest expense present | Finance costs line | ✅/❌ |
| Net income present | Last line (may be negative) | ✅/❌ |
| Q2 and 6-month columns | 4 columns (current + prior) | ✅/❌ |
| Numbers properly formatted | Commas, negatives in ( ) | ✅/❌ |

### C. FFO/AFFO RECONCILIATION TABLE VALIDATION (if present)

**Check for:**

1. **Table Structure:**
   ```markdown
   | Reconciliation Item | Amount (000s) | Per Unit |
   ```

2. **Key Components:**
   - "Net income" as starting point
   - Add-backs (depreciation, FV adjustments, etc.)
   - "FFO" subtotal
   - AFFO adjustments (capex, TI, leasing costs)
   - "AFFO" total

**Validation Checks:**

| Check | Expected | Status |
|-------|----------|--------|
| Table uses markdown format | ` | Header | Header | ` | ✅/❌ |
| Starts with Net Income | First reconciliation item | ✅/❌ |
| FFO clearly labeled | FFO subtotal row | ✅/❌ |
| AFFO clearly labeled | AFFO total row | ✅/❌ |
| Per unit column present | Shows per-unit calculations | ✅/❌ |
| Adjustment labels clear | Each adjustment described | ✅/❌ |

### D. CASH FLOW STATEMENT TABLE VALIDATION

**Check for:**

1. **Three Sections:**
   - Operating activities
   - Investing activities
   - Financing activities

2. **Key Totals:**
   - "Cash flows from operating activities"
   - "Cash flows from investing activities"
   - "Cash flows from financing activities"
   - "Increase (decrease) in cash"

**Validation Checks:**

| Check | Expected | Status |
|-------|----------|--------|
| Table uses markdown format | ` | Header | Header | ` | ✅/❌ |
| Three sections present | Operating, Investing, Financing | ✅/❌ |
| Section totals present | Each section has subtotal | ✅/❌ |
| Net change in cash | Final line | ✅/❌ |
| Sign consistency | Negatives in ( ) | ✅/❌ |

---

## Step 4: Data Integrity Checks

Validate internal consistency of extracted data:

### A. BALANCE SHEET EQUATION

**Formula:** Assets = Liabilities + Equity

**Extract from markdown:**
- Total Assets (from balance sheet table)
- Total Liabilities (from balance sheet table)
- Total Equity (from balance sheet table)

**Calculate:**
```
Check: Total Liabilities + Total Equity = Total Assets
Tolerance: ±$5K (rounding across multiple line items)
```

**Result:**
- ✅ **PASS** if equation balances within tolerance
- ❌ **FAIL** if equation doesn't balance → indicates table parsing error

### B. BALANCE SHEET SUBTOTALS

**Validate asset aggregation:**
```
Total Assets = Current Assets + Non-Current Assets
Tolerance: ±$2K
```

**Validate liability aggregation:**
```
Total Liabilities = Current Liabilities + Non-Current Liabilities
Tolerance: ±$2K
```

**Result:**
- ✅ **PASS** if subtotals aggregate correctly
- ❌ **FAIL** if mismatch → indicates missing rows or incorrect parsing

### C. DEBT AGGREGATION (from notes)

**If debt note is present:**
```
Total Mortgages = Current portion + Non-current portion
Crosscheck against: Balance sheet mortgages line items
Tolerance: ±$1K
```

### D. NOI CALCULATION (if components present)

**If income statement has breakdown:**
```
NOI = Revenue - Property Operating Expenses - Realty Taxes
Tolerance: ±$2K
```

**Result:**
- ✅ **PASS** if calculation matches
- ⚠️  **WARNING** if small discrepancy (may be rounding)
- ❌ **FAIL** if large discrepancy → check for missing expense lines

### E. FFO/AFFO RECONCILIATION MATH (if present)

**Validate reconciliation adds up:**
```
FFO = Net Income + Adjustments (sum)
AFFO = FFO - Adjustments (sum)
Tolerance: ±$500 (tighter for reconciliation)
```

**Result:**
- ✅ **PASS** if reconciliation math correct
- ❌ **FAIL** if doesn't add up → table parsing captured wrong values

---

## Step 5: Conversion Error Detection

Search for common PDF-to-markdown conversion errors:

### A. GARBLED TEXT DETECTION

**Search for patterns indicating corruption:**
- Random special characters: `���`, `####`, `***`
- Overlapping text: Numbers merged with labels
- Encoding errors: `Ã©` instead of `é`
- OCR artifacts: `O` instead of `0`, `I` instead of `1`

**Example Error:**
```markdown
| Total Assets | 2,O47,I49 |  ← OCR error: "O" and "I" instead of "0" and "1"
```

**Result:**
- ✅ **PASS** if no garbled text found
- ⚠️  **WARNING** if isolated issues (can be manually corrected)
- ❌ **FAIL** if widespread corruption → reconvert PDF

### B. MISSING COLUMNS DETECTION

**Check if tables have expected column count:**

**Balance Sheet:** Should have 2-3 columns (Item, Current Period, Prior Period)
**Income Statement:** Should have 4-5 columns (Item, Q2, Q2 Prior, 6M, 6M Prior)

**Search for:**
- Tables with only 1 column (conversion failure)
- Missing headers
- Column content merged into single cell

**Result:**
- ✅ **PASS** if all tables have correct column structure
- ❌ **FAIL** if columns missing → reconvert with different settings

### C. SPLIT TABLE DETECTION

**Check if tables broken across pages:**

**Indicators:**
- Two tables with same headers
- "Continued" or "(cont'd)" notation
- Table ends mid-section then restarts

**Result:**
- ✅ **PASS** if tables are continuous
- ⚠️  **WARNING** if split tables detected (may need manual merging)

### D. NUMBER FORMATTING CORRUPTION

**Check for:**
- Numbers without commas: `1234567` should be `1,234,567`
- Commas in wrong places: `12,345,67`
- Decimals misplaced: `1,234.567.89`
- Currency symbols mixed in: `$1,234$`

**Search Pattern:**
Look for numbers >999 without commas in financial tables

**Result:**
- ✅ **PASS** if consistent formatting
- ⚠️  **WARNING** if isolated issues
- ❌ **FAIL** if systematic formatting problems

---

## Step 6: Completeness Check

Verify all required sections are present:

### Critical Sections Checklist

| Section | Expected Location | Status |
|---------|-------------------|--------|
| **Balance Sheet** | Financial Statements file | ✅ Present / ❌ Missing |
| **Income Statement** | Financial Statements file | ✅ Present / ❌ Missing |
| **Cash Flow Statement** | Financial Statements file | ✅ Present / ❌ Missing |
| **FFO/AFFO Reconciliation** | MD&A file | ✅ Present / ⚠️ N/A (not all issuers report) |
| **Portfolio Summary** | MD&A file | ✅ Present / ❌ Missing |
| **Debt Note** | Notes or MD&A | ✅ Present / ⚠️ Partial |
| **Units Outstanding** | Notes or Balance Sheet | ✅ Present / ❌ Missing |

**Result:**
- ✅ **PASS** if all critical sections present
- ⚠️  **WARNING** if optional sections missing (FFO/AFFO)
- ❌ **FAIL** if critical sections (Balance Sheet, Income Statement) missing

---

## Step 7: Generate Conversion Quality Report

### Conversion Quality Summary

```markdown
## Conversion Quality Summary

✅ **PASSED:** XX/XX checks (XX.X%)
❌ **FAILED:** X/XX checks
⚠️  **WARNINGS:** X issues requiring attention

**Overall Quality:** EXCELLENT / GOOD / ACCEPTABLE / POOR
```

### Critical Conversion Errors (if any)

```markdown
## Critical Errors: X

1. ❌ **Missing Section:** [Section Name]
   - **Expected:** Consolidated Balance Sheet
   - **Found:** Not present in any markdown file
   - **Impact:** Cannot perform Phase 2 extraction
   - **Recommended Fix:** Reconvert PDF with focus on page [X]

2. ❌ **Table Structure Failure:** [Table Name]
   - **Issue:** Columns missing or malformed
   - **Detected:** Income statement has only 1 column
   - **Impact:** Phase 2 extraction will fail
   - **Recommended Fix:** Try `camelot` with `flavor='stream'` mode

3. ❌ **Balance Sheet Equation Failure:**
   - **Assets:** $2,047,149K
   - **Liabilities + Equity:** $2,050,000K
   - **Difference:** $2,851K (exceeds ±$5K tolerance)
   - **Impact:** Data integrity compromised
   - **Recommended Fix:** Manually review balance sheet table for missing values
```

### Warnings (if any)

```markdown
## Warnings: X

1. ⚠️  **Number Formatting Inconsistency:**
   - **Issue:** Some numbers lack comma separators
   - **Examples:** Line 45: "1234567" should be "1,234,567"
   - **Impact:** Minor - Phase 2 extraction can handle
   - **Recommendation:** Consider post-processing to standardize

2. ⚠️  **Split Table Detected:**
   - **Section:** Debt maturity schedule
   - **Issue:** Table continues on next page
   - **Impact:** May require manual merging
   - **Recommendation:** Review note X for completeness

3. ⚠️  **Optional Section Missing:**
   - **Section:** FFO/AFFO reconciliation
   - **Impact:** Phase 2 will mark as "not reported" (acceptable)
   - **Note:** Not all issuers report FFO/AFFO in detail
```

### Quality Metrics

```markdown
## Quality Metrics

### Table Structure
✅ Balance Sheet: Well-formed
✅ Income Statement: Well-formed
✅ Cash Flow Statement: Well-formed
⚠️ FFO/AFFO Table: Minor formatting issues
✅ Debt Note: Well-formed

### Data Integrity
✅ Balance Sheet Equation: Balanced (±$2K)
✅ Asset Subtotals: Match totals
✅ Liability Subtotals: Match totals
✅ NOI Calculation: Consistent
⚠️ FFO Reconciliation: Small rounding difference

### Conversion Quality
✅ No garbled text detected
✅ All columns present
✅ Number formatting: 95% consistent
✅ All critical sections present

### Completeness
✅ Balance Sheet: 100%
✅ Income Statement: 100%
✅ Cash Flow Statement: 100%
✅ Notes: 85% (some optional notes missing)
⚠️ MD&A: 90% (portfolio detail limited)
```

---

## Step 8: Recommendations

### If Critical Errors Found (Reconversion Required):

```markdown
## Recommendations

### RECONVERSION REQUIRED

**Critical Issues:**
- Missing critical section: [Name]
- Table structure failure: [Table]
- Data integrity failure: Balance sheet doesn't balance

**Reconversion Steps:**

1. **Identify Problem PDFs:**
   - [PDF filename] - Page [X] missing conversion

2. **Try Alternative Conversion Settings:**
   - Current: `pymupdf4llm + camelot lattice mode`
   - Alternative: Try `camelot stream mode` for complex tables
   - Fallback: `pdfplumber` for nested tables (see Issue #9 research)

3. **Manual Intervention:**
   - If auto-conversion fails, extract problematic table manually
   - Update Phase 1 markdown directly
   - Document manual corrections

4. **Re-run Validation:**
   - After reconversion, run `/verifyconversion` again
   - Verify all critical errors resolved
```

### If Warnings Only (Acceptable Quality):

```markdown
## Recommendations

### ACCEPTABLE - Proceed with Caution

**Minor Issues Detected:**
- [List warnings]

**Mitigation:**
1. **Phase 2 Extraction Adjustments:**
   - Add extra validation for [problematic area]
   - Use fallback logic for missing data

2. **Manual Review Points:**
   - Double-check [specific metric] in Phase 2 JSON
   - Verify [table] extracted correctly

3. **Documentation:**
   - Note conversion limitations in analysis
   - Flag data quality concerns if material

**Proceed to Phase 2:** Yes, with noted caveats
```

### If All Passed (Excellent Quality):

```markdown
## Recommendations

✅ **EXCELLENT CONVERSION QUALITY** - Ready for Phase 2 extraction

**Quality Indicators:**
- [X] All financial statements properly converted
- [X] Table structures intact
- [X] Data integrity validated
- [X] No conversion errors detected
- [X] All critical sections present

**Next Steps:**
- Proceed to Phase 2 extraction with confidence
- No manual corrections needed
- Conversion can serve as baseline for future PDFs
```

---

## Output Format Template

```markdown
# PDF Conversion Quality Report: {Issuer Name}

**Phase 1 Markdown Files:** {List files}
**Validation Date:** {current date}
**Validator:** Claude Code /verifyconversion command

---

## Conversion Quality Summary

✅ **PASSED:** XX/XX checks (XX.X%)
❌ **FAILED:** X/XX checks
⚠️  **WARNINGS:** X issues

**Overall Quality:** [EXCELLENT / GOOD / ACCEPTABLE / POOR]

---

## Critical Errors: X

[List errors with specific file/line references]

---

## Warnings: X

[List warnings]

---

## Quality Metrics

[Detailed quality metrics]

---

## Detailed Validation Results

### A. Table Structure Validation

[Results for each critical table]

### B. Data Integrity Checks

[Results of equation checks, subtotal validations]

### C. Conversion Error Detection

[Results of garbled text, missing columns, etc.]

### D. Completeness Check

[Checklist of required sections]

---

## Recommendations

[Specific recommendations based on findings]

---

**Conversion Validation Complete** ✓
```

---

## Important Guidelines

1. **Focus on Critical Tables:**
   - Don't try to validate every table in 100+ page document
   - Prioritize: Balance Sheet, Income Statement, Cash Flow, FFO/AFFO

2. **Use Sampling:**
   - If conversion quality is good in first few tables, assume rest is good
   - If issues found, check more thoroughly

3. **Be Practical:**
   - Perfect conversion is rare
   - Accept minor formatting issues if data integrity intact
   - Distinguish critical errors from cosmetic issues

4. **Provide Context:**
   - Note which PDF and page range each markdown came from
   - Reference file names and approximate line numbers

5. **Actionable Guidance:**
   - If reconversion needed, suggest specific settings
   - If acceptable, note what to watch for in Phase 2
   - If excellent, affirm quality

---

## Success Criteria

A successful conversion validation should:

- ✅ Confirm all critical financial statements present and well-formatted
- ✅ Verify data integrity (balance sheet equation, subtotals)
- ✅ Detect any systemic conversion errors (garbled text, missing columns)
- ✅ Assess overall conversion quality (excellent/good/acceptable/poor)
- ✅ Provide clear recommendation (proceed/reconvert/manual fixes)
- ✅ Give confidence that Phase 1 markdown is suitable for Phase 2 extraction

---

## Integration with Other Validation Commands

**Three-tier validation workflow:**

1. **`/verifyconversion`** - Validates PDF → Phase 1 markdown (conversion quality)
2. **`/verifyextract`** - Validates Phase 1 markdown → Phase 2 JSON (extraction accuracy)
3. **`/verifyreport`** - Validates Phase 2/3/4 → Phase 5 report (template accuracy)

**Complete QA Process:**
```
PDF → Phase 1 Markdown → Phase 2 JSON → Phase 3 Metrics → Phase 4 Analysis → Phase 5 Report
      ↓ /verifyconversion   ↓ /verifyextract                                    ↓ /verifyreport
      Quality Check         Accuracy Check                                      Final Check
```

**Benefit:** Catch errors early in the pipeline before they propagate

---

**Note:** This validation ensures Phase 1 markdown conversion quality and identifies issues that would prevent successful Phase 2 extraction.
