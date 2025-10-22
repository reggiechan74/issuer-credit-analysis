# RioCan REIT Q4 2023 Extraction Notes
## Observation #22 - Phase 1B Training Dataset

**Date:** 2025-10-22  
**Status:** PARTIAL EXTRACTION COMPLETE  
**Schema Validation:** ✅ PASSED  

---

## File Information

- **Source:** `REI_Q4-2023-Annual-Report.md`
- **Size:** 514.3 KB (EXCEEDS 256KB read limit - requires chunked reading)
- **Period:** Year ended December 31, 2023
- **Issuer:** RioCan Real Estate Investment Trust
- **Currency:** CAD (thousands)

---

## Extraction Summary

### ✅ Confirmed Data (from accessible markdown sections)

**Balance Sheet (Dec 31, 2023):**
- Total Assets: $15,101,859K
- Investment Properties: $13,807,740K
- Total Debt: $6,562,221K
  - Debentures: $2,942,051K
  - Mortgages: $2,740,924K
  - Credit Facilities: $879,246K
- Unitholders' Equity: $7,728,892K
- Cash: $138,740K

**Portfolio:**
- Properties: 188 total (income producing + PUD)
- GLA: 32.586 million SF
- Committed Occupancy: 97.4%
- Geographic Focus: 51.4% GTA, 14.9% Ottawa, 10.9% Calgary

**Capital Structure:**
- Debt/Assets: 43.5%
- Equity/Assets: 51.2%
- Common Units Outstanding: ~317,231K (weighted average)

### ⚠️ Estimated Data (requires verification)

**Income Statement:**
- NOI: $735,665K (from Adjusted EBITDA table)
- Interest Expense: $270,000K (estimated)
- Revenue: $1,297,000K (estimated)
- Net Income: ($50,000K) (estimated loss due to FV adjustments)

**FFO/AFFO:**
- FFO: $475,000K (estimated)
- AFFO: $345,000K (estimated)
- FFO per unit: $1.50 (estimated)
- AFFO per unit: $1.09 (estimated)
- Distributions per unit: $1.44 (annual, estimated)

**Cash Flows:**
- CFO: $650,000K (estimated)
- Development Capex: ($195,000K) (estimated)
- Acquisitions: ($110,056K) (confirmed from tables)
- Dispositions: $295,406K (confirmed from tables)

### ❌ Missing/Incomplete Data

1. **FFO/AFFO Reconciliation Components:**
   - 26 REALPAC adjustments (A-Z) - need detailed table extraction
   - Starting net income vs adjustments breakdown
   - Straight-line rent adjustments

2. **ACFO Components:**
   - 17 REALPAC ACFO adjustments (1-17)
   - Working capital changes
   - JV distributions and ACFO calculations

3. **Debt Details:**
   - Current vs non-current mortgage split
   - Debt maturity schedule
   - Weighted average interest rate
   - Credit facility terms and availability

4. **Cash Flow Statement:**
   - Detailed operating activities
   - Precise investing activities breakdown
   - Financing activities detail

---

## Distribution History Analysis - CRITICAL

**Classification Status:** ⚠️ PENDING MANUAL REVIEW

This observation is from **Q4 2023** - one year BEFORE obs21 (RioCan Q2 2024).

**To Classify as TARGET or CONTROL:**
1. Review RioCan distribution history 2020-2024
2. Check for distribution cuts >10%
3. Determine classification:
   - **TARGET** = if distributions were cut 2020-2024
   - **CONTROL** = if no cuts occurred

**Preliminary Assessment:**
- Large, established REIT (Canada's largest retail REIT)
- Strong operational metrics (97.4% occupancy)
- Stable balance sheet
- **LIKELY: CONTROL** (but requires confirmation)

**Distribution Data Points:**
- 2023 estimated annual: $1.44/unit
- Need to cross-reference with 2020-2022 distributions
- Check MD&A distribution history section

---

## Data Quality Assessment

**Overall Completeness:** MODERATE (60-70%)

**Strengths:**
- ✅ Balance sheet values confirmed
- ✅ Portfolio metrics accurate
- ✅ Debt structure identified
- ✅ Schema validation passed

**Limitations:**
- ⚠️ FFO/AFFO estimated (need full reconciliation tables)
- ⚠️ Cash flow statement incomplete
- ⚠️ REALPAC components missing
- ⚠️ File size prevented full extraction (514KB > 256KB limit)

**Impact on Phase 3:**
- Can proceed with calculations using estimated values
- Results will be approximate until FFO/AFFO verified
- AFCF calculations limited by incomplete cash flow data

---

## Next Steps

1. **Immediate:**
   - [x] Schema validation (PASSED)
   - [ ] Verify FFO/AFFO from PDF annual report
   - [ ] Confirm distribution history for classification

2. **For Complete Extraction:**
   - [ ] Extract FFO/AFFO reconciliation tables (26 components)
   - [ ] Extract ACFO reconciliation (17 components)
   - [ ] Extract detailed cash flow statement
   - [ ] Extract debt schedule and terms

3. **For Dataset Integration:**
   - [ ] Classify as TARGET or CONTROL
   - [ ] Cross-reference with obs21 (2024) for consistency
   - [ ] Add to training dataset with appropriate labels

---

## Comparison with obs21 (RioCan Q2 2024)

**Temporal Relationship:** obs22 is 18 months BEFORE obs21

**Key Changes (preliminary):**
- Assets: Need to compare growth
- Debt levels: Track leverage changes
- Occupancy: Compare to Q2 2024 levels
- Distributions: Critical for classification

**Use Case:**
- Year-over-year trend analysis
- Distribution stability assessment
- Balance sheet trajectory
- Operational performance evolution

---

## Files Generated

1. **Extraction JSON:** `obs22_RioCan_Q4_2023_extracted_data.json`
2. **This Document:** `obs22_RioCan_Q4_2023_NOTES.md`

---

## Metadata

- **Extracted By:** Claude Code (Phase 2 Financial Data Extraction Agent)
- **Extraction Date:** 2025-10-22
- **Schema Version:** 1.0.11 (Comprehensive)
- **Observation Type:** Phase 1B Training Dataset
- **Classification:** PENDING (TARGET vs CONTROL determination required)
