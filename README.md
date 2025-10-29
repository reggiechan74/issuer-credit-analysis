# Real Estate Issuer Credit Analysis Pipeline

**Multi-phase credit analysis system for real estate investment trusts (REITs) using Claude Code agents.**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Version](https://img.shields.io/badge/version-1.0.15-blue.svg)](CHANGELOG.md)
[![Model](https://img.shields.io/badge/model-v2.2-green.svg)](models/README.md)

## What's New in v1.0.15 🎉

### Distribution Cut Prediction Model v2.2 Deployed (October 29, 2025)

✅ **Model v2.2 fixes critical underestimation issue - now accurately predicts distribution cut risk for distressed REITs**

**The Problem with v2.1:**
- REIT A: Predicted 2.1% (Very Low) when actual risk was 67.1% (High)
- Underestimation: 65 percentage points off
- Root cause: Feature distribution mismatch (trained on total AFCF, but Phase 3 calculates sustainable AFCF)

**Model v2.2 Improvements:**
- ✅ **67.1% High risk prediction** for REIT A (was 2.1% Very Low) - aligns with critical distress
- ✅ **Sustainable AFCF methodology** - matches Phase 3 calculations (Issue #40)
- ✅ **28 Phase 3 features** (was 54 with market/macro) - more focused feature set
- ✅ **Validated on 3 REITs** - improvements of +27 to +65 percentage points
- ✅ **Production deployment** - default model path updated, v2.1 archived

**Performance (5-fold CV):**
- F1 Score: 0.870, ROC AUC: 0.930, Accuracy: 87.5%
- Top drivers: monthly_burn_rate, acfo_calculated, available_cash

**See:** [Model v2.2 Documentation](models/README.md) | [Deployment Summary](docs/MODEL_V2.2_DEPLOYMENT_SUMMARY.md) | [Analysis](docs/DISTRIBUTION_CUT_MODEL_DISCREPANCY_ANALYSIS.md)

---

### Previous Updates (v1.0.13)

**Structural Considerations Content Extraction (October 21, 2025)**

✅ **Debt Structure, Security & Collateral, Perpetual Securities sections now auto-populated from Phase 4 analysis**

- **Debt Structure**: Credit facilities, covenant compliance, debt profile
- **Security & Collateral**: Unencumbered asset pool, LTV ratios, recovery estimates
- **Perpetual Securities**: Automatically detected or marked "Not applicable"

**Impact**: +15% report completeness, $0 token cost. See [CHANGELOG.md](CHANGELOG.md).

---

## Overview

This system performs comprehensive credit analysis on real estate issuers (REITs, real estate companies) using a multi-phase pipeline that achieves 99.2% token reduction while generating professional Moody's-style credit opinion reports.

### Key Features

- **5-Phase Sequential Pipeline**: Proven architecture (PDF→Markdown→JSON→Metrics→Analysis→Report)
- **Distribution Cut Prediction**: ML model v2.2 predicts 12-month distribution cut risk (High accuracy: F1=0.87, ROC AUC=0.93)
- **99.2% Token Reduction**: File reference patterns reduce Phase 2 from ~140K to ~1K tokens
- **Dual PDF Conversion Methods**: Choose between speed (PyMuPDF4LLM+Camelot, ~30s) or quality (Docling, ~20min)
- **Market Data Integration**: Automated price stress, volatility, and momentum analysis via OpenBB Platform
- **Macro Environment Tracking**: Bank of Canada and Federal Reserve rate monitoring with credit stress scoring
- **Context-Efficient Phase 2**: File references preserve ~199K tokens for extraction logic
- **Absolute Path Implementation**: Reliable execution from any working directory
- **Organized Output**: Issuer-specific folders with separate temp and reports directories
- **Claude Code Integration**: Uses Claude Code agents for intelligent extraction and analysis
- **Zero-API Dependency**: Core pipeline works entirely within Claude Code (OpenBB optional, $0 cost)
- **Test-Driven Development**: Comprehensive test suite for all phases
- **Production Ready**: Generates professional credit opinion reports with 5-factor scorecard analysis
- **100% Success Rate**: Sequential markdown-first approach prevents context window exhaustion

## Architecture (v1.0.15 - Sequential Markdown-First with ML Prediction)

```
Phase 1        Phase 2          Phase 3         Phase 3.5        Phase 4         Phase 5
PDF→MD    →   MD→JSON     →    Calculations  →  Enrichment  →   Agent      →    Report
PyMuPDF/      File refs        Pure Python      ML Model v2.2    Slim Agent      Template
Docling       (~1K tok)        0 tokens         0 tokens         (12K tok)       (0 tok)
30s-20min     Efficient        FFO/AFFO/ACFO    Cut risk:        Credit          Final
                               AFCF metrics     67% High         analysis        report
```

**Phase 3.5 (Optional - Enrichment):**
- Market risk data (OpenBB Platform): Price stress, volatility, momentum
- Macro environment (Bank of Canada, Federal Reserve): Rate cycles, credit stress
- Distribution history: 10-year dividend history, cut detection, recovery analysis
- **Distribution cut prediction (Model v2.2)**: 12-month cut probability with risk drivers

### Two PDF Conversion Methods (Phase 1)

**Method 1: PyMuPDF4LLM + Camelot (Default - Fast)**
- **Command:** `/analyzeREissuer @statements.pdf @mda.pdf "Issuer Name"`
- **Speed:** ~30 seconds for 2 PDFs (75 pages total)
- **Table Format:** Enhanced 14-column tables with metadata
- **Use Case:** Interactive analysis, fast iteration, production workloads
- **Extraction:** 113 tables from 75 pages, superior to pure PyMuPDF4LLM
- **Output:** 545KB markdown with rich table formatting

**Method 2: Docling (Alternative - Cleaner)**
- **Command:** `/analyzeREissuer-docling @statements.pdf @mda.pdf "Issuer Name"`
- **Speed:** ~20 minutes for 2 PDFs (Docling FAST mode)
- **Table Format:** Compact 4-column tables, cleaner structure
- **Use Case:** Overnight batch processing, cleaner extraction testing
- **Extraction:** Same table coverage, more compact markdown
- **Output:** More concise markdown, easier to parse manually

### PDF Conversion Comparison

| Method | Phase 1 Time | Table Format | Output Size | Best For |
|--------|--------------|--------------|-------------|----------|
| **PyMuPDF4LLM + Camelot** | ~30s | Enhanced (14 cols) | 545KB | Interactive, production |
| **Docling FAST** | ~20min | Compact (4 cols) | Smaller | Batch, testing |

**Both methods produce identical Phase 2-5 outputs** - the choice only affects Phase 1 processing time and markdown structure.

### Why Sequential Markdown-First?

| Approach | Phase 2 Token Cost | Context Available | Result |
|----------|-------------------|-------------------|---------|
| **Direct PDF Reading** | ~136K tokens | ~64K remaining | ❌ Context exhausted |
| **Markdown-First (v1.0.4+)** | ~1K tokens (file refs) | ~199K remaining | ✅ Reliable extraction |

**Key Benefits:**
- ✅ **99.2% token reduction**: File references (~1K) vs embedding content (~140K tokens)
- ✅ **Enhanced table extraction**: Both methods capture 113 tables from 75 pages
- ✅ **Context preservation**: Leaves ~199K tokens for extraction logic and validation
- ✅ **Flexible conversion**: Choose speed (PyMuPDF+Camelot) or quality (Docling) per use case
- ✅ **Absolute paths**: Reliable execution from any working directory using `Path.cwd()`
- ✅ **Proven reliability**: 100% success rate on production workloads

### Distribution Cut Prediction (Model v2.2)

**Predicts 12-month distribution cut probability** for Canadian REITs using logistic regression trained on 24 observations (11 cuts, 13 controls).

**Model Performance:**
- **F1 Score:** 0.870 (5-fold CV) - Excellent balance between precision and recall
- **ROC AUC:** 0.930 - Strong discrimination between cut vs. no-cut
- **Accuracy:** 87.5% - High overall prediction accuracy

**Key Features (Top 5):**
1. **Monthly burn rate** - Cash depletion speed (most predictive)
2. **ACFO calculated** - Sustainable operating cash flow
3. **Available cash** - Immediate liquidity
4. **Total available liquidity** - Cash + undrawn facilities
5. **Self-funding ratio** - AFCF / Total obligations

**Example Predictions:**
| REIT | Cut Probability | Risk Level | Financial Context |
|------|----------------|------------|-------------------|
| **REIT A** | 67.1% | 🔴 High | Cash runway: 1.6 months, Self-funding: -0.61x |
| **REIT B** | 48.5% | 🔴 High | Sustainable AFCF negative |
| **REIT C** | 29.3% | 🟠 Moderate | AFFO payout: 115% |

**What Changed in v2.2:**
- ✅ Fixed 65-point underestimation in severe distress cases
- ✅ Uses sustainable AFCF methodology (aligns with Phase 3)
- ✅ 28 Phase 3 features only (removed market/macro for simplicity)
- ✅ Deployed to production (Oct 29, 2025)

**Risk Classification:**
- 🟢 Very Low: 0-10% probability
- 🟡 Low: 10-25%
- 🟠 Moderate: 25-50%
- 🔴 High: 50-75%
- 🚨 Very High: 75-100%

**See:** [Model Documentation](models/README.md) | [Deployment Analysis](docs/MODEL_V2.2_DEPLOYMENT_SUMMARY.md)

### Output Structure

```
Issuer_Reports/
  {Issuer_Name}/
    temp/                                    # Intermediate files (can delete)
      phase1_markdown/*.md                   # Converted PDFs (markdown format)
      phase2_extracted_data.json             # Extracted financial data
      phase2_extraction_prompt.txt           # Extraction prompt for debugging
      phase3_calculated_metrics.json         # Calculated metrics (FFO/AFFO/ACFO/AFCF)
      phase4_enriched_data.json              # Phase 3 + market/macro/prediction (optional)
      phase4_agent_prompt.txt                # Agent prompt for debugging
      phase4_credit_analysis.md              # Qualitative credit assessment
    reports/                                 # Final reports (permanent)
      2025-10-29_031335_Credit_Opinion_{issuer}.md  # Timestamped final report
```

**Note:** If Phase 3.5 enrichment runs successfully, `phase4_enriched_data.json` includes:
- Phase 3 calculated metrics
- Market risk assessment (price stress, volatility, momentum)
- Macro environment (BoC/Fed rates, credit stress score)
- Distribution history (10-year dividend data, cut detection)
- **Distribution cut prediction** (Model v2.2: probability, risk level, top drivers)

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

**Method 1: Fast Analysis (Default)** - `/analyzeREissuer`

Best for interactive analysis and production workloads:

```bash
# With Claude Code open in this directory:
/analyzeREissuer @statements.pdf @mda.pdf "REIT Name"

# The slash command automatically executes all phases:
# 1. Phase 1: PDF → Markdown (PyMuPDF4LLM + Camelot, 113 tables extracted)
# 2. Phase 2: Markdown → JSON (file references, ~1K tokens)
# 3. Phase 3: Calculate metrics (0 tokens, pure Python)
# 3.5. Enrichment: Market/macro data + distribution cut prediction (Model v2.2)
# 4. Phase 4: Credit analysis (slim agent, ~12K tokens)
# 5. Phase 5: Generate report (0 tokens, templating)

# Total time: ~60 seconds | Total cost: ~$0.30
# Output includes: Distribution cut risk prediction with risk level
```

**Method 2: Cleaner Extraction** - `/analyzeREissuer-docling`

Alternative for batch processing with cleaner markdown output:

```bash
# Same usage, different PDF conversion method:
/analyzeREissuer-docling @statements.pdf @mda.pdf "REIT Name"

# Uses Docling for Phase 1 (slower but more compact markdown)
# Phases 2-5 are identical to Method 1

# Total time: ~20 minutes | Total cost: ~$0.30
# Best for: Overnight batch jobs, testing cleaner extraction
```

**When to use Docling:**
- Overnight/batch processing (time not critical)
- Testing if cleaner markdown improves extraction quality
- Fallback if PyMuPDF4LLM has issues with specific PDFs

**Burn Rate Analysis:** `/burnrate` (New in v1.0.7)

Generate comprehensive cash burn rate and liquidity runway analysis:

```bash
# Using issuer name (searches Issuer_Reports/)
/burnrate "REIT Name"

# Using issuer abbreviation
/burnrate REIT

# Using direct path to Phase 2 JSON
/burnrate Issuer_Reports/REIT_Name/temp/phase2_extracted_data.json

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

Choose your PDF conversion method:

```bash
# Method 1: PyMuPDF4LLM + Camelot (Fast - 30 seconds)
python scripts/preprocess_pdfs_enhanced.py \
  --issuer-name "REIT Name" \
  statements.pdf mda.pdf

# Method 2: Docling (Cleaner - 20 minutes)
python scripts/preprocess_pdfs_docling.py \
  --issuer-name "REIT Name" \
  statements.pdf mda.pdf

# Both create: Issuer_Reports/REIT_Name/temp/phase1_markdown/*.md
```

**Phase 2: Markdown → JSON (after Phase 1 completes)**

```bash
# Extract financial data using file references (~1K tokens)
python scripts/extract_key_metrics_efficient.py \
  --issuer-name "REIT Name" \
  Issuer_Reports/REIT_Name/temp/phase1_markdown/*.md

# Then Claude Code reads the prompt and extracts data
```

**Phase 3: Metric Calculations**
```bash
python scripts/calculate_credit_metrics.py \
  Issuer_Reports/REIT_Name/temp/phase2_extracted_data.json
```

**Phase 4: Credit Analysis (requires Claude Code agent)**
```python
# Within Claude Code:
# Invoke issuer_due_diligence_expert_slim agent with metrics from Phase 3
```

**Phase 5: Final Report Generation**
```bash
python scripts/generate_final_report.py \
  Issuer_Reports/REIT_Name/temp/phase3_calculated_metrics.json \
  Issuer_Reports/REIT_Name/temp/phase4_credit_analysis.md
```

## Usage Examples

### Complete Analysis via Slash Command

```bash
# Example 1: Single REIT with multiple PDFs (recommended)
/analyzeREissuer @financial_statements.pdf @mda.pdf "REIT Name"

# Example 2: Quarterly analysis
/analyzeREissuer @Q2_2025_statements.pdf "REIT Name"
```

### Manual Phase 1 Execution (if needed)

```bash
# Using PyMuPDF4LLM + Camelot (current default)
python scripts/preprocess_pdfs_enhanced.py \
  --issuer-name "REIT Name" \
  financial_statements.pdf mda.pdf

# Results: 113 tables extracted from 75 pages
# Output: Issuer_Reports/REIT_Name/temp/phase1_markdown/
```

### Cleanup

```bash
# Remove temporary files after analysis (keeps reports)
rm -rf Issuer_Reports/*/temp/

# Keep everything organized by issuer
ls Issuer_Reports/REIT_Name/reports/
# Output:
# 2025-10-17_153045_Credit_Opinion_REIT_Name.md
# 2025-10-18_091230_Credit_Opinion_REIT_Name.md
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

The system generates comprehensive reports with 15+ sections:

1. **Executive Summary** - Rating and credit story
2. **Credit Strengths** - Quantified positive factors
3. **Credit Challenges** - Risk factors with mitigants
4. **Rating Outlook** - Stable/Positive/Negative with timeframe
5. **Upgrade Factors** - Specific thresholds for improvement
6. **Downgrade Factors** - Quantified triggers
7. **5-Factor Scorecard** - Detailed rating methodology
8. **Key Observations** - Portfolio quality, unusual metrics
9. **Peer Comparison** - Parallel web research of 3-4 comparable REITs with citations (v1.0.1)
10. **Scenario Analysis** - Base/Upside/Downside/Stress cases with pro forma metrics
11. **Structural Considerations** - **NEW in v1.0.13** - Auto-extracted from Phase 4 analysis:
    - **Debt Structure**: Credit facilities, covenant compliance, debt profile
    - **Security & Collateral**: Unencumbered assets, LTV ratios, recovery estimates
    - **Perpetual Securities**: Hybrid capital instruments or "Not applicable"
12. **ESG Considerations** - Environmental, Social, Governance factors with CIS scoring
13. **Company Background** - Corporate structure, history, portfolio composition
14. **Business Strategy** - Strategic priorities and capital allocation
15. **Detailed Financial Analysis** - FFO/AFFO/ACFO/AFCF reconciliations and bridge analysis

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
