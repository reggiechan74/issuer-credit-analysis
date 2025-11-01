# Phase 2 Extraction Schema Documentation

## Overview

This document defines the **standardized JSON schema** that Phase 2 extraction MUST produce for Phase 3 calculations to work correctly.

## Schema Files

1. **`phase2_extraction_schema_v2.json`** - JSON Schema specification (AUTHORITATIVE, machine-readable)
2. **`COMPREHENSIVE_EXTRACTION_GUIDE.md`** - Detailed extraction guide with examples
3. **This README** - Complete schema documentation with examples

## Key Schema Principles

### 1. Flat Structure for balance_sheet

❌ **WRONG (nested objects):**
```json
{
  "balance_sheet": {
    "assets": {
      "total_assets": 2611435,
      "cash": 16639
    },
    "liabilities": {
      "mortgages_noncurrent": 217903
    }
  }
}
```

✅ **CORRECT (flat structure):**
```json
{
  "balance_sheet": {
    "total_assets": 2611435,
    "cash": 16639,
    "mortgages_noncurrent": 217903
  }
}
```

### 2. Top-Level Values Required

Both `income_statement` and `ffo_affo` MUST include top-level values for the **most recent period** (e.g., Q2 2025).

❌ **WRONG (only nested periods):**
```json
{
  "income_statement": {
    "q2_2025": {
      "noi": 30729,
      "interest_expense": 16937
    }
  }
}
```

✅ **CORRECT (top-level + optional nested):**
```json
{
  "income_statement": {
    "noi": 30729,
    "interest_expense": 16937,
    "revenue": 59082,
    "q2_2025": {
      "noi": 30729,
      "interest_expense": 16937
    }
  }
}
```

### 3. No Null Values for Numeric Fields

Use `0` instead of `null` for unknown numeric values.

❌ **WRONG:**
```json
{
  "portfolio": {
    "total_gla_sf": null
  }
}
```

✅ **CORRECT:**
```json
{
  "portfolio": {
    "total_gla_sf": 0
  }
}
```

### 4. Decimal Format for Rates

Occupancy and growth rates MUST be decimals (0-1 range), NOT percentages.

❌ **WRONG:**
```json
{
  "portfolio": {
    "occupancy_rate": 87.8
  }
}
```

✅ **CORRECT:**
```json
{
  "portfolio": {
    "occupancy_rate": 0.878
  }
}
```

## Required Fields

### Top Level (Always Required)

```json
{
  "issuer_name": "string",
  "reporting_date": "YYYY-MM-DD",
  "currency": "CAD | USD"
}
```

### balance_sheet (Required Fields)

```json
{
  "balance_sheet": {
    "total_assets": number,
    "mortgages_noncurrent": number,
    "mortgages_current": number,
    "credit_facilities": number,
    "cash": number
  }
}
```

**Note:** `senior_unsecured_debentures` is optional (defaults to 0).

### income_statement (Required Fields)

```json
{
  "income_statement": {
    "noi": number,
    "interest_expense": number,
    "revenue": number
  }
}
```

**Important:** `interest_expense` must be a **positive number** (absolute value).

### ffo_affo (Required Fields)

```json
{
  "ffo_affo": {
    "ffo": number,
    "affo": number,
    "ffo_per_unit": number,
    "affo_per_unit": number,
    "distributions_per_unit": number
  }
}
```

## Field Naming Conventions

### Standardized Field Names

Use these EXACT field names (case-sensitive):

| ✅ Correct | ❌ Incorrect |
|-----------|-------------|
| `mortgages_noncurrent` | `mortgages_loans_noncurrent` |
| `mortgages_current` | `mortgages_loans_current` |
| `occupancy_with_commitments` | `occupancy_including_commitments` |
| `same_property_noi_growth_6m` | `same_property_noi_growth` |
| `total_gla_sf` | `gla_sf` |

**Note:** Phase 3 now supports both naming conventions for backward compatibility, but new extractions should use the standardized names.

## Dilution Tracking (Optional)

### Overview

The `dilution_detail` section provides transparency on share dilution sources and materiality for credit analysis. Extract this when the issuer discloses dilution calculations in their MD&A.

