# Phase 2 Extraction Schema Documentation

## Overview

This document defines the **standardized JSON schema** that Phase 2 extraction MUST produce for Phase 3 calculations to work correctly.

## Schema Files

1. **`phase2_extraction_schema.json`** - JSON Schema specification (machine-readable)
2. **`phase2_extraction_template.json`** - Template with inline comments (human-readable)
3. **This README** - Complete documentation with examples

## Key Schema Principles

### 1. Flat Structure for balance_sheet

❌ **WRONG (nested objects):**
```json
{
  "balance_sheet": {
    "assets": {
      "total_assets": 2611435,
      "cash": 16639
    },
    "liabilities": {
      "mortgages_noncurrent": 217903
    }
  }
}
```

✅ **CORRECT (flat structure):**
```json
{
  "balance_sheet": {
    "total_assets": 2611435,
    "cash": 16639,
    "mortgages_noncurrent": 217903
  }
}
```

### 2. Top-Level Values Required

Both `income_statement` and `ffo_affo` MUST include top-level values for the **most recent period** (e.g., Q2 2025).

❌ **WRONG (only nested periods):**
```json
{
  "income_statement": {
    "q2_2025": {
      "noi": 30729,
      "interest_expense": 16937
    }
  }
}
```

✅ **CORRECT (top-level + optional nested):**
```json
{
  "income_statement": {
    "noi": 30729,
    "interest_expense": 16937,
    "revenue": 59082,
    "q2_2025": {
      "noi": 30729,
      "interest_expense": 16937
    }
  }
}
```

### 3. No Null Values for Numeric Fields

Use `0` instead of `null` for unknown numeric values.

❌ **WRONG:**
```json
{
  "portfolio": {
    "total_gla_sf": null
  }
}
```

✅ **CORRECT:**
```json
{
  "portfolio": {
    "total_gla_sf": 0
  }
}
```

### 4. Decimal Format for Rates

Occupancy and growth rates MUST be decimals (0-1 range), NOT percentages.

❌ **WRONG:**
```json
{
  "portfolio": {
    "occupancy_rate": 87.8
  }
}
```

✅ **CORRECT:**
```json
{
  "portfolio": {
    "occupancy_rate": 0.878
  }
}
```

## Required Fields

### Top Level (Always Required)

```json
{
  "issuer_name": "string",
  "reporting_date": "YYYY-MM-DD",
  "currency": "CAD | USD"
}
```

### balance_sheet (Required Fields)

```json
{
  "balance_sheet": {
    "total_assets": number,
    "mortgages_noncurrent": number,
    "mortgages_current": number,
    "credit_facilities": number,
    "cash": number
  }
}
```

**Note:** `senior_unsecured_debentures` is optional (defaults to 0).

### income_statement (Required Fields)

```json
{
  "income_statement": {
    "noi": number,
    "interest_expense": number,
    "revenue": number
  }
}
```

**Important:** `interest_expense` must be a **positive number** (absolute value).

### ffo_affo (Required Fields)

```json
{
  "ffo_affo": {
    "ffo": number,
    "affo": number,
    "ffo_per_unit": number,
    "affo_per_unit": number,
    "distributions_per_unit": number
  }
}
```

## Field Naming Conventions

### Standardized Field Names

Use these EXACT field names (case-sensitive):

| ✅ Correct | ❌ Incorrect |
|-----------|-------------|
| `mortgages_noncurrent` | `mortgages_loans_noncurrent` |
| `mortgages_current` | `mortgages_loans_current` |
| `occupancy_with_commitments` | `occupancy_including_commitments` |
| `same_property_noi_growth_6m` | `same_property_noi_growth` |
| `total_gla_sf` | `gla_sf` |

**Note:** Phase 3 now supports both naming conventions for backward compatibility, but new extractions should use the standardized names.

## Complete Example

