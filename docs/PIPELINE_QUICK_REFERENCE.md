# Credit Analysis Pipeline - Quick Reference

## 🎯 Schema Consistency Solution

**Problem:** Inconsistent JSON schema between Phase 2 extraction and Phase 3 calculations caused runtime errors.

**Solution:** Standardized schema with validation, backward compatibility, and comprehensive documentation.

---

## 📋 Schema Files (All in `.claude/knowledge/`)

1. **`phase2_extraction_schema.json`** - JSON Schema specification (technical)
2. **`phase2_extraction_template.json`** - Template with comments (practical)
3. **`SCHEMA_README.md`** - Complete documentation with examples

---

## 🔧 New Tools

### Schema Validator
```bash
python scripts/validate_extraction_schema.py <path_to_json>
```

**Usage:**
```bash
# Validate Phase 2 extraction before Phase 3
python scripts/validate_extraction_schema.py \
  Issuer_Reports/Artis_REIT/temp/phase2_extracted_data.json
```

**Output:**
- ✅ Pass: Ready for Phase 3
- ❌ Fail: Shows specific errors to fix
- ⚠️  Warnings: Non-blocking issues

---

## 🎬 Complete Pipeline

### Run Full Analysis
```bash
/analyzeREissuer @financial-statements.pdf @mda.pdf "Issuer Name"
```

### Manual Steps (if needed)

**Phase 1: PDF to Markdown**
```bash
python scripts/preprocess_pdfs_markitdown.py \
  --issuer-name "Issuer Name" \
  financial-statements.pdf mda.pdf
```

**Phase 2: Extract Financial Data**
```bash
python scripts/extract_key_metrics.py \
  --issuer-name "Issuer Name" \
  Issuer_Reports/Issuer_Name/temp/phase1_markdown/*.md
```

**Phase 2.5: Validate Schema (NEW!)**
```bash
python scripts/validate_extraction_schema.py \
  Issuer_Reports/Issuer_Name/temp/phase2_extracted_data.json
```

**Phase 3: Calculate Metrics**
```bash
python scripts/calculate_credit_metrics.py \
  Issuer_Reports/Issuer_Name/temp/phase2_extracted_data.json
```

**Phase 4: Credit Analysis**
```bash
# Handled by Claude Code agent automatically
```

**Phase 5: Generate Report**
```bash
python scripts/generate_final_report.py \
  Issuer_Reports/Issuer_Name/temp/phase3_calculated_metrics.json \
  Issuer_Reports/Issuer_Name/temp/phase4_credit_analysis.md
```

---

## 🔑 Key Schema Rules

### Rule 1: Flat Structure for balance_sheet
```json
{
  "balance_sheet": {
    "total_assets": 2611435,      // ✅ Top level
    "cash": 16639                  // ✅ Top level
  }
}
```

**NOT:**
```json
{
  "balance_sheet": {
    "assets": {                    // ❌ Nested
      "total_assets": 2611435
    }
  }
}
```

### Rule 2: Top-Level Values Required
```json
{
  "income_statement": {
    "noi": 30729,                  // ✅ Required
    "interest_expense": 16937,     // ✅ Required
    "q2_2025": { ... }             // Optional detail
  }
}
```

### Rule 3: No Null for Numbers
```json
{
  "portfolio": {
    "total_gla_sf": 0              // ✅ Use 0
  }
}
```

**NOT:**
```json
{
  "portfolio": {
    "total_gla_sf": null           // ❌ Causes errors
  }
}
```

### Rule 4: Decimal Format for Rates
```json
{
  "portfolio": {
    "occupancy_rate": 0.878        // ✅ Decimal (87.8%)
  }
}
```

**NOT:**
```json
{
  "portfolio": {
    "occupancy_rate": 87.8         // ❌ Percentage
  }
}
```

---

## 🆘 Troubleshooting

### Error: "Missing required field: balance_sheet.total_assets"

**Cause:** Field not at top level of balance_sheet

**Fix:**
```json
{
  "balance_sheet": {
    "total_assets": 2611435        // Move to top level
  }
}
```

### Error: "unsupported operand type(s) for /: 'NoneType' and 'int'"

**Cause:** Null value in numeric field

**Fix:** Replace `null` with `0` for unknown values

### Error: "Missing required field: income_statement.noi"

**Cause:** Only nested quarterly data provided

**Fix:** Add top-level noi field with most recent period value

### Warning: "Use 'occupancy_with_commitments' instead of 'occupancy_including_commitments'"

**Impact:** Non-blocking (backward compatible)

**Fix:** Use standardized field name in new extractions

---

## ✅ Validation Checklist

Before running Phase 3:

- [ ] Run schema validator
- [ ] All required fields present
- [ ] balance_sheet is flat (no nested objects)
- [ ] income_statement has top-level noi, interest_expense, revenue
- [ ] ffo_affo has top-level ffo, affo, ffo_per_unit, affo_per_unit, distributions_per_unit
- [ ] No null values for numeric fields
- [ ] Occupancy rates are decimals (0-1 range)
- [ ] Interest expense is positive number

---

## 📚 Documentation

- **Schema Spec:** `.claude/knowledge/phase2_extraction_schema.json`
- **Template:** `.claude/knowledge/phase2_extraction_template.json`
- **Full Guide:** `.claude/knowledge/SCHEMA_README.md`
- **This Guide:** `PIPELINE_QUICK_REFERENCE.md`

---

## 🎯 What Changed?

### Phase 2 (extract_key_metrics.py)
- ✅ Updated prompt with explicit schema instructions
- ✅ References to schema files in prompt
- ✅ Validation step added to workflow

### Phase 3 (calculate_credit_metrics.py)
- ✅ Handles null values gracefully (converts to 0)
- ✅ Supports both old and new field naming conventions
- ✅ Better error messages with field paths
- ✅ Backward compatible with existing extractions

### New Files
- ✅ `scripts/validate_extraction_schema.py` - Validator tool
- ✅ `.claude/knowledge/phase2_extraction_schema.json` - JSON Schema
- ✅ `.claude/knowledge/phase2_extraction_template.json` - Template
- ✅ `.claude/knowledge/SCHEMA_README.md` - Documentation

---

## 🚀 Quick Start

**For new analysis:**
```bash
/analyzeREissuer @statements.pdf @mda.pdf "Company Name"
```

**To validate existing extraction:**
```bash
python scripts/validate_extraction_schema.py <your_file.json>
```

**To fix schema issues:**
1. Run validator to identify errors
2. Check SCHEMA_README.md for examples
3. Fix JSON manually or re-run Phase 2
4. Re-validate before Phase 3

---

**Last Updated:** 2025-10-17
**Pipeline Version:** 1.0.0
**Schema Version:** 1.0.0