### When to Extract

✅ **Extract dilution_detail when:**
- Issuer provides detailed dilution calculation (e.g., Artis REIT Q2 2025 MD&A page 21)
- Shows breakdown by instrument type (RSUs, options, convertibles, etc.)
- Useful for assessing dilution materiality and quality

❌ **Skip dilution_detail when:**
- Issuer only reports basic vs diluted totals (e.g., DIR)
- No detailed breakdown available
- Just include `common_units_outstanding` and `diluted_units_outstanding` in balance_sheet

### Structure

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

### Typical Dilution Levels by Instrument

| Instrument | Typical Range | Credit Concern |
|------------|---------------|----------------|
| Restricted Units (RSUs/PSUs) | 0.5-2% | Low - part of normal compensation |
| Deferred Units (DSUs) | <1% | Low - director compensation only |
| Stock Options | 1-3% | Low-Moderate - typical for REITs |
| Convertible Debentures | 5-15% | **Moderate-High** - can be material |
| Warrants | Varies | Case-by-case assessment |

### Credit Analysis Use Cases

**1. Assess Dilution Materiality:**
```
Artis REIT: 2.01% dilution (101,444 diluted vs 99,444 basic)
→ Low dilution risk, minimal equity overhang
→ Positive for credit quality
```

**2. Identify Material Convertibles:**
```
If convertible_debentures = 10,000 units (10% dilution):
→ Material equity overhang
→ Review conversion terms and potential forced conversion scenarios
→ Factor into debt capacity assessment
```

**3. Governance/Disclosure Quality:**
```
Provides detailed breakdown → Higher transparency
Only reports totals → Standard disclosure
→ Can be factored into governance score
```

### Example: Artis REIT (Q2 2025 MD&A Page 21)

```json
{
  "balance_sheet": {
    "common_units_outstanding": 99444,
    "diluted_units_outstanding": 101444
  },
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
    "reconciliation_note": "All dilutive instruments included, no anti-dilutive exclusions",
    "disclosure_source": "Q2 2025 MD&A page 21"
  }
}
```

### Reconciliation Notes - Common Scenarios

**Scenario 1: Calculated = Reported**
```
"reconciliation_note": "Calculated matches reported - no anti-dilutive exclusions"
```

**Scenario 2: Calculated > Reported (Anti-dilutive Exclusion)**
```
"reconciliation_note": "Issuer excluded 500 anti-dilutive options per IAS 33"
```

**Scenario 3: Calculated < Reported (Missing Detail)**
```
"reconciliation_note": "Full detail not disclosed - 200 units unattributed to specific instrument"
```

## ACFO Components (Optional)

### Overview

The `acfo_components` section enables extraction of **Adjusted Cash Flow from Operations (ACFO)** per the REALPAC ACFO White Paper (January 2023). ACFO measures sustainable cash flow from operations after adjusting for non-recurring items and sustainable capital expenditures.

### When to Extract

✅ **Extract acfo_components when:**
- Issuer doesn't report ACFO (need to calculate from cash flow statement)
- Want to validate issuer-reported ACFO
- Need transparency on ACFO calculation methodology
- Building comprehensive reconciliation tables

❌ **Skip acfo_components when:**
- Issuer reports ACFO and no validation needed
- Cash flow statement data not available

### Key Formula

```
ACFO = Cash Flow from Operations
     + Adjustments 1-17 per REALPAC ACFO White Paper (Jan 2023)
```

### Structure

The section includes **17 REALPAC adjustments**:

```json
{
  "acfo_components": {
    "cash_flow_from_operations": 45000,

    "change_in_working_capital": -2000,
    "interest_financing": 15000,
    "jv_distributions": 3000,
    "capex_sustaining_acfo": -8000,
    "leasing_costs_external": -2000,
    "tenant_improvements_acfo": -4000,
    "realized_investment_gains_losses": 500,
    "taxes_non_operating": -300,
    "transaction_costs_acquisitions": -1000,
    "transaction_costs_disposals": 200,
    "deferred_financing_fees": 400,
    "debt_termination_costs": -500,
    "off_market_debt_favorable": 100,
    "off_market_debt_unfavorable": -50,
    "interest_income_timing": 50,
    "interest_expense_timing": -75,
    "puttable_instruments_distributions": -800,
    "rou_sublease_principal_received": 150,
    "rou_lease_principal_paid": -200,
    "rou_depreciation_amortization": 300,
    "non_controlling_interests_acfo": -500,
    "nci_puttable_units": -200,

    "calculation_method_acfo": "actual",
    "jv_treatment_method": "distributions",
    "missing_adjustments_acfo": []
  }
}
```

