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
- `issuer-name`: **OPTIONAL** issuer name for folder organization (last argument without @ prefix). If not provided, the first PDF filename will be used.

**Example:** `/analyzeREissuer @statements.pdf @mda.pdf "Artis REIT"`

**IMPORTANT:** The issuer name (from arguments or first PDF filename) creates folder structure: `Issuer_Reports/{issuer_name}/temp/` and `Issuer_Reports/{issuer_name}/reports/`

## Overview: What Happens Automatically

**NO MANUAL AGENT INVOCATION NEEDED!**

When you run `/analyzeREissuer`, Claude Code will:
- **Phase 1 (Sequential):** Convert PDFs → markdown (PyMuPDF4LLM + Camelot, foreground)
- **Phase 2 (Sequential):** Extract JSON from markdown (file references, after Phase 1)
- **Phase 3:** Run bash script for calculations
- **Phase 4:** **You invoke the slim agent automatically** (using Task tool)
- **Phase 5:** Run bash script to generate final report

**Key Architecture:** Sequential markdown-first approach ensures token efficiency (~1K prompt vs ~136K direct PDF reading) and reliable extraction with pre-processed, structured data.

**You DO NOT need to manually activate the agent** - the slash command handles everything.

## Multi-Phase Workflow

Execute the following phases sequentially:

### Phase 1: PDF to Markdown Conversion
Convert PDFs to clean, structured markdown using PyMuPDF4LLM + Camelot.

**IMPORTANT:**
- This phase MUST complete before Phase 2 begins
- **DO NOT read PDF files into context** - pass the file paths directly to the Python script
- **DO NOT attempt to determine issuer name from PDF content** - use command arguments or filename only
- The preprocessing script handles all PDF parsing internally

**Steps:**
1. Extract PDF file paths from command arguments (those with @ prefix)
2. Determine issuer name:
   - If last argument has no @ prefix, use it as issuer name
   - Otherwise, extract issuer name from first PDF filename (remove extension and path)
3. Immediately run the preprocessing script (do NOT read PDFs or search for issuer name)

```bash
echo "=========================================="
echo "PHASE 1: PDF TO MARKDOWN CONVERSION"
echo "=========================================="

# Phase 1: Convert PDFs to markdown (FOREGROUND - must complete first)
echo "📄 Phase 1: Converting PDFs to markdown (PyMuPDF4LLM + Camelot)..."
python scripts/preprocess_pdfs_enhanced.py \
  --issuer-name "{ISSUER_NAME}" \
  {PDF_FILES}

if [ $? -ne 0 ]; then
  echo "❌ Phase 1 failed: PDF conversion error"
  exit 1
fi

echo "✅ Phase 1 complete: Markdown files created"
echo "   → Output: ./Issuer_Reports/{ISSUER_NAME_SAFE}/temp/phase1_markdown/"
```

**Output:** `./Issuer_Reports/{issuer}/temp/phase1_markdown/*.md`

### Phase 2: Extract Financial Data from Markdown
Extract structured JSON using file references (context-efficient).

**IMPORTANT:** Runs AFTER Phase 1 completes. Uses markdown files from Phase 1.

```bash
echo ""
echo "=========================================="
echo "PHASE 2: MARKDOWN TO JSON EXTRACTION"
echo "=========================================="

# Phase 2: Extract JSON from markdown files (enhanced v2 with grep-based indexing)
echo "📊 Phase 2: Extracting financial data from markdown (v2 enhanced)..."
python scripts/extract_key_metrics_v2.py \
  --issuer-name "{ISSUER_NAME}" \
  Issuer_Reports/{ISSUER_NAME_SAFE}/temp/phase1_markdown/*.md

if [ $? -ne 0 ]; then
  echo "❌ Phase 2 failed: Extraction error"
  exit 1
fi

echo "✅ Phase 2 complete: JSON data extracted"
echo "   → Output: ./Issuer_Reports/{ISSUER_NAME_SAFE}/temp/phase2_extracted_data.json"
```

**What Phase 2 v2 Does (Enhanced):**
1. **Phase 2a (Indexing):** Use grep to find section locations (0 tokens, <1 second)
2. **Phase 2b (Prompt):** Generate targeted extraction prompt with line ranges
3. **Phase 2c (Extract):** Read ONLY indexed sections using targeted line ranges
4. **Phase 2d (Validate):** Validate each section, auto-expand if fields missing
5. **Checkpointing:** Save validated sections for resumable extraction

