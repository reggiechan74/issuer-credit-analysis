# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Integration with financial data APIs (Bloomberg, FactSet)
- Visualization dashboards for credit metrics
- Additional asset class support (corporate bonds, structured finance)

---

## [1.0.6] - 2025-10-20

### Added - AFCF (Adjusted Free Cash Flow) Calculations
- **New Metric:** Implemented Adjusted Free Cash Flow (AFCF) for comprehensive credit analysis
  - **Formula:** AFCF = ACFO + Net Cash Flow from Investing Activities
  - **Purpose:** Measures cash available for debt service and distributions after ALL operating and investing activities
  - **Key Distinction:** More conservative than ACFO - accounts for growth investments (property acquisitions, development capex, JV investments)

### Schema Extensions
- **Phase 2 Schema:** Added `cash_flow_investing` section
  - Captures development CAPEX, property acquisitions/dispositions, JV investments, business combinations
  - Uses negative numbers for outflows, positive for inflows
  - Includes `total_cfi` for reconciliation with IFRS cash flow statement

- **Phase 2 Schema:** Added `cash_flow_financing` section
  - Captures debt principal repayments, distributions, new financing (debt/equity issuances)
  - Enables AFCF coverage ratio analysis
  - Includes `total_cff` for reconciliation

### New Functions (Phase 3)
- **`calculate_afcf()`** - Calculates AFCF from ACFO and investing activities
  - Prevents double-counting with ACFO components (sustaining capex, TI, leasing costs already deducted)
  - Returns AFCF value, net CFI breakdown, data quality assessment, reconciliation checks
  - Automatically validates against reported total_cfi if available

- **`calculate_afcf_coverage_ratios()`** - Calculates financing obligation coverage metrics
  - **AFCF Debt Service Coverage:** AFCF / (Interest + Principal Repayments)
  - **AFCF Distribution Coverage:** AFCF / Total Distributions (inverted payout ratio)
  - **AFCF Self-Funding Ratio:** AFCF / (Debt Service + Distributions - New Financing)
  - More conservative than traditional NOI/Interest coverage

- **`validate_afcf_reconciliation()`** - Validates AFCF calculation accuracy
  - Checks: AFCF = ACFO + Net CFI
  - Validates development CAPEX consistency between ACFO and CFI
  - Reconciles to IFRS cash flow statement if all components available (CFO + CFI + CFF = Change in Cash)

### Integration
- **`calculate_all_metrics()`** - Integrated AFCF into Phase 3 output
  - Automatically calculates AFCF if `cash_flow_investing` data present
  - Adds `afcf_metrics`, `afcf_coverage`, and `afcf_reconciliation` to output JSON
  - Backward compatible - AFCF calculation is optional (gracefully skipped if data unavailable)

### Testing
- **New Test Suite:** `tests/test_afcf_financial_calculations.py` (17 comprehensive tests)
  - Tests basic AFCF calculation with all components
  - Tests data quality assessment (strong/moderate/limited)
  - Tests coverage ratios (debt service, distributions, self-funding)
  - Tests reconciliation validation and error detection
  - Tests double-counting prevention with ACFO
  - Tests edge cases (negative FCF, positive net CFI, missing data)
  - **All tests passing** ✅

### Use Cases
- **Credit Analysis:** Identifies REITs reliant on external financing for debt service
- **Distribution Sustainability:** Modified payout ratio based on true free cash flow (more conservative than AFFO payout)
- **Growth Assessment:** Distinguishes between self-funding growth vs. capital market dependent growth
- **Debt Service Coverage:** More comprehensive than NOI/Interest (includes principal repayments and capex)

### Example
```json
{
  "afcf_metrics": {
    "afcf": 22000,
    "acfo_starting_point": 50000,
    "net_cfi": -28000,
    "data_quality": "strong"
  },
  "afcf_coverage": {
    "afcf_debt_service_coverage": 0.40,  // ⚠️ Low - needs external financing
    "afcf_payout_ratio": 86.4,           // Sustainable from FCF
    "afcf_self_funding_ratio": 0.37      // Reliant on capital markets
  }
}
```

### Documentation
- **Research Paper:** `docs/AFCF_Research_Proposal.md` - Comprehensive methodology and implementation guide
- **Schema Documentation:** Updated `.claude/knowledge/phase2_extraction_schema.json` and template
- **GitHub Issue:** #6 - Complete implementation roadmap

### Migration Notes
- **Backward Compatible:** Existing Phase 3 outputs will continue to work
- **Optional Feature:** AFCF only calculated if `cash_flow_investing` data provided in Phase 2
- **Phase 2 Enhancement:** Update extraction prompts to include CFI/CFF sections for full AFCF support
- **No Breaking Changes:** All existing metrics (FFO, AFFO, ACFO, leverage, coverage) unchanged

