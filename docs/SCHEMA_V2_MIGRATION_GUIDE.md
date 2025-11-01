# Phase 2 Schema v2.0 Migration Guide

**Date:** 2025-11-01
**Schema Version:** 1.0 → 2.0.0
**Breaking Change:** Yes

## Overview

Schema v2.0 is a major refactoring that addresses critical issues identified in the schema review (docs/SCHEMA_REVIEW_2025-11-01.md). The primary change is **explicit separation of issuer-reported vs REALPAC-calculated values**.

## Key Changes

### 1. Schema Version Tracking
**New Required Field:**
```json
{
  "schema_version": "2.0.0"
}
```

### 2. Issuer Metadata
**New Required Fields:**
```json
{
  "ticker": "AX-UN.TO",
  "financial_units": "thousands",
  "reporting_period": {
    "period_type": "Q2",
    "period_label": "Q2 2025",
    "fiscal_year": 2025,
    "period_start_date": "2025-04-01",
    "period_end_date": "2025-06-30",
    "period_months": 3
  }
}
```

**Changed:** `reporting_period` is now an object (was string)

### 3. FFO/AFFO Section Renamed → `reit_metrics`
**Old Structure:**
```json
{
  "ffo_affo": {
    "ffo": 34491,                    // Issuer-reported
    "affo": 16939,                   // Issuer-reported
    "ffo_per_unit": 0.17,           // Issuer-reported
    "ytd_2025": { ... }              // No schema
  }
}
```

**New Structure:**
```json
{
  "reit_metrics": {
    "issuer_reported": {
      "ffo": 34491,
      "affo": 16939,
      "acfo": null,
      "ffo_per_unit_diluted": 0.34,
      "affo_per_unit_diluted": 0.17,
      "acfo_per_unit_diluted": null,
      "ffo_payout_ratio": 52.0,      // NOW IN SCHEMA
      "affo_payout_ratio": 105.8,    // NOW IN SCHEMA
      "ffo_coverage_ratio": 1.92,    // NOW IN SCHEMA
      "affo_coverage_ratio": 0.95    // NOW IN SCHEMA
    },
    "realpac_calculated": {
      "ffo": -3815,                  // Phase 3 output
      "affo": -3751,
      "acfo": -7127,
      "afcf": -24021,
      "ffo_per_unit_diluted": -0.038,
      "affo_per_unit_diluted": -0.0374,
      "acfo_per_unit_diluted": -0.0711,
      "afcf_per_unit": -0.2421,
      "ffo_payout_ratio": null,      // N/A for negative
      "affo_payout_ratio": null,
      "acfo_payout_ratio": null,
      "afcf_payout_ratio": null,
      "ffo_coverage_ratio": null,
      "affo_coverage_ratio": null,
      "acfo_coverage_ratio": null,
      "afcf_coverage_ratio": null
    },
    "validation": {
      "ffo_variance_amount": -38306,
      "ffo_variance_percent": -122.5,
      "affo_variance_amount": -20690,
      "affo_variance_percent": -145.7
    }
  }
}
```

**Key Changes:**
- ✅ Explicit `issuer_reported` vs `realpac_calculated` sections
- ✅ Coverage and payout ratios now in schema
- ✅ ACFO and AFCF included in unified structure
- ✅ Removed nested period objects (q2_2025, ytd_2025) - periods handled at top level
- ✅ Validation section for variance tracking

### 4. Distributions Section (New)
**New Required Section:**
```json
{
  "distributions": {
    "per_unit": 0.30,
    "total": 29937,                  // NEW: explicit total
    "annualized_per_unit": 1.20,
    "declaration_dates": ["2025-05-15", "2025-06-15"],
    "payment_dates": ["2025-06-30", "2025-07-31"]
  }
}
```

**Old Location:** `ffo_affo.distributions_per_unit`
**New Location:** `distributions.per_unit` + `distributions.total`

