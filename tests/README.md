# Test Suite Documentation

Comprehensive test coverage for the Real Estate Issuer Credit Analysis Pipeline.

**Last Updated:** 2025-10-21
**Test Coverage:** Phase 1-5 + Integration Tests
**Total Tests:** 100+ tests across 12 test files

---

## Table of Contents

- [Overview](#overview)
- [Test Organization](#test-organization)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Test Files Reference](#test-files-reference)
- [Fixtures and Test Data](#fixtures-and-test-data)
- [Writing New Tests](#writing-new-tests)

---

## Overview

The test suite validates all 5 phases of the credit analysis pipeline plus integration testing across phases. Tests ensure:

✅ **Correctness:** Calculations match REALPAC standards
✅ **Reliability:** Handles missing data gracefully
✅ **Performance:** Phase execution times meet targets
✅ **Integration:** Phases connect properly end-to-end

---

## Test Organization

### By Phase

```
Phase 1 (PDF Conversion)      → test_phase1_preprocessing.py
Phase 2 (Extraction)          → test_phase2_extraction.py
Phase 3 (Calculations)        → test_phase3_calculations.py
                                test_ffo_affo_calculations.py
                                test_acfo_calculations.py
                                test_afcf_financial_calculations.py
                                test_burn_rate_calculations.py
Phase 4 (Credit Analysis)     → test_phase4_credit_analysis.py
Phase 5 (Report Generation)   → test_phase5_report_generation.py
Integration                   → test_burn_rate_integration.py
                                test_acfo_integration_dir.py
                                test_artis_reit_ffo_affo.py
                                test_dream_industrial_reit_ffo_affo.py
```

### By Feature

- **FFO/AFFO Calculations:** `test_ffo_affo_calculations.py`, `test_artis_reit_ffo_affo.py`, `test_dream_industrial_reit_ffo_affo.py`
- **ACFO Calculations:** `test_acfo_calculations.py`, `test_acfo_integration_dir.py`
- **AFCF Calculations:** `test_afcf_financial_calculations.py`
- **Burn Rate Analysis:** `test_burn_rate_calculations.py`, `test_burn_rate_integration.py`
- **Structural Considerations (v1.0.13):** `test_phase5_report_generation.py::TestStructuralConsiderationsParsing`

---

## Running Tests

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Phase

```bash
# Phase 3 calculations
pytest tests/test_phase3_calculations.py -v

# Phase 5 report generation
pytest tests/test_phase5_report_generation.py -v
```

### Run Specific Test Class

```bash
# FFO/AFFO calculations
pytest tests/test_ffo_affo_calculations.py::TestFFOCalculations -v

# Burn rate analysis
pytest tests/test_burn_rate_calculations.py::TestBurnRateCalculations -v

# Structural considerations parsing (v1.0.13)
pytest tests/test_phase5_report_generation.py::TestStructuralConsiderationsParsing -v
```

### Run Single Test

```bash
pytest tests/test_phase3_calculations.py::TestPhase3Calculations::test_calculate_leverage_metrics -v
```

### Coverage Report

```bash
# Generate HTML coverage report
pytest tests/ --cov=scripts --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

---

## Test Categories

### 1. Unit Tests

**Purpose:** Test individual functions in isolation

**Examples:**
- `test_calculate_ffo()` - FFO calculation logic
- `test_calculate_leverage_metrics()` - Leverage ratio calculations
- `test_parse_debt_structure()` - Debt structure parsing (v1.0.13)

**Location:** All `test_*.py` files with function-level tests

### 2. Integration Tests

**Purpose:** Test data flow between phases

**Examples:**
- `test_acfo_integration_dir.py` - Full ACFO calculation with Dream Industrial data
- `test_burn_rate_integration.py` - Burn rate analysis with real Phase 2 data
- `test_structural_considerations_integration()` - All 3 parsing functions together (v1.0.13)

**Location:** Files with `integration` in the name, plus integration test classes

### 3. End-to-End Tests

**Purpose:** Test complete pipeline workflows

**Examples:**
- `test_complete_pipeline_readiness()` - All phases can connect
- `test_assembly_with_sample_data()` - Phase 3 + Phase 4 → Phase 5 report

**Location:** `test_phase5_report_generation.py::TestPhase5Integration`

### 4. Validation Tests

**Purpose:** Ensure data quality and schema compliance

**Examples:**
- `test_balance_sheet_balancing()` - Assets = Liabilities + Equity
- `test_noi_margin_validation()` - NOI margins in realistic range
- `test_phase3_to_phase5_flow()` - Required fields present for report generation

**Location:** `test_phase3_calculations.py::TestPhase3Validation`

### 5. Error Handling Tests

**Purpose:** Verify graceful degradation with missing/invalid data

**Examples:**
- `test_affo_variance_none_handling()` - Handle unreported AFFO
- `test_all_variance_fields_none()` - All variance fields None (extreme case)
- `test_parse_debt_structure_with_no_content()` - No debt info → "Not available" (v1.0.13)

**Location:** `test_phase5_report_generation.py::TestPhase5NoneHandling`

### 6. Performance Tests

**Purpose:** Ensure execution time targets are met

**Examples:**
- `test_fast_execution()` - Phase 5 completes in <5 seconds
- `test_no_llm_usage()` - Phase 5 uses 0 tokens (pure templating)

**Location:** `test_phase5_report_generation.py::TestPhase5Performance`

### 7. Regression Tests

**Purpose:** Prevent bugs from reappearing

**Examples:**
- `test_parse_debt_structure_debt_calculation_fix()` - Debt shows $7.4B not $7,435.7B (v1.0.13)
- `test_parse_security_collateral_recovery_estimate_precedence()` - Recovery estimate >80%, not 30% discount (v1.0.13)

**Location:** Test methods with descriptive names referencing specific bug fixes

---

## Test Files Reference

### Phase 1: PDF Conversion

#### `test_phase1_preprocessing.py`
Tests PDF → Markdown conversion with PyMuPDF4LLM + Camelot

**Test Classes:**
- `TestPhase1ScriptExists` - Script file existence and interface
- `TestPhase1Execution` - PDF conversion execution
- `TestPhase1OutputQuality` - Markdown output validation

**Key Tests:**
- PDF file validation
- Markdown file creation
- Table extraction quality

---

### Phase 2: Data Extraction

#### `test_phase2_extraction.py`
Tests Markdown → JSON extraction using file references

**Test Classes:**
- `TestPhase2ScriptExists` - Script existence
- `TestPhase2Execution` - Extraction execution with file references
- `TestPhase2SchemaCompliance` - JSON schema validation

**Key Tests:**
- File reference pattern (not embedding content)
- Schema compliance
- Required field validation

---

### Phase 3: Metric Calculations

#### `test_phase3_calculations.py`
Core Phase 3 calculation tests

**Test Classes:**
- `TestPhase3Calculations` - Main calculation functions
- `TestPhase3Validation` - Data quality validation
- `TestPhase3SafetyFeatures` - No hardcoded data, loud failures

**Key Tests:**
- `test_calculate_leverage_metrics()` - Debt/Assets, Net Debt ratios
- `test_calculate_coverage_ratios()` - NOI/Interest, EBITDA/Interest
- `test_calculate_portfolio_metrics()` - Occupancy, NOI growth

#### `test_ffo_affo_calculations.py`
FFO/AFFO calculation logic (REALPAC standards)

**Test Classes:**
- `TestFFOCalculations` - FFO from net income
- `TestAFFOCalculations` - AFFO from FFO
- `TestFFOAFFOValidation` - Variance calculations

**Key Tests:**
- `test_ffo_from_net_income()` - Add back D&A, gains, IFRS 16
- `test_affo_from_ffo()` - Deduct sustaining capex/TI/leasing
- `test_ffo_affo_variance()` - Calculated vs reported comparison

#### `test_acfo_calculations.py`
ACFO calculation tests

**Test Classes:**
- `TestACFOCalculations` - ACFO from NOI
- `TestACFOValidation` - Variance and reconciliation

**Key Tests:**
- `test_calculate_acfo_from_components()` - REALPAC adjustments A-Z
- `test_acfo_vs_affo_consistency()` - ACFO ≈ AFFO validation
- `test_acfo_variance_calculation()` - Calculated vs reported variance

#### `test_acfo_integration_dir.py`
Dream Industrial REIT ACFO integration tests

**Purpose:** Full ACFO calculation with real issuer data

**Key Tests:**
- Complete ACFO calculation from Phase 2 data
- Component extraction validation
- Variance analysis

#### `test_afcf_financial_calculations.py`
AFCF (Adjusted Free Cash Flow) tests

**Test Classes:**
- `TestAFCFCalculations` - AFCF from ACFO + Net CFI
- `TestAFCFCoverageRatios` - Debt service, payout, self-funding

**Key Tests:**
- `test_calculate_afcf()` - ACFO + Net CFI = AFCF
- `test_afcf_debt_service_coverage()` - AFCF / Total Debt Service
- `test_afcf_self_funding_ratio()` - Can REIT self-fund obligations?

#### `test_burn_rate_calculations.py`
Cash burn rate calculation tests

**Test Classes:**
- `TestBurnRateCalculations` - Monthly/annualized burn rate
- `TestCashRunwayCalculations` - Months until depletion
- `TestLiquidityRiskAssessment` - CRITICAL/HIGH/MODERATE/LOW
- `TestSustainableBurnRate` - Target runway calculations

**Key Tests:**
- 25 burn rate calculation tests
- Edge cases (positive AFCF + burn, zero cash, etc.)

#### `test_burn_rate_integration.py`
Burn rate integration tests with real data

**Test Classes:**
- 11 integration tests
- Real issuer scenarios (RioCan, Artis, DIR)

**Key Tests:**
- Complete burn rate analysis from Phase 2 data
- Liquidity risk assessment accuracy

#### `test_artis_reit_ffo_affo.py`, `test_dream_industrial_reit_ffo_affo.py`
Issuer-specific FFO/AFFO validation tests

**Purpose:** Verify calculations match actual issuer disclosures

**Key Tests:**
- FFO per unit calculations
- AFFO payout ratios
- Distribution coverage

---

### Phase 4: Credit Analysis

#### `test_phase4_credit_analysis.py`
Agent-based credit analysis tests

**Test Classes:**
- `TestPhase4AgentExists` - Agent definition file validation
- `TestPhase4AgentPrompt` - Prompt structure and completeness
- `TestPhase4OutputQuality` - Analysis output validation

**Key Tests:**
- Agent prompt includes 5-factor scorecard methodology
- Output includes required sections (rating, outlook, strengths/challenges)
- Peer comparison research (parallel web searches, v1.0.1)

---

### Phase 5: Report Generation

#### `test_phase5_report_generation.py`
Final report assembly tests

**Test Classes:**
- `TestPhase5ScriptExists` - Script existence and interface
- `TestPhase5Templates` - Template structure validation
- `TestPhase5Assembly` - Report assembly with Phase 3 + Phase 4 data
- `TestPhase5OutputQuality` - Final report quality checks
- `TestPhase5Integration` - Phase 3-4-5 integration
- `TestPhase5Performance` - 0 tokens, <5 second execution
- `TestPhase5NoneHandling` - Graceful handling of missing metrics
- **`TestStructuralConsiderationsParsing` (v1.0.13 - NEW)** - Debt structure, security/collateral, perpetual securities parsing

**Key Tests (v1.0.13 Structural Considerations):**
- `test_parse_debt_structure_with_full_content()` - Extract credit facilities, covenants, debt profile
- `test_parse_security_collateral_with_full_content()` - Extract unencumbered assets, LTV, recovery estimates
- `test_check_perpetual_securities_not_applicable()` - Default to "Not applicable" when none exist
- `test_parse_debt_structure_debt_calculation_fix()` - Debt shows $7.4B not $7,435.7B (bug fix regression test)
- `test_parse_security_collateral_recovery_estimate_precedence()` - Prioritize >80-90% over 30% discount
- `test_structural_considerations_integration()` - All 3 parsing functions work together

**Total Tests:** 35 tests (24 existing + 11 new for v1.0.13)

---

## Fixtures and Test Data

### Location
`tests/fixtures/` - Contains sample data for testing

### Available Fixtures

**Phase 2 Extraction:**
- `sample_extracted_data.json` - Sample Phase 2 output

**Phase 3 Metrics:**
- `phase3_artis_reit_metrics.json` - Complete Artis REIT calculations
- Contains: leverage, coverage, REIT metrics, portfolio metrics

**Phase 4 Analysis:**
- `phase4_sample_analysis.md` - Sample credit analysis markdown

### Test PDFs

**Artis REIT Q2 2025:**
- `tests/ArtisREIT-Q2-25-MDA-Aug-7.pdf` - Original PDF
- `tests/existing_ArtisREIT-Q2-25-MDA-Aug-7.md` - PyMuPDF4LLM markdown
- `tests/docling_ArtisREIT_Q2_25_MDA.md` - Docling markdown
- `tests/docling_FAST_ArtisREIT_Q2_25_MDA.md` - Docling FAST mode
- `tests/mineru_ArtisREIT_Q2_25_MDA.md` - MinerU markdown

**Purpose:** Compare PDF conversion quality across methods

---

## Writing New Tests

### Test Naming Conventions

```python
# Good test names (descriptive, specific)
def test_calculate_ffo_from_net_income():
def test_affo_variance_none_handling():
def test_parse_debt_structure_with_full_content():  # v1.0.13

# Bad test names (vague, unclear)
def test_ffo():
def test_calculation():
def test_parsing():
```

### Test Structure

```python
def test_descriptive_name(self):
    """What this test validates"""
    from module import function

    # Arrange: Set up test data
    input_data = {...}

    # Act: Execute function
    result = function(input_data)

    # Assert: Validate output
    assert result['metric'] == expected_value
    assert 'required_field' in result
```

### Testing Parsing Functions (v1.0.13 Example)

```python
def test_parse_new_feature(self):
    """Test that new feature extracts expected content"""
    from generate_final_report import parse_new_feature

    # Sample Phase 4 content
    phase4_content = """
    ## Section Title
    **Feature:** Some expected content here
    """

    result = parse_new_feature(phase4_content, None, None)

    # Should extract expected content
    assert 'expected content' in result

    # Should handle missing content gracefully
    empty_result = parse_new_feature("No content here", None, None)
    assert empty_result == 'Not available'
```

### Adding Integration Tests

```python
def test_feature_integration(self):
    """Test that feature integrates with existing pipeline"""
    # Load real Phase 2 data
    with open('tests/fixtures/phase3_metrics.json') as f:
        metrics = json.load(f)

    # Execute Phase 3 calculation
    result = calculate_new_metric(metrics)

    # Verify output structure
    assert 'new_metric' in result
    assert result['new_metric'] > 0
```

### Test Coverage Goals

- **Phase 1-2:** 80%+ coverage (harder to test due to LLM dependency)
- **Phase 3:** 95%+ coverage (pure Python, should be near 100%)
- **Phase 4:** 70%+ coverage (agent-based, harder to test)
- **Phase 5:** 90%+ coverage (templating + parsing functions)

---

## Continuous Integration

### Pre-Commit Checks

```bash
# Run before committing
pytest tests/ -v
```

### GitHub Actions

Tests automatically run on:
- Pull requests to `main`
- Commits to `main` branch

**Required:** All tests must pass before merge

---

## Version History

### v1.0.13 (2025-10-21)
- ✅ Added 11 new tests for structural considerations parsing (Issue #32)
- ✅ `TestStructuralConsiderationsParsing` class with comprehensive coverage
- ✅ Tests for `parse_debt_structure()`, `parse_security_collateral()`, `check_perpetual_securities()`
- ✅ Regression tests for debt calculation fix and recovery estimate precedence

### v1.0.10 (2025-10-20)
- Added burn rate and AFCF tests
- Integration tests with real issuer data

### v1.0.7 (2025-10-20)
- Burn rate analysis test suite (36 tests)
- Cash runway and liquidity risk tests

### v1.0.6 (2025-10-19)
- AFCF calculation tests
- Coverage ratio tests

---

## Support

**Issues:** Report test failures via GitHub Issues
**Questions:** See project README.md or CLAUDE.md

**Test Maintenance:** Update tests when adding new features or fixing bugs. Always add regression tests for bug fixes.