### Performance
- **Minimal Overhead:** AFCF adds ~500 lines of well-tested code
- **Token Impact:** None for Phase 2 (uses file references)
- **Execution Time:** < 100ms for AFCF calculations

---

## [1.0.5] - 2025-10-18

### Fixed
- **Critical Fix:** Annualized interest calculation in `scripts/calculate_credit_metrics.py`
  - **Root Cause:** `calculate_coverage_ratios()` hardcoded assumption that all interest_expense was quarterly (×4 multiplier)
  - **Impact:** Semi-annual data was incorrectly annualized (e.g., Dream Industrial REIT: $169,484 instead of $84,742 - 100% overstatement)
  - **Solution:** Added intelligent period detection logic that identifies:
    - Semi-annual periods: "six months", "6 months" → multiply by 2
    - Quarterly periods: "three months", "quarterly", "quarter" → multiply by 4
    - Annual periods: "year", "annual" → multiply by 1
    - Unknown periods: Default to quarterly with warning
  - **New Metadata:** Added `annualization_factor` and `detected_period` fields to output
  - **Field Rename:** `quarterly_interest_expense` → `period_interest_expense` (more accurate terminology)
  - **Validation:** Discovered via comprehensive validation report for Dream Industrial REIT Q2 2025

### Validation Details
- **Test Case:** Dream Industrial REIT Q2 2025 (six months ended June 30, 2025)
- **Period Interest Expense:** $42,371 (actual 6-month data from financial statements)
- **Before Fix:** $42,371 × 4 = $169,484 (wrong - treated as quarterly)
- **After Fix:** $42,371 × 2 = $84,742 (correct - detected as semi-annual)
- **Coverage Ratio:** 4.40x (remained correct because both NOI and interest were same period)

### Migration Notes
- Existing Phase 3 outputs should be regenerated for accuracy
- No schema changes - backward compatible with existing JSON structure
- New fields (`annualization_factor`, `detected_period`) are additive enhancements

### Performance
- No performance impact
- Detection adds ~10 lines of code (minimal overhead)
- Warning messages help identify edge cases where period can't be detected

---

## [1.0.4] - 2025-10-17

### Changed - REVERT v1.1.0 Parallel PDF Approach
- **REVERTED to v1.0.x sequential markdown-first architecture**
  - v1.1.0 parallel PDF approach caused context window exhaustion
  - Direct PDF reading consumed ~136K tokens (545KB PDFs)
  - Left insufficient context for extraction logic

### Fixed
- **Config Default:** Changed from `pdf_direct` back to `manual` (markdown-first)
  - `config/extraction_config.yaml`: Updated recommendations and preset ordering
  - Deprecated `pdf_direct` and `pdf_only` presets with warnings

- **Slash Command:** `/analyzeREissuer` restored to sequential execution
  - Phase 1 runs FIRST (foreground): PDF → Markdown
  - Phase 2 runs SECOND (after Phase 1): Markdown → JSON with file references
  - Removed `--pdf` flag and parallel execution with `&`

- **CLAUDE.md:** Updated to reflect v1.0.4 architecture
  - Version bumped from 1.1.0 → 1.0.4
  - Architecture diagram shows sequential processing
  - Token usage table corrected: ~13K total (not ~18K)
  - Added "Why Markdown-First Architecture" section explaining design rationale

### Architecture Comparison

| Approach | Phase 1 | Phase 2 Tokens | Context Available | Result |
|----------|---------|----------------|-------------------|---------|
| **v1.1.0 (Parallel PDF)** | Background | ~136K (reading PDFs) | ~64K | ❌ Context exhausted |
| **v1.0.4 (Sequential MD)** | Foreground | ~1K (file refs) | ~199K | ✅ Works reliably |

### Performance
- **Token usage:** ~13,000 total (89% reduction vs original 121,500)
  - Phase 1: 0 tokens (Python preprocessing)
  - Phase 2: ~1,000 tokens (file references)
  - Phase 3: 0 tokens (calculations)
  - Phase 4: ~12,000 tokens (agent)
  - Phase 5: 0 tokens (templating)
- **Execution time:** ~60 seconds total (sequential)
- **Reliability:** 100% success rate (no context exhaustion)
- **Cost:** ~$0.30 per analysis

### Migration Notes
- No action required for existing workflows
- `/analyzeREissuer` command continues to work as expected
- Phase 1 now completes before Phase 2 begins (sequential)
- Markdown files required for Phase 2 extraction

---

## [1.1.0] - 2025-10-17 - DEPRECATED

### Status: DEPRECATED - Do Not Use
This version attempted parallel PDF processing but caused context window exhaustion.
**Use v1.0.4 or later instead.**

