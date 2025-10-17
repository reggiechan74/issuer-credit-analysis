#!/usr/bin/env python3
"""
Phase 2: Extract key financial metrics using Claude Code (no API required)

This script:
1. Takes markdown financial statements as input
2. Creates extraction prompt for Claude Code
3. Saves prompt for Claude Code to process
4. Claude Code extracts data and saves JSON

ADVANTAGE: No API key required - uses Claude Code's built-in capabilities
"""

import json
import sys
from pathlib import Path


def create_extraction_prompt(markdown_text, output_path):
    """
    Create extraction prompt for Claude Code to process

    Args:
        markdown_text: Financial statement markdown
        output_path: Path where JSON should be saved

    Returns:
        str: Prompt for Claude Code
    """

    prompt = f"""Extract financial data from these financial statements and save as JSON.

**Output File:** `{output_path}`

**CRITICAL: Follow this EXACT schema for Phase 3 compatibility**

Schema reference: `.claude/knowledge/phase2_extraction_schema.json`
Template: `.claude/knowledge/phase2_extraction_template.json`

**Required JSON Structure:**

```json
{{
  "issuer_name": "REQUIRED: Full legal name of issuer",
  "reporting_date": "REQUIRED: YYYY-MM-DD format",
  "reporting_period": "Human-readable period (e.g., 'Q2 2025')",
  "currency": "REQUIRED: CAD or USD",

  "balance_sheet": {{
    "_comment": "FLAT structure - NO nested objects",
    "total_assets": "REQUIRED: number",
    "mortgages_noncurrent": "REQUIRED: number (non-current mortgages/loans)",
    "mortgages_current": "REQUIRED: number (current portion)",
    "credit_facilities": "REQUIRED: number (credit facility borrowings)",
    "cash": "REQUIRED: number (cash and equivalents)",
    "senior_unsecured_debentures": "Optional: number (default 0)",
    "investment_properties": "Optional: number",
    "total_liabilities": "Optional: number",
    "total_unitholders_equity": "Optional: number"
  }},

  "income_statement": {{
    "_comment": "MUST include top-level noi, interest_expense, revenue",
    "noi": "REQUIRED: number (Net Operating Income - most recent period)",
    "interest_expense": "REQUIRED: number (positive value - most recent period)",
    "revenue": "REQUIRED: number (most recent period)",
    "q2_2025": {{
      "_comment": "Optional detailed breakdown",
      "revenue": "number",
      "net_operating_income": "number"
    }}
  }},

  "ffo_affo": {{
    "_comment": "MUST include top-level values for most recent period",
    "ffo": "REQUIRED: number (FFO - most recent period)",
    "affo": "REQUIRED: number (AFFO - most recent period)",
    "ffo_per_unit": "REQUIRED: number (FFO per unit)",
    "affo_per_unit": "REQUIRED: number (AFFO per unit)",
    "distributions_per_unit": "REQUIRED: number",
    "q2_2025": {{
      "_comment": "Optional detailed breakdown"
    }}
  }},

  "portfolio": {{
    "_comment": "IMPORTANT: Search MD&A 'PROPERTY PORTFOLIO' section or quarterly tables",
    "total_properties": "REQUIRED: number - Search for 'XX properties', 'Number of properties', 'property count' in MD&A",
    "total_gla_sf": "REQUIRED: number - GLA in square feet (search for 'XX million square feet', 'GLA (000s', 'gross leasable area')",
    "occupancy_rate": "REQUIRED: number (decimal) - Search MD&A for occupancy tables or 'Occupancy:' sections",
    "occupancy_with_commitments": "Optional: number (decimal) - Occupancy including committed leases if disclosed",
    "same_property_noi_growth_6m": "Optional: number (decimal) - Same property NOI growth if disclosed"
  }}
}}
```

**CRITICAL Extraction Rules:**
1. **Numbers:** NO commas or $ signs (e.g., 2611435 not $2,611,435)
2. **Units:** All amounts in thousands unless specified
3. **Portfolio data:** GLA in full square feet (e.g., 9673000 for 9.673 million sq ft)
4. **Missing data:** Only use 0 if truly not disclosed after thorough search (check MD&A, quarterly tables, footnotes)
5. **Decimals:** Occupancy/growth rates as decimals (0.878 for 87.8%, NOT 87.8)
6. **Periods:** Use most recent period (e.g., Q2) for top-level fields
7. **Flat structure:** balance_sheet fields must be flat (NO nested objects)
8. **Field names:** EXACTLY as shown (mortgages_noncurrent NOT mortgages_loans_noncurrent)
9. **Search thoroughly:** Property count and GLA are usually in MD&A 'PROPERTY PORTFOLIO' section - search the entire document

**Validation Checks:**
- Balance sheet must balance: Assets = Liabilities + Equity (within 1% tolerance)
- Interest expense must be POSITIVE number
- Occupancy rates must be 0.0-1.0 (decimal format)
- NOI margin should be 40-70% for REITs

**After extraction, validate with:**
```bash
python scripts/validate_extraction_schema.py {output_path}
```

**Financial Statements:**

{markdown_text}

**IMPORTANT:** Save the extracted JSON to: `{output_path}`
"""

    return prompt