### 5. Balance Sheet Enhancements
**New Fields:**
```json
{
  "balance_sheet": {
    "balance_sheet_date": "2025-06-30",  // NEW: explicit date
    "total_debt": 1079000,               // NEW: single source of truth
    "net_debt": 1063740,                 // NEW: calculated but explicit
    "restricted_cash": 0                 // NEW: separated from cash
  }
}
```

### 6. Metadata Fields Added Throughout
Every major section now has:
```json
{
  "disclosure_source": "MD&A page 18 - FFO/AFFO Reconciliation"
}
```

### 7. Validation Section Enhanced
**Old:**
```json
{
  "validation": {
    "balance_sheet_balanced": true,
    "noi_margin_reasonable": true
  }
}
```

**New:**
```json
{
  "validation": {
    "schema_version_compliance": true,
    "balance_sheet_balanced": true,
    "debt_reconciliation": true,
    "dilution_reconciliation": true,
    "ffo_affo_reconciliation": true,
    "data_completeness_score": 87.5,
    "extraction_warnings": [
      "ACFO not reported by issuer",
      "Property count estimated from table rows"
    ],
    "extraction_errors": []
  }
}
```

---

## Migration Path

### Phase 2 Extraction Script
**File:** `scripts/extract_key_metrics_efficient.py`

**Changes Required:**

1. **Add schema version and metadata:**
```python
output = {
    "schema_version": "2.0.0",
    "extraction_metadata": {
        "extraction_timestamp": datetime.now().isoformat(),
        "extraction_method": "llm",
        "model_name": "claude-sonnet-4",
        "data_quality_score": 85.0
    },
    "ticker": extract_ticker(md_content),
    "financial_units": "thousands",
    # ...
}
```

2. **Restructure reporting_period:**
```python
# OLD
"reporting_period": "Q2 2025"

# NEW
"reporting_period": {
    "period_type": "Q2",
    "period_label": "Q2 2025",
    "fiscal_year": 2025,
    "period_start_date": "2025-04-01",
    "period_end_date": "2025-06-30",
    "period_months": 3
}
```

3. **Restructure reit_metrics:**
```python
# OLD
"ffo_affo": {
    "ffo": extract_ffo(),
    "affo": extract_affo(),
    # ...
}

# NEW
"reit_metrics": {
    "issuer_reported": {
        "ffo": extract_ffo(),
        "affo": extract_affo(),
        "acfo": extract_acfo() or None,
        "ffo_per_unit_diluted": extract_ffo_per_unit(),
        "affo_per_unit_diluted": extract_affo_per_unit(),
        "ffo_payout_ratio": calculate_payout_ratio(ffo_per_unit, dist_per_unit),
        "affo_payout_ratio": calculate_payout_ratio(affo_per_unit, dist_per_unit),
        "ffo_coverage_ratio": calculate_coverage_ratio(ffo, dist_total),
        "affo_coverage_ratio": calculate_coverage_ratio(affo, dist_total),
        "disclosure_source": "MD&A page 18"
    },
    "realpac_calculated": {},  # Empty - Phase 3 populates
    "validation": {}           # Empty - Phase 3 populates
}
```

4. **Add distributions section:**
```python
"distributions": {
    "per_unit": extract_distributions_per_unit(),
    "total": extract_distributions_total(),  # NEW
    "annualized_per_unit": extract_distributions_per_unit() * 4,
    "disclosure_source": "MD&A page 5"
}
```

5. **Update balance_sheet:**
```python
"balance_sheet": {
    "balance_sheet_date": reporting_date,  # NEW
    "total_debt": mortgages_nc + mortgages_c + credit_fac + debentures,  # NEW
    "net_debt": total_debt - cash,  # NEW
    "restricted_cash": extract_restricted_cash(),  # NEW
    # ... existing fields
}
```

### Phase 3 Calculation Script
**File:** `scripts/calculate_credit_metrics.py`

**Changes Required:**

1. **Read from new structure:**
```python
# OLD
ffo_reported = data['ffo_affo']['ffo']
affo_reported = data['ffo_affo']['affo']

# NEW
ffo_reported = data['reit_metrics']['issuer_reported']['ffo']
affo_reported = data['reit_metrics']['issuer_reported']['affo']
```

