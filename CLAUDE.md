# CLAUDE.md

Guidance for Claude Code when working with this real estate issuer credit analysis pipeline.

**Version:** 1.0.15 | **Model:** v2.2 (Distribution Cut Prediction)

---

## Project Overview

Generates professional Moody's-style credit reports for Canadian REITs using a 5-phase pipeline:

```
Phase 1: PDF → Markdown (PyMuPDF4LLM + Camelot)
Phase 2: Markdown → JSON extraction (structured data)
Phase 3: Calculate credit metrics (Python)
Phase 4: Generate credit analysis (Agent)
Phase 5: Produce final report (Template-based)
```

**Key Points:**
- Sequential processing (Phase 1 MUST complete before Phase 2)
- Schema-validated JSON between phases
- Token-efficient design (~13K tokens total, ~$0.30 per report)
- Issuer-specific folders with temp/ and reports/ separation

## Commands

**Primary (recommended):**
```bash
/analyzeREissuer @financial-statements.pdf @mda.pdf "Issuer Name"
```

**Individual phases (for debugging):**
```bash
# Phase 1: PDF → Markdown (MUST run first)
python scripts/preprocess_pdfs_enhanced.py --issuer-name "REIT Name" statements.pdf mda.pdf

# Phase 2: Markdown → JSON (run AFTER Phase 1)
python scripts/extract_key_metrics_efficient.py --issuer-name "REIT Name" \
  Issuer_Reports/REIT_Name/temp/phase1_markdown/*.md

# Validate schema (before Phase 3)
python scripts/validate_extraction_schema.py Issuer_Reports/REIT_Name/temp/phase2_extracted_data.json

# Phase 3: Calculate metrics
python scripts/calculate_credit_metrics.py Issuer_Reports/REIT_Name/temp/phase2_extracted_data.json

# Phase 4: Use Task tool to invoke issuer_due_diligence_expert_slim agent

# Phase 5: Generate report
python scripts/generate_final_report.py \
  --template credit_opinion_template_enhanced.md \
  Issuer_Reports/REIT_Name/temp/phase3_calculated_metrics.json \
  Issuer_Reports/REIT_Name/temp/phase4_credit_analysis.md
```

**OpenBB Data Collection (optional):**
```bash
# Market analysis
python scripts/openbb_market_monitor.py --ticker REI-UN.TO

# Macro analysis
python scripts/openbb_macro_monitor.py --output data/macro.json

# Dividend history
python scripts/openbb_data_collector.py --ticker REI-UN.TO
```

## Output Structure

```
Issuer_Reports/{Issuer_Name}/
  temp/                      # Intermediate files
    phase1_markdown/*.md
    phase2_extracted_data.json
    phase3_calculated_metrics.json
    phase4_credit_analysis.md
  reports/                   # Final reports (timestamped)
    {YYYY-MM-DD_HHMMSS}_Credit_Opinion_{Issuer}.md
```

## Critical Schema Rules (Phase 2 → Phase 3)

**MUST follow these rules or Phase 3 will fail:**

1. **Flat structure** for balance_sheet (NO nested objects)
2. **Top-level values** for income_statement and ffo_affo (not nested by period)
3. **No null values** in numeric fields (use 0 instead)
4. **Decimal format** for rates (0-1 range, NOT percentages: 0.878 not 87.8)

**Always validate:**
```bash
python scripts/validate_extraction_schema.py Issuer_Reports/REIT_Name/temp/phase2_extracted_data.json
```

**Schema reference:**
- `.claude/knowledge/phase2_extraction_schema.json` (authoritative)
- `.claude/knowledge/COMPREHENSIVE_EXTRACTION_GUIDE.md` (extraction guide)
- `.claude/knowledge/SCHEMA_README.md` (complete docs)

## Advanced Metrics

### AFCF (Adjusted Free Cash Flow)
```
AFCF = ACFO + Net Cash Flow from Investing
```
- Measures cash after ALL investments (operating + growth)
- More conservative than ACFO
- Self-funding ratio: AFCF / (Debt Service + Distributions)
- < 1.0x = Reliant on capital markets

**See:** `docs/AFCF_Research_Proposal.md`

### Dilution Tracking
Optional detailed tracking of share dilution from convertibles, options, warrants. Phase 3 automatically analyzes when `dilution_detail` is present in Phase 2.

**Materiality thresholds:**
- < 1%: Minimal
- 1-3%: Low
- 3-7%: Moderate
- \> 7%: High (credit concern)

**See:** `.claude/knowledge/SCHEMA_README.md` (Dilution Tracking section)

### Burn Rate & Cash Runway
```
Monthly Burn Rate = (Net Financing Needs - AFCF) / 12
Cash Runway = Available Cash / Monthly Burn Rate
```

**Liquidity risk levels:**
- < 6 months: CRITICAL
- 6-12 months: HIGH
- 12-24 months: MODERATE
- \> 24 months: LOW

**See:** GitHub Issue #7

## Key Files

**Scripts:**
- `scripts/preprocess_pdfs_enhanced.py` - Phase 1
- `scripts/extract_key_metrics_efficient.py` - Phase 2
- `scripts/calculate_credit_metrics.py` - Phase 3
- `scripts/generate_final_report.py` - Phase 5
- `scripts/validate_extraction_schema.py` - Schema validator
- `scripts/openbb_*.py` - Market/macro/dividend data collection

**Configuration:**
- `templates/credit_opinion_template_enhanced.md` - Report template
- `.claude/agents/domain_expert/issuer_due_diligence_expert_slim.md` - Phase 4 agent
- `.claude/commands/analyzeREissuer.md` - Main command
- `.claude/knowledge/*.json` - Schema and extraction guides

## Common Issues

| Error | Cause | Fix |
|-------|-------|-----|
| Missing required field | Nested structure in JSON | Flatten to top level |
| TypeError on null | null in numeric field | Use 0 instead of null |
| Missing noi/interest | Nested quarterly data | Add top-level values for recent period |
| Schema validation fails | Schema not followed | Check `.claude/knowledge/SCHEMA_README.md` |

## Documentation

- `README.md` - Full documentation
- `PIPELINE_QUICK_REFERENCE.md` - Quick reference
- `.claude/knowledge/SCHEMA_README.md` - Schema guide
- `CHANGELOG.md` - Version history

---

## Disclaimer

**IMPORTANT:** This tool is for informational purposes only. NOT investment advice, credit ratings, or recommendations. All outputs MUST be reviewed by qualified credit professionals before use. Machine learning predictions are based on limited historical data and may be inaccurate. Users assume all risks. See README.md for complete disclaimer.

**BY USING THIS TOOL, YOU ACKNOWLEDGE UNDERSTANDING AND ACCEPTANCE OF ALL TERMS.**
