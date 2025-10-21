# Adjusted Free Cash Flow (AFCF) - Research & Proposal

## Executive Summary

This document proposes a new **Adjusted Free Cash Flow (AFCF)** metric that bridges the gap between operating cash flow (ACFO) and financing cash flows for real estate issuer credit analysis. AFCF represents the cash available to service debt and equity obligations after all operating and investing activities.

**Date:** 2025-10-20
**Purpose:** Design AFCF calculation methodology for comparing against debt/equity payments
**Starting Point:** ACFO (Adjusted Cash Flow from Operations) per REALPAC methodology

---

## Conceptual Framework

### Cash Flow Cascade

```
IFRS Cash Flow from Operations (CFO)
  + 17 ACFO Adjustments (REALPAC Jan 2023)
= Adjusted Cash Flow from Operations (ACFO)    ← Current endpoint
  - Cash Outflows from Investing Activities
  + Cash Inflows from Investing Activities
= Adjusted Free Cash Flow (AFCF)                ← New metric
  vs.
  Cash Flows from Financing Activities
  (Debt principal, distributions, equity transactions)
```

### Key Distinction

**ACFO** = Sustainable economic cash flow from operations (already deducts sustaining capex/TI/leasing costs)
**AFCF** = Free cash flow after ALL investing activities (growth capex, acquisitions, dispositions)

---

## What ACFO Already Captures

Per REALPAC ACFO White Paper (January 2023), ACFO **already deducts**:

1. **Sustaining Capital Expenditures** (Adj 4) - Routine maintenance capex
2. **Tenant Improvements** (Adj 6) - Sustaining TI only
3. **External Leasing Costs** (Adj 5) - Costs to lease up properties

These are **recurring operating requirements** already reflected in ACFO.

---

## What AFCF Should Deduct (Investing Activities)

### Category 1: Growth & Development (CASH OUTFLOWS)

**1.1 Development Capital Expenditures**
- New property development projects
- Major redevelopments and repositioning
- Land acquisition for development
- **Note:** NOT sustaining capex (already in ACFO)

**1.2 Property Acquisitions**
- Purchase of new investment properties
- Portfolio acquisitions
- Land purchases (non-development)

**1.3 Business Combinations**
- Acquisitions of entire REIT entities
- Asset purchase transactions
- **Note:** Transaction costs may already be in ACFO (Adj 9)

**1.4 Joint Venture Investments**
- Capital contributions to JV development projects
- Equity investments in joint ventures
- **Note:** JV distributions are already in ACFO (Adj 3)

**1.5 Other Development Costs**
- Pre-development costs capitalized
- Development soft costs not in CFO

### Category 2: Dispositions & Returns (CASH INFLOWS)

**2.1 Property Dispositions**
- Sale proceeds from investment properties
- **Note:** Gains/losses excluded from FFO/ACFO

**2.2 Joint Venture Dispositions**
- Return of capital from JV exits
- Sale of JV interests

**2.3 Other Investing Inflows**
- Proceeds from marketable securities sales
- Return of development deposits

### Category 3: Other Investing Items

**3.1 Changes in Restricted Cash**
- Escrows and reserves (if classified as investing)
- Tenant improvement reserves

**3.2 Other Capital Investments**
- Investments in securities (if material)
- Other long-term asset acquisitions

---

## Proposed AFCF Calculation

### Formula

```
AFCF = ACFO
       - Development CAPEX (net of sustaining)
       - Property Acquisitions
       - JV Capital Contributions
       - Other Growth Investments
       + Property Disposition Proceeds
       + JV Disposition Proceeds
       + Other Investing Inflows
```

### Alternative Shorthand

```
AFCF = ACFO + Net Cash Flow from Investing Activities
```

**Where:**
- Net CFI = Cash inflows from investing - Cash outflows from investing
- Excludes items already adjusted in ACFO calculation

---

## Use Case: Comparison to Financing Activities

### Purpose

AFCF measures **cash available for financing obligations**:

```
AFCF vs. Financing Cash Outflows
  - Principal repayments on debt
  - Distributions to unitholders
  - Distributions to non-controlling interests
  - Preferred unit distributions
  - Share/unit buybacks
  + New debt drawdowns
  + Equity issuances
= Change in Cash Position
```

### Key Coverage Ratios

**1. AFCF to Total Debt Service**
```
AFCF / (Interest Expense + Principal Repayments)
```
- Measures ability to service all debt obligations from free cash flow
- More conservative than NOI/Interest coverage

**2. AFCF to Distributions**
```
AFCF / Total Distributions
```
- Modified payout ratio based on true free cash flow
- More conservative than AFFO payout ratio

