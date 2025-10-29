# Claude Code Slash Commands

This directory contains custom slash commands for the Real Estate Issuer Credit Analysis pipeline.

## Available Commands

### `/analyzeREissuer` - Multi-Phase Credit Analysis

Performs comprehensive credit analysis on a real estate issuer using a 5-phase pipeline to avoid context length limitations.

**Usage:**
```bash
/analyzeREissuer @financial-statements.pdf @mda.pdf "Issuer Name"
```

**Arguments:**
- `@file1.pdf`: Path to financial statements PDF (use @ prefix)
- `@file2.pdf`: Additional PDFs (optional, e.g., MD&A, supplementary disclosures)
- `"Issuer Name"`: **REQUIRED** - Issuer name for folder organization (last argument without @)

**Example:**
```bash
/analyzeREissuer @ExampleREIT-Q2-25-Consol-FS-Aug-7.pdf @ExampleREIT-Q2-25-MDA-Aug-7.pdf "Example REIT"
```

**What It Does:**
1. **Phase 1:** Converts PDFs to markdown (markitdown)
2. **Phase 2:** Extracts financial data using Claude Code
3. **Phase 3:** Calculates credit metrics (pure Python, 0 tokens)
4. **Phase 4:** Generates qualitative credit analysis using slim agent
5. **Phase 5:** Generates final comprehensive credit opinion report (0 tokens)

**Output:**
```
Issuer_Reports/{Issuer_Name}/
├── temp/
│   ├── phase1_markdown/        # Converted PDFs
│   ├── phase2_extracted_data.json
│   ├── phase3_calculated_metrics.json
│   └── phase4_credit_analysis.md
└── reports/
    └── {timestamp}_Credit_Opinion_{Issuer_Name}.md
```

**Token Usage:** ~13,000 tokens total (~$0.30 per analysis)

---

### `/analyzeREissuer-docling` - Credit Analysis with Docling PDF Conversion

Alternative version of `/analyzeREissuer` using Docling for higher-quality PDF conversion (slower but cleaner table extraction).

**Usage:**
```bash
/analyzeREissuer-docling @financial-statements.pdf @mda.pdf "Issuer Name"
```

**Key Differences from Default:**
- **Phase 1:** Uses Docling FAST mode instead of PyMuPDF4LLM + Camelot
- **Processing Time:** ~20 minutes (vs 30 seconds for PyMuPDF)
- **Table Quality:** Cleaner 4-column tables, better structure
- **Use Case:** When PyMuPDF extraction has formatting issues

**All other phases identical to standard `/analyzeREissuer` command.**

---

### `/verifyreport` - Credit Report Validation

Verifies the accuracy of a generated credit opinion report by comparing it against all source documents in the analysis pipeline.

**Usage:**
```bash
/verifyreport "Issuer Name"
/verifyreport "Issuer Name" "report_filename.md"
```

**Arguments:**
- `"Issuer Name"`: Name of issuer to validate (required)
- `"report_filename.md"`: Specific report to validate (optional, defaults to most recent)

**Example:**
```bash
/verifyreport "Example REIT"
/verifyreport "Example REIT" "2025-10-17_125408_Credit_Opinion_Example_Real_Estate_Investment_Trust.md"
```

**What It Does:**
1. Locates all source files for the issuer:
   - Original PDFs
   - Phase 1 markdown files
   - Phase 2 extracted data
   - Phase 3 calculated metrics
   - Phase 4 credit analysis
   - Phase 5 final report

2. Performs comprehensive validation:
   - ✅ Balance sheet accuracy (PDF → Extracted → Report)
   - ✅ Income statement accuracy
   - ✅ Calculated metrics verification (manual recalculation)
   - ✅ Qualitative assessment consistency
   - ✅ Data integrity checks (balance sheet equation, NOI calculation, etc.)

3. Generates detailed validation report with:
   - Overall validation score (pass/fail rate)
   - Comparison tables for all key metrics
   - Error classification (critical/warning/pass)
   - Specific recommendations for any discrepancies found

**Output:**
- Comprehensive markdown validation report
- Line-by-line comparison of key metrics
- Confidence assessment for credit opinion reliability

**Use Case:**
Quality assurance before presenting credit analysis to stakeholders or credit committee.

---

### `/verifyconversion` - Phase 1 PDF Conversion Quality Check

Validates the quality of Phase 1 markdown conversion by checking table structure, data integrity, and completeness.

**Usage:**
```bash
/verifyconversion "Issuer Name"
```

**What It Does:**
- Validates table extraction completeness
- Checks table structure (proper rows/columns)
- Verifies financial statement hierarchies preserved
- Identifies missing or malformed tables
- Recommends Docling if PyMuPDF extraction has issues

**Use Case:** QA check after Phase 1 before proceeding to extraction.

---

### `/verifyextract` - Phase 2 Extraction Accuracy Validation

Validates Phase 2 extraction accuracy by comparing extracted JSON against Phase 1 markdown source.

