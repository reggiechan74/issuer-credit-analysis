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
/analyzeREissuer @ArtisREIT-Q2-25-Consol-FS-Aug-7.pdf @ArtisREIT-Q2-25-MDA-Aug-7.pdf "Artis REIT"
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

**Token Usage:** ~18,000 tokens total (~$0.45 per analysis)

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
/verifyreport "Artis REIT"
/verifyreport "Artis REIT" "2025-10-17_125408_Credit_Opinion_Artis_Real_Estate_Investment_Trust.md"
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

- **Credit Analysis Pipeline:** Multi-phase approach to avoid context limits
- **Quality Assurance:** Validation and verification workflows
- **Token Optimization:** 0-token phases using pure Python/templating

For detailed methodology, see: `/docs/METHODOLOGY.md`

---

**Maintained by:** Credit Analysis Team
**Last Updated:** October 2025
