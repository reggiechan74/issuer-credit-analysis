---
description: Analyze real estate issuer financial statements and generate comprehensive credit opinion report
argument-hint: @financial-statements-pdf [issuer-name]
allowed-tools: Task, Read, Write, Edit, Bash, Glob, Grep
---

# Analyze Real Estate Issuer - Multi-Phase Credit Analysis

You are tasked with performing comprehensive credit analysis on a real estate issuer using a **multi-phase pipeline** to avoid context length limitations.

## Command Arguments

- `$1`: Path to financial statements PDF (use @ prefix for file reference)
- Additional PDFs: Can provide multiple PDF files (e.g., consolidated statements + MD&A)
- `issuer-name`: **REQUIRED** issuer name for folder organization (last argument without @ prefix)

**Example:** `/analyzeREissuer @statements.pdf @mda.pdf "Artis REIT"`

**IMPORTANT:** You must extract the issuer name from the command arguments and pass it to all phases using `--issuer-name` parameter. The issuer name creates folder structure: `Issuer_Reports/{issuer_name}/temp/` and `Issuer_Reports/{issuer_name}/reports/`

## Overview: What Happens Automatically

**NO MANUAL AGENT INVOCATION NEEDED!**

When you run `/analyzeREissuer`, Claude Code will:
- **Phase 1:** Run bash script to convert PDFs → markdown
- **Phase 2:** Extract financial data (you handle this directly, no API key needed)
- **Phase 3:** Run bash script for calculations
- **Phase 4:** **You invoke the slim agent automatically** (using Task tool)
- **Phase 5:** Run bash script to generate final report

**You DO NOT need to manually activate the agent** - the slash command handles everything.

## Multi-Phase Workflow

Execute the following phases sequentially:

### Phase 1: PDF Preprocessing (markitdown)
Convert PDF(s) to markdown format.

**IMPORTANT:** Before running Phase 1, extract the issuer name from command arguments.

**Steps:**
1. Identify all PDF arguments (those with @ prefix)
2. Identify issuer name (last argument without @ prefix, or ask user if not provided)
3. Pass issuer name to script using `--issuer-name` parameter

```bash
echo "=========================================="
echo "PHASE 1: PDF PREPROCESSING"
echo "=========================================="

# Convert PDFs to markdown (auto-creates folder: Issuer_Reports/{issuer_name}/temp/phase1_markdown)
python scripts/preprocess_pdfs_markitdown.py \
  --issuer-name "{ISSUER_NAME}" \
  {PDF_FILES}

if [ $? -ne 0 ]; then
  echo "❌ Phase 1 failed: PDF preprocessing error"
  exit 1
fi

echo "✅ Phase 1 complete: Markdown files created in Issuer_Reports/{ISSUER_NAME}/temp/phase1_markdown/"
```

**Output Structure:**
```
Issuer_Reports/
  {Issuer_Name}/
    temp/
      phase1_markdown/
        {pdf1}.md
        {pdf2}.md
```

### Phase 2: Financial Data Extraction (Claude Code)
Extract structured data using Claude Code (no API key required).

**Process:**
1. Run extraction script with issuer name and markdown files
2. Script creates extraction prompt
3. Read the prompt and extract financial data according to schema
4. Save JSON to issuer's temp folder

```bash
echo ""
echo "=========================================="
echo "PHASE 2: FINANCIAL DATA EXTRACTION"
echo "=========================================="

# Create extraction prompt
python scripts/extract_key_metrics.py \
  --issuer-name "{ISSUER_NAME}" \
  ./Issuer_Reports/{ISSUER_NAME_SAFE}/temp/phase1_markdown/*.md

# Read prompt and perform extraction (you handle this step directly)
```

**Manual Steps (Claude Code handles automatically):**
1. Read the prompt from `./Issuer_Reports/{issuer}/temp/phase2_extraction_prompt.txt`
2. Extract the financial data according to the prompt schema
3. Save JSON to `./Issuer_Reports/{issuer}/temp/phase2_extracted_data.json`

**Required JSON Schema:** issuer_name, reporting_date, balance_sheet (assets, liabilities, debt), income_statement (revenue, NOI, interest), ffo_affo (FFO, AFFO, distributions), portfolio (occupancy, NOI growth)

**Output:** `./Issuer_Reports/{issuer}/temp/phase2_extracted_data.json`

### Phase 3: Metric Calculations (Safe Python Library)
Calculate credit metrics using pure functions (NO hardcoded data).

