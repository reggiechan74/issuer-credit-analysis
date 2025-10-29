# Burn Rate and Cash Flow Analysis Implementation - Technical Report

**Date:** October 21, 2025
**Version:** v1.0.7+ Analysis
**Status:** Current Implementation Review

---

## 1. Executive Summary

The codebase implements a sophisticated burn rate and cash flow analysis pipeline (v1.0.7+) that measures forward-looking liquidity stress when AFCF (Adjusted Free Cash Flow) cannot cover mandatory financing obligations. The implementation is split across multiple modules with comprehensive data validation, error handling, and credit assessment capabilities.

**Key Components:**
- Burn rate calculation from negative AFCF scenarios
- Cash runway analysis (with extended liquidity runway)
- Liquidity risk assessment with 4-tier classification system
- Sustainable burn rate analysis
- Full integration with Phase 2→3→5 data pipeline

---

## 2. Burn Rate Calculation Implementation

### 2.1 Core Function: `calculate_burn_rate()`

**Location:** `/workspaces/issuer-credit-analysis/scripts/calculate_credit_metrics/burn_rate.py` (lines 9-129)

**Function Signature:**
```python
def calculate_burn_rate(financial_data, afcf_metrics, afcf_coverage=None):
    """
    Calculate monthly burn rate when AFCF cannot cover mandatory financing obligations
    
    Returns: dict with keys:
    - applicable: bool (True when AFCF < Mandatory Obligations)
    - monthly_burn_rate: float or None
    - period_burn_rate: float or None (deficit for reporting period)
    - period_months: int or None
    - afcf: float
    - mandatory_obligations: float or None
    - self_funding_ratio: float or None (AFCF / Mandatory Obligations)
    - reason: str (explanation if not applicable)
    - data_quality: str ('strong', 'moderate', 'limited', 'none')
    """
```

**Key Algorithm:**
```
Mandatory Obligations = Total Debt Service + Distributions
                      = (Period Interest + Principal Repayments) + (Common Dist + Preferred Dist + NCI Dist)

Period Deficit = AFCF - Mandatory Obligations (when AFCF < Obligations)
Monthly Burn Rate = Period Deficit / Period Months

Self-Funding Ratio = AFCF / Mandatory Obligations
                   (Indicates % of obligations covered by AFCF)
```

**Critical Design Notes:**
1. **No New Financing Subtraction:** Burn rate ASSUMES no future capital raises - this is a stress test
2. **Period-Based Calculation:** Uses actual period amounts (Q2 = 6 months), not annualized
3. **Applicable Only When AFCF < Obligations:** If AFCF exceeds obligations, burn rate is N/A
4. **Mandatory vs Optional:** Excludes new financing (optional), focuses only on mandatory obligations

**Input Requirements:**
```python
financial_data = {
    'cash_flow_financing': {
        'debt_principal_repayments': -18000,  # Negative (outflow)
        'distributions_common': -20000,       # Negative (outflow)
        'distributions_preferred': 0,
        'distributions_nci': 0,
        # Note: new_debt_issuances, equity_issuances NOT used in burn rate
    },
    'coverage_ratios': {
        'period_interest_expense': 18000,     # PERIOD interest (not annualized)
        'annualization_factor': 2,             # Q2=2, Q3=1.33, Q4=1, etc.
    }
}

afcf_metrics = {
    'afcf': 25000,
    'data_quality': 'strong'
}
```

**Output Example (Negative AFCF Scenario):**
```json
{
  "applicable": true,
  "monthly_burn_rate": -1916667,
  "period_burn_rate": -23000000,
  "period_months": 12,
  "afcf": 28000000,
  "mandatory_obligations": 51000000,
  "self_funding_ratio": 0.55,
  "data_quality": "complete"
}
```

**Output Example (Positive AFCF Scenario):**
```json
{
  "applicable": false,
  "monthly_burn_rate": null,
  "period_burn_rate": null,
  "afcf": 40000,
  "mandatory_obligations": 32000,
  "self_funding_ratio": 1.25,
  "reason": "AFCF covers mandatory obligations - surplus of $8,000 for the 12-month period",
  "monthly_surplus": 666.67,
  "data_quality": "complete"
}
```

---

## 2.2 Data Flow: Phase 2 → Burn Rate Calculation

### Phase 2 Extraction Data (Required)