### Why Deprecated
- Direct PDF reading consumed ~136K tokens for typical financial statements
- Claude Code context exhaustion prevented reliable extraction
- Sequential markdown-first approach (v1.0.x) is more token-efficient

### What Was Attempted
- Parallel execution of Phase 1 (background) and Phase 2 (foreground)
- Direct PDF→JSON extraction using Claude Code's native PDF reading
- Goal was to eliminate markdown intermediary for data extraction

### Why It Failed
- ❌ 545KB PDFs = ~136K tokens when read directly
- ❌ Left only ~64K tokens for extraction logic and output
- ❌ Frequent context window exhaustion errors
- ✅ v1.0.x markdown-first uses ~1K tokens via file references

---

## [1.0.3] - 2025-10-17

### Added
- **Phase 2 Efficiency Improvement:** New `extract_key_metrics_efficient.py` script
  - 99.2% token reduction (563 KB → 4.1 KB, ~140K → ~1K tokens)
  - References file paths instead of embedding entire markdown content
  - Significantly faster Claude Code processing
  - Identical JSON output format to legacy script
  - Scales to any number/size of input files
- Documentation: `docs/PHASE2_EFFICIENCY_IMPROVEMENT.md` with technical details

### Changed
- README.md: Updated Phase 2 command to use efficient script as default
- CLAUDE.md: Added Phase 2 Efficiency section with comparison table
- CLAUDE.md: Marked `extract_key_metrics.py` as legacy (inefficient)
- Version badges: Updated to 1.0.3

### Performance
- **Phase 2 prompt size:** 563 KB → 4.1 KB (99.2% smaller)
- **Phase 2 tokens:** ~140,000 → ~1,000 (99.3% reduction)
- **Processing speed:** Significantly faster (context-efficient)
- **Scalability:** No longer limited by prompt size constraints

### Documentation
- Complete technical analysis in `docs/PHASE2_EFFICIENCY_IMPROVEMENT.md`
- Before/after comparison with example outputs
- Migration guide for existing projects

---

## [1.0.2] - 2025-10-17

