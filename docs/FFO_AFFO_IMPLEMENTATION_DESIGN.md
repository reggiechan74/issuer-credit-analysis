# FFO/AFFO Calculation Implementation Design

**Issue**: #4 - Implement AFFO Calculation When Issuer Does Not Provide It
**Date**: 2025-10-20
**Reference**: REALPAC White Paper on FFO & AFFO for IFRS (February 2019)

## Overview

Implement automated FFO and AFFO calculations following REALPAC methodology when issuers don't report these metrics in their financial statements.

## Methodology Summary

### FFO Calculation (IFRS P&L → FFO)

**Formula:**
```
FFO = IFRS Net Income
  + Adjustments A-U (add back non-cash/non-recurring items)
  - Non-controlling interests (adjustment U)
```

**Adjustments (A-U):**
- **A**: Unrealized fair value changes (investment properties)
- **B**: Depreciation (depreciable real estate assets)
- **C**: Amortization (tenant allowances for fit-out)
- **D**: Amortization (tenant/customer relationship intangibles)
- **E**: Gains/losses from property sales
- **F**: Tax on property disposals
- **G**: Deferred taxes
- **H**: Impairment losses/reversals (real estate)
- **I**: Revaluation gains/losses (owner-occupied properties)
- **J**: Transaction costs (business combinations)
- **K**: Foreign exchange gains/losses
- **L**: Gain/loss on sale of foreign operations
- **M**: Fair value changes (economically effective hedges)
- **N**: Goodwill impairment/negative goodwill
- **O**: Effects of puttable instruments
- **P**: Discontinued operations results
- **Q**: Equity accounted entities adjustments
- **R**: Incremental leasing costs
- **S**: Property taxes (IFRIC 21)
- **T**: Right of Use Asset revenue/expenses (IFRS 16)
- **U**: Non-controlling interests

### AFFO Calculation (FFO → AFFO)

**Formula:**
```
AFFO = FFO
  - Sustaining CAPEX (V)
  - Leasing Costs (W)
  - Tenant Improvements (X)
  - Straight-Line Rent (Y)
  - Non-controlling interests (Z)
```

**Adjustments (V-Z):**
- **V**: Capital Expenditures - sustaining/maintenance only (exclude development)
- **W**: Leasing Costs - internal + external (exclude development-related)
- **X**: Tenant Improvements - sustaining costs only
- **Y**: Straight-Line Rent - adjustment to contractual/receivable basis
- **Z**: Non-controlling Interests - attributable to parent

## Data Requirements

### Phase 2 Extraction Schema Updates

Add new section: `ffo_affo_components` with subsections:

```json
{
  "ffo_affo_components": {
    "net_income_ifrs": number,

    // FFO Adjustments (A-U)
    "unrealized_fv_changes": number,
    "depreciation_real_estate": number,
    "amortization_tenant_allowances": number,
    "amortization_intangibles": number,
    "gains_losses_property_sales": number,
    "tax_on_disposals": number,
    "deferred_taxes": number,
    "impairment_losses_reversals": number,
    "revaluation_gains_losses": number,
    "transaction_costs_business_comb": number,
    "foreign_exchange_gains_losses": number,
    "sale_foreign_operations": number,
    "fv_changes_hedges": number,
    "goodwill_impairment": number,
    "puttable_instruments_effects": number,
    "discontinued_operations": number,
    "equity_accounted_adjustments": number,
    "incremental_leasing_costs": number,
    "property_taxes_ifric21": number,
    "rou_asset_revenue_expense": number,
    "non_controlling_interests_ffo": number,

    // AFFO Adjustments (V-Z)
    "capex_sustaining": number,
    "capex_development": number,  // for disclosure only
    "leasing_costs": number,
    "tenant_improvements": number,
    "straight_line_rent": number,
    "non_controlling_interests_affo": number,

    // Metadata
    "calculation_method": "actual | reserve | hybrid",
    "reserve_methodology": "string (if reserve used)",
    "missing_adjustments": ["array of missing items"]
  }
}
```

### Existing Schema Fields to Use

From `income_statement`:
- `net_income` - IFRS net income starting point

From `ffo_affo` (existing):
- `ffo` - issuer-reported FFO (for validation)
- `affo` - issuer-reported AFFO (for validation)
- `ffo_per_unit` - for payout ratio calculations
- `affo_per_unit` - for payout ratio calculations

## Implementation Approach

### Option: Enhance Phase 3 (Recommended)

Integrate into `scripts/calculate_credit_metrics.py` as new function:

```python
def calculate_ffo_from_components(financial_data):
    """
    Calculate FFO from IFRS net income using REALPAC methodology (A-U adjustments)

    Returns:
        dict: {
            'ffo_calculated': float,
            'adjustments': dict,  # A-U breakdown
            'missing_components': list,  # flags for incomplete data
        }
    """
    pass

def calculate_affo_from_ffo(financial_data, ffo):
    """
    Calculate AFFO from FFO using REALPAC methodology (V-Z adjustments)

    Returns:
        dict: {
            'affo_calculated': float,
            'adjustments': dict,  # V-Z breakdown
            'missing_components': list,
        }
    """
    pass

def validate_ffo_affo(calculated, reported):
    """
    Compare calculated vs. reported FFO/AFFO

    Returns:
        dict: {
            'variance_amount': float,
            'variance_percent': float,
            'within_threshold': bool,  # <5% is acceptable
            'reconciliation_notes': str
        }
    """
    pass

def generate_reconciliation_table(financial_data):
    """
    Generate IFRS P&L → FFO → AFFO reconciliation table

    Returns:
        dict: Complete reconciliation with line items
    """
    pass
```

## Validation Strategy