**Efficiency:**
- Full files: ~140,000 tokens → Context window errors
- Enhanced v2: ~15,000 tokens (89% savings)
- Progressive enhancement: Auto-expands reads if validation fails
- Checkpoints: Resume failed extractions without re-work

**Output:**
- `./Issuer_Reports/{issuer}/temp/phase2_extracted_data.json`
- `./Issuer_Reports/{issuer}/temp/section_index.json` (cached index)

### Phase 3: Metric Calculations (Safe Python Library)
Calculate credit metrics using pure functions (NO hardcoded data).

```bash
echo ""
echo "=========================================="
echo "PHASE 3: METRIC CALCULATIONS"
echo "=========================================="

# Calculate credit metrics (output auto-generated in same folder as input)
python scripts/calculate_credit_metrics.py \
  Issuer_Reports/{ISSUER_NAME_SAFE}/temp/phase2_extracted_data.json

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
metrics_path = "Issuer_Reports/{ISSUER_NAME_SAFE}/temp/phase3_calculated_metrics.json"
with open(metrics_path) as f:
    metrics = json.load(f)

# Invoke agent using Task tool
# Save output to: Issuer_Reports/{ISSUER_NAME_SAFE}/temp/phase4_credit_analysis.md
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
  Issuer_Reports/{ISSUER_NAME_SAFE}/temp/phase3_calculated_metrics.json \
  Issuer_Reports/{ISSUER_NAME_SAFE}/temp/phase4_credit_analysis.md

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

✅ **Phase 1: Working** - PDF to markdown conversion (PyMuPDF4LLM + Camelot, foreground)
✅ **Phase 2 v2: Working** - Enhanced grep-based extraction with progressive enhancement
  - Grep-based section indexing (0 tokens)
  - Targeted section reads (89% token savings)
  - Progressive enhancement (auto-expands if fields missing)
  - Checkpointing (resumable extraction)
✅ **Phase 3: Working** - Safe calculation library (pure functions)
✅ **Phase 4: Working** - Slim agent for credit analysis (7.7KB agent profile)
✅ **Phase 5: Working** - Report template engine (pure Python, 0 tokens)

**Architecture:** Sequential markdown-first approach with v2 enhanced extraction. Phase 1 completes before Phase 2 begins, ensuring clean pre-processed data and context-efficient extraction.

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

This multi-phase approach reduces token usage by **89%** with enhanced v2 grep-based extraction:
- ❌ Old approach: 121,500 tokens (failed with context errors)
- ✅ New approach (v2): ~13,000 tokens total across all phases
  - Phase 1: 0 tokens (Python preprocessing, PyMuPDF4LLM+Camelot)
  - Phase 2: ~1,000 tokens (v2 grep-based section indexing + targeted reads)
    - Phase 2a: 0 tokens (grep-based indexing)
    - Phase 2b-d: ~1,000 tokens (targeted section reads only)
  - Phase 3: 0 tokens (pure Python calculations)
  - Phase 4: ~12,000 tokens (slim agent credit analysis)
  - Phase 5: 0 tokens (pure Python templating)

**Key Benefits:**
- **v2 Enhancement:** Grep-based indexing eliminates reading entire files
- **Targeted reads:** Read ONLY the ~15K tokens needed vs 140K full files
- **Progressive enhancement:** Auto-expands if fields missing
- **Checkpointing:** Resume failed extractions without re-work

**Total Cost:** ~$0.30 per issuer analysis

## Example Usage

```bash
# Multiple PDFs with explicit issuer name - RECOMMENDED
/analyzeREissuer @ArtisREIT-Q2-25-Consol-FS-Aug-7.pdf @ArtisREIT-Q2-25-MDA-Aug-7.pdf "Artis REIT"

# Single PDF with explicit issuer name
/analyzeREissuer @CapitaLand-Q2-25-FS.pdf "CapitaLand Ascendas REIT"

# Without issuer name (uses first PDF filename)
/analyzeREissuer @ArtisREIT-Q2-25-Consol-FS-Aug-7.pdf @ArtisREIT-Q2-25-MDA-Aug-7.pdf
# Creates folder: Artis_REIT/ (from "ArtisREIT-Q2-25-Consol-FS-Aug-7.pdf")
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