**Location:** `.claude/knowledge/phase2_extraction_schema.json` (lines 739-776)

**Liquidity Section:**
```json
{
  "liquidity": {
    "cash_and_equivalents": 65000,          # Balance sheet cash
    "marketable_securities": 20000,         # Short-term investments
    "restricted_cash": 5000,                # Tied up / not available
    "undrawn_credit_facilities": 150000,    # Available credit facility capacity
    "credit_facility_limit": 200000,        # Total facility limit
    "available_cash": 80000,                # Calc: Cash + Securities - Restricted
    "total_available_liquidity": 230000,    # Calc: Available Cash + Undrawn Facilities
    "data_source": "balance sheet + note 12"
  }
}
```

**Cash Flow Financing Section:**
```json
{
  "cash_flow_financing": {
    "debt_principal_repayments": -15000,    # Period principal paid (negative)
    "new_debt_issuances": 10000,            # New borrowing (positive, NOT used in burn)
    "distributions_common": -18000,         # Period distributions (negative)
    "distributions_preferred": 0,
    "distributions_nci": 0,
    "equity_issuances": 5000,               # New equity (NOT used in burn)
    "total_cff": -18000                     # For reconciliation
  }
}
```

**Coverage Ratios Section:**
```json
{
  "coverage_ratios": {
    "noi_interest_coverage": 1.32,
    "period_interest_expense": 18000,       # CRITICAL: Period interest, not annualized
    "annualized_interest_expense": 36000,   # For context
    "annualization_factor": 2,              # Q2 = factor of 2
    "detected_period": "semi_annual_q2"
  }
}
```

---

## 2.3 Integration with AFCF Calculation

**Location:** `/workspaces/issuer-credit-analysis/scripts/calculate_credit_metrics/afcf.py` (lines 8-165)

**AFCF Formula:**
```
AFCF = ACFO + Net Cash Flow from Investing Activities
```

**Where used in burn rate:**
```python
# In calculate_burn_rate()
afcf = afcf_metrics['afcf']  # Starting point
mandatory_obligations = total_debt_service + total_distributions

# When AFCF < Mandatory Obligations
burn_applicable = afcf < mandatory_obligations
monthly_burn = (afcf - mandatory_obligations) / period_months
```

**AFCF Prerequisites:**
1. ACFO must be calculated first (from acfo_components)
2. CFI (Cash Flow from Investing) data must be available
3. Both sustaining and growth capital expenditures separated

---

## 3. Cash Runway Analysis

### 3.1 Core Function: `calculate_cash_runway()`

**Location:** `/workspaces/issuer-credit-analysis/scripts/calculate_credit_metrics/burn_rate.py` (lines 132-257)

**Function Signature:**
```python
def calculate_cash_runway(financial_data, burn_rate_metrics):
    """
    Calculate months until cash depletion based on burn rate
    
    Runway = Available Cash / Monthly Burn Rate
    Extended Runway = (Available Cash + Undrawn Facilities) / Monthly Burn Rate
    
    Returns: dict with keys:
    - runway_months: float (months until cash-only depletion)
    - runway_years: float
    - extended_runway_months: float (including credit facility access)
    - extended_runway_years: float
    - depletion_date: str (YYYY-MM-DD estimated date)
    - extended_depletion_date: str (with credit facility access)
    - available_cash: float
    - total_available_liquidity: float
    - data_quality: str
    - error: str or None
    """
```

**Algorithm:**
```
Available Cash = Cash + Marketable Securities - Restricted Cash
Total Liquidity = Available Cash + Undrawn Credit Facilities

Runway (months) = Available Cash / |Monthly Burn Rate|
Extended Runway = Total Liquidity / |Monthly Burn Rate|

Depletion Date = Reporting Date + (Runway Months × 30 days)
```

**Input Requirements:**
- Burn rate must be applicable (negative AFCF)
- Liquidity data must be populated
- Monthly burn rate must be non-zero

**Output Example:**
```json
{
  "runway_months": 41.7,
  "runway_years": 3.5,
  "extended_runway_months": 119.8,
  "extended_runway_years": 10.0,
  "depletion_date": "2029-04-15",
  "extended_depletion_date": "2035-10-21",
  "available_cash": 80000000,
  "total_available_liquidity": 230000000,
  "data_quality": "strong",
  "error": null
}
```

