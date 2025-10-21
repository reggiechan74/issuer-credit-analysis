# Burn Rate and Cash Flow Analysis - Documentation Index

**Complete Technical Documentation Package (v1.0.7+)**

---

## Overview

This directory contains comprehensive documentation for the burn rate and cash flow analysis implementation, including technical specifications, schema references, and implementation details.

---

## Documents

### 1. BURN_RATE_ANALYSIS_REPORT.md (27 KB, 873 lines)

**Purpose:** Comprehensive technical analysis and architecture documentation

**Contents:**
- Executive Summary
- Burn Rate Calculation Implementation (detailed algorithm)
- Cash Runway Analysis (runway calculation and risk assessment)
- Sustainable Burn Rate Analysis
- Complete Data Flow Diagram (Phase 2 → 3 → 5)
- Current Metrics Output (JSON schema examples)
- Phase 5 Template Integration (placeholder mapping)
- Testing & Validation (unit and integration tests)
- Recommended Integration Points for Distribution Cut Prediction
- Code Locations Summary (file paths and line numbers)
- Critical Insights for Distribution Cut Prediction
- Summary and Conclusion

**Best For:**
- Understanding the complete architecture
- Learning how burn rate feeds into credit analysis
- Designing distribution cut prediction module
- Reference guide for credit committee

**Key Sections:**
1. Core function signatures and algorithms
2. Data flow from Phase 2 extraction → Phase 3 calculations → Phase 5 reports
3. Real-world example calculations
4. Testing strategies

---

### 2. BURN_RATE_SCHEMA_REFERENCE.md (17 KB, 544 lines)

**Purpose:** Quick reference guide for schema, inputs, outputs, and testing

**Contents:**
- Phase 2 Extraction Schema (input data requirements)
- Phase 3 Output Schema (calculated metrics JSON)
- Data Flow Reference (calculation sequence)
- Distribution Cut Prediction Integration Points
- Testing Reference (test fixtures and scenarios)
- Validation Checklist
- Common Integration Scenarios
- File Location Reference

**Best For:**
- Quick lookups during development
- Schema validation
- Integration testing
- Understanding data relationships

**Key Sections:**
1. Required fields for burn rate calculation
2. JSON output examples with values
3. Validation checklist
4. Test scenarios (CRITICAL/HIGH/MODERATE/LOW risk cases)

---

### 3. BURN_RATE_IMPLEMENTATION_SUMMARY.txt (17 KB, 385 lines)

**Purpose:** Executive summary of implementation status and key findings

**Contents:**
- Overview and key understanding
- Core Functions (4 total, with line numbers)
- Data Flow Architecture (sequential Phase 2 → 3 → 5)
- Key Algorithms (pseudocode for each calculation)
- Output Metrics (burn_rate_analysis, cash_runway, liquidity_risk, sustainable_burn)
- Input Data Requirements (critical vs. optional vs. not used)
- Testing & Validation (test suite overview)
- Real-World Example (worked scenario with numbers)
- Distribution Cut Prediction Readiness
- File Locations Reference
- Quality Assurance Metrics
- Next Steps for Distribution Cut Prediction

**Best For:**
- Executive briefing
- Project status overview
- Understanding quality metrics
- Planning distribution cut feature

**Key Sections:**
1. Self-Funding Ratio interpretation guide
2. Real-world REIT example with calculations
3. Distribution cut probability framework
4. Next steps roadmap

---

## Quick Navigation

### By Purpose

**I need to understand how burn rate works:**
→ Start with BURN_RATE_IMPLEMENTATION_SUMMARY.txt (Section 1-5)

**I need to implement/debug code:**
→ BURN_RATE_ANALYSIS_REPORT.md (Section 2-3) + BURN_RATE_SCHEMA_REFERENCE.md

**I need to check input data requirements:**
→ BURN_RATE_SCHEMA_REFERENCE.md (Phase 2 Extraction Schema)

**I need to know what's being output:**
→ BURN_RATE_ANALYSIS_REPORT.md (Section 6) or BURN_RATE_SCHEMA_REFERENCE.md (Phase 3 Output)

