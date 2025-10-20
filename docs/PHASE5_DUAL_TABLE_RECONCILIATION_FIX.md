# Phase 5 Dual-Table Reconciliation Fix - Implementation Plan

**Version:** 1.0.13-dev
**Date:** 2025-10-20
**Issue:** ACFO calculated values and per-unit metrics not populating in report sections 2.2.2 and 2.5.2
**Severity:** HIGH - Calculated values exist but not displayed
**Status:** Issues 1-3 COMPLETED ✅ | Issue 4 OPTIONAL | Issue 5 REMAINING ⚠️

---

## Executive Summary

The Phase 5 report generation identified **FIVE** issues. **Issues 1-3 have been COMPLETED ✅**. This document now focuses on the remaining Issue 5.

### Completed Issues ✅
1. **Section 2.2.2**: ✅ IFRS Cash Flow from Operations now shows `28,640` (FIXED)
2. **Section 2.3**: ✅ Dual-table FFO/AFFO reconciliation (2.3.1 issuer-reported + 2.3.2 calculated) (FIXED)
3. **Section 2.4**: ✅ Dual-table ACFO reconciliation (2.4.1 issuer-reported + 2.4.2 calculated) (FIXED)

### Remaining Issues ⚠️
4. **Phase 1/Phase 2**: FFO to AFFO reconciliation table (Table 33, MD&A page 20) extraction failure - AFFO adjustments (V-Z) not captured - **OPTIONAL** (future enhancement)
5. **Section 2.2.2 & 2.5.2**: ACFO calculated value (7,198) not populating placeholders; per-unit metrics not calculated for Net Income and ACFO - **CRITICAL** (needs immediate fix)

This implementation plan provides the remaining work to complete Issue 5.

---

## Quick Summary of Issues

| Issue | Section | Problem | Fix | Status |
|-------|---------|---------|-----|--------|
| **Issue 1** | 2.2.2 | CFO shows "Not extracted" | Read from `acfo_calculation_detail.cash_flow_from_operations` | ✅ **COMPLETED** |
| **Issue 2** | 2.3 | Missing issuer-reported FFO/AFFO table (2.3.1) | Add new reconciliation generator + template section | ✅ **COMPLETED** |
| **Issue 3** | 2.4 | Missing issuer-reported ACFO table (2.4.1) | Add new reconciliation generator + template section | ✅ **COMPLETED** |
| **Issue 4** | Phase 1/2 | Table 33 extraction failure (AFFO adjustments) | Investigate Camelot parameters or LLM table understanding | 🔵 **OPTIONAL** |
| **Issue 5** | 2.2.2 | Net Income per unit = N/A | Calculate: `-12,065 / 97,139 = -0.1242` | ⚠️ **REMAINING** |
| **Issue 5** | 2.2.2 | ACFO = "Not available" | Read from `acfo_metrics.acfo = 7,198` | ⚠️ **REMAINING** |
| **Issue 5** | 2.2.2 | ACFO per unit = "Not available" | Calculate: `7,198 / 97,139 = 0.0741` | ⚠️ **REMAINING** |
| **Issue 5** | 2.5.2 | ACFO Coverage = "Not available" | Calculate: `7,198 / 29,770 = 0.24x` | ⚠️ **REMAINING** |

**Key Insight:** Issue 5 consists of **simple placeholder fixes** (~45 minutes) that will complete all visible report issues.

---

## Root Cause Analysis

### Issue 1: CASH_FLOW_FROM_OPERATIONS Placeholder Bug

**Location:** `scripts/generate_final_report.py:1356`

**Current Code:**
```python
'CASH_FLOW_FROM_OPERATIONS': 'Not extracted',
```

**Actual Data Available:**
- Phase 2 extraction: `acfo_components.cash_flow_from_operations = 28640`
- Phase 3 metrics: Available in `acfo_calculation_detail.cash_flow_from_operations`

**Root Cause:** Hardcoded placeholder value instead of reading from Phase 2/Phase 3 data

**Impact:**
- Section 2.2.1 shows "IFRS Cash Flow from Operations: Not extracted"
- Section 2.2.2 shows "IFRS Cash Flow from Operations: Not extracted"
- Users cannot see the CFO starting point for ACFO calculations

---

### Issue 2: Missing Issuer-Reported FFO/AFFO Reconciliation (Section 2.3.1)

**Location:** `templates/credit_opinion_template.md:289-307`

**Current Implementation:**
- Template has ONE placeholder: `{{FFO_AFFO_RECONCILIATION_TABLE}}`
- Script generates ONE table using `format_reconciliation_table()` (line 755)
- Table shows only REALPAC-calculated values (Net Income → FFO → AFFO with adjustments A-Z)

**Required Implementation:**
- **2.3.1**: Issuer-Reported FFO/AFFO Reconciliation (if disclosed in MD&A)
  - Show issuer's disclosed reconciliation components (if available)
  - Mark as "Not disclosed" if issuer does not provide detailed reconciliation
- **2.3.2**: REALPAC-Calculated FFO/AFFO Reconciliation (always available)
  - Show standardized REALPAC calculation per January 2022 methodology
  - Current table moves to this subsection

**Root Cause:**
- Template structure assumes single reconciliation table
- No code to generate issuer-reported reconciliation from Phase 2 `ffo_affo_components`
- Phase 2 extraction contains individual components but not formatted as reconciliation

**Data Availability:**
- **Issuer-reported**: Phase 2 `ffo_affo.{ffo, affo}` - top-level values (34,491 and 16,939)
- **Issuer components**: Phase 2 `ffo_affo_components.*` - individual adjustments if disclosed
- **Calculated values**: Phase 3 `reit_metrics.ffo_calculation_detail` - full breakdown

**Challenge:**
- Most issuers (including Artis) do NOT disclose detailed FFO/AFFO component breakdowns in standardized REALPAC format
- Artis reports FFO=34,491 and AFFO=16,939 but does NOT show detailed A-Z adjustments
- Solution must handle "top-level values only" vs "full reconciliation disclosed" cases

---

### Issue 3: Missing Issuer-Reported ACFO Reconciliation (Section 2.4.1)

**Location:** `templates/credit_opinion_template.md:309-327`

**Current Implementation:**
- Template has ONE placeholder: `{{ACFO_RECONCILIATION_TABLE}}`
- Script generates ONE table using `format_acfo_reconciliation_table()` (line 762)
- Table shows only REALPAC-calculated values (CFO → ACFO with adjustments 1-17)

**Required Implementation:**
- **2.4.1**: Issuer-Reported ACFO Reconciliation (if disclosed - rare)
  - Show issuer's disclosed ACFO calculation (if available)
  - Mark as "Not disclosed - most issuers do not report ACFO" if unavailable
- **2.4.2**: REALPAC-Calculated ACFO Reconciliation (always available)
  - Show standardized REALPAC calculation per January 2023 White Paper
  - Current table moves to this subsection

**Root Cause:** Same as Issue 2 - single table assumption, no issuer-reported variant

**Data Availability:**
- **Issuer-reported**: Phase 2 `ffo_affo.acfo` - typically NULL (Artis = NULL)
- **Issuer components**: Phase 2 `acfo_components.*` - individual adjustments if disclosed
- **Calculated values**: Phase 3 `reit_metrics.acfo_calculation_detail` - full breakdown

**Reality Check:**
- > 95% of REITs do NOT report ACFO at all
- Artis does NOT report ACFO (correctly marked as NULL in Phase 2)
- Section 2.4.1 will almost always be "Not disclosed"
- This is expected and acceptable

---

### Issue 4: FFO to AFFO Reconciliation Table Extraction Failure (CRITICAL)

**Location:** Phase 1 markdown extraction → Phase 2 component extraction

