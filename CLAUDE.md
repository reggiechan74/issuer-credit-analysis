# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Version:** 1.0.4
**Last Updated:** 2025-10-17
**Pipeline Version:** 1.0.4 (Sequential markdown-first extraction - proven architecture)

## Project Overview

Real estate issuer credit analysis pipeline that generates professional Moody's-style credit opinion reports through a 5-phase architecture. The system reduces token usage by 85% (from 121,500 to ~18,000 tokens) while maintaining comprehensive analysis quality.

**Key Design Philosophy:**
- Multi-phase pipeline avoids context length limitations
- **Sequential processing: PDF→Markdown→JSON** (Phase 1 must complete before Phase 2)
- Phase 2 uses file references (~1K tokens) instead of embedding markdown (~140K tokens)
- Each phase has zero or minimal token usage (only Phase 4 uses ~12K tokens)
- Issuer-specific folder organization with temp/reports separation
- Schema-validated JSON ensures phase compatibility

**Why Markdown-First Architecture:**
- ✅ Token efficient: File references (~1K) vs reading PDFs directly (~136K tokens)
- ✅ Context preservation: Leaves room for extraction logic and validation
- ✅ Pre-processed data: PyMuPDF4LLM+Camelot creates clean, structured tables
- ✅ Reliable: Proven architecture that doesn't exhaust context window

## Commands

### Running Credit Analysis

**Primary command (recommended):**
```bash
/analyzeREissuer @financial-statements.pdf @mda.pdf "Issuer Name"
```
This slash command automatically executes all 5 phases sequentially.

**Individual phases (for debugging):**

```bash
# Phase 1: PDF → Markdown (MUST run first)
python scripts/preprocess_pdfs_enhanced.py --issuer-name "Artis REIT" statements.pdf mda.pdf

# Phase 2: Markdown → JSON (run AFTER Phase 1 completes)
python scripts/extract_key_metrics_efficient.py --issuer-name "Artis REIT" \
  Issuer_Reports/Artis_REIT/temp/phase1_markdown/*.md

# Validate schema (before Phase 3)
python scripts/validate_extraction_schema.py Issuer_Reports/Artis_REIT/temp/phase2_extracted_data.json

# Phase 3: JSON → Calculated metrics
python scripts/calculate_credit_metrics.py Issuer_Reports/Artis_REIT/temp/phase2_extracted_data.json

# Phase 4: Metrics → Credit analysis (invoke issuer_due_diligence_expert_slim agent via Task tool)

# Phase 5: Generate final report
python scripts/generate_final_report.py \
  --template credit_opinion_template_enhanced.md \
  Issuer_Reports/Artis_REIT/temp/phase3_calculated_metrics.json \
  Issuer_Reports/Artis_REIT/temp/phase4_credit_analysis.md
```

### Testing

```bash
# Run all tests
pytest tests/

# Run specific phase tests
pytest tests/test_phase3_calculations.py -v

# Run single test with output
pytest tests/test_phase3_calculations.py::test_calculate_leverage_metrics -v -s

# Coverage report
pytest tests/ --cov=scripts --cov-report=html
```

### Schema Validation

```bash
# Validate Phase 2 extraction before Phase 3
python scripts/validate_extraction_schema.py <path_to_json>

# Example
python scripts/validate_extraction_schema.py \
  Issuer_Reports/Artis_REIT/temp/phase2_extracted_data.json
```

## Architecture

### 5-Phase Pipeline (v1.0.x - Sequential Markdown-First)

```
Phase 1 (PDF→MD)  →  Phase 2 (MD→JSON)  →  Phase 3 (Calc)  →  Phase 4 (Agent)  →  Phase 5 (Report)
PyMuPDF4LLM+Camelot  File refs (~1K tok)    Pure Python        Slim Agent (12K)    Template (0 tok)
0 tokens, 10-15s     Context-efficient      0 tokens           Credit analysis     Final report
```

**Phase Responsibilities:**
1. **Phase 1** (Sequential): Convert PDFs to markdown using PyMuPDF4LLM + Camelot
   - Creates clean, structured markdown with proper table formatting
   - Required before Phase 2 (MUST complete first)
   - 0 tokens, ~10-15 seconds
2. **Phase 2** (Sequential): Extract structured JSON from markdown files
   - Uses file references (~1K tokens) instead of embedding content
   - Reads markdown files via Claude Code's Read tool
   - Context-efficient approach leaves room for extraction logic
