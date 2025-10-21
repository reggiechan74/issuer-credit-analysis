# Burn Rate Analysis Command

Generate a comprehensive cash burn rate and liquidity runway analysis report for a REIT.

## Usage

```bash
/burnrate <issuer-name-or-path>
```

## Parameters

- `<issuer-name-or-path>`: Either:
  - Issuer name (e.g., "Artis REIT", "DIR") - searches in Issuer_Reports/
  - Direct path to Phase 2 extracted data JSON file

## What This Command Does

**NOTE:** This command creates a **standalone burn rate analysis report**. It can be run anytime after Phase 2 extraction is complete. It does NOT require the main credit opinion report to be generated first - it performs its own calculations independently.

1. **Loads Financial Data**: Reads Phase 2 extracted data (must include cash_flow_investing, cash_flow_financing, and liquidity sections)

2. **Calculates Metrics** (performs own Phase 3-style calculations):
   - ACFO (Adjusted Cash Flow from Operations)
   - AFCF (Adjusted Free Cash Flow)
   - Mandatory Obligations (Debt Service + Distributions, NO new financing)
   - Burn Rate (when AFCF < Mandatory Obligations)
   - Cash Runway (months until cash depletion)
   - Liquidity Risk Assessment
   - Sustainable Burn Rate

3. **Generates Report**: Creates a formatted markdown report with:
   - Executive summary
   - Detailed calculations
   - Liquidity risk assessment
   - Credit implications
   - Recommended actions

4. **Saves Output**: Saves report to `Issuer_Reports/{Issuer}/reports/`

## Prerequisites

The Phase 2 extracted data JSON must include:
- ✅ `cash_flow_investing` section (for AFCF calculation)
- ✅ `cash_flow_financing` section (for Mandatory Obligations)
- ✅ `liquidity` section (for cash runway)
- ✅ `coverage_ratios` section (for period interest and annualization factor)
- ✅ `acfo_components` section (optional, for ACFO calculation)

If liquidity data is missing, you'll be prompted to extract it from the issuer's MD&A.

## Examples

```bash
# Using issuer name
/burnrate "Artis REIT"

# Using issuer abbreviation
/burnrate DIR

# Using direct path
/burnrate Issuer_Reports/Artis_REIT/temp/phase2_extracted_data.json
```

## Task Instructions

You are tasked with generating a comprehensive **Cash Burn Rate and Liquidity Runway Analysis Report** for the specified REIT issuer.

### Step 1: Locate and Load Financial Data

1. If given an issuer name, search `Issuer_Reports/` for matching directory
2. Load the Phase 2 extracted data from `temp/phase2_extracted_data.json`
3. Verify required sections exist:
   - `cash_flow_investing`
   - `cash_flow_financing`
   - `liquidity` (if missing, prompt user to extract from MD&A)
   - `acfo_components` or `cash_flow_from_operations`

### Step 2: Run Burn Rate Calculations

Execute the following Python script to calculate all metrics:

```python
import json
import sys
from datetime import datetime
sys.path.insert(0, 'scripts')

from calculate_credit_metrics import (
    calculate_acfo_from_components,
    calculate_afcf,
    calculate_burn_rate,
    calculate_cash_runway,
    assess_liquidity_risk,
    calculate_sustainable_burn_rate
)

# Load data
with open('<path-to-phase2-json>') as f:
    data = json.load(f)

# Calculate ACFO
acfo_result = calculate_acfo_from_components(data)
data['acfo_calculated'] = acfo_result['acfo_calculated']

# Calculate AFCF
afcf_result = calculate_afcf(data)

# Ensure coverage_ratios exists with period_interest_expense
# (This should already be calculated in Phase 3 calculate_credit_metrics.py)
# coverage_ratios contains: period_interest_expense, annualization_factor

# Calculate Burn Rate (uses period amounts, NO new financing)
burn_result = calculate_burn_rate(data, afcf_result)

# If burn rate applicable, calculate runway and risk
if burn_result['applicable']:
    runway_result = calculate_cash_runway(data, burn_result)
    risk_result = assess_liquidity_risk(runway_result)
    sustainable_result = calculate_sustainable_burn_rate(data, burn_result, target_runway_months=24)
else:
    runway_result = None
    risk_result = None
    sustainable_result = None
```

### Step 3: Generate Formatted Report

Create a markdown report using this template:

```markdown
# Cash Burn Rate & Liquidity Analysis
## {Issuer Name}

**Report Date:** {Current Date}
**Reporting Period:** {data['reporting_period']}
**Currency:** {data['currency']} (thousands)
**Analysis Version:** 1.0.7

---

## Executive Summary

### Liquidity Risk Assessment

**Risk Level:** {risk_result['risk_level'] if applicable else 'N/A - SELF-FUNDED'}
**Risk Score:** {risk_result['risk_score']}/4

{risk_result['assessment']}

### Key Metrics

| Metric | Amount | Status |
|--------|--------|--------|
| **ACFO** | ${acfo_result['acfo_calculated']:,.0f}K | {POSITIVE/NEGATIVE} |
| **AFCF** | ${afcf_result['afcf']:,.0f}K | {POSITIVE/NEGATIVE} |
| **Mandatory Obligations** | ${burn_result['mandatory_obligations']:,.0f}K | - |
| **Self-Funding Ratio** | {burn_result['self_funding_ratio']:.2f}x | {✓ if >= 1.0 else ⚠️} |
| **Burn Rate** | ${burn_result['monthly_burn_rate']:,.0f}K/month | {if applicable} |
| **Cash Runway** | {runway_result['runway_months']:.1f} months | {if applicable} |
| **Available Liquidity** | ${data['liquidity']['total_available_liquidity']:,.0f}K | - |

---

## 1. Operating Performance

### Adjusted Cash Flow from Operations (ACFO)

**Cash Flow from Operations:** ${data['acfo_components']['cash_flow_from_operations']:,.0f}K
**ACFO (Calculated):** ${acfo_result['acfo_calculated']:,.0f}K
**Data Quality:** {acfo_result['data_quality']}

{If ACFO positive: "✓ Strong operating cash flow generation"}
{If ACFO negative: "⚠️ Operations consuming cash - negative ACFO"}

### Adjusted Free Cash Flow (AFCF)

```
ACFO:                    ${acfo_result['acfo_calculated']:,.0f}K
+ Net Cash from Investing: ${afcf_result['net_cfi']:,.0f}K
= AFCF:                   ${afcf_result['afcf']:,.0f}K
```

**Investment Activity Breakdown:**
- Property Dispositions: ${data['cash_flow_investing']['property_dispositions']:,.0f}K
- Property Acquisitions: ${data['cash_flow_investing']['property_acquisitions']:,.0f}K
- Development CAPEX: ${data['cash_flow_investing']['development_capex']:,.0f}K
- JV Activity (net): ${net_jv:,.0f}K

**Strategy:** {if net_cfi > 0: "Asset harvesting" else: "Growth/investment phase"}

---

## 2. Mandatory Obligations & Burn Rate

### Mandatory Obligations (Forward-Looking Stress Test)

**Total Debt Service (Period):**
- Period Interest: ${period_interest:,.0f}K
- Principal Repayments: ${principal_repayments:,.0f}K
- **TOTAL:** ${total_debt_service:,.0f}K

**Total Distributions (Period):**
- Common Unitholders: ${distributions_common:,.0f}K
- Preferred Unitholders: ${distributions_preferred:,.0f}K
- **TOTAL:** ${total_distributions:,.0f}K

**Mandatory Obligations:** ${mandatory_obligations:,.0f}K

**Note:** Burn rate is a forward-looking stress test. New financing is NOT subtracted - we assume NO future access to capital markets.

### Burn Rate Analysis

**AFCF (Period):** ${afcf:,.0f}K
**Mandatory Obligations (Period):** ${mandatory_obligations:,.0f}K
**Self-Funding Ratio:** {ratio:.2f}x
**Reporting Period:** {period_months} months

{If burn_result['applicable']:}
**⚠️ BURN RATE APPLICABLE**

The REIT's AFCF (${afcf:,.0f}K) cannot cover its mandatory obligations (${mandatory_obligations:,.0f}K).

**Period Deficit:** ${burn_result['period_burn_rate']:,.0f}K (for {period_months}-month period)
**Monthly Burn Rate:** ${burn_result['monthly_burn_rate']:,.0f}K/month

**What This Means:**
At the current run rate, the REIT depletes ${abs(burn_result['monthly_burn_rate']):,.0f}K of cash per month. This assumes distributions and debt service continue at current levels with NO new financing.

{Else:}
**✓ SELF-FUNDED**

{burn_result['reason']}

**Monthly Surplus:** ${burn_result['monthly_surplus']:,.0f}K/month

---

## 3. Liquidity Position & Cash Runway

{If burn rate applicable:}

### Available Liquidity

- **Cash & Equivalents:** ${liquidity['cash_and_equivalents']:,.0f}K
- **Marketable Securities:** ${liquidity['marketable_securities']:,.0f}K
- **Restricted Cash:** (${liquidity['restricted_cash']:,.0f}K)
- **Available Cash:** ${liquidity['available_cash']:,.0f}K
- **Undrawn Credit Facilities:** ${liquidity['undrawn_credit_facilities']:,.0f}K
- **Total Available Liquidity:** ${liquidity['total_available_liquidity']:,.0f}K

### Cash Runway

**Using Cash Only:**
- **Runway:** {runway_result['runway_months']:.1f} months ({runway_result['runway_years']:.1f} years)
- **Estimated Depletion Date:** {runway_result['depletion_date']}

**Including Credit Facilities:**
- **Extended Runway:** {runway_result['extended_runway_months']:.1f} months ({runway_result['extended_runway_years']:.1f} years)

### Liquidity Risk Assessment

**Risk Level:** {risk_result['risk_level']}
**Risk Score:** {risk_result['risk_score']}/4

{risk_result['assessment']}

{If warning_flags:}
**Warning Flags:**
{for flag in risk_result['warning_flags']:}
- {flag}

**Recommended Actions:**
{for rec in risk_result['recommendations']:}
- {rec}

### Sustainable Burn Rate

To maintain a **{sustainable_result['target_runway_months']}-month cash runway**, the REIT should burn no more than:

**Sustainable Monthly Burn:** ${sustainable_result['sustainable_monthly_burn']:,.0f}K/month

**Actual Monthly Burn:** ${sustainable_result['actual_monthly_burn']:,.0f}K/month
**Excess Burn:** ${sustainable_result['excess_burn_per_month']:,.0f}K/month
**Excess Burn (Annual):** ${sustainable_result['excess_burn_annualized']:,.0f}K/year

**Status:** {sustainable_result['status']}

{End if burn rate applicable}

---

## 4. Credit Implications

### Operating Health
{If ACFO > 0: "✓ Positive operating cash flow indicates healthy core operations"}
{If ACFO < 0: "⚠️ Negative operating cash flow indicates operational challenges"}

### Capital Deployment Strategy
{If net_cfi > 0: "Asset harvesting / deleveraging strategy"}
{If net_cfi < 0: "Growth / acquisition strategy"}

### Self-Funding Capacity
{If self_funding_ratio >= 1.0:}
✓ **SELF-SUFFICIENT** - AFCF fully covers financing obligations without external capital

{Else if self_funding_ratio >= 0.8:}
⚠️ **NEAR SELF-SUFFICIENT** - Minimal reliance on capital markets ({(1-ratio)*100:.0f}% shortfall)

{Else if self_funding_ratio >= 0.5:}
⚠️ **MODERATE RELIANCE** - Significant dependence on capital markets ({(1-ratio)*100:.0f}% shortfall)

{Else:}
🚨 **HIGH RELIANCE** - Heavily dependent on capital markets or asset sales ({(1-ratio)*100:.0f}% shortfall)

### Distribution Sustainability

**AFFO Payout Ratio:** {affo_payout_ratio*100:.1f}%
{If < 100%: "✓ Distributions covered by AFFO"}
{If >= 100%: "⚠️ Distributions exceed AFFO - unsustainable without external financing"}

### Overall Credit Assessment

{Generate overall assessment based on:}
- ACFO sign (positive/negative)
- AFCF sign (positive/negative)
- Self-funding ratio
- Cash runway (if applicable)
- Risk level
- AFFO payout ratio
{Provide STRONG/ADEQUATE/MODERATE/WEAK/CRITICAL rating}

---

## 5. Comparative Analysis

{If other REIT reports available, include comparison table}

---

## Appendix: Methodology

**Burn Rate Definition:**
```
Burn Rate = Mandatory Obligations - AFCF (when AFCF < Mandatory Obligations)

