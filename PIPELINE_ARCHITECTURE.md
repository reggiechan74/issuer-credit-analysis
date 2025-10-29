# Pipeline Architecture: Input/Output Flow Diagram

**Version:** 1.0.15
**Last Updated:** 2025-10-29
**Purpose:** Complete technical specification of data flows through the 5-phase credit analysis pipeline

---

## Architecture Overview

```
╔═══════════════════════════════════════════════════════════════════════════╗
║           REAL ESTATE ISSUER CREDIT ANALYSIS PIPELINE                     ║
║                                                                           ║
║  Input: Financial Statements PDFs → Output: Credit Opinion Report        ║
║                                                                           ║
║  Phases: 5 Sequential + 1 Optional Enrichment                            ║
║  Token Usage: ~13,000 tokens (~$0.30 per analysis)                       ║
║  Execution Time: ~60 seconds (PyMuPDF) or ~20 minutes (Docling)          ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## Phase 1: PDF → Markdown Conversion

### Purpose
Convert financial statement PDFs to structured markdown with extracted tables.

### Inputs

| Input Type | Format | Source | Required |
|------------|--------|--------|----------|
| Financial Statements | PDF | User-provided | Yes |
| Management Discussion & Analysis (MD&A) | PDF | User-provided | Yes |
| Issuer Name | String | Command argument | Yes |

**Example Input Files:**
```
/workspace/
  ├── reit_q2_2025_statements.pdf     (30-50 pages)
  └── reit_q2_2025_mda.pdf            (20-40 pages)
```

### Processing Tools

**Option 1: PyMuPDF4LLM + Camelot (Default)**
```bash
python scripts/preprocess_pdfs_enhanced.py \
  --issuer-name "Example REIT" \
  reit_q2_2025_statements.pdf \
  reit_q2_2025_mda.pdf
```

**Option 2: Docling (Alternative)**
```bash
python scripts/preprocess_pdfs_docling.py \
  --issuer-name "Example REIT" \
  reit_q2_2025_statements.pdf \
  reit_q2_2025_mda.pdf
```

### Outputs

| Output File | Format | Size | Location |
|------------|--------|------|----------|
| Statements Markdown | `.md` | ~300KB | `Issuer_Reports/{Issuer}/temp/phase1_markdown/` |
| MD&A Markdown | `.md` | ~245KB | `Issuer_Reports/{Issuer}/temp/phase1_markdown/` |

**Output Structure:**
```
Issuer_Reports/
  └── Example_REIT/
      └── temp/
          └── phase1_markdown/
              ├── reit_q2_2025_statements.md    (~300KB, 113 tables)
              └── reit_q2_2025_mda.md           (~245KB, text + tables)
```

**Markdown Features:**
- Extracted tables in markdown format (PyMuPDF: 14-column, Docling: 4-column)
- Preserved text structure and headings
- Page numbers and section references
- Financial statement hierarchies
- Footnotes and disclosures

### Execution Metrics

| Method | Time | Tables Extracted | Quality |
|--------|------|------------------|---------|
| PyMuPDF4LLM + Camelot | 30s | 113 tables | Good (production default) |
| Docling FAST | 20min | 95 tables | Excellent (cleaner structure) |

### Critical Requirements

✅ **Phase 1 MUST complete before Phase 2 starts** (sequential dependency)
✅ **Output markdown files must exist** before Phase 2 extraction
✅ **Issuer name must match** across all phases (folder naming)

---

## Phase 2: Markdown → JSON Extraction

### Purpose
Extract structured financial data from markdown files into schema-validated JSON.

### Inputs

| Input Type | Format | Source | Required |
|------------|--------|--------|----------|
| Financial Statements Markdown | `.md` | Phase 1 output | Yes |
| MD&A Markdown | `.md` | Phase 1 output | Yes |
| Extraction Schema | JSON Schema | `.claude/knowledge/phase2_extraction_schema.json` | Yes |
| Extraction Guide | Markdown | `.claude/knowledge/COMPREHENSIVE_EXTRACTION_GUIDE.md` | Yes |

**Input File Paths:**
```
Issuer_Reports/Example_REIT/temp/phase1_markdown/
  ├── reit_q2_2025_statements.md
  └── reit_q2_2025_mda.md