**Data Quality Assessment:**
- `strong`: Has cash, marketable_securities, restricted_cash, undrawn_facilities
- `moderate`: Has cash and some other fields
- `limited`: Has only cash
- `none`: No liquidity data

---

## 3.2 Liquidity Risk Assessment

### 3.3 Core Function: `assess_liquidity_risk()`

**Location:** `/workspaces/issuer-credit-analysis/scripts/calculate_credit_metrics/burn_rate.py` (lines 260-373)

**Risk Classification System:**

| Risk Level | Runway | Risk Score | Action Required |
|-----------|--------|-----------|-----------------|
| **CRITICAL** | < 6 months | 4 | Immediate financing or distribution cut |
| **HIGH** | 6-12 months | 3 | Capital raise within 6 months required |
| **MODERATE** | 12-24 months | 2 | Plan financing within 12 months |
| **LOW** | > 24 months | 1 | Adequate runway |
| **N/A** | No burn rate | 0 | AFCF sufficient or data missing |

**Output Example (HIGH Risk):**
```json
{
  "risk_level": "HIGH",
  "risk_score": 3,
  "assessment": "⚠️ Near-term capital raise required - runway 6-12 months",
  "warning_flags": [
    "Limited financing window",
    "Capital raise needed within 6 months",
    "Potential covenant concerns"
  ],
  "recommendations": [
    "Initiate capital raise process immediately",
    "Consider distribution reduction",
    "Identify asset sales to bridge liquidity gap",
    "Defer growth capital expenditures",
    "Negotiate credit facility extensions"
  ],
  "data_quality": "strong"
}
```

---

## 4. Sustainable Burn Rate Analysis

### 4.1 Core Function: `calculate_sustainable_burn_rate()`

**Location:** `/workspaces/issuer-credit-analysis/scripts/calculate_credit_metrics/burn_rate.py` (lines 376-462)

**Purpose:** Identify if current burn rate exceeds sustainable levels and quantify overspend needing correction.

**Function Signature:**
```python
def calculate_sustainable_burn_rate(financial_data, burn_rate_metrics, target_runway_months=24):
    """
    Calculate maximum sustainable monthly burn rate to maintain target runway
    
    Args:
        target_runway_months: Desired runway length (default: 24 months)
    
    Returns: dict with keys:
    - target_runway_months: int
    - sustainable_monthly_burn: float (maximum to maintain runway)
    - actual_monthly_burn: float (current burn rate)
    - excess_burn_per_month: float (overspend = actual - sustainable)
    - excess_burn_annualized: float (overspend × 12)
    - status: str ('Above sustainable', 'Below sustainable', 'N/A')
    - available_cash: float
    - data_quality: str
    """
```

**Algorithm:**
```
Sustainable Monthly Burn = Available Cash / Target Runway (months)
Excess Burn Per Month = Actual Monthly Burn - Sustainable Monthly Burn

If Excess Burn > 0: REIT is overspending relative to target runway
If Excess Burn < 0: REIT has cushion below target runway
```

**Output Example:**
```json
{
  "target_runway_months": 24,
  "sustainable_monthly_burn": 3333333,
  "actual_monthly_burn": 1916667,
  "excess_burn_per_month": -1416666,
  "excess_burn_annualized": -17000000,
  "status": "Below sustainable - $1,417,000/month cushion",
  "available_cash": 80000000,
  "data_quality": "strong"
}
```

**Credit Interpretation:**
- **Negative excess burn:** REIT is well-positioned (can extend runway)
- **Positive excess burn:** REIT overspending relative to target
- **Example:** If excess = $1M/month, REIT burning $1M more than sustainable

---

## 5. Complete Data Flow Diagram

