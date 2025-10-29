# Burn Rate and Cash Flow Analysis - Schema Reference Guide

**Quick Reference for Integration and Testing**

---

## Phase 2 Extraction Schema (Input Data)

### Required Fields for Burn Rate Calculation

#### Liquidity Section
```json
{
  "liquidity": {
    "cash_and_equivalents": number,           // ✅ REQUIRED
    "marketable_securities": number,          // ✅ REQUIRED (0 if not available)
    "restricted_cash": number,                // ✅ REQUIRED (0 if none)
    "undrawn_credit_facilities": number,      // ✅ REQUIRED (0 if none)
    "credit_facility_limit": number,          // Optional (for context)
    "available_cash": number,                 // Calculated field
    "total_available_liquidity": number,      // Calculated field
    "data_source": string                     // Documentation
  }
}
```

**Usage in Pipeline:**
- `cash_and_equivalents` + `marketable_securities` - `restricted_cash` = Available Cash
- Available Cash + `undrawn_credit_facilities` = Total Liquidity
- Used by `calculate_cash_runway()` for runway calculation

---

#### Cash Flow Financing Section
```json
{
  "cash_flow_financing": {
    "debt_principal_repayments": number,      // ✅ REQUIRED (negative = outflow)
    "distributions_common": number,           // ✅ REQUIRED (negative = outflow)
    "distributions_preferred": number,        // Optional (0 if none)
    "distributions_nci": number,              // Optional (0 if none)
    "new_debt_issuances": number,             // Optional (NOT used in burn rate)
    "equity_issuances": number,               // Optional (NOT used in burn rate)
    "total_cff": number                       // Optional (for reconciliation)
  }
}
```

**Usage in Pipeline:**
- `debt_principal_repayments` (abs value) + period interest = Total Debt Service
- `distributions_common` + `distributions_preferred` + `distributions_nci` (abs values) = Total Distributions
- Debt Service + Distributions = Mandatory Obligations
- Used by `calculate_burn_rate()` to determine if burn applicable

**Important Notes:**
- All outflows are NEGATIVE numbers in JSON
- Burn rate calculation uses absolute values
- `new_debt_issuances` and `equity_issuances` are EXCLUDED from burn rate (stress test assumes no capital markets access)

---

#### Cash Flow Investing Section
```json
{
  "cash_flow_investing": {
    "development_capex": number,              // Negative (growth capex)
    "property_acquisitions": number,          // Negative (capex)
    "property_dispositions": number,          // Positive (proceeds)
    "jv_capital_contributions": number,       // Negative (investment)
    "jv_return_of_capital": number,           // Positive (proceeds)
    "business_combinations": number,          // Negative (acquisitions)
    "other_investing_outflows": number,       // Negative
    "other_investing_inflows": number,        // Positive
    "total_cfi": number                       // Total net CFI
  }
}
```

**Usage in Pipeline:**
- Sum all components = Net Cash Flow from Investing (CFI)
- ACFO + CFI = AFCF (used as input to burn rate)

---

#### ACFO Components Section
```json
{
  "acfo_components": {
    "cash_flow_from_operations": number,      // ✅ REQUIRED (CFO from cash flow statement)
    "change_in_working_capital": number,      // Working capital adjustments
    "jv_distributions": number,               // JV distributions received
    "capex_sustaining_acfo": number,          // Sustaining capex (negative)
    "leasing_costs_external": number,         // External leasing (negative)
    "tenant_improvements_acfo": number,       // Sustaining TI (negative)
    "calculation_method_acfo": string,        // "actual", "reserve", or "hybrid"
    "jv_treatment_method": string             // "distributions" or "acfo"
  }
}
```

**Usage in Pipeline:**
- CFO + Adjustments (1-17) = ACFO
- ACFO + Net CFI = AFCF
- AFCF - Mandatory Obligations = Burn (when negative)

---

#### Coverage Ratios Section
```json
{
  "coverage_ratios": {
    "noi_interest_coverage": number,          // NOI / Interest
    "period_interest_expense": number,        // ✅ REQUIRED (PERIOD interest, not annualized)
    "annualized_interest_expense": number,    // For reference
    "annualization_factor": number,           // ✅ REQUIRED (Q2=2, Q3=1.33, Q4=1)
    "detected_period": string                 // Period label
  }
}
```

