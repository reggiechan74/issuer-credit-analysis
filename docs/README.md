# Documentation Index

**Pipeline Version:** v1.0.12
**Last Updated:** 2025-10-21

This directory contains all technical documentation for the Issuer Credit Analysis Pipeline. Documentation is organized by purpose and status.

---

## 📖 Quick Navigation

| Category | Purpose | Location |
|----------|---------|----------|
| **Architecture** | Foundation documents & design decisions | [`architecture/`](architecture/) |
| **Active Work** | Current development tasks | [`active/`](active/) |
| **Research** | Technical research & evaluations | [`research/`](research/) |
| **Outreach** | LinkedIn posts & external communication | [`outreach/`](outreach/) |
| **Archive** | Completed features & deprecated docs | [`archive/`](archive/) |

---

## 🏗️ Architecture (Foundation Documents)

Essential reading for understanding the system design:

### [`architecture/COMPLETE_ARCHITECTURE.md`](architecture/COMPLETE_ARCHITECTURE.md)
**Status:** ✅ Active Reference (v1.0.12)
**Summary:** Complete end-to-end pipeline documentation covering all 5 phases, token usage, and file structure.

**Key Topics:**
- Phase 1: PDF → Markdown conversion (PyMuPDF4LLM + Camelot)
- Phase 2: Markdown → JSON extraction (file references, ~1K tokens)
- Phase 3: Pure Python credit metric calculations (0 tokens)
- Phase 4: Credit analysis via issuer_due_diligence_expert_slim agent
- Phase 5: Template-based final report generation

**When to Read:** Start here for system overview, architecture decisions, and phase interdependencies.

---

### [`architecture/V1.0.4_REVERSION_LESSONS.md`](architecture/V1.0.4_REVERSION_LESSONS.md)
**Status:** ✅ Lessons Learned
**Summary:** Why markdown-first architecture beats direct PDF reading (v1.1.0 failure analysis).

**Key Lessons:**
- v1.1.0 parallel PDF approach failed due to context window exhaustion (136K tokens)
- v1.0.4 markdown-first approach succeeded with file references (~1K tokens)
- "Simpler and slower beats complex and broken"

**When to Read:** Before proposing architectural changes to PDF processing or Phase 2 extraction.

---

## 🔧 Active Work (Current Development)

Documentation for ongoing implementation tasks:

### [`active/PHASE5_DUAL_TABLE_RECONCILIATION_FIX.md`](active/PHASE5_DUAL_TABLE_RECONCILIATION_FIX.md)
**Status:** ⚠️ Partially Complete (Issues 1-3 ✅ | Issue 5 Pending)
**Summary:** Implementation plan for dual-table reporting (Issuer-Reported vs. REALPAC-Calculated metrics).

**Completed:**
- ✅ Section 2.2.2: IFRS Cash Flow from Operations display fix
- ✅ Section 2.3: Dual-table FFO/AFFO reconciliation
- ✅ Section 2.4: Dual-table ACFO reconciliation

**Remaining:**
- ⚠️ Issue 5: ACFO calculated value not populating in Section 2.2.2 & 2.5.2

**When to Read:** Working on Phase 5 template population or reconciliation tables.

---

### [`active/reportfix.md`](active/reportfix.md)
**Status:** ✅ Active Analysis (v1.0.10)
**Summary:** Analysis of why many template placeholders remain unfilled (Phase 2 extraction gap).

**Key Finding:** Phase 3 calculations are fully implemented. The bottleneck is Phase 2 extraction not extracting detailed component data.

**Missing Phase 2 Data:**
- FFO/AFFO reconciliation components (26 REALPAC adjustments)
- ACFO reconciliation components (17 REALPAC adjustments)
- Cash flow investing/financing details (for AFCF + burn rate)
- Liquidity breakdown (for cash runway analysis)
- Dilution detail (for credit assessment)

**Solution:** Implement comprehensive Phase 2 extraction (Option 2 from this document).

**When to Read:** Understanding template placeholder population gaps or planning Phase 2 enhancements.

---

## 🔬 Research (Technical Evaluations)

Research documents evaluating technologies and approaches:

### [`research/PDF_EXTRACTION_LIBRARY_RESEARCH.md`](research/PDF_EXTRACTION_LIBRARY_RESEARCH.md)
**Status:** ✅ Active Research (2025-10-21)
**Summary:** Evaluation of alternative PDF extraction libraries for parallel conversion and validation.

**Key Findings:**
- **PDFPlumber:** Strongest alternative to Camelot (96% accuracy on complex tables)
- **Camelot Status:** `camelot-py` actively maintained (v1.0.9, Aug 2025)
- **PyMuPDF4LLM:** Best for markdown conversion (0.14s, clean output)
- **Multi-Library Validation:** Recommended best practice for production systems