```
Phase 2 Extraction
├─ balance_sheet
│  ├─ cash
│  ├─ total_assets
│  └─ debt_components
│
├─ income_statement
│  ├─ interest_expense
│  ├─ noi
│  └─ revenue
│
├─ liquidity
│  ├─ cash_and_equivalents
│  ├─ marketable_securities
│  ├─ restricted_cash
│  ├─ undrawn_credit_facilities
│  └─ credit_facility_limit
│
├─ cash_flow_financing
│  ├─ debt_principal_repayments
│  ├─ distributions_common
│  ├─ distributions_preferred
│  ├─ distributions_nci
│  ├─ new_debt_issuances
│  └─ equity_issuances
│
├─ cash_flow_investing
│  ├─ development_capex
│  ├─ property_acquisitions
│  ├─ property_dispositions
│  ├─ jv_capital_contributions
│  └─ jv_return_of_capital
│
└─ acfo_components
   ├─ cash_flow_from_operations
   ├─ capex_sustaining_acfo
   ├─ leasing_costs_external
   └─ tenant_improvements_acfo
        ↓
Phase 3 Calculations
├─ coverage_ratios.py
│  └─ calculate_coverage_ratios()
│     └─ period_interest_expense (KEY INPUT)
│
├─ acfo.py
│  └─ calculate_acfo_from_components()
│     └─ acfo_calculated
│
├─ afcf.py
│  └─ calculate_afcf()
│     └─ afcf (AFCF = ACFO + Net CFI)
│
└─ burn_rate.py
   ├─ calculate_burn_rate()
   │  ├─ Input: financial_data, afcf_metrics
   │  └─ Output: burn_rate_analysis (applicable, monthly_burn_rate, etc.)
   │
   ├─ calculate_cash_runway()
   │  ├─ Input: burn_rate_metrics
   │  └─ Output: cash_runway (runway_months, extended_runway_months, etc.)
   │
   ├─ assess_liquidity_risk()
   │  ├─ Input: runway_metrics
   │  └─ Output: liquidity_risk (risk_level, risk_score, recommendations)
   │
   └─ calculate_sustainable_burn_rate()
      ├─ Input: burn_rate_metrics
      └─ Output: sustainable_burn (excess_burn_per_month, status)
        ↓
Phase 5 Report Generation
├─ generate_final_report.py
│  └─ Template placeholder mapping:
│     ├─ BURN_RATE_APPLICABLE
│     ├─ MONTHLY_BURN_RATE
│     ├─ CASH_RUNWAY_MONTHS
│     ├─ LIQUIDITY_RISK_LEVEL
│     └─ BURN_SUSTAINABILITY_ASSESSMENT
│
└─ credit_opinion_template.md
   └─ Section 4.3: Burn Rate and Cash Runway Analysis
      ├─ Burn Rate Analysis table
      ├─ Cash Runway metrics
      ├─ Liquidity Risk Assessment
      └─ Sustainable Burn Rate Analysis
```

---

## 6. Current Metrics Output (Phase 3 JSON)

### 6.1 Burn Rate Analysis Section

**Location:** Output in `phase3_calculated_metrics.json` (if AFCF < obligations)

```json
{
  "burn_rate_analysis": {
    "applicable": true,
    "monthly_burn_rate": -1916667.0,
    "period_burn_rate": -23000000.0,
    "period_months": 12,
    "afcf": 28000000,
    "mandatory_obligations": 51000000,
    "self_funding_ratio": 0.55,
    "reason": null,
    "data_quality": "complete"
  }
}
```

### 6.2 Liquidity Position Section

```json
{
  "liquidity_position": {
    "cash_and_equivalents": 65000000,
    "marketable_securities": 20000000,
    "restricted_cash": 5000000,
    "available_cash": 80000000,
    "undrawn_credit_facilities": 150000000,
    "total_available_liquidity": 230000000
  }
}
```

### 6.3 Cash Runway Section

```json
{
  "cash_runway": {
    "runway_months": 41.7,
    "runway_years": 3.5,
    "extended_runway_months": 119.8,
    "extended_runway_years": 10.0,
    "depletion_date": "2029-04-15",
    "extended_depletion_date": "2035-10-21"
  }
}
```

### 6.4 Liquidity Risk Section

```json
{
  "liquidity_risk": {
    "risk_level": "LOW",
    "risk_score": 1,
    "warning_flags": [],
    "assessment": "✓ Adequate liquidity runway (> 24 months)",
    "recommendations": [
      "Monitor burn rate quarterly",
      "Maintain covenant compliance",
      "Continue current growth strategy",
      "Consider opportunistic refinancing"
    ],
    "data_quality": "strong"
  }
}
```

### 6.5 Sustainable Burn Section

```json
{
  "sustainable_burn": {
    "target_runway_months": 24,
    "sustainable_monthly_burn": 3333333,
    "actual_monthly_burn": -1916667,
    "excess_burn_per_month": -1416666,
    "excess_burn_annualized": -17000000,
    "status": "Below sustainable - $1,417,000/month cushion",
    "available_cash": 80000000,
    "data_quality": "strong"
  }
}
```