def main():
    """Main execution - prepares extraction for Claude Code"""
    import argparse
    import re

    parser = argparse.ArgumentParser(
        description='Phase 2: Extract financial metrics using Claude Code (no API key needed)',
        epilog='Example: python extract_key_metrics.py --issuer-name "Artis REIT" financial_statements.md'
    )
    parser.add_argument(
        'markdown_files',
        nargs='+',
        help='Markdown file(s) to process (from Phase 1)'
    )
    parser.add_argument(
        '--issuer-name',
        required=True,
        help='Issuer name (for folder organization)'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output JSON file path (default: auto-generated from issuer name)'
    )

    args = parser.parse_args()

    # Auto-generate output path if not specified
    if args.output is None:
        safe_name = args.issuer_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '', safe_name)
        args.output = f'./Issuer_Reports/{safe_name}/temp/phase2_extracted_data.json'

    print("=" * 70)
    print("PHASE 2: FINANCIAL DATA EXTRACTION (Claude Code)")
    print("=" * 70)

    # Combine all markdown files
    combined_text = ""
    for md_file in args.markdown_files:
        md_path = Path(md_file)

        if not md_path.exists():
            print(f"❌ Error: File not found: {md_path}")
            sys.exit(1)

        print(f"\n📄 Reading: {md_path.name}")
        with open(md_path, 'r', encoding='utf-8') as f:
            text = f.read()
            combined_text += f"\n\n# FILE: {md_path.name}\n\n{text}"

    print(f"\n📊 Total text length: {len(combined_text):,} characters")
    print(f"📊 Estimated tokens: ~{len(combined_text)//4:,}")

    # Create extraction prompt for Claude Code
    print("\n🤖 Creating extraction prompt for Claude Code...")

    prompt = create_extraction_prompt(combined_text, args.output)

    # Save prompt to file (same folder as output)
    output_dir = Path(args.output).parent
    prompt_path = output_dir / 'phase2_extraction_prompt.txt'
    prompt_path.parent.mkdir(parents=True, exist_ok=True)

    with open(prompt_path, 'w') as f:
        f.write(prompt)

    print(f"✅ Extraction prompt saved to: {prompt_path}")

    # Instructions for Claude Code
    print("\n" + "=" * 70)
    print("CLAUDE CODE EXTRACTION MODE")
    print("=" * 70)
    print("\n📋 Prompt saved - Claude Code will now:")
    print("   1. Read the extraction prompt")
    print("   2. Extract financial data from markdown")
    print("   3. Validate the extraction")
    print(f"   4. Save JSON to: {args.output}")
    print("\n⏳ Processing with Claude Code...")
    print("=" * 70)

    # Exit successfully - Claude Code will handle the extraction
    sys.exit(0)


if __name__ == "__main__":
    main()
