# Phase 4 Output Format Standard

**Version:** 1.0.0
**Date:** 2025-10-29
**Purpose:** Strict format contract between Phase 4 (LLM agent) and Phase 5 (Python script)

---

## Overview

Phase 4 must output markdown with **EXACT** section headers specified below. Phase 5 Python script expects these precise headers - no variations allowed.

**Why This Matters:**
- Eliminates section mapping bugs
- Removes need for Phase 5 to handle multiple header variations
- Creates clear API contract between phases
- Enables simple, maintainable Phase 5 code

---

## Required Section Headers (Exact Format)

### 1. Credit Opinion Summary
```markdown
## 1. Credit Opinion Summary

[4 paragraphs of comprehensive credit analysis]

**Key Credit Drivers:**
- Driver 1
- Driver 2
- Driver 3
- Driver 4
```

**Requirements:**
- Must be numbered section "## 1."
- Must use EXACT title "Credit Opinion Summary"
- Must include "**Key Credit Drivers:**" subsection with bullet list
- Drivers should be concise factor names (not full sentences)

---

### 2. Key Credit Factors (Scorecard Table)
```markdown
## 2. Key Credit Factors

| **Factor** | **Weight** | **Assessment** | **Score** | **Rationale** |
|------------|------------|----------------|-----------|---------------|
| **1. Factor Name** | X% | Rating | X/5 | Explanation |
| **2. Factor Name** | X% | Rating | X/5 | Explanation |
...
| **Overall Scorecard Outcome** | **100%** | **Rating** | **X.X/5** | **Overall assessment** |
```

**Requirements:**
- Must be numbered section "## 2."
- Must use EXACT title "Key Credit Factors"
- Must be markdown table with exact column names
- Factor names in first column must be bolded with numbers
- Must include "Overall Scorecard Outcome" as final row

---

### 3. Rating Outlook
```markdown
## 3. Rating Outlook

**Outlook:** [Positive/Stable/Negative/Developing] (XX-XX months)

**Justification:**

[Narrative explaining outlook]

**Base Case (XX% probability):**
[Scenario description]

**Upside Case (XX% probability):**
[Scenario description]

**Downside Case (XX% probability):**
[Scenario description]

**Distressed Case (XX% probability):**
[Scenario description]

**Key Monitoring Metrics:**
- Metric 1
- Metric 2

**Rating Upgrade Factors (XX-XX months):**
- Factor 1
- Factor 2
...

**Rating Downgrade Factors (XX-XX months):**
- Factor 1
- Factor 2
...
```

**Requirements:**
- Must be numbered section "## 3."
- Must use EXACT title "Rating Outlook"
- Must include subsections with EXACT titles:
  - "**Rating Upgrade Factors**" (not "Upgrade Scenarios" or variations)
  - "**Rating Downgrade Factors**" (not "Downgrade Scenarios" or variations)
- Upgrade/downgrade must be embedded in Rating Outlook section

---

### 4. Detailed Credit Analysis
```markdown
## 4. Detailed Credit Analysis

### 4.1 Scale & Diversification
[Analysis]

### 4.2 Asset Quality & Portfolio
[Analysis]

### 4.3 Leverage & Coverage
[Analysis]

### 4.4 Financial Flexibility
[Analysis]

### 4.5 Liquidity & Cash Flow
[Analysis]

### 4.6 Market Position & Strategy
[Analysis]

### 4.7 Governance & Transparency
[Analysis]
```

**Requirements:**
- Must be numbered section "## 4."
- Must use EXACT title "Detailed Credit Analysis"
- Subsections must use numbered format (4.1, 4.2, etc.)
- Factor names must match scorecard exactly

---

### 5. Credit Strengths
```markdown
## 5. Credit Strengths

- **Strength Name:** Explanation
- **Strength Name:** Explanation
...
```

**Requirements:**
- Can be standalone section OR synthesized by Phase 5 from scorecard (scores ≥4/5)
- If provided, must use EXACT title "Credit Strengths"
- Must use bullet list format with bold strength names