**3. AFCF Self-Funding Ratio**
```
AFCF / (Total Debt Service + Total Distributions)
```
- Measures ability to cover all financing obligations from free cash flow
- <1.0x = reliant on external financing (cannot self-fund)
- ≥1.0x = self-funding (can cover obligations without new financing)
- NOTE: Does NOT subtract new financing (aligns with burn rate methodology)

---

## Data Requirements

### Required from Cash Flow Statement

**From Investing Activities Section:**
```json
{
  "cash_flow_investing": {
    "property_acquisitions": -50000,           // Outflow
    "property_dispositions": 25000,             // Inflow
    "development_capex": -30000,                // Outflow (incremental to sustaining)
    "jv_capital_contributions": -10000,         // Outflow
    "jv_return_of_capital": 5000,               // Inflow
    "other_investing_outflows": -2000,          // Other
    "other_investing_inflows": 1000             // Other
  }
}
```

**From Financing Activities Section (for comparison):**
```json
{
  "cash_flow_financing": {
    "debt_principal_repayments": -40000,        // Outflow
    "new_debt_issuances": 20000,                // Inflow
    "distributions_common": -12000,             // Outflow
    "distributions_preferred": -1000,           // Outflow
    "distributions_nci": -500,                  // Outflow
    "equity_issuances": 5000,                   // Inflow
    "unit_buybacks": -1000                      // Outflow
  }
}
```

### Reconciliation to IFRS Statement

The AFCF calculation should reconcile to the standard IFRS cash flow statement:

```
CFO (IFRS)
+ CFI (IFRS)
+ CFF (IFRS)
= Change in Cash

ACFO (Calculated)
+ Net CFI (Extracted)
= AFCF

AFCF
+ Net CFF (Extracted)
= Change in Cash (should match IFRS)
```

---

## Implementation Considerations

### 1. Double-Counting Prevention (CRITICAL)

**Critical:** Ensure no double-counting between ACFO and AFCF:

| Item | Already in ACFO? | Include in AFCF? | Notes |
|------|------------------|------------------|-------|
| Sustaining CAPEX | ✅ Yes (Adj 4) | ❌ No | Deducted in ACFO |
| Development CAPEX | ⚠️ Disclosed only | ✅ Yes | Add to CFI deduction |
| Tenant Improvements (sustaining) | ✅ Yes (Adj 6) | ❌ No | Already in ACFO |
| Tenant Improvements (development) | ❌ No | ✅ Yes | Part of development projects |
| External Leasing Costs | ✅ Yes (Adj 5) | ❌ No | Already in ACFO |
| Property Acquisitions | ❌ No | ✅ Yes | Pure investing activity |
| Property Dispositions | ❌ No | ✅ Yes | Investing inflow |
| JV Distributions Received | ✅ Yes (Adj 3a) | ❌ No | Operating in ACFO |
| JV Capital Contributions | ❌ No | ✅ Yes | Investing outflow |
| Transaction Costs (acquisitions) | ⚠️ Maybe (Adj 9) | ⚠️ Check | Verify ACFO treatment |

**Why This Works (Standard IFRS Practice):**

Under IFRS (IAS 7 Statement of Cash Flows), the classification is typically:

**Cash Flow from Operations (CFO):**
- Sustaining CAPEX (maintenance/routine capital expenditures)
- Sustaining tenant improvements (normal tenant turnover)
- External leasing costs (broker commissions for normal leasing)
- Interest paid (operating activity)

**Cash Flow from Investing (CFI):**
- Development CAPEX (growth projects, redevelopment)
- Property acquisitions (new investments)
- Property dispositions (sale of investments)
- JV capital contributions/returns
- Business combinations

**Therefore:**
- ACFO deducts sustaining items from CFO → They do NOT appear in CFI
- AFCF adds CFI to ACFO → No double-counting because sustaining items only in CFO
- The formula AFCF = ACFO + CFI is correct by design

**Verification Required:**
- Always verify that `total_cfi` from cash flow statement does NOT include sustaining items
- Check notes to financial statements for CAPEX classification methodology
- If issuer uses non-standard classification, adjust accordingly

### 2. Development CAPEX Treatment

**Issue:** ACFO Adjustment 4 includes:
- `capex_sustaining_acfo` - Already deducted in ACFO
- `capex_development_acfo` - Disclosed but NOT deducted in ACFO

**Solution:**
```python
# In AFCF calculation:
net_cfi_capex = -capex_development_acfo  # Deduct development capex not in ACFO
```