### Critical ACFO Adjustments

| Adjustment | REALPAC # | Purpose | Typical Sign |
|------------|-----------|---------|--------------|
| `change_in_working_capital` | Adj 1 | Eliminate non-sustainable fluctuations | +/- |
| `interest_financing` | Adj 2 | Add back interest in financing section | + |
| `jv_distributions` | Adj 3 | JV cash distributions received | + |
| `capex_sustaining_acfo` | Adj 4 | Sustaining/maintenance CAPEX | - |
| `leasing_costs_external` | Adj 5 | External leasing costs only | - |
| `tenant_improvements_acfo` | Adj 6 | Sustaining tenant improvements | - |
| `deferred_financing_fees` | Adj 11 | Amortization of financing fees | + |
| `non_controlling_interests_acfo` | Adj 17 | NCI adjustments | - |

### ACFO vs AFFO Consistency

**CRITICAL:** These fields MUST match between ACFO and AFFO calculations:
- `capex_sustaining_acfo` = `capex_sustaining` (from AFFO)
- `tenant_improvements_acfo` = `tenant_improvements` (from AFFO)

Phase 3 validates this consistency automatically.

### Example: Complete ACFO Extraction

```json
{
  "acfo_components": {
    "cash_flow_from_operations": 48500,
    "change_in_working_capital": -1500,
    "interest_financing": 14000,
    "jv_distributions": 2500,
    "capex_sustaining_acfo": -7500,
    "capex_development_acfo": -15000,
    "leasing_costs_external": -1800,
    "tenant_improvements_acfo": -3500,
    "realized_investment_gains_losses": 0,
    "taxes_non_operating": 0,
    "transaction_costs_acquisitions": -800,
    "transaction_costs_disposals": 150,
    "deferred_financing_fees": 350,
    "debt_termination_costs": 0,
    "off_market_debt_favorable": 75,
    "off_market_debt_unfavorable": 0,
    "interest_income_timing": 0,
    "interest_expense_timing": 0,
    "puttable_instruments_distributions": -750,
    "rou_sublease_principal_received": 0,
    "rou_sublease_interest_received": 0,
    "rou_lease_principal_paid": 0,
    "rou_depreciation_amortization": 0,
    "non_controlling_interests_acfo": -450,
    "nci_puttable_units": -180,
    "calculation_method_acfo": "actual",
    "reserve_methodology_acfo": "",
    "jv_treatment_method": "distributions",
    "missing_adjustments_acfo": []
  }
}
```

**Result:** ACFO = $48,695K

### Data Sources

Extract ACFO components from:
- **IFRS Consolidated Statement of Cash Flows** - Operating Activities section
- **MD&A - ACFO Reconciliation Tables** (if provided)
- **Notes to Financial Statements** - JV distributions, financing fees, NCI details
- **Supplemental Disclosures** - CAPEX breakdown, leasing costs

## AFCF Support (Optional)

### Overview

**Adjusted Free Cash Flow (AFCF)** extends analysis beyond ACFO to measure cash available for financing obligations after ALL investing activities:

```
AFCF = ACFO + Net Cash Flow from Investing Activities
```

AFCF requires two sections: `cash_flow_investing` and `cash_flow_financing`.

### When to Extract

✅ **Extract CFI/CFF when:**
- Need to calculate AFCF coverage ratios
- Assessing self-funding capacity
- Analyzing financing dependency
- Building complete cash flow analysis

❌ **Skip CFI/CFF when:**
- Only analyzing operating metrics (FFO/AFFO/ACFO sufficient)
- Cash flow statement not available

### cash_flow_investing

