# Phase 2 JSON Schema Comprehensive Review
**Date:** 2025-11-01
**Reviewer:** Claude Code
**Schema Version:** Current (no version tracking)

## Executive Summary

Comprehensive review of `.claude/knowledge/phase2_extraction_schema.json` identified **20 major deficiencies** that create confusion, inconsistency, and maintenance challenges. The most critical issue is the lack of explicit separation between **issuer-reported** and **REALPAC-calculated** values, which directly caused the Section 2.5.1 coverage ratio bug (Issue #58).

## Critical Issues (Immediate Fix Required)

### 1. **Issuer-Reported vs Calculated Not Distinguished** ⚠️ CRITICAL
**Problem:**
FFO/AFFO/ACFO metrics, coverage ratios, and payout ratios don't distinguish between issuer-reported and REALPAC-calculated values at the schema level.

**Current State:**
```json
"ffo_affo": {
  "ffo": 34491,                    // Issuer-reported (from MD&A table)
  "affo": 16939,                   // Issuer-reported
  "ffo_per_unit": 0.17,            // Issuer-reported
  "affo_per_unit": 0.08,           // Issuer-reported
  "ytd_2025": {
    "ffo_payout_ratio": 88.2,      // Issuer-reported
    "affo_payout_ratio": 176.5     // Issuer-reported
    // No coverage_ratio field at all!
  }
}
```

**What's Missing:**
- No `ffo_calculated`, `affo_calculated` fields
- No `coverage_ratio` fields (issuer vs calculated)
- Phase 3 writes calculated values back but they overwrite or mix with reported
- Section 2.5.1 vs 2.5.2 distinction impossible to maintain

**Impact:**
- Section 2.5.1 shows totals but calculates coverage from per-unit (Issue #58)
- Validation tables can't compare issuer vs calculated properly
- Phase 5 report generator has to reverse-engineer which values are which

**Proposed Solution:**
```json
"ffo_affo": {
  "issuer_reported": {
    "ffo": 34491,
    "affo": 16939,
    "ffo_per_unit_basic": 0.35,
    "ffo_per_unit_diluted": 0.34,
    "affo_per_unit_basic": 0.17,
    "affo_per_unit_diluted": 0.17,
    "acfo": null,                  // Often not reported
    "acfo_per_unit": null,
    "ffo_coverage_ratio": 1.92,    // NEW: explicit coverage
    "affo_coverage_ratio": 0.95,   // NEW: explicit coverage
    "ffo_payout_ratio": 88.2,
    "affo_payout_ratio": 187.5
  },
  "realpac_calculated": {
    "ffo": -3815,                  // Phase 3 calculates from components
    "affo": -3751,
    "acfo": -7127,                 // Always calculated
    "afcf": -24021,                // Always calculated
    "ffo_per_unit_diluted": -0.038,
    "affo_per_unit_diluted": -0.0374,
    "acfo_per_unit_diluted": -0.0711,
    "afcf_per_unit": -0.2421,
    "ffo_coverage_ratio": null,    // N/A for negative
    "affo_coverage_ratio": null,   // N/A for negative
    "acfo_coverage_ratio": null,
    "afcf_coverage_ratio": null,
    "ffo_payout_ratio": null,
    "affo_payout_ratio": null,
    "acfo_payout_ratio": null,
    "afcf_payout_ratio": null
  },
  "validation": {
    "ffo_variance_amount": -38306,
    "ffo_variance_percent": -122.5,
    "affo_variance_amount": -20690,
    "affo_variance_percent": -145.7
  }
}
```

---

### 2. **Coverage & Payout Ratios Missing from Schema** ⚠️ CRITICAL
**Problem:**
`ffo_payout_ratio`, `affo_payout_ratio`, `coverage_ratio` appear in actual JSON data but are NOT in schema.

**Evidence:**
```bash
$ jq '.ffo_affo.ytd_2025 | keys' phase2_extracted_data.json
[
  "affo",
  "affo_payout_ratio",      # NOT IN SCHEMA
  "affo_per_unit_basic",
  "affo_per_unit_diluted",
  "distributions_per_unit",
  "ffo",
  "ffo_payout_ratio",       # NOT IN SCHEMA
  "ffo_per_unit_basic",
  "ffo_per_unit_diluted"
]
```

**Impact:**
- Schema validation tools would fail
- No type checking, no required field enforcement
- Phase 2 extraction can put any ratios anywhere with no consistency

**Solution:**
Add explicit schema for all ratio fields in both `issuer_reported` and `realpac_calculated` subsections.

---

### 3. **Period Inconsistency & Ambiguity** ⚠️ HIGH
**Problem:**
Top-level fields say "most recent period" but don't specify which (Q2? YTD? H1? Annual?).

**Current State:**
```json
"ffo": {
  "type": "number",
  "description": "REQUIRED: Funds From Operations (most recent period, e.g., Q2)"
}
```

**Issues:**
- What if most recent period is YTD? Or H1? Or Annual?
- `q2_2025`, `ytd_2025` are optional with no schema
- Which period should be used for coverage ratio calculations?
- Balance sheet is point-in-time, income/FFO are period-based - mismatch

**Current Workaround:**
- Phase 5 tries to use YTD if available: `ytd_distributions = phase2_data.get('ffo_affo', {}).get('ytd_2025', {}).get('distributions_per_unit')`
- Falls back to quarterly if YTD missing
- No schema guidance on which to prefer

**Solution:**
Add explicit `period_type` field and standardize period structure.

---

### 4. **Units Not Consistently Specified** ⚠️ HIGH
**Problem:**
Some fields specify units (e.g., "thousands"), others don't.

**Examples:**
- ✅ `total_assets (thousands)` - clear
- ❌ `ffo` - is this thousands? millions?
- ❌ `noi` - unstated
- ✅ `occupancy_rate (decimal, e.g., 0.878 for 87.8%)` - clear
- ❌ `ffo_payout_ratio` - is this decimal or percentage?

**Current Practice:**
- Financial totals are thousands (based on template `({{CURRENCY}} 000s)`)
- Ratios are percentages (e.g., 88.2 not 0.882)
- But this is NOT in schema

**Impact:**
- Phase 2 extraction may use different units
- Phase 3 calculations assume thousands but no validation
- International issuers may report in millions

**Solution:**
Add top-level `financial_units` field (e.g., "thousands", "millions") and document ratio format.

---

### 5. **Duplicate/Overlapping Fields** ⚠️ MEDIUM
**Problem:**
Multiple fields represent the same data without clear precedence.

| Field 1 | Field 2 | Issue |
|---------|---------|-------|
| `balance_sheet.cash` | `liquidity.cash_and_equivalents` | Should match but duplicated |
| `balance_sheet.common_units_outstanding` | `dilution_detail.basic_units` | Conceptually same |
| `ffo_affo_components.capex_sustaining` | `acfo_components.capex_sustaining_acfo` | MUST match per REALPAC |
| `ffo_affo_components.tenant_improvements` | `acfo_components.tenant_improvements_acfo` | MUST match per REALPAC |

**Current Solution:**
- Manual validation in Phase 3: check if they match
- If mismatch, which is authoritative?

**Better Solution:**
- Single source of truth for each value
- References/pointers where needed instead of duplication
- Or explicit "primary" vs "reconciliation" fields

---

### 6. **Nested Period Objects Have No Schema** ⚠️ MEDIUM
**Problem:**
Period objects like `q2_2025`, `ytd_2025` defined as empty `"type": "object"`.

**Current:**
```json
"q2_2025": {
  "type": "object",
  "description": "Optional: Detailed Q2 2025 FFO/AFFO metrics"
},
"ytd_2025": {
  "type": "object",
  "description": "Optional: YTD 2025 FFO/AFFO metrics"
}
```

**What Phase 2 Actually Puts There:**
```json
"ytd_2025": {
  "ffo": 34491,
  "affo": 16939,
  "ffo_per_unit_basic": 0.35,
  "ffo_per_unit_diluted": 0.34,
  "affo_per_unit_basic": 0.17,
  "affo_per_unit_diluted": 0.17,
  "distributions_per_unit": 0.30,
  "ffo_payout_ratio": 88.2,     // Not in schema!
  "affo_payout_ratio": 176.5    // Not in schema!
}
```

**Impact:**
- No validation of period structure
- Can't enforce required fields per period
- Different REITs may have different period structures

**Solution:**
Define explicit schema for period objects with all expected fields.

---

### 7. **Total vs Calculated Fields Ambiguity** ⚠️ MEDIUM
**Problem:**
Some "calculated" fields are in extraction schema instead of calculation schema.

**Examples:**
```json
"liquidity": {
  "available_cash": {
    "description": "Calculated: cash + securities - restricted"
  },
  "total_available_liquidity": {
    "description": "Calculated: available_cash + undrawn_facilities"
  }
}
```

**Issues:**
- If these are calculated, why are they in Phase 2 extraction schema?
- Should Phase 2 extract them or calculate them?
- If extracted, what if calculation doesn't match?

**Current Practice:**
- Phase 2 extracts them if disclosed
- Phase 3 calculates them if missing
- No clear precedence

**Solution:**
Separate `extracted` vs `calculated` vs `derived` fields explicitly.

---

### 8. **Missing Distribution Total Field** ⚠️ MEDIUM
**Problem:**
Schema has `distributions_per_unit` but no `distributions_total`.

**Current Workaround:**
- Phase 5 multiplies: `distributions_total = distributions_per_unit * common_units`
- But this assumes quarterly distribution * quarterly units
- For YTD, should be YTD total distributions

**Better Approach:**
```json
"distributions": {
  "per_unit": 0.30,
  "total": 29937,              // NEW: explicit total
  "period": "Q2 2025",
  "annualized_per_unit": 1.20
}
```

---

### 9. **Validation Section Too Vague** ⚠️ LOW
**Current:**
```json
"validation": {
  "balance_sheet_balanced": {"type": "boolean"},
  "noi_margin_reasonable": {"type": "boolean"}
}
```

**Missing Validations:**
- FFO/AFFO variance (issuer vs calculated)
- ACFO calculation success (did CFO data exist?)
- Component reconciliation (did REALPAC adjustments sum correctly?)
- Schema version compliance
- Data completeness score

**Solution:**
Expand validation section with comprehensive checks.

---

### 10. **ACFO/AFCF Missing from ffo_affo Section** ⚠️ LOW
**Problem:**
`ffo_affo` section has FFO and AFFO but no ACFO or AFCF.

**Current State:**
- ACFO only in `acfo_components` as optional `issuer-reported` value
- AFCF doesn't exist in Phase 2 at all
- Phase 3 calculates both and writes to separate sections

**Impact:**
- Inconsistent metric organization
- Section 2.5 has 4 metrics (FFO/AFFO/ACFO/AFCF) but schema only tracks 2 in ffo_affo

**Solution:**
Include all 4 metrics in unified `reit_metrics` section with issuer/calculated split.

---

## Medium Priority Issues

### 11. **YTD vs Quarterly Ambiguity**
No clear indication of which values should be YTD vs quarterly for coverage calculations.

### 12. **Source/Metadata Incomplete**
Only `dilution_detail` has `disclosure_source` field. Should be consistent across all sections.

### 13. **Ticker Symbol Missing**
No `ticker` field in schema. Phase 3.5 enrichment needs it. Should be in top-level metadata.

### 14. **Negative Numbers Convention Unclear**
Cash flow sections say "negative for outflows" but some fields are inherently negative (gains/losses). Inconsistent.

### 15. **Common vs Diluted Confusion**
Schema has both basic and diluted units but doesn't clarify which to use where.

### 16. **Missing Derived Fields**
Fields used in reports but not in schema:
- `total_debt` (sum of debt components)
- `net_debt` (total_debt - cash)
- `debt_to_assets` ratio
- `net_debt_ratio`

### 17. **No Period End Date for Time-Series**
Period objects have no `period_start_date` or `period_end_date` for proper time-series tracking.

### 18. **Working Capital Change Sign Confusion**
`change_in_working_capital` - is this the change itself, or the adjustment amount? Sign convention unclear.

### 19. **Portfolio Metrics Incomplete**
Has basic metrics but missing:
- Geographic breakdown
- Property type breakdown
- Tenant concentration
- Lease maturity profile

### 20. **No Schema Version Tracking**
No `schema_version` field to track evolution. Critical for backward compatibility.

---

## Recommended Schema Refactoring Approach

### Phase 1: Core Structure (Issue #58 fix)
1. **Separate issuer_reported vs realpac_calculated**
   - Create two top-level sections under each metric category
   - Move all issuer-disclosed values to `issuer_reported`
   - Reserve `realpac_calculated` for Phase 3 output

2. **Add explicit coverage & payout ratio fields**
   - Total-based coverage ratios
   - Per-unit payout ratios
   - Both in issuer and calculated sections

3. **Standardize period structure**
   - Define schema for `q2_2025`, `ytd_2025`, etc.
   - Include all required fields per period
   - Add `period_start_date` and `period_end_date`

### Phase 2: Clarifications
4. **Document units consistently**
   - Add `financial_units: "thousands"` top-level
   - Specify ratio format (decimal vs percentage)
   - Add unit comments to all numeric fields

5. **Eliminate duplicates**
   - Single source of truth for common data
   - Remove redundant fields or mark as "reconciliation only"

6. **Add missing metadata**
   - `ticker` symbol
   - `schema_version`
   - `extraction_timestamp`
   - `disclosure_sources` per section

### Phase 3: Validation & Completeness
7. **Expand validation section**
   - FFO/AFFO variance tracking
   - Component reconciliation status
   - Data completeness score
   - Schema compliance indicators

8. **Add derived fields**
   - Explicit `total_debt`, `net_debt`
   - Calculated ratios that are always derived

9. **Complete portfolio metrics**
   - Geographic/property type breakdowns
   - Optional but structured when available

---

## Impact on Existing Code

### Scripts to Update:
1. ✅ `.claude/knowledge/phase2_extraction_schema.json` - full refactor
2. ✅ `scripts/extract_key_metrics_efficient.py` - Phase 2 extraction logic
3. ✅ `scripts/calculate_credit_metrics.py` - Phase 3 calculation (write to new structure)
4. ✅ `scripts/generate_final_report.py` - Phase 5 report (read from new structure)
5. ✅ `scripts/validate_extraction_schema.py` - schema validator
6. ✅ `.claude/knowledge/COMPREHENSIVE_EXTRACTION_GUIDE.md` - update examples
7. ✅ `.claude/knowledge/SCHEMA_README.md` - update documentation

### Data Migration:
- Existing Phase 2 JSON files will need conversion script
- Or: Phase 5 can read both old and new formats during transition
- Test cases: Allied Properties, Artis REIT, Dream Office REIT

---

## Next Steps

1. **Review this document with user** - confirm priority and approach
2. **Design new schema structure** - create complete schema draft
3. **Create migration plan** - backward compatibility strategy
4. **Implement schema changes** - update JSON schema file
5. **Update extraction logic** - Phase 2 script changes
6. **Update calculation logic** - Phase 3 script changes
7. **Update report generator** - Phase 5 script changes
8. **Test with existing REITs** - validate against 3-4 test cases
9. **Update documentation** - all guides and README files
10. **Close Issue #58** - verify coverage ratio fix works with new schema