---

### 6. Credit Challenges
```markdown
## 6. Credit Challenges

- **Challenge Name:** Explanation
- **Challenge Name:** Explanation
...
```

**Requirements:**
- Can be standalone section OR synthesized by Phase 5 from scorecard (scores ≤2/5)
- If provided, must use EXACT title "Credit Challenges"
- Must use bullet list format with bold challenge names

---

### Optional Sections

These sections are optional but if included must use exact titles:

- "## 7. Liquidity and Capital Resources"
- "## 8. Financial Covenants"
- "## 9. Debt Maturity Profile"
- "## 10. Recent Developments"
- "## 11. Peer Comparison"
- "## 12. Methodology and Rating Factors"

---

## Forbidden Variations

**DO NOT USE these header variations** (causes Phase 5 mapping errors):

❌ "Executive Summary" → Use "Credit Opinion Summary"
❌ "Five-Factor Scorecard" → Use "Key Credit Factors"
❌ "Upgrade Scenarios" → Use "Rating Upgrade Factors"
❌ "Downgrade Scenarios" → Use "Rating Downgrade Factors"
❌ "RATING SENSITIVITY ANALYSIS" → Use "Rating Outlook" with subsections
❌ "Factor-by-Factor Scoring" → Use "Key Credit Factors"

---

## Phase 5 Extraction Logic (Simplified)

With this standard, Phase 5 can use simple exact matching:

```python
# Simple extraction - no variation handling needed
exec_summary = sections.get('1. Credit Opinion Summary', 'Not available')
scorecard = sections.get('2. Key Credit Factors', 'Not available')
rating_outlook = sections.get('3. Rating Outlook', 'Not available')
detailed_analysis = sections.get('4. Detailed Credit Analysis', 'Not available')
credit_strengths = sections.get('5. Credit Strengths', 'Synthesize from scorecard')
credit_challenges = sections.get('6. Credit Challenges', 'Synthesize from scorecard')

# Extract upgrade/downgrade from Rating Outlook subsections
upgrade_factors = extract_subsection(rating_outlook, 'Rating Upgrade Factors')
downgrade_factors = extract_subsection(rating_outlook, 'Rating Downgrade Factors')
```

---

## Validation Checklist

Phase 4 output must pass this checklist:

- [ ] Section "1. Credit Opinion Summary" exists
- [ ] "**Key Credit Drivers:**" subsection with bullet list exists
- [ ] Section "2. Key Credit Factors" exists with table
- [ ] Table has columns: Factor, Weight, Assessment, Score, Rationale
- [ ] Section "3. Rating Outlook" exists
- [ ] "**Rating Upgrade Factors**" subsection exists in Rating Outlook
- [ ] "**Rating Downgrade Factors**" subsection exists in Rating Outlook
- [ ] Section "4. Detailed Credit Analysis" exists with subsections
- [ ] All section numbers are sequential
- [ ] No forbidden header variations used

---

## Benefits

✅ **Zero section mapping bugs** - Exact headers, no variations
✅ **Simplified Phase 5 code** - Remove all variation handling
✅ **Clear contract** - Phase 4 knows exactly what to output
✅ **Maintainable** - Single source of truth for format
✅ **Testable** - Easy to validate format compliance

---

## Implementation

1. **Update Phase 4 agent definition** (`.claude/agents/domain_expert/issuer_due_diligence_expert_slim.md`)
   - Add Output Format section with exact header requirements
   - Include validation checklist
   - Emphasize: "Use EXACT headers - Phase 5 depends on precise format"

2. **Simplify Phase 5 script** (`scripts/generate_final_report.py`)
   - Remove all header variation handling
   - Use exact section name matching
   - Add format validation warnings

3. **Test with new Phase 4 run**
   - Generate new credit analysis with updated agent
   - Verify Phase 5 extracts all sections correctly
   - Confirm no "Not available" placeholders

---

*This standard eliminates 90% of Phase 5 maintenance burden by enforcing format at the source.*