### When Issuer Provides FFO/AFFO

1. Calculate using available components
2. Compare calculated vs. reported
3. Flag discrepancies > 5%
4. Document methodology differences

### When Issuer Doesn't Provide FFO/AFFO

1. Calculate from available components
2. Flag missing data points
3. Document assumptions
4. Calculate "best-effort" AFFO

## Output Structure (Phase 3)

```json
{
  "issuer_name": "...",
  "reporting_date": "...",

  "ffo_affo_analysis": {
    "issuer_reported": {
      "ffo": number | null,
      "affo": number | null,
      "ffo_per_unit": number | null,
      "affo_per_unit": number | null
    },

    "calculated": {
      "ffo": number,
      "affo": number,
      "ffo_per_unit": number,
      "affo_per_unit": number
    },

    "validation": {
      "ffo_variance_percent": number | null,
      "affo_variance_percent": number | null,
      "within_acceptable_range": boolean,
      "notes": "string"
    },

    "reconciliation": {
      "ifrs_net_income": number,
      "ffo_adjustments": {
        "adjustment_a_unrealized_fv": number,
        "adjustment_b_depreciation": number,
        // ... A-U
        "total_adjustments": number
      },
      "ffo_total": number,
      "affo_adjustments": {
        "adjustment_v_capex": number,
        "adjustment_w_leasing": number,
        "adjustment_x_tenant_imp": number,
        "adjustment_y_straight_line": number,
        "adjustment_z_nci": number,
        "total_adjustments": number
      },
      "affo_total": number
    },

    "data_quality": {
      "completeness": "strong | moderate | limited",
      "missing_components": ["list of missing items"],
      "assumptions_made": ["list of assumptions"]
    },

    "distribution_coverage": {
      "ffo_payout_ratio": number,
      "affo_payout_ratio": number,
      "sustainability_assessment": "string"
    }
  }
}
```

## Disclosure Requirements

Per REALPAC guidelines, the system should generate:

1. **Methodology Disclosure**: Which adjustments were made
2. **Data Sources**: Where each component came from
3. **Assumptions**: Any estimations or missing data handling
4. **Comparison**: Calculated vs. reported (when available)
5. **Reconciliation Table**: Complete IFRS → FFO → AFFO breakdown

## Best Practices Implementation

### Capital Expenditures (V)
- **Preferred**: Use actual amounts
- **Alternative**: Use reserve (e.g., 3-year rolling average)
- **Required**: If reserve used, disclose calculation and reconcile to actuals

### Leasing Costs (W)
- Include both internal and external costs
- Exclude development-related costs

### Data Availability Handling
- Flag missing adjustments
- Calculate "best-effort" FFO/AFFO
- Document limitations clearly

## Testing Strategy

### Unit Tests

```python
def test_calculate_ffo_complete_data():
    """Test FFO calculation with all components available"""

def test_calculate_ffo_missing_components():
    """Test FFO calculation with some missing data"""

def test_calculate_affo_from_ffo():
    """Test AFFO calculation from FFO"""

def test_validation_within_threshold():
    """Test validation when calculated vs reported < 5% variance"""

def test_validation_outside_threshold():
    """Test validation when calculated vs reported > 5% variance"""

def test_reconciliation_table_generation():
    """Test complete reconciliation table"""
```

### Integration Tests

Use actual issuer data (e.g., Artis REIT Q2 2025) to:
1. Extract components from financial statements
2. Calculate FFO/AFFO
3. Compare to reported values
4. Validate reconciliation

## Implementation Phases

### Phase 1: Core FFO Calculation ✓
- Implement `calculate_ffo_from_components()`
- Handle A-U adjustments
- Basic validation

### Phase 2: AFFO Calculation ✓
- Implement `calculate_affo_from_ffo()`
- Handle V-Z adjustments
- Sustaining vs. development CAPEX logic

### Phase 3: Validation & Reconciliation ✓
- Implement `validate_ffo_affo()`
- Implement `generate_reconciliation_table()`
- Variance analysis

### Phase 4: Integration ✓
- Update Phase 2 extraction schema
- Update Phase 3 metrics calculation
- Update Phase 4 credit analysis prompts
- Update Phase 5 report template

### Phase 5: Testing & Documentation ✓
- Comprehensive unit tests
- Integration tests with real data
- Update CLAUDE.md
- Update README.md

## Success Criteria (from Issue #4)

- [x] Calculate FFO from IFRS profit/loss for all ~20 adjustments (A-U)
- [x] Calculate AFFO from FFO with V-Z adjustments
- [ ] Validate against issuer-reported AFFO (when available) with <5% variance
- [ ] Generate clear reconciliation table (IFRS P&L → FFO → AFFO)
- [ ] Document all assumptions and data sources
- [ ] Add to Phase 3 credit metrics output
- [ ] Include in final credit opinion report

## Related Metrics

This implementation enables calculation of:
- **FFO/Share**: FFO ÷ diluted shares outstanding
- **AFFO/Share**: AFFO ÷ diluted shares outstanding
- **FFO Payout Ratio**: Distributions ÷ FFO
- **AFFO Payout Ratio**: Distributions ÷ AFFO (sustainability metric)
- **AFFO Yield**: AFFO per share ÷ unit price

## References

- REALPAC White Paper on FFO & AFFO for IFRS (February 2019)
- Issue #4: Implement AFFO Calculation When Issuer Does Not Provide It
- `docs/realpac_whitepaper_on_ffoaff-szb5kf.pdf`
- REALPAC ACFO White Paper (January 2023) - for cash flow variant

---

**Next Steps:**
1. Update Phase 2 extraction schema
2. Implement calculation functions in Phase 3
3. Write comprehensive tests
4. Update documentation and templates