**Usage in Pipeline:**
- `period_interest_expense` = Interest for reporting period (Q2 = 6 months of interest)
- `annualization_factor` used to convert period months to 12 months
- `Period Months = 12 / annualization_factor` (Q2: 12/2 = 6 months)
- Burn Rate = Period Deficit / Period Months

**Critical:** Must use PERIOD interest expense, not annualized

---

### Balance Sheet Section (For Per-Unit Calculations)
```json
{
  "balance_sheet": {
    "common_units_outstanding": number,       // Basic shares/units
    "diluted_units_outstanding": number       // Diluted shares/units (optional)
  }
}
```

**Usage:** For per-unit distribution calculations in distribution cut scenarios

---

### FFO/AFFO Section (For Distribution Info)
```json
{
  "ffo_affo": {
    "distributions_per_unit": number,         // ✅ REQUIRED for distribution analysis
    "ffo": number,
    "affo": number,
    "ffo_per_unit": number,
    "affo_per_unit": number
  }
}
```

---

## Phase 3 Output Schema (Calculated Metrics)

### Burn Rate Analysis Object
```json
{
  "burn_rate_analysis": {
    "applicable": boolean,                    // True when AFCF < Mandatory Obligations
    "monthly_burn_rate": number or null,      // Negative when burning cash
    "period_burn_rate": number or null,       // Total deficit for reporting period
    "period_months": integer,                 // Number of months in reporting period
    "afcf": number,                           // Input: Adjusted Free Cash Flow
    "mandatory_obligations": number or null,  // Debt Service + Distributions
    "self_funding_ratio": number or null,     // AFCF / Mandatory Obligations
    "reason": string or null,                 // Explanation if not applicable
    "data_quality": string                    // "strong", "moderate", "limited", "none"
  }
}
```

**Key Metrics:**
- `applicable`: YES if AFCF < Obligations (indicates burn rate applies)
- `monthly_burn_rate`: Monthly cash depletion (typically negative)
- `self_funding_ratio`: % of obligations covered by AFCF
  - < 0.5 = HIGH burn
  - 0.5-0.8 = MODERATE burn
  - 0.8-1.0 = LOW burn
  - ≥ 1.0 = No burn (self-sufficient)

---

### Cash Runway Object
```json
{
  "cash_runway": {
    "runway_months": number,                  // Months until cash-only depletion
    "runway_years": number,                   // Years (for readability)
    "extended_runway_months": number,         // With undrawn credit facilities
    "extended_runway_years": number,
    "depletion_date": string,                 // Estimated YYYY-MM-DD
    "extended_depletion_date": string,        // With facilities
    "available_cash": number,                 // Cash + Securities - Restricted
    "total_available_liquidity": number,      // Available Cash + Undrawn Facilities
    "data_quality": string,                   // "strong", "moderate", "limited", "none"
    "error": string or null                   // Error message if calculation failed
  }
}
```

**Runway Risk Thresholds:**
- < 6 months = CRITICAL (immediate action needed)
- 6-12 months = HIGH (capital raise within 6 months)
- 12-24 months = MODERATE (plan financing within 12 months)
- > 24 months = LOW (adequate liquidity)

---

### Liquidity Risk Object
```json
{
  "liquidity_risk": {
    "risk_level": string,                     // "CRITICAL", "HIGH", "MODERATE", "LOW", "N/A"
    "risk_score": integer,                    // 0=N/A, 1=LOW, 2=MODERATE, 3=HIGH, 4=CRITICAL
    "warning_flags": array of strings,        // Specific concerns (if any)
    "assessment": string,                     // Human-readable assessment
    "recommendations": array of strings,      // Action items (e.g., "Consider distribution reduction")
    "data_quality": string                    // Quality of underlying data
  }
}
```

**Example Recommendations by Risk Level:**
- **CRITICAL**: "Suspend or reduce distributions immediately", "Accelerate asset sales"
- **HIGH**: "Initiate capital raise", "Consider distribution reduction", "Defer growth capex"
- **MODERATE**: "Begin financing planning", "Evaluate distribution sustainability"
- **LOW**: "Monitor burn rate quarterly", "Continue current strategy"

---

### Sustainable Burn Object
```json
{
  "sustainable_burn": {
    "target_runway_months": integer,          // Target runway (default 24 months)
    "sustainable_monthly_burn": number,       // Max burn to maintain target runway
    "actual_monthly_burn": number,            // Current monthly burn rate
    "excess_burn_per_month": number,          // Overspend (+ = above, - = below)
    "excess_burn_annualized": number,         // Annual overspend
    "status": string,                         // "Above sustainable", "Below sustainable", "N/A"
    "available_cash": number,                 // Available liquidity
    "data_quality": string
  }
}
```

