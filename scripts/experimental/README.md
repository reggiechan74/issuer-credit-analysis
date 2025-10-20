# Experimental Phase 2 Extraction (v2.0)

This folder contains experimental implementations of Phase 2 (Markdown → JSON) extraction that are **not recommended for production use**.

## Files

### `extract_key_metrics_v2.py`
Alternative Phase 2 extraction using grep-based section indexing and targeted extraction.

**Features:**
- Grep-based section indexing (0 LLM tokens for indexing)
- Section-by-section extraction with validation
- Progressive enhancement (expand reads if data missing)
- Checkpointing for resumable extraction
- Token reduction: ~140K → ~15K (89% savings vs embedded approach)

**Why Experimental:**
- More token-efficient than original embedded approach (~89% reduction)
- BUT slower in practice due to overhead of indexing + multiple extraction passes
- **The production method (`extract_key_metrics_efficient.py`) achieves 99% token reduction (~1K tokens) with file references**, making v2's complexity unnecessary

### `extraction_indexer.py`
Section indexing module for v2 extraction.

Implements grep-based discovery of financial data sections in markdown files:
- Balance sheet location
- Income statement location
- Cash flow statement location
- FFO/AFFO reconciliation location
- Portfolio metrics location

### `section_extractor.py`
Targeted extraction module for v2.

Implements section-by-section extraction with validation:
- Read only indexed sections (minimal token usage)
- Validate each section immediately after extraction
- Progressive enhancement if data is incomplete
- Checkpoint intermediate results

## Why Not Production?

While v2 implements sophisticated optimization techniques, it is **not recommended for production** because:

1. **Slower:** Multiple passes (indexing → extraction → validation → expansion) add overhead
2. **More complex:** Harder to debug and maintain compared to simple file reference approach
3. **Unnecessary:** The production `extract_key_metrics_efficient.py` achieves better results:
   - **99% token reduction** (~1K tokens) vs v2's 89% reduction (~15K tokens)
   - **Faster:** Single-pass extraction with Claude Code's Read tool
   - **Simpler:** Just reference file paths, Claude Code handles reading
   - **More reliable:** Proven architecture without context window issues

## Production Recommendation

**Use `scripts/extract_key_metrics_efficient.py` instead** (v1.0.10 default)

```bash
# Phase 2 extraction (recommended)
python scripts/extract_key_metrics_efficient.py --issuer-name "Artis REIT" \
  Issuer_Reports/Artis_REIT/temp/phase1_markdown/*.md
```

Token usage: ~1K tokens (file references only)
Execution time: ~5-10 seconds
Success rate: 100% (no context window issues)

## When to Use v2?

**Theoretical scenarios only:**
- Research into alternative extraction architectures
- Experimentation with section-based progressive enhancement
- Studying tradeoffs between token efficiency and execution speed

**Not recommended for production credit analysis.**

---

**Version:** v2.0 (Experimental)
**Status:** 🧪 Research/Testing Only
**Maintained:** No active development (production uses efficient method)