Extract from **IFRS Cash Flow Statement - Investing Activities** section.

**Sign Convention:** Negative for outflows, positive for inflows.

```json
{
  "cash_flow_investing": {
    "development_capex": -20000,
    "property_acquisitions": -30000,
    "property_dispositions": 25000,
    "jv_capital_contributions": -5000,
    "jv_return_of_capital": 2000,
    "business_combinations": 0,
    "other_investing_outflows": -500,
    "other_investing_inflows": 100,
    "total_cfi": -28400
  }
}
```

**Key Fields:**

| Field | Purpose | Typical Sign |
|-------|---------|--------------|
| `development_capex` | Growth CAPEX (NOT sustaining) | Negative |
| `property_acquisitions` | Cash paid for acquisitions | Negative |
| `property_dispositions` | Proceeds from sales | Positive |
| `jv_capital_contributions` | Capital invested in JVs | Negative |
| `jv_return_of_capital` | Capital returned from JV exits | Positive |
| `total_cfi` | Net CFI per IFRS (reconciliation) | Usually negative |

**⚠️ Double-Counting Prevention:**

ACFO already deducts these items - DO NOT include in CFI:
- ✅ Sustaining CAPEX (already in ACFO Adj 4)
- ✅ Sustaining tenant improvements (already in ACFO Adj 6)
- ✅ External leasing costs (already in ACFO Adj 5)
- ✅ JV distributions received (already in ACFO Adj 3)

**AFCF should ONLY add:**
- Development CAPEX (growth projects)
- Property acquisitions and dispositions
- JV capital contributions/returns (not distributions)

### cash_flow_financing

Extract from **IFRS Cash Flow Statement - Financing Activities** section.

**Sign Convention:** Negative for outflows, positive for inflows.

```json
{
  "cash_flow_financing": {
    "debt_principal_repayments": -15000,
    "new_debt_issuances": 10000,
    "distributions_common": -18000,
    "distributions_preferred": -1000,
    "distributions_nci": -500,
    "equity_issuances": 5000,
    "unit_buybacks": 0,
    "deferred_financing_costs_paid": -300,
    "other_financing_outflows": 0,
    "other_financing_inflows": 0,
    "total_cff": -19800
  }
}
```

**Key Fields:**

| Field | Purpose | Typical Sign |
|-------|---------|--------------|
| `debt_principal_repayments` | Principal payments on all debt | Negative |
| `new_debt_issuances` | Proceeds from new debt | Positive |
| `distributions_common` | Common distributions/dividends | Negative |
| `equity_issuances` | Proceeds from equity/unit issuances | Positive |
| `total_cff` | Net CFF per IFRS (reconciliation) | Usually negative |

### AFCF Coverage Ratios

Phase 3 automatically calculates these ratios when CFI/CFF data is present:

**1. AFCF Debt Service Coverage**
```
AFCF / (Annualized Interest + Principal Repayments)
```
- More conservative than NOI/Interest coverage
- < 1.0x = Cannot self-fund debt service

**2. AFCF Distribution Coverage**
```
AFCF / Total Distributions
```
- Modified payout ratio based on free cash flow
- < 1.0x = Distributions exceed free cash flow

**3. AFCF Self-Funding Ratio**
```
AFCF / (Debt Service + Distributions - New Financing)
```
- Measures true self-sustainability
- < 1.0x = Reliant on capital markets

### Example: AFCF Analysis

```json
{
  "acfo_metrics": {
    "acfo": 50000
  },
  "cash_flow_investing": {
    "development_capex": -20000,
    "property_acquisitions": -30000,
    "property_dispositions": 25000,
    "jv_capital_contributions": -5000,
    "jv_return_of_capital": 2000,
    "total_cfi": -28000
  },
  "cash_flow_financing": {
    "debt_principal_repayments": -15000,
    "new_debt_issuances": 10000,
    "distributions_common": -18000,
    "distributions_preferred": -1000,
    "equity_issuances": 5000,
    "total_cff": -19000
  }
}
```