**Problem Discovered:** MD&A Page 20/22 (Table 33) shows FFO to AFFO reconciliation with AFFO adjustments (V-Z), but table extraction is **incomplete**.

**Evidence from Artis REIT Q2 2025 MD&A:**

**Table 33 - Malformed Extraction:**
```markdown
| Column 1 | Column 2 |
|:---------|:---------|
| AFFO     | $        |
|          | 8,204    |
|          | $        |
|          | 17,063   |
|          | $        |
|          | (8,859)  |
|          | (51.9) % $|
|          | 16,939   |
|          | $        |
|          | 31,641   |
|          | $        |
|          | (14,702) |
|          | (46.5) % |
```

**What's Missing:** Row labels showing the FFO to AFFO adjustments!

**Expected table structure (based on MD&A text and REALPAC methodology):**
```
FFO                                    $16,956 (Q2)   $34,491 (YTD)
Less: Property maintenance reserve          (XXX)         (XXX)
Less: Leasing cost reserve                  (XXX)         (XXX)
Add/Less: Straight-line rent adjustment     (XXX)         (XXX)
Less: Other AFFO adjustments                (XXX)         (XXX)
AFFO                                    $8,204 (Q2)   $16,939 (YTD)
```

**Root Cause:** Camelot table extraction failure
- Values extracted correctly (8,204 / 16,939)
- Row labels NOT extracted (property maintenance reserve, leasing cost reserve, straight-line rent)
- Table structure malformed in markdown

**Cascading Impact:**

1. **Phase 1 (PDF → Markdown)**: Table 33 extraction incomplete
2. **Phase 2 (Markdown → JSON)**: Cannot identify AFFO adjustments without row labels
3. **Phase 2 Result**: `ffo_affo_components` has ZERO for all AFFO adjustments (V-Z):
   ```json
   {
     "capex_sustaining": 0,
     "leasing_costs": 0,
     "tenant_improvements": 0,
     "straight_line_rent": 0,
     "non_controlling_interests_affo": 0
   }
   ```
4. **Phase 3**: Calculates AFFO from FFO with zero adjustments → AFFO_calculated = FFO_calculated (4,034 = 4,034)
5. **Phase 5**: Cannot show issuer-reported AFFO reconciliation in Section 2.3.1

**What Artis ACTUALLY Disclosed (per MD&A text):**
- Uses **reserve methodology** for AFFO calculation
- Property maintenance reserve: "2021-2024 actuals + 2025 budget, adjusted for dispositions"
- Leasing cost reserve: "Amortization of leasing costs over lease term"
- Approximately 60.5% of capex recoverable from tenants
- Straight-line rent adjustments: Present but not quantified in broken table

**Severity:** CRITICAL
- Artis discloses detailed AFFO methodology but we can't extract it
- Makes "issuer-reported reconciliation" feature partially ineffective for Artis
- Similar table extraction issues likely affect other issuers

**Solutions (in priority order):**

**Option 1: Enhanced Camelot Extraction (HIGH PRIORITY)**
- Investigate why Camelot failed on Table 33
- Test with different Camelot parameters (lattice vs stream, edge detection)
- May require manual table structure hints for complex multi-level tables

**Option 2: Alternative PDF Table Extraction**
- Try `pdfplumber` or `tabula-py` as alternatives to Camelot
- Compare extraction quality across tools
- Hybrid approach: Camelot + fallback to pdfplumber

**Option 3: LLM-Based Table Understanding (MEDIUM PRIORITY)**
- Use LLM to "understand" malformed tables from context
- Extract table semantics from surrounding text (e.g., "Management has deducted from AFFO the actual amortization of recoverable capital expenditures")
- More robust but slower

**Option 4: Manual Extraction Hints (SHORT-TERM WORKAROUND)**
- Flag known problematic tables for manual review
- Provide extraction hints file: "MD&A Table 33 = FFO to AFFO reconciliation"
- Human-in-the-loop for critical tables

**Recommended Approach:**
1. **Phase 0 (NEW)**: Investigate Camelot parameters for Table 33 specifically (1 hour)
2. If Camelot fixes work → apply to Phase 1 preprocessing
3. If Camelot cannot fix → implement Option 3 (LLM table understanding) for FFO/AFFO reconciliations
4. Document known extraction failures in Phase 2 output (`data_quality.table_extraction_issues`)

**Impact on Current Implementation Plan:**
- **Phase 3** (reconciliation generators) must handle "summary only" case for Artis
- Even with perfect code, Artis will show "Summary values only" in Section 2.3.1
- This is correct behavior given broken source table extraction
- Future improvement: Fix Phase 1 extraction, re-run Phase 2 for Artis

**Data Quality Note:**
Add to Phase 2 extraction output:
```json
{
  "ffo_affo_components": {
    "data_quality": {
      "ffo_components": "strong",
      "affo_components": "limited - table extraction failure",
      "table_extraction_issues": [
        "MD&A Table 33 (FFO to AFFO reconciliation): Row labels not extracted by Camelot",
        "AFFO adjustments (V-Z) could not be identified from malformed table"
      ]
    }
  }
}
```

---

### Issue 5: ACFO Value and Per-Unit Calculations Missing in Sections 2.2.2 and 2.5.2

**Location:** `scripts/generate_final_report.py` placeholder population (lines ~1300-1400)

**Problems Discovered:**

1. **Section 2.2.2 Line 687**: ACFO shows "Not available" when it was calculated as **7,198** (visible in section 2.4.2 reconciliation table line 800)
2. **Section 2.2.2 Line 683**: Net Income per unit shows "N/A" when it should be calculated as -12,065 / 97,139 = **-$0.1242**
3. **Section 2.2.2 Line 687**: ACFO per unit shows "Not available" when it should be calculated as 7,198 / 97,139 = **$0.0741**
4. **Section 2.5.2 Line 848**: ACFO Coverage shows "Not available" when it should be 7,198 / 29,770 = **0.24x** coverage (24% payout ratio = 404.9%)

**Evidence from Report:**

**Section 2.2.2 (Current - Broken):**
```markdown
| Metric | Amount (CAD 000s) | Per Unit (CAD) | Payout Ratio | Variance from Reported (%) |
|--------|---------------------------|------------------------|--------------|---------------------------|
| **IFRS Net Income** | -12,065 | N/A | N/A | N/A |
| **ACFO** | Not available | Not available | Not available% | Not available% |
```

**Section 2.4.2 Reconciliation (Shows ACFO WAS Calculated):**
```markdown
| **Adjusted Cash Flow from Operations (ACFO)** | **7,198** |
```

**Section 2.5.2 (Current - Broken):**
```markdown
| **ACFO Coverage** | Not available | 29,770 | N/Ax | Not available% | Not calculated - requires cash flow statement data | Not available% |
```

**Root Cause:**

The placeholders in `generate_final_report.py` are not reading ACFO from the Phase 3 `acfo_metrics` dictionary. Specifically:

**Line ~1340-1360 (Section 2.2.2 placeholders):**
```python
'ACFO_CALCULATED': 'Not available',           # HARDCODED - should read from acfo_metrics['acfo']
'ACFO_PER_UNIT_CALCULATED': 'Not available',  # HARDCODED - should calculate from acfo / units
'NET_INCOME_PER_UNIT_CALCULATED': 'N/A',      # HARDCODED - should calculate from net_income / units
```

**Line ~1450-1480 (Section 2.5.2 placeholders):**
```python
'ACFO_COVERAGE_CALCULATED': 'Not available',  # HARDCODED - should calculate from acfo / distributions
'ACFO_PAYOUT_RATIO_CALCULATED': 'Not available%',  # HARDCODED - should calculate inverse
```