**I need to validate data/tests:**
→ BURN_RATE_SCHEMA_REFERENCE.md (Validation Checklist + Testing Reference)

**I need real examples:**
→ BURN_RATE_IMPLEMENTATION_SUMMARY.txt (Section 8) or BURN_RATE_SCHEMA_REFERENCE.md (Scenarios)

**I need to plan distribution cut feature:**
→ BURN_RATE_ANALYSIS_REPORT.md (Section 9) + BURN_RATE_IMPLEMENTATION_SUMMARY.txt (Section 12)

---

### By Audience

**Credit Analysts:**
- BURN_RATE_IMPLEMENTATION_SUMMARY.txt (overview + examples)
- BURN_RATE_SCHEMA_REFERENCE.md (output metrics)

**Software Engineers:**
- BURN_RATE_ANALYSIS_REPORT.md (complete reference)
- BURN_RATE_SCHEMA_REFERENCE.md (schema and validation)
- Inline code comments in burn_rate.py

**Project Managers:**
- BURN_RATE_IMPLEMENTATION_SUMMARY.txt (status + next steps)

**Data Scientists/Analysts:**
- BURN_RATE_SCHEMA_REFERENCE.md (schema + examples)
- Test fixtures in `/tests/fixtures/`

---

## Related Source Files

### Core Implementation
- `/scripts/calculate_credit_metrics/burn_rate.py` - Main implementation (4 functions, 473 lines)
- `/scripts/calculate_credit_metrics/afcf.py` - AFCF calculation (input to burn rate)
- `/scripts/calculate_credit_metrics/acfo.py` - ACFO calculation (input to AFCF)
- `/scripts/calculate_credit_metrics/coverage.py` - Interest coverage (period interest extraction)

### Schema
- `/.claude/knowledge/phase2_extraction_schema.json` - JSON schema definition
- `/.claude/knowledge/SCHEMA_README.md` - Schema documentation

### Templates
- `/templates/credit_opinion_template.md` - Section 4.3 has burn rate output

### Testing
- `/tests/test_burn_rate_calculations.py` - 25+ unit tests
- `/tests/test_burn_rate_integration.py` - Integration tests
- `/tests/fixtures/reit_burn_rate_high_risk.json` - Test scenario

---

## Key Metrics at a Glance

### Self-Funding Ratio (Primary Indicator)
```
AFCF / Mandatory Obligations

≥ 1.0x   → No burn (self-sufficient)
0.8-1.0  → Low burn (needs capital markets)
0.5-0.8  → Moderate burn (medium-term stress)
< 0.5x   → High burn (critical stress)
```

### Cash Runway (Timing Indicator)
```
> 24 months  → LOW risk (adequate runway)
12-24 months → MODERATE risk (plan financing)
6-12 months  → HIGH risk (capital raise needed)
< 6 months   → CRITICAL risk (immediate action)
```

### Risk Score (0-4 scale)
```
0    → N/A (no burn rate)
1    → LOW (runway > 24 months)
2    → MODERATE (runway 12-24 months)
3    → HIGH (runway 6-12 months)
4    → CRITICAL (runway < 6 months)
```

---

## Common Calculations

### Monthly Burn Rate
```
Period Deficit = AFCF - (Debt Service + Distributions)
Monthly Burn = Period Deficit / Period Months
```

### Cash Runway
```
Available Cash = Cash + Securities - Restricted Cash
Runway (months) = Available Cash / |Monthly Burn Rate|
```

### Self-Funding Ratio
```
Self-Funding Ratio = AFCF / (Interest + Principal + Distributions)
```

### Sustainable Burn
```
Sustainable Monthly Burn = Available Cash / 24 (target runway)
Excess Burn = Actual Monthly Burn - Sustainable Monthly Burn
```

---

## Important Notes

### Critical Understanding
1. **Burn Rate ≠ Negative AFCF** - A REIT can have positive AFCF but still burn cash
2. **Period vs. Annualized** - Burn rate uses PERIOD interest, not annualized
3. **No Capital Markets Assumption** - Burn rate excludes new financing (stress test)
4. **Mandatory vs. Optional** - Only debt service and distributions count (not growth investments)