**Phase 3 Calculation:**
```
AFCF = ACFO + Net CFI = $50,000 + (-$28,000) = $22,000

Total Debt Service = Interest ($22,000) + Principal ($15,000) = $37,000
AFCF Debt Service Coverage = $22,000 / $37,000 = 0.59x ⚠️

Total Distributions = $19,000
AFCF Distribution Coverage = $22,000 / $19,000 = 1.16x ✓

Net Financing Needs = $37,000 + $19,000 - $15,000 = $41,000
AFCF Self-Funding Ratio = $22,000 / $41,000 = 0.54x ⚠️
```

**Credit Assessment:**
- ⚠️ REIT cannot self-fund debt service (0.59x coverage)
- ✓ Distributions covered by free cash flow (1.16x)
- ⚠️ Reliant on capital markets for financing (0.54x self-funding)
- → Growth-oriented REIT with market access dependency

### Data Sources

Extract CFI/CFF from:
- **IFRS Consolidated Statement of Cash Flows** - Investing and Financing sections
- **Notes to Financial Statements** - Acquisition/disposition details
- **MD&A - Capital Allocation Discussion** - Growth vs sustaining CAPEX breakdown

## Burn Rate and Liquidity (Optional)

### Overview

**Cash burn rate** measures the speed at which a REIT depletes cash reserves when AFCF cannot cover financing obligations. A REIT can have **positive AFCF** but still burn cash if free cash flow is insufficient.

### When to Extract

✅ **Extract liquidity when:**
- AFCF < Net Financing Needs (self-funding ratio < 1.0x)
- Need to assess cash runway and liquidity risk
- Analyzing financing dependency and stress scenarios
- Required for comprehensive credit analysis

❌ **Skip liquidity when:**
- AFCF fully covers financing needs (self-funding ratio > 1.0x)
- Basic operational analysis sufficient

### Key Formula

```
Burn Rate = Net Financing Needs - AFCF (when AFCF < Net Financing Needs)

Where:
  Net Financing Needs = Total Debt Service + Distributions - New Financing
  Total Debt Service = Annualized Interest + Principal Repayments
```

### Structure

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
    "data_source": "balance sheet + note 12 - credit facilities"
  }
}
```

**Key Fields:**

| Field | Purpose | Calculation |
|-------|---------|-------------|
| `cash_and_equivalents` | Cash per balance sheet | Direct from balance sheet |
| `marketable_securities` | Short-term investments | From balance sheet (0 if none) |
| `restricted_cash` | Unavailable cash | From balance sheet notes (0 if none) |
| `undrawn_credit_facilities` | Available credit capacity | Facility limit - drawn amount |
| `available_cash` | Unrestricted liquid assets | Cash + securities - restricted |
| `total_available_liquidity` | Total liquidity buffer | Available cash + undrawn facilities |

### Burn Rate Metrics

Phase 3 automatically calculates when liquidity data is present:

**1. Monthly Burn Rate**
```
Monthly Burn Rate = (Net Financing Needs - AFCF) / 12 months
```

**2. Cash Runway**
```
Available Cash = Cash + Securities - Restricted Cash
Cash Runway (months) = Available Cash / Monthly Burn Rate
Extended Runway = Total Available Liquidity / Monthly Burn Rate
```

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

### Example: Burn Rate Analysis

**Scenario:** REIT with positive AFCF but burning cash

```json
{
  "afcf_metrics": {
    "afcf": 28000
  },
  "cash_flow_financing": {
    "debt_principal_repayments": -25000,
    "new_debt_issuances": 10000,
    "distributions_common": -19000,
    "equity_issuances": 5000
  },
  "income_statement": {
    "interest_expense": 22000
  },
  "liquidity": {
    "cash_and_equivalents": 65000,
    "marketable_securities": 20000,
    "restricted_cash": 5000,
    "undrawn_credit_facilities": 150000,
    "credit_facility_limit": 200000,
    "available_cash": 80000,
    "total_available_liquidity": 230000,
    "data_source": "Q2 2025 balance sheet + note 15"
  }
}
```

**Phase 3 Calculation:**
```
Total Debt Service = Interest ($22,000) + Principal ($25,000) = $47,000
Total Distributions = $19,000
New Financing = Debt ($10,000) + Equity ($5,000) = $15,000