```bash
echo ""
echo "=========================================="
echo "PHASE 3: METRIC CALCULATIONS"
echo "=========================================="

# Calculate credit metrics (output auto-generated in same folder as input)
python scripts/calculate_credit_metrics.py \
  ./Issuer_Reports/{ISSUER_NAME_SAFE}/temp/phase2_extracted_data.json

if [ $? -ne 0 ]; then
  echo "❌ Phase 3 failed: Calculation error"
  exit 1
fi

echo "✅ Phase 3 complete: Credit metrics calculated"
echo "   → Output: ./Issuer_Reports/{ISSUER_NAME_SAFE}/temp/phase3_calculated_metrics.json"
```

**Output:** `./Issuer_Reports/{issuer}/temp/phase3_calculated_metrics.json` (auto-generated)

### Phase 4: Credit Analysis (Slim Agent)
**Status:** ✅ Implemented

Generate qualitative credit assessment using slim agent.

**IMPORTANT:** This phase requires Claude Code to invoke the agent using the Task tool.

After Phase 3 completes:
1. Load the Phase 3 metrics from `./Issuer_Reports/{issuer}/temp/phase3_calculated_metrics.json`
2. Create the extraction prompt for the agent
3. Invoke `issuer_due_diligence_expert_slim` agent using Task tool with the metrics
4. Save the agent's analysis to `./Issuer_Reports/{issuer}/temp/phase4_credit_analysis.md`

**Agent Configuration:**
- **Agent:** `issuer_due_diligence_expert_slim`
- **Input:** Phase 3 calculated metrics JSON
- **Output:** Qualitative credit assessment markdown (save to phase4_credit_analysis.md)
- **Token usage:** ~12,000 tokens
- **Focus:** 5-factor scorecard, strengths/challenges, rating outlook

**Steps:**
```python
# Read metrics
metrics_path = "./Issuer_Reports/{ISSUER_NAME_SAFE}/temp/phase3_calculated_metrics.json"
with open(metrics_path) as f:
    metrics = json.load(f)

# Invoke agent using Task tool
# Save output to: ./Issuer_Reports/{ISSUER_NAME_SAFE}/temp/phase4_credit_analysis.md
```

**Output:** `./Issuer_Reports/{issuer}/temp/phase4_credit_analysis.md`

You should invoke the agent directly rather than running a bash script for this phase.

### Phase 5: Report Generation (Pure Python Templating)
**Status:** ✅ Implemented

Generate comprehensive final credit opinion report with ET timestamp.

```bash
echo ""
echo "=========================================="
echo "PHASE 5: REPORT GENERATION (0 TOKENS)"
echo "=========================================="

# Generate final credit opinion report (auto-saves to reports/ folder with timestamp)
python scripts/generate_final_report.py \
  ./Issuer_Reports/{ISSUER_NAME_SAFE}/temp/phase3_calculated_metrics.json \
  ./Issuer_Reports/{ISSUER_NAME_SAFE}/temp/phase4_credit_analysis.md

if [ $? -ne 0 ]; then
  echo "❌ Phase 5 failed: Report generation error"
  exit 1
fi

echo "✅ Phase 5 complete: Final credit opinion report generated"
echo "   → Output: ./Issuer_Reports/{ISSUER_NAME_SAFE}/reports/{timestamp}_Credit_Opinion_{issuer}.md"
echo "   → Report length: ~17,000 characters"
echo "   → Token usage: 0 tokens (pure templating)"
```

**Characteristics:**
- **Input:** Phase 3 calculated metrics JSON + Phase 4 credit analysis markdown
- **Output:** Comprehensive Moody's-style credit opinion report with ET timestamp
- **Location:** Automatically saved to `./Issuer_Reports/{issuer}/reports/` folder
- **Filename:** `{YYYY-MM-DD_HHMMSS}_Credit_Opinion_{Issuer_Name}.md`
- **Token usage:** 0 tokens (pure Python templating)
- **Execution time:** <1 second
- **Report sections:** Executive Summary, Credit Strengths/Challenges, Rating Outlook, Upgrade/Downgrade Factors, Key Indicators, 5-Factor Scorecard, Detailed Analysis, Liquidity, ESG, Methodology, Appendices