Where:
  Mandatory Obligations = Debt Service + Distributions (period amounts)
  Debt Service = Period Interest + Period Principal Repayments
  AFCF = ACFO + Net Cash Flow from Investing (period amount)
  Monthly Burn Rate = Period Deficit / Number of Months in Period

IMPORTANT: Do NOT subtract new financing - burn rate is a forward-looking stress test
           that assumes NO future access to capital markets.
```

**Cash Runway:**
```
Cash Runway = Available Cash / Monthly Burn Rate
Extended Runway = (Available Cash + Undrawn Facilities) / Monthly Burn Rate
```

**Risk Thresholds:**
- CRITICAL: < 6 months
- HIGH: 6-12 months
- MODERATE: 12-24 months
- LOW: > 24 months

---

**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Analysis Tool:** Claude Code Burn Rate Analysis v1.0.7
**Issue:** #7 - Cash Burn Rate and Runway Analysis
```

### Step 4: Save Report

Save the generated report to:
```
Issuer_Reports/{Issuer_Name}/reports/{YYYY-MM-DD_HHMMSS}_Burn_Rate_Analysis_{Issuer}.md
```

### Step 5: Display Summary

After generating the report, display a concise summary to the user:

```
✓ Burn Rate Analysis Complete for {Issuer Name}

Key Findings:
- Risk Level: {risk_level}
- Self-Funding: {ratio:.0%}
- Cash Runway: {runway_months:.1f} months
- Burn Rate: ${burn_rate:,.0f}K/year {if applicable}

Report saved to: {report_path}
```

