#!/usr/bin/env python3
"""
Phase 2 (EFFICIENT): Extract key financial metrics using Claude Code (no API required)

IMPROVEMENT: Instead of embedding 140K tokens of markdown in the prompt,
this version references file paths and lets Claude Code read them directly.

Token reduction: ~140K → ~1K tokens (99% reduction)

Configuration support: v1.1.0
- Supports markdown→JSON or PDF→JSON extraction
- Configurable via config/extraction_config.yaml
"""

import json
import sys
from pathlib import Path

# Import configuration loader
try:
    from config_loader import load_config
except ImportError:
    # Fallback if not in same directory
    sys.path.insert(0, str(Path(__file__).parent))
    from config_loader import load_config


def create_efficient_extraction_prompt(markdown_files, output_path, issuer_name):
    """
    Create EFFICIENT extraction prompt for Claude Code

    Instead of embedding full markdown text (~140K tokens),
    just reference file paths (~1K tokens)

    Args:
        markdown_files: List of markdown file paths
        output_path: Path where JSON should be saved
        issuer_name: Name of issuer

    Returns:
        str: Compact prompt for Claude Code
    """

    # Load schema from single source of truth
    schema_path = Path(__file__).parent.parent / '.claude' / 'knowledge' / 'phase2_extraction_schema.json'
    with open(schema_path, 'r') as f:
        schema_template = f.read()

    # Create file list with paths
    file_list = "\n".join([f"- `{f}`" for f in markdown_files])

    prompt = f"""# Phase 2: Extract Financial Data for {issuer_name}

**Task:** Extract structured financial data from markdown files and save as JSON.

**Input Files:**
{file_list}

**Output File:** `{output_path}`

---

## EXTRACTION INSTRUCTIONS

### Step 1: Read Files
Use the Read tool to access each markdown file listed above.

### Step 2: Extract Required Data

Follow this **EXACT schema** (required for Phase 3 compatibility):

```json
{schema_template}
```

### Step 3: Data Extraction Guidelines

**CRITICAL RULES:**
1. **Numbers:** No commas or $ signs (e.g., `2611435` not `$2,611,435`)
2. **Units:** All amounts in thousands (as shown in statements)
3. **Decimals:** Rates as decimals (e.g., `0.878` for 87.8%, NOT `87.8`)
4. **Field Names:** EXACTLY as shown above
5. **Structure:** FLAT - no nested objects in balance_sheet
6. **Most Recent Period:** Use latest period data (e.g., Q2 2025, six months)

**WHERE TO FIND DATA:**

**Balance Sheet:**
- Look for "Consolidated Balance Sheets" or "Statement of Financial Position"
- Usually in consolidated financial statements PDF
- Extract: total_assets, cash, mortgages (current/non-current), debentures, equity

**Income Statement:**
- Look for "Consolidated Statements of Operations" or "Statement of Income"
- Calculate NOI = Revenue - Operating Expenses - Realty Taxes
- Extract: revenue, NOI, interest expense, net income

**FFO/AFFO (Basic - Required):**
- Usually in MD&A document
- Look for "FFO and AFFO" section or tables showing "Funds from Operations"
- Extract: FFO, AFFO, per unit amounts, payout ratios
- **Minimum Required:** `ffo`, `affo`, `ffo_per_unit`, `affo_per_unit`, `distributions_per_unit`

**FFO/AFFO Components (COMPREHENSIVE - enables reconciliation tables):**
- Enables calculating FFO/AFFO from first principles per REALPAC methodology (Jan 2022)
- Look in "Notes to Financial Statements" - often has FFO/AFFO reconciliation table
- **Starting Point:** Net income from Statement of Comprehensive Income
- **Key Adjustments to Extract:**
  - **Adjustment A:** Unrealized fair value changes in investment properties
  - **Adjustment B:** Depreciation of depreciable real estate assets
  - **Adjustment C:** Amortization of tenant allowances
  - **Adjustment D:** Amortization of tenant/customer relationship intangibles
  - **Adjustment E:** Gains/losses from property sales
  - **Adjustment V (for AFFO):** Sustaining capital expenditures
  - **Adjustment W (for AFFO):** Leasing costs (internal + external)
  - **Adjustment X (for AFFO):** Tenant improvements (sustaining only)
  - **Adjustment Y (for AFFO):** Straight-line rent adjustment
- **Common Section:** "Reconciliation of Net Income to FFO" or "FFO Calculation"
- **Note:** Extract actual amounts shown in reconciliation, not formulas

**ACFO Components (OPTIONAL - for REALPAC ACFO calculation):**
- Enables calculating ACFO per REALPAC ACFO White Paper (January 2023)
- Look for "Consolidated Statements of Cash Flows" for starting point
- **Starting Point:** Cash flow from operations (IFRS) from cash flow statement
- **Key Adjustments to Extract (if disclosed in notes):**
  - **Adjustment 1:** Change in working capital (to eliminate non-sustainable fluctuations)
  - **Adjustment 2:** Interest expense in financing activities (add back)
  - **Adjustment 3:** JV distributions received OR calculated JV ACFO
  - **Adjustment 4:** Sustaining/maintenance CAPEX (should match AFFO Adj V)
  - **Adjustment 5:** External leasing costs only
  - **Adjustment 6:** Sustaining tenant improvements (should match AFFO Adj X)
  - **Adjustment 14:** Interest expense/income timing adjustments
  - **Adjustment 16:** ROU (Right of Use) asset adjustments for ground leases
- **Common Sections:**
  - Cash flow statement for CFO starting point
  - Notes showing "Non-IFRS measures" or "ACFO reconciliation"
  - May be in MD&A "Adjusted Cash Flow from Operations" section
- **Important:** Many issuers don't disclose full ACFO - extract what's available

**Portfolio Data:**
- Look in MD&A "PROPERTY PORTFOLIO" section
- Search for: "XX properties", "Portfolio Summary", "GLA", "Occupancy"
- Common table headers: "Property count", "GLA (000's S.F.)", "% Occupied"
- **GLA Units:** Usually shown as "9,549" meaning 9,549,000 SF → enter as `9549000`

**Debt Details:**
- Current vs non-current mortgages usually in Notes (e.g., "Note 11: Mortgages")
- Debentures in separate note (e.g., "Note 12: Debentures")
- Check cash flow statement for recent repayments

**Cash Flow from Investing Activities (OPTIONAL - for AFCF analysis):**
- Look for "Consolidated Statements of Cash Flows" or "Cash Flow Statement"
- Find the "INVESTING ACTIVITIES" section
- Extract the following (use NEGATIVE for outflows, POSITIVE for inflows):
  - **Development CAPEX:** "Additions to investment properties" or "Development expenditures" (negative)
    - Should match `capex_development_acfo` if extracting ACFO components
  - **Property Acquisitions:** "Acquisition of investment properties" (negative)
  - **Property Dispositions:** "Proceeds from sale of investment properties" (positive)
  - **JV Capital Contributions:** "Investment in equity accounted entities" or "Contributions to joint ventures" (negative)
  - **JV Return of Capital:** "Distribution from equity accounted entities" or "Return of capital from JVs" (positive)
  - **Business Combinations:** "Acquisition of subsidiaries" or "Business combinations" (negative)
  - **Total CFI:** "Net cash used in investing activities" (for reconciliation)
- **IMPORTANT:** Do NOT include sustaining CAPEX here - that's already in ACFO components
- **Sign Convention:** Outflows are negative, inflows are positive (as shown in cash flow statement)

**Cash Flow from Financing Activities (OPTIONAL - for AFCF coverage analysis):**
- Look in the "FINANCING ACTIVITIES" section of the cash flow statement
- Extract the following (use NEGATIVE for outflows, POSITIVE for inflows):
  - **Debt Principal Repayments:** "Repayment of mortgages" or "Principal payments on debt" (negative)
  - **New Debt Issuances:** "Proceeds from mortgages" or "Issuance of debentures" (positive)
  - **Distributions - Common:** "Distributions to unitholders" or "Dividends paid" (negative)
  - **Distributions - Preferred:** "Distributions on preferred units" (negative, if separate line)
  - **Distributions - NCI:** "Distributions to non-controlling interests" (negative, if separate line)
  - **Equity Issuances:** "Issuance of units" or "Proceeds from equity" (positive)
  - **Unit Buybacks:** "Repurchase of units" or "Unit buyback" (negative)
  - **Deferred Financing Costs:** "Deferred financing costs paid" (negative)
  - **Total CFF:** "Net cash from (used in) financing activities" (for reconciliation)
- **Note:** Some statements combine all distributions into one line - extract as `distributions_common`
- **Sign Convention:** Outflows are negative, inflows are positive (as shown in statement)

### Step 4: Validation

After extraction, check:
- ✓ All REQUIRED fields present
- ✓ Numbers are integers (no commas)
- ✓ Decimals for rates (0.878 not 87.8)
- ✓ Balance sheet reasonably balances
- ✓ Interest expense is POSITIVE
- ✓ Occupancy between 0.0-1.0

### Step 5: Save JSON

Save to: `{output_path}`

### Step 6: Validate Schema

Run validation:
```bash
python scripts/validate_extraction_schema.py {output_path}
```

Fix any errors before proceeding to Phase 3.

---

## REFERENCE DOCUMENTS

**Schema & Templates:**
- Schema specification: `.claude/knowledge/phase2_extraction_schema.json`
- Template with examples: `.claude/knowledge/phase2_extraction_template.json`
- Full schema documentation: `.claude/knowledge/SCHEMA_README.md`

**Comprehensive Extraction Guide (NEW - v1.0.11):**
- **Detailed extraction guide:** `.claude/knowledge/COMPREHENSIVE_EXTRACTION_GUIDE.md`
- **Purpose:** Step-by-step instructions for extracting FFO/AFFO/ACFO components
- **Includes:**
  - 26 FFO/AFFO adjustments (A-U + V-Z) with lookup tables
  - 17 ACFO adjustments with consistency checks
  - Cash flow investing/financing extraction
  - Liquidity and dilution data extraction (including multiple credit facilities)
  - Credit facility extraction priority order (MD&A → Notes → Balance Sheet)
  - Handling conflicting information and borrowing base limitations
  - Validation procedures and sign conventions
- **🔥 READ THIS GUIDE FIRST** before starting comprehensive extraction

---

**IMPORTANT:**
- Read the markdown files using the Read tool (do NOT ask user for content)
- Search thoroughly across all files for portfolio data
- Use exact field names from schema
- Save valid JSON to output path specified above
"""

    return prompt