### 3. Alignment with Burn Rate Methodology

**AFCF Self-Funding Ratio** is the foundation for burn rate analysis (v1.0.7).

**Connection:**
```
If AFCF Self-Funding Ratio < 1.0x:
  → Cannot cover obligations from free cash flow
  → Burns cash to meet obligations
  → Burn Rate = Total Obligations - AFCF
  → Cash runway = Available Cash / Monthly Burn Rate

If AFCF Self-Funding Ratio ≥ 1.0x:
  → Self-funding (no burn rate)
  → Generates surplus cash
  → Can accumulate reserves or reduce debt
```

**Why NOT Subtract New Financing:**
- Self-funding ratio measures **inherent cash generation capacity**
- New financing is external/discretionary, not sustainable operations
- Burn rate analysis focuses on **how long can survive WITHOUT new financing**
- Consistent methodology: Both metrics measure self-sustainability

**Example - Artis REIT (v1.0.7):**
```
AFCF = $50.2M
Total Obligations = $98.4M (debt service + distributions)
Self-Funding Ratio = 50.2 / 98.4 = 0.51x

→ Can only cover 51% of obligations from free cash flow
→ Must access $48.2M from external sources (burn)
→ If no new financing: Burns $48.2M / 6 months = $8.0M/month
→ Cash runway = Available cash / Monthly burn
```

**Credit Implications:**
- <0.5x = HIGH reliance on capital markets
- 0.5x-0.8x = MODERATE reliance
- 0.8x-1.0x = LOW reliance (nearly self-funding)
- ≥1.0x = Self-funding (no reliance)

### 4. Joint Venture Treatment

**ACFO includes** (Adj 3):
- Distributions received from JVs (3a), OR
- ACFO from JVs (3b, calculated method)
- Notional interest on JV development (3c)

**AFCF should add:**
- Capital contributions TO joint ventures (outflow)
- Return of capital FROM joint ventures (inflow)
- NOT the recurring distributions (already in ACFO)

### 4. Transaction Costs

Check if transaction costs are already adjusted in ACFO:
- Adj 9: Transaction costs for acquisitions
- Adj 10: Transaction costs for disposals

If already in ACFO, do NOT deduct from property acquisition/disposition proceeds in AFCF.

---

## Proposed Schema Extension

### Add to Phase 2 Extraction Schema

```json
{
  "cash_flow_investing": {
    "_comment": "Required for AFCF calculation - extract from Cash Flow Statement investing section",
    "development_capex": "number - Development CAPEX not included in sustaining (should match capex_development_acfo)",
    "property_acquisitions": "number - Cash paid for property acquisitions (negative)",
    "property_dispositions": "number - Cash received from property sales (positive)",
    "jv_capital_contributions": "number - Capital invested in joint ventures (negative)",
    "jv_return_of_capital": "number - Return of capital from JV dispositions (positive)",
    "business_combinations": "number - Cash paid for acquiring entities (negative)",
    "other_investing_outflows": "number - Other investing cash outflows (negative)",
    "other_investing_inflows": "number - Other investing cash inflows (positive)",
    "total_cfi": "number - Total net cash from investing per IFRS (for reconciliation)"
  },

  "cash_flow_financing": {
    "_comment": "Required for AFCF coverage analysis - extract from Cash Flow Statement financing section",
    "debt_principal_repayments": "number - Principal repayments on all debt (negative)",
    "new_debt_issuances": "number - Proceeds from new debt (positive)",
    "distributions_common": "number - Distributions to common unitholders (negative)",
    "distributions_preferred": "number - Distributions to preferred unitholders (negative)",
    "distributions_nci": "number - Distributions to non-controlling interests (negative)",
    "equity_issuances": "number - Proceeds from equity issuances (positive)",
    "unit_buybacks": "number - Cash paid for unit buybacks (negative)",
    "deferred_financing_costs_paid": "number - Cash paid for financing fees (negative)",
    "other_financing_outflows": "number - Other financing cash outflows (negative)",
    "other_financing_inflows": "number - Other financing cash inflows (positive)",
    "total_cff": "number - Total net cash from financing per IFRS (for reconciliation)"
  }
}
```

---

## Proposed Python Functions

### Function 1: Calculate AFCF

```python
def calculate_afcf(financial_data):
    """
    Calculate Adjusted Free Cash Flow (AFCF) from ACFO and investing activities

    AFCF = ACFO + Net Cash Flow from Investing Activities

    Purpose: Measure cash available for financing obligations (debt service + distributions)

    Args:
        financial_data (dict): Validated JSON with acfo_calculated and cash_flow_investing

    Returns:
        dict: {
            'afcf': float,
            'acfo': float,
            'net_cfi': float,
            'cfi_breakdown': dict,
            'data_quality': str
        }
    """
    pass
```

