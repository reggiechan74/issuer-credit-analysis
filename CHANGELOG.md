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

## [2.0.0] - 2025-10-17

### Added - Schema Standardization

#### New Files
- **`scripts/validate_extraction_schema.py`** - Schema validation tool to catch Phase 2→Phase 3 compatibility issues
- **`.claude/knowledge/phase2_extraction_schema.json`** - Formal JSON Schema specification for Phase 2 extraction output
- **`.claude/knowledge/phase2_extraction_template.json`** - Practical template with inline comments
- **`.claude/knowledge/SCHEMA_README.md`** - Comprehensive schema documentation with examples and troubleshooting
- **`PIPELINE_QUICK_REFERENCE.md`** - Quick reference guide for common operations
- **`.claude/commands/analyzeREissuer.md`** - Slash command for complete pipeline execution
- **`.claude/commands/README.md`** - Slash commands documentation
- **`CLAUDE.md`** - Guidance file for Claude Code instances
- **`CHANGELOG.md`** - This file

#### Features
- **Schema validation** - Automated validation catches errors before Phase 3 calculations
- **Backward compatibility** - Phase 3 now supports both old and new field naming conventions
- **Null handling** - Graceful conversion of null values to 0 for numeric fields
- **Clear error messages** - Field path reporting with fix suggestions
- **Slash command integration** - `/analyzeREissuer` command for streamlined workflow

### Changed

#### Phase 2 (extract_key_metrics.py)
- Updated extraction prompt with explicit schema instructions
- Added references to schema files in prompt
- Emphasized critical rules (flat structure, no nulls, decimal rates)
- Added validation step to recommended workflow

#### Phase 3 (calculate_credit_metrics.py)
- Added null value handling (converts to 0)
- Added support for both `occupancy_with_commitments` and `occupancy_including_commitments`
- Added support for both `same_property_noi_growth_6m` and `same_property_noi_growth`
- Improved error messages with dot-notation field paths
- Enhanced portfolio metrics extraction with defensive coding

#### Documentation
- Reorganized agents and knowledge into `.claude/` folder structure
- Created comprehensive schema documentation
- Added quick reference guide
- Improved README with schema compliance notes

### Fixed
- **Critical:** Schema inconsistencies between Phase 2 extraction and Phase 3 calculations
- **TypeError:** Division by None when `portfolio.total_gla_sf` was null
- **KeyError:** Missing top-level `income_statement.noi` and `ffo_affo.*` fields
- **KeyError:** Nested `balance_sheet` structure causing field access errors
- Occupancy rate interpretation (decimal vs percentage format)

### Breaking Changes
None - Backward compatibility maintained for existing extractions

### Migration Notes
- Existing Phase 2 JSON files continue to work due to backward compatibility
- New extractions automatically use standardized schema
- Run `python scripts/validate_extraction_schema.py <file>` to check compatibility

---

## [1.0.0] - 2025-10-16

### Added - Initial Release

#### Core Pipeline
- **Phase 1:** PDF to Markdown conversion using markitdown
- **Phase 2:** Financial data extraction using Claude Code
- **Phase 3:** Credit metrics calculation with pure Python
- **Phase 4:** Qualitative credit analysis using slim agent
- **Phase 5:** Final report generation with templating

#### Agent Profiles
- `issuer_due_diligence_expert_slim.md` - 7.7KB optimized agent (recommended)
- `issuer_due_diligence_expert.md` - 60KB full agent for complex scenarios

#### Scripts
- `preprocess_pdfs_markitdown.py` - PDF preprocessing
- `extract_key_metrics.py` - Financial data extraction prompt generator
- `calculate_credit_metrics.py` - Safe calculation library (no hardcoded data)
- `generate_final_report.py` - Report template engine

#### Testing
- Comprehensive test suite covering all 5 phases
- Test fixtures for each phase
- 19 tests (13 active, 6 skipped)

#### Features
- **Multi-phase architecture** - Avoids context length limitations
- **Token efficiency** - 85% reduction (121,500 → 18,000 tokens)
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

#### Documentation
- Comprehensive README.md
- Domain knowledge documentation
- Research summaries
- Scope and limitations

---

## Version Numbering

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR** version: Incompatible API/schema changes
- **MINOR** version: New functionality (backward compatible)
- **PATCH** version: Bug fixes (backward compatible)

### Current Versions

| Component | Version | Notes |
|-----------|---------|-------|
| Pipeline | 2.0 | Schema standardization |
| Schema | 1.0 | Initial standardized schema |
| CLAUDE.md | 1.0.0 | Initial guidance document |

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