**Actual Data Available in Phase 3 Metrics:**
```json
{
  "acfo_metrics": {
    "acfo": 7198,
    "acfo_per_unit": 0.0741,              // May or may not be present
    "acfo_calculation_detail": {
      "cash_flow_from_operations": 28640,
      "adjustments": {...},
      "acfo": 7198
    }
  },
  "income_statement": {
    "net_income": -12065
  },
  "balance_sheet": {
    "common_units_outstanding": 97139,
    "diluted_units_outstanding": 98387
  },
  "distributions": {
    "total_distributions": 29770
  }
}
```

**Impact:**

1. **Incorrect Report Content**: Users see "Not available" when value is actually calculated
2. **Inconsistency**: Section 2.4.2 shows ACFO=7,198 but section 2.2.2 shows "Not available"
3. **Missing Analysis**: Cannot assess ACFO payout ratio (404.9% - critically unsustainable)
4. **Incomplete Coverage Analysis**: Missing ACFO coverage metric (0.24x) in section 2.5.2

**Fix Strategy:**

**Phase 1A (NEW - 15 minutes):** Add ACFO and per-unit calculation functions
**Phase 1B (REVISED - 30 minutes):** Update placeholders to populate from Phase 3 metrics

**Required Functions (add to `generate_final_report.py`):**

```python
def calculate_per_unit_if_available(amount, units_outstanding):
    """Calculate per-unit metric safely"""
    if amount is not None and units_outstanding and units_outstanding > 0:
        return amount / units_outstanding
    return None

def format_per_unit(value):
    """Format per-unit value or return N/A"""
    if value is not None:
        return f"{value:.4f}"
    return "N/A"
```

**Required Placeholder Updates (lines ~1340-1360):**

```python
# Calculate per-unit metrics
basic_units = balance_sheet.get('common_units_outstanding', 0)
net_income = income_statement.get('net_income', 0)
acfo_value = acfo_metrics.get('acfo', 0)

# Net Income per unit (CALCULATED)
net_income_per_unit_calc = calculate_per_unit_if_available(net_income, basic_units)

# ACFO (CALCULATED)
acfo_per_unit_calc = calculate_per_unit_if_available(acfo_value, basic_units)

# Section 2.2.2 placeholders
'NET_INCOME_PER_UNIT_CALCULATED': format_per_unit(net_income_per_unit_calc),
'ACFO_CALCULATED': format_number(acfo_value) if acfo_value else 'Not available',
'ACFO_PER_UNIT_CALCULATED': format_per_unit(acfo_per_unit_calc),
```

**Required Placeholder Updates (lines ~1450-1480):**

```python
# ACFO coverage calculations
total_distributions = distributions.get('total_distributions', 0)
acfo_coverage_calc = acfo_value / total_distributions if total_distributions > 0 and acfo_value else None
acfo_payout_calc = (total_distributions / acfo_value * 100) if acfo_value > 0 else None

# Section 2.5.2 placeholders
'ACFO_COVERAGE_CALCULATED': f"{acfo_coverage_calc:.2f}x" if acfo_coverage_calc else 'N/Ax',
'ACFO_PAYOUT_RATIO_CALCULATED': f"{acfo_payout_calc:.1f}%" if acfo_payout_calc else 'Not available%',
'ACFO_COVERAGE_ASSESSMENT_CALCULATED': assess_distribution_coverage(acfo_coverage_calc) if acfo_coverage_calc else 'Not calculated',
```

**Expected Results After Fix:**

**Section 2.2.2 (Fixed):**
```markdown
| Metric | Amount (CAD 000s) | Per Unit (CAD) | Payout Ratio | Variance from Reported (%) |
|--------|---------------------------|------------------------|--------------|---------------------------|
| **IFRS Net Income** | -12,065 | -0.1242 | N/A | N/A |
| **ACFO** | 7,198 | 0.0741 | 404.9% | N/A (not reported) |
```

**Section 2.5.2 (Fixed):**
```markdown
| **ACFO Coverage** | 7,198 | 29,770 | 0.24x | 404.9% | Insufficient - distributions exceed sustainable cash flow by 305% | -304.9% |
```

**Severity:** HIGH - Calculated values exist but are not displayed, creating false impression of missing data

---

## Implementation Plan

### Phase 1A: Add Per-Unit Calculation Helper Functions (15 minutes)

**Priority:** CRITICAL
**Effort:** Low
**Risk:** Low

**File:** `scripts/generate_final_report.py`

**Add helper functions after the existing helper functions (around line 486):**

```python
def calculate_per_unit_if_available(amount, units_outstanding):
    """
    Calculate per-unit metric safely with None handling

    Args:
        amount: Numeric value (can be negative, e.g., net income)
        units_outstanding: Number of units/shares outstanding

    Returns:
        float or None: Per-unit value, or None if calculation not possible
    """
    if amount is not None and units_outstanding and units_outstanding > 0:
        return amount / units_outstanding
    return None

def format_per_unit(value):
    """
    Format per-unit value for display

    Args:
        value: Per-unit value (float or None)

    Returns:
        str: Formatted string (e.g., "0.1234") or "N/A"
    """
    if value is not None:
        return f"{value:.4f}"
    return "N/A"
```

**Commit:**
```bash
git add scripts/generate_final_report.py
git commit -m "feat(phase5): add per-unit calculation helper functions (v1.0.13)"
```

---

### Phase 1B: Fix ACFO, CFO, and Per-Unit Placeholders (30 minutes)

**Priority:** CRITICAL
**Effort:** Medium
**Risk:** Low

**File:** `scripts/generate_final_report.py`

**Location:** Placeholder population section (lines ~1300-1500)

#### Step 1: Calculate Per-Unit Metrics (add before placeholder dict)

```python
# Extract data for per-unit calculations
balance_sheet = phase3_data.get('balance_sheet', {})
income_statement = phase3_data.get('income_statement', {})
acfo_metrics_dict = phase3_data.get('acfo_metrics', {})
distributions_dict = phase3_data.get('distributions', {})

basic_units = balance_sheet.get('common_units_outstanding', 0)
net_income = income_statement.get('net_income', 0)
acfo_value = acfo_metrics_dict.get('acfo', 0)
cfo_value = acfo_metrics_dict.get('acfo_calculation_detail', {}).get('cash_flow_from_operations', 0)
total_distributions = distributions_dict.get('total_distributions', 0)

# Calculate per-unit metrics
net_income_per_unit_calc = calculate_per_unit_if_available(net_income, basic_units)
acfo_per_unit_calc = calculate_per_unit_if_available(acfo_value, basic_units)

# Calculate ACFO coverage ratios
acfo_coverage_calc = acfo_value / total_distributions if total_distributions > 0 and acfo_value else None
acfo_payout_calc = (total_distributions / acfo_value * 100) if acfo_value > 0 else None
```

#### Step 2: Update Section 2.2.2 Placeholders (line ~1340-1360)

**Current:**
```python
'CASH_FLOW_FROM_OPERATIONS': 'Not extracted',
'NET_INCOME_PER_UNIT_CALCULATED': 'N/A',
'ACFO_CALCULATED': 'Not available',
'ACFO_PER_UNIT_CALCULATED': 'Not available',
'ACFO_PAYOUT_RATIO_CALCULATED': 'Not available%',
```

**Fixed:**
```python
'CASH_FLOW_FROM_OPERATIONS': format_number(cfo_value) if cfo_value else 'Not extracted',
'NET_INCOME_PER_UNIT_CALCULATED': format_per_unit(net_income_per_unit_calc),
'ACFO_CALCULATED': format_number(acfo_value) if acfo_value else 'Not available',
'ACFO_PER_UNIT_CALCULATED': format_per_unit(acfo_per_unit_calc),
'ACFO_PAYOUT_RATIO_CALCULATED': f"{acfo_payout_calc:.1f}%" if acfo_payout_calc else 'Not available%',
'ACFO_VARIANCE_FROM_REPORTED': 'N/A (not reported)',  # Artis does not report ACFO
```