Net Financing Needs = $47,000 + $19,000 - $15,000 = $51,000
AFCF = $28,000

Burn Rate Applicable? Yes ($28,000 < $51,000)
Annualized Burn Rate = $51,000 - $28,000 = $23,000
Monthly Burn Rate = $23,000 / 12 = $1,917/month

Available Cash = $80,000
Cash Runway = $80,000 / $1,917 = 41.7 months ✓

Extended Runway = $230,000 / $1,917 = 119.8 months ✓

Risk Level = LOW (> 24 months)
```

**Credit Assessment:**
- ⚠️ REIT burns $1.9M/month despite positive AFCF
- ✓ Comfortable 41.7-month runway without new financing
- ✓ Extended runway of 10 years if credit facility accessed
- ✓ Growth-oriented strategy is sustainable
- → Low liquidity risk, adequate buffer

### Use Cases

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

### Data Sources

Extract liquidity data from:
- **Consolidated Balance Sheet** - Cash and cash equivalents
- **Note Disclosures - Credit Facilities** - Drawn vs undrawn capacity
- **Note Disclosures - Restricted Cash** - Identify unavailable cash
- **MD&A - Liquidity Discussion** - Management commentary on liquidity position

## Complete Example

```json
{
  "issuer_name": "Artis Real Estate Investment Trust",
  "reporting_date": "2025-06-30",
  "reporting_period": "Q2 2025",
  "currency": "CAD",

  "balance_sheet": {
    "total_assets": 2611435,
    "investment_properties": 2025831,
    "cash": 16639,
    "mortgages_noncurrent": 217903,
    "mortgages_current": 423519,
    "credit_facilities": 437590,
    "senior_unsecured_debentures": 0,
    "total_liabilities": 1155452,
    "total_unitholders_equity": 1455983
  },

  "income_statement": {
    "noi": 30729,
    "interest_expense": 16937,
    "revenue": 59082,
    "q2_2025": {
      "revenue": 59082,
      "net_operating_income": 30729
    }
  },

  "ffo_affo": {
    "ffo": 16956,
    "affo": 8204,
    "ffo_per_unit": 0.17,
    "affo_per_unit": 0.08,
    "distributions_per_unit": 0.03
  },

  "portfolio": {
    "total_properties": 0,
    "total_gla_sf": 0,
    "occupancy_rate": 0.878,
    "occupancy_with_commitments": 0.890,
    "same_property_noi_growth_6m": 0.023
  },

  "acfo_components": {
    "cash_flow_from_operations": 48500,
    "change_in_working_capital": -1500,
    "interest_financing": 14000,
    "jv_distributions": 2500,
    "capex_sustaining_acfo": -7500,
    "capex_development_acfo": -15000,
    "leasing_costs_external": -1800,
    "tenant_improvements_acfo": -3500,
    "deferred_financing_fees": 350,
    "non_controlling_interests_acfo": -450,
    "calculation_method_acfo": "actual",
    "jv_treatment_method": "distributions",
    "missing_adjustments_acfo": []
  },

  "cash_flow_investing": {
    "development_capex": -15000,
    "property_acquisitions": -30000,
    "property_dispositions": 25000,
    "jv_capital_contributions": -5000,
    "jv_return_of_capital": 2000,
    "total_cfi": -23000
  },

  "cash_flow_financing": {
    "debt_principal_repayments": -15000,
    "new_debt_issuances": 10000,
    "distributions_common": -18000,
    "distributions_preferred": -1000,
    "equity_issuances": 5000,
    "total_cff": -19000
  },

  "liquidity": {
    "cash_and_equivalents": 16639,
    "marketable_securities": 0,
    "restricted_cash": 0,
    "undrawn_credit_facilities": 150000,
    "credit_facility_limit": 200000,
    "available_cash": 16639,
    "total_available_liquidity": 166639,
    "data_source": "Q2 2025 balance sheet + note 15"
  }
}
```

**Note:** This example includes all optional sections (acfo_components, cash_flow_investing, cash_flow_financing, liquidity) for comprehensive analysis. Extract these sections when data is available for advanced credit metrics (ACFO, AFCF, burn rate).

## Validation

### Automated Validation

Run schema validation after Phase 2 extraction:

```bash
python scripts/validate_extraction_schema.py <path_to_json>
```

Example:
```bash
python scripts/validate_extraction_schema.py \
  Issuer_Reports/Artis_REIT/temp/phase2_extracted_data.json
