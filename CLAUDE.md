# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Version:** 1.0.7
**Last Updated:** 2025-10-20
**Pipeline Version:** 1.0.7 (Sequential markdown-first + AFCF + Burn Rate analysis)

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
AFCF / (Debt Service + Distributions - New Financing)
```
- Measures true self-sustainability
- < 1.0x = Reliant on capital markets for financing
- Identifies growth vs. income-oriented REITs

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
    "afcf_self_funding_ratio": 0.37,       // Reliant on capital markets
    "total_debt_service": 55000,
    "net_financing_needs": 59000
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

For version history and release notes, see [CHANGELOG.md](CHANGELOG.md).