### Added
- **Phase 1 Enhancement:** New `preprocess_pdfs_enhanced.py` script (resolves Issue #1)
  - PyMuPDF4LLM + Camelot hybrid approach for table extraction
  - Properly formatted financial tables with aligned headers
  - Automatic table classification (Balance Sheet, Income Statement, FFO/AFFO)
  - 40+ tables extracted per financial statement
- v3 enhancements to enhanced script:
  - Removes confusing text-based table fragments from base content
  - Extracts proper column headers from context (e.g., "June 30 2025", "December 31 2024")
  - Enhanced table categorization
- Documentation: Issue resolution docs, comparison documents
- Dependencies: pymupdf4llm, camelot-py[cv], opencv-python-headless

### Changed
- Marked `preprocess_pdfs_markitdown.py` as legacy (being phased out)
- Updated README.md with enhanced script as recommended approach
- CLAUDE.md: Added Phase 1 Enhancements section
- Version: 1.0.1 → 1.0.2

### Fixed
- Issue #1: Poor PDF table formatting causing Phase 2 extraction errors
- Balance sheets now show proper column alignment
- Headers correctly associated with values

### Performance
- Table extraction: 0 → 40+ tables per statement
- Phase 2 accuracy: Significantly improved
- Processing time: 15s (vs 10s markitdown) - acceptable tradeoff

---

## [1.0.1] - 2025-10-17

### Changed
- **Phase 4 Agent Enhancement:** Updated `issuer_due_diligence_expert_slim` agent to use parallel web searches for peer comparison research
  - Section 9 (Peer Comparison) now researches 3-4 comparable REITs simultaneously instead of sequentially
  - Added explicit parallel processing instructions with concrete examples
  - Includes efficiency guideline emphasizing parallel tool calls
  - Significantly improves Phase 4 execution time when generating peer comparisons

### Added
- Comprehensive peer comparison example report for Artis REIT with actual Q2 2025 data
  - Dream Office REIT, Allied Properties REIT, H&R REIT, Choice Properties REIT
  - All sources properly cited with URLs and dates
  - Demonstrates parallel web research capabilities

### Performance
- **Peer Research Speed:** Reduced from sequential (N × search_time) to parallel (1 × search_time) for N peers
- **Agent Efficiency:** Better utilization of Claude Code's concurrent tool execution capabilities

---

## [1.0.0] - 2025-10-17

### Added - Initial Release with Schema Standardization

#### Core Pipeline
- **Phase 1:** PDF to Markdown conversion using markitdown
- **Phase 2:** Financial data extraction using Claude Code
- **Phase 3:** Credit metrics calculation with pure Python
- **Phase 4:** Qualitative credit analysis using slim agent
- **Phase 5:** Final report generation with templating

#### Schema Standardization
- **`scripts/validate_extraction_schema.py`** - Schema validation tool
- **`.claude/knowledge/phase2_extraction_schema.json`** - JSON Schema specification
- **`.claude/knowledge/phase2_extraction_template.json`** - Schema template with comments
- **`.claude/knowledge/SCHEMA_README.md`** - Complete schema documentation
- **`PIPELINE_QUICK_REFERENCE.md`** - Quick reference guide

#### Agent Profiles
- `.claude/agents/issuer_due_diligence_expert_slim.md` - 7.7KB optimized agent (recommended)
- `.claude/agents/issuer_due_diligence_expert.md` - 60KB full agent for complex scenarios

#### Scripts
- `scripts/preprocess_pdfs_markitdown.py` - PDF preprocessing
- `scripts/extract_key_metrics.py` - Financial data extraction prompt generator
- `scripts/calculate_credit_metrics.py` - Safe calculation library (no hardcoded data)
- `scripts/generate_final_report.py` - Report template engine
- `scripts/validate_extraction_schema.py` - Schema validation

#### Slash Commands
- `.claude/commands/analyzeREissuer.md` - Complete pipeline execution
- `.claude/commands/verifyreport.md` - Report verification
- `.claude/commands/README.md` - Commands documentation

#### Testing
- Comprehensive test suite covering all 5 phases
- Test fixtures for each phase
- 19 tests (13 active, 6 skipped)

#### Features
- **Multi-phase architecture** - Avoids context length limitations
- **Token efficiency** - 85% reduction (121,500 → 18,000 tokens)
- **Schema validation** - Automated error detection before Phase 3
- **Backward compatibility** - Supports legacy field naming conventions
- **Null handling** - Graceful conversion of null to 0 for numeric fields
- **Issuer-specific folders** - Organized output with temp/reports separation
- **Zero-API dependency** - Works entirely within Claude Code
- **Production-ready reports** - Professional Moody's-style credit opinions

#### Credit Metrics
- Leverage: Debt/Assets, Net Debt Ratio
- REIT Metrics: FFO, AFFO, payout ratios
- Coverage: NOI/Interest, EBITDA/Interest
- Portfolio: Occupancy, same-property NOI growth

#### Safety Features
- No hardcoded financial data
- Loud failures with clear error messages
- Balance sheet validation
- NOI margin checks
- Occupancy range validation
- Schema compliance validation

#### Documentation
- `README.md` - Comprehensive project documentation
- `CLAUDE.md` - Guidance for Claude Code instances
- `CHANGELOG.md` - Version history and release notes
- `PIPELINE_QUICK_REFERENCE.md` - Quick reference guide
- `.claude/knowledge/SCHEMA_README.md` - Schema documentation
- Domain knowledge documentation
- Research summaries
- Scope and limitations

### Fixed
- **Critical:** Schema inconsistencies between Phase 2 extraction and Phase 3 calculations
- **TypeError:** Division by None when `portfolio.total_gla_sf` was null
- **KeyError:** Missing top-level `income_statement.noi` and `ffo_affo.*` fields
- **KeyError:** Nested `balance_sheet` structure causing field access errors
- Occupancy rate interpretation (decimal vs percentage format)

---

## Version Numbering

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR** version: Incompatible API/schema changes
- **MINOR** version: New functionality (backward compatible)
- **PATCH** version: Bug fixes (backward compatible)

### Current Versions

| Component | Version | Notes |
|-----------|---------|-------|
| Pipeline | 1.0.5 | Fixed annualized interest calculation |
| Schema | 1.0.0 | Initial standardized schema |
| CLAUDE.md | 1.0.4 | Sequential markdown-first architecture |
| CHANGELOG.md | 1.0.5 | Added v1.0.5 release notes |

---

## Contributing

When updating this changelog:

1. Add entries under `[Unreleased]` as changes are made
2. Move entries to a new version section when releasing
3. Follow the categories: Added, Changed, Deprecated, Removed, Fixed, Security
4. Include context and impact for significant changes
5. Reference issue/PR numbers when applicable
6. Update version numbers in:
   - `CLAUDE.md` (header)
   - `CHANGELOG.md` (new version section)
   - `.claude/knowledge/SCHEMA_README.md` (if schema changes)
   - `PIPELINE_QUICK_REFERENCE.md` (if pipeline changes)

---

## Links

- [Repository](https://github.com/reggiechan74/issuer-credit-analysis)
- [Issues](https://github.com/reggiechan74/issuer-credit-analysis/issues)
- [Discussions](https://github.com/reggiechan74/issuer-credit-analysis/discussions)
- [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
- [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
