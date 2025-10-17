#!/usr/bin/env python3
"""
Phase 2: Extract key financial metrics using Claude Code (no API key required)

This script:
1. Takes markdown financial statements as input
2. Creates extraction prompt for Claude Code
3. Saves prompt to file for Claude Code to process
4. Claude Code will perform extraction and save JSON output

ADVANTAGE: No API key required - uses Claude Code's built-in capabilities
"""

import json
import sys
from pathlib import Path


def create_extraction_prompt(markdown_text, issuer_name_hint=None):
    """
    Create extraction prompt for Claude Code

    Args:
        markdown_text: Markdown financial statements
        issuer_name_hint: Optional issuer name hint

    Returns:
        str: Prompt for Claude Code
    """

    prompt = f"""You are extracting financial data from financial statements for credit analysis.

Extract key financial metrics from the financial statement below into structured JSON.

**Required JSON Structure:**

```json
{{
  "issuer_name": "string (name of the REIT/company)",
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
    "revenue": number (in thousands),
    "property_operating_expenses": number,
    "noi": number (net operating income),
    "interest_expense": number,
    "net_income": number,
    "ebitda": number
  }},

  "ffo_affo": {{
    "ffo": number (funds from operations, in thousands),
    "affo": number (adjusted funds from operations, in thousands),
    "ffo_per_unit": number,
    "affo_per_unit": number,
    "distributions_per_unit": number
  }},

  "portfolio": {{
    "occupancy_rate": number (percentage 0-100),
    "gla_sf": number (gross leasable area in square feet),
    "same_property_noi_growth": number (percentage),
    "property_count": number
  }}
}}
```

**Extraction Rules:**
1. Extract numbers WITHOUT commas or dollar signs (e.g., 2611435 not $2,611,435)
2. All amounts in thousands unless otherwise noted
3. If a field is not found, use null
4. Percentages should be just the number (e.g., 92.5 for 92.5%)
5. For quarterly data, do NOT annualize - keep quarterly values
6. Return ONLY valid JSON

**Important:**
- Save your extracted JSON to: `./temp_analysis/phase2_extracted_data.json`
- Ensure the JSON is properly formatted and valid
- Run validation checks after extraction

**Financial Statement:**

{markdown_text}

**Task:**
1. Extract the data following the schema above
2. Validate the extraction (balance sheet must balance, revenue > 0, occupancy 0-100%)
3. Save the result to `./temp_analysis/phase2_extracted_data.json`
"""

    return prompt


def main():
    """Main execution - prepares extraction for Claude Code"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract financial metrics using Claude Code (no API key needed)',
        epilog='Example: python extract_key_metrics_claude_code.py financial_statements.md'
    )
    parser.add_argument(
        'markdown_files',
        nargs='+',
        help='Markdown file(s) to process (from Phase 1)'
    )
    parser.add_argument(
        '--output',
        default='./temp_analysis/phase2_extracted_data.json',
        help='Output JSON file path'
    )
    parser.add_argument(
        '--issuer',
        help='Optional issuer name hint'
    )

    args = parser.parse_args()

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

    # Create extraction prompt
    print("\n🤖 Preparing extraction prompt for Claude Code...")

    prompt = create_extraction_prompt(combined_text, args.issuer)

    # Save prompt to file
    prompt_path = Path('./temp_analysis/phase2_extraction_prompt.txt')
    prompt_path.parent.mkdir(parents=True, exist_ok=True)

    with open(prompt_path, 'w') as f:
        f.write(prompt)

    print(f"✅ Extraction prompt saved to: {prompt_path}")

    # Save combined markdown for reference
    markdown_path = Path('./temp_analysis/phase2_combined_markdown.md')
    with open(markdown_path, 'w') as f:
        f.write(combined_text)

    print(f"✅ Combined markdown saved to: {markdown_path}")

    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("\n📋 Claude Code will now extract the financial data")
    print(f"📄 Prompt saved at: {prompt_path}")
    print(f"📊 Output will be saved to: {args.output}")
    print("\nProcessing with Claude Code...")
    print("=" * 70)


if __name__ == "__main__":
    main()