3. **Phase 3**: Calculate credit metrics using pure Python (NO hardcoded data)
4. **Phase 4**: Generate qualitative credit assessment via `issuer_due_diligence_expert_slim` agent
5. **Phase 5**: Template-based final report generation using markdown + metrics

**Why Sequential (Not Parallel):**
- Phase 2 needs Phase 1's markdown output to exist before extraction begins
- Markdown-first ensures clean, pre-processed data for reliable extraction
- File references keep token usage minimal while preserving context for analysis

### Output Structure

```
Issuer_Reports/
  {Issuer_Name}/              # Folder name sanitized (spaces→underscores)
    temp/                     # Intermediate files (deletable)
      phase1_markdown/*.md
      phase2_extracted_data.json
      phase2_extraction_prompt.txt
      phase3_calculated_metrics.json
      phase4_agent_prompt.txt
      phase4_credit_analysis.md
    reports/                  # Final reports (permanent archive)
      {YYYY-MM-DD_HHMMSS}_Credit_Opinion_{Issuer}.md
```

**Important:** Each issuer gets its own folder. Reports are timestamped for versioning.

### Critical Schema Compliance (Phase 2 → Phase 3)

Phase 3 calculations expect a **specific JSON schema** from Phase 2. Schema violations cause runtime errors.

**Key Schema Rules:**

1. **Flat structure for balance_sheet** (NO nested objects):
```json
// ✅ CORRECT
{"balance_sheet": {"total_assets": 123, "cash": 45}}

// ❌ WRONG (causes KeyError)
{"balance_sheet": {"assets": {"total_assets": 123}}}
```

2. **Top-level values required** for income_statement and ffo_affo:
```json
// ✅ CORRECT
{"income_statement": {"noi": 30729, "interest_expense": 16937, "revenue": 59082}}

// ❌ WRONG (causes KeyError)
{"income_statement": {"q2_2025": {"noi": 30729}}}
```

3. **No null values** in numeric fields (use 0):
```json
// ✅ CORRECT
{"portfolio": {"total_gla_sf": 0}}

// ❌ WRONG (causes TypeError: unsupported operand type(s) for /: 'NoneType' and 'int')
{"portfolio": {"total_gla_sf": null}}
```

4. **Decimal format** for rates (0-1 range, NOT percentages):
```json
// ✅ CORRECT
{"portfolio": {"occupancy_rate": 0.878}}  // 87.8%

// ❌ WRONG
{"portfolio": {"occupancy_rate": 87.8}}
```

**Schema Files:**
- `.claude/knowledge/phase2_extraction_schema.json` - JSON Schema specification
- `.claude/knowledge/phase2_extraction_template.json` - Template with comments
- `.claude/knowledge/SCHEMA_README.md` - Complete documentation with examples

**Always validate Phase 2 output before Phase 3:**
```bash
python scripts/validate_extraction_schema.py <json_file>
```

## Agent Invocation (Phase 4)

Phase 4 requires invoking the `issuer_due_diligence_expert_slim` agent via the Task tool:

```python
# Read Phase 3 metrics
with open("Issuer_Reports/Artis_REIT/temp/phase3_calculated_metrics.json") as f:
    metrics = json.load(f)

# Invoke agent with Task tool
# Agent analyzes metrics and generates credit assessment
# Save output to: Issuer_Reports/Artis_REIT/temp/phase4_credit_analysis.md
```

**Agent Profile:** `.claude/agents/domain_expert/issuer_due_diligence_expert_slim.md` (7.7KB)

**Key Enhancement (v1.0.1):** The slim agent now uses parallel web searches for peer comparison research in Section 9, researching 3-4 comparable REITs simultaneously instead of sequentially for improved performance.

**DO NOT** run Python scripts for Phase 4 - use the Task tool to invoke the agent directly.

## Key Files

**Pipeline Scripts:**
- `scripts/preprocess_pdfs_enhanced.py` - Phase 1: PDF→Markdown (PyMuPDF4LLM + Camelot)
- `scripts/extract_key_metrics_efficient.py` - Phase 2: PDF/Markdown→JSON extraction
- `scripts/calculate_credit_metrics.py` - Phase 3: Metric calculations
- `scripts/generate_final_report.py` - Phase 5: Report generation