**Output Structure:**
```
Issuer_Reports/
  {Issuer_Name}/
    temp/
      phase1_markdown/
      phase2_extracted_data.json
      phase2_extraction_prompt.txt
      phase3_calculated_metrics.json
      phase4_agent_prompt.txt
      phase4_credit_analysis.md
    reports/
      2025-10-17_153045_Credit_Opinion_Artis_Real_Estate_Investment_Trust.md
      2025-10-18_091230_Credit_Opinion_Artis_Real_Estate_Investment_Trust.md
```

## Current Implementation Status

✅ **Phase 1: Working** - PDF to markdown conversion (markitdown)
✅ **Phase 2: Working** - LLM extraction with validation
✅ **Phase 3: Working** - Safe calculation library (pure functions)
✅ **Phase 4: Working** - Slim agent for credit analysis (7.7KB agent profile)
✅ **Phase 5: Working** - Report template engine (pure Python, 0 tokens)

## Success Indicators

After Phase 5 completes successfully, you will have the following folder structure:

```
Issuer_Reports/
  {Issuer_Name}/
    temp/
      phase1_markdown/*.md        - Markdown versions of financial statements
      phase2_extracted_data.json  - Structured financial data
      phase2_extraction_prompt.txt - Extraction prompt (for debugging)
      phase3_calculated_metrics.json - Comprehensive credit metrics
      phase4_agent_prompt.txt     - Agent invocation prompt (for review/debugging)
      phase4_credit_analysis.md   - Qualitative credit assessment with scorecard
    reports/
      {timestamp}_Credit_Opinion_{issuer}.md - Final timestamped credit opinion report (~17,000 characters)
```

**Key outputs:**
- **temp/** folder contains all intermediate files (can be cleaned up after analysis)
- **reports/** folder contains timestamped final reports (permanent archive)

## Token Usage Optimization

This multi-phase approach reduces token usage by **85%**:
- ❌ Old approach: 121,500 tokens (failed with context errors)
- ✅ New approach: 18,000 tokens total across all phases
  - Phase 1: 0 tokens (markitdown preprocessing)
  - Phase 2: ~6,000 tokens (LLM extraction with validation)
  - Phase 3: 0 tokens (pure Python calculations)
  - Phase 4: ~12,000 tokens (slim agent credit analysis)
  - Phase 5: 0 tokens (pure Python templating)

**Total Cost:** ~$0.45 per issuer analysis

## Example Usage

**IMPORTANT:** Always provide issuer name as the last argument (without @ prefix).

```bash
# Multiple PDFs (financial statements + MD&A) - RECOMMENDED
/analyzeREissuer @ArtisREIT-Q2-25-Consol-FS-Aug-7.pdf @ArtisREIT-Q2-25-MDA-Aug-7.pdf "Artis REIT"

# Single PDF
/analyzeREissuer @CapitaLand-Q2-25-FS.pdf "CapitaLand Ascendas REIT"

# Complex issuer name with spaces
/analyzeREissuer @statements.pdf @mda.pdf "Allied Properties Real Estate Investment Trust"
```

**What gets created:**
```
Issuer_Reports/
  Artis_REIT/                # Sanitized folder name (spaces → underscores)
    temp/
      phase1_markdown/
      phase2_extracted_data.json
      ...
    reports/
      2025-10-17_153045_Credit_Opinion_Artis_REIT.md
```

## Important Notes

### Safety Features
- Phase 3 calculation library has **NO hardcoded data** - completely safe
- All functions require explicit input and fail loudly if data missing
- Validation checks catch extraction errors before calculations
- Issuer name logged to console for verification

### Evidence Quality
- Phase 2 validation marks data quality (strong/moderate/limited)
- Automated checks include: balance sheet balancing, NOI margins, occupancy rates
- Warnings flagged but don't block processing

### Professional Caveats
- This is analysis, not investment advice
- Requires credit committee review
- Quality depends on input data completeness
- Forecasts are estimates based on assumptions

## Error Handling

Each phase exits with non-zero status on failure:
- Phase 1 fails: Check PDF is valid and readable
- Phase 2 fails: Check validation errors in output JSON
- Phase 3 fails: Check that Phase 2 output has required fields

## Next Steps

After running all 5 phases successfully:
1. Review `Final_Credit_Opinion_Report.md` for comprehensive credit analysis
2. Validate key metrics against source financial statements
3. Professional review by qualified credit analyst recommended
4. Use as input for credit committee discussion

**Important:** This is credit analysis, NOT investment advice. Final rating decisions require credit committee review and approval.