def create_pdf_direct_extraction_prompt(pdf_files, output_path, issuer_name):
    """
    Create extraction prompt for DIRECT PDF→JSON extraction

    Skips markdown conversion entirely, reads PDFs directly.

    Args:
        pdf_files: List of PDF file paths
        output_path: Path where JSON should be saved
        issuer_name: Name of issuer

    Returns:
        str: Compact prompt for Claude Code
    """

    # Load schema from single source of truth
    schema_path = Path(__file__).parent.parent / '.claude' / 'knowledge' / 'phase2_extraction_schema.json'
    with open(schema_path, 'r') as f:
        schema_template = f.read()

    # Create file list with paths
    file_list = "\n".join([f"- `{f}`" for f in pdf_files])

    prompt = f"""# Phase 2: Extract Financial Data for {issuer_name} (DIRECT PDF EXTRACTION)

**Task:** Extract structured financial data DIRECTLY from PDF files and save as JSON.

**Input Files (PDFs):**
{file_list}

**Output File:** `{output_path}`

---

## EXTRACTION INSTRUCTIONS

### Step 1: Read PDFs Directly
Use the Read tool to access each PDF file listed above. Claude Code can read PDFs natively.

### Step 2: Extract Required Data

Follow this **EXACT schema** (required for Phase 3 compatibility):

```json
{schema_template}
```

### Step 3: Data Extraction Guidelines

**CRITICAL RULES:**
1. **Numbers:** No commas or $ signs (e.g., `2611435` not `$2,611,435`)
2. **Units:** All amounts in thousands (as shown in statements)
3. **Decimals:** Rates as decimals (e.g., `0.878` for 87.8%, NOT `87.8`)
4. **Field Names:** EXACTLY as shown above
5. **Structure:** FLAT - no nested objects in balance_sheet
6. **Most Recent Period:** Use latest period data (e.g., Q2 2025, six months)

**WHERE TO FIND DATA:**

**Balance Sheet:**
- Look for "Consolidated Balance Sheets" or "Statement of Financial Position"
- Usually in consolidated financial statements PDF
- Extract: total_assets, cash, mortgages (current/non-current), debentures, equity

**Income Statement:**
- Look for "Consolidated Statements of Operations" or "Statement of Income"
- Calculate NOI = Revenue - Operating Expenses - Realty Taxes
- Extract: revenue, NOI, interest expense, net income

**FFO/AFFO (Basic - Required):**
- Usually in MD&A document
- Look for "FFO and AFFO" section or tables showing "Funds from Operations"
- Extract: FFO, AFFO, per unit amounts, payout ratios
- **Minimum Required:** `ffo`, `affo`, `ffo_per_unit`, `affo_per_unit`, `distributions_per_unit`

**FFO/AFFO Components (COMPREHENSIVE - enables reconciliation tables):**
- Enables calculating FFO/AFFO from first principles per REALPAC methodology (Jan 2022)
- Look in "Notes to Financial Statements" - often has FFO/AFFO reconciliation table
- **Starting Point:** Net income from Statement of Comprehensive Income
- **Key Adjustments to Extract:**
  - **Adjustment A:** Unrealized fair value changes in investment properties
  - **Adjustment B:** Depreciation of depreciable real estate assets
  - **Adjustment C:** Amortization of tenant allowances
  - **Adjustment D:** Amortization of tenant/customer relationship intangibles
  - **Adjustment E:** Gains/losses from property sales
  - **Adjustment V (for AFFO):** Sustaining capital expenditures
  - **Adjustment W (for AFFO):** Leasing costs (internal + external)
  - **Adjustment X (for AFFO):** Tenant improvements (sustaining only)
  - **Adjustment Y (for AFFO):** Straight-line rent adjustment
- **Common Section:** "Reconciliation of Net Income to FFO" or "FFO Calculation"
- **Note:** Extract actual amounts shown in reconciliation, not formulas

**ACFO Components (OPTIONAL - for REALPAC ACFO calculation):**
- Enables calculating ACFO per REALPAC ACFO White Paper (January 2023)
- Look for "Consolidated Statements of Cash Flows" for starting point
- **Starting Point:** Cash flow from operations (IFRS) from cash flow statement
- **Key Adjustments to Extract (if disclosed in notes):**
  - **Adjustment 1:** Change in working capital (to eliminate non-sustainable fluctuations)
  - **Adjustment 2:** Interest expense in financing activities (add back)
  - **Adjustment 3:** JV distributions received OR calculated JV ACFO
  - **Adjustment 4:** Sustaining/maintenance CAPEX (should match AFFO Adj V)
  - **Adjustment 5:** External leasing costs only
  - **Adjustment 6:** Sustaining tenant improvements (should match AFFO Adj X)
  - **Adjustment 14:** Interest expense/income timing adjustments
  - **Adjustment 16:** ROU (Right of Use) asset adjustments for ground leases
- **Common Sections:**
  - Cash flow statement for CFO starting point
  - Notes showing "Non-IFRS measures" or "ACFO reconciliation"
  - May be in MD&A "Adjusted Cash Flow from Operations" section
- **Important:** Many issuers don't disclose full ACFO - extract what's available

**Portfolio Data:**
- Look in MD&A "PROPERTY PORTFOLIO" section
- Search for: "XX properties", "Portfolio Summary", "GLA", "Occupancy"
- Common table headers: "Property count", "GLA (000's S.F.)", "% Occupied"
- **GLA Units:** Usually shown as "9,549" meaning 9,549,000 SF → enter as `9549000`

**Debt Details:**
- Current vs non-current mortgages usually in Notes (e.g., "Note 11: Mortgages")
- Debentures in separate note (e.g., "Note 12: Debentures")
- Check cash flow statement for recent repayments

**Cash Flow from Investing Activities (OPTIONAL - for AFCF analysis):**
- Look for "Consolidated Statements of Cash Flows" or "Cash Flow Statement"
- Find the "INVESTING ACTIVITIES" section
- Extract the following (use NEGATIVE for outflows, POSITIVE for inflows):
  - **Development CAPEX:** "Additions to investment properties" or "Development expenditures" (negative)
    - Should match `capex_development_acfo` if extracting ACFO components
  - **Property Acquisitions:** "Acquisition of investment properties" (negative)
  - **Property Dispositions:** "Proceeds from sale of investment properties" (positive)
  - **JV Capital Contributions:** "Investment in equity accounted entities" or "Contributions to joint ventures" (negative)
  - **JV Return of Capital:** "Distribution from equity accounted entities" or "Return of capital from JVs" (positive)
  - **Business Combinations:** "Acquisition of subsidiaries" or "Business combinations" (negative)
  - **Total CFI:** "Net cash used in investing activities" (for reconciliation)
- **IMPORTANT:** Do NOT include sustaining CAPEX here - that's already in ACFO components
- **Sign Convention:** Outflows are negative, inflows are positive (as shown in cash flow statement)

**Cash Flow from Financing Activities (OPTIONAL - for AFCF coverage analysis):**
- Look in the "FINANCING ACTIVITIES" section of the cash flow statement
- Extract the following (use NEGATIVE for outflows, POSITIVE for inflows):
  - **Debt Principal Repayments:** "Repayment of mortgages" or "Principal payments on debt" (negative)
  - **New Debt Issuances:** "Proceeds from mortgages" or "Issuance of debentures" (positive)
  - **Distributions - Common:** "Distributions to unitholders" or "Dividends paid" (negative)
  - **Distributions - Preferred:** "Distributions on preferred units" (negative, if separate line)
  - **Distributions - NCI:** "Distributions to non-controlling interests" (negative, if separate line)
  - **Equity Issuances:** "Issuance of units" or "Proceeds from equity" (positive)
  - **Unit Buybacks:** "Repurchase of units" or "Unit buyback" (negative)
  - **Deferred Financing Costs:** "Deferred financing costs paid" (negative)
  - **Total CFF:** "Net cash from (used in) financing activities" (for reconciliation)
- **Note:** Some statements combine all distributions into one line - extract as `distributions_common`
- **Sign Convention:** Outflows are negative, inflows are positive (as shown in statement)

### Step 4: Validation

After extraction, check:
- ✓ All REQUIRED fields present
- ✓ Numbers are integers (no commas)
- ✓ Decimals for rates (0.878 not 87.8)
- ✓ Balance sheet reasonably balances
- ✓ Interest expense is POSITIVE
- ✓ Occupancy between 0.0-1.0

### Step 5: Save JSON

Save to: `{output_path}`

### Step 6: Validate Schema

Run validation:
```bash
python scripts/validate_extraction_schema.py {output_path}
```

Fix any errors before proceeding to Phase 3.

---

## REFERENCE DOCUMENTS

**Schema & Templates:**
- Schema specification: `.claude/knowledge/phase2_extraction_schema.json`
- Template with examples: `.claude/knowledge/phase2_extraction_template.json`
- Full schema documentation: `.claude/knowledge/SCHEMA_README.md`

**Comprehensive Extraction Guide (NEW - v1.0.11):**
- **Detailed extraction guide:** `.claude/knowledge/COMPREHENSIVE_EXTRACTION_GUIDE.md`
- **Purpose:** Step-by-step instructions for extracting FFO/AFFO/ACFO components
- **Includes:**
  - 26 FFO/AFFO adjustments (A-U + V-Z) with lookup tables
  - 17 ACFO adjustments with consistency checks
  - Cash flow investing/financing extraction
  - Liquidity and dilution data extraction (including multiple credit facilities)
  - Credit facility extraction priority order (MD&A → Notes → Balance Sheet)
  - Handling conflicting information and borrowing base limitations
  - Validation procedures and sign conventions
- **🔥 READ THIS GUIDE FIRST** before starting comprehensive extraction

---

**IMPORTANT:**
- Read the PDF files using the Read tool (Claude Code has native PDF support)
- Search thoroughly across all files for portfolio data
- Use exact field names from schema
- Save valid JSON to output path specified above
"""

    return prompt