```json
{
  "issuer_name": "Artis Real Estate Investment Trust",
  "reporting_date": "2025-06-30",
  "reporting_period": "Q2 2025",
  "currency": "CAD",

  "balance_sheet": {
    "total_assets": 2611435,
    "investment_properties": 2025831,
    "cash": 16639,
    "mortgages_noncurrent": 217903,
    "mortgages_current": 423519,
    "credit_facilities": 437590,
    "senior_unsecured_debentures": 0,
    "total_liabilities": 1155452,
    "total_unitholders_equity": 1455983
  },

  "income_statement": {
    "noi": 30729,
    "interest_expense": 16937,
    "revenue": 59082,
    "q2_2025": {
      "revenue": 59082,
      "net_operating_income": 30729
    }
  },

  "ffo_affo": {
    "ffo": 16956,
    "affo": 8204,
    "ffo_per_unit": 0.17,
    "affo_per_unit": 0.08,
    "distributions_per_unit": 0.03
  },

  "portfolio": {
    "total_properties": 0,
    "total_gla_sf": 0,
    "occupancy_rate": 0.878,
    "occupancy_with_commitments": 0.890,
    "same_property_noi_growth_6m": 0.023
  }
}
```

## Validation

### Automated Validation

Run schema validation after Phase 2 extraction:

```bash
python scripts/validate_extraction_schema.py <path_to_json>
```

Example:
```bash
python scripts/validate_extraction_schema.py \
  Issuer_Reports/Artis_REIT/temp/phase2_extracted_data.json
```

### Expected Output

✅ **Valid schema:**
```
📋 Validating schema for: phase2_extracted_data.json
======================================================================

✅ Schema validation PASSED

Issuer: Artis Real Estate Investment Trust
Reporting Date: 2025-06-30
Currency: CAD

✅ This file is compatible with Phase 3 calculations
```

❌ **Invalid schema:**
```
❌ Schema validation FAILED

Found 3 errors:

  ❌ Missing required field: balance_sheet.mortgages_noncurrent
  ❌ Missing required field: income_statement.noi
  ❌ Field 'portfolio.occupancy_rate' must be numeric, got str

💡 Fix these errors before running Phase 3 calculations
```

## Common Issues and Fixes

### Issue 1: Nested balance_sheet structure

**Error:** `TypeError: unsupported operand type(s) for /`

**Cause:** Phase 3 expects flat structure

**Fix:** Flatten balance_sheet fields to top level

### Issue 2: Missing top-level noi/interest_expense

**Error:** `KeyError: 'income_statement.noi'`

**Cause:** Only nested quarterly data provided

**Fix:** Add top-level fields for most recent period

### Issue 3: Null values in portfolio

**Error:** `TypeError: unsupported operand type(s) for /: 'NoneType' and 'int'`

**Cause:** `total_gla_sf: null`

**Fix:** Use `0` instead of `null`

### Issue 4: Wrong occupancy format

**Error:** Occupancy calculated as 8780% instead of 87.8%

**Cause:** Used `87.8` instead of `0.878`

**Fix:** Convert to decimal (divide by 100)

## Phase 3 Compatibility

Phase 3 (`calculate_credit_metrics.py`) has been updated to:

1. ✅ Accept flat balance_sheet structure
2. ✅ Support both old and new field naming conventions
3. ✅ Handle null values gracefully (convert to 0)
4. ✅ Validate required fields and fail with clear error messages

## Migration Guide

### Updating Existing Extractions

If you have existing Phase 2 JSON files that fail validation:

1. **Run validation first:**
   ```bash
   python scripts/validate_extraction_schema.py <your_file.json>
   ```

2. **Fix errors in order:**
   - Required fields first
   - Type mismatches second
   - Naming conventions third (warnings only)

3. **Re-run Phase 3:**
   ```bash
   python scripts/calculate_credit_metrics.py <your_file.json>
   ```

### Creating New Extractions

When creating new Phase 2 extractions:

1. Use the updated `extract_key_metrics.py` script
2. It now includes schema instructions in the prompt
3. Validate output automatically before Phase 3
4. Schema compliance is enforced

## References

- **Schema Definition:** `.claude/knowledge/phase2_extraction_schema.json`
- **Template:** `.claude/knowledge/phase2_extraction_template.json`
- **Validator:** `scripts/validate_extraction_schema.py`
- **Phase 3 Script:** `scripts/calculate_credit_metrics.py`

## Questions?

If you encounter schema issues:

1. Run the validator to identify specific problems
2. Check this README for common issues
3. Review the complete example above
4. Consult the JSON schema files for technical details

---

**Last Updated:** 2025-10-17
**Schema Version:** 1.0.0
**Pipeline Version:** 1.0.0