```

### Processing Tool

```bash
python scripts/extract_key_metrics_efficient.py \
  --issuer-name "Example REIT" \
  Issuer_Reports/Example_REIT/temp/phase1_markdown/*.md
```

**Token Usage:** ~1,000 tokens (file references, not embedded content)

### Extraction Process

1. **Read markdown files** via Claude Code Read tool
2. **Extract structured data** following schema:
   - Balance sheet (flat structure)
   - Income statement (top-level values)
   - Cash flow statements (operating, investing, financing)
   - FFO/AFFO/ACFO reconciliations (26 REALPAC adjustments)
   - Portfolio details (properties, occupancy, GLA)
   - Debt details (maturities, covenants, facilities)
   - Liquidity (cash, credit facilities)
   - Distributions (common, preferred, NCI)
   - Share count (basic, diluted)
   - Dilution detail (optional, if disclosed)
3. **Validate against schema** (flat structures, no nulls, decimal rates)
4. **Save JSON output**

### Outputs

| Output File | Format | Size | Location |
|------------|--------|------|----------|
| Extracted Data | JSON | ~50-100KB | `Issuer_Reports/{Issuer}/temp/phase2_extracted_data.json` |
| Extraction Prompt | Text | ~5KB | `Issuer_Reports/{Issuer}/temp/phase2_extraction_prompt.txt` |

**JSON Schema Compliance:**

```json
{
  "issuer_name": "Example REIT",
  "report_date": "2025-06-30",
  "period": "Q2 2025",
  "balance_sheet": {
    "total_assets": 3500000,           // FLAT structure (no nesting)
    "cash": 65000,
    "total_debt": 1800000,
    "common_units_outstanding": 99444, // Required for per-unit calcs
    "diluted_units_outstanding": 101444
  },
  "income_statement": {
    "revenue": 59082,                  // TOP-LEVEL values (not nested)
    "noi": 30729,
    "interest_expense": 16937
  },
  "ffo_affo": {
    "net_income": 22000,
    "ffo_reported": 34500,
    "affo_reported": 28000,
    "ffo_adjustments": {                // 26 REALPAC adjustments A-U + V-Z
      "adj_a_depreciation": 15000,
      "adj_b_amortization": 2000,
      // ... all adjustments
    }
  },
  "acfo": {
    "acfo_reported": 26500,
    "acfo_adjustments": {               // 17 REALPAC ACFO adjustments
      "adj_1_distributions_received": 1500,
      "adj_4_sustaining_capex": -8000,
      // ... all adjustments
    }
  },
  "cash_flow_investing": {              // Required for AFCF
    "development_capex": -20000,
    "property_acquisitions": -30000,
    "property_dispositions": 25000,
    "total_cfi": -28000
  },
  "cash_flow_financing": {              // Required for burn rate
    "debt_principal_repayments": -15000,
    "new_debt_issuances": 10000,
    "distributions_common": -18000,
    "equity_issuances": 5000,
    "total_cff": -18000
  },
  "liquidity": {                        // Required for cash runway
    "cash_and_equivalents": 65000,
    "undrawn_credit_facilities": 150000,
    "available_cash": 80000,
    "total_available_liquidity": 230000
  },
  "dilution_detail": {                  // OPTIONAL (if disclosed)
    "basic_units": 99444,
    "dilutive_instruments": {
      "restricted_units": 1500,
      "deferred_units": 500,
      "convertible_debentures": 0
    },
    "dilution_percentage": 2.01
  }
}
```

### Validation Step

**CRITICAL: Validate before Phase 3**

```bash
python scripts/validate_extraction_schema.py \
  Issuer_Reports/Example_REIT/temp/phase2_extracted_data.json
```

**Validation Checks:**
- ✅ Flat structure for balance_sheet
- ✅ Top-level values for income_statement
- ✅ No null values in numeric fields (use 0)
- ✅ Decimal format for rates (0-1 range, not percentages)
- ✅ All required fields present
- ✅ Data types match schema

### Critical Requirements

✅ **Schema compliance is MANDATORY** (Phase 3 will fail otherwise)
✅ **No nested structures** in balance_sheet
✅ **No null values** (use 0 for missing data)
✅ **Rates as decimals** (0.878 not 87.8)

---

## Phase 3: JSON → Calculated Metrics

### Purpose
Calculate credit metrics from extracted financial data using pure Python (NO tokens).

### Inputs

| Input Type | Format | Source | Required |
|------------|--------|--------|----------|
| Extracted Financial Data | JSON | Phase 2 output | Yes |
| Phase 2 Schema | JSON Schema | `.claude/knowledge/phase2_extraction_schema.json` | Yes |

**Input File Path:**
```
Issuer_Reports/Example_REIT/temp/phase2_extracted_data.json
```

### Processing Tool

```bash
python scripts/calculate_credit_metrics.py \
  Issuer_Reports/Example_REIT/temp/phase2_extracted_data.json
```

**Token Usage:** 0 tokens (pure Python calculations)

### Calculation Functions

**Core Metrics (Always Calculated):**

1. **FFO Metrics** (`calculate_ffo_from_components()`)
   - FFO calculated from REALPAC adjustments A-U
   - FFO per unit (basic and diluted)
   - Validation against issuer-reported FFO

2. **AFFO Metrics** (`calculate_affo_from_ffo()`)
   - AFFO calculated from FFO + adjustments V-Z
   - AFFO per unit (basic and diluted)
   - AFFO payout ratio

3. **ACFO Metrics** (`calculate_acfo_from_components()`)
   - ACFO calculated from 17 REALPAC ACFO adjustments
   - ACFO per unit (basic and diluted)
   - ACFO coverage ratio

4. **Leverage Metrics** (`calculate_leverage_metrics()`)
   - Debt/Assets ratio
   - Net Debt/EBITDA
   - Interest coverage (NOI/Interest)

5. **Liquidity Metrics** (`calculate_liquidity_metrics()`)
   - Current ratio
   - Debt maturity profile
   - Covenant headroom

6. **Portfolio Metrics** (`calculate_portfolio_metrics()`)
   - Occupancy rate
   - NOI margin
   - Revenue per square foot

**Advanced Metrics (Conditional - if data present):**

7. **AFCF Metrics** (`calculate_afcf()`)
   - AFCF = ACFO + Net Cash Flow from Investing
   - AFCF per unit (basic and diluted)
   - AFCF debt service coverage
   - AFCF payout ratio
   - Self-funding ratio

8. **Burn Rate Analysis** (`calculate_burn_rate()`)
   - Monthly burn rate
   - Annualized burn rate
   - Net financing needs
   - Cash runway (months/years)
   - Liquidity risk score (1-4)

9. **Dilution Analysis** (`analyze_dilution()`)
   - Dilution percentage
   - Dilution materiality (minimal/low/moderate/high)
   - Convertible debt risk
   - Governance score

### Outputs

| Output File | Format | Size | Location |
|------------|--------|------|----------|
| Calculated Metrics | JSON | ~150-300KB | `Issuer_Reports/{Issuer}/temp/phase3_calculated_metrics.json` |

**JSON Output Structure:**

```json
{
  "issuer_name": "Example REIT",
  "calculation_date": "2025-10-29T12:00:00",
  "data_source": "phase2_extracted_data.json",

  "ffo_metrics": {
    "ffo": 34500,
    "ffo_per_unit": 0.3471,              // Basic
    "ffo_per_unit_diluted": 0.3401,      // Diluted
    "ffo_reported": 34500,
    "ffo_variance": 0,
    "data_source": "calculated"
  },

  "affo_metrics": {
    "affo": 28000,
    "affo_per_unit": 0.2816,
    "affo_per_unit_diluted": 0.2760,
    "affo_payout_ratio": 85.7,           // %
    "data_source": "calculated"
  },

  "acfo_metrics": {
    "acfo": 26500,
    "acfo_per_unit": 0.2665,
    "acfo_per_unit_diluted": 0.2612,
    "acfo_coverage_ratio": 1.17,         // ACFO / Distributions
    "data_source": "calculated"
  },

  "afcf_metrics": {                      // CONDITIONAL
    "afcf": 22000,
    "afcf_per_unit": 0.2213,
    "afcf_per_unit_diluted": 0.2169,
    "acfo_starting_point": 26500,
    "net_cfi": -4500,
    "data_quality": "strong"
  },

  "afcf_coverage": {                     // CONDITIONAL
    "afcf_debt_service_coverage": 0.40,  // AFCF / Debt Service
    "afcf_payout_ratio": 86.4,           // Distributions / AFCF
    "afcf_self_funding_ratio": 0.30,     // AFCF / (Debt Svc + Dist)
    "afcf_self_funding_capacity": -52000 // Negative = needs financing
  },

  "burn_rate_analysis": {                // CONDITIONAL
    "applicable": true,
    "monthly_burn_rate": 1916667,        // $/month
    "annualized_burn_rate": 23000000,
    "self_funding_ratio": 0.55,
    "net_financing_needs": 51000000
  },

  "cash_runway": {                       // CONDITIONAL
    "runway_months": 41.7,
    "runway_years": 3.5,
    "extended_runway_months": 119.8,     // With credit facilities
    "depletion_date": "2029-04-15"
  },

  "liquidity_risk": {                    // CONDITIONAL
    "risk_level": "LOW",                 // CRITICAL/HIGH/MODERATE/LOW
    "risk_score": 1,                     // 1-4 (1=low, 4=critical)
    "warning_flags": [],
    "assessment": "Adequate liquidity runway"
  },

  "dilution_analysis": {                 // CONDITIONAL
    "has_dilution_detail": true,
    "dilution_percentage": 2.01,
    "dilution_materiality": "low",       // minimal/low/moderate/high
    "material_instruments": ["restricted_units", "deferred_units"],
    "convertible_debt_risk": "none",     // none/low/moderate/high
    "governance_score": "enhanced"       // standard/enhanced
  },

  "leverage_metrics": {
    "debt_to_assets": 0.514,             // 51.4%
    "net_debt_to_ebitda": 8.88,
    "interest_coverage": 1.81,           // NOI / Interest
    "unencumbered_assets_ratio": 0.58    // 58%
  },

  "portfolio_metrics": {
    "occupancy_rate": 0.878,             // 87.8%
    "noi_margin": 0.520,                 // 52.0%
    "revenue_per_sf": 23.45,
    "total_gla_sf": 2500000
  },

  "validation": {
    "balance_sheet_balanced": true,
    "noi_margin_reasonable": true,
    "occupancy_rate_valid": true,
    "warnings": [],
    "errors": []
  }
}
```

### Per-Unit Calculation Logic

**Automatic per-unit calculations when share data available:**

```python
# Basic per-unit (common_units_outstanding required)
ffo_per_unit = ffo / common_units_outstanding

# Diluted per-unit (diluted_units_outstanding required)
ffo_per_unit_diluted = ffo / diluted_units_outstanding

# Applied to: FFO, AFFO, ACFO, AFCF
```

### Execution Metrics

- **Time:** < 1 second
- **Token Usage:** 0 tokens (pure Python)
- **Dependencies:** None (no external APIs)
- **Safety:** No hardcoded data, fails loudly if data missing

### Critical Requirements

✅ **Phase 2 JSON must be schema-valid** (validation required)
✅ **No hardcoded financial data** (all calculations use input JSON)
✅ **Per-unit calculations require share counts** in Phase 2
✅ **AFCF requires cash_flow_investing** data
✅ **Burn rate requires liquidity** data

---

## Phase 3.5: Data Enrichment (Optional)

### Purpose
Enrich Phase 3 metrics with market data, macro environment, and ML prediction.

### Inputs

| Input Type | Format | Source | Required |
|------------|--------|--------|----------|
| Phase 3 Calculated Metrics | JSON | Phase 3 output | Yes |
| Stock Ticker | String | Command argument | Yes |
| ML Model v2.2 | `.pkl` | `models/distribution_cut_logistic_regression_v2.2.pkl` | No (default) |

**Input File Path:**
```
Issuer_Reports/Example_REIT/temp/phase3_calculated_metrics.json
```

### Processing Tool

```bash
python scripts/enrich_phase4_data.py \
  --phase3 Issuer_Reports/Example_REIT/temp/phase3_calculated_metrics.json \
  --ticker REIT-UN.TO \
  --model models/distribution_cut_logistic_regression_v2.2.pkl
```

**Token Usage:** 0 tokens (Python + OpenBB API calls)

### Enrichment Components

**1. Market Data (OpenBB Platform)**

```bash
python scripts/openbb_market_monitor.py --ticker REIT-UN.TO
```

**Extracted Metrics:**
- Price stress detection (>30% decline from 52-week high)
- Volatility analysis (30d/90d/252d annualized)
- Momentum indicators (3/6/12-month returns)
- Risk score (0-100 scale)

**2. Macroeconomic Data (Bank of Canada + Federal Reserve)**

```bash
python scripts/openbb_macro_monitor.py --output data/macro.json
```

**Extracted Metrics:**
- Bank of Canada policy rate (Valet API - FREE)
- US Federal Reserve rate (FRED API - FREE, requires key)
- Rate cycle classification (easing/tightening)
- Credit environment score (0-100)
- Canada vs US rate differential

**3. Dividend History (OpenBB Platform)**

```bash
python scripts/openbb_data_collector.py --ticker REIT-UN.TO
```

**Extracted Metrics:**
- 10-15 years dividend history
- Distribution cut detection (>10% threshold)
- Recovery analysis (time to restore, recovery level %)
- TTM yield calculations

**4. Distribution Cut Prediction (ML Model v2.2)**

**Model Specifications:**
- Algorithm: Logistic Regression (sklearn)
- Features: 28 Phase 3 fundamentals
- Training: 24 observations (11 cuts, 13 controls)
- Performance: F1=0.870, ROC AUC=0.930

**Top 5 Predictors:**
1. monthly_burn_rate (1.10)
2. acfo_calculated (0.71)
3. available_cash (0.69)
4. total_available_liquidity (0.59)
5. dilution_materiality (0.58)

### Outputs

| Output File | Format | Size | Location |
|------------|--------|------|----------|
| Enriched Metrics | JSON | ~200-400KB | `Issuer_Reports/{Issuer}/temp/phase3_enriched_data.json` |

**Enriched JSON Structure:**

```json
{
  // All Phase 3 metrics (inherited)
  "issuer_name": "Example REIT",
  "ffo_metrics": { ... },
  "afcf_metrics": { ... },

  // NEW: Market data
  "market_data": {
    "ticker": "REIT-UN.TO",
    "price_current": 5.23,
    "price_52w_high": 12.45,
    "price_stress": true,            // >30% decline
    "price_decline_pct": -58.0,
    "volatility_30d": 0.45,          // Annualized
    "momentum_3m": -0.25,            // 3-month return
    "market_risk_score": 82          // 0-100 (higher = riskier)
  },

  // NEW: Macro environment
  "macro_environment": {
    "canada_policy_rate": 0.0475,    // 4.75%
    "us_fed_rate": 0.0525,           // 5.25%
    "rate_differential": -0.005,     // -50 bps
    "rate_cycle": "easing",          // easing/tightening/neutral
    "credit_stress_score": 65        // 0-100 (higher = more stress)
  },

  // NEW: Distribution history
  "distribution_history": {
    "years_covered": 15,
    "distribution_cuts": [
      {
        "date": "2020-03-15",
        "cut_percentage": -32.5,
        "recovery_time_months": 24,
        "recovery_level_pct": 85.0
      }
    ],
    "ttm_yield": 0.092               // 9.2%
  },

  // NEW: ML prediction
  "distribution_cut_prediction": {
    "model_version": "v2.2",
    "prediction_date": "2025-10-29",
    "cut_probability": 0.671,        // 67.1% probability
    "risk_level": "HIGH",            // VERY_LOW/LOW/MODERATE/HIGH/VERY_HIGH
    "confidence_interval": [0.55, 0.78],
    "top_risk_drivers": [
      {
        "feature": "monthly_burn_rate",
        "value": -10600000,
        "importance": 1.10,
        "interpretation": "Critical cash depletion"
      },
      {
        "feature": "acfo_calculated",
        "value": -5000000,
        "importance": 0.71,
        "interpretation": "Negative sustainable cash flow"
      },
      {
        "feature": "available_cash",
        "value": 17000000,
        "importance": 0.69,
        "interpretation": "Low cash reserves"
      }
    ],
    "model_performance": {
      "f1_score": 0.870,
      "roc_auc": 0.930,
      "accuracy": 0.875
    }
  }
}
```

### Execution Metrics

- **Time:** 10-15 seconds
- **Token Usage:** 0 tokens (Python + API calls)
- **Cost:** $0 (all free tier APIs)
- **Dependencies:** OpenBB Platform, internet connection

### Optional Nature

**Phase 3.5 is OPTIONAL** - Phase 4 and Phase 5 work with or without enrichment:
- If enriched data exists: Phase 4/5 use enhanced metrics
- If not enriched: Phase 4/5 use Phase 3 metrics only

---

## Phase 4: Credit Analysis Generation

### Purpose
Generate qualitative credit assessment using Claude Code agent.

### Inputs

| Input Type | Format | Source | Required |
|------------|--------|--------|----------|
| Phase 3 Metrics (or Enriched) | JSON | Phase 3/3.5 output | Yes |
| Agent Profile | Markdown | `.claude/agents/domain_expert/issuer_due_diligence_expert_slim.md` | Yes |

**Input File Path:**
```
Issuer_Reports/Example_REIT/temp/phase3_calculated_metrics.json
OR
Issuer_Reports/Example_REIT/temp/phase3_enriched_data.json  (if enriched)
```

### Processing Method

**Use Claude Code Task tool to invoke agent:**

```python
# Invoke issuer_due_diligence_expert_slim agent via Task tool
# Agent reads Phase 3 JSON and generates credit assessment
# Output saved to: Issuer_Reports/Example_REIT/temp/phase4_credit_analysis.md
```

**Token Usage:** ~12,000 tokens (~$0.30)

### Agent Analysis Framework

**Agent Profile:** `.claude/agents/domain_expert/issuer_due_diligence_expert_slim.md` (7.7KB)

**Analysis Sections:**

1. **Executive Summary**
   - Credit opinion (1-2 sentences)
   - Key credit factors (strengths/weaknesses)
   - Rating recommendation (if applicable)

2. **Factor 1: Business Profile**
   - Property portfolio analysis
   - Geographic diversification
   - Tenant quality and lease structure
   - Market position

3. **Factor 2: Operating Performance**
   - NOI trends and margins
   - Occupancy rates and lease renewals
   - Same-property growth
   - Revenue stability

4. **Factor 3: Cash Flow Generation**
   - FFO/AFFO/ACFO analysis
   - Distribution coverage ratios
   - Payout sustainability
   - Cash flow quality

5. **Factor 4: Capital Structure & Financial Flexibility**
   - Leverage metrics (Debt/Assets, Net Debt/EBITDA)
   - Interest coverage
   - Debt maturity profile
   - Liquidity position
   - Dilution analysis (if applicable)

6. **Factor 5: Financial Policy**
   - Distribution policy
   - Capital allocation strategy
   - Balance sheet management
   - Covenant compliance

7. **Liquidity & Burn Rate Analysis** (if applicable)
   - AFCF self-funding analysis
   - Monthly burn rate
   - Cash runway calculations
   - Liquidity risk assessment

8. **Distribution Cut Risk** (if enriched)
   - ML model prediction (v2.2)
   - Top risk drivers
   - Probability interpretation
   - Mitigating factors

9. **Peer Comparison**
   - 3-4 comparable REITs
   - Relative positioning
   - Competitive advantages/disadvantages

10. **Rating & Outlook**
    - Credit rating (if applicable)
    - Outlook (positive/stable/negative)
    - Key rating sensitivities
    - Monitoring factors

### Agent Enhancements (v1.0.1)

**Parallel Web Searches:** Agent uses parallel web searches for peer comparison research (Section 9), researching 3-4 comparable REITs simultaneously for improved performance.

### Outputs

| Output File | Format | Size | Location |
|------------|--------|------|----------|
| Credit Analysis | Markdown | ~30-50KB | `Issuer_Reports/{Issuer}/temp/phase4_credit_analysis.md` |
| Agent Prompt | Text | ~5KB | `Issuer_Reports/{Issuer}/temp/phase4_agent_prompt.txt` |

**Markdown Output Structure:**

```markdown
# Credit Analysis: Example REIT

**Analysis Date:** October 29, 2025
**Period Analyzed:** Q2 2025
**Analyst:** Claude Code Agent (issuer_due_diligence_expert_slim)

---

## Executive Summary

[2-3 paragraph credit opinion summary]

**Key Credit Strengths:**
- Strength 1
- Strength 2

**Key Credit Weaknesses:**
- Weakness 1
- Weakness 2

---

## Factor 1: Business Profile

[Detailed analysis of business profile...]

---

## Factor 2: Operating Performance

[Detailed analysis of operating performance...]

---

[... Sections 3-10 ...]

---

## Appendix: Data Sources

- Phase 3 calculated metrics: phase3_calculated_metrics.json
- ML prediction: Model v2.2 (67.1% cut probability)
- Market data: OpenBB Platform (REIT-UN.TO)
- Peer comparison: [List of 3-4 comparable REITs]
```

### Execution Metrics

- **Time:** 30-60 seconds
- **Token Usage:** ~12,000 tokens
- **Cost:** ~$0.30
- **Quality:** Professional Moody's-style analysis

### Critical Requirements

✅ **Agent must be invoked via Task tool** (DO NOT run Python scripts)
✅ **Phase 3 JSON must exist** before agent invocation
✅ **Agent output must be saved** to `phase4_credit_analysis.md`

---

## Phase 5: Final Report Generation

### Purpose
Generate final credit opinion report by populating markdown template with data from all phases.

### Inputs

| Input Type | Format | Source | Required |
|------------|--------|--------|----------|
| Phase 3 Metrics (or Enriched) | JSON | Phase 3/3.5 output | Yes |
| Phase 4 Credit Analysis | Markdown | Phase 4 output | Yes |
| Phase 2 Extracted Data | JSON | Phase 2 output | Yes |
| Report Template | Markdown | `templates/credit_opinion_template_enhanced.md` | Yes |

**Input File Paths:**
```
Issuer_Reports/Example_REIT/temp/
  ├── phase2_extracted_data.json
  ├── phase3_calculated_metrics.json (or phase3_enriched_data.json)
  └── phase4_credit_analysis.md
```

### Processing Tool

```bash
python scripts/generate_final_report.py \
  --template credit_opinion_template_enhanced.md \
  Issuer_Reports/Example_REIT/temp/phase3_calculated_metrics.json \
  Issuer_Reports/Example_REIT/temp/phase4_credit_analysis.md
```

**Token Usage:** 0 tokens (pure Python string replacement)

### Template Population Logic

**Template:** `templates/credit_opinion_template_enhanced.md` (100KB, 2000+ lines)

**Placeholder Categories:**

1. **Metadata** (Section 1)
   - `{{ISSUER_NAME}}` → "Example REIT"
   - `{{REPORT_DATE}}` → "October 29, 2025"
   - `{{PERIOD}}` → "Q2 2025"
   - `{{CURRENCY}}` → "CAD"

2. **Financial Metrics** (Section 2)
   - `{{FFO_TOTAL}}` → "$34,500,000"
   - `{{FFO_PER_UNIT}}` → "$0.3471"
   - `{{FFO_PER_UNIT_DILUTED}}` → "$0.3401"
   - `{{AFFO_TOTAL}}` → "$28,000,000"
   - `{{AFFO_PAYOUT_RATIO}}` → "85.7%"
   - ... (100+ financial placeholders)

3. **Dual-Table Reporting** (Sections 2.2, 2.5, 2.6, 2.7)
   - **Issuer-Reported vs REALPAC-Calculated**
   - Variance analysis (amount and percentage)
   - Coverage quality assessment (Strong/Adequate/Tight/Insufficient)

4. **Balance Sheet** (Section 3)
   - `{{TOTAL_ASSETS}}` → "$3,500,000,000"
   - `{{TOTAL_DEBT}}` → "$1,800,000,000"
   - `{{DEBT_TO_ASSETS}}` → "51.4%"

5. **Portfolio Details** (Section 4)
   - `{{TOTAL_GLA}}` → "2,500,000 SF"
   - `{{OCCUPANCY_RATE}}` → "87.8%"
   - `{{NOI_MARGIN}}` → "52.0%"

6. **Liquidity Analysis** (Section 5)
   - `{{AVAILABLE_CASH}}` → "$80,000,000"
   - `{{UNDRAWN_FACILITIES}}` → "$150,000,000"
   - `{{TOTAL_LIQUIDITY}}` → "$230,000,000"

7. **AFCF & Burn Rate** (Section 6 - if applicable)
   - `{{AFCF}}` → "$22,000,000"
   - `{{SELF_FUNDING_RATIO}}` → "0.30x"
   - `{{MONTHLY_BURN_RATE}}` → "$1,916,667"
   - `{{CASH_RUNWAY_MONTHS}}` → "41.7 months"
   - `{{LIQUIDITY_RISK_LEVEL}}` → "LOW"

8. **Distribution Cut Prediction** (Section 7 - if enriched)
   - `{{CUT_PROBABILITY}}` → "67.1%"
   - `{{RISK_LEVEL}}` → "HIGH"
   - `{{TOP_RISK_DRIVER_1}}` → "Monthly burn rate: -$10.6M"
   - `{{MODEL_VERSION}}` → "v2.2"

9. **Structural Considerations** (Section 8)
   - **Debt Structure** (parsed from Phase 4)
   - **Security & Collateral** (parsed from Phase 4)
   - **Perpetual Securities** (checked across Phase 2/3/4)

10. **Credit Analysis** (Section 9)
    - Entire Phase 4 markdown inserted

11. **Market & Macro** (Section 10 - if enriched)
    - `{{PRICE_STRESS}}` → "Yes (-58.0%)"
    - `{{VOLATILITY_30D}}` → "45.0%"
    - `{{RATE_CYCLE}}` → "Easing"
    - `{{CREDIT_STRESS_SCORE}}` → "65/100"

### Helper Functions

**Phase 5 Helper Functions** (lines 486-678 in `generate_final_report.py`):

1. `calculate_per_unit()` - Safe per-unit calculations with None handling
2. `calculate_payout_ratio()` - Payout % from per-unit metrics
3. `calculate_coverage_ratio()` - Coverage ratios (inverse of payout)
4. `assess_distribution_coverage()` - Quality assessment (Strong ≥1.3x, Adequate ≥1.1x, Tight ≥1.0x, Insufficient <1.0x)
5. `assess_self_funding_capacity()` - AFCF self-funding capability
6. `generate_reported_adjustments_list()` - Top 3-5 FFO→AFFO adjustments

**Phase 5 Parsing Functions** (lines 1007-1246):

1. `parse_debt_structure()` - Extracts credit facilities, covenant compliance from Phase 4
2. `parse_security_collateral()` - Extracts unencumbered assets, LTV from Phase 4
3. `check_perpetual_securities()` - Checks Phase 2/3/4 for perpetual securities

### Outputs

| Output File | Format | Size | Location |
|------------|--------|------|----------|
| Final Credit Report | Markdown | ~200-300KB | `Issuer_Reports/{Issuer}/reports/{TIMESTAMP}_Credit_Opinion_{Issuer}.md` |

**Output File Naming:**
```
Issuer_Reports/Example_REIT/reports/
  └── 2025-10-29_125045_Credit_Opinion_Example_REIT.md
```

**Report Structure:**

```markdown
# Credit Opinion: Example REIT

**Report Date:** October 29, 2025
**Period Analyzed:** Q2 2025 (June 30, 2025)
**Currency:** CAD Thousands (unless noted)

---

## Table of Contents

1. Executive Summary
2. Financial Performance Metrics
   2.1 Funds From Operations (FFO)
   2.2 Adjusted Funds From Operations (AFFO)
   2.3 Adjusted Cash Flow from Operations (ACFO)
   2.4 Adjusted Free Cash Flow (AFCF)
   2.5 Coverage Ratios
   2.6 Bridge & Gap Analysis
   2.7 Self-Funding Analysis
3. Balance Sheet Analysis
4. Portfolio Overview
5. Liquidity & Debt Analysis
6. Burn Rate & Cash Runway Analysis
7. Distribution Cut Risk Assessment
8. Structural Considerations
9. Qualitative Credit Assessment
10. Market & Macro Environment
11. Peer Comparison
12. Rating & Outlook
13. Appendices

---

## 1. Executive Summary

[Populated from Phase 4 executive summary]

---

## 2. Financial Performance Metrics

### 2.1 Funds From Operations (FFO)

| Metric | Reported | Calculated | Variance |
|--------|----------|------------|----------|
| FFO (Total) | $34,500 | $34,500 | $0 (0.0%) |
| FFO per Unit (Basic) | $0.3471 | $0.3471 | $0.0000 |
| FFO per Unit (Diluted) | $0.3401 | $0.3401 | $0.0000 |

[... complete dual-table reporting ...]

---

[... Sections 3-13 ...]

---

## Appendix A: Data Sources

- Financial Statements: Q2 2025 Financial Statements (June 30, 2025)
- MD&A: Q2 2025 Management Discussion & Analysis
- Market Data: OpenBB Platform (TMX, YFinance)
- Macro Data: Bank of Canada Valet API, Federal Reserve FRED
- ML Prediction: Distribution Cut Model v2.2

## Appendix B: Methodology

- FFO/AFFO/ACFO: REALPAC White Paper (2022)
- AFCF: Custom methodology (see docs/AFCF_Research_Proposal.md)
- Burn Rate: Custom methodology (see GitHub Issue #7)
- ML Model: Logistic Regression v2.2 (see models/README.md)

## Appendix C: Disclaimers

[Institutional-grade disclaimer from README.md]

---

**Report Generated by:** Claude Code Real Estate Issuer Credit Analysis Pipeline v1.0.15
**Generation Date:** October 29, 2025 12:50:45 UTC
**Model:** Distribution Cut Prediction v2.2
```

### Execution Metrics

- **Time:** < 1 second
- **Token Usage:** 0 tokens (pure Python)
- **Report Size:** ~200-300KB
- **Placeholder Population:** 90%+ (varies by data availability)

### Critical Requirements

✅ **All input files must exist** (Phase 2, Phase 3, Phase 4)
✅ **Template file must be valid markdown**
✅ **Output directory must have write permissions**
✅ **Timestamp ensures unique filenames** (no overwrites)

---

## Complete Data Flow Diagram

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    INPUT: USER-PROVIDED PDFs                          ║
║                                                                       ║
║  • Financial Statements PDF (30-50 pages)                            ║
║  • MD&A PDF (20-40 pages)                                            ║
║  • Issuer Name (string)                                              ║
╚═════════════════════════════════╤═════════════════════════════════════╝
                                  │
                                  ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                      PHASE 1: PDF → MARKDOWN                          ║
║                                                                       ║
║  Tool: preprocess_pdfs_enhanced.py (PyMuPDF + Camelot)               ║
║        OR preprocess_pdfs_docling.py (Docling FAST)                  ║
║                                                                       ║
║  Processing:                                                          ║
║    - Extract text and tables from PDFs                               ║
║    - Convert to structured markdown                                  ║
║    - Preserve financial statement hierarchies                        ║
║                                                                       ║
║  Time: 30 seconds (PyMuPDF) or 20 minutes (Docling)                  ║
║  Tokens: 0  |  Cost: $0.00                                           ║
╚═════════════════════════════════╤═════════════════════════════════════╝
                                  │
                                  ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                  OUTPUT: PHASE 1 MARKDOWN FILES                       ║
║                                                                       ║
║  Issuer_Reports/{Issuer}/temp/phase1_markdown/                       ║
║    ├── statements.md (~300KB, 113 tables)                            ║
║    └── mda.md (~245KB, text + tables)                                ║
╚═════════════════════════════════╤═════════════════════════════════════╝
                                  │
                                  ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                      PHASE 2: MARKDOWN → JSON                         ║
║                                                                       ║
║  Tool: extract_key_metrics_efficient.py                              ║
║  Schema: .claude/knowledge/phase2_extraction_schema.json             ║
║                                                                       ║
║  Processing:                                                          ║
║    - Read markdown files via Claude Code Read tool                   ║
║    - Extract structured financial data                               ║
║    - Validate against JSON schema → Save to JSON                     ║
║                                                                       ║
║  Time: 5-10 seconds  |  Tokens: ~1,000  |  Cost: $0.00              ║
╚═════════════════════════════════╤═════════════════════════════════════╝
                                  │
                                  ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                   OUTPUT: PHASE 2 EXTRACTED JSON                      ║
║                                                                       ║
║  File: phase2_extracted_data.json (~50-100KB)                        ║
║                                                                       ║
║  Contents:                                                            ║
║    • Balance sheet (flat structure)                                  ║
║    • Income statement (top-level values)                             ║
║    • FFO/AFFO/ACFO reconciliations (43 REALPAC adjustments)          ║
║    • Cash flows (operating, investing, financing)                    ║
║    • Portfolio, debt, liquidity, distributions, dilution             ║
╚═════════════════════════════════╤═════════════════════════════════════╝
                                  │
                                  ▼
╔═══════════════════════════════════════════════════════════════════════╗
║               VALIDATION: SCHEMA COMPLIANCE CHECK                     ║
║                                                                       ║
║  Tool: validate_extraction_schema.py                                 ║
║                                                                       ║
║  Checks:                                                              ║
║    ✓ Flat structure for balance_sheet                                ║
║    ✓ Top-level values for income_statement                           ║
║    ✓ No null values in numeric fields                                ║
║    ✓ Decimal format for rates (0-1 range)                            ║
║                                                                       ║
║  ⚠️  CRITICAL: Phase 3 will FAIL if validation fails                 ║
╚═════════════════════════════════╤═════════════════════════════════════╝
                                  │
                                  ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                 PHASE 3: JSON → CALCULATED METRICS                    ║
║                                                                       ║
║  Tool: calculate_credit_metrics.py                                   ║
║                                                                       ║
║  Calculations:                                                        ║
║    • FFO, AFFO, ACFO (per-unit: basic & diluted)                    ║
║    • AFCF (if cash flow data present)                               ║
║    • Burn rate & cash runway (if liquidity data present)            ║
║    • Dilution analysis (if dilution_detail present)                 ║
║    • Leverage, liquidity, portfolio metrics                          ║
║                                                                       ║
║  Functions: calculate_ffo_from_components(), calculate_affo(),       ║
║    calculate_acfo(), calculate_afcf(), calculate_burn_rate(),        ║
║    calculate_cash_runway(), analyze_dilution(), etc.                 ║
║                                                                       ║
║  Time: < 1 second  |  Tokens: 0  |  Cost: $0.00                     ║
╚═════════════════════════════════╤═════════════════════════════════════╝
                                  │
                                  ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                OUTPUT: PHASE 3 CALCULATED METRICS                     ║
║                                                                       ║
║  File: phase3_calculated_metrics.json (~150-300KB)                   ║
║                                                                       ║
║  Contents:                                                            ║
║    • ffo_metrics, affo_metrics, acfo_metrics, afcf_metrics          ║
║    • afcf_coverage, burn_rate_analysis, cash_runway                 ║
║    • dilution_analysis, leverage_metrics, liquidity_metrics         ║
║    • portfolio_metrics, validation                                   ║
╚═════════════════════════════════╤═════════════════════════════════════╝
                                  │
                                  ▼
╔═══════════════════════════════════════════════════════════════════════╗
║             PHASE 3.5 (OPTIONAL): DATA ENRICHMENT                     ║
║                                                                       ║
║  Tool: enrich_phase4_data.py                                         ║
║  Model: distribution_cut_logistic_regression_v2.2.pkl                ║
║                                                                       ║
║  Data Sources:                                                        ║
║    1. OpenBB Platform: Market data (TMX, YFinance)                  ║
║    2. OpenBB Platform: Dividend history (10-15 years)               ║
║    3. Bank of Canada: Policy rate (Valet API)                       ║
║    4. Federal Reserve: Fed rate (FRED API)                          ║
║    5. ML Model v2.2: Distribution cut prediction (28 features)      ║
║                                                                       ║
║  Processing:                                                          ║
║    • Market risk (price stress, volatility, momentum)               ║
║    • Macro environment (rate cycle, credit stress)                  ║
║    • Dividend history (cuts, recovery patterns)                     ║
║    • ML prediction (cut probability, risk level, drivers)           ║
║                                                                       ║
║  Time: 10-15 seconds  |  Tokens: 0  |  Cost: $0.00 (free APIs)     ║
╚═════════════════════════════════╤═════════════════════════════════════╝
                                  │
                                  ▼
╔═══════════════════════════════════════════════════════════════════════╗
║              OUTPUT: PHASE 3 ENRICHED METRICS (OPTIONAL)              ║
║                                                                       ║
║  File: phase3_enriched_data.json (~200-400KB)                        ║
║                                                                       ║
║  Additional Contents (beyond Phase 3):                               ║
║    • market_data, macro_environment                                  ║
║    • distribution_history, distribution_cut_prediction               ║
╚═════════════════════════════════╤═════════════════════════════════════╝
                                  │
                                  ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                PHASE 4: CREDIT ANALYSIS GENERATION                    ║
║                                                                       ║
║  Method: Invoke issuer_due_diligence_expert_slim via Task tool      ║
║  Agent: .claude/agents/domain_expert/issuer_due_diligence_...       ║
║                                                                       ║
║  Processing:                                                          ║
║    • Read Phase 3 metrics (or enriched data)                        ║
║    • Analyze 5 credit factors (business, operations, cash flow,     ║
║      capital structure, financial policy)                            ║
║    • Assess liquidity & burn rate                                    ║
║    • Evaluate distribution cut risk (if enriched)                    ║
║    • Research 3-4 peer REITs (parallel web searches)                ║
║    • Provide rating & outlook                                        ║
║                                                                       ║
║  Time: 30-60 seconds  |  Tokens: ~12,000  |  Cost: ~$0.30          ║
╚═════════════════════════════════╤═════════════════════════════════════╝
                                  │
                                  ▼
╔═══════════════════════════════════════════════════════════════════════╗
║              OUTPUT: PHASE 4 CREDIT ANALYSIS MARKDOWN                 ║
║                                                                       ║
║  File: phase4_credit_analysis.md (~30-50KB)                          ║
║                                                                       ║
║  Contents:                                                            ║
║    • Executive summary                                               ║
║    • 5 credit factors analysis                                       ║
║    • Liquidity & burn rate analysis                                  ║
║    • Distribution cut risk (if enriched)                             ║
║    • Peer comparison, rating & outlook                               ║
╚═════════════════════════════════╤═════════════════════════════════════╝
                                  │
                                  ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                 PHASE 5: FINAL REPORT GENERATION                      ║
║                                                                       ║
║  Tool: generate_final_report.py                                      ║
║  Template: templates/credit_opinion_template_enhanced.md             ║
║                                                                       ║
║  Inputs:                                                              ║
║    • Phase 2: phase2_extracted_data.json                             ║
║    • Phase 3: phase3_calculated_metrics.json (or enriched)           ║
║    • Phase 4: phase4_credit_analysis.md                              ║
║                                                                       ║
║  Processing:                                                          ║
║    • Load all inputs → Populate 2000+ template placeholders          ║
║    • Generate dual-table reporting (reported vs calculated)          ║
║    • Parse structural considerations from Phase 4                    ║
║    • Format currency/percentages → Insert Phase 4 analysis           ║
║    • Add disclaimers and appendices → Save timestamped report        ║
║                                                                       ║
║  Time: < 1 second  |  Tokens: 0  |  Cost: $0.00                     ║
╚═════════════════════════════════╤═════════════════════════════════════╝
                                  │
                                  ▼
╔═══════════════════════════════════════════════════════════════════════╗
║                 OUTPUT: FINAL CREDIT OPINION REPORT                   ║
║                                                                       ║
║  File: {YYYY-MM-DD_HHMMSS}_Credit_Opinion_{Issuer}.md               ║
║  Location: Issuer_Reports/{Issuer}/reports/                          ║
║  Size: ~200-300KB                                                     ║
║                                                                       ║
║  Contents (13 Sections):                                              ║
║    1. Executive Summary                                              ║
║    2. Financial Performance (FFO/AFFO/ACFO/AFCF, coverage ratios)   ║
║    3. Balance Sheet Analysis                                         ║
║    4. Portfolio Overview                                             ║
║    5. Liquidity & Debt Analysis                                      ║
║    6. Burn Rate & Cash Runway                                        ║
║    7. Distribution Cut Risk                                          ║
║    8. Structural Considerations                                      ║
║    9. Qualitative Credit Assessment (Phase 4)                        ║
║   10. Market & Macro Environment                                     ║
║   11. Peer Comparison                                                ║
║   12. Rating & Outlook                                               ║
║   13. Appendices (sources, methodology, disclaimers)                 ║
║                                                                       ║
║  Format: Professional Moody's-style credit opinion                   ║
║  Completeness: 90%+ placeholder population                           ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

## Summary Metrics

### Overall Pipeline Performance

| Metric | Value |
|--------|-------|
| **Total Phases** | 5 (+ 1 optional enrichment) |
| **Total Execution Time** | ~60 seconds (PyMuPDF) or ~20 minutes (Docling) |
| **Total Token Usage** | ~13,000 tokens |
| **Total Cost** | ~$0.30 per analysis |
| **Input Size** | ~50-90 pages (2 PDFs) |
| **Output Size** | ~200-300KB (final report) |
| **Success Rate** | 100% (sequential architecture prevents failures) |

### Phase-by-Phase Breakdown

| Phase | Time | Tokens | Cost | Dependencies |
|-------|------|--------|------|--------------|
| **Phase 1** | 30s-20min | 0 | $0.00 | PyMuPDF/Docling |
| **Phase 2** | 5-10s | ~1K | $0.00 | Phase 1 complete |
| **Phase 3** | <1s | 0 | $0.00 | Phase 2 valid JSON |
| **Phase 3.5** | 10-15s | 0 | $0.00 | Phase 3 complete (optional) |
| **Phase 4** | 30-60s | ~12K | ~$0.30 | Phase 3 complete |
| **Phase 5** | <1s | 0 | $0.00 | Phases 2/3/4 complete |

### Token Efficiency

| Approach | Tokens | Cost | Status |
|----------|--------|------|--------|
| **Original (Embedded PDFs)** | 121,500 | ~$3.04 | Deprecated (context errors) |
| **v1.0.x (Sequential Markdown-First)** | 13,000 | ~$0.30 | Production (100% success) |
| **Efficiency Gain** | **89% reduction** | **90% cost reduction** | ✅ |

---

## File Dependency Graph

```
INPUT: Financial Statement PDFs (2 files)
   │
   ├──▶ PHASE 1: PDF → Markdown
   │      ├── statements.md (300KB)
   │      └── mda.md (245KB)
   │
   ├──▶ PHASE 2: Markdown → JSON
   │      └── phase2_extracted_data.json (50-100KB)
   │            │
   │            ├──▶ VALIDATION: Schema check (MANDATORY)
   │            │
   │            └──▶ PHASE 3: JSON → Calculated Metrics
   │                   └── phase3_calculated_metrics.json (150-300KB)
   │                         │
   │                         ├──▶ PHASE 3.5 (OPTIONAL): Enrichment
   │                         │      └── phase3_enriched_data.json (200-400KB)
   │                         │
   │                         └──▶ PHASE 4: Credit Analysis Generation
   │                                └── phase4_credit_analysis.md (30-50KB)
   │
   └──▶ PHASE 5: Final Report Generation
          │
          ├── Input 1: phase2_extracted_data.json
          ├── Input 2: phase3_calculated_metrics.json (or enriched)
          ├── Input 3: phase4_credit_analysis.md
          │
          └── Output: {TIMESTAMP}_Credit_Opinion_{Issuer}.md (200-300KB)

SEQUENTIAL DEPENDENCIES:
  Phase 1 MUST complete → Phase 2 can start
  Phase 2 MUST complete → Phase 3 can start
  Phase 3 MUST complete → Phase 3.5 (optional) or Phase 4 can start
  Phase 4 MUST complete → Phase 5 can start
  Phase 5 requires: Phase 2 + Phase 3 + Phase 4 outputs
```

---

## Critical Success Factors

### Sequential Processing Requirements

✅ **Phase 1 MUST complete before Phase 2** (markdown files must exist)
✅ **Phase 2 MUST be schema-valid before Phase 3** (validate before proceeding)
✅ **Phase 3 MUST complete before Phase 4** (metrics JSON must exist)
✅ **Phases 2, 3, 4 MUST complete before Phase 5** (all inputs required)

### Schema Compliance

✅ **Flat structures** for balance_sheet (no nested objects)
✅ **Top-level values** for income_statement (not nested by period)
✅ **No null values** in numeric fields (use 0)
✅ **Decimal rates** (0-1 range, not percentages)

### Data Quality

✅ **Financial statements must be complete** (balance sheet, income statement, cash flows)
✅ **FFO/AFFO/ACFO reconciliations required** (26 REALPAC adjustments)
✅ **Share counts required** for per-unit calculations (basic and diluted)
✅ **Cash flow data required** for AFCF (investing activities)
✅ **Liquidity data required** for burn rate (cash, credit facilities)

### Agent Invocation

✅ **Phase 4 MUST use Task tool** to invoke agent (not Python scripts)
✅ **Agent output MUST be saved** to phase4_credit_analysis.md
✅ **Agent has parallel web search capability** for peer research

### Template Population

✅ **Template file must exist** and be valid markdown
✅ **All Phase 2/3/4 files must exist** before Phase 5
✅ **Timestamps ensure unique filenames** (no overwrites)
✅ **Placeholder population is automatic** (90%+ coverage)

---

## Error Handling & Validation

### Common Errors

| Error | Phase | Cause | Solution |
|-------|-------|-------|----------|
| **Missing required field: balance_sheet.total_assets** | Phase 3 | Nested structure in Phase 2 JSON | Flatten balance_sheet to top level |
| **TypeError: unsupported operand type(s) for /: 'NoneType' and 'int'** | Phase 3 | null value in numeric field | Replace null with 0 in Phase 2 |
| **Missing required field: income_statement.noi** | Phase 3 | Nested quarterly data only | Add top-level values in Phase 2 |
| **Schema validation failed** | Phase 2 → 3 | Schema not followed | Check `.claude/knowledge/SCHEMA_README.md` |
| **File not found: phase1_markdown/*.md** | Phase 2 | Phase 1 not complete | Wait for Phase 1 to finish |
| **Agent not found** | Phase 4 | Incorrect invocation method | Use Task tool, not Python script |

### Validation Checkpoints

1. **After Phase 1:** Verify markdown files exist
2. **After Phase 2:** Run `validate_extraction_schema.py` (MANDATORY)
3. **After Phase 3:** Verify calculated metrics JSON exists and is valid
4. **After Phase 4:** Verify credit analysis markdown exists
5. **After Phase 5:** Verify final report generated with timestamp

---

## Appendix: Complete File Listing

### Input Files (User-Provided)

```
/workspace/
├── financial_statements.pdf        (User input)
└── mda.pdf                          (User input)
```

### Phase 1 Outputs

```
Issuer_Reports/{Issuer}/temp/phase1_markdown/
├── financial_statements.md         (~300KB, 113 tables)
└── mda.md                           (~245KB, text + tables)
```

### Phase 2 Outputs

```
Issuer_Reports/{Issuer}/temp/
├── phase2_extracted_data.json      (~50-100KB, schema-validated)
└── phase2_extraction_prompt.txt    (~5KB, extraction prompt log)
```

### Phase 3 Outputs

```
Issuer_Reports/{Issuer}/temp/
└── phase3_calculated_metrics.json  (~150-300KB, all credit metrics)
```

### Phase 3.5 Outputs (Optional)

```
Issuer_Reports/{Issuer}/temp/
└── phase3_enriched_data.json       (~200-400KB, Phase 3 + market/macro/ML)
```

### Phase 4 Outputs

```
Issuer_Reports/{Issuer}/temp/
├── phase4_credit_analysis.md       (~30-50KB, qualitative assessment)
└── phase4_agent_prompt.txt         (~5KB, agent prompt log)
```

### Phase 5 Outputs

```
Issuer_Reports/{Issuer}/reports/
└── {YYYY-MM-DD_HHMMSS}_Credit_Opinion_{Issuer}.md  (~200-300KB, final report)
```

### Configuration Files

```
.claude/
├── knowledge/
│   ├── phase2_extraction_schema.json           (Authoritative schema)
│   ├── COMPREHENSIVE_EXTRACTION_GUIDE.md      (Extraction guide)
│   └── SCHEMA_README.md                        (Complete docs)
├── agents/
│   └── domain_expert/
│       └── issuer_due_diligence_expert_slim.md (Phase 4 agent)
└── commands/
    ├── analyzeREissuer.md                      (Main command)
    └── analyzeREissuer-docling.md              (Docling variant)

templates/
└── credit_opinion_template_enhanced.md         (Phase 5 template)

scripts/
├── preprocess_pdfs_enhanced.py                 (Phase 1 - PyMuPDF)
├── preprocess_pdfs_docling.py                  (Phase 1 - Docling)
├── extract_key_metrics_efficient.py            (Phase 2)
├── validate_extraction_schema.py               (Phase 2 validation)
├── calculate_credit_metrics.py                 (Phase 3)
├── enrich_phase4_data.py                       (Phase 3.5)
├── openbb_market_monitor.py                    (Phase 3.5 - market data)
├── openbb_macro_monitor.py                     (Phase 3.5 - macro data)
├── openbb_data_collector.py                    (Phase 3.5 - dividend history)
└── generate_final_report.py                    (Phase 5)

models/
├── distribution_cut_logistic_regression_v2.2.pkl  (Production model)
└── archive/
    └── distribution_cut_logistic_regression_v2.1_DEPRECATED.pkl
```

---

## Document Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-29 | Initial architectural documentation |

---

**END OF PIPELINE ARCHITECTURE DOCUMENT**