def main():
    """Main execution - creates efficient extraction prompt"""
    import argparse
    import re

    parser = argparse.ArgumentParser(
        description='Phase 2 (EFFICIENT): Extract financial metrics - Supports markdown or PDF input',
        epilog='Example: python extract_key_metrics_efficient.py --issuer-name "Artis REIT" FS.md MDA.md\n'
               'Example: python extract_key_metrics_efficient.py --issuer-name "Artis REIT" --pdf statements.pdf mda.pdf'
    )
    parser.add_argument(
        'input_files',
        nargs='+',
        help='Input file(s) - can be markdown (.md) or PDF (.pdf) files'
    )
    parser.add_argument(
        '--issuer-name',
        required=True,
        help='Issuer name'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output JSON path (default: auto-generated)'
    )
    parser.add_argument(
        '--pdf',
        action='store_true',
        help='Treat input as PDF files (direct PDF→JSON extraction)'
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"⚠️  Warning: Could not load config ({e}), using defaults")
        config = None

    # Auto-generate output path
    if args.output is None:
        import re
        safe_name = args.issuer_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '', safe_name)
        # Use absolute path from current working directory
        cwd = Path.cwd()
        args.output = str(cwd / 'Issuer_Reports' / safe_name / 'temp' / 'phase2_extracted_data.json')

    # Determine extraction mode
    # Priority: 1) CLI flag --pdf, 2) Config setting, 3) Auto-detect from file extensions
    use_pdf_mode = False

    if args.pdf:
        # Explicit CLI flag
        use_pdf_mode = True
        extraction_mode = "PDF→JSON (CLI flag)"
    elif config and config.get_phase2_method() == "pdf_to_json":
        # Config setting
        use_pdf_mode = True
        extraction_mode = "PDF→JSON (config)"
    else:
        # Auto-detect from file extensions
        first_file = Path(args.input_files[0])
        if first_file.suffix.lower() == '.pdf':
            use_pdf_mode = True
            extraction_mode = "PDF→JSON (auto-detected)"
        else:
            extraction_mode = "Markdown→JSON (default)"

    print("=" * 70)
    print("PHASE 2: FINANCIAL DATA EXTRACTION (EFFICIENT MODE)")
    print("=" * 70)
    if config:
        config.print_active_config()
    print(f"Extraction mode: {extraction_mode}\n")

    # Validate input files exist
    input_paths = []
    total_size = 0
    file_type = "PDF" if use_pdf_mode else "Markdown"

    for input_file in args.input_files:
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"❌ Error: File not found: {input_path}")
            sys.exit(1)

        size = input_path.stat().st_size
        total_size += size
        input_paths.append(str(input_path))
        print(f"✓ Found: {input_path.name} ({size/1024:.1f} KB)")

    print(f"\n📊 Total {file_type} size: {total_size/1024:.1f} KB")

    if use_pdf_mode:
        print(f"📊 Estimated tokens (PDF reading): ~{total_size//4:,}")
    else:
        print(f"📊 Estimated tokens if embedded: ~{total_size//4:,}")

    # Create extraction prompt based on mode
    print(f"\n🚀 Creating extraction prompt...")

    if use_pdf_mode:
        print("   (Direct PDF→JSON extraction, skips Phase 1)")
        prompt = create_pdf_direct_extraction_prompt(
            input_paths,
            args.output,
            args.issuer_name
        )
    else:
        print("   (References file paths instead of embedding content)")
        prompt = create_efficient_extraction_prompt(
            input_paths,
            args.output,
            args.issuer_name
        )

    # Save prompt
    output_dir = Path(args.output).parent
    prompt_path = output_dir / 'phase2_extraction_prompt.txt'
    prompt_path.parent.mkdir(parents=True, exist_ok=True)

    with open(prompt_path, 'w') as f:
        f.write(prompt)

    prompt_size = len(prompt)
    print(f"\n✅ Extraction prompt saved: {prompt_path}")
    print(f"   Prompt size: {prompt_size/1024:.1f} KB (~{prompt_size//4:,} tokens)")

    if not use_pdf_mode:
        print(f"   🎯 Token reduction: ~{total_size//4:,} → ~{prompt_size//4:,} tokens")
        print(f"   💰 Efficiency gain: {100*(1-prompt_size/total_size):.1f}% smaller")

    # Instructions
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("\n📋 Claude Code will now:")
    print("   1. Read the extraction prompt")

    if use_pdf_mode:
        print("   2. Use Read tool to access PDF files directly")
    else:
        print("   2. Use Read tool to access markdown files")

    print("   3. Extract financial data per schema")
    print("   4. Validate extraction")
    print(f"   5. Save JSON to: {args.output}")
    print("\n⏳ Ready for Claude Code extraction...")
    print("=" * 70)

    sys.exit(0)


if __name__ == "__main__":
    main()