**Validation:**
- `scripts/validate_extraction_schema.py` - Schema validator (use before Phase 3)

**Templates:**
- `templates/credit_opinion_template_enhanced.md` - Final report template (recommended)

**Agent Definitions:**
- `.claude/agents/domain_expert/issuer_due_diligence_expert_slim.md` - Phase 4 credit analysis agent

**Slash Commands:**
- `.claude/commands/analyzeREissuer.md` - Main analysis command

**Configuration:**
- `config/extraction_config.yaml` - Pipeline configuration (v1.0.x defaults: sequential markdown-first)

## Safety Features

**Phase 3 Calculation Safety:**
- NO hardcoded financial data anywhere
- All functions require explicit input (no defaults)
- Fails loudly with KeyError/ValueError if data missing
- Includes issuer identification in all outputs

**Validation Checks:**
- Balance sheet balancing (Assets = Liabilities + Equity)
- NOI margins (40-70% typical for REITs)
- Occupancy rates (0-100%)
- Interest coverage minimums

## Common Issues

### "Missing required field: balance_sheet.total_assets"
**Cause:** Nested structure in balance_sheet
**Fix:** Flatten balance_sheet fields to top level (see schema rules above)

### "TypeError: unsupported operand type(s) for /: 'NoneType' and 'int'"
**Cause:** null value in numeric field (usually portfolio.total_gla_sf)
**Fix:** Replace null with 0

### "Missing required field: income_statement.noi"
**Cause:** Only nested quarterly data provided
**Fix:** Add top-level noi/interest_expense/revenue fields for most recent period

### Phase 2 extraction not following schema
**Solution:**
1. Check `.claude/knowledge/SCHEMA_README.md` for correct format
2. Re-run extraction with updated prompt
3. Validate with `validate_extraction_schema.py` before Phase 3

## Documentation

- **README.md** - Full project documentation
- **PIPELINE_QUICK_REFERENCE.md** - Quick reference for pipeline operations
- **.claude/knowledge/SCHEMA_README.md** - Complete schema documentation with examples
- **tests/** - Comprehensive test fixtures and examples

## Token Usage & Cost

| Phase | Tokens | Cost | Time |
|-------|--------|------|------|
| Phase 1 (sequential) | 0 | $0.00 | 10-15s (foreground) |
| Phase 2 (sequential) | ~1,000* | $0.00 | 5-10s (after Phase 1) |
| Phase 3 | 0 | $0.00 | <1s |
| Phase 4 | 12,000 | ~$0.30 | 30-60s |
| Phase 5 | 0 | $0.00 | <1s |
| **Total** | **~13,000** | **~$0.30** | **~60s** |

*Phase 2 uses file references (~1K prompt tokens), Claude Code reads markdown files directly

**Efficiency vs original approach:**
- Old: 121,500 tokens (~$3.04) with frequent context errors
- v1.0.x: 89% token reduction, reliable execution, 100% success rate

## Professional Disclaimers

This tool provides credit analysis for informational purposes only. It is NOT:
- Investment advice
- A substitute for professional credit analysis
- A guarantee of credit quality or investment returns

All credit decisions require review by qualified analysts and credit committee approval.

---

## Version History

### v1.0.4 (2025-10-17) - Revert to Sequential Markdown-First Architecture
**Major Changes:**
- **REVERTED v1.1.0 parallel PDF approach** (caused context window exhaustion)
- Restored v1.0.x sequential architecture: Phase 1 (PDF→MD) completes before Phase 2 (MD→JSON)
- Config default changed from `pdf_direct` back to `manual` (markdown-first)
- Updated all documentation to reflect correct architecture

**Why the Reversion:**
- ❌ v1.1.0 PDF direct reading consumed ~136K tokens (545KB PDFs)
- ❌ Context exhaustion left no room for extraction logic
- ✅ v1.0.x markdown-first uses ~1K prompt tokens + file references
- ✅ Pre-processed markdown is cleaner and more reliable for extraction

**Architecture:**
- Phase 1 runs FIRST (foreground): PDF → Markdown (PyMuPDF4LLM + Camelot)
- Phase 2 runs SECOND: Markdown → JSON (file references, context-efficient)
- Total tokens: ~13K (vs ~148K for direct PDF reading)

---

See [CHANGELOG.md](CHANGELOG.md) for complete version history.
