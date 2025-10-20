# Phase 5 Implementation Plan: Reported vs. Calculated Metrics

**Document Version:** 1.0
**Date:** 2025-10-20
**Pipeline Version:** 1.0.12 (planned)
**Author:** System Architecture Team

---

## Executive Summary

This document outlines the implementation plan for enhancing Phase 5 (Report Generation) to support dual-table reporting of **Issuer-Reported** vs. **REALPAC-Calculated** metrics across all FFO/AFFO/ACFO/AFCF sections.

**Objective:** Provide transparency on calculation methodology and enable variance analysis between issuer-disclosed values and standardized REALPAC calculations.

**Scope:** `/workspaces/issuer-credit-analysis/scripts/generate_final_report.py`

**Estimated Effort:** 14 hours (~2-3 days)

**Status:** Planning Complete - Ready for Implementation

---

## Table of Contents

1. [Overview](#overview)
2. [Code Structure Analysis](#code-structure-analysis)
3. [Helper Functions](#helper-functions)
4. [Placeholder Dictionary Updates](#placeholder-dictionary-updates)
5. [Implementation Sequence](#implementation-sequence)
6. [Testing Strategy](#testing-strategy)
7. [Rollback Strategy](#rollback-strategy)
8. [Documentation Updates](#documentation-updates)
9. [Success Criteria](#success-criteria)
10. [Risk Assessment](#risk-assessment)

---

## Overview

### Background

**Current State:**
- Template sections 2.2-2.7 have been updated with dual-table structure (reported vs. calculated)
- Phase 2 schema now captures `acfo` and `acfo_per_unit` (reported values)
- Phase 3 has `validate_acfo()` function for variance calculation
- Phase 5 script has ~107 missing placeholders for reported vs. calculated metrics

**Target State:**
- All 60-70 new placeholders populated
- Dual-table reconciliation tables functional
- Variance analysis working
- Zero unpopulated placeholders in final reports

### Affected Template Sections

| Section | Current | Target | New Placeholders |
|---------|---------|--------|------------------|
| 2.2 | Single table | 2.2.1 (Reported) + 2.2.2 (Calculated) | ~30 |
| 2.3 | Single column | Dual-column reconciliation | ~5 |
| 2.4 | Single column | Dual-column reconciliation | ~5 |
| 2.5 | Single table | 2.5.1 (Reported) + 2.5.2 (Calculated) | ~12 |
| 2.6 | Single values | 2.6.1 (Reported) + 2.6.2 (Calculated) + 2.6.3 (Gap) | ~15 |
| 2.7 | Single table | 2.7.1 (Reported) + 2.7.2 (Calculated) + 2.7.3 (Coverage) | ~10 |

**Total:** ~77 new placeholders

---

## Code Structure Analysis

### Current Script Organization

```python
generate_final_report.py (current ~1,200 lines)
├── Imports and setup (lines 1-30)
├── Helper functions (lines 31-100)
│   ├── format_number()
│   ├── format_currency()
│   ├── safe_get()
│   └── format_date()
├── Main function (lines 101-1200)
│   ├── Load Phase 2 data
│   ├── Load Phase 3 metrics
│   ├── Load Phase 4 analysis
│   ├── Build replacements dictionary
│   │   ├── Basic metadata (lines 200-250)
│   │   ├── Financial metrics (lines 251-400)
│   │   ├── FFO/AFFO placeholders (lines 401-600)
│   │   ├── ACFO placeholders (lines 601-700)
│   │   ├── AFCF placeholders (lines 701-800)
│   │   └── Coverage/analysis (lines 801-1000)
│   ├── Process template
│   └── Write output
```

### Implementation Strategy

**Approach:** Incremental enhancement with backward compatibility

1. **Add new helper functions** (lines 100-200) - calculation utilities
2. **Expand replacements dictionary** (insert at appropriate sections)
3. **Maintain existing placeholders** (rename with `_CALCULATED` suffix where needed)
4. **Add new placeholders** (reported metrics, variance, gap analysis)

**Key Principle:** Additive changes only - no breaking changes to existing functionality.

---

## Helper Functions

### Location

Insert after existing helper functions (~line 100)

### 1. Per-Unit Calculation

```python
def calculate_per_unit(amount, units_outstanding):
    """
    Calculate per-unit metric safely

    Args:
        amount (float): Dollar amount (000s)
        units_outstanding (float): Number of units (000s)

    Returns:
        float: Per-unit value (dollars), or None if invalid

    Examples:
        >>> calculate_per_unit(34500, 100000)
        0.35
        >>> calculate_per_unit(None, 100000)
        None
        >>> calculate_per_unit(34500, 0)
        None
    """
    if amount is None or units_outstanding is None or units_outstanding == 0:
        return None
    return round(amount / units_outstanding, 2)
```

**Lines:** ~15
**Test Cases:** None, 0, negative values
**Dependencies:** None

---

### 2. Payout Ratio Calculation

```python
def calculate_payout_ratio(metric_per_unit, distributions_per_unit):
    """
    Calculate payout ratio as percentage

    Args:
        metric_per_unit (float): FFO/AFFO/ACFO/AFCF per unit
        distributions_per_unit (float): Distributions per unit

    Returns:
        float: Payout ratio (percentage), or None if invalid

    Formula:
        payout_ratio = (distributions_per_unit / metric_per_unit) * 100

    Examples:
        >>> calculate_payout_ratio(0.35, 0.30)
        85.7
        >>> calculate_payout_ratio(0, 0.30)
        None
        >>> calculate_payout_ratio(None, 0.30)
        None
    """
    if metric_per_unit is None or metric_per_unit == 0:
        return None
    if distributions_per_unit is None:
        return None
    return round((distributions_per_unit / metric_per_unit) * 100, 1)
```

**Lines:** ~18
**Test Cases:** Zero metric, None values, edge cases (payout > 100%)
**Dependencies:** None

---

### 3. Coverage Ratio Calculation

```python
def calculate_coverage_ratio(metric, distributions):
    """
    Calculate coverage ratio (inverse of payout ratio)

    Args:
        metric (float): FFO/AFFO/ACFO/AFCF amount (000s)
        distributions (float): Total distributions amount (000s)

    Returns:
        float: Coverage ratio (x.xx), or None if invalid

    Formula:
        coverage_ratio = metric / distributions

    Examples:
        >>> calculate_coverage_ratio(34500, 30000)
        1.15
        >>> calculate_coverage_ratio(0, 30000)
        None
    """
    if metric is None or metric == 0 or distributions is None or distributions == 0:
        return None
    return round(metric / distributions, 2)
```

**Lines:** ~15
**Test Cases:** Zero values, None, negative amounts
**Dependencies:** None

---

### 4. Coverage Assessment

```python
def assess_coverage(coverage_ratio):
    """
    Assess coverage quality based on ratio

    Args:
        coverage_ratio (float): Coverage ratio (x.xx)

    Returns:
        str: Assessment (Strong/Adequate/Tight/Insufficient)

    Thresholds:
        >= 1.3x: Strong coverage
        >= 1.1x: Adequate coverage
        >= 1.0x: Tight coverage
        < 1.0x: Insufficient coverage

    Examples:
        >>> assess_coverage(1.5)
        'Strong coverage'
        >>> assess_coverage(0.95)
        'Insufficient coverage'
    """
    if coverage_ratio is None:
        return 'Not available'

    if coverage_ratio >= 1.3:
        return 'Strong coverage'
    elif coverage_ratio >= 1.1:
        return 'Adequate coverage'
    elif coverage_ratio >= 1.0:
        return 'Tight coverage'
    else:
        return 'Insufficient coverage'
```

**Lines:** ~20
**Test Cases:** Boundary values (1.0, 1.1, 1.3), None
**Dependencies:** None

---

### 5. Self-Funding Assessment

```python
def assess_self_funding(self_funding_ratio):
    """
    Assess self-funding capacity

    Args:
        self_funding_ratio (float): Self-funding ratio (AFCF / Net Financing Needs)

    Returns:
        str: Assessment of self-funding capability

    Thresholds:
        >= 1.0x: Self-funding
        >= 0.75x: Moderate reliance on external financing
        >= 0.5x: High reliance on external financing
        < 0.5x: Critical reliance on external financing

    Examples:
        >>> assess_self_funding(1.2)
        'Self-funding - no external financing required'
        >>> assess_self_funding(0.4)
        'Critical reliance on external financing'
    """
    if self_funding_ratio is None:
        return 'Not available'

    if self_funding_ratio >= 1.0:
        return 'Self-funding - no external financing required'
    elif self_funding_ratio >= 0.75:
        return 'Moderate reliance on external financing'
    elif self_funding_ratio >= 0.5:
        return 'High reliance on external financing'
    else:
        return 'Critical reliance on external financing'
```

**Lines:** ~20
**Test Cases:** Boundary values, None, negative ratios
**Dependencies:** None

---

### 6. Reported Adjustments List Generator

```python
def generate_reported_adjustments_list(ffo_affo_components):
    """
    Generate formatted list of top FFO→AFFO adjustments from reported components

    Args:
        ffo_affo_components (dict): Phase 2 extracted FFO/AFFO components

    Returns:
        str: Formatted markdown list of top 3-5 adjustments

    Example Output:
        - Sustaining CAPEX: ($8,752)
        - Leasing costs: ($10,800)
        - Tenant improvements: ($3,300)
    """
    if not ffo_affo_components:
        return 'Issuer does not disclose detailed adjustments'

    # Extract AFFO adjustments (V-Z)
    affo_adjustments = {
        'Sustaining CAPEX': ffo_affo_components.get('capex_sustaining', 0),
        'Leasing costs': ffo_affo_components.get('leasing_costs', 0),
        'Tenant improvements': ffo_affo_components.get('tenant_improvements', 0),
        'Straight-line rent': ffo_affo_components.get('straight_line_rent', 0),
    }

    # Sort by absolute value
    sorted_adjustments = sorted(
        [(k, v) for k, v in affo_adjustments.items() if v != 0],
        key=lambda x: abs(x[1]),
        reverse=True
    )

    # Format top 3-5
    lines = []
    for name, amount in sorted_adjustments[:5]:
        formatted_amount = f"({abs(amount):,.0f})" if amount < 0 else f"{amount:,.0f}"
        lines.append(f"- {name}: {formatted_amount}")

    return '\n'.join(lines) if lines else 'No material adjustments disclosed'
```

**Lines:** ~30
**Test Cases:** Empty dict, all zeros, negative values
**Dependencies:** Phase 2 `ffo_affo_components` structure

---

### Summary: Helper Functions

| Function | Lines | Complexity | Dependencies |
|----------|-------|------------|--------------|
| `calculate_per_unit()` | 15 | Low | None |
| `calculate_payout_ratio()` | 18 | Low | None |
| `calculate_coverage_ratio()` | 15 | Low | None |
| `assess_coverage()` | 20 | Low | None |
| `assess_self_funding()` | 20 | Low | None |
| `generate_reported_adjustments_list()` | 30 | Medium | Phase 2 data |
| **Total** | **118 lines** | **Low-Medium** | **Minimal** |

---

## Placeholder Dictionary Updates

### Section 2.2.1 - Issuer-Reported Metrics

**Location:** In main `replacements` dictionary (~line 200)

**Dependencies:**
- `phase2_data` - Loaded from Phase 2 JSON
- `phase2_data['ffo_affo']` - Reported metrics section

**Code:**

```python
# ========================================
# Section 2.2.1: Issuer-Reported Metrics
# ========================================

# Extract reported values from Phase 2
ffo_affo_reported = phase2_data.get('ffo_affo', {}) if phase2_data else {}
distributions_per_unit = ffo_affo_reported.get('distributions_per_unit', 0)

# FFO Reported
'FFO_REPORTED': format_number(ffo_affo_reported.get('ffo', 0)),
'FFO_PER_UNIT_REPORTED': format_currency(ffo_affo_reported.get('ffo_per_unit', 0)),
'FFO_PAYOUT_REPORTED': format_number(
    calculate_payout_ratio(
        ffo_affo_reported.get('ffo_per_unit'),
        distributions_per_unit
    ) or 0, 1
),

# AFFO Reported
'AFFO_REPORTED': format_number(ffo_affo_reported.get('affo', 0)),
'AFFO_PER_UNIT_REPORTED': format_currency(ffo_affo_reported.get('affo_per_unit', 0)),
'AFFO_PAYOUT_REPORTED': format_number(
    calculate_payout_ratio(
        ffo_affo_reported.get('affo_per_unit'),
        distributions_per_unit
    ) or 0, 1
),

# ACFO Reported (if available - rare)
acfo_reported = ffo_affo_reported.get('acfo')
'ACFO_REPORTED': format_number(acfo_reported) if acfo_reported else 'Not reported',
'ACFO_PER_UNIT_REPORTED': format_currency(
    ffo_affo_reported.get('acfo_per_unit', 0)
) if ffo_affo_reported.get('acfo_per_unit') else 'N/A',
'ACFO_PAYOUT_REPORTED': format_number(
    calculate_payout_ratio(
        ffo_affo_reported.get('acfo_per_unit'),
        distributions_per_unit
    ), 1
) if ffo_affo_reported.get('acfo_per_unit') else 'N/A',
```

**Placeholders Added:** 9
**Lines:** ~35
**Error Handling:** None/0 values → 'Not reported' or 'N/A'

---

### Section 2.2.2 - REALPAC-Calculated Metrics

**Location:** Immediately after 2.2.1 placeholders

**Dependencies:**
- `reit_metrics` - Calculated metrics from Phase 3
- `afcf_metrics` - AFCF calculations from Phase 3

**Code:**

```python
# ========================================
# Section 2.2.2: REALPAC-Calculated Metrics
# ========================================

# Get unit counts for per-unit calculations
common_units = reit_metrics.get('common_units_outstanding', 100000)  # Default for safety
diluted_units = reit_metrics.get('diluted_units_outstanding', common_units)

# FFO Calculated
ffo_calc = reit_metrics.get('ffo_calculated', 0)
'FFO_CALCULATED': format_number(ffo_calc),
'FFO_PER_UNIT_CALCULATED': format_currency(
    calculate_per_unit(ffo_calc, diluted_units) or 0
),
'FFO_PAYOUT_CALCULATED': format_number(
    calculate_payout_ratio(
        calculate_per_unit(ffo_calc, common_units),
        distributions_per_unit
    ) or 0, 1
),

# AFFO Calculated
affo_calc = reit_metrics.get('affo_calculated', 0)
'AFFO_CALCULATED': format_number(affo_calc),
'AFFO_PER_UNIT_CALCULATED': format_currency(
    calculate_per_unit(affo_calc, diluted_units) or 0
),
'AFFO_PAYOUT_CALCULATED': format_number(
    calculate_payout_ratio(
        calculate_per_unit(affo_calc, common_units),
        distributions_per_unit
    ) or 0, 1
),

# ACFO Calculated
acfo_calc = reit_metrics.get('acfo_calculated', 0)
'ACFO_CALCULATED': format_number(acfo_calc),
'ACFO_PER_UNIT_CALCULATED': format_currency(
    calculate_per_unit(acfo_calc, common_units) or 0
),
'ACFO_PAYOUT_CALCULATED': format_number(
    calculate_payout_ratio(
        calculate_per_unit(acfo_calc, common_units),
        distributions_per_unit
    ) or 0, 1
),

# AFCF Calculated
afcf_calc = afcf_metrics.get('afcf', 0)
'AFCF_CALCULATED': format_number(afcf_calc),
'AFCF_PER_UNIT_CALCULATED': format_currency(afcf_metrics.get('afcf_per_unit', 0)),
'AFCF_PAYOUT_CALCULATED': format_number(
    calculate_payout_ratio(
        afcf_metrics.get('afcf_per_unit'),
        distributions_per_unit
    ) or 0, 1
),
```

**Placeholders Added:** 12
**Lines:** ~45
**Error Handling:** Default to 0 for calculations, None-safe helpers

---

### Variance Placeholders

**Location:** After calculated metrics placeholders

**Dependencies:**
- `reit_metrics['validation']` - FFO/AFFO validation from Phase 3
- `reit_metrics['acfo_validation']` - ACFO validation from Phase 3

**Code:**

```python
# ========================================
# Variance Placeholders (Reported vs Calculated)
# ========================================

validation = reit_metrics.get('validation', {})
acfo_validation = reit_metrics.get('acfo_validation', {})

# FFO Variance
ffo_var_pct = validation.get('ffo_variance_percent')
'FFO_VARIANCE_PERCENT': format_number(ffo_var_pct, 1) if ffo_var_pct is not None else 'N/A',
'FFO_VALIDATION_STATUS': (
    f"✓ Validated: {ffo_var_pct:.1f}% variance"
    if validation.get('ffo_within_threshold')
    else f"⚠️ Exceeds threshold: {ffo_var_pct:.1f}% variance"
) if ffo_var_pct is not None else 'Not available',

# AFFO Variance
affo_var_pct = validation.get('affo_variance_percent')
'AFFO_VARIANCE_PERCENT': format_number(affo_var_pct, 1) if affo_var_pct is not None else 'N/A',
'AFFO_VALIDATION_STATUS': (
    f"✓ Validated: {affo_var_pct:.1f}% variance"
    if validation.get('affo_within_threshold')
    else f"⚠️ Exceeds threshold: {affo_var_pct:.1f}% variance"
) if affo_var_pct is not None else 'Not available',

# ACFO Variance
acfo_var_pct = acfo_validation.get('acfo_variance_percent')
'ACFO_VARIANCE_PERCENT': format_number(acfo_var_pct, 1) if acfo_var_pct is not None else 'N/A',
'ACFO_VALIDATION_STATUS': (
    f"✓ Validated: {acfo_var_pct:.1f}% variance"
    if acfo_validation.get('acfo_within_threshold')
    else f"⚠️ Exceeds threshold: {acfo_var_pct:.1f}% variance"
) if acfo_var_pct is not None else 'Not available - issuer does not report ACFO',
```

**Placeholders Added:** 6
**Lines:** ~25
**Error Handling:** Check for None, provide 'N/A' or 'Not available'

---

### Section 2.5 - Distribution Coverage (Reported)

**Location:** After variance placeholders

**Code:**

```python
# ========================================
# Section 2.5.1: Distribution Coverage (Reported)
# ========================================

# Calculate total distributions
distributions_total = distributions_per_unit * common_units if distributions_per_unit and common_units else 0

# FFO Coverage (Reported)
ffo_rep = ffo_affo_reported.get('ffo', 0)
ffo_cov_rep = calculate_coverage_ratio(ffo_rep, distributions_total)
'FFO_COVERAGE_REPORTED': format_number(ffo_cov_rep, 2) if ffo_cov_rep else 'N/A',
'FFO_COVERAGE_ASSESSMENT_REPORTED': assess_coverage(ffo_cov_rep),

# AFFO Coverage (Reported)
affo_rep = ffo_affo_reported.get('affo', 0)
affo_cov_rep = calculate_coverage_ratio(affo_rep, distributions_total)
'AFFO_COVERAGE_REPORTED': format_number(affo_cov_rep, 2) if affo_cov_rep else 'N/A',
'AFFO_COVERAGE_ASSESSMENT_REPORTED': assess_coverage(affo_cov_rep),

# ACFO Coverage (Reported - if available)
acfo_rep = ffo_affo_reported.get('acfo', 0)
acfo_cov_rep = calculate_coverage_ratio(acfo_rep, distributions_total) if acfo_rep else None
'ACFO_COVERAGE_REPORTED': format_number(acfo_cov_rep, 2) if acfo_cov_rep else 'N/A',
'ACFO_COVERAGE_ASSESSMENT_REPORTED': assess_coverage(acfo_cov_rep) if acfo_rep else 'Not reported',
```

**Placeholders Added:** 6
**Lines:** ~20
**Error Handling:** Handle ACFO not reported case

---

### Section 2.5 - Distribution Coverage (Calculated)

**Location:** After reported coverage placeholders

**Code:**

```python
# ========================================
# Section 2.5.2: Distribution Coverage (Calculated)
# ========================================

# Rename existing placeholders with _CALCULATED suffix
coverage_ratios = reit_metrics.get('coverage_ratios', {})

'FFO_COVERAGE_CALCULATED': format_number(coverage_ratios.get('ffo_coverage', 0), 2),
'AFFO_COVERAGE_CALCULATED': format_number(coverage_ratios.get('affo_coverage', 0), 2),
'ACFO_COVERAGE_CALCULATED': format_number(coverage_ratios.get('acfo_coverage', 0), 2),

# Assessments (use existing logic, based on calculated values)
'FFO_COVERAGE_ASSESSMENT': assess_coverage(coverage_ratios.get('ffo_coverage')),
'AFFO_COVERAGE_ASSESSMENT': assess_coverage(coverage_ratios.get('affo_coverage')),
'ACFO_COVERAGE_ASSESSMENT': assess_coverage(coverage_ratios.get('acfo_coverage')),
```

**Placeholders Added:** 3 (+ 3 renamed)
**Lines:** ~10
**Note:** Existing placeholders need `_CALCULATED` suffix

---

### Section 2.6 - Bridge Analysis (Reported)

**Location:** After coverage placeholders

**Code:**

```python
# ========================================
# Section 2.6.1: Bridge Analysis (Reported)
# ========================================

# FFO to AFFO Bridge (Reported)
ffo_to_affo_reduction_rep = ffo_rep - affo_rep if ffo_rep and affo_rep else 0
'FFO_TO_AFFO_REDUCTION_REPORTED': format_number(ffo_to_affo_reduction_rep),
'FFO_TO_AFFO_PERCENT_REPORTED': format_number(
    (ffo_to_affo_reduction_rep / ffo_rep * 100) if ffo_rep else 0, 1
),
'FFO_TO_AFFO_ADJUSTMENTS_REPORTED': generate_reported_adjustments_list(
    phase2_data.get('ffo_affo_components', {})
) if phase2_data and phase2_data.get('ffo_affo_components') else 'Issuer does not disclose detailed adjustments',

# CFO to ACFO (Reported - usually N/A)
'CFO_TO_ACFO_REDUCTION_REPORTED': 'N/A - issuer does not report ACFO',
'CFO_TO_ACFO_PERCENT_REPORTED': 'N/A',
```

**Placeholders Added:** 5
**Lines:** ~15
**Dependencies:** `generate_reported_adjustments_list()` helper

---

### Section 2.6 - Bridge Analysis (Calculated)

**Location:** After reported bridge placeholders

**Code:**

```python
# ========================================
# Section 2.6.2: Bridge Analysis (Calculated)
# ========================================

# Rename existing placeholders with _CALCULATED suffix
# (Assuming existing logic calculates these values)

'FFO_TO_AFFO_REDUCTION_CALCULATED': # existing FFO_TO_AFFO_REDUCTION logic
'FFO_TO_AFFO_PERCENT_CALCULATED': # existing FFO_TO_AFFO_PERCENT logic
'FFO_TO_AFFO_ADJUSTMENTS_CALCULATED': # existing FFO_TO_AFFO_ADJUSTMENTS logic

'CFO_TO_ACFO_REDUCTION_CALCULATED': # existing CFO_TO_ACFO_REDUCTION logic
'CFO_TO_ACFO_PERCENT_CALCULATED': # existing CFO_TO_ACFO_PERCENT logic
'CFO_TO_ACFO_ADJUSTMENTS_CALCULATED': # existing CFO_TO_ACFO_ADJUSTMENTS logic
```

**Placeholders Added:** 0 (6 renamed)
**Lines:** ~5 (renaming only)
**Note:** Preserve existing calculation logic

---

### Section 2.6.3 - AFFO vs ACFO Gap Analysis

**Location:** After bridge analysis placeholders

**Code:**

```python
# ========================================
# Section 2.6.3: AFFO vs ACFO Gap Analysis
# ========================================

# Gap Analysis (Reported)
affo_acfo_gap_rep = affo_rep - acfo_rep if affo_rep and acfo_rep else 0
'AFFO_ACFO_GAP_REPORTED': format_number(affo_acfo_gap_rep),
'AFFO_ACFO_GAP_PERCENT_REPORTED': format_number(
    (affo_acfo_gap_rep / affo_rep * 100) if affo_rep else 0, 1
),

# Gap Analysis (Calculated) - rename existing
affo_acfo_gap_calc = affo_calc - acfo_calc if affo_calc and acfo_calc else 0
'AFFO_ACFO_GAP_CALCULATED': format_number(affo_acfo_gap_calc),
'AFFO_ACFO_GAP_PERCENT_CALCULATED': format_number(
    (affo_acfo_gap_calc / affo_calc * 100) if affo_calc else 0, 1
),

# Gap Variance
'AFFO_ACFO_GAP_VARIANCE': format_number(
    affo_acfo_gap_calc - affo_acfo_gap_rep if affo_acfo_gap_calc and affo_acfo_gap_rep else 0
),
```

**Placeholders Added:** 5
**Lines:** ~15
**Dependencies:** Calculated and reported AFFO/ACFO values

---

### Section 2.7 - AFCF Analysis

**Location:** After gap analysis placeholders

**Code:**

```python
# ========================================
# Section 2.7: AFCF Analysis
# ========================================

# AFCF from Reported ACFO (if available)
net_cfi = phase2_data.get('cash_flow_investing', {}).get('total_cfi', 0) if phase2_data else 0
afcf_rep_based = acfo_rep + net_cfi if acfo_rep else None

'AFCF_REPORTED_BASED': format_number(afcf_rep_based) if afcf_rep_based else 'N/A - issuer does not report ACFO',
'AFCF_PER_UNIT_REPORTED_BASED': format_currency(
    calculate_per_unit(afcf_rep_based, common_units)
) if afcf_rep_based else 'N/A',

# AFCF Coverage Assessments
'AFCF_DEBT_SERVICE_ASSESSMENT': assess_coverage(
    afcf_metrics.get('afcf_debt_service_coverage')
),
'AFCF_DISTRIBUTION_ASSESSMENT': assess_coverage(
    afcf_metrics.get('afcf_distribution_coverage')
),
'AFCF_SELF_FUNDING_ASSESSMENT': assess_self_funding(
    afcf_metrics.get('afcf_self_funding_ratio')
),
```

**Placeholders Added:** 5
**Lines:** ~20
**Dependencies:** `assess_self_funding()` helper

---

### Summary: Placeholder Additions

| Section | Reported | Calculated | Variance/Other | Total |
|---------|----------|------------|----------------|-------|
| 2.2.1 & 2.2.2 | 9 | 12 | 6 | 27 |
| 2.5.1 & 2.5.2 | 6 | 3 | - | 9 |
| 2.6.1 & 2.6.2 & 2.6.3 | 5 | 0 (6 renamed) | 5 | 10 |
| 2.7 | 2 | 0 | 3 | 5 |
| **Total New** | **22** | **15** | **14** | **51** |
| **Total Renamed** | - | - | - | **6** |
| **Grand Total** | - | - | - | **57** |

**Estimated Lines:** ~230 lines of code additions

---

## Implementation Sequence

### Phase 1: Helper Functions

**Duration:** 2 hours
**Priority:** High (foundation for all other work)

**Tasks:**
1. Add `calculate_per_unit()` function
2. Add `calculate_payout_ratio()` function
3. Add `calculate_coverage_ratio()` function
4. Add `assess_coverage()` function
5. Add `assess_self_funding()` function
6. Add `generate_reported_adjustments_list()` function

**Testing:**
- Unit tests for each function
- Edge case testing (None, 0, negative values)
- Validate against manual calculations

**Deliverable:** 6 new helper functions (~120 lines)

---

### Phase 2: Reported Metrics

**Duration:** 3 hours
**Priority:** High

**Tasks:**
1. Add Section 2.2.1 placeholders (FFO/AFFO/ACFO reported)
2. Add Section 2.5.1 placeholders (reported coverage)
3. Add Section 2.6.1 placeholders (reported bridge)
4. Add Section 2.7.1 placeholders (reported AFCF)

**Testing:**
- Run with Artis REIT data (has reported FFO/AFFO, no ACFO)
- Verify 'Not reported' handling for ACFO
- Check formatting consistency

**Deliverable:** ~22 new placeholders (~70 lines)

---

### Phase 3: Calculated Metrics

**Duration:** 2 hours
**Priority:** Medium

**Tasks:**
1. Rename existing placeholders with `_CALCULATED` suffix
2. Add Section 2.2.2 placeholders (calculated metrics)
3. Add Section 2.5.2 placeholders (calculated coverage)
4. Add Section 2.6.2 placeholders (calculated bridge - rename)
5. Add Section 2.7.2 placeholders (calculated AFCF)

**Testing:**
- Run with Artis REIT data
- Verify calculations match Phase 3 output
- Check per-unit calculations

**Deliverable:** ~15 new + 6 renamed placeholders (~60 lines)

---

### Phase 4: Variance & Gap Analysis

**Duration:** 2 hours
**Priority:** Medium

**Tasks:**
1. Add variance placeholders (FFO/AFFO/ACFO)
2. Add validation status formatting
3. Add gap analysis placeholders
4. Add gap variance calculation

**Testing:**
- Verify variance calculations
- Check threshold logic (✓ vs ⚠️)
- Test with synthetic data (high variance)

**Deliverable:** ~14 new placeholders (~40 lines)

---

### Phase 5: Integration Testing

**Duration:** 4 hours
**Priority:** Critical

**Tasks:**
1. Run full pipeline with Artis REIT
2. Run with Dream Industrial REIT
3. Verify all placeholders populated
4. Check table formatting
5. Validate calculations against source data
6. Performance testing

**Testing:**
- Zero unpopulated placeholders
- Calculations accurate to 2 decimal places
- Report generation < 2 seconds
- No regressions in existing sections

**Deliverable:** Fully functional dual-table reporting

---

### Phase 6: Documentation

**Duration:** 1 hour
**Priority:** Medium

**Tasks:**
1. Update code comments
2. Add docstrings for new functions
3. Update CLAUDE.md with new placeholders
4. Document reported vs. calculated distinction

**Deliverable:** Complete inline and external documentation

---

### Timeline Summary

| Phase | Duration | Cumulative | Dependencies |
|-------|----------|------------|--------------|
| 1. Helper Functions | 2h | 2h | None |
| 2. Reported Metrics | 3h | 5h | Phase 1 |
| 3. Calculated Metrics | 2h | 7h | Phase 1, 2 |
| 4. Variance & Gap | 2h | 9h | Phase 1, 2, 3 |
| 5. Integration Testing | 4h | 13h | Phase 1-4 |
| 6. Documentation | 1h | 14h | Phase 1-5 |
| **Total** | **14h** | **~2-3 days** | - |

---

## Testing Strategy

### Test Data Sets

**1. Artis REIT (Primary Test Case)**
- ✅ Reports FFO/AFFO
- ❌ Does not report ACFO
- Use Case: Typical issuer behavior

**2. Dream Industrial REIT (Secondary Test Case)**
- ✅ Reports FFO/AFFO
- ❌ Does not report ACFO
- Use Case: Different disclosure pattern

**3. Synthetic Test Case (Edge Case)**
- ✅ Reports all metrics (FFO/AFFO/ACFO)
- Use Case: Test full dual-table functionality

### Test Cases

#### TC1: All Metrics Reported (Synthetic)

```python
assert placeholders['FFO_REPORTED'] != 'Not reported'
assert placeholders['FFO_CALCULATED'] is not None
assert placeholders['FFO_VARIANCE_PERCENT'] is not None
assert placeholders['FFO_VALIDATION_STATUS'] contains '✓' or '⚠️'

assert placeholders['AFFO_REPORTED'] != 'Not reported'
assert placeholders['ACFO_REPORTED'] != 'Not reported'  # Edge case
```

**Expected:** All tables fully populated, variance shown

---

#### TC2: ACFO Not Reported (Artis REIT)

```python
assert placeholders['ACFO_REPORTED'] == 'Not reported'
assert placeholders['ACFO_PER_UNIT_REPORTED'] == 'N/A'
assert placeholders['ACFO_PAYOUT_REPORTED'] == 'N/A'
assert placeholders['ACFO_CALCULATED'] is not None
assert placeholders['ACFO_VARIANCE_PERCENT'] == 'N/A'
assert placeholders['ACFO_VALIDATION_STATUS'] == 'Not available - issuer does not report ACFO'
```

**Expected:** Reported table shows 'Not reported', calculated table populates normally

---

#### TC3: Payout Ratio Consistency

```python
# Test FFO
ffo_payout_reported = placeholders['FFO_PAYOUT_REPORTED']
ffo_reported = phase2_data['ffo_affo']['ffo']
distributions_total = phase2_data['ffo_affo']['distributions_per_unit'] * common_units

expected_payout = (distributions_total / ffo_reported) * 100
assert abs(ffo_payout_reported - expected_payout) < 0.1  # Within 0.1%

# Same for calculated
ffo_payout_calculated = placeholders['FFO_PAYOUT_CALCULATED']
ffo_calculated = reit_metrics['ffo_calculated']
expected_payout_calc = (distributions_total / ffo_calculated) * 100
assert abs(ffo_payout_calculated - expected_payout_calc) < 0.1
```

**Expected:** Payout ratios accurate to 0.1%

---

#### TC4: Coverage = Inverse of Payout

```python
ffo_coverage = placeholders['FFO_COVERAGE_CALCULATED']
ffo_payout = placeholders['FFO_PAYOUT_CALCULATED']

expected_coverage = 100 / ffo_payout  # Inverse relationship
assert abs(ffo_coverage - expected_coverage) < 0.01  # Within 0.01x
```

**Expected:** Coverage ratio = 1 / (payout_ratio / 100)

---

#### TC5: Variance Calculation

```python
ffo_reported = float(placeholders['FFO_REPORTED'].replace(',', ''))
ffo_calculated = float(placeholders['FFO_CALCULATED'].replace(',', ''))
ffo_variance_pct = placeholders['FFO_VARIANCE_PERCENT']

expected_variance = ((ffo_calculated - ffo_reported) / ffo_reported) * 100
assert abs(float(ffo_variance_pct) - expected_variance) < 0.1  # Within 0.1%
```

**Expected:** Variance percentage accurate to 0.1%

---

#### TC6: Performance Regression

```python
import time

start = time.time()
# Run generate_final_report.py
elapsed = time.time() - start

assert elapsed < 2.0  # Must complete in < 2 seconds
```

**Expected:** No performance degradation from new placeholders

---

#### TC7: Zero Unpopulated Placeholders

```python
with open(output_report, 'r') as f:
    content = f.read()

# Check for any remaining Handlebars placeholders
unpopulated = re.findall(r'\{\{([A-Z_]+)\}\}', content)

# Exclude conditional placeholders (Handlebars #if/#each)
unpopulated = [p for p in unpopulated if not p.startswith('#') and not p == '/']

assert len(unpopulated) == 0, f"Unpopulated placeholders: {unpopulated}"
```

**Expected:** Zero unpopulated placeholders in final report

---

### Testing Checklist

- [ ] All helper functions have unit tests
- [ ] Edge cases tested (None, 0, negative)
- [ ] Artis REIT generates without errors
- [ ] Dream Industrial REIT generates without errors
- [ ] Synthetic test case generates without errors
- [ ] All placeholders populated
- [ ] Variance calculations validated
- [ ] Performance < 2 seconds
- [ ] No regressions in existing sections
- [ ] Documentation updated

---

## Rollback Strategy

### Pre-Implementation

**1. Create Git Branch**
```bash
git checkout -b feature/reported-vs-calculated-metrics
git commit -m "Pre-implementation: Phase 5 reported vs calculated metrics"
```

**2. Create Backup**
```bash
cp scripts/generate_final_report.py scripts/generate_final_report.py.backup
```

### During Implementation

**Incremental Commits:**
```bash
# After Phase 1
git add scripts/generate_final_report.py
git commit -m "Phase 1: Add helper functions for per-unit/payout/coverage calculations"

# After Phase 2
git commit -m "Phase 2: Add reported metrics placeholders (Sections 2.2.1, 2.5.1, 2.6.1, 2.7.1)"

# After Phase 3
git commit -m "Phase 3: Add calculated metrics placeholders (Sections 2.2.2, 2.5.2, 2.6.2, 2.7.2)"

# After Phase 4
git commit -m "Phase 4: Add variance and gap analysis placeholders"

# After Phase 5
git commit -m "Phase 5: Integration testing complete - all placeholders functional"
```

### Rollback Procedure

**If Critical Issue Found:**

```bash
# Option 1: Revert specific commit
git log --oneline  # Find problematic commit
git revert <commit-hash>

# Option 2: Reset to pre-implementation
git reset --hard origin/main

# Option 3: Restore from backup
cp scripts/generate_final_report.py.backup scripts/generate_final_report.py
```

### Compatibility Assurance

**Template Backward Compatibility:**
- Old placeholders still work (existing `FFO`, `AFFO`, etc.)
- New placeholders additive only
- No breaking changes to existing functionality

**Graceful Degradation:**
- Missing reported values → 'Not reported' or 'N/A'
- Division by zero → None (handled by helpers)
- Missing Phase 3 data → Defaults to 0 with warning

---

## Documentation Updates

### 1. Code Comments

**Add inline documentation for:**
- Each new helper function (docstrings)
- Placeholder calculation logic (inline comments)
- Complex calculations (multi-line comments)

**Example:**
```python
# Section 2.2.1: Issuer-Reported Metrics
# These placeholders populate the "Reported" table showing values as disclosed
# by the issuer in their MD&A. If the issuer does not report a metric (common
# for ACFO), we show 'Not reported' to distinguish from zero.
```

---

### 2. CLAUDE.md Updates

**Add Section:**

```markdown
## Reported vs. Calculated Metrics (v1.0.12)

Phase 5 now supports dual-table reporting to distinguish between:
- **Issuer-Reported Metrics:** As disclosed in MD&A (may use non-REALPAC methodology)
- **REALPAC-Calculated Metrics:** Standardized calculations for cross-issuer comparability

### New Placeholders:

**Reported Metrics:**
- FFO_REPORTED, FFO_PER_UNIT_REPORTED, FFO_PAYOUT_REPORTED
- AFFO_REPORTED, AFFO_PER_UNIT_REPORTED, AFFO_PAYOUT_REPORTED
- ACFO_REPORTED, ACFO_PER_UNIT_REPORTED, ACFO_PAYOUT_REPORTED

**Calculated Metrics:**
- FFO_CALCULATED, FFO_PER_UNIT_CALCULATED, FFO_PAYOUT_CALCULATED
- AFFO_CALCULATED, AFFO_PER_UNIT_CALCULATED, AFFO_PAYOUT_CALCULATED
- ACFO_CALCULATED, ACFO_PER_UNIT_CALCULATED, ACFO_PAYOUT_CALCULATED
- AFCF_CALCULATED, AFCF_PER_UNIT_CALCULATED, AFCF_PAYOUT_CALCULATED

**Variance:**
- FFO_VARIANCE_PERCENT, FFO_VALIDATION_STATUS
- AFFO_VARIANCE_PERCENT, AFFO_VALIDATION_STATUS
- ACFO_VARIANCE_PERCENT, ACFO_VALIDATION_STATUS
```

---

### 3. PIPELINE_QUICK_REFERENCE.md

**Add Section:**

```markdown
## Phase 5: Reported vs. Calculated Metrics

**Dual-Table Reporting:**
Phase 5 generates separate tables for reported and calculated metrics.

**When to Use Each:**
- **Reported:** Show what issuer actually disclosed (transparency)
- **Calculated:** Show standardized REALPAC values (comparability)
- **Variance:** Highlight methodology differences

**Typical Variance Causes:**
- Non-REALPAC adjustments
- Different CAPEX/leasing cost treatments
- Timing differences
- Adjustment classification differences
```

---

### 4. Inline Docstrings

**Example:**

```python
def calculate_payout_ratio(metric_per_unit, distributions_per_unit):
    """
    Calculate payout ratio as percentage

    The payout ratio measures what percentage of a metric (FFO/AFFO/ACFO/AFCF)
    is distributed to unitholders. A ratio > 100% indicates distributions
    exceed the metric (unsustainable).

    Args:
        metric_per_unit (float): FFO/AFFO/ACFO/AFCF per unit (dollars)
        distributions_per_unit (float): Distributions per unit (dollars)

    Returns:
        float: Payout ratio (percentage, e.g., 85.7 for 85.7%), or None if invalid

    Formula:
        payout_ratio = (distributions_per_unit / metric_per_unit) * 100

    Examples:
        >>> calculate_payout_ratio(0.35, 0.30)
        85.7
        >>> calculate_payout_ratio(0.20, 0.30)  # Distributions > metric
        150.0
        >>> calculate_payout_ratio(0, 0.30)  # Invalid: division by zero
        None

    Edge Cases:
        - Returns None if metric_per_unit is 0 or None (division by zero)
        - Returns None if distributions_per_unit is None
        - Handles payout ratios > 100% (distributions exceed metric)

    See Also:
        - calculate_coverage_ratio(): Inverse relationship (coverage = 1 / payout)
    """
```

---

## Success Criteria

### Definition of Done

**Functional Requirements:**
- [ ] All 57 new placeholders implemented
- [ ] All 6 helper functions added and tested
- [ ] Artis REIT report generates without errors
- [ ] Dream Industrial REIT report generates without errors
- [ ] Synthetic test case (all metrics reported) passes
- [ ] Zero unpopulated placeholders in output
- [ ] Variance calculations validated against manual calculations

**Quality Requirements:**
- [ ] Code coverage ≥ 80% for new functions
- [ ] All helper functions have docstrings
- [ ] Inline comments for complex calculations
- [ ] No linting errors or warnings
- [ ] Consistent formatting (PEP 8)

**Performance Requirements:**
- [ ] Phase 5 completes in < 2 seconds
- [ ] No memory leaks or resource issues
- [ ] No performance regression vs. baseline

**Documentation Requirements:**
- [ ] CLAUDE.md updated with new placeholders
- [ ] PIPELINE_QUICK_REFERENCE.md updated
- [ ] Implementation plan saved to docs/
- [ ] Code comments comprehensive

---

## Risk Assessment

### Risk Matrix

| Risk | Likelihood | Impact | Severity | Mitigation |
|------|------------|--------|----------|------------|
| Missing edge cases in calculations | Medium | High | **HIGH** | Comprehensive unit tests, defensive coding |
| Performance degradation | Low | Medium | **LOW** | Profile before/after, optimize if needed |
| Schema incompatibility | Low | High | **MEDIUM** | Additive changes only, backward compatibility |
| Placeholder naming conflicts | Low | Medium | **LOW** | Grep for existing placeholders before adding |
| Division by zero errors | Medium | High | **HIGH** | None-safe helper functions, defensive checks |
| Data type mismatches | Low | Medium | **LOW** | Type validation in helpers |
| Missing Phase 3 validation data | Medium | Medium | **MEDIUM** | Graceful degradation, default to 'N/A' |

### Mitigation Strategies

**1. Division by Zero:**
```python
# Always check denominator before division
if denominator is None or denominator == 0:
    return None
return numerator / denominator
```

**2. Missing Data:**
```python
# Provide meaningful defaults
value = data.get('field', 'Not reported')  # Not 0 or None
```

**3. Type Safety:**
```python
# Validate types in helpers
if not isinstance(amount, (int, float)) or amount is None:
    return None
```

**4. Performance:**
```python
# Cache expensive calculations
distributions_total = cache.get('distributions_total') or calculate_total()
cache['distributions_total'] = distributions_total
```

---

## Appendix A: Placeholder Reference

### Complete List of New Placeholders

#### Reported Metrics (Section 2.2.1)
1. `FFO_REPORTED`
2. `FFO_PER_UNIT_REPORTED`
3. `FFO_PAYOUT_REPORTED`
4. `AFFO_REPORTED`
5. `AFFO_PER_UNIT_REPORTED`
6. `AFFO_PAYOUT_REPORTED`
7. `ACFO_REPORTED`
8. `ACFO_PER_UNIT_REPORTED`
9. `ACFO_PAYOUT_REPORTED`

#### Calculated Metrics (Section 2.2.2)
10. `FFO_CALCULATED`
11. `FFO_PER_UNIT_CALCULATED`
12. `FFO_PAYOUT_CALCULATED`
13. `AFFO_CALCULATED`
14. `AFFO_PER_UNIT_CALCULATED`
15. `AFFO_PAYOUT_CALCULATED`
16. `ACFO_CALCULATED`
17. `ACFO_PER_UNIT_CALCULATED`
18. `ACFO_PAYOUT_CALCULATED`
19. `AFCF_CALCULATED`
20. `AFCF_PER_UNIT_CALCULATED`
21. `AFCF_PAYOUT_CALCULATED`

#### Variance (Section 2.2)
22. `FFO_VARIANCE_PERCENT`
23. `FFO_VALIDATION_STATUS`
24. `AFFO_VARIANCE_PERCENT`
25. `AFFO_VALIDATION_STATUS`
26. `ACFO_VARIANCE_PERCENT`
27. `ACFO_VALIDATION_STATUS`

#### Distribution Coverage - Reported (Section 2.5.1)
28. `FFO_COVERAGE_REPORTED`
29. `FFO_COVERAGE_ASSESSMENT_REPORTED`
30. `AFFO_COVERAGE_REPORTED`
31. `AFFO_COVERAGE_ASSESSMENT_REPORTED`
32. `ACFO_COVERAGE_REPORTED`
33. `ACFO_COVERAGE_ASSESSMENT_REPORTED`

#### Distribution Coverage - Calculated (Section 2.5.2)
34. `FFO_COVERAGE_CALCULATED` (renamed from `FFO_COVERAGE`)
35. `AFFO_COVERAGE_CALCULATED` (renamed from `AFFO_COVERAGE`)
36. `ACFO_COVERAGE_CALCULATED` (renamed from `ACFO_COVERAGE`)

#### Bridge Analysis - Reported (Section 2.6.1)
37. `FFO_TO_AFFO_REDUCTION_REPORTED`
38. `FFO_TO_AFFO_PERCENT_REPORTED`
39. `FFO_TO_AFFO_ADJUSTMENTS_REPORTED`
40. `CFO_TO_ACFO_REDUCTION_REPORTED`
41. `CFO_TO_ACFO_PERCENT_REPORTED`

#### Bridge Analysis - Calculated (Section 2.6.2)
42. `FFO_TO_AFFO_REDUCTION_CALCULATED` (renamed)
43. `FFO_TO_AFFO_PERCENT_CALCULATED` (renamed)
44. `FFO_TO_AFFO_ADJUSTMENTS_CALCULATED` (renamed)
45. `CFO_TO_ACFO_REDUCTION_CALCULATED` (renamed)
46. `CFO_TO_ACFO_PERCENT_CALCULATED` (renamed)
47. `CFO_TO_ACFO_ADJUSTMENTS_CALCULATED` (renamed)

#### Gap Analysis (Section 2.6.3)
48. `AFFO_ACFO_GAP_REPORTED`
49. `AFFO_ACFO_GAP_PERCENT_REPORTED`
50. `AFFO_ACFO_GAP_CALCULATED` (renamed)
51. `AFFO_ACFO_GAP_PERCENT_CALCULATED` (renamed)
52. `AFFO_ACFO_GAP_VARIANCE`

#### AFCF Analysis (Section 2.7)
53. `AFCF_REPORTED_BASED`
54. `AFCF_PER_UNIT_REPORTED_BASED`
55. `AFCF_DEBT_SERVICE_ASSESSMENT`
56. `AFCF_DISTRIBUTION_ASSESSMENT`
57. `AFCF_SELF_FUNDING_ASSESSMENT`

**Total:** 57 placeholders (51 new + 6 renamed)

---

## Appendix B: Estimated Line Counts

| Component | Lines | Complexity |
|-----------|-------|------------|
| Helper Functions | 118 | Low-Medium |
| Section 2.2.1 (Reported) | 35 | Low |
| Section 2.2.2 (Calculated) | 45 | Low |
| Variance Placeholders | 25 | Low |
| Section 2.5.1 (Coverage - Reported) | 20 | Low |
| Section 2.5.2 (Coverage - Calculated) | 10 | Low |
| Section 2.6.1 (Bridge - Reported) | 15 | Low |
| Section 2.6.2 (Bridge - Calculated) | 5 | Low |
| Section 2.6.3 (Gap Analysis) | 15 | Low |
| Section 2.7 (AFCF) | 20 | Low |
| **Total Code** | **~308 lines** | **Low** |
| Documentation | 50 | Low |
| Unit Tests | 100 | Medium |
| **Grand Total** | **~458 lines** | **Low-Medium** |

---

## Appendix C: Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-20 | Initial implementation plan created |

---

**End of Implementation Plan**

**Next Steps:**
1. Review and approve this plan
2. Create feature branch: `feature/reported-vs-calculated-metrics`
3. Begin Phase 1: Helper Functions
4. Execute phases sequentially with testing at each stage
5. Final integration testing and documentation
6. Merge to main branch