## Error Handling

### If Liquidity Section Missing or Incorrect

If the `liquidity` section is missing or shows incorrect data (e.g., $0 undrawn when facilities exist), extract it from the issuer's MD&A using this guidance:

**Where to Look (Priority Order):**
1. **MD&A "Credit Facilities" or "Liquidity" section** (MOST AUTHORITATIVE)
   - Usually includes current facility limits, drawn amounts, and available capacity
   - Example: "At June 30, 2025, the REIT had $78,400 available on its revolving term credit facilities"

2. **Financial Statement Notes** (e.g., Note 10 - Credit Facilities)
   - Detailed terms and facility descriptions
   - May show balances and limits

3. **Balance Sheet line items**
   - Shows total drawn amount but rarely shows available capacity
   - Use to verify drawn amounts from other sources

4. **Subsequent Events notes**
   - ⚠️ May reference future/planned limits, not current limits
   - Always verify against current period MD&A

**Handling Multiple Credit Facilities:**

Many REITs have multiple facilities (revolving + non-revolving, or multiple tranches). For each facility:
1. Identify facility type (revolving, non-revolving, term loan, etc.)
2. Find the limit for EACH facility (not just total)
3. Find the drawn amount for EACH facility
4. Calculate undrawn: `facility_limit - facility_drawn`
5. Sum all undrawn amounts for total capacity

**Example - Artis REIT Q2 2025:**
```
MD&A page 36: "The REIT has a secured revolving term credit facility
in the amount of $350,000... At June 30, 2025, the REIT had $78,400 available"

Notes: "As at June 30, 2025, there was $271,600 drawn on the revolving
credit facility and $170,000 drawn on the non-revolving credit facility"

Calculation:
- Revolving: $350,000 limit - $271,600 drawn = $78,400 available ✓
- Non-revolving: $170,000 drawn (assume fully drawn if limit not stated) = $0 available
- Total undrawn: $78,400K
```

**Handling Conflicting Information:**

If you find conflicting facility limits (e.g., $275M in one place, $350M in another):
1. Prioritize MD&A credit facilities section - this is the most current source
2. Check dates - subsequent events may reference future amendments
3. Look for "available" or "undrawn" disclosures stated directly
4. DO NOT make conservative assumptions - search more thoroughly

**⚠️ Borrowing Base vs Facility Limit:**

Many secured facilities have BOTH:
- **Facility Limit**: Maximum committed amount (e.g., $350M) - use this for undrawn calculation
- **Borrowing Base**: Current capacity based on secured property values (e.g., $514M) - informational only

**Required JSON Format:**
```json
{
  "liquidity": {
    "cash_and_equivalents": 16639,
    "marketable_securities": 0,
    "restricted_cash": 0,
    "undrawn_credit_facilities": 78400,
    "credit_facility_limit": 520000,
    "available_cash": 16639,
    "total_available_liquidity": 95039,
    "data_source": "Q2 2025 MD&A page 36. Revolving facility $350M, $271.6M drawn, $78.4M available. Non-revolving $170M drawn (assumed fully drawn)."
  }
}
```

### Other Error Conditions

- If cash_flow_financing missing: Cannot calculate burn rate - inform user
- If ACFO components missing: Try to use FFO/AFFO data as proxy
- If issuer not found: List available issuers in Issuer_Reports/

## Notes

**When to Run:**
- ✅ Can run **anytime after Phase 2 extraction** is complete
- ✅ Does **NOT** require Phase 3 or Phase 5 (main report) to be generated first
- ✅ Performs its own ACFO/AFCF/burn rate calculations independently
- ✅ Creates a **standalone** burn rate analysis report
- ℹ️ Typically run as a follow-up to the main credit report for deep-dive liquidity analysis

**Requirements:**
- Phase 2 data with complete cash flow information (CFI, CFF, liquidity)
- For best results, ensure liquidity data is extracted from the issuer's MD&A

**Methodology:**
- Burn rate is a forward-looking stress test that assumes NO future capital markets access
- New financing is NOT subtracted - we measure mandatory obligations only (debt service + distributions)
- Self-funding ratio = AFCF / (Debt Service + Distributions) - does NOT subtract new financing
- A REIT can have positive AFCF but still burn cash if mandatory obligations exceed free cash flow