```

### Expected Output

✅ **Valid schema:**
```
📋 Validating schema for: phase2_extracted_data.json
======================================================================

✅ Schema validation PASSED

Issuer: Artis Real Estate Investment Trust
Reporting Date: 2025-06-30
Currency: CAD

✅ This file is compatible with Phase 3 calculations
```

❌ **Invalid schema:**
```
❌ Schema validation FAILED

Found 3 errors:

  ❌ Missing required field: balance_sheet.mortgages_noncurrent
  ❌ Missing required field: income_statement.noi
  ❌ Field 'portfolio.occupancy_rate' must be numeric, got str

💡 Fix these errors before running Phase 3 calculations
```

## Common Issues and Fixes

### Issue 1: Nested balance_sheet structure

**Error:** `TypeError: unsupported operand type(s) for /`

**Cause:** Phase 3 expects flat structure

**Fix:** Flatten balance_sheet fields to top level

### Issue 2: Missing top-level noi/interest_expense

**Error:** `KeyError: 'income_statement.noi'`

**Cause:** Only nested quarterly data provided

**Fix:** Add top-level fields for most recent period

### Issue 3: Null values in portfolio

**Error:** `TypeError: unsupported operand type(s) for /: 'NoneType' and 'int'`

**Cause:** `total_gla_sf: null`

**Fix:** Use `0` instead of `null`

### Issue 4: Wrong occupancy format

**Error:** Occupancy calculated as 8780% instead of 87.8%

**Cause:** Used `87.8` instead of `0.878`

**Fix:** Convert to decimal (divide by 100)

## Phase 3 Compatibility

Phase 3 (`calculate_credit_metrics.py`) has been updated to:

1. ✅ Accept flat balance_sheet structure
2. ✅ Support both old and new field naming conventions
3. ✅ Handle null values gracefully (convert to 0)
4. ✅ Validate required fields and fail with clear error messages

## Migration Guide

### Updating Existing Extractions

If you have existing Phase 2 JSON files that fail validation:

1. **Run validation first:**
   ```bash
   python scripts/validate_extraction_schema.py <your_file.json>
   ```

2. **Fix errors in order:**
   - Required fields first
   - Type mismatches second
   - Naming conventions third (warnings only)

3. **Re-run Phase 3:**
   ```bash
   python scripts/calculate_credit_metrics.py <your_file.json>
   ```

### Creating New Extractions

When creating new Phase 2 extractions:

1. Use the updated `extract_key_metrics.py` script
2. It now includes schema instructions in the prompt
3. Validate output automatically before Phase 3
4. Schema compliance is enforced

## References

- **Schema Definition:** `.claude/knowledge/phase2_extraction_schema_v2.json` (AUTHORITATIVE)
- **Extraction Guide:** `.claude/knowledge/COMPREHENSIVE_EXTRACTION_GUIDE.md`
- **Validator:** `scripts/validate_extraction_schema.py`
- **Phase 3 Script:** `scripts/calculate_credit_metrics.py`

## Questions?

If you encounter schema issues:

1. Run the validator to identify specific problems
2. Check this README for common issues
3. Review the complete example above
4. Consult the JSON schema files for technical details

---

**Last Updated:** 2025-10-20
**Schema Version:** 1.0.11
**Pipeline Version:** 1.0.11

## Version History

### v1.0.11 (2025-10-20)
- Added comprehensive documentation for ACFO components (17 REALPAC adjustments)
- Added AFCF support documentation (cash_flow_investing and cash_flow_financing)
- Added burn rate and liquidity analysis documentation
- Updated complete example to include all optional sections
- Synchronized documentation with latest schema files

### v1.0.8 (2025-10-17)
- Added dilution tracking documentation
- Initial schema documentation

### v1.0.0 (2025-10-17)
- Initial release of SCHEMA_README.md
