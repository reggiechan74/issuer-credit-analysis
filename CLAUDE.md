# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Version:** 1.0.15
**Last Updated:** 2025-10-23
**Pipeline Version:** 1.0.13 (Structural Considerations Content Extraction)
**OpenBB Integration:** v1.0.0 (Complete - Issue #39)
**Distribution Cut Prediction Model:** v2.2 (Sustainable AFCF - Issue #45)

---

## Distribution Cut Prediction Model v2.2 (Issue #45) - NEW ✨

**Status:** COMPLETE (Oct 23, 2025)
**Model File:** `models/distribution_cut_logistic_regression_v2.2.pkl`

### Overview

Updated distribution cut prediction model to align with two-tier AFCF methodology (v1.0.14 - Issue #40). Model v2.2 is trained on **sustainable AFCF** instead of total AFCF, providing more conservative and credit-appropriate risk assessments.

### Why This Update Was Necessary

**Problem:** Model v2.1 was trained on total AFCF (includes non-recurring items like property dispositions), but Phase 3 now calculates sustainable AFCF (recurring items only). This caused a feature distribution mismatch.

**Impact:** v2.1 significantly **underestimated** distribution cut risk by 27-58 percentage points:
- Artis REIT: 5.4% → 63.5% (+58.1%)
- RioCan REIT: 1.3% → 48.5% (+47.2%)
- Dream Industrial REIT: 1.4% → 29.3% (+27.9%)

**Root Cause:** Self-funding ratio (AFCF / Total Obligations) was #4 most predictive feature in v2.1, but the AFCF values shifted dramatically after excluding non-recurring items.

### Model Performance

**v2.2 Training Metrics (5-fold CV):**
- F1 Score: 0.870 (target: ≥0.80) ✅
- ROC AUC: 0.930
- Accuracy: 87.5%
- Precision: 83.3%, Recall: 90.9%

**Training Dataset:**
- 24 observations (11 distribution cuts, 13 controls)
- Canadian REITs from 2022-2024
- All Phase 3 metrics regenerated with sustainable AFCF

**Top 15 Features (by importance):**
1. monthly_burn_rate (1.1039)
2. acfo_calculated (0.7108)
3. available_cash (0.6859)
4. self_funding_ratio (0.6284) - **Dropped from rank #4 to #15**
5. total_available_liquidity (0.5948)

**Key Change:** Self-funding ratio dropped from rank #4 (v2.1) to rank #15 (v2.2), reflecting the shift from total AFCF to sustainable AFCF.

### Usage

**Automatic (via enrichment script):**
```bash
python scripts/enrich_phase4_data.py \
  --phase3 Issuer_Reports/Artis_REIT/temp/phase3_calculated_metrics.json \
  --ticker AX-UN.TO \
  --model models/distribution_cut_logistic_regression_v2.2.pkl
```

**Comparison (v2.1 vs v2.2):**
```bash
python scripts/compare_model_predictions.py
```

### Files Modified

- `scripts/regenerate_phase3_for_training.py` - Batch regeneration script (created)
- `scripts/compare_model_predictions.py` - v2.1 vs v2.2 comparison tool (created)
- `data/training_dataset_v2_sustainable_afcf.csv` - New training dataset (created)
- `models/distribution_cut_logistic_regression_v2.2.pkl` - New model (created)

### Next Steps

- **Production deployment:** Update default model path in `enrich_phase4_data.py` to v2.2
- **Monitoring:** Track prediction accuracy on new observations
- **Documentation:** Update user-facing docs to reflect new risk levels

**See GitHub Issue #45 for complete implementation details**

---

## OpenBB Platform Integration (Issue #39) - NEW ✨

**Status:** COMPLETE (Weeks 1-6, Oct 2025)
**Cost:** $0/month (all free tier APIs)

### Overview

Integrated OpenBB Platform to automate market data, dividend history, and macroeconomic analysis for Canadian REITs. Reduces manual research time by 95%+ while maintaining $0 cost.

### New Scripts (Week 2-6)

1. **`scripts/openbb_market_monitor.py`** (Week 4 - 764 lines)
   - Price stress detection (>30% decline from 52-week high)
   - Volatility analysis (annualized, 30d/90d/252d)
   - Momentum indicators (3/6/12-month returns)
   - Risk scoring (0-100 scale)
   - **Usage:** `python scripts/openbb_market_monitor.py --ticker REI-UN.TO`

2. **`scripts/openbb_macro_monitor.py`** (Week 5 - 200 lines, enhanced)
   - Bank of Canada policy rate (Valet API - FREE, no auth)
   - US Federal Reserve rate (FRED API - FREE, requires key)
   - Rate cycle classification (easing/tightening)
   - Credit environment scoring (0-100)
   - Canada vs US rate differential analysis
   - **Usage:** `python scripts/openbb_macro_monitor.py --output data/macro.json`

3. **`scripts/openbb_data_collector.py`** (Week 2 - 558 lines, enhanced)
   - Dividend history retrieval (10-15 years)
   - Distribution cut detection (>10% threshold)
   - **Recovery analysis** (NEW - time to restore, recovery level %)
   - TTM yield calculations
   - **Usage:** `python scripts/openbb_data_collector.py --ticker REI-UN.TO`

4. **`scripts/build_distribution_cut_dataset.py`** (Week 2 - 420 lines)
   - Automated dataset builder for Issue #38 v2.0 model
   - Scans 20-30 REITs for distribution cuts
   - Recovery pattern analysis
   - CSV export for model training
   - **Usage:** `python scripts/build_distribution_cut_dataset.py --config config/canadian_reits.yaml`

### Data Sources Integrated

| Source | Purpose | Cost | Authentication |
|--------|---------|------|----------------|
| **TMX (via OpenBB)** | Market prices, dividend history | $0 | None |
| **YFinance (via OpenBB)** | Financial statements validation | $0 | None |
| **Bank of Canada Valet API** | Canadian policy rates | $0 | None |
| **FRED (via OpenBB)** | US Federal Funds Rate | $0 | Free API key |

**Total: $0/month** ✅

### Integration Benefits

**For Phase 4 Credit Analysis:**
- Market risk signals (price stress, volatility, momentum)
- Macroeconomic context (rate environment, credit stress score)
- Distribution sustainability indicators (recovery patterns)

**For Issue #38 (Distribution Cut Prediction v2.0):**
- New features: market risk score, rate environment, recovery metrics
- Dataset expansion: n=9 → n=20-30 REITs (automated)
- Time savings: 95%+ reduction in data collection

### Quick Start

```bash
# Test complete pipeline with RioCan REIT
python scripts/openbb_market_monitor.py --ticker REI-UN.TO
python scripts/openbb_macro_monitor.py
python scripts/openbb_data_collector.py --ticker REI-UN.TO

# Build training dataset for 28 Canadian REITs
python scripts/build_distribution_cut_dataset.py \
  --config config/canadian_reits.yaml \
  --output data/training_dataset_v2.csv
```

### FRED API Setup (One-time, 2 minutes)

**Required for US rate comparison (optional but recommended):**

1. Register at: https://fred.stlouisfed.org/
2. Request free API key: https://fred.stlouisfed.org/docs/api/api_key.html
3. Set as GitHub Codespace secret:
   - Repository Settings → Secrets → Codespaces → New secret
   - Name: `FRED_API_KEY`
   - Value: Your API key
4. Configure OpenBB:
```bash
python -c "import json, os; config_path='/home/codespace/.openbb_platform/user_settings.json'; config=json.load(open(config_path)); config['credentials']['fred_api_key']=os.environ.get('FRED_API_KEY'); json.dump(config, open(config_path,'w'), indent=4)"
```

### Configuration Files

- `config/canadian_reits.yaml` - 28 Canadian REIT tickers
- `config/canadian_reits_test.yaml` - 5 REITs (testing)
- `config/canadian_reits_validation.yaml` - 10 REITs (validation)

### Performance Metrics

**Execution Time:**
- Market analysis: 5-10 seconds per REIT
- Macro analysis: <3 seconds
- Dividend history: 2-3 seconds per REIT
- Full 28-REIT scan: 2-3 hours (vs 2-3 weeks manual)

**Data Quality:**
- TMX provider: 90-100% success rate
- 10-15 years dividend history per REIT
- Official source data (Bank of Canada, Federal Reserve)

**Documentation:**
- See GitHub Issue #39 for complete implementation details
- Week 2-6 completion summaries posted to issue

---

## What's New in v1.0.13

**Phase 5: Structural Considerations Content Extraction (Issue #32)**

Enhanced Phase 5 report generation to populate Structural Considerations section by extracting content from Phase 4 analysis:

**New Capabilities:**
- ✅ **3 Parsing Functions:** Extract debt structure, security/collateral, and perpetual securities from Phase 4 content
- ✅ **Debt Structure Extraction:** Credit facilities, covenant compliance, debt profile metrics from Liquidity section
- ✅ **Security/Collateral Extraction:** Unencumbered assets, LTV ratios, recovery estimates from scattered Phase 4 content
- ✅ **Perpetual Securities Detection:** Checks Phase 2, Phase 3, and Phase 4 for perpetual securities
- ✅ **Graceful Degradation:** Returns "Not available" when content not found, "Not applicable" for perpetual securities
- ✅ **Multi-Issuer Testing:** Verified with RioCan, Artis, and Dream Industrial REITs

**What This Fixes:**
- Structural Considerations section no longer shows "Not available" when Phase 4 contains relevant content
- Debt structure information (credit facilities, covenants) now extracted from Liquidity section
- Security analysis (unencumbered assets, recovery estimates) now consolidated from multiple Phase 4 mentions
- Perpetual securities properly detected or marked "Not applicable"

**New Parsing Functions (lines 1007-1246 in `generate_final_report.py`):**
1. `parse_debt_structure()` - Extracts credit facilities, covenant analysis, debt profile from Phase 4 + Phase 3
2. `parse_security_collateral()` - Extracts unencumbered assets, LTV, recovery estimates from Phase 4
3. `check_perpetual_securities()` - Checks Phase 2/3/4 for perpetual securities, defaults to "Not applicable"

**Example Output (RioCan REIT):**
```markdown
### Debt Structure
**Credit Facilities:** $1.93B limit with $771.6M drawn = $1.16B available (60% undrawn)
**Covenant Compliance:** Debt/Assets: 48.3% vs 60-65% (cushion), Interest Coverage: 1.32x vs 1.50x (tight)
**Debt Profile:** Total debt: $7.4B, Debt/Assets: 48.3%, Net Debt/EBITDA: 8.88x

### Security and Collateral
**Unencumbered Asset Pool:** $9.0B, 58% of gross assets
**Security Analysis:** LTV: 48%, Recovery estimate: >80-90%

### Perpetual Securities
Not applicable - no perpetual securities in capital structure
```

**Implementation Details:** See GitHub Issue #32 for complete analysis and testing results

---

## What's New in v1.0.12

**Phase 5: Dual-Table Reporting - Issuer-Reported vs REALPAC-Calculated Metrics**

Enhanced Phase 5 report generation with comprehensive dual-table reporting that separates issuer-disclosed values from standardized REALPAC calculations:

**New Capabilities:**
- ✅ **6 Helper Functions:** Calculate per-unit metrics, payout ratios, coverage ratios, distribution assessments (192 lines)
- ✅ **55+ New Placeholders:** Organized across sections 2.2, 2.5, 2.6, 2.7 for dual-table reporting
- ✅ **Variance Analysis:** Automatic comparison of reported vs calculated metrics with threshold validation
- ✅ **Bridge Analysis:** FFO→AFFO reconciliation showing top adjustments
- ✅ **Gap Analysis:** AFFO vs ACFO differences with implications
- ✅ **Coverage Quality Assessment:** Strong/Adequate/Tight/Insufficient classifications
- ✅ **Self-Funding Analysis:** AFCF capacity for financing obligations

**What This Enables:**
- Side-by-side comparison of issuer-reported and REALPAC-calculated metrics
- Transparency on methodology differences and calculation variances
- Enhanced credit analysis with validation flags for material variances
- Complete FFO/AFFO/ACFO/AFCF coverage and payout analysis
- Professional-grade reporting matching industry best practices

**New Helper Functions (lines 486-678 in `generate_final_report.py`):**
1. `calculate_per_unit()` - Safe per-unit calculations with None handling
2. `calculate_payout_ratio()` - Payout % from per-unit metrics and distributions
3. `calculate_coverage_ratio()` - Coverage ratios (inverse of payout)
4. `assess_distribution_coverage()` - Quality assessment (Strong ≥1.3x, Adequate ≥1.1x, Tight ≥1.0x, Insufficient <1.0x)
5. `assess_self_funding_capacity()` - AFCF self-funding capability assessment
6. `generate_reported_adjustments_list()` - Top 3-5 FFO→AFFO adjustments formatted

**Template Sections Enhanced:**
- **Section 2.2.1:** Issuer-Reported Metrics (FFO/AFFO/ACFO totals, per-unit, payout ratios)
- **Section 2.2.2:** REALPAC-Calculated Metrics (FFO/AFFO/ACFO/AFCF totals, per-unit, payout ratios)
- **Section 2.5:** Coverage Ratios (FFO/AFFO/ACFO coverage with quality assessments)
- **Section 2.6:** Bridge & Gap Analysis (FFO→AFFO adjustments, AFFO vs ACFO differences)
- **Section 2.7:** AFCF Self-Funding Analysis (capacity assessment, financing reliance)

**Implementation Details:** See `docs/PHASE5_REPORTED_VS_CALCULATED_IMPLEMENTATION.md` for complete specification

---

## What's New in v1.0.11

**Comprehensive Phase 2 Extraction (Option 2 Implementation from docs/reportfix.md)**

Enhanced Phase 2 extraction to extract detailed FFO/AFFO/ACFO reconciliation components, enabling full reconciliation tables in credit reports:

**New Capabilities:**
- ✅ **FFO/AFFO Components:** Extract all 26 REALPAC adjustments (A-U + V-Z) from reconciliation tables
- ✅ **ACFO Components:** Extract all 17 REALPAC ACFO adjustments from cash flow statements
- ✅ **Comprehensive Extraction Guide:** 14.5KB detailed guide (`.claude/knowledge/COMPREHENSIVE_EXTRACTION_GUIDE.md`)
- ✅ **Enhanced Prompts:** Upgraded extraction prompts in `extract_key_metrics_efficient.py` with detailed where-to-find guidance
- ✅ **Validation Procedures:** Built-in validation against issuer-reported values
- ✅ **Consistency Checks:** Automatic validation of ACFO vs AFFO consistency

**What This Unlocks:**
- Full FFO/AFFO/ACFO reconciliation tables in Phase 5 reports
- Validation of issuer-reported metrics against calculated values
- 90%+ template placeholder population (vs 40-50% previously)
- Enhanced credit analysis transparency and auditability
- Enables all Phase 3 calculations that were previously data-starved

**Token Impact:** +3-4K tokens for comprehensive extraction (still within 20K budget)

**Implementation Details:** See `docs/reportfix.md` for complete analysis

---

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

## Development Workflow

**GitHub Issue Management:**

When working on GitHub issues, follow this workflow:

1. **Create issue** with detailed problem description, root cause analysis, implementation plan, and acceptance criteria
2. **Work on issue** - implement fixes, create functions, update placeholders
3. **Test thoroughly** - regenerate reports and verify all acceptance criteria are met
4. **Close issue** with summary of changes made and verification results
5. **ALWAYS commit after closing an issue** - this ensures all fixes are saved and tracked

**Commit message format after closing issues:**
```bash
git add .
git commit -m "fix: [brief description of what was fixed]

Resolves #[issue-number]

- Change 1
- Change 2
- Change 3

Verified with [test case]"
```

**Example:**
```bash
git add scripts/generate_final_report.py templates/credit_opinion_template.md
git commit -m "fix: populate AFFO/ACFO variance placeholders in Section 2.6.3

Resolves #12

- Added AFFO_VARIANCE placeholder with amount and percentage format
- Added ACFO_VARIANCE placeholder with N/A handling for unreported values
- Both placeholders read from Phase 3 validation data

Verified with Artis REIT - variances display correctly in Section 2.6.3"
```

**Why commit after closing issues:**
- Preserves work immediately after verification
- Links commits to GitHub issues for traceability
- Prevents accidental loss of fixes
- Creates clear project history
- Enables rollback if needed

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
- `.claude/knowledge/phase2_extraction_schema.json` - JSON Schema specification (AUTHORITATIVE)
- `.claude/knowledge/COMPREHENSIVE_EXTRACTION_GUIDE.md` - Detailed extraction guide with examples
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

## AFCF Metrics (v1.0.6)

**Adjusted Free Cash Flow (AFCF)** extends the analysis beyond ACFO to measure cash available for financing obligations after ALL investing activities.

### What is AFCF?

```
AFCF = ACFO + Net Cash Flow from Investing Activities
```

**Purpose:** Measure cash available to service debt and distributions after operating cash flow AND growth investments (acquisitions, development, JV investments).

**Key Distinction:**
- **ACFO** = Sustainable operating cash flow (deducts sustaining capex/TI/leasing costs)
- **AFCF** = Free cash flow after ALL investments (more conservative, includes growth capex and acquisitions)

### Double-Counting Prevention ⚠️

**CRITICAL:** ACFO already deducts these items - DO NOT include in AFCF:
- ✅ Sustaining CAPEX (ACFO Adj 4) - Already deducted
- ✅ Sustaining tenant improvements (ACFO Adj 6) - Already deducted
- ✅ External leasing costs (ACFO Adj 5) - Already deducted
- ✅ JV distributions received (ACFO Adj 3) - Already included

**AFCF should ONLY add:**
- Development CAPEX (growth projects, not sustaining)
- Property acquisitions and dispositions
- JV capital contributions/returns (not distributions)
- Business combinations
- Other investing activities

**Why This Works (IAS 7 Classification):**
Under IFRS, sustaining items go in **Cash Flow from Operations (CFO)**, while growth/investing items go in **Cash Flow from Investing (CFI)**. Therefore:
- ACFO deducts sustaining items from CFO (already removed)
- AFCF adds CFI to ACFO (only growth items)
- No double-counting by design

### Required Phase 2 Data

Add to Phase 2 extraction for AFCF support:

```json
{
  "cash_flow_investing": {
    "development_capex": -20000,           // Growth capex (negative)
    "property_acquisitions": -30000,       // Acquisitions (negative)
    "property_dispositions": 25000,         // Sale proceeds (positive)
    "jv_capital_contributions": -5000,     // JV investments (negative)
    "jv_return_of_capital": 2000,          // JV exits (positive)
    "total_cfi": -28000                    // For reconciliation
  },
  "cash_flow_financing": {
    "debt_principal_repayments": -15000,   // Principal payments (negative)
    "new_debt_issuances": 10000,           // New debt (positive)
    "distributions_common": -18000,        // Distributions (negative)
    "equity_issuances": 5000,              // New equity (positive)
    "total_cff": -18000                    // For reconciliation
  }
}
```

### AFCF Coverage Ratios

**1. AFCF Debt Service Coverage**
```
AFCF / (Annualized Interest + Principal Repayments)
```
- More conservative than NOI/Interest coverage
- Measures ability to service ALL debt obligations from free cash flow
- < 1.0x = Cannot self-fund debt service (needs external financing)

**2. AFCF Distribution Coverage**
```
AFCF / Total Distributions
```
- Modified payout ratio based on free cash flow
- More conservative than AFFO payout ratio
- < 1.0x = Distributions exceed free cash flow

**3. AFCF Self-Funding Ratio**
```
AFCF / (Total Debt Service + Total Distributions)
```
- Measures ability to cover ALL financing obligations from free cash flow
- < 1.0x = Reliant on capital markets (cannot self-fund)
- ≥ 1.0x = Self-funding (can cover obligations without new financing)
- **Note:** Does NOT subtract new financing (aligns with burn rate methodology)
- **Rationale:** Measures inherent cash generation capacity, not external financing decisions

### Example Output

```json
{
  "afcf_metrics": {
    "afcf": 22000,
    "afcf_per_unit": 0.2185,              // Per-unit calculated automatically
    "acfo_starting_point": 50000,
    "net_cfi": -28000,
    "cfi_breakdown": {
      "development_capex": {"amount": -20000},
      "property_acquisitions": {"amount": -30000},
      "property_dispositions": {"amount": 25000}
    },
    "data_quality": "strong"
  },
  "afcf_coverage": {
    "afcf_debt_service_coverage": 0.40,    // ⚠️ LOW - needs external financing
    "afcf_payout_ratio": 86.4,             // Distributions sustainable from FCF
    "afcf_self_funding_ratio": 0.30,       // Can only cover 30% of obligations
    "total_debt_service": 55000,
    "total_distributions": 19000,
    "afcf_self_funding_capacity": -52000   // Needs $52k external financing
  },
  "afcf_reconciliation": {
    "afcf_calculation_valid": true,
    "development_capex_consistent": true,
    "validation_notes": ["✓ AFCF calculation correct: ACFO + Net CFI = AFCF"]
  }
}
```

**Note:** All Phase 3 calculations automatically compute per-unit amounts (FFO, AFFO, ACFO, AFCF) on both **basic** and **diluted** share bases:
- **Basic per-unit**: Calculated when `common_units_outstanding` is available in balance sheet
- **Diluted per-unit**: Calculated when `diluted_units_outstanding` is available in balance sheet
  - Accounts for convertible securities, options, warrants, and other dilutive instruments
  - Provides more conservative per-unit metrics for credit analysis

### Credit Analysis Use Cases

**Identify Financing Reliance:**
```
AFCF = $22M, Debt Service = $55M → Coverage = 0.40x
⚠️ REIT cannot self-fund debt service from free cash flow
→ Must access capital markets for debt refinancing
→ Higher credit risk during market stress
```

**Assess Growth Strategy:**
```
ACFO = $50M (strong operations)
Net CFI = -$28M (growth investments)
AFCF = $22M (positive but constrained)
→ Growth-oriented REIT deploying capital actively
→ Sustainable if capital markets remain accessible
```

**Distribution Sustainability:**
```
AFCF = $22M, Distributions = $19M → Coverage = 1.16x
✓ Distributions covered by free cash flow
→ Sustainable payout even without new financing
```

**Self-Funding and Burn Rate Connection (v1.0.7):**
```
AFCF = $50M
Total Obligations = $98M (debt service + distributions)
Self-Funding Ratio = 50 / 98 = 0.51x

→ Can only cover 51% of obligations from free cash flow
→ Financing gap = $98M - $50M = $48M (must be funded externally)
→ If no new financing: Burns $48M / 6 months = $8M/month
→ Cash runway = Available cash / Monthly burn rate

Credit Implication:
- <0.5x = HIGH reliance on capital markets
- 0.5-0.8x = MODERATE reliance
- 0.8-1.0x = LOW reliance (nearly self-funding)
- ≥1.0x = Self-funding (generates surplus)
```

### Functions

**Phase 3 Functions (automatic if CFI/CFF data present):**
- `calculate_afcf()` - Main AFCF calculation (includes afcf_per_unit if shares outstanding available)
- `calculate_afcf_coverage_ratios()` - Coverage metrics
- `validate_afcf_reconciliation()` - Validation checks

**Per-Unit Calculations:**
All calculation functions automatically compute per-unit metrics when share data is available:
- `calculate_ffo_from_components()` → includes `ffo_per_unit` (basic) and `ffo_per_unit_diluted`
- `calculate_affo_from_ffo()` → includes `affo_per_unit` (basic) and `affo_per_unit_diluted`
- `calculate_acfo_from_components()` → includes `acfo_per_unit` (basic) and `acfo_per_unit_diluted`
- `calculate_afcf()` → includes `afcf_per_unit` (basic) and `afcf_per_unit_diluted`

**Note:** Basic per-unit uses `common_units_outstanding`. Diluted per-unit uses `diluted_units_outstanding` (if available in Phase 2 extraction). Diluted calculations account for convertible securities, options, and warrants.

**See:** `docs/AFCF_Research_Proposal.md` for complete methodology

## Dilution Tracking and Analysis (v1.0.8)

**Share dilution** from convertible securities, options, and warrants can materially impact per-unit metrics and credit quality. The pipeline now supports optional detailed dilution tracking for enhanced credit analysis.

### What is Dilution Tracking?

The `dilution_detail` section (optional in Phase 2 extraction) provides transparency on dilution sources and materiality:

```json
{
  "dilution_detail": {
    "basic_units": 99444,
    "dilutive_instruments": {
      "restricted_units": 1500,        // RSUs/PSUs
      "deferred_units": 500,           // DSUs (director awards)
      "stock_options": 0,              // Employee options
      "convertible_debentures": 0,     // If-converted units
      "warrants": 0,                   // Outstanding warrants
      "other": 0                       // Other dilutive securities
    },
    "diluted_units_calculated": 101444,
    "diluted_units_reported": 101444,
    "dilution_percentage": 2.01,
    "reconciliation_note": "Calculated matches reported - no anti-dilutive exclusions",
    "disclosure_source": "Q2 2025 MD&A page 21"
  }
}
```

### When to Extract Dilution Detail

**✅ Extract dilution_detail when:**
- Issuer provides detailed dilution calculation in MD&A (e.g., Artis REIT Q2 2025 MD&A page 21)
- Shows breakdown by instrument type (RSUs, options, convertibles, warrants)
- Useful for assessing dilution materiality and quality

**❌ Skip dilution_detail when:**
- Issuer only reports basic vs diluted totals (e.g., DIR)
- No detailed breakdown available
- Just include `common_units_outstanding` and `diluted_units_outstanding` in balance_sheet

**Hybrid Approach:** The schema supports both simple (totals only) and detailed (instrument breakdown) disclosures.

### Materiality Assessment

Phase 3 automatically analyzes dilution when `dilution_detail` is present:

| Dilution % | Materiality | Typical Sources | Credit Impact |
|------------|-------------|-----------------|---------------|
| < 1% | **Minimal** | RSUs/DSUs only | Negligible |
| 1-3% | **Low** | Normal equity compensation | Low concern |
| 3-7% | **Moderate** | Options + RSUs | Monitor equity overhang |
| > 7% | **High** | Material convertibles or warrants | Credit concern |

**Special Case - Convertible Debt:**
- Convertible debentures > 5% dilution = **Moderate-High credit risk**
- Review conversion terms and forced conversion scenarios
- Factor into debt capacity assessment

### Phase 3 Analysis Function

The `analyze_dilution()` function automatically runs when `dilution_detail` is present:

**Output:**
```json
{
  "dilution_analysis": {
    "has_dilution_detail": true,
    "dilution_percentage": 2.01,
    "dilution_materiality": "low",
    "material_instruments": ["restricted_units", "deferred_units"],
    "convertible_debt_risk": "none",
    "governance_score": "enhanced",
    "credit_assessment": "Minimal dilution (2.01%) from normal equity compensation. No material convertible debt. Enhanced disclosure suggests strong governance."
  }
}
```

**Materiality Levels:**
- `minimal` - < 1% dilution
- `low` - 1-3% dilution
- `moderate` - 3-7% dilution
- `high` - > 7% dilution

**Convertible Debt Risk:**
- `none` - No convertible debt or < 1% dilution
- `low` - 1-5% dilution from convertibles
- `moderate` - 5-10% dilution from convertibles
- `high` - > 10% dilution from convertibles

**Governance Score:**
- `standard` - Only reports basic/diluted totals
- `enhanced` - Provides detailed instrument breakdown

### Phase 4 Integration

Phase 4 credit assessment incorporates dilution analysis into **Factor 4: Capital Structure and Financial Flexibility**:

**Impact on Credit Rating:**
```
Low dilution (< 3%) + Enhanced disclosure = Positive for governance
Moderate dilution (3-7%) = Neutral, monitor equity overhang
High dilution (> 7%) or Material convertibles = Negative adjustment
```

**Example Assessment:**
```
Artis REIT: 2.01% dilution from RSUs/DSUs
→ Minimal equity overhang risk
→ Enhanced disclosure demonstrates transparency
→ Positive governance signal
→ No adjustment to credit rating
```

### Credit Analysis Use Cases

**1. Assess Equity Overhang**
```
10% dilution from convertible debentures:
→ Material potential equity issuance
→ Review conversion terms (forced conversion risk?)
→ Factor into debt capacity calculations
```

**2. Identify Governance Quality**
```
Provides detailed breakdown (Artis) vs totals only (DIR):
→ Enhanced disclosure = better transparency
→ Can be factored into governance/management score
```

**3. Evaluate Distribution Sustainability**
```
High dilution increases unit count over time:
→ Must grow distributions to maintain per-unit payout
→ Assess if AFFO growth can support dilution + distribution growth
```

**4. Forced Conversion Analysis**
```
Convertible debt with $X conversion price, current price $Y:
→ If Y > X, conversion likely
→ Dilution impact on metrics
→ Covenant implications
```

### Required Phase 2 Fields

**Minimum (all issuers):**
```json
{
  "balance_sheet": {
    "common_units_outstanding": 99444,      // Basic weighted average
    "diluted_units_outstanding": 101444     // Diluted weighted average
  }
}
```

**Enhanced (when detailed breakdown available):**
```json
{
  "dilution_detail": {
    "basic_units": 99444,
    "dilutive_instruments": {
      "restricted_units": 1500,
      "deferred_units": 500,
      "stock_options": 0,
      "convertible_debentures": 0,
      "warrants": 0,
      "other": 0
    },
    "diluted_units_calculated": 101444,
    "diluted_units_reported": 101444,
    "dilution_percentage": 2.01,
    "reconciliation_note": "...",
    "disclosure_source": "Q2 2025 MD&A page 21"
  }
}
```

### Per-Unit Calculations (Basic vs Diluted)

All Phase 3 functions automatically calculate both basic and diluted per-unit metrics:

**Functions:**
- `calculate_ffo_from_components()` → `ffo_per_unit` + `ffo_per_unit_diluted`
- `calculate_affo_from_ffo()` → `affo_per_unit` + `affo_per_unit_diluted`
- `calculate_acfo_from_components()` → `acfo_per_unit` + `acfo_per_unit_diluted`
- `calculate_afcf()` → `afcf_per_unit` + `afcf_per_unit_diluted`
- `analyze_dilution()` → Dilution materiality and credit assessment

**Example Output:**
```json
{
  "ffo_metrics": {
    "ffo": 34500,
    "ffo_per_unit": 0.3471,           // Basic: 34500 / 99444
    "ffo_per_unit_diluted": 0.3401,   // Diluted: 34500 / 101444
    "data_source": "calculated"
  }
}
```

**Documentation:**
- Schema: `.claude/knowledge/phase2_extraction_schema.json` (AUTHORITATIVE)
- Extraction guide: `.claude/knowledge/COMPREHENSIVE_EXTRACTION_GUIDE.md`
- Complete guide: `.claude/knowledge/SCHEMA_README.md` (Dilution Tracking section, lines 190-307)
- Phase 4 agent: `.claude/agents/domain_expert/issuer_due_diligence_expert_slim.md` (Dilution Analysis section)

## Burn Rate and Cash Runway Analysis (v1.0.7)

**Cash burn rate** measures the speed at which a REIT depletes cash reserves when AFCF cannot cover financing obligations.

### What is Burn Rate?

```
Burn Rate = Net Financing Needs - AFCF (when AFCF < Net Financing Needs)
```

**Key Insight:** A REIT can have *positive AFCF* but still burn cash if free cash flow is insufficient to cover debt service + distributions.

**When Burn Rate Applies:**
- ✅ AFCF < (Debt Service + Distributions - New Financing)
- ✅ Self-funding ratio < 1.0x
- ❌ NOT just when AFCF is negative

### Formula Components

```
Net Financing Needs = Total Debt Service + Total Distributions - New Financing

Where:
  Total Debt Service = Annualized Interest Expense + Principal Repayments
  Total Distributions = Common + Preferred + NCI distributions
  New Financing = New Debt Issuances + Equity Issuances
```

### Required Phase 2 Data

Burn rate analysis requires liquidity data extraction:

```json
{
  "liquidity": {
    "cash_and_equivalents": 65000,
    "marketable_securities": 20000,
    "restricted_cash": 5000,
    "undrawn_credit_facilities": 150000,
    "credit_facility_limit": 200000,
    "available_cash": 80000,
    "total_available_liquidity": 230000,
    "data_source": "balance sheet + note 12"
  }
}
```

### Burn Rate Metrics

**1. Monthly Burn Rate**
```
Monthly Burn Rate = Annualized Burn Rate / 12 months
```
- Measures cash depletion per month
- Denominator for runway calculations

**2. Cash Runway**
```
Available Cash = Cash + Marketable Securities - Restricted Cash
Cash Runway (months) = Available Cash / Monthly Burn Rate
Extended Runway = (Available Cash + Undrawn Facilities) / Monthly Burn Rate
```
- Months until cash depletion at current burn rate
- Extended runway includes credit facility capacity

**3. Liquidity Risk Assessment**

| Runway | Risk Level | Risk Score | Action Required |
|--------|------------|------------|-----------------|
| < 6 months | 🚨 **CRITICAL** | 4 | Immediate financing required |
| 6-12 months | ⚠️ **HIGH** | 3 | Near-term capital raise needed |
| 12-24 months | ⚠️ **MODERATE** | 2 | Plan financing within 12 months |
| > 24 months | ✓ **LOW** | 1 | Adequate liquidity runway |

**4. Sustainable Burn Rate**
```
Sustainable Monthly Burn = Available Cash / Target Runway (24 months)
Excess Burn = Actual Monthly Burn - Sustainable Monthly Burn
```
- Maximum burn rate to maintain target runway
- Identifies overspend requiring corrective action

### Example Calculation

**Scenario:** REIT with positive AFCF but burning cash

**Input:**
- AFCF = $28M (positive - operations are healthy)
- Annualized Interest = $22M
- Principal Repayments = $25M
- Distributions = $19M
- New Debt = $10M
- New Equity = $5M
- Available Cash = $80M
- Undrawn Facilities = $150M

**Calculation:**
```
Net Financing Needs = (22M + 25M + 19M) - (10M + 5M) = 51M
AFCF = 28M

Burn Rate Applicable? Yes (28M < 51M)
Self-Funding Ratio = 28M / 51M = 0.55x (REIT cannot self-fund)

Annualized Burn = 51M - 28M = 23M
Monthly Burn = 23M / 12 = 1.92M/month

Cash Runway = 80M / 1.92M = 41.7 months
Extended Runway = (80M + 150M) / 1.92M = 119.8 months

Risk Level = LOW (> 24 months)
```

**Interpretation:**
- ⚠️ REIT burns $1.92M/month despite positive AFCF
- ✓ Comfortable 41.7-month runway without new financing
- ✓ Extended runway of 10 years if credit facility accessed
- ✓ Growth-oriented strategy is sustainable

### Output Schema

```json
{
  "burn_rate_analysis": {
    "applicable": true,
    "monthly_burn_rate": 1916667,
    "annualized_burn_rate": 23000000,
    "afcf": 28000000,
    "net_financing_needs": 51000000,
    "self_funding_ratio": 0.55
  },
  "liquidity_position": {
    "cash_and_equivalents": 65000000,
    "marketable_securities": 20000000,
    "restricted_cash": 5000000,
    "available_cash": 80000000,
    "undrawn_credit_facilities": 150000000,
    "total_available_liquidity": 230000000
  },
  "cash_runway": {
    "runway_months": 41.7,
    "runway_years": 3.5,
    "extended_runway_months": 119.8,
    "extended_runway_years": 10.0,
    "depletion_date": "2029-04-15"
  },
  "liquidity_risk": {
    "risk_level": "LOW",
    "risk_score": 1,
    "warning_flags": [],
    "assessment": "✓ Adequate liquidity runway (> 24 months)",
    "recommendations": [
      "Monitor burn rate quarterly",
      "Maintain covenant compliance"
    ]
  },
  "sustainable_burn": {
    "target_runway_months": 24,
    "sustainable_monthly_burn": 3333333,
    "excess_burn_per_month": -1416666,
    "status": "Below sustainable - $1,417,000/month cushion"
  }
}
```

### Credit Analysis Use Cases

**1. Differentiate Growth vs. Distress**
```
Positive AFCF + Burn Rate = Growth investments exceed operating cash flow
Negative AFCF + Burn Rate = Operational distress
```

**2. Assess Financing Dependency**
```
Self-Funding Ratio < 1.0 = Reliant on capital markets
Short Runway (<12mo) + High Burn = Forced seller/financing risk
```

**3. Distribution Sustainability**
```
If suspending distributions (saving $19M/year):
  New Burn Rate = $4M/year
  New Runway = 80M / (4M/12) = 240 months
→ Distribution cut would extend runway dramatically
```

**4. Refinancing Risk**
```
Debt maturity in 18 months, Current runway = 10 months
→ Must refinance before cash depletion
→ Weak negotiating position
```

### Functions

**Phase 3 Functions (automatic if AFCF + financing + liquidity data present):**
- `calculate_burn_rate()` - Calculate burn rate from AFCF vs financing needs
- `calculate_cash_runway()` - Calculate months until cash depletion
- `assess_liquidity_risk()` - Risk level assessment (CRITICAL/HIGH/MODERATE/LOW)
- `calculate_sustainable_burn_rate()` - Maximum sustainable burn rate

**Testing:**
- Unit tests: `tests/test_burn_rate_calculations.py` (25 tests)
- Integration tests: `tests/test_burn_rate_integration.py` (11 tests)

**See:** GitHub Issue #7 for complete implementation details

## Key Files

**Pipeline Scripts:**
- `scripts/preprocess_pdfs_enhanced.py` - Phase 1: PDF→Markdown (PyMuPDF4LLM + Camelot)
- `scripts/extract_key_metrics_efficient.py` - Phase 2: Markdown→JSON extraction (file references)
- `scripts/calculate_credit_metrics.py` - Phase 3: Metric calculations
- `scripts/generate_final_report.py` - Phase 5: Report generation

**Alternative Phase 2 (experimental - NOT RECOMMENDED):**
- `scripts/experimental/extract_key_metrics_v2.py` - Enhanced extraction with grep-based indexing
- `scripts/experimental/extraction_indexer.py` - Section indexing module
- `scripts/experimental/section_extractor.py` - Targeted extraction with validation
- Note: V2 is more token-efficient than original embedded approach (89% reduction) but slower in practice due to overhead. The production method achieves 99% reduction (~1K tokens) making v2 unnecessary.

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

For version history and release notes, see [CHANGELOG.md](CHANGELOG.md).
