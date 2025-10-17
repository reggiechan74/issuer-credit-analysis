# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Integration with financial data APIs (Bloomberg, FactSet)
- Visualization dashboards for credit metrics
- Peer comparison analytics
- Additional asset class support (corporate bonds, structured finance)

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
| Pipeline | 1.0.0 | Initial release with schema standardization |
| Schema | 1.0.0 | Initial standardized schema |
| CLAUDE.md | 1.0.0 | Initial guidance document |
| CHANGELOG.md | 1.0.0 | Initial changelog |

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