**When to Read:** Evaluating Phase 1 improvements or troubleshooting PDF extraction issues.

---

## 📢 Outreach (External Communication)

LinkedIn posts and external-facing content:

### [`outreach/Linkedin_AFCF.md`](outreach/Linkedin_AFCF.md)
**Status:** ✅ Updated (v1.0.12 implementation)
**Summary:** 4 LinkedIn post options announcing AFCF metric implementation.

**Options:**
1. **Technical/Professional** - Implementation details + GitHub link
2. **Problem-Focused** - Distribution sustainability analysis
3. **Story-Driven** - Real-world example (Dream Industrial REIT)
4. **Short & Direct** - Production-ready announcement

**When to Use:** Sharing AFCF implementation on LinkedIn or technical blogs.

---

## 📦 Archive

### Completed Features ([`archive/completed_features/`](archive/completed_features/))

Implementation guides for completed features (historical reference):

| File | Feature | Version | Date |
|------|---------|---------|------|
| `ACFO_IMPLEMENTATION.md` | ACFO calculation | v1.0.5 | 2025-10-20 |
| `FFO_AFFO_IMPLEMENTATION_DESIGN.md` | FFO/AFFO calculation | v1.0.4 | 2025-10-20 |
| `ISSUE_4_IMPLEMENTATION_SUMMARY.md` | Issue #4 summary | v1.0.4 | 2025-10-20 |
| `AFCF_Research_Proposal.md` | AFCF methodology | v1.0.6 | 2025-10-21 |

**When to Read:** Understanding implementation history or reviewing past design decisions.

---

### Deprecated ([`archive/deprecated/`](archive/deprecated/))

Historical research superseded by current implementation:

| File | Topic | Status |
|------|-------|--------|
| `SEMANTIC_CHUNKING_RESEARCH.md` | Semantic chunking strategies | ❌ Superseded by file reference architecture |

---

## 🗺️ Documentation Map by Use Case

### "I'm new to the project"
1. Start: [`architecture/COMPLETE_ARCHITECTURE.md`](architecture/COMPLETE_ARCHITECTURE.md)
2. Then: [`architecture/V1.0.4_REVERSION_LESSONS.md`](architecture/V1.0.4_REVERSION_LESSONS.md)

### "I need to enhance Phase 2 extraction"
1. Read: [`active/reportfix.md`](active/reportfix.md) (understand the gap)
2. Check: [`archive/completed_features/ACFO_IMPLEMENTATION.md`](archive/completed_features/ACFO_IMPLEMENTATION.md) (example implementation)

### "I want to improve PDF extraction"
1. Read: [`research/PDF_EXTRACTION_LIBRARY_RESEARCH.md`](research/PDF_EXTRACTION_LIBRARY_RESEARCH.md)
2. Review: [`architecture/V1.0.4_REVERSION_LESSONS.md`](architecture/V1.0.4_REVERSION_LESSONS.md) (avoid past mistakes)

### "I'm working on Phase 5 template population"
1. Read: [`active/PHASE5_DUAL_TABLE_RECONCILIATION_FIX.md`](active/PHASE5_DUAL_TABLE_RECONCILIATION_FIX.md)
2. Check: [`active/reportfix.md`](active/reportfix.md) (data availability)

### "I want to share the AFCF implementation"
1. Use: [`outreach/Linkedin_AFCF.md`](outreach/Linkedin_AFCF.md)

---

## 📊 Documentation Statistics

| Category | Files | Total Size |
|----------|-------|------------|
| Architecture | 2 | 54KB |
| Active | 2 | 80KB |
| Research | 1 | 17KB |
| Outreach | 1 | 4KB |
| Archive (Completed) | 4 | 63KB |
| Archive (Deprecated) | 1 | 16KB |
| **Total** | **11** | **234KB** |

**Reduction from reorganization:** -31KB (1 file deleted: `old-PHASE5_REPORTED_VS_CALCULATED_IMPLEMENTATION.md`)

---

## 🔄 Maintenance

**Documentation Review Schedule:**
- **Monthly:** Update version numbers in active docs
- **Quarterly:** Archive completed implementation guides
- **Per Release:** Update `COMPLETE_ARCHITECTURE.md` with new features

**Adding New Documentation:**
- Active work → `active/`
- Research → `research/`
- Architecture changes → `architecture/`
- Completed features → `archive/completed_features/`

---

**Last Reorganization:** 2025-10-21 (v1.0.12)
**Maintained by:** System Architecture Team