2. **Write calculated values to new section:**
```python
# OLD
data['reit_metrics'] = {
    'ffo_calculated': ffo_calc,
    'affo_calculated': affo_calc,
    # ...
}

# NEW
data['reit_metrics']['realpac_calculated'] = {
    'ffo': ffo_calc,
    'affo': affo_calc,
    'acfo': acfo_calc,
    'afcf': afcf_calc,
    'ffo_per_unit_diluted': ffo_calc / diluted_units,
    'affo_per_unit_diluted': affo_calc / diluted_units,
    'acfo_per_unit_diluted': acfo_calc / diluted_units,
    'afcf_per_unit': afcf_calc / common_units,
    'ffo_payout_ratio': calculate_payout_ratio(ffo_per_unit, dist_per_unit),
    'affo_payout_ratio': calculate_payout_ratio(affo_per_unit, dist_per_unit),
    'acfo_payout_ratio': calculate_payout_ratio(acfo_per_unit, dist_per_unit),
    'afcf_payout_ratio': calculate_payout_ratio(afcf_per_unit, dist_per_unit),
    'ffo_coverage_ratio': calculate_coverage_ratio(ffo_calc, dist_total),
    'affo_coverage_ratio': calculate_coverage_ratio(affo_calc, dist_total),
    'acfo_coverage_ratio': calculate_coverage_ratio(acfo_calc, dist_total),
    'afcf_coverage_ratio': calculate_coverage_ratio(afcf_calc, dist_total),
    'calculation_timestamp': datetime.now().isoformat()
}
```

3. **Calculate validation metrics:**
```python
data['reit_metrics']['validation'] = {
    'ffo_variance_amount': ffo_calc - ffo_reported,
    'ffo_variance_percent': ((ffo_calc - ffo_reported) / ffo_reported) * 100,
    'affo_variance_amount': affo_calc - affo_reported,
    'affo_variance_percent': ((affo_calc - affo_reported) / affo_reported) * 100,
    'material_variance_flag': abs((ffo_calc - ffo_reported) / ffo_reported) > 0.10
}
```

### Phase 5 Report Generator
**File:** `scripts/generate_final_report.py`

**Changes Required:**

1. **Read from new structure:**
```python
# OLD
ffo_reported = metrics.get('ffo_affo', {}).get('ffo', 0)

# NEW - Section 2.5.1 (Issuer-Reported)
issuer_metrics = metrics.get('reit_metrics', {}).get('issuer_reported', {})
ffo_reported = issuer_metrics.get('ffo', 0)
ffo_per_unit_rep = issuer_metrics.get('ffo_per_unit_diluted', 0)
ffo_coverage_rep = issuer_metrics.get('ffo_coverage_ratio')
ffo_payout_rep = issuer_metrics.get('ffo_payout_ratio')

# NEW - Section 2.5.2 (REALPAC-Calculated)
calc_metrics = metrics.get('reit_metrics', {}).get('realpac_calculated', {})
ffo_calculated = calc_metrics.get('ffo', 0)
ffo_per_unit_calc = calc_metrics.get('ffo_per_unit_diluted', 0)
ffo_coverage_calc = calc_metrics.get('ffo_coverage_ratio')
ffo_payout_calc = calc_metrics.get('ffo_payout_ratio')
```

2. **Update template placeholders:**
```python
# Section 2.5.1: Issuer-Reported
'FFO_REPORTED': f"{ffo_reported:,.0f}",
'FFO_COVERAGE_REPORTED': f"{ffo_coverage_rep:.2f}" if ffo_coverage_rep else 'N/A',
'FFO_PAYOUT_REPORTED': f"{ffo_payout_rep:.1f}" if ffo_payout_rep else 'N/A',

# Section 2.5.2: REALPAC-Calculated
'FFO_CALCULATED': f"{ffo_calculated:,.0f}",
'FFO_COVERAGE_CALCULATED': f"{ffo_coverage_calc:.2f}" if ffo_coverage_calc else 'N/A',
'FFO_PAYOUT_CALCULATED': f"{ffo_payout_calc:.1f}" if ffo_payout_calc else 'N/A',
```

