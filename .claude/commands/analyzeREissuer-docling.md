---
description: Analyze real estate issuer financial statements and generate comprehensive credit opinion report (Docling pipeline - slower but cleaner)
project: true
---

# Real Estate Issuer Credit Analysis - Docling Pipeline

Execute the full 5-phase credit analysis pipeline using **Docling** for PDF conversion (Phase 1 alternative).

**Key Differences from /analyzeREissuer:**
- **PDF Conversion**: Docling (cleaner, compact tables) vs PyMuPDF4LLM + Camelot (faster, enhanced metadata)
- **Processing Time**: ~20 minutes vs ~90 seconds (2 PDFs)
- **Use Case**: Overnight batch processing, cleaner extraction testing

**When to use this command:**
- Overnight/batch processing (time not critical)
- Testing if cleaner markdown improves Phase 2 extraction
- Fallback if PyMuPDF4LLM has issues with specific PDFs

## Usage

```
/analyzeREissuer-docling @financial-statements.pdf @mda.pdf "Issuer Name"
```

## Pipeline Phases

**Phase 1: PDF → Markdown (Docling FAST mode)**
- Convert PDFs using Docling with TableFormerMode.FAST
- ~9.6 minutes per 48-page PDF
- Output: Clean, compact markdown (4 columns vs 14)
- No cleanup/enhancement needed

**Phase 2: Markdown → JSON Extraction**
- Same as existing pipeline (file references, ~1K tokens)
- Extract financial data from markdown files

**Phase 3: Calculate Credit Metrics**
- Same as existing pipeline (pure Python, 0 tokens)
- Calculate FFO, AFFO, ACFO, AFCF, coverage ratios

**Phase 3.5: Data Enrichment (OPTIONAL)**
- Same as existing pipeline (pure Python + OpenBB APIs)
- Enrich with market risk, macro environment, distribution cut prediction
- Graceful degradation if ticker not found or enrichment fails

**Phase 4: Credit Analysis**
- Same as existing pipeline (issuer_due_diligence_expert_slim agent, enhanced with Issue #40)
- Generate qualitative credit assessment with enriched data when available

**Phase 5: Generate Final Report**
- Same as existing pipeline (template-based, 0 tokens)
- Produce comprehensive credit opinion markdown report

## Implementation

1. **Validate inputs**
   - Verify PDF files exist and are readable
   - Sanitize issuer name for folder structure

2. **Phase 1: Run Docling conversion**
   ```bash
   python scripts/preprocess_pdfs_docling.py \
     --issuer-name "{issuer_name}" \
     {pdf_file_1} {pdf_file_2}
   ```
   - Creates `Issuer_Reports/{Issuer_Name}/temp/phase1_markdown/*.md`
   - Expected time: ~19 minutes for 2 PDFs

3. **Phase 2: Extract JSON from markdown**
   ```bash
   python scripts/extract_key_metrics_efficient.py \
     --issuer-name "{issuer_name}" \
     Issuer_Reports/{Issuer_Name}/temp/phase1_markdown/*.md
   ```
   - Uses file references (~1K tokens)
   - Creates `phase2_extracted_data.json`

4. **Validate schema**
   ```bash
   python scripts/validate_extraction_schema.py \
     Issuer_Reports/{Issuer_Name}/temp/phase2_extracted_data.json
   ```

5. **Phase 3: Calculate metrics**
   ```bash
   python scripts/calculate_credit_metrics.py \
     Issuer_Reports/{Issuer_Name}/temp/phase2_extracted_data.json
   ```
   - Creates `phase3_calculated_metrics.json`

5.5. **Phase 3.5: Enrich with market/macro/prediction data (OPTIONAL)**
   ```bash
   # Extract ticker from Phase 2 data
   TICKER=$(grep -oP '"ticker":\s*"\K[^"]+' Issuer_Reports/{Issuer_Name}/temp/phase2_extracted_data.json 2>/dev/null || echo "")

   if [ -n "$TICKER" ]; then
     python scripts/enrich_phase4_data.py \
       --ticker "$TICKER" \
       --phase3-file Issuer_Reports/{Issuer_Name}/temp/phase3_calculated_metrics.json \
       --output Issuer_Reports/{Issuer_Name}/temp/phase4_enriched_data.json
   fi
   ```
   - Creates `phase4_enriched_data.json` (if ticker found and enrichment succeeds)
   - Gracefully skips if no ticker or enrichment fails

6. **Phase 4: Invoke credit analysis agent**
   - Use Task tool with `issuer_due_diligence_expert_slim` agent
   - Agent uses enriched data if available, otherwise standard metrics
   - Creates `phase4_credit_analysis.md`

7. **Phase 5: Generate final report**
   ```bash
   # Use enriched data if available (from Phase 3.5), otherwise fall back to standard metrics
   ENRICHED_PATH="Issuer_Reports/{Issuer_Name}/temp/phase4_enriched_data.json"
   STANDARD_PATH="Issuer_Reports/{Issuer_Name}/temp/phase3_calculated_metrics.json"

   if [ -f "$ENRICHED_PATH" ]; then
     METRICS_FILE="$ENRICHED_PATH"
     echo "✅ Using enriched data (includes market/macro/prediction sections)"
   else
     METRICS_FILE="$STANDARD_PATH"
     echo "⚠️  Using standard metrics only"
   fi

   python scripts/generate_final_report.py \
     --template credit_opinion_template.md \
     "$METRICS_FILE" \
     Issuer_Reports/{Issuer_Name}/temp/phase4_credit_analysis.md
   ```
   - Creates timestamped report in `Issuer_Reports/{Issuer_Name}/reports/`
   - **Automatically uses enriched data** if Phase 3.5 succeeded (includes market/macro/prediction sections)
   - **New in v1.0.13:** Structural Considerations section now auto-populated from Phase 4 content

## Expected Output

```
Issuer_Reports/
  {Issuer_Name}/
    temp/
      phase1_markdown/
        Financial_Statements.md  (Docling output - clean tables)
        MDA.md                   (Docling output - compact format)
      phase2_extracted_data.json
      phase2_extraction_prompt.txt
      phase3_calculated_metrics.json
      phase4_enriched_data.json    (if Phase 3.5 succeeded)
      phase4_agent_prompt.txt
      phase4_credit_analysis.md
    reports/
      {YYYY-MM-DD_HHMMSS}_Credit_Opinion_{Issuer}.md
```

## Performance Comparison

| Pipeline | Phase 1 Time | Total Time | Output Format |
|----------|--------------|------------|---------------|
| **Existing (/analyzeREissuer)** | 30s | ~90s | Enhanced (14 columns, metadata) |
| **Docling (this command)** | 19min | ~20min | Clean (4 columns, compact) |

## Error Handling

- PDF file not found → Clear error message with file paths
- Schema validation failure → Show validation errors, halt pipeline
- Agent invocation failure → Save prompt for debugging
- Phase failures → Stop pipeline, preserve intermediate outputs

## Notes

- All phases after Phase 1 are **identical** to existing pipeline
- Docling output is compatible with existing Phase 2-5 scripts
- Use existing pipeline (`/analyzeREissuer`) for interactive/fast analysis
- Use this pipeline for batch jobs or cleaner extraction testing



Expected time: ~20 minutes