### Function 2: Calculate AFCF Coverage Ratios

```python
def calculate_afcf_coverage_ratios(financial_data, afcf):
    """
    Calculate coverage ratios using AFCF

    Ratios:
    1. AFCF to Total Debt Service = AFCF / (Interest + Principal)
    2. AFCF to Distributions = AFCF / Total Distributions
    3. AFCF to Net Financing = AFCF / (Debt Service + Dist - New Financing)

    Args:
        financial_data (dict): Validated JSON with cash_flow_financing
        afcf (float): Calculated AFCF value

    Returns:
        dict: Coverage ratios and components
    """
    pass
```

### Function 3: Validate AFCF Reconciliation

```python
def validate_afcf_reconciliation(financial_data, acfo, afcf):
    """
    Validate AFCF calculation reconciles to IFRS cash flow statement

    Check: CFO + CFI + CFF = Change in Cash
    Where: ACFO ≈ CFO (after adjustments)
           AFCF = ACFO + CFI

    Args:
        financial_data (dict): Complete financial data
        acfo (float): Calculated ACFO
        afcf (float): Calculated AFCF

    Returns:
        dict: Reconciliation checks and validation results
    """
    pass
```

---

## Industry Best Practices

### 1. Credit Rating Agency Approach

**Moody's / S&P / DBRS:**
- Focus on **cash flow available for debt service**
- Use operating cash flow AFTER sustaining capex
- Consider growth capex as discretionary
- Analyze debt service coverage from recurring cash flows

**AFCF Alignment:**
- AFCF represents cash AFTER all capex (sustaining + growth)
- More conservative than ACFO
- Better measure for highly levered issuers
- Accounts for growth investment requirements

### 2. REIT-Specific Considerations

**REITs differ from corporates:**
- High payout requirements (90%+ of taxable income)
- Require external financing for growth
- Capital-intensive business model
- Portfolio turnover (acquisitions/dispositions)

**AFCF Advantages for REITs:**
- Captures episodic property transactions
- Measures true self-funding capacity
- Identifies reliance on capital markets
- Better indicator of financial flexibility

### 3. Private Real Estate vs. Public REITs

**Private Real Estate:**
- Often focus on property-level cash flow
- Less emphasis on corporate-level FCF
- Acquisitions funded with new debt

**Public REITs (our focus):**
- Corporate-level cash flow critical
- Access to equity markets
- Distributions drive valuation
- **AFCF helps assess distribution sustainability**

---

## Proposed Workflow Integration

### Phase 3 Enhancement

**Current Phase 3:**
```
Phase 2 JSON → calculate_reit_metrics() → ACFO calculated → Output
```

**Enhanced Phase 3:**
```
Phase 2 JSON
  → calculate_reit_metrics() → ACFO calculated
  → calculate_afcf() → AFCF calculated
  → calculate_afcf_coverage_ratios() → Coverage metrics
  → Output (includes AFCF + ratios)
```

### Phase 2 Extraction Update

**Add to extraction prompt:**
- Extract complete Cash Flow Statement (CFO, CFI, CFF)
- Break down CFI into components (acquisitions, dispositions, development)
- Break down CFF into components (debt, equity, distributions)
- Ensure reconciliation to IFRS totals

---

## Validation & Quality Checks

### 1. Internal Consistency

```python
# Check 1: CFO + CFI + CFF = Change in Cash
assert abs((cfo + cfi + cff) - change_in_cash) < 100  # Allow rounding

# Check 2: ACFO + CFI = AFCF
assert afcf == acfo + net_cfi

# Check 3: Development CAPEX matches
assert cash_flow_investing['development_capex'] == acfo_components['capex_development_acfo']
```

### 2. Reasonableness Tests

```python
# AFCF should be less than ACFO for growing REITs (net investing outflow)
if net_cfi < 0:  # Net investing outflow
    assert afcf < acfo

# AFCF should be positive for stable operations
if acfo > 0 and abs(net_cfi) < acfo:
    assert afcf > 0 or abs(afcf) < acfo * 0.5  # Allow some negative FCF
```

### 3. Coverage Ratio Bounds

```python
# AFCF debt service coverage should be lower than NOI coverage
assert afcf_dscr < noi_interest_coverage

# AFCF payout ratio should be higher than AFFO payout
if afcf > 0:
    assert afcf_payout_ratio > affo_payout_ratio
```