**Usage:**
```bash
/verifyextract "Issuer Name"
```

**What It Does:**
- Compares Phase 2 JSON against Phase 1 markdown
- Validates balance sheet, income statement, cash flows
- Checks FFO/AFFO/ACFO reconciliation completeness
- Verifies schema compliance
- Identifies extraction errors or omissions

**Use Case:** QA check after Phase 2 before Phase 3 calculations.

---

### `/updatemodel` - Distribution Cut Prediction Model Update

Comprehensive workflow for updating the distribution cut prediction model with new training data.

**Usage:**
```bash
/updatemodel
```

**What It Does:**

11-step guided workflow:
1. **Assess Current Model** - Review v2.2 baseline (F1: 0.870, ROC AUC: 0.930)
2. **Identify Observations** - Find 3-5 distribution cuts + 3-5 controls
3. **Collect PDFs** - Download financial statements from SEDAR+
4. **Generate Phase 3 Metrics** - Run pipeline for each observation
5. **Build Training Dataset** - Extract 28 Phase 3 features, compile CSV
6. **Merge Data** - Combine new data with existing training set
7. **Train Model** - Retrain logistic regression (includes Python script)
8. **Validate Model** - Compare v2.3 vs v2.2 performance
9. **Deploy Model** - Archive v2.2, deploy v2.3, update docs
10. **Verify Deployment** - Test with real pipeline run
11. **Commit Changes** - Git commit with detailed changelog

**Key Features:**
- Complete Python training scripts provided
- Model validation framework (side-by-side comparison)
- Deployment procedures (archive, deploy, verify)
- Documentation templates (README, CHANGELOG)
- Troubleshooting guide for common issues

**Success Criteria:**
- F1 Score ≥ 0.80 (target)
- Improved over v2.2 baseline
- Tested with full pipeline run
- Documented in CHANGELOG

**Use Case:** Quarterly model updates or when 5+ new observations available.

---

## How Slash Commands Work

1. **Create Command:** Place a `.md` file in `.claude/commands/` directory
2. **Add Metadata:** Include `description` and optional `tags` in YAML frontmatter
3. **Write Prompt:** The markdown content becomes the prompt that Claude Code executes
4. **Use Arguments:** Reference command arguments as `$1`, `$2`, etc.
5. **Execute:** Run with `/commandname arg1 arg2`

## Command Development Guidelines

### File Naming
- Use lowercase with hyphens: `my-command.md`
- Avoid special characters except hyphens and underscores

### Frontmatter (YAML)
```yaml
---
description: Short description of what the command does
tags: [category1, category2, category3]
---
```

### Argument Handling
- `$1`, `$2`, `$3`, etc. for positional arguments
- Always document required vs optional arguments
- Provide clear examples in the command documentation

### Best Practices
1. **Clear Documentation:** Explain what the command does, inputs, outputs
2. **Examples:** Provide realistic usage examples
3. **Error Handling:** Describe what happens if files are missing or arguments invalid
4. **Output Format:** Specify the expected output format and location
5. **Token Efficiency:** Design for minimal token usage when possible

## Testing Commands

After creating a new command, test it with:
```bash
/commandname arg1 arg2
```

If the command doesn't appear:
1. Check the file is in `.claude/commands/` directory
2. Verify the filename ends with `.md`
3. Ensure the YAML frontmatter is valid
4. Restart Claude Code session if needed

## Project-Specific Commands

This project includes specialized commands for real estate credit analysis:

### Analysis Commands
- **`/analyzeREissuer`** - Primary credit analysis pipeline (PyMuPDF, 30s, ~$0.30)
- **`/analyzeREissuer-docling`** - Alternative with Docling (20min, higher quality)

### Quality Assurance Commands
- **`/verifyreport`** - Comprehensive report validation (Phase 5 QA)
- **`/verifyconversion`** - PDF conversion quality check (Phase 1 QA)
- **`/verifyextract`** - Extraction accuracy validation (Phase 2 QA)

### Model Management Commands
- **`/updatemodel`** - Update distribution cut prediction model with new training data

### Architecture Highlights
- **Multi-Phase Pipeline:** Avoids context limits through sequential processing
- **Token Optimization:** 0-token phases using pure Python/templating
- **ML Prediction:** Integrated distribution cut risk model (v2.2, F1: 0.870)
- **Quality Controls:** Validation at each phase for accuracy

### Documentation

- **Pipeline Architecture:** `PIPELINE_ARCHITECTURE.md` - Complete input/output flow diagrams
- **Schema Documentation:** `.claude/knowledge/SCHEMA_README.md` - Phase 2 extraction schema
- **Model Documentation:** `models/README.md` - Distribution cut prediction model specs
- **Quick Reference:** `PIPELINE_QUICK_REFERENCE.md` - Phase-by-phase commands

---

**Maintained by:** Credit Analysis Team
**Last Updated:** October 29, 2025
