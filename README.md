# Real Estate Issuer Credit Analysis Pipeline

**Multi-phase credit analysis system for real estate investment trusts (REITs) using Claude Code agents.**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Version](https://img.shields.io/badge/version-1.0.7-blue.svg)](CHANGELOG.md)

## Overview

This system performs comprehensive credit analysis on real estate issuers (REITs, real estate companies) using a multi-phase pipeline that achieves 99.2% token reduction while generating professional Moody's-style credit opinion reports.

### Key Features

- **5-Phase Sequential Pipeline**: Proven architecture (PDF→Markdown→JSON→Metrics→Analysis→Report)
- **99.2% Token Reduction**: File reference patterns reduce Phase 2 from ~140K to ~1K tokens
- **PyMuPDF4LLM + Camelot Hybrid**: Enhanced PDF extraction with superior table quality (Issue #1 solution)
- **Context-Efficient Phase 2**: File references preserve ~199K tokens for extraction logic
- **Absolute Path Implementation**: Reliable execution from any working directory
- **Organized Output**: Issuer-specific folders with separate temp and reports directories
- **Claude Code Integration**: Uses Claude Code agents for intelligent extraction and analysis
- **Zero-API Dependency**: Works entirely within Claude Code environment (no external API keys needed)
- **Test-Driven Development**: Comprehensive test suite for all phases
- **Production Ready**: Generates professional credit opinion reports with 5-factor scorecard analysis
- **100% Success Rate**: Sequential markdown-first approach prevents context window exhaustion

## Architecture (v1.0.4 - Sequential Markdown-First)

```
Phase 1 (PDF→MD)  →  Phase 2 (MD→JSON)  →  Phase 3 (Calc)  →  Phase 4 (Agent)  →  Phase 5 (Report)
PyMuPDF4LLM+Camelot  File refs (~1K tok)    Pure Python        Slim Agent (12K)    Template (0 tok)
0 tokens, 10-15s     Context-efficient      0 tokens           Credit analysis     Final report
```

### Why Sequential Markdown-First?

| Approach | Phase 2 Token Cost | Context Available | Result |
|----------|-------------------|-------------------|---------|
| **Direct PDF Reading** | ~136K tokens | ~64K remaining | ❌ Context exhausted |
| **Markdown-First (v1.0.4)** | ~1K tokens (file refs) | ~199K remaining | ✅ Reliable extraction |

**Key Benefits:**
- ✅ **99.2% token reduction**: File references (~1K) vs embedding content (~140K tokens)
- ✅ **Enhanced table extraction**: PyMuPDF4LLM + Camelot hybrid captures 113 tables from 75 pages
- ✅ **Context preservation**: Leaves ~199K tokens for extraction logic and validation
- ✅ **Absolute paths**: Reliable execution from any working directory using `Path.cwd()`
- ✅ **Proven reliability**: 100% success rate on production workloads (545KB markdown files)

### Output Structure

```
Issuer_Reports/
  {Issuer_Name}/
    temp/                                    # Intermediate files (can delete)
      phase1_markdown/*.md
      phase2_extracted_data.json
      phase2_extraction_prompt.txt
      phase3_calculated_metrics.json
      phase4_agent_prompt.txt
      phase4_credit_analysis.md
    reports/                                 # Final reports (permanent)
      2025-10-17_153045_Credit_Opinion_{issuer}.md
```

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+ (for Claude Code)
- Git

### Setup

**1. Install Claude Code:**

```bash
# Install Claude Code CLI globally
npm install -g @anthropic-ai/claude-code

# Verify installation
claude-code --version
```

**2. Set up the project:**

```bash
# Clone repository
git clone https://github.com/reggiechan74/issuer-credit-analysis.git
cd issuer-credit-analysis

# Install Python dependencies
pip install -r requirements.txt

# Run tests to verify installation
pytest tests/
```

**3. Start Claude Code:**

```bash
# Open Claude Code in the project directory
claude-code

# Or use the web interface at:
# https://claude.com/claude-code
```

## Configuration (v1.0.4)

Configure the extraction pipeline via `config/extraction_config.yaml`.

### Recommended Settings (Default in v1.0.4)

```yaml
phase1_extraction:
  method: "enhanced"  # PyMuPDF4LLM + Camelot (best table quality)

phase2_extraction:
  method: "manual"  # Markdown→JSON with file references
  manual:
    prompt_strategy: "reference"  # ~1K tokens vs ~140K embedded
```

### Why These Defaults?

| Setting | Token Cost | Context Available | Reliability |
|---------|-----------|-------------------|-------------|
| **manual + reference** | ~1K tokens | ~199K remaining | ✅ 100% success |
| ~~pdf_direct~~ (deprecated) | ~136K tokens | ~64K remaining | ❌ Context exhaustion |

### Alternative: Agent-Based Extraction

For very large files (>10MB), use the agent-based approach:

```yaml
phase2_extraction:
  method: "agent"  # Uses financial_data_extractor agent
  # Cost: ~$0.30 per extraction
```

## Quick Start

### Using Slash Commands (Recommended)

**Complete Credit Analysis:** `/analyzeREissuer`

The simplest way to run the complete pipeline:

```bash
# With Claude Code open in this directory:
/analyzeREissuer @statements.pdf @mda.pdf "Artis REIT"

# The slash command automatically executes all 5 phases:
# 1. Phase 1: PDF → Markdown (PyMuPDF4LLM + Camelot, 113 tables extracted)
# 2. Phase 2: Markdown → JSON (file references, ~1K tokens)
# 3. Phase 3: Calculate metrics (0 tokens, pure Python)
# 4. Phase 4: Credit analysis (slim agent, ~12K tokens)
# 5. Phase 5: Generate report (0 tokens, templating)

# Total time: ~60 seconds | Total cost: ~$0.30
```

**Burn Rate Analysis:** `/burnrate` (New in v1.0.7)

Generate comprehensive cash burn rate and liquidity runway analysis:

```bash
# Using issuer name (searches Issuer_Reports/)
/burnrate "Dream Industrial REIT"

# Using issuer abbreviation
/burnrate DIR

# Using direct path to Phase 2 JSON
/burnrate Issuer_Reports/DIR-Q2-Report-FINAL/temp/phase2_extracted_data.json

# Report includes:
# - Cash burn rate (monthly & annualized)
# - Cash runway (months until depletion)
# - Liquidity risk assessment (CRITICAL/HIGH/MODERATE/LOW)
# - Self-funding ratio and sustainable burn analysis
# - Credit implications and recommended actions
```

### Manual Execution (Individual Phases)

If you prefer to run phases individually:

**Phase 1: PDF → Markdown (MUST run first)**

```bash
# Convert PDFs to clean markdown (PyMuPDF4LLM + Camelot)
python scripts/preprocess_pdfs_enhanced.py \
  --issuer-name "Artis REIT" \
  statements.pdf mda.pdf

# Creates: Issuer_Reports/Artis_REIT/temp/phase1_markdown/*.md
```

**Phase 2: Markdown → JSON (after Phase 1 completes)**

```bash
# Extract financial data using file references (~1K tokens)
python scripts/extract_key_metrics_efficient.py \
  --issuer-name "Artis REIT" \
  Issuer_Reports/Artis_REIT/temp/phase1_markdown/*.md

# Then Claude Code reads the prompt and extracts data
```

**Phase 3: Metric Calculations**
```bash
python scripts/calculate_credit_metrics.py \
  Issuer_Reports/Artis_REIT/temp/phase2_extracted_data.json
```

**Phase 4: Credit Analysis (requires Claude Code agent)**
```python
# Within Claude Code:
# Invoke issuer_due_diligence_expert_slim agent with metrics from Phase 3
```

**Phase 5: Final Report Generation**
```bash
python scripts/generate_final_report.py \
  Issuer_Reports/Artis_REIT/temp/phase3_calculated_metrics.json \
  Issuer_Reports/Artis_REIT/temp/phase4_credit_analysis.md
```

## Usage Examples

### Complete Analysis via Slash Command

```bash
# Example 1: Single REIT with multiple PDFs (recommended)
/analyzeREissuer @financial_statements.pdf @mda.pdf "CapitaLand Ascendas REIT"

# Example 2: Quarterly analysis
/analyzeREissuer @Q2_2025_statements.pdf "Allied Properties REIT"
```

### Manual Phase 1 Execution (if needed)

```bash
# Using PyMuPDF4LLM + Camelot (current default)
python scripts/preprocess_pdfs_enhanced.py \
  --issuer-name "CapitaLand Ascendas REIT" \
  financial_statements.pdf mda.pdf

# Results: 113 tables extracted from 75 pages
# Output: Issuer_Reports/CapitaLand_Ascendas_REIT/temp/phase1_markdown/
```

### Cleanup

```bash
# Remove temporary files after analysis (keeps reports)
rm -rf Issuer_Reports/*/temp/

# Keep everything organized by issuer
ls Issuer_Reports/Artis_REIT/reports/
# Output:
# 2025-10-17_153045_Credit_Opinion_Artis_REIT.md
# 2025-10-18_091230_Credit_Opinion_Artis_REIT.md
```

## Testing

Run the complete test suite:

```bash
# All tests
pytest tests/

# Specific phase
pytest tests/test_phase3_calculations.py -v

# With coverage
pytest tests/ --cov=scripts --cov-report=html
```

**Current Test Status:**
- Phase 1: ✅ All tests passing
- Phase 2: ✅ All tests passing
- Phase 3: ✅ All tests passing
- Phase 4: ✅ All tests passing
- Phase 5: ✅ All tests passing (13/19 active, 6 skipped)

## Agent Profiles

### issuer_due_diligence_expert_slim (Recommended)

**Size:** 7.7KB (85% reduction vs full agent)
**Focus:** Qualitative credit assessment from pre-calculated metrics
**Token Usage:** ~12,000 tokens per analysis
**Version:** 1.0.1 (with parallel peer research)

**Strengths:**
- Fast execution (30-60 seconds)
- Parallel web research for peer comparisons (new in v1.0.1)
- Consistent output format
- Comprehensive 5-factor scorecard including 12 detailed sections
- Evidence-based assessments with proper citations

### issuer_due_diligence_expert (Full Version)

**Size:** 60KB
**Use Cases:** Complex scenarios requiring deep domain knowledge

## Features

### Credit Metrics Calculated

**Leverage Metrics:**
- Debt/Gross Assets (%)
- Net Debt Ratio (%)
- Total Debt, Net Debt, Gross Assets

**REIT Metrics:**
- FFO (Funds From Operations)
- AFFO (Adjusted FFO)
- ACFO (Adjusted Cash Flow from Operations)
- AFCF (Adjusted Free Cash Flow)
- FFO/AFFO per unit
- FFO/AFFO payout ratios
- Distribution coverage

**Coverage Ratios:**
- NOI/Interest Coverage
- EBITDA/Interest Coverage
- Debt Service Coverage
- AFCF Debt Service Coverage
- AFCF Self-Funding Ratio

**Liquidity & Burn Rate Analysis (v1.0.7):**
- Cash burn rate (monthly & annualized)
- Cash runway (months until depletion)
- Liquidity risk assessment (CRITICAL/HIGH/MODERATE/LOW)
- Sustainable burn rate analysis
- Self-funding ratio (AFCF / Net Financing Needs)
- **Key Insight:** Identifies REITs with positive AFCF that still burn cash

### Credit Analysis Sections

The slim agent (v1.0.1) generates comprehensive reports with 12 sections:

1. **Executive Summary** - Rating and credit story
2. **Credit Strengths** - Quantified positive factors
3. **Credit Challenges** - Risk factors with mitigants
4. **Rating Outlook** - Stable/Positive/Negative with timeframe
5. **Upgrade Factors** - Specific thresholds for improvement
6. **Downgrade Factors** - Quantified triggers
7. **5-Factor Scorecard** - Detailed rating methodology
8. **Key Observations** - Portfolio quality, unusual metrics
9. **Peer Comparison** - Parallel web research of 3-4 comparable REITs with citations (new in v1.0.1)
10. **Scenario Analysis** - Base/Upside/Downside/Stress cases with pro forma metrics
11. **Company Background** - Corporate structure, history, portfolio composition
12. **Business Strategy** - Strategic priorities and capital allocation

### Safety Features

- **No Hardcoded Data**: All calculations use explicit inputs
- **Loud Failures**: Invalid data triggers clear error messages
- **Validation Checks**: Balance sheet balancing, NOI margins, occupancy ranges
- **Evidence Quality**: Strong/moderate/limited evidence labels
- **Professional Caveats**: Clear disclaimers on limitations

## Token Usage & Cost

| Phase | Tokens | Cost (approx) | Time | Details |
|-------|--------|---------------|------|---------|
| Phase 1 | 0 | $0.00 | 10-15s | PyMuPDF4LLM + Camelot (113 tables from 75 pages) |
| Phase 2 | ~1,000 | $0.00 | 5-10s | File references (not embedded content) |
| Phase 3 | 0 | $0.00 | <1s | Pure Python calculations |
| Phase 4 | ~12,000 | ~$0.30 | 30-60s | Slim agent credit analysis |
| Phase 5 | 0 | $0.00 | <1s | Template-based report generation |
| **Total** | **~13,000** | **~$0.30** | **~60s** | **99.2% token reduction** |

### Performance Comparison

| Approach | Total Tokens | Cost | Success Rate | Notes |
|----------|-------------|------|--------------|-------|
| **v1.0.4 (Current)** | ~13,000 | $0.30 | 100% | File reference patterns |
| ~~v1.1.0 PDF Direct~~ | ~148,000 | $3.70 | 0% | Context exhaustion (reverted) |
| Original Single-Pass | ~121,500 | $3.04 | ~30% | Frequent context errors |

**Key Achievement:** 99.2% token reduction in Phase 2 alone (~140K → ~1K tokens)

## Project Origin

This project was extracted from the [geniusstrategies](https://github.com/reggiechan74/geniusstrategies) repository, which explores cognitive strategy coaching through AI agents embodying historical geniuses' thinking patterns.

The credit analysis pipeline was developed as a domain expert implementation demonstrating:
- Multi-phase pipeline architecture
- Claude Code agent integration
- Test-driven development practices
- Production-ready financial analysis

## Recent Improvements

### v1.0.7 Updates (Latest)

**Issue #7 - Cash Burn Rate and Liquidity Runway Analysis (Implemented)**
- ✅ 4 new calculation functions: burn rate, cash runway, liquidity risk, sustainable burn
- ✅ New `/burnrate` slash command for comprehensive liquidity analysis
- ✅ 36 tests passing (25 unit + 11 integration)
- ✅ **Critical Discovery:** REITs can have positive AFCF but still burn cash when financing needs exceed free cash flow
- ✅ Production-ready: Tested with Dream Industrial REIT and Artis REIT

**Issue #6 - AFCF (Adjusted Free Cash Flow) Calculations (Implemented)**
- ✅ New metric: AFCF = ACFO + Net Cash Flow from Investing
- ✅ More conservative than ACFO - includes ALL investment activities
- ✅ AFCF coverage ratios: debt service, distributions, self-funding
- ✅ 17 tests passing with comprehensive validation

**Issue #5 - ACFO Implementation (Implemented)**
- ✅ Automated ACFO calculation using REALPAC methodology
- ✅ 17 adjustments to IFRS CFO for normalized operating cash flow
- ✅ Prevents double-counting with AFCF calculations

### v1.0.4 Updates

**Issue #1 - PDF Markdown Conversion (Resolved)**
- ✅ Implemented PyMuPDF4LLM + Camelot hybrid approach
- ✅ Extracts 113 tables from 75-page documents with high fidelity
- ✅ Superior table structure preservation vs MarkItDown

**Issue #2 - Context Length Optimization (Research Complete)**
- ✅ Comprehensive semantic chunking research completed ([docs/SEMANTIC_CHUNKING_RESEARCH.md](docs/SEMANTIC_CHUNKING_RESEARCH.md))
- ✅ Current file reference architecture already achieves 99.2% token reduction
- 📋 Optional semantic chunking planned for v1.1.0 (documents >256KB)
- 🔮 RAG-based approach for v2.0.0 (documents >1MB, future consideration)

**Code Quality Improvements**
- ✅ Absolute path implementation using `Path.cwd()` for reliable execution
- ✅ Fixed property_count field mapping bug (Phase 3 calculations)
- ✅ Enhanced error handling and validation across all phases
- ✅ 100% test passing rate (Phase 1-5)

## Contributing

Contributions welcome! Areas of interest:

- Additional asset classes (corporate bonds, structured finance)
- Enhanced portfolio quality metrics
- Integration with financial data APIs
- Visualization dashboards
- Semantic chunking implementation (v1.1.0 roadmap available in Issue #2)
- Enhanced peer comparison analytics (parallel research implemented in v1.0.1)

## License

GNU General Public License v3.0 (GPL-3.0) - See LICENSE file for details.

This project is licensed under the GPL-3.0, which requires that:
- Source code must be made available when the software is distributed
- Modifications must be released under the same license
- You may use this software for any purpose, but modified versions distributed to others must also be open source under GPL-3.0

For the complete license text, see the [LICENSE](LICENSE) file.

## Disclaimer

**IMPORTANT:** This tool provides credit analysis for informational purposes only. It is NOT:
- Investment advice
- A substitute for professional credit analysis
- A guarantee of credit quality or investment returns
- Approved by credit rating agencies

All credit decisions should be reviewed by qualified credit analysts and approved by appropriate credit committees.

## Support

- **Issues**: [GitHub Issues](https://github.com/reggiechan74/issuer-credit-analysis/issues)
- **Discussions**: [GitHub Discussions](https://github.com/reggiechan74/issuer-credit-analysis/discussions)
- **Original Project**: [geniusstrategies](https://github.com/reggiechan74/geniusstrategies)

---

**Built with Claude Code** | [Documentation](./docs/) | [Examples](./examples/)