#### Step 3: Update Section 2.5.2 Placeholders (line ~1450-1480)

**Current:**
```python
'ACFO_COVERAGE_CALCULATED': 'Not available',
'ACFO_PAYOUT_RATIO_CALCULATED': 'Not available%',
'ACFO_COVERAGE_ASSESSMENT_CALCULATED': 'Not calculated - requires cash flow statement data',
```

**Fixed:**
```python
'ACFO_COVERAGE_CALCULATED': f"{acfo_coverage_calc:.2f}x" if acfo_coverage_calc else 'N/Ax',
'ACFO_PAYOUT_RATIO_CALCULATED': f"{acfo_payout_calc:.1f}%" if acfo_payout_calc else 'Not available%',
'ACFO_COVERAGE_ASSESSMENT_CALCULATED': assess_distribution_coverage(acfo_coverage_calc) if acfo_coverage_calc else 'Not calculated',
'ACFO_COVERAGE_CUSHION_CALCULATED': f"{(acfo_coverage_calc - 1.0) * 100:.1f}%" if acfo_coverage_calc else 'Not available%',
```

#### Step 4: Test with Artis REIT data

```bash
python scripts/generate_final_report.py \
  Issuer_Reports/Artis_REIT/temp/phase3_calculated_metrics.json \
  Issuer_Reports/Artis_REIT/temp/phase4_credit_analysis.md
```

**Expected outputs:**
- Section 2.2.2 Line 672: `IFRS Cash Flow from Operations: 28,640` ✓
- Section 2.2.2 Line 683: `IFRS Net Income per unit: -0.1242` ✓
- Section 2.2.2 Line 687: `ACFO: 7,198 | Per Unit: 0.0741 | Payout: 404.9%` ✓
- Section 2.5.2 Line 848: `ACFO Coverage: 0.24x | Payout: 404.9% | Assessment: Insufficient` ✓

**Commit:**
```bash
git add scripts/generate_final_report.py
git commit -m "fix(phase5): populate ACFO, CFO, and per-unit metrics from Phase 3 data (v1.0.13)"
```

**Expected Results:**
- All placeholder values populated from Phase 3 calculated metrics
- Per-unit calculations working for Net Income and ACFO
- ACFO coverage ratios calculated and displayed correctly

---

## Completed Implementation (Issues 1-3) ✅

The following phases have been **COMPLETED**:

### ✅ Phase 1: CFO Placeholder Fix (Issue 1)
- **Completed**: `CASH_FLOW_FROM_OPERATIONS` now reads from Phase 3 metrics
- **Result**: Section 2.2.2 shows CFO = 28,640

### ✅ Phase 2: Template Restructuring (Issues 2-3)
- **Completed**: Sections 2.3 and 2.4 restructured with dual-table subsections (2.3.1/2.3.2 and 2.4.1/2.4.2)

### ✅ Phase 3: Issuer-Reported Reconciliation Generators (Issues 2-3)
- **Completed**: `generate_issuer_reported_ffo_affo_reconciliation()` and `generate_issuer_reported_acfo_reconciliation()` functions added

### ✅ Phase 4: Script Integration (Issues 2-3)
- **Completed**: New placeholders integrated into `generate_final_report.py`

### ✅ Phase 5: Testing with Artis REIT (Issues 1-3)
- **Completed**: Verified dual-table reconciliations working correctly

---

## Remaining Implementation (Issue 5) ⚠️

### Phase 2-6: Dual-Table Reconciliation Implementation

**STATUS: ALREADY COMPLETED ✅**

These phases have been completed and are documented in the "Completed Implementation" section above:
- ✅ Phase 2: Template restructuring (sections 2.3 and 2.4)
- ✅ Phase 3: Issuer-reported reconciliation generators
- ✅ Phase 4: Script integration
- ✅ Phase 5: Testing with Artis REIT
- ✅ Phase 6: Documentation updates

For implementation details, see the completed sections 2.3.1/2.3.2 (FFO/AFFO) and 2.4.1/2.4.2 (ACFO) in the generated reports.

---

## Next Steps (Issue 5 Only)

**REMAINING WORK:** Phase 1A + Phase 1B (45 minutes total)

See Phase 1A and Phase 1B sections above for detailed implementation steps.

---

#### OLD CONTENT BELOW (for reference only - already completed)

#### 2A: Section 2.3 - FFO/AFFO Reconciliation

**Current (lines 289-307):**
```markdown
#### 2.3 FFO/AFFO Reconciliation

This reconciliation demonstrates the adjustment process from IFRS Net Income to FFO to AFFO per REALPAC methodology (January 2022). The table shows both issuer-reported adjustments (if disclosed) and our calculated adjustments using REALPAC guidelines.

{{FFO_AFFO_RECONCILIATION_TABLE}}

**Key Observations:**
{{FFO_AFFO_OBSERVATIONS}}
```

**Updated:**
```markdown
#### 2.3 FFO/AFFO Reconciliation

This reconciliation demonstrates the adjustment process from IFRS Net Income to FFO to AFFO per REALPAC methodology (January 2022). This section presents both issuer-reported values (if disclosed) and our calculated values using standardized REALPAC guidelines for comparability.

**2.3.1 Issuer-Reported FFO/AFFO Reconciliation**

*As disclosed in issuer's MD&A (if available)*

{{FFO_AFFO_RECONCILIATION_TABLE_REPORTED}}

**2.3.2 REALPAC-Calculated FFO/AFFO Reconciliation**

*Calculated using standardized REALPAC methodology for cross-issuer comparability*

{{FFO_AFFO_RECONCILIATION_TABLE_CALCULATED}}

**Key Observations:**
{{FFO_AFFO_OBSERVATIONS}}
```

#### 2B: Section 2.4 - ACFO Reconciliation

**Current (lines 309-327):**
```markdown
#### 2.4 ACFO Reconciliation

This reconciliation demonstrates the adjustment process from IFRS Cash Flow from Operations to ACFO per REALPAC ACFO White Paper (January 2023). The table shows both issuer-reported adjustments (if disclosed - rare) and our calculated adjustments using REALPAC guidelines.

{{ACFO_RECONCILIATION_TABLE}}

**Key Observations:**
{{ACFO_OBSERVATIONS}}
```

**Updated:**
```markdown
#### 2.4 ACFO Reconciliation

This reconciliation demonstrates the adjustment process from IFRS Cash Flow from Operations to ACFO per REALPAC ACFO White Paper (January 2023). This section presents both issuer-reported values (if disclosed - rare) and our calculated values using standardized REALPAC guidelines.

**2.4.1 Issuer-Reported ACFO Reconciliation**

*As disclosed in issuer's MD&A (if available - most issuers do not report ACFO)*

{{ACFO_RECONCILIATION_TABLE_REPORTED}}

**2.4.2 REALPAC-Calculated ACFO Reconciliation**

*Calculated using standardized REALPAC methodology for cross-issuer comparability*

{{ACFO_RECONCILIATION_TABLE_CALCULATED}}

**Key Observations:**
{{ACFO_OBSERVATIONS}}
```

**Commit:**
```bash
git add templates/credit_opinion_template.md
git commit -m "refactor(template): restructure sections 2.3 and 2.4 for dual-table reconciliations (v1.0.13)"
```

---

### Phase 3: Implement Issuer-Reported Reconciliation Table Generators (2 hours)

**Priority:** HIGH
**Effort:** High
**Risk:** Medium (new code, edge cases)

**File:** `scripts/calculate_credit_metrics/reconciliation.py`

#### 3A: Add `generate_issuer_reported_ffo_affo_reconciliation()` Function

**New Function (add after line 115):**

