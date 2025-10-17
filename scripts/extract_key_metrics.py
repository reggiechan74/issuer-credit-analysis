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

**Required JSON Structure:**

```json
{{
  "issuer_name": "string",
  "reporting_date": "YYYY-MM-DD",
  "report_period": "string (e.g., 'Q2 2025')",
  "currency": "CAD or USD",

  "balance_sheet": {{
    "total_assets": number (in thousands),
    "investment_properties": number,
    "cash": number,
    "total_liabilities": number,
    "mortgages_noncurrent": number,
    "mortgages_current": number,
    "credit_facilities": number,
    "senior_unsecured_debentures": number,
    "equity": number
  }},

  "income_statement": {{
    "revenue": number (quarterly),
    "property_operating_expenses": number,
    "noi": number (net operating income),
    "interest_expense": number (quarterly),
    "net_income": number,
    "ebitda": number
  }},

  "ffo_affo": {{
    "ffo": number (quarterly),
    "affo": number (quarterly),
    "ffo_per_unit": number (quarterly),
    "affo_per_unit": number (quarterly),
    "distributions_per_unit": number (quarterly)
  }},

  "portfolio": {{
    "occupancy_rate": number (0-100),
    "gla_sf": number (total square feet),
    "same_property_noi_growth": number (percentage),
    "property_count": number
  }}
}}
```

**Extraction Rules:**
1. Extract numbers WITHOUT commas or $ signs (e.g., 2611435 not $2,611,435)
2. All amounts in thousands (unless specified otherwise)
3. Use null for missing fields
4. Percentages as numbers only (92.5 not "92.5%")
5. For quarterly data - do NOT annualize, keep quarterly values

**Validation Checks:**
- Balance sheet must balance: Assets = Liabilities + Equity (within 1% tolerance)
- Revenue must be > 0
- Occupancy must be 0-100%
- NOI margin should be 40-70% for REITs (warning if outside range)

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