---

## 7. Phase 5 Template Integration

### 7.1 Template Section: 4.3 Burn Rate and Cash Runway Analysis

**Location:** `templates/credit_opinion_template.md` (lines ~1450-1550)

**Placeholders Populated:**

| Placeholder | Source | Format | Example |
|-----------|--------|--------|---------|
| `BURN_RATE_APPLICABLE` | burn_rate_analysis.applicable | "Yes" or "No" | "Yes" |
| `MONTHLY_BURN_RATE` | burn_rate_analysis.monthly_burn_rate | "$X,XXX" | "$-1,916,667" |
| `BURN_MANDATORY_OBLIGATIONS` | burn_rate_analysis.mandatory_obligations | "$X,XXX" | "$51,000,000" |
| `BURN_PERIOD_DEFICIT` | burn_rate_analysis.period_burn_rate | "$X,XXX" | "$-23,000,000" |
| `CASH_RUNWAY_MONTHS` | cash_runway.runway_months | "X.X" | "41.7" |
| `EXTENDED_RUNWAY_MONTHS` | cash_runway.extended_runway_months | "X.X" | "119.8" |
| `CASH_DEPLETION_DATE` | cash_runway.depletion_date | "YYYY-MM-DD" | "2029-04-15" |
| `LIQUIDITY_RISK_LEVEL` | liquidity_risk.risk_level | "CRITICAL/HIGH/MODERATE/LOW" | "LOW" |
| `LIQUIDITY_RISK_SCORE` | liquidity_risk.risk_score | "0-4" | "1" |
| `BURN_SUSTAINABILITY_ASSESSMENT` | sustainable_burn.status | String | "Below sustainable - $1.4M/month cushion" |

**Template Section Content:**
```markdown
#### 4.3 Burn Rate and Cash Runway Analysis

**Applicability:** {{BURN_RATE_APPLICABLE}}

**Burn Rate Analysis:**
| Metric | Amount | Period | Notes |
|--------|--------|--------|-------|
| **AFCF (Period)** | {{AFCF_CALCULATED}} | {{REPORTING_PERIOD}} | Free cash flow |
| **Mandatory Obligations** | {{BURN_MANDATORY_OBLIGATIONS}} | {{REPORTING_PERIOD}} | Debt service + distributions |
| **Period Deficit/(Surplus)** | {{BURN_PERIOD_DEFICIT}} | {{REPORTING_PERIOD}} | AFCF - Obligations |
| **Monthly Burn Rate** | {{MONTHLY_BURN_RATE}} | Per month | {{BURN_PERIOD_MONTHS}}-month period |

**Cash Runway:**
- **Cash Only:** {{CASH_RUNWAY_MONTHS}} months → Depletion: {{CASH_DEPLETION_DATE}}
- **Extended:** {{EXTENDED_RUNWAY_MONTHS}} months (with credit facilities)

**Liquidity Risk Assessment:**
- **Risk Level:** {{LIQUIDITY_RISK_LEVEL}} (Score: {{LIQUIDITY_RISK_SCORE}}/4)

**Sustainable Burn Rate Analysis:**
- {{BURN_SUSTAINABILITY_ASSESSMENT}}
```

---

## 8. Testing and Validation

### 8.1 Unit Tests

**Location:** `/workspaces/issuer-credit-analysis/tests/test_burn_rate_calculations.py`

**Test Coverage:**
- ✅ `test_burn_rate_with_afcf_below_financing_needs()` - Burn rate when applicable
- ✅ `test_burn_rate_with_afcf_exceeding_financing_needs()` - Burn rate not applicable
- ✅ `test_burn_rate_missing_financing_data()` - Error handling
- ✅ `test_burn_rate_with_missing_afcf_metrics()` - Missing AFCF
- ✅ `test_burn_rate_with_none_afcf()` - AFCF = None case
- ✅ 25+ total tests covering all functions and edge cases

**Example Test Case:**
```python
def test_burn_rate_with_afcf_below_financing_needs():
    financial_data = {
        'cash_flow_financing': {
            'debt_principal_repayments': -18000,
            'distributions_common': -20000,
            'new_debt_issuances': 5000,
        },
        'coverage_ratios': {
            'period_interest_expense': 22000,
            'annualization_factor': 1
        }
    }
    afcf_metrics = {'afcf': 25000, 'data_quality': 'strong'}
    
    result = calculate_burn_rate(financial_data, afcf_metrics)
    
    assert result['applicable'] is True
    assert result['self_funding_ratio'] == pytest.approx(0.45, abs=0.01)
    assert result['monthly_burn_rate'] == 2500
```