```python
def generate_issuer_reported_ffo_affo_reconciliation(phase2_data):
    """
    Generate issuer-reported FFO/AFFO reconciliation table (if disclosed)

    Args:
        phase2_data (dict): Phase 2 extraction data (full JSON)

    Returns:
        dict or None: Issuer-reported reconciliation structure, or None if not disclosed
    """

    ffo_affo = phase2_data.get('ffo_affo', {})
    ffo_affo_components = phase2_data.get('ffo_affo_components', {})

    # Check if issuer disclosed detailed components (any non-zero adjustment)
    has_components = False
    component_fields = [
        'unrealized_fv_changes', 'depreciation_real_estate', 'amortization_tenant_allowances',
        'amortization_intangibles', 'gains_losses_property_sales', 'tax_on_disposals',
        'deferred_taxes', 'impairment_losses_reversals', 'revaluation_gains_losses',
        'transaction_costs_business_comb', 'foreign_exchange_gains_losses',
        'sale_foreign_operations', 'fv_changes_hedges', 'goodwill_impairment',
        'puttable_instruments_effects', 'discontinued_operations',
        'equity_accounted_adjustments', 'incremental_leasing_costs',
        'property_taxes_ifric21', 'rou_asset_revenue_expense',
        'non_controlling_interests_ffo', 'capex_sustaining', 'leasing_costs',
        'tenant_improvements', 'straight_line_rent', 'non_controlling_interests_affo'
    ]

    for field in component_fields:
        if ffo_affo_components.get(field, 0) != 0:
            has_components = True
            break

    # Case 1: Issuer provides detailed reconciliation (rare)
    if has_components and ffo_affo.get('ffo') and ffo_affo.get('affo'):
        return {
            'reconciliation_type': 'detailed',
            'starting_point': {
                'description': 'IFRS Net Income (as reported by issuer)',
                'amount': ffo_affo_components.get('net_income_ifrs', 0)
            },
            'ffo_adjustments': _build_issuer_adjustments(ffo_affo_components, 'ffo'),
            'ffo_total': {
                'description': 'Funds From Operations (FFO) - Issuer Reported',
                'amount': ffo_affo.get('ffo', 0)
            },
            'affo_adjustments': _build_issuer_adjustments(ffo_affo_components, 'affo'),
            'affo_total': {
                'description': 'Adjusted Funds From Operations (AFFO) - Issuer Reported',
                'amount': ffo_affo.get('affo', 0)
            },
            'metadata': {
                'disclosure_quality': 'detailed',
                'source': 'MD&A FFO/AFFO reconciliation table'
            }
        }

    # Case 2: Issuer provides only top-level FFO/AFFO (common - Artis example)
    elif ffo_affo.get('ffo') and ffo_affo.get('affo'):
        return {
            'reconciliation_type': 'summary_only',
            'ffo_reported': ffo_affo.get('ffo', 0),
            'ffo_per_unit': ffo_affo.get('ffo_per_unit', 0),
            'affo_reported': ffo_affo.get('affo', 0),
            'affo_per_unit': ffo_affo.get('affo_per_unit', 0),
            'metadata': {
                'disclosure_quality': 'summary_only',
                'source': 'MD&A - top-level FFO/AFFO disclosure',
                'note': 'Issuer does not disclose detailed FFO/AFFO reconciliation components. Only top-level values provided.'
            }
        }

    # Case 3: No FFO/AFFO disclosure (very rare for public REITs)
    else:
        return None


def _build_issuer_adjustments(components, metric_type):
    """
    Helper: Build adjustment list from Phase 2 components

    Args:
        components (dict): ffo_affo_components from Phase 2
        metric_type (str): 'ffo' or 'affo'

    Returns:
        list: Adjustment entries with description and amount
    """
    adjustments = []

    if metric_type == 'ffo':
        # FFO adjustments (A-U)
        adj_map = {
            'unrealized_fv_changes': 'A. Unrealized fair value changes (investment properties)',
            'depreciation_real_estate': 'B. Depreciation of depreciable real estate assets',
            'amortization_tenant_allowances': 'C. Amortization of tenant allowances (fit-out)',
            'amortization_intangibles': 'D. Amortization of tenant/customer relationship intangibles',
            'gains_losses_property_sales': 'E. Gains/losses from sales of investment properties',
            'tax_on_disposals': 'F. Tax on gains or losses on disposals',
            'deferred_taxes': 'G. Deferred taxes',
            'impairment_losses_reversals': 'H. Impairment losses or reversals',
            'revaluation_gains_losses': 'I. Revaluation gains/losses (owner-occupied)',
            'transaction_costs_business_comb': 'J. Transaction costs (business combinations)',
            'foreign_exchange_gains_losses': 'K. Foreign exchange gains/losses',
            'sale_foreign_operations': 'L. Gain/loss on sale of foreign operations',
            'fv_changes_hedges': 'M. Fair value changes (economically effective hedges)',
            'goodwill_impairment': 'N. Goodwill impairment or negative goodwill',
            'puttable_instruments_effects': 'O. Effects of puttable instruments',
            'discontinued_operations': 'P. Results of discontinued operations',
            'equity_accounted_adjustments': 'Q. Adjustments for equity accounted entities',
            'incremental_leasing_costs': 'R. Incremental leasing costs',
            'property_taxes_ifric21': 'S. Property taxes (IFRIC 21)',
            'rou_asset_revenue_expense': 'T. ROU asset revenue/expenses',
            'non_controlling_interests_ffo': 'U. Non-controlling interests (FFO adjustments)'
        }
    else:  # affo
        # AFFO adjustments (V-Z)
        adj_map = {
            'capex_sustaining': 'V. Sustaining/maintenance capital expenditures',
            'leasing_costs': 'W. Leasing costs (internal + external)',
            'tenant_improvements': 'X. Tenant improvements (sustaining)',
            'straight_line_rent': 'Y. Straight-line rent adjustment',
            'non_controlling_interests_affo': 'Z. Non-controlling interests (AFFO adjustments)'
        }

    for field, description in adj_map.items():
        amount = components.get(field, 0)
        if amount != 0:  # Only include non-zero adjustments
            adjustments.append({
                'description': description,
                'amount': amount
            })

    return adjustments


def format_issuer_reported_ffo_affo_reconciliation(recon):
    """
    Format issuer-reported FFO/AFFO reconciliation as markdown

    Args:
        recon (dict or None): Output from generate_issuer_reported_ffo_affo_reconciliation()

    Returns:
        str: Markdown-formatted table or "Not disclosed" message
    """

    if not recon:
        return """## Issuer-Reported FFO/AFFO Reconciliation

**Not disclosed** - Issuer does not report FFO/AFFO. All metrics calculated using REALPAC methodology (see Section 2.3.2).

*Note: This is rare for public REITs. Verify MD&A for non-standard FFO disclosures.*"""

    if recon['reconciliation_type'] == 'summary_only':
        # Case: Top-level values only (Artis example)
        return f"""## Issuer-Reported FFO/AFFO Summary

**Disclosure Type:** Summary values only (detailed reconciliation not disclosed)

| Metric | Amount (000s) | Per Unit |
|--------|---------------|----------|
| **FFO (Issuer-Reported)** | {recon['ffo_reported']:,.0f} | ${recon['ffo_per_unit']:.4f} |
| **AFFO (Issuer-Reported)** | {recon['affo_reported']:,.0f} | ${recon['affo_per_unit']:.4f} |

**Note:** {recon['metadata']['note']}

**Source:** {recon['metadata']['source']}

*For detailed reconciliation showing Net Income → FFO → AFFO adjustments, see Section 2.3.2 (REALPAC-Calculated Reconciliation).*"""

    else:  # detailed reconciliation
        lines = []
        lines.append("## Issuer-Reported FFO/AFFO Reconciliation (Detailed)")
        lines.append("")
        lines.append("**Disclosure Type:** Full reconciliation disclosed by issuer")
        lines.append("")
        lines.append("| Line Item | Amount (000s) |")
        lines.append("|-----------|---------------|")

        # Starting point
        lines.append(f"| **{recon['starting_point']['description']}** | **{recon['starting_point']['amount']:,.0f}** |")

        # FFO adjustments
        if recon['ffo_adjustments']:
            lines.append("| **FFO Adjustments (as reported):** | |")
            for adj in recon['ffo_adjustments']:
                sign = "+" if adj['amount'] >= 0 else ""
                lines.append(f"| {adj['description']} | {sign}{adj['amount']:,.0f} |")

        # FFO total
        lines.append(f"| **{recon['ffo_total']['description']}** | **{recon['ffo_total']['amount']:,.0f}** |")

        # AFFO adjustments
        if recon['affo_adjustments']:
            lines.append("| **AFFO Adjustments (as reported):** | |")
            for adj in recon['affo_adjustments']:
                sign = "+" if adj['amount'] >= 0 else ""
                lines.append(f"| {adj['description']} | {sign}{adj['amount']:,.0f} |")

        # AFFO total
        lines.append(f"| **{recon['affo_total']['description']}** | **{recon['affo_total']['amount']:,.0f}** |")

        lines.append("")
        lines.append(f"**Source:** {recon['metadata']['source']}")
        lines.append("")
        lines.append("*Note: This reconciliation reflects the issuer's disclosed methodology, which may differ from standardized REALPAC methodology. See Section 2.3.2 for REALPAC-calculated reconciliation for cross-issuer comparability.*")

        return "\n".join(lines)
```