3. **No more manual coverage/payout calculation:**
```python
# OLD - Phase 5 calculated these
ffo_cov_rep = calculate_coverage_ratio(ffo_per_unit_rep, distributions)

# NEW - Read directly from JSON (already calculated)
ffo_cov_rep = issuer_metrics.get('ffo_coverage_ratio')
```

### Phase 2 Schema Validator
**File:** `scripts/validate_extraction_schema.py`

**Changes Required:**

1. **Update schema file path:**
```python
# OLD
SCHEMA_PATH = ".claude/knowledge/phase2_extraction_schema.json"

# NEW
SCHEMA_PATH = ".claude/knowledge/phase2_extraction_schema_v2.json"
```

2. **Check schema version:**
```python
def validate_schema_version(data):
    """Validate schema version matches expected v2.0.0"""
    version = data.get('schema_version')
    if version != '2.0.0':
        raise ValueError(f"Schema version mismatch: expected '2.0.0', got '{version}'")
```

---

## Backward Compatibility

### Reading Old Format (v1.0) Files
Phase 5 report generator should support both old and new formats during transition:

```python
def read_reit_metrics_compat(data):
    """Read REIT metrics with backward compatibility"""

    # Check schema version
    schema_version = data.get('schema_version', '1.0')

    if schema_version == '2.0.0':
        # New format
        return {
            'issuer': data['reit_metrics']['issuer_reported'],
            'calculated': data['reit_metrics']['realpac_calculated']
        }
    else:
        # Old format - convert on the fly
        old_ffo_affo = data.get('ffo_affo', {})

        return {
            'issuer': {
                'ffo': old_ffo_affo.get('ffo'),
                'affo': old_ffo_affo.get('affo'),
                'ffo_per_unit_diluted': old_ffo_affo.get('ffo_per_unit_diluted'),
                'affo_per_unit_diluted': old_ffo_affo.get('affo_per_unit_diluted'),
                # Calculate coverage/payout if missing
                'ffo_coverage_ratio': None,  # Need to calculate
                'ffo_payout_ratio': old_ffo_affo.get('ytd_2025', {}).get('ffo_payout_ratio')
            },
            'calculated': {
                'ffo': data.get('reit_metrics', {}).get('ffo_calculated'),
                'affo': data.get('reit_metrics', {}).get('affo_calculated'),
                # ...
            }
        }
```

### Converting Existing Files to v2.0
Create migration script:

**File:** `scripts/migrate_phase2_to_v2.py`
```python
#!/usr/bin/env python3
"""
Migrate existing Phase 2 JSON files from v1.0 to v2.0 schema
"""

def migrate_v1_to_v2(old_data):
    """Convert v1.0 schema to v2.0 schema"""

    new_data = {
        "schema_version": "2.0.0",
        # Map old fields to new structure
        # ...
    }

    return new_data

if __name__ == "__main__":
    # Find all phase2_extracted_data.json files
    # Convert each to v2.0
    # Save as phase2_extracted_data_v2.json
    pass
```

---

## Testing Strategy

### 1. Unit Tests
```python
# tests/test_schema_v2.py

def test_schema_version_required():
    """Schema version must be 2.0.0"""
    assert data['schema_version'] == '2.0.0'

def test_reit_metrics_structure():
    """REIT metrics must have issuer/calculated separation"""
    assert 'issuer_reported' in data['reit_metrics']
    assert 'realpac_calculated' in data['reit_metrics']
    assert 'validation' in data['reit_metrics']

def test_coverage_ratios_in_schema():
    """Coverage ratios must be explicitly in schema"""
    issuer = data['reit_metrics']['issuer_reported']
    assert 'ffo_coverage_ratio' in issuer
    assert 'affo_coverage_ratio' in issuer

def test_distributions_section_exists():
    """Distributions must be separate section"""
    assert 'distributions' in data
    assert 'per_unit' in data['distributions']
    assert 'total' in data['distributions']
```