### 8.2 Integration Tests

**Location:** `/workspaces/issuer-credit-analysis/tests/test_burn_rate_integration.py`

**Fixture:** `reit_burn_rate_high_risk.json` (lines 1-96)

**Scenario:** REIT with aggressive development program exceeding operating cash flow
```json
{
  "scenario": "HIGH risk (10.8 month runway)",
  "acfo_calculated": 27200,
  "net_cfi": -60000,
  "afcf_calculated": -32800,
  "monthly_burn_rate": 3858.33,
  "runway_months": 10.8,
  "risk_level": "HIGH"
}
```

---

## 9. Recommended Integration Points for Distribution Cut Prediction

### 9.1 Function Architecture

**Proposed Location:** `/workspaces/issuer-credit-analysis/scripts/calculate_credit_metrics/distribution_cut_analysis.py` (NEW)

**New Functions:**

```python
def predict_distribution_cut_scenarios(
    financial_data,
    burn_rate_metrics,
    runway_metrics,
    current_distribution_per_unit,
    target_runway_months=24,
    cut_scenarios=[0.25, 0.50, 0.75]
):
    """
    Predict distribution cuts needed to achieve target runway
    
    Returns:
    - cut_probability: float (0-1)
    - cut_timing: str (immediate, 6mo, 12mo, etc.)
    - cut_magnitude: float (0.25 = 25% cut)
    - new_distribution_per_unit: float (post-cut)
    - post_cut_runway: float (months)
    - credit_implications: str
    - sustainability_assessment: str
    """
```

### 9.2 Reusable Metrics

**Can leverage existing calculations:**
1. `burn_rate_analysis.monthly_burn_rate` - Current burn rate
2. `burn_rate_analysis.self_funding_ratio` - Coverage of obligations
3. `cash_runway.runway_months` - Current runway
4. `sustainable_burn.excess_burn_per_month` - Overspend
5. `liquidity_risk.risk_level` - Stress indicators

### 9.3 Schema Extensions

**Phase 2 Enhancement:** Already has all needed components
- ✅ `cash_flow_financing.distributions_common`
- ✅ `ffo_affo.distributions_per_unit`
- ✅ `balance_sheet.common_units_outstanding`

**Phase 3 Output Enhancement:**

```json
{
  "distribution_cut_analysis": {
    "applicable": true,
    "current_distribution_per_unit": 0.18,
    "current_payout_ratio_afcf": 86.4,
    "scenarios": [
      {
        "cut_percentage": 0,
        "new_distribution_per_unit": 0.18,
        "expected_runway": 10.8,
        "status": "HIGH RISK"
      },
      {
        "cut_percentage": 25,
        "new_distribution_per_unit": 0.135,
        "expected_runway": 14.4,
        "status": "MODERATE RISK"
      },
      {
        "cut_percentage": 50,
        "new_distribution_per_unit": 0.09,
        "expected_runway": 21.6,
        "status": "LOW RISK"
      }
    ],
    "cut_probability": 0.75,
    "cut_timing": "within_6_months",
    "cut_magnitude_if_required": 0.35,
    "credit_implications": "...",
    "data_quality": "strong"
  }
}
```

---

## 10. Code Locations Summary

### Core Implementation

| File | Lines | Function | Purpose |
|------|-------|----------|---------|
| `burn_rate.py` | 9-129 | `calculate_burn_rate()` | Main burn rate calculation |
| `burn_rate.py` | 132-257 | `calculate_cash_runway()` | Runway calculation |
| `burn_rate.py` | 260-373 | `assess_liquidity_risk()` | Risk assessment |
| `burn_rate.py` | 376-462 | `calculate_sustainable_burn_rate()` | Sustainability analysis |
| `afcf.py` | 8-165 | `calculate_afcf()` | AFCF calculation (input to burn rate) |
| `coverage.py` | 10-96 | `calculate_coverage_ratios()` | Period interest extraction |
| `calculate_credit_metrics.py` | ~100+ | Various | Main orchestrator, burn rate imports |