#### 3B: Add `generate_issuer_reported_acfo_reconciliation()` Function

**New Function (add after format_issuer_reported_ffo_affo_reconciliation):**

```python
def generate_issuer_reported_acfo_reconciliation(phase2_data):
    """
    Generate issuer-reported ACFO reconciliation table (if disclosed)

    Note: > 95% of issuers do NOT report ACFO. This will almost always return None.

    Args:
        phase2_data (dict): Phase 2 extraction data (full JSON)

    Returns:
        dict or None: Issuer-reported ACFO reconciliation, or None if not disclosed
    """

    ffo_affo = phase2_data.get('ffo_affo', {})
    acfo_components = phase2_data.get('acfo_components', {})

    # Check if issuer reported ACFO (very rare)
    issuer_acfo = ffo_affo.get('acfo')

    if issuer_acfo is None:
        # Common case - issuer does not report ACFO
        return None

    # Issuer reports ACFO - check if detailed components disclosed
    has_components = False
    component_fields = [
        'change_in_working_capital', 'interest_financing', 'jv_distributions',
        'capex_sustaining_acfo', 'leasing_costs_external', 'tenant_improvements_acfo',
        'realized_investment_gains_losses', 'taxes_non_operating',
        'transaction_costs_acquisitions', 'transaction_costs_disposals',
        'deferred_financing_fees', 'debt_termination_costs'
    ]

    for field in component_fields:
        if acfo_components.get(field, 0) != 0:
            has_components = True
            break

    cfo = acfo_components.get('cash_flow_from_operations', 0)

    if has_components and cfo > 0:
        # Detailed ACFO reconciliation disclosed (extremely rare)
        return {
            'reconciliation_type': 'detailed',
            'starting_point': {
                'description': 'Cash Flow from Operations (IFRS) - Issuer Reported',
                'amount': cfo
            },
            'acfo_adjustments': _build_issuer_acfo_adjustments(acfo_components),
            'acfo_total': {
                'description': 'Adjusted Cash Flow from Operations (ACFO) - Issuer Reported',
                'amount': issuer_acfo
            },
            'metadata': {
                'disclosure_quality': 'detailed',
                'source': 'MD&A ACFO reconciliation table',
                'note': 'Rare disclosure - most issuers do not report ACFO'
            }
        }
    else:
        # Summary only - issuer reports ACFO value but not detailed reconciliation
        return {
            'reconciliation_type': 'summary_only',
            'acfo_reported': issuer_acfo,
            'acfo_per_unit': ffo_affo.get('acfo_per_unit', 0),
            'cfo_reported': cfo if cfo > 0 else None,
            'metadata': {
                'disclosure_quality': 'summary_only',
                'source': 'MD&A - top-level ACFO disclosure',
                'note': 'Issuer reports ACFO value but does not disclose detailed reconciliation components.'
            }
        }


def _build_issuer_acfo_adjustments(components):
    """
    Helper: Build ACFO adjustment list from Phase 2 components

    Args:
        components (dict): acfo_components from Phase 2

    Returns:
        list: Adjustment entries with description and amount
    """
    adjustments = []

    adj_map = {
        'change_in_working_capital': '1. Eliminate working capital changes',
        'interest_financing': '2. Interest expense (financing activities)',
        'jv_distributions': '3a. JV distributions received',
        'jv_acfo': '3b. JV ACFO (calculated)',
        'capex_sustaining_acfo': '4. Sustaining/maintenance capital expenditures',
        'leasing_costs_external': '5. External leasing costs',
        'tenant_improvements_acfo': '6. Sustaining tenant improvements',
        'realized_investment_gains_losses': '7. Realized investment gains/losses',
        'taxes_non_operating': '8. Taxes related to non-operating activities',
        'transaction_costs_acquisitions': '9. Transaction costs (acquisitions)',
        'transaction_costs_disposals': '10. Transaction costs (disposals)',
        'deferred_financing_fees': '11. Deferred financing fees',
        'debt_termination_costs': '12. Debt termination costs',
        'interest_income_timing': '14a. Interest income timing adjustments',
        'interest_expense_timing': '14b. Interest expense timing adjustments',
        'rou_sublease_principal_received': '16a. ROU sublease principal received',
        'rou_lease_principal_paid': '16c. ROU lease principal paid',
        'non_controlling_interests_acfo': '17a. Non-controlling interests (ACFO)'
    }

    for field, description in adj_map.items():
        amount = components.get(field, 0)
        if amount != 0:  # Only include non-zero adjustments
            adjustments.append({
                'description': description,
                'amount': amount
            })

    return adjustments


def format_issuer_reported_acfo_reconciliation(recon):
    """
    Format issuer-reported ACFO reconciliation as markdown

    Args:
        recon (dict or None): Output from generate_issuer_reported_acfo_reconciliation()

    Returns:
        str: Markdown-formatted table or "Not disclosed" message
    """

    if not recon:
        return """## Issuer-Reported ACFO Reconciliation

**Not disclosed** - Issuer does not report ACFO.

*Note: Most issuers (> 95%) do not report ACFO per REALPAC ACFO White Paper (January 2023). This is expected. All ACFO metrics calculated using REALPAC methodology (see Section 2.4.2).*"""

    if recon['reconciliation_type'] == 'summary_only':
        # Issuer reports ACFO value but not detailed reconciliation
        cfo_line = ""
        if recon.get('cfo_reported'):
            cfo_line = f"| **IFRS Cash Flow from Operations** | {recon['cfo_reported']:,.0f} | N/A |\n"

        return f"""## Issuer-Reported ACFO Summary

**Disclosure Type:** Summary value only (detailed reconciliation not disclosed)

| Metric | Amount (000s) | Per Unit |
|--------|---------------|----------|
{cfo_line}| **ACFO (Issuer-Reported)** | {recon['acfo_reported']:,.0f} | ${recon['acfo_per_unit']:.4f} |

**Note:** {recon['metadata']['note']}

**Source:** {recon['metadata']['source']}

*For detailed reconciliation showing CFO → ACFO adjustments, see Section 2.4.2 (REALPAC-Calculated Reconciliation).*"""

    else:  # detailed reconciliation (extremely rare)
        lines = []
        lines.append("## Issuer-Reported ACFO Reconciliation (Detailed)")
        lines.append("")
        lines.append("**Disclosure Type:** Full reconciliation disclosed by issuer (rare)")
        lines.append("")
        lines.append("| Line Item | Amount (000s) |")
        lines.append("|-----------|---------------|")

        # Starting point
        lines.append(f"| **{recon['starting_point']['description']}** | **{recon['starting_point']['amount']:,.0f}** |")

        # ACFO adjustments
        if recon['acfo_adjustments']:
            lines.append("| **ACFO Adjustments (as reported):** | |")
            for adj in recon['acfo_adjustments']:
                sign = "+" if adj['amount'] >= 0 else ""
                lines.append(f"| {adj['description']} | {sign}{adj['amount']:,.0f} |")

        # ACFO total
        lines.append(f"| **{recon['acfo_total']['description']}** | **{recon['acfo_total']['amount']:,.0f}** |")

        lines.append("")
        lines.append(f"**Source:** {recon['metadata']['source']}")
        lines.append(f"**Note:** {recon['metadata']['note']}")
        lines.append("")
        lines.append("*This reconciliation reflects the issuer's disclosed methodology. See Section 2.4.2 for REALPAC-calculated reconciliation for cross-issuer comparability.*")

        return "\n".join(lines)
```