### Data Quality
- All calculations include data_quality assessment ("strong", "moderate", "limited", "none")
- Missing data results in graceful degradation, not errors
- Optional fields default to 0 when not available

### Period Normalization
- Q1 → annualization factor 4 → period_months = 3
- Q2 → annualization factor 2 → period_months = 6
- Q3 → annualization factor 1.33 → period_months = 9
- Q4 → annualization factor 1 → period_months = 12

---

## Feature Roadmap: Distribution Cut Prediction

### Current Status (v1.0.7)
- ✅ Burn rate calculation
- ✅ Cash runway analysis
- ✅ Liquidity risk assessment
- ✅ Sustainable burn analysis
- ✅ 4-tier risk classification

### Planned (v1.0.8+)
- 🔄 Distribution cut prediction module
- 🔄 Cut probability calculation
- 🔄 Post-cut runway projection
- 🔄 Credit implications assessment
- 🔄 Scenario modeling

### Prerequisites Met
All data needed for distribution cut prediction is already calculated:
- `burn_rate_analysis.self_funding_ratio` (primary signal)
- `burn_rate_analysis.monthly_burn_rate` (intensity)
- `cash_runway.runway_months` (timing)
- `liquidity_risk.risk_level` (classification)
- `sustainable_burn.excess_burn_per_month` (magnitude)
- `ffo_affo.distributions_per_unit` (current payout)
- `balance_sheet.common_units_outstanding` (unit count)

---

## File Organization in Repository

```
/workspaces/issuer-credit-analysis/
├── BURN_RATE_DOCUMENTATION_INDEX.md (this file)
├── BURN_RATE_ANALYSIS_REPORT.md (27 KB comprehensive)
├── BURN_RATE_SCHEMA_REFERENCE.md (17 KB quick reference)
├── BURN_RATE_IMPLEMENTATION_SUMMARY.txt (17 KB status summary)
│
├── scripts/
│   └── calculate_credit_metrics/
│       └── burn_rate.py (main implementation)
│
├── templates/
│   └── credit_opinion_template.md (Section 4.3)
│
├── .claude/knowledge/
│   └── phase2_extraction_schema.json
│
└── tests/
    ├── test_burn_rate_calculations.py
    └── fixtures/
        └── reit_burn_rate_high_risk.json
```

---

## Getting Started

### For New Users
1. Read: BURN_RATE_IMPLEMENTATION_SUMMARY.txt (15 min read)
2. Reference: BURN_RATE_SCHEMA_REFERENCE.md (as needed)
3. Explore: burn_rate.py code with inline comments

### For Developers
1. Review: BURN_RATE_ANALYSIS_REPORT.md (section 2-3, 4-5, 8)
2. Reference: BURN_RATE_SCHEMA_REFERENCE.md
3. Run: tests/test_burn_rate_calculations.py
4. Debug: Use test fixture reit_burn_rate_high_risk.json

### For Integration
1. Understand: Data flow (BURN_RATE_ANALYSIS_REPORT.md section 5)
2. Map: Phase 2 schema to your extraction process
3. Validate: Required fields checklist (BURN_RATE_SCHEMA_REFERENCE.md)
4. Test: With provided fixtures and test cases

---

## Support & Questions

### Understanding Burn Rate
→ See BURN_RATE_IMPLEMENTATION_SUMMARY.txt Section 1-5 and Section 8 (example)

### Schema/Data Mapping
→ See BURN_RATE_SCHEMA_REFERENCE.md Phase 2/3 sections

### Implementation Details
→ See BURN_RATE_ANALYSIS_REPORT.md (all sections)

### Code Reference
→ See inline comments in /scripts/calculate_credit_metrics/burn_rate.py

### Test Examples
→ See /tests/test_burn_rate_calculations.py and fixtures

---

**Document Status:** Final | **Version:** v1.0.7 | **Last Updated:** 2025-10-21