**Interpretation:**
- `excess_burn_per_month` > 0: REIT is overspending (unsustainable)
- `excess_burn_per_month` < 0: REIT has cushion (can extend runway)
- Example: "Below sustainable - $1.4M/month cushion" = well-positioned REIT

---

## Data Flow Reference

### Calculation Order (Phase 3)

1. **Coverage Ratios** (extract period_interest_expense and annualization_factor)
   ```
   Input: income_statement.interest_expense, reporting_period
   Output: coverage_ratios with period_interest_expense and annualization_factor
   ```

2. **ACFO** (calculate from acfo_components)
   ```
   Input: acfo_components (cash_flow_from_operations + 17 adjustments)
   Output: acfo_calculated
   ```

3. **AFCF** (calculate from ACFO + CFI)
   ```
   Input: acfo_calculated, cash_flow_investing
   Output: afcf (ACFO + Net CFI)
   ```

4. **Burn Rate** (determine if applicable)
   ```
   Input: afcf, cash_flow_financing (principal + distributions), 
          coverage_ratios (period_interest_expense, annualization_factor)
   Output: burn_rate_analysis with monthly_burn_rate, self_funding_ratio
   ```

5. **Cash Runway** (calculate months until depletion)
   ```
   Input: burn_rate_analysis, liquidity (cash, securities, restricted, undrawn facilities)
   Output: cash_runway with runway_months, depletion_date
   ```

6. **Liquidity Risk** (assess 4-tier risk level)
   ```
   Input: cash_runway (runway_months)
   Output: liquidity_risk with risk_level, risk_score, recommendations
   ```

7. **Sustainable Burn** (calculate overspend magnitude)
   ```
   Input: burn_rate_analysis, liquidity (available_cash)
   Output: sustainable_burn with excess_burn_per_month, status
   ```

---

## Distribution Cut Prediction Integration Points

### Input Metrics (Already Calculated)
```json
{
  "burn_rate_analysis": {
    "self_funding_ratio": 0.55,              // PRIMARY INDICATOR
    "monthly_burn_rate": -1916667,           // Burn intensity
    "mandatory_obligations": 51000000        // Total to cover
  },
  "cash_runway": {
    "runway_months": 41.7                    // Timing indicator
  },
  "liquidity_risk": {
    "risk_level": "LOW",                     // Risk classification
    "risk_score": 1
  },
  "ffo_affo": {
    "distributions_per_unit": 0.18           // Current payout
  },
  "balance_sheet": {
    "common_units_outstanding": 100000       // For per-unit calc
  }
}
```

### Calculation Algorithm
```python
# Distribution Cut Prediction

if burn_rate_analysis['self_funding_ratio'] >= 1.0:
    # No burn - distributions sustainable
    cut_probability = 0.05
    cut_magnitude = 0.0
    
elif runway_months < 6:
    # CRITICAL - immediate action
    cut_probability = 0.95
    cut_magnitude = 0.50    # 50% cut likely
    
elif runway_months < 12:
    # HIGH - near-term pressure
    cut_probability = 0.75
    required_gap = mandatory_obligations - afcf
    cut_magnitude = 0.25    # 25-50% cut
    
elif runway_months < 24:
    # MODERATE - medium-term pressure
    cut_probability = 0.40
    cut_magnitude = 0.15    # Modest trim
    
else:
    # LOW - adequate runway
    cut_probability = 0.15
    cut_magnitude = 0.05    # Minimal trim

# Calculate post-cut runway
current_dist_total = distributions_common + distributions_preferred + distributions_nci
new_dist_total = current_dist_total * (1 - cut_magnitude)
cash_saved = current_dist_total - new_dist_total

# New monthly burn after cut
new_monthly_burn = monthly_burn_rate + (cash_saved / period_months)
post_cut_runway = available_cash / abs(new_monthly_burn)
```

---

## Testing Reference

### Test Fixture: `reit_burn_rate_high_risk.json`

**Scenario:** Aggressive development REIT (HIGH risk)

**Key Metrics:**
- AFCF: -$32.8M (NEGATIVE)
- Obligations: $46M
- Monthly Burn: $3.86M
- Runway: 10.8 months (HIGH RISK)