**Commit:**
```bash
git add scripts/calculate_credit_metrics/reconciliation.py
git commit -m "feat(reconciliation): add issuer-reported FFO/AFFO/ACFO reconciliation generators (v1.0.13)"
```

---

### Phase 4: Update Report Generation Script to Use New Functions (1 hour)

**Priority:** HIGH
**Effort:** Medium
**Risk:** Medium

**File:** `scripts/generate_final_report.py`

#### 4A: Import New Functions

**Add imports (near line 15):**
```python
from scripts.calculate_credit_metrics.reconciliation import (
    generate_ffo_affo_reconciliation,
    format_reconciliation_table,
    generate_acfo_reconciliation,
    format_acfo_reconciliation_table,
    generate_issuer_reported_ffo_affo_reconciliation,  # NEW
    format_issuer_reported_ffo_affo_reconciliation,    # NEW
    generate_issuer_reported_acfo_reconciliation,       # NEW
    format_issuer_reported_acfo_reconciliation          # NEW
)
```

#### 4B: Generate Issuer-Reported Tables

**Add after line 754 (after calculated table generation):**

```python
    try:
        # FFO/AFFO Reconciliation Table (CALCULATED - already exists)
        ffo_affo_recon_data = generate_ffo_affo_reconciliation(recon_data_source)
        ffo_affo_table = format_reconciliation_table(ffo_affo_recon_data) if ffo_affo_recon_data else "Insufficient data - FFO/AFFO reconciliation not available. Enable comprehensive Phase 2 extraction for detailed reconciliations."
    except Exception as e:
        ffo_affo_table = f"Error generating FFO/AFFO reconciliation: {str(e)}"

    try:
        # FFO/AFFO Reconciliation Table (ISSUER-REPORTED - NEW)
        ffo_affo_recon_reported = generate_issuer_reported_ffo_affo_reconciliation(phase2_data)
        ffo_affo_table_reported = format_issuer_reported_ffo_affo_reconciliation(ffo_affo_recon_reported)
    except Exception as e:
        ffo_affo_table_reported = f"Error generating issuer-reported FFO/AFFO reconciliation: {str(e)}"

    try:
        # ACFO Reconciliation Table (CALCULATED - already exists)
        acfo_recon_data = generate_acfo_reconciliation(recon_data_source)
        acfo_table = format_acfo_reconciliation_table(acfo_recon_data) if acfo_recon_data else "Insufficient data - ACFO reconciliation not available. Requires cash flow statement data in Phase 2 extraction."
    except Exception as e:
        acfo_table = f"Error generating ACFO reconciliation: {str(e)}"

    try:
        # ACFO Reconciliation Table (ISSUER-REPORTED - NEW)
        acfo_recon_reported = generate_issuer_reported_acfo_reconciliation(phase2_data)
        acfo_table_reported = format_issuer_reported_acfo_reconciliation(acfo_recon_reported)
    except Exception as e:
        acfo_table_reported = f"Error generating issuer-reported ACFO reconciliation: {str(e)}"
```

#### 4C: Add New Placeholders

**Add near line 1246 (in placeholders dict):**

```python
        # Reconciliation Tables (v1.0.13) - Dual-table support
        'FFO_AFFO_RECONCILIATION_TABLE_REPORTED': ffo_affo_table_reported,  # NEW
        'FFO_AFFO_RECONCILIATION_TABLE_CALCULATED': ffo_affo_table,         # RENAMED (was FFO_AFFO_RECONCILIATION_TABLE)
        'FFO_AFFO_RECONCILIATION_TABLE': ffo_affo_table,                    # KEEP for backward compat
        'FFO_AFFO_RECONCILIATION_TABLE_DETAILED': ffo_affo_table,           # Keep for Appendix F

        'ACFO_RECONCILIATION_TABLE_REPORTED': acfo_table_reported,          # NEW
        'ACFO_RECONCILIATION_TABLE_CALCULATED': acfo_table,                 # RENAMED (was ACFO_RECONCILIATION_TABLE)
        'ACFO_RECONCILIATION_TABLE': acfo_table,                            # KEEP for backward compat
        'ACFO_RECONCILIATION_TABLE_DETAILED': acfo_table,                   # Keep for Appendix F
```

**Commit:**
```bash
git add scripts/generate_final_report.py
git commit -m "feat(phase5): integrate issuer-reported reconciliation tables (v1.0.13)"
```

---

### Phase 5: Test with Artis REIT Data (30 minutes)

**Priority:** CRITICAL
**Effort:** Low
**Risk:** Low

**Steps:**

1. **Regenerate Artis REIT report:**
   ```bash
   python scripts/generate_final_report.py \
     Issuer_Reports/Artis_REIT/temp/phase3_calculated_metrics.json \
     Issuer_Reports/Artis_REIT/temp/phase4_credit_analysis.md
   ```

2. **Verify Section 2.2.2:**
   - Check line ~672: `IFRS Cash Flow from Operations: 28,640` ✓ (not "Not extracted")

3. **Verify Section 2.3:**
   - Check Section 2.3.1: Should show "Summary values only" table with FFO=34,491, AFFO=16,939
   - Check Section 2.3.2: Should show REALPAC-calculated reconciliation with FFO=4,034, AFFO=4,034

4. **Verify Section 2.4:**
   - Check Section 2.4.1: Should show "Not disclosed - Issuer does not report ACFO"
   - Check Section 2.4.2: Should show REALPAC-calculated ACFO=7,198 from CFO=28,640

**Expected Output Examples:**

**Section 2.3.1 (Artis - summary only):**
```markdown
## Issuer-Reported FFO/AFFO Summary

**Disclosure Type:** Summary values only (detailed reconciliation not disclosed)

| Metric | Amount (000s) | Per Unit |
|--------|---------------|----------|
| **FFO (Issuer-Reported)** | 34,491 | $0.3400 |
| **AFFO (Issuer-Reported)** | 16,939 | $0.1700 |

**Note:** Issuer does not disclose detailed FFO/AFFO reconciliation components. Only top-level values provided.

**Source:** MD&A - top-level FFO/AFFO disclosure

*For detailed reconciliation showing Net Income → FFO → AFFO adjustments, see Section 2.3.2 (REALPAC-Calculated Reconciliation).*
```