---

## Example Calculation

### Sample Data

```json
{
  "acfo_calculated": 50000,
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
  },
  "coverage_ratios": {
    "annualized_interest_expense": 40000
  }
}
```

### Calculation

```python
# Step 1: Calculate AFCF
ACFO = 50,000
Net CFI = -28,000  # From IFRS cash flow statement
AFCF = 50,000 + (-28,000) = 22,000

# Step 2: Calculate coverage ratios
Total_Debt_Service = 40,000 (interest) + 15,000 (principal) = 55,000
AFCF_Debt_Coverage = 22,000 / 55,000 = 0.40x  # ⚠️ Low coverage

Total_Distributions = 18,000 + 1,000 = 19,000
AFCF_Payout_Ratio = 19,000 / 22,000 = 86.4%

Total_Obligations = 55,000 (debt service) + 19,000 (dist) = 74,000
AFCF_Self_Funding_Ratio = 22,000 / 74,000 = 0.30x  # Needs external financing

Net_Financing_Received = 15,000 (new debt + equity)
Financing_Gap = 74,000 - 22,000 = 52,000  # Must be covered by new financing

# Step 3: Reconciliation
CFO (IFRS) = ~50,000 (approximates ACFO)
CFI (IFRS) = -28,000
CFF (IFRS) = -19,000
Change in Cash = 50,000 - 28,000 - 19,000 = 3,000  ✅
```

### Interpretation

**Findings:**
- ACFO = $50M (strong operating cash flow)
- Net CFI = -$28M (growth investments exceed dispositions)
- AFCF = $22M (positive but constrained)
- AFCF/Debt Service = 0.40x (⚠️ LOW - cannot cover debt + interest from free cash flow)
- AFCF/Distributions = 115.8% (sustainable but tight)
- AFCF Self-Funding Ratio = 0.30x (can only cover 30% of total obligations)
- Required external financing = $52M ($74M obligations - $22M AFCF)

**Credit Implications:**
- Issuer is growth-oriented (high investing outflows)
- Cannot self-fund debt service from free cash flow
- Reliant on capital markets for debt refinancing
- Distribution coverage adequate from AFCF
- **Credit risk:** Moderate to High (financing reliance)

---

## Next Steps

### 1. Schema Design
- [ ] Add `cash_flow_investing` section to Phase 2 schema
- [ ] Add `cash_flow_financing` section to Phase 2 schema
- [ ] Define required vs. optional fields
- [ ] Create validation rules

### 2. Implementation
- [ ] Write `calculate_afcf()` function
- [ ] Write `calculate_afcf_coverage_ratios()` function
- [ ] Write `validate_afcf_reconciliation()` function
- [ ] Integrate into `calculate_credit_metrics.py`
- [ ] Add unit tests

### 3. Extraction
- [ ] Update Phase 2 extraction prompt to include CFI/CFF
- [ ] Test extraction with sample financial statements
- [ ] Validate data quality and completeness

### 4. Documentation
- [ ] Update CLAUDE.md with AFCF methodology
- [ ] Add AFCF to credit analysis template
- [ ] Document coverage ratio interpretations
- [ ] Create AFCF reconciliation table format

### 5. Testing
- [ ] Create test fixtures with sample data
- [ ] Test with real REIT financial statements
- [ ] Validate against manual calculations
- [ ] Verify reconciliation to IFRS statements

---

## References

1. **REALPAC ACFO White Paper** (January 2023) - ACFO methodology
2. **IAS 7 Statement of Cash Flows** - IFRS cash flow classification
3. **Moody's REIT Rating Methodology** - Credit metrics and coverage ratios
4. **S&P Global REIT Criteria** - Cash flow analysis framework
5. **CFA Institute** - Free cash flow analysis in capital-intensive industries

---

## Conclusion

**AFCF (Adjusted Free Cash Flow) provides a critical missing link in real estate credit analysis:**

1. **Bridges operating and financing activities** - Shows cash available after ALL investments
2. **More conservative than ACFO** - Accounts for growth capital requirements
3. **Better debt coverage metric** - Measures true ability to service obligations
4. **Identifies financing needs** - Highlights reliance on capital markets
5. **Enhances credit analysis** - Complements existing FFO/AFFO/ACFO metrics

**Recommendation:** Implement AFCF calculation as a complementary metric to the existing ACFO framework, focusing on credit analysis and debt service coverage applications.

---

**Document Author:** Claude Code & Reggie Chan
**Date:** 2025-10-20
**Version:** 1.0 (Draft)
**Status:** Proposal - Pending Implementation