### 2. Integration Tests
Test with existing REIT data:
- Allied Properties Q3 2025
- Artis REIT Q2 2025
- Dream Office REIT Q2 2025

### 3. Validation Tests
```bash
# Validate all migrated files against v2.0 schema
python scripts/validate_extraction_schema.py \
  Issuer_Reports/*/temp/phase2_extracted_data_v2.json
```

---

## Rollout Plan

### Week 1: Schema & Documentation
- ✅ Create v2.0 schema
- ✅ Write migration guide (this document)
- ⬜ Update SCHEMA_README.md
- ⬜ Update COMPREHENSIVE_EXTRACTION_GUIDE.md

### Week 2: Phase 2 Extraction
- ⬜ Update extract_key_metrics_efficient.py
- ⬜ Test with 3 REITs
- ⬜ Fix any extraction issues

### Week 3: Phase 3 Calculation
- ⬜ Update calculate_credit_metrics.py
- ⬜ Update to write to realpac_calculated section
- ⬜ Add validation metrics
- ⬜ Test with 3 REITs

### Week 4: Phase 5 Report Generation
- ⬜ Update generate_final_report.py
- ⬜ Add backward compatibility layer
- ⬜ Test report generation with both v1.0 and v2.0 files
- ⬜ Verify Issue #58 fix works

### Week 5: Migration & Testing
- ⬜ Create migration script for existing files
- ⬜ Migrate all test cases to v2.0
- ⬜ Run full pipeline on all test REITs
- ⬜ Compare reports (v1.0 vs v2.0)

### Week 6: Deployment
- ⬜ Update slash commands to use v2.0
- ⬜ Update validation script
- ⬜ Archive v1.0 schema
- ⬜ Update all documentation
- ⬜ Close Issue #58

---

## Benefits Summary

### For Issue #58 (Section 2.5.1 Coverage Ratios)
✅ **FIXED:** Coverage and payout ratios now explicitly calculated and stored in schema
- Section 2.5.1 reads from `issuer_reported.ffo_coverage_ratio`
- Section 2.5.2 reads from `realpac_calculated.ffo_coverage_ratio`
- No more confusion about which values to use

### For Data Quality
✅ Explicit validation section tracks:
- FFO/AFFO variance between issuer and calculated
- Component reconciliation status
- Data completeness score
- Extraction warnings and errors

### For Maintainability
✅ Single source of truth for each metric
✅ Clear separation of concerns (extraction vs calculation)
✅ Schema version tracking for future changes
✅ Comprehensive metadata for debugging

### For Accuracy
✅ Coverage ratios calculated from totals (not per-unit)
✅ Payout ratios handle negative values (return null)
✅ All calculations documented with formulas in schema
✅ Reconciliation checks enforce consistency

---

## Questions & Answers

**Q: Do we need to migrate existing files immediately?**
A: No. Phase 5 will support both v1.0 and v2.0 during transition. Migrate when convenient.

**Q: What happens to old slash commands?**
A: They continue to work. New runs will use v2.0 schema. Old reports remain valid.

**Q: How do we handle partial migrations?**
A: Schema validator checks version. v1.0 files validated with old schema, v2.0 with new.

**Q: Can Phase 3 read v1.0 and write v2.0?**
A: Yes. Phase 3 will be updated to:
1. Read from v1.0 or v2.0 structure (compat layer)
2. Always write v2.0 structure

**Q: What about performance?**
A: No performance impact. Schema defines structure, not processing logic.

---

## Support

For issues or questions:
1. Check `docs/SCHEMA_REVIEW_2025-11-01.md` for design rationale
2. Review `.claude/knowledge/SCHEMA_README.md` for field definitions
3. See `.claude/knowledge/COMPREHENSIVE_EXTRACTION_GUIDE.md` for examples
4. Create GitHub issue with label `schema-v2`