### Phase 2 Schema

| Section | Lines | Contents |
|---------|-------|----------|
| `phase2_extraction_schema.json` | 739-776 | Liquidity section |
| `phase2_extraction_schema.json` | 689-737 | Cash flow financing |
| `phase2_extraction_schema.json` | 647-687 | Cash flow investing |

### Phase 5 Template

| Section | Content | Placeholders |
|---------|---------|--------------|
| `credit_opinion_template.md` | 4.3 Burn Rate Analysis | 15+ burn rate placeholders |
| `generate_final_report.py` | Placeholder mapping | `assess_burn_rate_sustainability()` function |

### Testing

| File | Purpose |
|------|---------|
| `test_burn_rate_calculations.py` | 25+ unit tests |
| `test_burn_rate_integration.py` | Integration tests |
| `reit_burn_rate_high_risk.json` | Test fixture with scenario |

---

## 11. Critical Insights for Distribution Cut Prediction

### 11.1 Key Observations

1. **Burn Rate ≠ Negative AFCF**
   - REIT can have POSITIVE AFCF but still burn cash
   - Burn occurs when AFCF < Mandatory Obligations (debt service + distributions)
   - Example: $28M AFCF covering $51M obligations = 0.55x self-funding = BURN

2. **Self-Funding Ratio is the Key Metric**
   - < 0.5x = HIGH burn, HIGH cut probability
   - 0.5-0.8x = MODERATE burn, MODERATE cut probability
   - 0.8-1.0x = LOW burn, but still needs capital markets
   - ≥ 1.0x = No burn, distributions sustainable

3. **Period Matters**
   - Q2 is 6 months → factor of 2 annualization
   - Annualization factor embedded in coverage_ratios
   - Monthly burn = Period Deficit / Period Months

4. **Excess Burn Calculation**
   - Shows how much overspending relative to target runway
   - Negative = REIT has cushion
   - Positive = REIT needs cost reduction

### 11.2 Distribution Cut Prediction Logic

**Proposed Algorithm:**

```python
if self_funding_ratio < 1.0:
    # REIT cannot fully self-fund
    
    if runway_months < 12:
        # Near-term stress - cut likely in 6 months
        cut_probability = max(0.7, 1.0 - self_funding_ratio)
        
        # Calculate required cut
        required_funding_gap = mandatory_obligations - afcf
        max_sustainable_distributions = afcf * 0.7  # Keep 30% for debt service
        current_distributions = dist_common + dist_preferred + dist_nci
        
        required_cut = max(0, (current_distributions - max_sustainable_distributions) / current_distributions)
        cut_magnitude = max(required_cut, 0.25)  # Minimum 25% if cutting
        
    elif runway_months < 24:
        # Medium-term pressure
        cut_probability = max(0.4, 1.0 - self_funding_ratio)
        cut_magnitude = 0.15  # Modest trim
        
    else:
        # Adequate runway
        cut_probability = 0.15  # Low but not impossible
        cut_magnitude = 0.05   # Nominal reduction
```

---

## 12. Summary: Key Metrics Already Calculated

The implementation provides all metrics needed for distribution cut prediction:

✅ **Available Metrics:**
1. `burn_rate_analysis.self_funding_ratio` - Primary predictor
2. `burn_rate_analysis.monthly_burn_rate` - Burn intensity
3. `cash_runway.runway_months` - Stress timing
4. `liquidity_risk.risk_level` - Risk classification
5. `liquidity_risk.recommendations` - Includes "Suspend or reduce distributions"
6. `sustainable_burn.excess_burn_per_month` - Overspend magnitude
7. `ffo_affo.distributions_per_unit` - Current payout level
8. `balance_sheet.common_units_outstanding` - Unit count for per-unit calc

✅ **Integration Ready:**
- Full data validation
- Error handling
- Period normalization
- Data quality assessment

---

## 13. Conclusion

The burn rate and cash flow analysis is comprehensively implemented with:
- 4 core calculation functions
- Full Phase 2→3 data pipeline integration
- 5 template placeholders for report generation
- 25+ unit and integration tests
- Sophisticated risk assessment (4-tier classification)
- Sustainable burn analysis

**For distribution cut prediction:**
- All prerequisite data already calculated
- Self-funding ratio provides primary signal
- Runway and liquidity risk provide timing indicators
- Can be added as new module using existing calculations

