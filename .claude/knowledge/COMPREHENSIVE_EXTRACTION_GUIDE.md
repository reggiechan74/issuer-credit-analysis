# Comprehensive Phase 2 Extraction Guide
## FFO/AFFO/ACFO Component Extraction

**Last Updated:** 2025-10-20 (v1.0.11)
**Purpose:** Enable full FFO/AFFO/ACFO reconciliation tables in credit reports

---

## Table of Contents
1. [FFO/AFFO Components Extraction](#ffо-affo-components)
2. [ACFO Components Extraction](#acfo-components)
3. [Cash Flow Investing/Financing](#cash-flow-sections)
4. [Liquidity Data Extraction](#liquidity-extraction)
5. [Dilution Detail Extraction](#dilution-extraction)

---

## FFO/AFFO Components

### Purpose
- Enables calculating FFO/AFFO from first principles per REALPAC methodology (Jan 2022)
- Validates issuer-reported FFO/AFFO values
- Generates detailed reconciliation tables (Net Income → FFO → AFFO)

### When to Extract
**Always attempt** to extract these components - they unlock comprehensive reconciliation analysis

### Where to Find
1. **MD&A Document** - Search for:
   - "Funds From Operations (FFO) and Adjusted Funds From Operations (AFFO)"
   - "Non-IFRS Financial Measures"
   - "Reconciliation of Net Income to FFO"
   - "FFO/AFFO Calculation" or "FFO/AFFO Reconciliation"

2. **Financial Statement Notes** - Often in:
   - "Significant Accounting Policies"
   - "Non-IFRS Measures" note
   - Supplementary schedules

3. **Typical Table Format:**
```
Net Income (IFRS)                           $XX,XXX
Add: Fair value adjustments                  XX,XXX
Add: Depreciation                            XX,XXX
Add: Amortization                            XX,XXX
Less: Gains on property sales                (X,XXX)
Add: Deferred taxes                           X,XXX
= Funds From Operations (FFO)               $XX,XXX
Less: Sustaining CAPEX                       (X,XXX)
Less: Leasing costs                          (X,XXX)
Less: Tenant improvements                    (X,XXX)
Add/Less: Straight-line rent adjustment        XXX
= Adjusted FFO (AFFO)                       $XX,XXX
```

---

### EXTRACTION STEPS

#### Step 1: Find Starting Point (Net Income)

**Location:** "Consolidated Statements of Comprehensive Income" or "Statement of Income"

**Extract:** The line showing:
- "Net income (profit or loss)"
- "Net earnings"
- "Profit (loss) for the period"

**Save as:** `net_income_ifrs`

**Example (Artis REIT Q2 2025):**
```
Consolidated Statement of Income and Comprehensive Income
For the three months ended June 30, 2025

Net income (loss)                           $12,345 thousand
```
→ Extract: `net_income_ifrs: 12345`

---

#### Step 2: Extract FFO Adjustments (A-U)

**Extract ALL available adjustments from the reconciliation table:**

| Adjustment | Field Name | Common Labels | Sign Convention |
|------------|------------|---------------|-----------------|
| **A** | `unrealized_fv_changes` | "Fair value adjustments", "Unrealized changes in value of investment properties", "Fair value gains (losses)" | Positive for add-backs, negative for reversals |
| **B** | `depreciation_real_estate` | "Depreciation of real estate assets", "Depreciation of income-producing properties", "Depreciation - properties" | Usually POSITIVE (add back) |
| **C** | `amortization_tenant_allowances` | "Amortization of tenant improvements", "Tenant improvement allowances", "Amortization of lease incentives" | Usually POSITIVE (add back) |
| **D** | `amortization_intangibles` | "Amortization of intangible assets", "Customer relationship intangibles", "Lease intangibles" | Usually POSITIVE (add back) |
| **E** | `gains_losses_property_sales` | "Gains (losses) on sale of properties", "Property disposition gains", "Gain on disposals" | Usually NEGATIVE (subtract gains) or POSITIVE (add back losses) |
| **F** | `tax_on_disposals` | "Tax on property disposals" | Often combined with Adjustment E |
| **G** | `deferred_taxes` | "Deferred income tax expense (recovery)", "Deferred tax provision" | Positive to add back expense, negative to add back recovery |
| **H** | `impairment_losses_reversals` | "Impairment of investment properties", "Impairment reversals", "Write-downs" | Positive for impairments (add back), negative for reversals |
| **I** | `revaluation_gains_losses` | "Revaluation of owner-occupied property" | Rare in REITs - most use fair value model |
| **J** | `transaction_costs_business_comb` | "Transaction costs", "Acquisition costs", "Business combination expenses" | Usually POSITIVE (add back) |
| **K** | `foreign_exchange_gains_losses` | "Foreign exchange gains (losses)", "FX adjustments", "Foreign currency translation" | Positive or negative depending on FX position |
| **L** | `sale_foreign_operations` | "Gain on sale of foreign subsidiary" | Rare event - usually NEGATIVE (subtract gain) |
| **M** | `fv_changes_hedges` | "Fair value changes on derivatives", "Hedge ineffectiveness", "Derivative adjustments" | Positive or negative |
| **N** | `goodwill_impairment` | "Goodwill impairment" | Rare in REITs - usually POSITIVE if present |
| **O** | `puttable_instruments_effects` | "Puttable unit adjustments", "Class B unit adjustments", "LP unit adjustments" | Can be positive or negative |
| **P** | `discontinued_operations` | "Income from discontinued operations", "Discontinued operations adjustment" | NEGATIVE (subtract if income), POSITIVE (add back if loss) |
| **Q** | `equity_accounted_adjustments` | "Share of income from joint ventures", "Equity accounted entities FFO", "JV FFO adjustment" | Complex - may replace JV net income with JV FFO |
| **R** | `incremental_leasing_costs` | "Incremental direct leasing costs" | Usually POSITIVE (add back) - per IFRS 16 |
| **S** | `property_taxes_ifric21` | "Property tax timing adjustment (IFRIC 21)", "Realty tax accrual adjustment" | Timing adjustment - can be positive or negative |
| **T** | `rou_asset_revenue_expense` | "ROU asset revenue", "Ground lease adjustments", "IFRS 16 lease expense" | Can be positive or negative |
| **U** | `non_controlling_interests_ffo` | "Non-controlling interests - FFO", "NCI adjustments", "Minority interest adjustments" | Usually NEGATIVE (deduct NCI's share of FFO adjustments) |

**Note:** Per REALPAC Jan 2022, Adjustment U was enhanced to include NCI adjustments for consolidated entities with puttable units classified as financial liabilities under IAS 32.

---

#### Step 3: Extract AFFO Adjustments (V-Z)

**These are deductions from FFO to arrive at AFFO:**

| Adjustment | Field Name | Common Labels | Sign Convention | Notes |
|------------|------------|---------------|-----------------|-------|
| **V** | `capex_sustaining` | "Sustaining capital expenditures", "Maintenance CAPEX", "Normalized capital expenditures", "Reserve for CAPEX" | **NEGATIVE** (deduction from FFO) | May use actual amounts OR reserve methodology (e.g., "$0.XX per SF") |
| **W** | `leasing_costs` | "Leasing commissions", "Direct leasing costs", "Leasing costs (internal + external)", "Broker commissions" | **NEGATIVE** | Includes both internal and external leasing costs |
| **X** | `tenant_improvements` | "Tenant improvements", "TI costs", "Sustaining tenant improvements", "Tenant allowances paid" | **NEGATIVE** | **CRITICAL:** Do NOT include development TI - only sustaining TI |
| **Y** | `straight_line_rent` | "Straight-line rent adjustment", "IFRS 16 straight-line rent", "Straight-line rent receivable adjustment" | Can be **POSITIVE** or **NEGATIVE** | Adjusts for timing difference between cash and accrual accounting |
| **Z** | `non_controlling_interests_affo` | "Non-controlling interests - AFFO", "NCI - AFFO adjustments" | Usually NEGATIVE | NCI's share of AFFO adjustments |

**CRITICAL CONSISTENCY REQUIREMENT:**
- `capex_sustaining` MUST be the SAME value used in ACFO (Adjustment 4)
- `tenant_improvements` MUST be the SAME value used in ACFO (Adjustment 6)

---

#### Step 4: Record Calculation Method

**Fields:**
- `calculation_method`: Set to "actual", "reserve", or "hybrid"
  - **"actual"** = Issuer uses actual cash amounts for CAPEX/TI/leasing costs
  - **"reserve"** = Issuer uses reserve estimates (e.g., "$0.15 per SF annually")
  - **"hybrid"** = Mix of actual and reserve

- `reserve_methodology`: If reserve used, describe the methodology
  - Example: "3-year rolling average of actual costs"
  - Example: "$0.15 per SF for CAPEX, $0.10 per SF for TI"
  - Example: "Based on historical average over prior 5 years"

- `missing_adjustments`: Array of adjustments you couldn't find
  - Example: `["adjustment_M", "adjustment_N", "adjustment_P"]`
  - Used for transparency and debugging

**Example:**
```json
{
  "calculation_method": "reserve",
  "reserve_methodology": "Sustaining CAPEX: $0.15/SF annually. TI/leasing: 3-year rolling average",
  "missing_adjustments": ["adjustment_M", "adjustment_N"]
}
```

---

#### Step 5: Validate FFO/AFFO Calculation

**Validation Steps:**

1. **Calculate FFO:**
   ```
   FFO = Net Income + Sum(Adjustments A through U)
   ```

2. **Compare to Issuer's Reported FFO:**
   - Extract issuer's reported FFO from `ffo_affo.ffo` section
   - Calculate variance: `Calculated FFO - Reported FFO`
   - Calculate variance %: `(variance / Reported FFO) × 100`

3. **Acceptable Variance:**
   - ✅ < 5% variance = Acceptable (minor rounding or timing differences)
   - ⚠️ 5-10% variance = Review for missing adjustments
   - ❌ > 10% variance = Significant issue - list missing adjustments

4. **Calculate AFFO:**
   ```
   AFFO = FFO + Sum(Adjustments V through Z)
   ```
   Note: V, W, X are typically negative, so this is effectively FFO - V - W - X ± Y - Z

5. **Compare to Issuer's Reported AFFO:**
   - Same process as FFO validation

**Example Validation:**
```json
{
  "validation": {
    "calculated_ffo": 34491,
    "reported_ffo": 34500,
    "ffo_variance_amount": -9,
    "ffo_variance_percent": -0.03,
    "ffo_within_threshold": true,
    "calculated_affo": 16939,
    "reported_affo": 16950,
    "affo_variance_amount": -11,
    "affo_variance_percent": -0.06,
    "affo_within_threshold": true,
    "notes": "Minor rounding differences - validation successful"
  }
}
```

---

## ACFO Components

### Purpose
- Enables calculating ACFO per REALPAC ACFO White Paper (January 2023)
- Measures sustainable economic cash flow from operations
- Generates CFO → ACFO reconciliation table

### When to Extract
**Attempt if:** Issuer reports ACFO OR provides detailed cash flow disclosures

**Note:** Many issuers don't report ACFO - extract what's available

### Where to Find
1. **Cash Flow Statement** - "Consolidated Statements of Cash Flows"
2. **MD&A** - Search for:
   - "Adjusted Cash Flow from Operations (ACFO)"
   - "Economic Cash Flow"
   - "Sustainable Operating Cash Flow"
3. **Notes** - "Non-IFRS Measures" or "Supplementary Cash Flow Information"

---

### EXTRACTION STEPS

#### Step 1: Find Starting Point (CFO)

**Location:** "Consolidated Statements of Cash Flows"

**Extract:** The line showing:
- "Cash provided by (used in) operating activities"
- "Net cash from operations"
- "Cash flows from operating activities"

**Save as:** `cash_flow_from_operations`

**Example:**
```
Consolidated Statement of Cash Flows
For the six months ended June 30, 2025

OPERATING ACTIVITIES
Net income                                  $12,345
  Adjustments to reconcile net income...
  Changes in working capital...             (2,500)
Net cash from operating activities          $45,000 ← Extract this
```
→ Extract: `cash_flow_from_operations: 45000`

---

#### Step 2: Extract ACFO Adjustments (1-17)

| Adj # | Field Name | Common Labels | Sign | Notes |
|-------|------------|---------------|------|-------|
| **1** | `change_in_working_capital` | "Change in non-cash working capital", "Working capital adjustments" | Use **OPPOSITE** sign | Purpose: Eliminate non-sustainable working capital fluctuations. If CFO already includes +$2M working capital increase, use -$2M here to normalize |
| **2** | `interest_financing` | "Interest paid" (in financing section) | **POSITIVE** | Add back if interest is shown in financing activities instead of operations |
| **3a** | `jv_distributions` | "Distributions from joint ventures", "Distributions received from equity accounted entities" | **POSITIVE** | Option 1: Use actual JV distributions received |
| **3b** | `jv_acfo` | "ACFO from joint ventures", "Proportionate ACFO from JVs" | **POSITIVE** | Option 2: Use calculated ACFO from JVs (more complex, rarely disclosed) |
| **3c** | `jv_notional_interest` | "Notional interest on JV development" | **POSITIVE** | Rare - add back notional interest that would have been capitalized |
| **4** | `capex_sustaining_acfo` | "Sustaining capital expenditures", "Maintenance CAPEX" | **NEGATIVE** | ⚠️ MUST match `capex_sustaining` from FFO/AFFO (Adjustment V) |
| **4_dev** | `capex_development_acfo` | "Development capital expenditures", "Growth CAPEX" | Disclosure only | Not deducted from ACFO - disclosed separately |
| **5** | `leasing_costs_external` | "External leasing costs", "Broker leasing commissions" | **NEGATIVE** | Only external costs - internal leasing costs already in operations |
| **6** | `tenant_improvements_acfo` | "Sustaining tenant improvements", "TI expenditures" | **NEGATIVE** | ⚠️ MUST match `tenant_improvements` from FFO/AFFO (Adjustment X) |
| **7** | `realized_investment_gains_losses` | "Realized gains on marketable securities" | **NEGATIVE** (if gain) | Remove non-operating investment gains/losses |
| **8** | `taxes_non_operating` | "Taxes on property disposals", "Non-operating tax items" | Adjust accordingly | Taxes related to non-operating items (e.g., disposal taxes) |
| **9** | `transaction_costs_acquisitions` | "Acquisition transaction costs", "Due diligence costs" | **POSITIVE** | Add back one-time acquisition costs |
| **10** | `transaction_costs_disposals` | "Disposition transaction costs", "Selling costs" | **POSITIVE** | Add back one-time disposition costs |
| **11** | `deferred_financing_fees` | "Amortization of deferred financing costs" | **POSITIVE** | Add back non-cash amortization |
| **12** | `debt_termination_costs` | "Loss on debt extinguishment", "Prepayment penalties", "Debt breakage costs" | **POSITIVE** | Add back one-time refinancing costs |
| **13a** | `off_market_debt_favorable` | "Favorable off-market debt adjustments", "Below-market debt" | Adjust accordingly | Amortization of favorable acquired debt |
| **13b** | `off_market_debt_unfavorable` | "Unfavorable off-market debt adjustments", "Above-market debt" | Adjust accordingly | Amortization of unfavorable acquired debt |
| **14a** | `interest_income_timing` | "Interest income accrual adjustments" | Adjust accordingly | Cash vs accrual timing differences |
| **14b** | `interest_expense_timing` | "Interest expense accrual adjustments" | Adjust accordingly | Cash vs accrual timing differences |
| **15** | `puttable_instruments_distributions` | "Distributions on Class B units", "LP unit distributions" | Adjust accordingly | When puttable units treated as debt (IAS 32) |
| **16a** | `rou_sublease_principal_received` | "Principal portion of sublease payments received" | **POSITIVE** | Finance lease income - principal portion |
| **16b** | `rou_sublease_interest_received` | "Interest portion of sublease payments received" | **POSITIVE** | Finance lease income - interest portion |
| **16c** | `rou_lease_principal_paid` | "Principal portion of ground lease payments" | **NEGATIVE** | Ground lease payments - principal portion |
| **16d** | `rou_depreciation_amortization` | "Depreciation on ROU assets" | **POSITIVE** | Add back if using cost model for ROU assets |
| **17a** | `non_controlling_interests_acfo` | "NCI in respect of ACFO adjustments" | **NEGATIVE** | NCI's proportionate share of all above adjustments |
| **17b** | `nci_puttable_units` | "NCI for puttable units" | **NEGATIVE** | NCI for consolidated entities with puttable units as liabilities (IAS 32) |

---

#### Step 3: Consistency Checks (CRITICAL)

**ACFO must be consistent with AFFO for these items:**

1. **Sustaining CAPEX:**
   ```
   capex_sustaining_acfo == ffo_affo_components.capex_sustaining
   ```
   - If different, investigate which source is more reliable
   - Use the same value in both sections

2. **Tenant Improvements:**
   ```
   tenant_improvements_acfo == ffo_affo_components.tenant_improvements
   ```
   - Must be identical
   - Ensures ACFO and AFFO are reconcilable

3. **Methodology:**
   - Set `calculation_method_acfo` to match `calculation_method` from FFO/AFFO
   - If using reserve methodology, should be the same reserves

**Example Consistency Check:**
```json
{
  "ffo_affo_components": {
    "capex_sustaining": -12000,
    "tenant_improvements": -8000,
    "calculation_method": "reserve"
  },
  "acfo_components": {
    "capex_sustaining_acfo": -12000,    // ✓ MATCHES
    "tenant_improvements_acfo": -8000,   // ✓ MATCHES
    "calculation_method_acfo": "reserve" // ✓ MATCHES
  }
}
```

---

#### Step 4: JV Treatment Method

**Choose ONE of two methods for joint ventures:**

**Option 1: Distributions Method (more common)**
- Extract: `jv_distributions` (Adjustment 3a)
- Set: `jv_treatment_method: "distributions"`
- Use: Actual distributions received from JVs

**Option 2: ACFO Method (more accurate but complex)**
- Extract: `jv_acfo` (Adjustment 3b)
- Set: `jv_treatment_method: "acfo"`
- Use: Proportionate share of JV's calculated ACFO

**Example:**
```json
{
  "acfo_components": {
    "jv_distributions": 5000,
    "jv_acfo": null,
    "jv_treatment_method": "distributions"
  }
}
```

---

#### Step 5: Missing Adjustments

**Reality Check:** Most issuers don't disclose all 17 ACFO adjustments

**Best Practice:**
- Extract what's available
- List unavailable adjustments in `missing_adjustments_acfo`
- Phase 3 will work with partial data

**Example:**
```json
{
  "acfo_components": {
    "cash_flow_from_operations": 45000,
    "change_in_working_capital": -2500,
    "capex_sustaining_acfo": -12000,
    "tenant_improvements_acfo": -8000,
    "leasing_costs_external": -2000,
    // ... (other available adjustments)
    "missing_adjustments_acfo": [
      "adjustment_7_realized_investment_gains_losses",
      "adjustment_11_deferred_financing_fees",
      "adjustment_16_rou_adjustments"
    ],
    "calculation_method_acfo": "actual",
    "jv_treatment_method": "distributions"
  }
}
```

---

## Cash Flow Sections

### Cash Flow from Investing Activities

**Purpose:** Required for AFCF (Adjusted Free Cash Flow) calculation

**Location:** "Consolidated Statements of Cash Flows" - Investing Activities section

**Extract:**
| Field | Label | Sign | Notes |
|-------|-------|------|-------|
| `development_capex` | "Additions to investment properties", "Development expenditures" | **NEGATIVE** | Growth CAPEX only. Should match `capex_development_acfo` if available |
| `property_acquisitions` | "Acquisition of investment properties", "Purchase of real estate" | **NEGATIVE** | Cash paid for acquisitions |
| `property_dispositions` | "Proceeds from sale of investment properties", "Disposition proceeds" | **POSITIVE** | Cash received from sales |
| `jv_capital_contributions` | "Investment in equity accounted entities", "Contributions to joint ventures" | **NEGATIVE** | Capital invested in JVs |
| `jv_return_of_capital` | "Distribution from equity accounted entities", "Return of capital from JVs" | **POSITIVE** | Return of capital from JV exits |
| `business_combinations` | "Acquisition of subsidiaries", "Business combinations" | **NEGATIVE** | Acquiring entire entities |
| `other_investing_outflows` | Other investing outflows not categorized | **NEGATIVE** | Miscellaneous |
| `other_investing_inflows` | Other investing inflows not categorized | **POSITIVE** | Miscellaneous |
| `total_cfi` | "Net cash used in investing activities" | Usually NEGATIVE | For reconciliation |

**IMPORTANT:** Do NOT include sustaining CAPEX here - that's already in ACFO components

---

### Cash Flow from Financing Activities

**Purpose:** Required for AFCF coverage analysis and burn rate calculations

**Location:** "Consolidated Statements of Cash Flows" - Financing Activities section

**Extract:**
| Field | Label | Sign | Notes |
|-------|-------|------|-------|
| `debt_principal_repayments` | "Repayment of mortgages", "Principal payments on debt" | **NEGATIVE** | All principal repayments |
| `new_debt_issuances` | "Proceeds from mortgages", "Issuance of debentures" | **POSITIVE** | New debt proceeds |
| `distributions_common` | "Distributions to unitholders", "Dividends paid" | **NEGATIVE** | Common unit distributions |
| `distributions_preferred` | "Distributions on preferred units" | **NEGATIVE** | Preferred distributions (if separate line) |
| `distributions_nci` | "Distributions to non-controlling interests" | **NEGATIVE** | NCI distributions (if separate line) |
| `equity_issuances` | "Issuance of units", "Proceeds from equity" | **POSITIVE** | New equity proceeds |
| `unit_buybacks` | "Repurchase of units", "Unit buyback" | **NEGATIVE** | Buybacks |
| `deferred_financing_costs_paid` | "Deferred financing costs paid" | **NEGATIVE** | Upfront financing fees |
| `other_financing_outflows` | Other financing outflows | **NEGATIVE** | Miscellaneous |
| `other_financing_inflows` | Other financing inflows | **POSITIVE** | Miscellaneous |
| `total_cff` | "Net cash from (used in) financing activities" | Can be either | For reconciliation |

**Note:** Some statements combine all distributions into one line - extract as `distributions_common`

---

## Liquidity Extraction

### Purpose
Required for burn rate and cash runway analysis

### Location
1. **Balance Sheet** - Current assets section
2. **Notes** - "Credit Facilities" note (often Note 11-15)
3. **MD&A** - "Liquidity and Capital Resources" section

### Extract:
| Field | Source | Calculation |
|-------|--------|-------------|
| `cash_and_equivalents` | Balance sheet | Should match `balance_sheet.cash` |
| `marketable_securities` | Balance sheet - Current assets | Short-term investments (0 if not disclosed) |
| `restricted_cash` | Balance sheet notes | Cash not available for operations (0 if none) |
| `credit_facility_limit` | Notes - Credit Facilities | **Total limit across ALL facilities** |
| `undrawn_credit_facilities` | Notes - Credit Facilities | **Sum of undrawn across ALL facilities** (see below) |
| `available_cash` | Calculated | `cash_and_equivalents + marketable_securities - restricted_cash` |
| `total_available_liquidity` | Calculated | `available_cash + undrawn_credit_facilities` |
| `data_source` | Text | Note the source (e.g., "balance sheet + note 12") |

### Handling Multiple Credit Facilities

**IMPORTANT:** Many REITs have multiple credit facilities (e.g., revolving + non-revolving, or multiple tranches).

#### Where to Look for Credit Facility Information (Priority Order)

**🔍 Search these locations in order until you find complete information:**

1. **MD&A "Credit Facilities" or "Liquidity" section** (MOST AUTHORITATIVE)
   - Usually includes current facility limits, drawn amounts, and available capacity
   - May include borrowing base limitations
   - Example: "At June 30, 2025, the REIT had $78,400 available on its revolving term credit facilities"

2. **Financial Statement Notes** (e.g., Note 10 - Credit Facilities)
   - Detailed terms, covenants, and facility descriptions
   - May show historical balances and limits

3. **Balance Sheet line items**
   - Shows total drawn amount but rarely shows limits or available capacity
   - Can be used to verify drawn amounts from other sources

4. **Subsequent Events notes**
   - May reference facility amendments or renewals
   - ⚠️ May reference future/planned limits, not current limits
   - Always verify against current period MD&A

#### If Multiple Facilities Exist:

1. **Identify each facility separately** (revolving, non-revolving, term loans, etc.)
2. **Find the limit for EACH facility** (not just total)
3. **Find the drawn amount for EACH facility**
4. **Calculate undrawn for each:** `facility_limit - facility_drawn`
5. **Sum all undrawn amounts** for total undrawn capacity

#### Handling Conflicting Information

**If you find conflicting facility limits (e.g., $275M in one place, $350M in another):**

1. **Prioritize MD&A credit facilities section** - this is the most current, detailed source
2. **Check dates** - subsequent events may reference future amendments, not current limits
3. **Look for "available" or "undrawn" disclosures** - these are often stated directly
4. **DO NOT make conservative assumptions** - if something looks wrong, search more thoroughly

**⚠️ WARNING - Borrowing Base vs Facility Limit:**

Many secured credit facilities have BOTH:
- **Facility Limit**: Maximum committed amount (e.g., $350M)
- **Borrowing Base**: Current capacity based on secured property values (e.g., $514M)

The **facility limit** is what matters for undrawn capacity calculation.

**Example - When something appears wrong:**
```
❌ WRONG APPROACH:
"Balance sheet shows $437.6M drawn, but I found a $275M limit reference.
Facility appears overdrawn. Conservative estimate: $0 undrawn."

✓ CORRECT APPROACH:
"Balance sheet shows $437.6M drawn. Found $275M in subsequent events.
This seems inconsistent - let me check MD&A credit facilities section...
Found: MD&A page 36 states $350M revolving facility with $78.4M available.
The $437.6M includes both revolving ($271.6M) and non-revolving ($170M) facilities."
```

#### Example - Artis REIT Q2 2025 (CORRECT EXTRACTION)

**Source hierarchy used:**
1. ✓ MD&A page 36: "The REIT has a secured revolving term credit facility in the amount of $350,000... At June 30, 2025, the REIT had $78,400 available"
2. ✓ Notes: "As at June 30, 2025, there was $271,600 drawn on the revolving credit facility and $170,000 drawn on the non-revolving credit facility"
3. ⚠️ Subsequent events: Mentioned "$275,000 limit" - this was either outdated or referred to a different facility component

**Calculation:**
```
Revolving facility:
  Limit: $350,000 (from MD&A page 36)
  Drawn: $271,600 (from notes)
  Available: $78,400 (directly stated in MD&A, or calculated: 350,000 - 271,600)

Non-revolving facility:
  Limit: Not disclosed (assume fully drawn)
  Drawn: $170,000 (from notes)
  Available: $0 (assume fully drawn)

Total:
  Total facility limit: $350,000 + $170,000 = $520,000
  Total drawn: $271,600 + $170,000 = $441,600
  Total undrawn: $78,400
```

**Common patterns:**
- "Revolving credit facility" + "Non-revolving credit facility"
- "Tranche A" + "Tranche B"
- "Secured facility" + "Unsecured facility"
- "Term loan" + "Revolver"

**If limit not disclosed for a facility:**
- If fully drawn, assume limit = drawn amount (undrawn = $0)
- Note this assumption in `data_source`

**Example JSON (Artis REIT - Correct):**
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
    "data_source": "Q2 2025 MD&A page 36. Revolving facility $350M, $271.6M drawn, $78.4M available. Non-revolving facility $170M drawn (assumed fully drawn)."
  }
}
```

**Example (Single Facility):**
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
    "data_source": "Balance sheet + note 12. Revolving facility $200M limit, $50M drawn."
  }
}
```

---

## Dilution Extraction

### Purpose
Optional - enables dilution materiality assessment and governance scoring

### When to Extract
When issuer provides detailed dilution calculation in MD&A

### Where to Find
Look for sections titled:
- "Weighted Average Number of Units"
- "Diluted Units Outstanding"
- "Share/Unit Count Reconciliation"

**Example (Artis REIT Q2 2025 MD&A page 21):**
```
Weighted Average Units Outstanding Calculation
Basic units outstanding                     99,444,000
Add: Restricted units                        1,500,000
Add: Deferred units                            500,000
Diluted units outstanding                  101,444,000
```

### Extract:
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
    "reconciliation_note": "Calculated matches reported - no anti-dilutive exclusions",
    "disclosure_source": "Q2 2025 MD&A page 21"
  }
}
```

---

## Summary Checklist

### Before Starting Extraction

- [ ] Read all input files using Read tool
- [ ] Identify MD&A vs Financial Statements vs Notes
- [ ] Locate key sections: FFO/AFFO reconciliation, Cash Flow Statement, Notes

### During Extraction

- [ ] **FFO/AFFO Components:** Extract 26 adjustments (A-U + V-Z)
- [ ] **ACFO Components:** Extract 17 adjustments (1-17) if available
- [ ] **Cash Flow Investing:** Extract 8 components + total
- [ ] **Cash Flow Financing:** Extract 10 components + total
- [ ] **Liquidity:** Extract 7 components
- [ ] **Dilution:** Extract if detailed breakdown available

### After Extraction

- [ ] Validate FFO/AFFO calculations against issuer-reported values
- [ ] Check ACFO consistency (CAPEX and TI must match AFFO)
- [ ] Verify sign conventions (NEGATIVE for outflows, POSITIVE for inflows)
- [ ] List missing adjustments in appropriate arrays
- [ ] Run schema validation: `python scripts/validate_extraction_schema.py <output_file>`

---

## Token Impact

**Estimated token increase from comprehensive extraction:**
- Basic extraction (current): ~1,000 tokens
- + FFO/AFFO components: +1,500 tokens
- + ACFO components: +800 tokens
- + Cash flow sections: +500 tokens
- + Liquidity: +200 tokens
- + Dilution: +150 tokens (optional)
- **Total: ~4,150 tokens** (still well within budget)

**Benefit:**
- Unlocks FFO/AFFO/ACFO reconciliation tables
- Enables AFCF and burn rate calculations
- Provides validation against issuer-reported values
- Generates 90% more populated template placeholders

---

**END OF COMPREHENSIVE EXTRACTION GUIDE**