**Section 2.4.1 (Artis - not disclosed):**
```markdown
## Issuer-Reported ACFO Reconciliation

**Not disclosed** - Issuer does not report ACFO.

*Note: Most issuers (> 95%) do not report ACFO per REALPAC ACFO White Paper (January 2023). This is expected. All ACFO metrics calculated using REALPAC methodology (see Section 2.4.2).*
```

---

### Phase 6: Update Documentation (30 minutes)

**Priority:** MEDIUM
**Effort:** Low
**Risk:** Low

**Files to Update:**

1. **`CLAUDE.md`**: Update version to 1.0.13, add Phase 5 dual-table reconciliation notes
2. **`docs/PHASE5_REPORTED_VS_CALCULATED_IMPLEMENTATION.md`**: Document issuer-reported vs calculated separation
3. **`.claude/knowledge/SCHEMA_README.md`**: No changes needed (schema unchanged)

**Commit:**
```bash
git add CLAUDE.md docs/PHASE5_REPORTED_VS_CALCULATED_IMPLEMENTATION.md
git commit -m "docs: update v1.0.13 dual-table reconciliation documentation"
```

---

## Testing Strategy

### Unit Tests (NEW - recommended but optional)

**File:** `tests/test_issuer_reported_reconciliations.py`

Test cases:
1. **Test Case 1**: Issuer with summary-only FFO/AFFO (Artis example)
2. **Test Case 2**: Issuer with detailed FFO/AFFO reconciliation (synthetic data)
3. **Test Case 3**: Issuer with no ACFO (> 95% of cases)
4. **Test Case 4**: Issuer with ACFO summary value (rare)
5. **Test Case 5**: Issuer with detailed ACFO reconciliation (extremely rare)

### Integration Tests

1. **Regenerate all existing issuer reports** and verify no regressions
2. **Create synthetic test case** with detailed issuer-reported reconciliations
3. **Verify Phase 2 → Phase 3 → Phase 5 data flow** for reconciliation tables

---

## Rollback Plan

If issues arise during implementation:

1. **Phase 1 rollback**: Revert `scripts/generate_final_report.py:1356` to hardcoded "Not extracted"
2. **Phase 2 rollback**: Restore single-table template structure
3. **Phase 3 rollback**: Remove new reconciliation functions
4. **Full rollback**: `git revert <commit-hash>` for each phase

**Rollback triggers:**
- Generated reports fail validation
- Template placeholders not populated
- Phase 5 execution errors

---

## Success Criteria

### ✅ Completed (Issues 1-3)

**Issue 1 (CFO) - COMPLETED ✅**
- ✅ **Section 2.2.2 Line 672**: IFRS CFO now shows `28,640` (VERIFIED)

**Issues 2-3 (Dual Tables) - COMPLETED ✅**
- ✅ **Section 2.3.1**: Shows issuer-reported FFO/AFFO (VERIFIED)
- ✅ **Section 2.3.2**: Shows REALPAC-calculated FFO/AFFO reconciliation (VERIFIED)
- ✅ **Section 2.4.1**: Shows issuer-reported ACFO (VERIFIED)
- ✅ **Section 2.4.2**: Shows REALPAC-calculated ACFO reconciliation (VERIFIED)

### ⚠️ Remaining (Issue 5) - TO BE FIXED

**Issue 5 (ACFO/Per-Unit) - CRITICAL**
- ⚠️ **Section 2.2.2 Line 683**: Net Income per unit should show `-0.1242` (currently shows "N/A")
- ⚠️ **Section 2.2.2 Line 687**: ACFO should show `7,198` (currently shows "Not available")
- ⚠️ **Section 2.2.2 Line 687**: ACFO per unit should show `0.0741` (currently shows "Not available")
- ⚠️ **Section 2.2.2 Line 687**: ACFO payout ratio should show `404.9%` (currently shows "Not available%")
- ⚠️ **Section 2.5.2 Line 848**: ACFO Coverage should show `0.24x` (currently shows "N/Ax")
- ⚠️ **Section 2.5.2 Line 848**: ACFO payout should show `404.9%` (currently shows "Not available%")
- ⚠️ **Section 2.5.2 Line 848**: Coverage assessment should show "Insufficient" (currently shows "Not calculated")

### General Requirements
- ✅ **No regressions**: All other report sections unchanged (VERIFIED)
- ⚠️ **Artis REIT test**: Must regenerate successfully after Phase 1A+1B implementation

**Remaining Work:** Phase 1A + Phase 1B (45 minutes)

---

## Post-Implementation

1. **Version bump**: Update to v1.0.13 in all relevant files
2. **Regenerate test reports**: Artis REIT and any other test issuers
3. **Update changelog**: Document dual-table reconciliation feature
4. **Create GitHub issue**: Track future enhancements (e.g., variance tables comparing reported vs calculated)

---

## Estimated Timeline

### ✅ Completed Work (Issues 1-3)
| Phase | Effort | Duration | Status |
|-------|--------|----------|--------|
| Phase 1: CFO placeholder fix | Low | 15 min | ✅ **DONE** |
| Phase 2: Template restructuring | Medium | 30 min | ✅ **DONE** |
| Phase 3: Issuer reconciliation generators | High | 2 hours | ✅ **DONE** |
| Phase 4: Script integration | Medium | 1 hour | ✅ **DONE** |
| Phase 5: Testing with Artis (Issues 1-3) | Low | 30 min | ✅ **DONE** |
| Phase 6: Documentation | Low | 30 min | ✅ **DONE** |
| **Completed** | | **~4.75 hours** | ✅ |

### ⚠️ Remaining Work (Issue 5)
| Phase | Effort | Duration | Priority |
|-------|--------|----------|----------|
| **Phase 1A: Per-unit helper functions** | **Low** | **15 min** | **CRITICAL** |
| **Phase 1B: ACFO/CFO/per-unit placeholder fixes** | **Medium** | **30 min** | **CRITICAL** |
| Testing and verification | Low | 10 min | CRITICAL |
| **Remaining Total** | | **~45 min** | |

### 🔵 Optional Future Work (Issue 4)
| Phase | Effort | Duration | Priority |
|-------|--------|----------|----------|
| Phase 0: Camelot table extraction investigation | Medium | 1 hour | **OPTIONAL** |

**Note:**
- **Issues 1-3**: COMPLETED ✅ (~4.75 hours of work already done)
- **Issue 5**: REMAINING ⚠️ (~45 minutes of simple placeholder fixes)
- **Issue 4**: OPTIONAL 🔵 (future enhancement for improved table extraction)

---

## Notes

- **Priority**: This fix addresses a user requirement and improves report accuracy
- **Risk**: Medium - involves changes across template, reconciliation module, and report generation
- **Impact**: High - affects core credit analysis reporting for all issuers
- **Testing**: Critical - must verify with Artis REIT data before considering complete

---

**Implementation Status:** UPDATED (expanded to include Issue 5 - ACFO/per-unit calculations)
**Target Version:** v1.0.13
**Document Status:** UPDATED - 2025-10-20 (added Issue 5, revised Phase 1A+1B)

**Revision History:**
- **2025-10-20 Initial**: Documented Issues 1-4 (CFO placeholder, dual-table reconciliations, table extraction)
- **2025-10-20 Update**: Added Issue 5 (ACFO/per-unit calculations); revised Phase 1 into Phase 1A+1B; updated timeline and success criteria

**Change Summary (v2):**
- ✅ Added Issue 5 analysis (ACFO value and per-unit calculations not populating)
- ✅ Split Phase 1 into Phase 1A (helper functions) + Phase 1B (placeholder fixes)
- ✅ Expanded success criteria with specific line number checks
- ✅ Updated timeline (5.5 hours vs original 6 hours)
- ✅ Prioritized quick wins (Phase 1A+1B) over dual-table infrastructure (Phase 2-4)