**Expected Outputs:**
```json
{
  "burn_rate_analysis": {
    "applicable": true,
    "monthly_burn_rate": -3858333,
    "self_funding_ratio": 0.71,
    "data_quality": "complete"
  },
  "cash_runway": {
    "runway_months": 10.8,
    "risk_level": "HIGH"
  }
}
```

---

## Validation Checklist

### Phase 2 Extraction Validation

- [ ] `liquidity.cash_and_equivalents` populated
- [ ] `liquidity.undrawn_credit_facilities` populated (or 0)
- [ ] `cash_flow_financing.distributions_common` populated (negative number)
- [ ] `cash_flow_financing.debt_principal_repayments` populated (negative number)
- [ ] `coverage_ratios.period_interest_expense` populated (PERIOD, not annualized)
- [ ] `coverage_ratios.annualization_factor` correct for reporting period
- [ ] `cash_flow_investing` section complete with net CFI
- [ ] `acfo_components.cash_flow_from_operations` populated

### Phase 3 Calculation Validation

- [ ] ACFO calculated before AFCF
- [ ] AFCF = ACFO + Net CFI (reconcile to cash flow statement if possible)
- [ ] Burn Rate applicable only when AFCF < Mandatory Obligations
- [ ] Monthly Burn = Period Deficit / Period Months
- [ ] Self-Funding Ratio = AFCF / Mandatory Obligations
- [ ] Runway = Available Cash / |Monthly Burn|
- [ ] Risk Level determined by runway thresholds
- [ ] Sustainable Burn calculated with target runway (default 24 months)

---

## Common Integration Scenarios

### Scenario 1: REITs Not Burning Cash (Self-Sufficient)

**Characteristics:**
- Self-Funding Ratio ≥ 1.0x
- Burn Rate Not Applicable
- No distribution cut probability

**Output:**
```json
{
  "burn_rate_analysis": {
    "applicable": false,
    "self_funding_ratio": 1.25,
    "reason": "AFCF covers mandatory obligations - surplus..."
  },
  "distribution_cut_analysis": {
    "cut_probability": 0.05,
    "cut_timing": "not_required"
  }
}
```

---

### Scenario 2: Moderate Burn Rate (6-12 Month Runway)

**Characteristics:**
- Self-Funding Ratio 0.5-0.8x
- Monthly Burn Rate Applicable
- HIGH risk, capital raise needed

**Output:**
```json
{
  "burn_rate_analysis": {
    "applicable": true,
    "self_funding_ratio": 0.65,
    "monthly_burn_rate": -1200000
  },
  "cash_runway": {
    "runway_months": 9.5,
    "risk_level": "HIGH"
  },
  "distribution_cut_analysis": {
    "cut_probability": 0.75,
    "cut_timing": "within_6_months",
    "cut_magnitude_if_required": 0.30
  }
}
```

---

### Scenario 3: Critical Burn Rate (< 6 Month Runway)

**Characteristics:**
- Self-Funding Ratio < 0.5x
- Severe Monthly Burn
- CRITICAL risk, immediate action required

**Output:**
```json
{
  "burn_rate_analysis": {
    "applicable": true,
    "self_funding_ratio": 0.30,
    "monthly_burn_rate": -3000000
  },
  "cash_runway": {
    "runway_months": 3.2,
    "risk_level": "CRITICAL"
  },
  "distribution_cut_analysis": {
    "cut_probability": 0.95,
    "cut_timing": "immediate",
    "cut_magnitude_if_required": 0.50,
    "credit_implications": "Distribution cut likely imminent without refinancing"
  }
}
```

---

## File Location Reference

```
/workspaces/issuer-credit-analysis/
├── scripts/
│   ├── calculate_credit_metrics/
│   │   ├── burn_rate.py                    # Burn rate functions
│   │   ├── afcf.py                         # AFCF calculation
│   │   ├── acfo.py                         # ACFO calculation
│   │   ├── coverage.py                     # Interest coverage
│   │   └── reit_metrics.py                 # REIT metrics orchestrator
│   └── generate_final_report.py            # Template placeholder mapping
│
├── templates/
│   └── credit_opinion_template.md          # Section 4.3: Burn Rate Analysis
│
├── .claude/knowledge/
│   └── phase2_extraction_schema.json       # Schema definition
│
└── tests/
    ├── test_burn_rate_calculations.py     # 25+ unit tests
    ├── test_burn_rate_integration.py      # Integration tests
    └── fixtures/
        └── reit_burn_rate_high_risk.json  # Test scenario
```

